# Tiny Grid

[![CI](https://github.com/kvkenyon/tinygrid/actions/workflows/ci.yml/badge.svg)](https://github.com/kvkenyon/tinygrid/actions)
[![codecov](https://codecov.io/gh/kvkenyon/tinygrid/branch/main/graph/badge.svg)](https://codecov.io/gh/kvkenyon/tinygrid)

A Python SDK for accessing electricity grid data from US Independent System Operators (ISOs).

## Supported ISOs

- **ERCOT** - Electric Reliability Council of Texas

More ISOs (CAISO, PJM, NYISO, ISO-NE, MISO, SPP) planned.

## Installation

```bash
git clone https://github.com/kvkenyon/tinygrid.git
cd tinygrid
uv sync --dev --all-extras
```

## Quick Start

### Using the Unified API

The unified API provides simple, consistent methods for common operations with automatic handling of date parsing, market routing, and historical data access.

```python
from tinygrid import ERCOT
from tinygrid.constants import Market, LocationType

# Authentication is optional for most endpoints
ercot = ERCOT()

# Get today's real-time settlement point prices
prices = ercot.get_spp()

# Get day-ahead prices for load zones
prices = ercot.get_spp(
    start="2024-01-15",
    market=Market.DAY_AHEAD_HOURLY,
    location_type=LocationType.LOAD_ZONE,
)

# Get locational marginal prices
lmp = ercot.get_lmp(start="yesterday")

# Get wind and solar forecasts
wind = ercot.get_wind_forecast(start="today", end="2024-01-20")
solar = ercot.get_solar_forecast(by_region=True)

# Get ancillary services data
as_prices = ercot.get_as_prices(start="2024-01-15")
as_plan = ercot.get_as_plan(start="2024-01-15")
```

### Direct Endpoint Access

For full control, call any of the 100+ ERCOT endpoints directly:

```python
from tinygrid import ERCOT, ERCOTAuth, ERCOTAuthConfig

# Set up authentication for restricted endpoints
auth = ERCOTAuth(ERCOTAuthConfig(
    username="your-email@example.com",
    password="your-password",
    subscription_key="your-subscription-key",
))

ercot = ERCOT(auth=auth)

# Call endpoints directly with specific parameters
load_data = ercot.get_actual_system_load_by_weather_zone(
    operating_day_from="2024-12-20",
    operating_day_to="2024-12-20",
    size=24,
)

forecast = ercot.get_load_forecast_by_weather_zone(
    start_date="2024-12-20",
    end_date="2024-12-27",
    size=100,
)
```

See [`examples/ercot_example.py`](examples/ercot_example.py) for complete examples.

## Unified API Methods

These methods provide a simpler interface with automatic routing, date parsing, and historical data access:

| Method | Description | Markets |
|--------|-------------|---------|
| `get_spp()` | Settlement Point Prices | Real-time 15-min, Day-ahead hourly |
| `get_lmp()` | Locational Marginal Prices | Real-time SCED, Day-ahead hourly |
| `get_as_prices()` | Ancillary Services MCPC prices | Day-ahead |
| `get_as_plan()` | Ancillary Services plan | Day-ahead |
| `get_wind_forecast()` | Wind power forecast | System-wide or by region |
| `get_solar_forecast()` | Solar power forecast | System-wide or by region |

### Features

- **Date parsing**: Use "today", "yesterday", or ISO date strings
- **Automatic historical routing**: Seamlessly switches between live and archive APIs based on data age
- **Location filtering**: Filter by load zones, trading hubs, or specific settlement points
- **Market selection**: Choose between real-time and day-ahead markets
- **Standardized columns**: Consistent column names across all endpoints

## ERCOT API Credentials

Authentication is required for some endpoints. To get credentials:

1. Register at [ERCOT API Explorer](https://apiexplorer.ercot.com/)
2. Subscribe to the API products you need
3. Use your email, password, and subscription key

## Available ERCOT Endpoints

Direct access to 100+ ERCOT endpoints organized by category:

| Category | Example Methods |
|----------|---------|
| Load Data | `get_actual_system_load_by_weather_zone`, `get_load_forecast_by_weather_zone`, `get_load_forecast_by_study_area` |
| Pricing | `get_dam_hourly_lmp`, `get_dam_settlement_point_prices`, `get_lmp_electrical_bus`, `get_spp_node_zone_hub` |
| Renewables | `get_wpp_hourly_average_actual_forecast`, `get_spp_hourly_average_actual_forecast` |
| Ancillary Services | `get_dam_as_plan`, `get_total_as_service_offers`, `get_aggregated_as_offers_*` |
| SCED | `get_sced_system_lambda`, `get_sced_gen_res_data`, `get_sced_dsr_load_data` |
| Shadow Prices | `get_shadow_prices_bound_transmission_constraint`, `get_dam_shadow_prices` |
| Outages | `get_hourly_res_outage_cap`, `get_aggregated_outage_schedule` |

All methods accept `**kwargs` for additional API parameters like `size`, `page`, `sort`, etc.

## Constants and Enums

```python
from tinygrid.constants import Market, LocationType, LOAD_ZONES, TRADING_HUBS

# Market types
Market.REAL_TIME_SCED         # Real-time SCED (5-minute)
Market.REAL_TIME_15_MIN       # Real-time 15-minute
Market.DAY_AHEAD_HOURLY       # Day-ahead hourly

# Location types for filtering
LocationType.LOAD_ZONE        # Load zones (LZ_*)
LocationType.TRADING_HUB      # Trading hubs (HB_*)
LocationType.RESOURCE_NODE    # Resource nodes
LocationType.ELECTRICAL_BUS   # Electrical buses

# Pre-defined location lists
LOAD_ZONES = ["LZ_HOUSTON", "LZ_NORTH", "LZ_SOUTH", "LZ_WEST", ...]
TRADING_HUBS = ["HB_HOUSTON", "HB_NORTH", "HB_SOUTH", "HB_WEST", ...]
```

## Error Handling

```python
from tinygrid import ERCOT, GridAPIError, GridTimeoutError, GridAuthenticationError

try:
    data = ercot.get_spp()
except GridAuthenticationError as e:
    print(f"Auth failed: {e.message}")
except GridAPIError as e:
    print(f"API error {e.status_code}: {e.message}")
except GridTimeoutError as e:
    print(f"Timed out after {e.timeout}s")
```

## Project Structure

```
tinygrid/
├── tinygrid/           # SDK layer
│   ├── ercot.py        # ERCOT client with unified and direct API methods
│   ├── auth/           # Authentication handling
│   ├── constants/      # Market types, location enums, endpoint mappings
│   ├── utils/          # Date parsing, timezone handling, decorators
│   └── errors.py       # Error types
├── pyercot/            # Auto-generated ERCOT API client (from OpenAPI spec)
├── examples/           # Usage examples
└── tests/              # Test suite (258 tests)
```

## Development

This project uses `uv` for dependency management and `just` for task automation.

```bash
# Install dependencies
just install

# Run tests
just test

# Run tests with coverage
just test-coverage

# Lint and format
just lint
just format
just lint-fix  # Auto-fix lint issues

# Type check
just type-check

# Run all checks (lint, format, type-check, test)
just check
```

### Pre-commit Hooks

Pre-commit hooks automatically run linting and formatting before each commit to catch issues early.

```bash
# Install hooks (one-time setup after cloning)
just hooks-install

# Run hooks manually on all files
just hooks-run
```

The hooks run:
- **ruff** - Linting with auto-fix
- **ruff-format** - Code formatting
- **pyright** - Type checking

If a hook fails, fix the issues and re-commit. Ruff auto-fixes will be staged automatically.

## License

MIT

## Author

Kevin Kenyon - kevin@poweredbylight.com
