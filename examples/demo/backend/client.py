"""ERCOT client singleton for the demo app."""

import os

from dotenv import load_dotenv

from tinygrid import ERCOT, ERCOTAuth, ERCOTAuthConfig

# Load environment variables from .env file
load_dotenv()

# Global ERCOT client instance
_ercot_client: ERCOT | None = None


def _create_auth() -> ERCOTAuth | None:
    """Create auth config from environment variables if available."""
    username = os.getenv("ERCOT_USERNAME")
    password = os.getenv("ERCOT_PASSWORD")
    subscription_key = os.getenv("ERCOT_SUBSCRIPTION_KEY")

    if username and password and subscription_key:
        print(f"Configuring ERCOT auth for user: {username}")
        config = ERCOTAuthConfig(
            username=username,
            password=password,
            subscription_key=subscription_key,
        )
        return ERCOTAuth(config)

    print("No ERCOT credentials found - using unauthenticated mode")
    return None


def get_ercot() -> ERCOT:
    """Get the global ERCOT client instance."""
    global _ercot_client
    if _ercot_client is None:
        auth = _create_auth()
        _ercot_client = ERCOT(auth=auth, rate_limit_enabled=True)
    return _ercot_client


def initialize_client() -> None:
    """Initialize the ERCOT client."""
    global _ercot_client
    auth = _create_auth()
    _ercot_client = ERCOT(auth=auth, rate_limit_enabled=True)


def cleanup_client() -> None:
    """Cleanup the ERCOT client."""
    global _ercot_client
    _ercot_client = None
