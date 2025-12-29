# tinygrid

The SDK layer that wraps auto-generated API clients with a clean, high-level interface.

## Architecture

The tinygrid SDK uses a modular mixin-based architecture for the ERCOT client:

```
tinygrid/
├── ercot/                 # ERCOT client package
│   ├── __init__.py        # Main ERCOT class (combines all mixins)
│   ├── client.py          # ERCOTBase - auth, retry, pagination, core helpers
│   ├── endpoints.py       # ERCOTEndpointsMixin - 100+ pyercot endpoint wrappers
│   ├── api.py             # ERCOTAPIMixin - high-level unified API methods
│   ├── archive.py         # ERCOTArchive - historical archive API access
│   ├── dashboard.py       # ERCOTDashboardMixin - public dashboard methods (no auth)
│   ├── documents.py       # ERCOTDocumentsMixin - MIS document fetching
│   └── transforms.py      # Data filtering and transformation utilities
├── auth/                  # Authentication handling
├── constants/             # Market types, location enums, mappings
├── utils/                 # Date parsing, timezone handling, decorators
└── errors.py              # Exception hierarchy
```

## Usage

### Basic Usage

```python
from tinygrid import ERCOT, ERCOTAuth, ERCOTAuthConfig

# Without authentication (for dashboard methods)
ercot = ERCOT()

# With authentication
auth = ERCOTAuth(ERCOTAuthConfig(
    username="you@example.com",
    password="your-password",
    subscription_key="your-key",
))
ercot = ERCOT(auth=auth)
```

### Unified API (api.py)

High-level methods with automatic routing, date parsing, and location filtering:

```python
from tinygrid import ERCOT, Market, LocationType

ercot = ERCOT()

# Get settlement point prices
df = ercot.get_spp(
    start="yesterday",
    market=Market.DAY_AHEAD_HOURLY,
    location_type=LocationType.LOAD_ZONE,
)

# Get locational marginal prices
df = ercot.get_lmp(start="2024-01-15")

# Get ancillary service prices
df = ercot.get_as_prices(start="today")
```

### Dashboard Module (dashboard.py)

**Note:** The dashboard methods are placeholders. ERCOT does not provide
documented public JSON endpoints for dashboard data. Use authenticated
API methods instead:

```python
ercot = ERCOT()

# For system load data, use:
load = ercot.get_load(start="today", by="weather_zone")

# For forecasts, use:
wind = ercot.get_wind_forecast(start="today")
solar = ercot.get_solar_forecast(start="today")
```

### Historical Yearly Data (documents.py)

Access full-year historical data from ERCOT's MIS document system:

```python
ercot = ERCOT()

# Get full year of RTM SPP
rtm_2023 = ercot.get_rtm_spp_historical(2023)

# Get full year of DAM SPP
dam_2023 = ercot.get_dam_spp_historical(2023)
```

### Direct Endpoint Access (endpoints.py)

Call any of the 100+ ERCOT endpoints directly:

```python
ercot = ERCOT(auth=auth)

data = ercot.get_actual_system_load_by_weather_zone(
    operating_day_from="2024-12-20",
    operating_day_to="2024-12-20",
    size=24,
)
```

### Context Manager

```python
with ERCOT(auth=auth) as ercot:
    data = ercot.get_load_forecast_by_weather_zone(
        start_date="2024-12-20",
        end_date="2024-12-27",
    )
```

## Module Responsibilities

### client.py (ERCOTBase)

Core functionality inherited by ERCOT class:
- Authentication and token management
- Retry with exponential backoff (via tenacity)
- Pagination handling for large result sets
- DataFrame conversion from API responses
- Historical data routing decisions

### endpoints.py (ERCOTEndpointsMixin)

Low-level wrappers for all pyercot API endpoints:
- Direct mapping to ERCOT REST API endpoints
- Minimal logic - just calls pyercot with retry/pagination
- ~100 methods covering all ERCOT data categories

### api.py (ERCOTAPIMixin)

High-level unified API methods:
- `get_spp()`, `get_lmp()`, `get_as_prices()`, etc.
- Automatic routing between live API and historical archive
- Date parsing with "today", "yesterday" keywords
- Location filtering by type or specific names

### dashboard.py (ERCOTDashboardMixin)

Public dashboard methods (no auth required):
- `get_status()` - Grid operating conditions
- `get_fuel_mix()` - Generation by fuel type
- `get_energy_storage_resources()` - ESR data
- `get_system_wide_demand()`, `get_renewable_generation()`

### documents.py (ERCOTDocumentsMixin)

MIS document fetching for yearly historical data:
- `get_rtm_spp_historical(year)`, `get_dam_spp_historical(year)`
- `get_settlement_point_mapping()`
- Access to ERCOT's Market Information System reports

### transforms.py

Standalone data transformation functions:
- `filter_by_location()` - Filter by location names or types
- `filter_by_date()` - Filter to date range
- `add_time_columns()` - Add Time/End Time from raw fields
- `standardize_columns()` - Rename and reorder columns

## Error Types

- `GridError` - Base exception
- `GridAPIError` - API returned an error (includes status_code, response_body)
- `GridAuthenticationError` - Auth failed
- `GridTimeoutError` - Request timed out
- `GridRateLimitError` - Rate limited (429)
- `GridRetryExhaustedError` - Max retries exceeded

## Tests

```bash
pytest tests/
```

505 tests covering all functionality.
