"""Tiny Grid - A unified Python SDK for accessing grid data from all major US ISOs"""

from .auth import ERCOTAuth, ERCOTAuthConfig
from .ercot import ERCOT
from .errors import GridAPIError, GridAuthenticationError, GridError, GridTimeoutError

__version__ = "0.1.0"

__all__ = (
    "ERCOT",
    "ERCOTAuth",
    "ERCOTAuthConfig",
    "GridError",
    "GridTimeoutError",
    "GridAPIError",
    "GridAuthenticationError",
)

