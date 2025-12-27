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

### Unified API Demo (Notebook)

The `unified_api_demo.ipynb` notebook demonstrates the new unified API with:

- **Type-safe enums** (`Market`, `LocationType`) for IDE autocomplete
- **Date parsing** with "today", "yesterday", "latest" keywords
- **Unified methods** like `get_spp()`, `get_lmp()`, `get_as_prices()`
- **Location filtering** by Load Zone, Trading Hub, or Resource Node

```bash
# Run with Jupyter
uv run jupyter notebook examples/unified_api_demo.ipynb
```

### Python Scripts

```bash
# Basic ERCOT demo
uv run python examples/ercot_demo.py

# Validate all endpoints
uv run python examples/validate_all_endpoints.py
```

## Quick Start

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
```
