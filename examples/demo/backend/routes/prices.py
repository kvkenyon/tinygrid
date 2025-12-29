"""Prices routes - SPP and LMP endpoints.

These endpoints provide access to ERCOT settlement point prices and
locational marginal prices.
"""

from typing import Any, Literal

from client import get_ercot
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from tinygrid import LocationType, Market

router = APIRouter()


class PriceRecord(BaseModel):
    """Single price record."""

    timestamp: str
    settlement_point: str | None = None
    price: float
    market: str | None = None


class SPPResponse(BaseModel):
    """Response model for SPP data."""

    data: list[dict[str, Any]]
    count: int
    market: str
    start_date: str
    end_date: str | None = None


class LMPResponse(BaseModel):
    """Response model for LMP data."""

    data: list[dict[str, Any]]
    count: int
    market: str
    location_type: str


class DailyPricesResponse(BaseModel):
    """Response model for daily prices."""

    data: list[dict[str, Any]]
    count: int


@router.get("/spp", response_model=SPPResponse)
def get_spp(
    start: str = Query(
        default="today",
        description="Start date (YYYY-MM-DD, 'today', or 'yesterday')",
    ),
    end: str | None = Query(default=None, description="End date (YYYY-MM-DD)"),
    market: Literal["real_time_15_min", "day_ahead_hourly"] = Query(
        default="real_time_15_min",
        description="Market type",
    ),
    location_type: Literal["load_zone", "trading_hub", "resource_node", "all"]
    | None = Query(
        default=None,
        description="Filter by location type",
    ),
    locations: str | None = Query(
        default=None,
        description="Comma-separated list of settlement points to filter",
    ),
) -> dict[str, Any]:
    """Get Settlement Point Prices.

    Returns SPP data for the specified date range and market type.
    Can filter by location type or specific settlement points.
    """
    try:
        ercot = get_ercot()

        # Map market string to enum
        market_enum = (
            Market.REAL_TIME_15_MIN
            if market == "real_time_15_min"
            else Market.DAY_AHEAD_HOURLY
        )

        # Map location type string to enum
        loc_type = None
        if location_type and location_type != "all":
            loc_map = {
                "load_zone": LocationType.LOAD_ZONE,
                "trading_hub": LocationType.TRADING_HUB,
                "resource_node": LocationType.RESOURCE_NODE,
            }
            loc_type = loc_map.get(location_type)

        # Parse locations list
        loc_list = None
        if locations:
            loc_list = [loc.strip() for loc in locations.split(",")]

        df = ercot.get_spp(
            start=start,
            end=end,
            market=market_enum,
            locations=loc_list,
            location_type=loc_type,
        )

        # Convert DataFrame to list of dicts
        data = df.to_dict(orient="records") if not df.empty else []

        return {
            "data": data,
            "count": len(data),
            "market": market,
            "start_date": start,
            "end_date": end,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch SPP data: {e}")


@router.get("/lmp", response_model=LMPResponse)
def get_lmp(
    start: str = Query(
        default="today",
        description="Start date (YYYY-MM-DD, 'today', or 'yesterday')",
    ),
    end: str | None = Query(default=None, description="End date (YYYY-MM-DD)"),
    market: Literal["real_time_sced", "day_ahead_hourly"] = Query(
        default="real_time_sced",
        description="Market type",
    ),
    location_type: Literal["resource_node", "electrical_bus"] = Query(
        default="resource_node",
        description="Location type for LMP data",
    ),
) -> dict[str, Any]:
    """Get Locational Marginal Prices.

    Returns LMP data for the specified date range, market, and location type.
    """
    try:
        ercot = get_ercot()

        # Map market string to enum
        market_enum = (
            Market.REAL_TIME_SCED
            if market == "real_time_sced"
            else Market.DAY_AHEAD_HOURLY
        )

        # Map location type string to enum
        loc_type = (
            LocationType.RESOURCE_NODE
            if location_type == "resource_node"
            else LocationType.ELECTRICAL_BUS
        )

        df = ercot.get_lmp(
            start=start,
            end=end,
            market=market_enum,
            location_type=loc_type,
        )

        # Convert DataFrame to list of dicts
        data = df.to_dict(orient="records") if not df.empty else []

        return {
            "data": data,
            "count": len(data),
            "market": market,
            "location_type": location_type,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch LMP data: {e}")


@router.get("/daily-prices", response_model=DailyPricesResponse)
def get_daily_prices() -> dict[str, Any]:
    """Get daily price summary from ERCOT dashboard.

    Returns the daily price summary including peak and average prices.
    This endpoint uses dashboard data and does not require authentication.
    """
    try:
        ercot = get_ercot()
        df = ercot.get_daily_prices()

        # Convert DataFrame to list of dicts
        data = df.to_dict(orient="records") if not df.empty else []

        return {
            "data": data,
            "count": len(data),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch daily prices: {e}"
        )
