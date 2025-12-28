# Tiny Grid

[![CI](https://github.com/kvkenyon/tinygrid/actions/workflows/ci.yml/badge.svg)](https://github.com/kvkenyon/tinygrid/actions)

A Python SDK for accessing electricity grid data from US Independent System Operators (ISOs).

## Supported ISOs

- **ERCOT** - Electric Reliability Council of Texas (100+ endpoints)

More ISOs (CAISO, PJM, NYISO, ISO-NE, MISO, SPP) planned.

## Installation

```bash
git clone https://github.com/kvkenyon/tinygrid.git
cd tinygrid
uv sync --dev --all-extras
```

## Quick Start

```python
from tinygrid import ERCOT, ERCOTAuth, ERCOTAuthConfig

# Set up authentication
auth = ERCOTAuth(ERCOTAuthConfig(
    username="your-email@example.com",
    password="your-password",
    subscription_key="your-subscription-key",
))

# Create client and fetch data
ercot = ERCOT(auth=auth)

# Get actual system load by weather zone
load_data = ercot.get_actual_system_load_by_weather_zone(
    operating_day_from="2024-12-20",
    operating_day_to="2024-12-20",
    size=24,
)

# Get 7-day load forecast
forecast = ercot.get_load_forecast_by_weather_zone(
    start_date="2024-12-20",
    end_date="2024-12-27",
    size=100,
)

# Get day-ahead market prices
prices = ercot.get_dam_hourly_lmp(
    start_date="2024-12-20",
    end_date="2024-12-20",
    size=50,
)
```

See [`examples/ercot_example.py`](examples/ercot_example.py) for a complete working example.

## ERCOT API Credentials

1. Register at [ERCOT API Explorer](https://apiexplorer.ercot.com/)
2. Subscribe to the API products you need
3. Use your email, password, and subscription key

## Available ERCOT Endpoints

The SDK wraps 100+ ERCOT endpoints:

| Category | Methods |
|----------|---------|
| Load Data | `get_actual_system_load_by_weather_zone`, `get_load_forecast_by_weather_zone`, `get_load_forecast_by_study_area` |
| Pricing | `get_dam_hourly_lmp`, `get_dam_settlement_point_prices`, `get_lmp_electrical_bus`, `get_spp_node_zone_hub` |
| Renewables | `get_wpp_hourly_average_actual_forecast`, `get_spp_hourly_average_actual_forecast` |
| Ancillary Services | `get_dam_as_plan`, `get_total_as_service_offers`, `get_aggregated_as_offers_*` |
| SCED | `get_sced_system_lambda`, `get_sced_gen_res_data`, `get_sced_dsr_load_data` |

All methods accept `**kwargs` for additional API parameters like `size`, `page`, `sort`, etc.

## Error Handling

```python
from tinygrid import ERCOT, GridAPIError, GridTimeoutError, GridAuthenticationError

try:
    data = ercot.get_actual_system_load_by_weather_zone(...)
except GridAuthenticationError as e:
    print(f"Auth failed: {e.message}")
except GridAPIError as e:
    print(f"API error {e.status_code}: {e.message}")
except GridTimeoutError as e:
    print(f"Timed out after {e.timeout}s")
```

## Project Structure

```
tiny-grid/
├── tinygrid/           # SDK layer
│   ├── ercot.py        # ERCOT client with 100+ methods
│   ├── auth/           # Authentication handling
│   └── errors.py       # Error types
├── pyercot/            # Auto-generated ERCOT API client
├── examples/           # Usage examples
└── tests/              # Test suite
```

## Development

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=tinygrid

# Lint
ruff check .

# Format
ruff format .
```

## License

MIT

## Author

Kevin Kenyon - kevin@poweredbylight.com
