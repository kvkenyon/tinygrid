# tinygrid

The SDK layer that wraps auto-generated API clients with a clean, high-level interface.

## Architecture

The tinygrid SDK uses a modular mixin-based architecture for the ERCOT client:

```
tinygrid/
├── ercot/                 # ERCOT client package
│   ├── __init__.py        # Main ERCOT class (combines all mixins)
│   ├── client.py          # ERCOTBase - auth, retry, pagination, rate limiting
│   ├── endpoints.py       # ERCOTEndpointsMixin - 100+ pyercot endpoint wrappers
│   ├── api.py             # ERCOTAPIMixin - high-level unified API methods
│   ├── archive.py         # ERCOTArchive - historical archive API access
│   ├── dashboard.py       # ERCOTDashboardMixin - public dashboard JSON endpoints
│   ├── documents.py       # ERCOTDocumentsMixin - MIS document fetching
│   ├── eia.py             # EIAClient - EIA API integration
│   ├── polling.py         # ERCOTPoller - real-time polling utilities
│   └── transforms.py      # Data filtering and transformation utilities
├── auth/                  # Authentication handling
├── constants/             # Market types, location enums, mappings
├── utils/                 # Date parsing, timezone, decorators, rate limiting
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

Access ERCOT's public dashboard JSON endpoints (no auth required):

```python
ercot = ERCOT()

# Get current grid status
status = ercot.get_status()
print(f"Condition: {status.condition}")  # NORMAL, WATCH, EMERGENCY, EEA1, etc.
print(f"Load: {status.current_load:,.0f} MW")
print(f"Reserves: {status.reserves:,.0f} MW")

# Get fuel mix
fuel_mix = ercot.get_fuel_mix()  # Returns DataFrame

# Get renewable generation
renewables = ercot.get_renewable_generation()  # Returns RenewableStatus
print(f"Wind: {renewables.wind_mw:,.0f} MW")
print(f"Solar: {renewables.solar_mw:,.0f} MW")

# Get supply/demand curve
supply_demand = ercot.get_supply_demand()
```

**Note:** These endpoints are undocumented and may change without notice.

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
- Rate limiting (30 req/min, configurable)
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

### eia.py (EIAClient)

Access ERCOT data via the EIA API (useful for data before Dec 2023):

```python
from tinygrid.ercot import EIAClient

eia = EIAClient(api_key="your-eia-key")

# Get hourly demand (from 2019)
demand = eia.get_demand(start="2022-01-01", end="2022-01-07")

# Get generation by fuel type
gen = eia.get_generation_by_fuel(start="2022-01-01")
```

### polling.py (ERCOTPoller)

Real-time polling utilities for continuous data monitoring:

```python
from tinygrid.ercot import ERCOTPoller, poll_latest

# Simple generator pattern
for df in poll_latest(ercot, ercot.get_spp, interval=60, max_iterations=10):
    process(df)

# Callback pattern with error handling
poller = ERCOTPoller(client=ercot, interval=60, max_errors=5)
poller.poll(method=ercot.get_spp, callback=handle_data)
```

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

## RTC+B Support

The SDK supports ERCOT's RTC+B (Real-Time Co-optimization + Batteries) changes that went live in December 2024:

### New Resource Types

```python
from tinygrid import ResourceType, AncillaryServiceType

# ESR (Energy Storage Resource) for batteries
ResourceType.ESR   # "ESR"
ResourceType.DESR  # "DESR" - Distributed ESR
ResourceType.DGR   # "DGR" - Distributed Generation Resource

# All ancillary service types
AncillaryServiceType.REGUP   # Regulation Up
AncillaryServiceType.REGDN   # Regulation Down
AncillaryServiceType.NSPIN   # Non-Spinning Reserve
AncillaryServiceType.ECRSM   # ECRS Slow (10-minute)
AncillaryServiceType.ECRSS   # ECRS Super Slow (30-minute)
AncillaryServiceType.RRSFFR  # RRS Fast Frequency Response
```

### Key Dates

- **ESR Integration**: June 1, 2024
- **RTC+B Go-Live**: December 4, 2024

### Legacy Compatibility

All existing endpoints continue to work. The REST API paths remain unchanged - only the data within responses may include new ESR-related fields.

## Tests

```bash
pytest tests/
```

821 tests with 96% code coverage.
