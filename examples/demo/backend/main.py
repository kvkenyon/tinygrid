"""TinyGrid Demo - FastAPI Backend.

This backend demonstrates the TinyGrid SDK's features through a REST API
that powers a React frontend dashboard.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any

from client import cleanup_client, initialize_client
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import (
    dashboard_router,
    forecasts_router,
    historical_router,
    prices_router,
)
from routes.prices import prefetch_all_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Initialize ERCOT client on startup
    initialize_client()
    # Prefetch all cacheable data in background thread - don't block event loop
    # This allows the server to start accepting requests immediately
    ref = asyncio.create_task(asyncio.to_thread(prefetch_all_data))
    yield
    # Wait for prefetch task to complete before shutdown
    await ref
    # Cleanup on shutdown
    cleanup_client()


app = FastAPI(
    title="TinyGrid Demo API",
    description="A demo API showcasing the TinyGrid SDK for accessing ERCOT grid data",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(dashboard_router, prefix="/api", tags=["Dashboard"])
app.include_router(prices_router, prefix="/api", tags=["Prices"])
app.include_router(forecasts_router, prefix="/api", tags=["Forecasts"])
app.include_router(historical_router, prefix="/api", tags=["Historical"])


@app.get("/")
def root() -> dict[str, Any]:
    """Root endpoint with API information."""
    return {
        "name": "TinyGrid Demo API",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": {
            "dashboard": [
                "/api/status",
                "/api/fuel-mix",
                "/api/renewable",
                "/api/supply-demand",
            ],
            "prices": [
                "/api/spp",
                "/api/lmp",
                "/api/lmp-grid",
                "/api/spp-grid",
                "/api/daily-prices",
            ],
            "forecasts": [
                "/api/load",
                "/api/wind-forecast",
                "/api/solar-forecast",
            ],
            "historical": ["/api/historical"],
        },
    }


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
