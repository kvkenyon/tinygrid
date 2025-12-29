# Examples

## Setup

```bash
cd tinygrid
uv sync --dev --all-extras
```

Create a `.env` file in this directory:

```bash
cp .env.example .env
# Edit .env with your credentials
```

## ERCOT Credentials

Get credentials from [ERCOT API Explorer](https://apiexplorer.ercot.com/):

1. Register an account
2. Subscribe to API products
3. Copy your subscription key

Your `.env` file needs:

```
ERCOT_USERNAME=your-email@example.com
ERCOT_PASSWORD=your-password
ERCOT_SUBSCRIPTION_KEY=your-key
```

## Examples

### Demo Notebook

The `ercot_demo.ipynb` notebook demonstrates the full tinygrid API with:

- **Unified API** - `get_spp()`, `get_lmp()`, `get_as_prices()` with automatic routing
- **Dashboard API** - No-auth methods like `get_status()`, `get_fuel_mix()`
- **Historical Yearly Data** - `get_rtm_spp_historical(year)`, `get_dam_spp_historical(year)`
- **Type-safe enums** - `Market`, `LocationType` for IDE autocomplete
- **Date parsing** - "today", "yesterday", "latest" keywords
- **Location filtering** - Filter by Load Zone, Trading Hub, or Resource Node

```bash
# Run with Jupyter
uv run jupyter notebook examples/ercot_demo.ipynb
```

## Quick Start

### Unified API

```python
from tinygrid import ERCOT, Market, LocationType

ercot = ERCOT()

# Get real-time SPP for load zones
df = ercot.get_spp(
    start="yesterday",
    market=Market.REAL_TIME_15_MIN,
    location_type=LocationType.LOAD_ZONE,
)

# Get day-ahead LMP
df = ercot.get_lmp(
    start="2024-01-15",
    market=Market.DAY_AHEAD_HOURLY,
)

# Get ancillary service prices
df = ercot.get_as_prices(start="yesterday")

# Get wind and solar forecasts
wind = ercot.get_wind_forecast(start="today")
solar = ercot.get_solar_forecast(by_region=True)
```

### Load and Forecast Data

```python
from tinygrid import ERCOT

ercot = ERCOT()

# Get actual system load
load = ercot.get_load(start="today", by="weather_zone")

# Get wind forecast
wind = ercot.get_wind_forecast(start="today")

# Get solar forecast
solar = ercot.get_solar_forecast(start="today")

# Get load forecast (direct endpoint)
forecast = ercot.get_load_forecast_by_weather_zone(
    start_date="2024-12-28",
    end_date="2024-12-29",
)
```

### Historical Yearly Data

Access complete yearly historical data from ERCOT's MIS document system:

```python
from tinygrid import ERCOT

ercot = ERCOT()

# Get full year of RTM settlement point prices
rtm_2023 = ercot.get_rtm_spp_historical(2023)

# Get full year of DAM settlement point prices
dam_2023 = ercot.get_dam_spp_historical(2023)

# Get settlement point mapping
mapping = ercot.get_settlement_point_mapping()
```

### Direct Endpoint Access

For full control over API parameters:

```python
from tinygrid import ERCOT, ERCOTAuth, ERCOTAuthConfig

# Set up authentication
auth = ERCOTAuth(ERCOTAuthConfig(
    username="your-email@example.com",
    password="your-password",
    subscription_key="your-key",
))

ercot = ERCOT(auth=auth)

# Call endpoints directly
load_data = ercot.get_actual_system_load_by_weather_zone(
    operating_day_from="2024-12-20",
    operating_day_to="2024-12-20",
    size=24,
)
```

## API Reference

### Unified Methods

| Method | Description |
|--------|-------------|
| `get_spp()` | Settlement Point Prices |
| `get_lmp()` | Locational Marginal Prices |
| `get_as_prices()` | Ancillary Services MCPC prices |
| `get_as_plan()` | Ancillary Services plan |
| `get_wind_forecast()` | Wind power forecast |
| `get_solar_forecast()` | Solar power forecast |
| `get_load()` | Actual system load |
| `get_shadow_prices()` | Transmission constraint shadow prices |

### Load and Forecast Methods

| Method | Description |
|--------|-------------|
| `get_load()` | Actual system load by zone |
| `get_wind_forecast()` | Wind power forecast |
| `get_solar_forecast()` | Solar power forecast |
| `get_load_forecast_by_weather_zone()` | Load forecast |

### Historical Methods

| Method | Description |
|--------|-------------|
| `get_rtm_spp_historical(year)` | Full year RTM SPP |
| `get_dam_spp_historical(year)` | Full year DAM SPP |
| `get_settlement_point_mapping()` | Settlement point mapping |
