"""Tiny Grid - A unified Python SDK for accessing grid data from all major US ISOs"""

from .auth import ERCOTAuth, ERCOTAuthConfig
from .constants import LocationType, Market, SettlementPointType
from .ercot import ERCOT, ERCOTArchive
from .errors import (
    GridAPIError,
    GridAuthenticationError,
    GridError,
    GridRateLimitError,
    GridRetryExhaustedError,
    GridTimeoutError,
)

# Backward compatibility - also export from historical
from .historical import ERCOTArchive as _ERCOTArchiveLegacy

__version__ = "0.1.0"

__all__ = (
    # Client
    "ERCOT",
    # Historical
    "ERCOTArchive",
    # Auth
    "ERCOTAuth",
    "ERCOTAuthConfig",
    "GridAPIError",
    "GridAuthenticationError",
    # Errors
    "GridError",
    "GridRateLimitError",
    "GridRetryExhaustedError",
    "GridTimeoutError",
    "LocationType",
    # Constants/Enums
    "Market",
    "SettlementPointType",
)
