# Tiny Grid Examples

This directory contains example notebooks demonstrating how to use the Tiny Grid SDK.

## Setup

1. **Install dependencies**:
   ```bash
   cd /path/to/tiny-grid
   uv sync --dev --all-extras
   ```

2. **Set up your credentials**:
   ```bash
   cp .env.example .env
   # Edit .env with your actual ERCOT credentials
   ```

3. **Get ERCOT API credentials**:
   - Register at [ERCOT API Explorer](https://apiexplorer.ercot.com/)
   - Subscribe to API products to get your subscription key
   - Use your email and password for authentication

4. **Run the notebook**:
   ```bash
   jupyter notebook ercot_example.ipynb
   ```

## Environment Variables

The `.env` file should contain:
- `ERCOT_USERNAME`: Your ERCOT API email/username
- `ERCOT_PASSWORD`: Your ERCOT API password
- `ERCOT_SUBSCRIPTION_KEY`: Your ERCOT API subscription key

**Important**: Never commit your `.env` file to version control!

## Troubleshooting Authentication

If you encounter a 404 error when authenticating:

1. **Verify your credentials** are correct in the `.env` file
2. **Check the authentication endpoint URL** - ERCOT may use different endpoints
3. **Run the debug script** to test different endpoint URLs:
   ```bash
   python examples/debug_auth.py
   ```
4. **Check ERCOT's API documentation** for the correct endpoint:
   https://developer.ercot.com/applications/pubapi/user-guide/registration-and-authentication/

If the default endpoint doesn't work, you can override it:
```python
from tinygrid import ERCOTAuth, ERCOTAuthConfig

auth_config = ERCOTAuthConfig(
    username=os.getenv("ERCOT_USERNAME"),
    password=os.getenv("ERCOT_PASSWORD"),
    subscription_key=os.getenv("ERCOT_SUBSCRIPTION_KEY"),
    auth_url="https://correct-endpoint-url.com/oauth2/v1/token",  # Override here
)
```

