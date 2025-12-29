# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Tiny Grid is a Python SDK for accessing electricity grid data from US Independent System Operators (ISOs). Currently supports 100+ ERCOT endpoints with plans to support other ISOs (CAISO, PJM, NYISO, ISO-NE, MISO, SPP).

## ERCOT Developer Resources

- **Developer Portal**: https://developer.ercot.com
- **API Explorer**: https://apiexplorer.ercot.com (register for subscription key)
- **OpenAPI Specs**: https://github.com/ercot/api-specs
- **API Base URL**: https://api.ercot.com/api/public-reports

## ERCOT API Data Availability (Important Limitations)

1. **API Data Start Date**: December 11, 2023
   - The REST API only contains data from this date forward
   - For earlier data, use MIS document downloads or historical archives
   - Historical archives extend 7+ years back

2. **Data Delay**: Approximately 1 hour
   - Real-time data is NOT truly real-time
   - There is ~1 hour delay from actual grid operations to API availability

3. **Geographic Restriction**: US IP addresses only
   - API blocks requests from non-US IP addresses
   - Users outside the US need a VPN or US-based proxy

4. **Rate Limit**: 30 requests per minute
   - Exceeding this limit results in HTTP 429 errors
   - SDK includes built-in rate limiter (enabled by default)

5. **Bulk Download Limit**: 1,000 documents per request
   - Archive bulk downloads limited to 1,000 files per POST request

## Architecture

The project follows a three-layer architecture:

1. **pyercot/** - Auto-generated API client
   - Low-level HTTP client wrapping ERCOT's REST API
   - Generated from ERCOT's OpenAPI specification
   - Provides sync/async methods for each endpoint (e.g., `get_spp.sync()`, `get_spp.asyncio()`)
   - Located in a separate directory with its own `pyproject.toml`

2. **tinygrid/** - SDK wrapper layer
   - High-level API abstraction over pyercot
   - Main `ERCOT` client composed of multiple mixin classes:
     - `ERCOTBase` (client.py): Auth, retry logic, pagination, rate limiting
     - `ERCOTEndpointsMixin` (endpoints.py): Low-level wrappers for 100+ pyercot endpoints
     - `ERCOTAPIMixin` (api.py): High-level unified API methods (get_spp, get_lmp, etc.)
     - `ERCOTDashboardMixin` (dashboard.py): Public dashboard methods (no auth required)
     - `ERCOTDocumentsMixin` (documents.py): MIS document fetching for yearly historical data
   - Supporting classes:
     - `ERCOTAuth`: Token-based authentication management
     - `ERCOTArchive`: Historical data access (>90 days old)
     - `ERCOTPoller`: Real-time polling utilities
     - `EIAClient`: EIA API integration for pre-December 2023 data
   - Exposes error types: `GridError`, `GridAPIError`, `GridAuthenticationError`, `GridTimeoutError`, `GridRateLimitError`, `GridRetryExhaustedError`

3. **tests/** - Test suite
   - Uses pytest with respx for HTTP mocking
   - Fixtures in `conftest.py` for common test data
   - Test organization by feature (test_ercot.py, test_ercot_retry.py, test_ercot_unified.py, etc.)
   - 746 tests with 95% coverage

4. **examples/** - Usage examples
   - `ercot_demo.ipynb`: Jupyter notebook demonstrating SDK features
   - `demo/`: Full-stack web application showcasing TinyGrid SDK
     - FastAPI backend with TinyGrid SDK integration
     - React + TypeScript + Vite frontend
     - Docker Compose for easy deployment
     - Demonstrates dashboard, prices, forecasts, and historical data

## Development Commands

This project uses `just` for task automation. View all available commands with:

```bash
just help
```

Common commands:

```bash
# Install dependencies
just install

# Run all tests
just test

# Run specific test file
just test-file tests/test_ercot.py

# Run single test function
just test-func tests/test_ercot.py::TestERCOT::test_initialization_default

# Run tests with coverage
just test-coverage

# Lint code
just lint

# Lint and fix issues automatically (use before committing)
just lint-fix

# Format code
just format

# Type check with pyright
just type-check

# Run all pre-commit checks (lint, format, type-check)
just pre-commit

# Run all checks including tests
just check

# Build distributions
just build

# Publish to PyPI
just publish
```

Alternatively, you can run commands directly with uv:

```bash
uv sync --dev --all-extras
uv run pytest
uv run ruff check --fix --unsafe-fixes .
uv run ruff format .
uv run pyright
```

## Key Patterns and Conventions

### ERCOT Client Usage

The `ERCOT` class is the main entry point. It wraps pyercot's generated client with:
- Automatic token management via `ERCOTAuth`
- Retry logic with exponential backoff (configurable via `max_retries`)
- Rate limiting (30 requests/minute, configurable via `rate_limit_enabled` and `requests_per_minute`)
- Context manager support for resource cleanup
- Pagination handling (page_size defaults to 10000)

Example initialization:
```python
from tinygrid import ERCOT, ERCOTAuth, ERCOTAuthConfig

auth = ERCOTAuth(ERCOTAuthConfig(
    username="user@example.com",
    password="password",
    subscription_key="key"
))
ercot = ERCOT(auth=auth, max_retries=3)

# Disable rate limiting for testing (not recommended for production)
ercot = ERCOT(auth=auth, rate_limit_enabled=False)
```

### Data Fetching Patterns

Methods in ERCOT class wrap pyercot endpoint functions. Key patterns:

1. **Date normalization**: Methods accept flexible date formats (strings, Timestamp) via `parse_date()`
2. **Date range chunking**: Decorator `@support_date_range(freq="7D")` automatically chunks large date ranges
3. **DataFrame conversion**: Methods return pandas DataFrames (via `pd.DataFrame` construction from pyercot Report data)
4. **Pagination**: Handled internally; results from multiple pages are concatenated

### Constants and Enums

Located in `tinygrid/constants/ercot.py`:
- `Market` enum: REAL_TIME_SCED, REAL_TIME_15_MIN, DAY_AHEAD_HOURLY
- `LocationType` enum: LOAD_ZONE, TRADING_HUB, RESOURCE_NODE, ELECTRICAL_BUS
- `SettlementPointType` enum: LZ, HB, RN prefixes
- `LOAD_ZONES` and `TRADING_HUBS` lists for ERCOT-specific locations
- `ENDPOINT_MAPPINGS` dict for unified method routing (maps market types to endpoint paths)
- `ERCOT_TIMEZONE` = "US/Central"
- `HISTORICAL_THRESHOLD_DAYS` = 90 (threshold for using archive API vs. real-time API)

### Dashboard Methods (No Authentication Required)

`ERCOTDashboardMixin` provides access to real-time grid data from ERCOT's public dashboard JSON:
- `get_status()`: Grid operating condition, current load, capacity, reserves
- `get_fuel_mix()`: Generation breakdown by fuel type (coal, gas, nuclear, wind, solar, etc.)
- `get_renewable_generation()`: Wind and solar output with forecasts
- `get_supply_demand()`: Hourly supply and demand data
- `get_daily_prices()`: Daily price summary
- Located in `tinygrid/ercot/dashboard.py`
- Returns structured Python objects (GridStatus, FuelMixEntry, RenewableStatus)

### Historical Data Access

`ERCOTArchive` class provides bulk download of historical data (>90 days old):
- Uses POST-based batch downloads (max 1000 items per batch)
- Returns data as pandas DataFrames
- Automatically handles date ranges with threading for concurrent downloads
- Located in `tinygrid/ercot/archive.py`

`ERCOTDocumentsMixin` provides access to yearly historical data from MIS documents:
- `get_rtm_spp_historical(year)`: Full year of RTM settlement point prices
- `get_dam_spp_historical(year)`: Full year of DAM settlement point prices
- `get_settlement_point_mapping()`: Settlement point to bus mapping
- Downloads and parses Excel/CSV files from ERCOT's document archive
- Located in `tinygrid/ercot/documents.py`
- Report type IDs available in `REPORT_TYPE_IDS` constant

### Polling Utilities

`ERCOTPoller` class and `poll_latest()` function for real-time data monitoring:
- `poll_latest(client, method, interval, max_iterations)`: Generator-based polling
- `ERCOTPoller(client, interval).poll(method, callback, max_iterations)`: Callback-based polling
- Automatic error handling and retry logic
- Configurable polling interval and iteration limits
- Located in `tinygrid/ercot/polling.py`

### EIA Integration

`EIAClient` provides access to ERCOT data via the EIA API for data before December 2023:
- `get_demand(start, end)`: Hourly electricity demand
- `get_generation_by_fuel(start, end)`: Generation breakdown by fuel type
- `get_interchange(start, end)`: Net interchange with other grids
- Requires free API key from https://www.eia.gov/opendata/register.php
- Located in `tinygrid/ercot/eia.py`

### Testing Patterns

- Use respx for mocking HTTP requests (configured in fixtures)
- Use `MagicMock` for mocking pyercot client
- Tests are organized by feature, not by file
- Fixtures provide sample Report, ReportData, and Product objects
- Use `pytest.mark.parametrize` for testing multiple scenarios

## Important Implementation Details

### Timezone Handling

All ERCOT times use "US/Central" timezone. Date utilities in `tinygrid/utils/tz.py` handle conversion.

### Retry Logic

Implemented via `tenacity` library. `ERCOT` class includes:
- Exponential backoff with jitter
- Configurable retry count via `max_retries` parameter
- Custom retry exceptions: `GridRetryExhaustedError`

### Authentication

`ERCOTAuth` manages token lifecycle:
- Caches tokens to avoid repeated authentication
- Auto-refreshes tokens before expiration (TTL defaults to 3300 seconds/55 minutes)
- Handles Azure B2C authentication flow
- Raises `GridAuthenticationError` on auth failures

### Error Handling

Custom exception hierarchy:
- `GridError` - base class
  - `GridTimeoutError` - request timeout
  - `GridAPIError` - HTTP/API errors (includes status_code, response_body, endpoint)
    - `GridAuthenticationError` - auth failures
  - `GridRateLimitError` - rate limiting
  - `GridRetryExhaustedError` - retry attempts exhausted

Methods with `raise_on_error=True` (default) raise exceptions; with `False` they return None/empty DataFrame.

## Building and Publishing

The project uses `uv` for dependency management:
- `pyproject.toml` defines dependencies, build system, tool configs
- Both tinygrid and pyercot are packages
- pyercot is installed editable from local path (via `[tool.uv.sources]`)
- Use `uv build` to create distributions
- Use `uv publish` to publish to PyPI

## Common Development Tasks

**Adding a new ERCOT method:**

For low-level endpoint wrappers (ERCOTEndpointsMixin):
1. Check pyercot has the endpoint function imported (in `tinygrid/ercot/__init__.py` imports)
2. Add wrapper method to `ERCOTEndpointsMixin` in `tinygrid/ercot/endpoints.py`
3. Handle date formatting via `format_api_date()`
4. Return pandas DataFrame
5. Add tests in appropriate test file

For high-level unified API methods (ERCOTAPIMixin):
1. Add method to `ERCOTAPIMixin` in `tinygrid/ercot/api.py`
2. Use `@support_date_range()` decorator if method should handle large date ranges
3. Route to appropriate endpoint based on market type using `ENDPOINT_MAPPINGS`
4. Handle automatic historical routing if data age > HISTORICAL_THRESHOLD_DAYS
5. Add tests in `tests/test_ercot_unified.py` or similar

For dashboard methods (ERCOTDashboardMixin):
1. Add method to `ERCOTDashboardMixin` in `tinygrid/ercot/dashboard.py`
2. Define response models using attrs dataclasses
3. Parse JSON response from ERCOT dashboard endpoint
4. No authentication required for these methods
5. Add tests in `tests/test_ercot_dashboard.py`

**Working with dates:**
- Use `parse_date()` for flexible input parsing
- Use `format_api_date()` for ERCOT API format (YYYY-MM-DD)
- Use `parse_date_range()` for start/end pairs
- Use `date_chunks()` with `@support_date_range()` decorator for automatic chunking

**Testing HTTP endpoints:**
- Use respx to mock requests
- Mock the full URL (base_url + endpoint path)
- Create realistic pyercot Report/ReportData objects as fixtures
- Test error cases explicitly

**Working with the demo application:**
- Backend: `cd examples/demo/backend && uvicorn main:app --reload`
- Frontend: `cd examples/demo/frontend && npm run dev`
- Docker: `cd examples/demo && docker compose up --build`
- Backend uses TinyGrid SDK to serve data to React frontend
- API docs available at http://localhost:8000/docs

## Demo Web Application

The `examples/demo/` directory contains a full-stack web application demonstrating TinyGrid SDK features.

### Architecture
- **Backend**: FastAPI application (`backend/main.py`) with modular routes
  - `routes/dashboard.py`: Grid status, fuel mix, renewables
  - `routes/prices.py`: SPP and LMP data with caching
  - `routes/forecasts.py`: Load, wind, and solar forecasts
  - `routes/historical.py`: Archive data access
  - `client.py`: Shared ERCOT client instance
- **Frontend**: React + TypeScript + Vite application
  - Pages: Dashboard, Prices, Forecasts, Historical
  - TanStack Query for data fetching and caching
  - Recharts for data visualization
  - Tailwind CSS for styling

### Key Features Demonstrated
- Dashboard methods without authentication (`get_status()`, `get_fuel_mix()`)
- Real-time data visualization with auto-refresh
- Data caching and background prefetching
- Error handling with retry logic
- Filtering and market selection
- Historical data access (>90 days)

### Running the Demo
See `examples/demo/README.md` for detailed setup instructions. Quick start:
```bash
cd examples/demo
docker compose up --build
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```
