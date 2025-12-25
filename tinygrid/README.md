# Tiny Grid SDK

The Tiny Grid SDK provides a clean, intuitive interface for accessing grid data from major US Independent System Operators (ISOs).

## Quick Start

### ERCOT

```python
from tinygrid import ERCOT

# Create an ERCOT client
ercot = ERCOT()

# Get load forecast by weather zone
forecast = ercot.get_load_forecast_by_weather_zone(
    start_date="2024-01-01",
    end_date="2024-01-07",
    model="WEATHERZONE"
)

# Access the forecast data
print(forecast)
```

### Using Context Managers

For better resource management, use the client as a context manager:

```python
from tinygrid import ERCOT

with ERCOT() as ercot:
    forecast = ercot.get_load_forecast_by_weather_zone(
        start_date="2024-01-01",
        end_date="2024-01-07"
    )
```

### Error Handling

The SDK provides clean error handling:

```python
from tinygrid import ERCOT, GridAPIError, GridTimeoutError

ercot = ERCOT()

try:
    forecast = ercot.get_load_forecast_by_weather_zone(
        start_date="2024-01-01",
        end_date="2024-01-07"
    )
except GridAPIError as e:
    print(f"API error: {e.message}")
    print(f"Status code: {e.status_code}")
except GridTimeoutError as e:
    print(f"Request timed out after {e.timeout} seconds")
```

## Architecture

The SDK is built on top of auto-generated API clients (`pyercot`, etc.) and provides:

- **Clean method names** - No need to know endpoint paths or API categories
- **Unified error handling** - Consistent error types across all ISOs
- **Automatic client management** - No need to manage client lifecycle manually
- **Type safety** - Full type hints for better IDE support

## Development

### Running Tests

```bash
pytest
```

### Running Tests with Coverage

```bash
pytest --cov=tinygrid --cov-report=html
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy tinygrid
```

