# ERCOT Authentication

The Tiny Grid SDK provides built-in authentication support for the ERCOT API.

## Overview

ERCOT API uses Azure B2C authentication and requires:
1. **Subscription Key** - Obtained from [ERCOT API Explorer](https://apiexplorer.ercot.com/) after subscribing to API products
2. **ID Token** - Generated using username/password via Azure B2C ROPC flow, valid for 1 hour

The SDK handles token generation, caching, and automatic refresh using the Azure B2C endpoint.

## Usage

### Basic Authentication

```python
from tinygrid import ERCOT, ERCOTAuth, ERCOTAuthConfig

# Create authentication configuration
auth_config = ERCOTAuthConfig(
    username="your-email@example.com",
    password="your-password",
    subscription_key="your-subscription-key",
)

# Create authentication handler
auth = ERCOTAuth(auth_config)

# Create ERCOT client with authentication
ercot = ERCOT(auth=auth)

# Use the client - authentication is handled automatically
forecast = ercot.get_load_forecast_by_weather_zone(
    start_date="2024-01-01",
    end_date="2024-01-07",
)
```

### Using Environment Variables

```python
import os
from dotenv import load_dotenv
from tinygrid import ERCOT, ERCOTAuth, ERCOTAuthConfig

load_dotenv()

auth_config = ERCOTAuthConfig(
    username=os.getenv("ERCOT_USERNAME"),
    password=os.getenv("ERCOT_PASSWORD"),
    subscription_key=os.getenv("ERCOT_SUBSCRIPTION_KEY"),
)

ercot = ERCOT(auth=ERCOTAuth(auth_config))
```

## Token Management

- Tokens are automatically cached and reused
- Tokens are refreshed automatically when expired (default: refresh at 55 minutes)
- Token cache can be cleared with `auth.clear_token_cache()`

## Error Handling

```python
from tinygrid import GridAuthenticationError

try:
    ercot = ERCOT(auth=auth)
    data = ercot.get_load_forecast_by_weather_zone(...)
except GridAuthenticationError as e:
    print(f"Authentication failed: {e.message}")
    print(f"Status code: {e.status_code}")
```

## Getting ERCOT API Credentials

1. Register at [ERCOT API Explorer](https://apiexplorer.ercot.com/)
2. Subscribe to the API products you need
3. Copy your subscription key
4. Use your email and password for authentication

## Security Best Practices

- ✅ Store credentials in `.env` file (never commit to git)
- ✅ Use environment variables in production
- ✅ Rotate credentials regularly
- ✅ Enable MFA on your ERCOT account
- ❌ Never hardcode credentials in source code
- ❌ Never commit `.env` files to version control

