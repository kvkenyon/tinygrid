# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Tiny Grid is a Python SDK for accessing electricity grid data from US Independent System Operators (ISOs). Currently supports 100+ ERCOT endpoints with plans to support other ISOs (CAISO, PJM, NYISO, ISO-NE, MISO, SPP).

## Architecture

The project follows a three-layer architecture:

1. **pyercot/** - Auto-generated API client
   - Low-level HTTP client wrapping ERCOT's REST API
   - Generated from ERCOT's OpenAPI specification
   - Provides sync/async methods for each endpoint (e.g., `get_spp.sync()`, `get_spp.asyncio()`)
   - Located in a separate directory with its own `pyproject.toml`

2. **tinygrid/** - SDK wrapper layer
   - High-level API abstraction over pyercot
   - Core classes: `ERCOT` client, `ERCOTAuth` authentication
   - Provides conveniences: pagination, retry logic, date range chunking, pandas DataFrames
   - Exposes error types: `GridError`, `GridAPIError`, `GridAuthenticationError`, `GridTimeoutError`

3. **tests/** - Test suite
   - Uses pytest with respx for HTTP mocking
   - Fixtures in `conftest.py` for common test data
   - Test organization by feature (test_ercot.py, test_ercot_retry.py, test_ercot_unified.py, etc.)

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

### Historical Data Access

`ERCOTArchive` class provides bulk download of historical data:
- Uses POST-based batch downloads (max 1000 items per batch)
- Returns data as pandas DataFrames
- Automatically handles date ranges with threading for concurrent downloads
- Located in `tinygrid/historical/ercot.py`

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
1. Check pyercot has the endpoint function imported (in `tinygrid/ercot.py` imports)
2. Add wrapper method to ERCOT class that calls the pyercot endpoint
3. Handle date formatting via `format_api_date()`
4. Return pandas DataFrame
5. Add tests in appropriate test file

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
