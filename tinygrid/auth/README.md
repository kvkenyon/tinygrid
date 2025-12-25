# ERCOT Authentication

ERCOT uses Azure B2C for authentication. You need:

1. **Subscription Key** - from [ERCOT API Explorer](https://apiexplorer.ercot.com/)
2. **Username/Password** - your ERCOT account credentials

## Usage

```python
from tinygrid import ERCOT, ERCOTAuth, ERCOTAuthConfig

auth = ERCOTAuth(ERCOTAuthConfig(
    username="you@example.com",
    password="your-password",
    subscription_key="your-key",
))

ercot = ERCOT(auth=auth)
data = ercot.get_actual_system_load_by_weather_zone(...)
```

## With Environment Variables

```python
import os
from dotenv import load_dotenv
from tinygrid import ERCOT, ERCOTAuth, ERCOTAuthConfig

load_dotenv()

auth = ERCOTAuth(ERCOTAuthConfig(
    username=os.getenv("ERCOT_USERNAME"),
    password=os.getenv("ERCOT_PASSWORD"),
    subscription_key=os.getenv("ERCOT_SUBSCRIPTION_KEY"),
))

ercot = ERCOT(auth=auth)
```

## Token Handling

- Tokens are cached automatically
- Tokens refresh before expiry (at 55 min of 60 min lifetime)
- Call `auth.clear_token_cache()` to force re-authentication

## Errors

```python
from tinygrid import GridAuthenticationError

try:
    ercot = ERCOT(auth=auth)
    data = ercot.get_load_forecast_by_weather_zone(...)
except GridAuthenticationError as e:
    print(f"Auth failed: {e.message}")
```
