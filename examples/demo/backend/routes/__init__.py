"""API routes for the TinyGrid demo backend."""

from .dashboard import router as dashboard_router
from .forecasts import router as forecasts_router
from .historical import router as historical_router
from .prices import router as prices_router

__all__ = [
    "dashboard_router",
    "forecasts_router",
    "historical_router",
    "prices_router",
]
