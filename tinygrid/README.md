# tinygrid

The SDK layer that wraps auto-generated API clients with a clean interface.

## Usage

```python
from tinygrid import ERCOT, ERCOTAuth, ERCOTAuthConfig

# With authentication
auth = ERCOTAuth(ERCOTAuthConfig(
    username="you@example.com",
    password="your-password",
    subscription_key="your-key",
))
ercot = ERCOT(auth=auth)

# Fetch data
data = ercot.get_actual_system_load_by_weather_zone(
    operating_day_from="2024-12-20",
    operating_day_to="2024-12-20",
    size=24,
)
```

## Context Manager

```python
with ERCOT(auth=auth) as ercot:
    data = ercot.get_load_forecast_by_weather_zone(
        start_date="2024-12-20",
        end_date="2024-12-27",
    )
```

## Error Types

- `GridError` - Base exception
- `GridAPIError` - API returned an error
- `GridAuthenticationError` - Auth failed
- `GridTimeoutError` - Request timed out
- `GridRateLimitError` - Rate limited

## Tests

```bash
pytest tests/
```
