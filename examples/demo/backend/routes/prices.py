"""Prices routes - SPP and LMP endpoints.

These endpoints provide access to ERCOT settlement point prices and
locational marginal prices.
"""

from datetime import datetime
from threading import Lock
from typing import Any, Literal

import pandas as pd
import pytz
from client import get_ercot
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from tinygrid import LocationType, Market
from tinygrid.constants.ercot import DC_TIES, LOAD_ZONES, TRADING_HUBS

router = APIRouter()

# ============================================================================
# Day-Ahead LMP Cache
# ============================================================================
# Day-Ahead prices don't change once published, so we cache them for the day.
# We prefetch all locations (load zones, hubs, DC ties) on first request.

_da_cache_lock = Lock()
_da_cache: dict[str, Any] = {
    "date": None,  # Date string for cache validity
    "data": None,  # Cached DataFrame
    "locations": [],  # List of all available locations
}


def _get_today_date() -> str:
    """Get today's date string in CT timezone."""
    ct = pytz.timezone("America/Chicago")
    return datetime.now(ct).strftime("%Y-%m-%d")


def _get_cached_da_spp() -> tuple[pd.DataFrame | None, list[str]]:
    """Get cached Day-Ahead SPP data, fetching if needed.

    Note: We use SPP for Day-Ahead because DA LMP returns electrical buses,
    while we want settlement points (load zones, trading hubs, DC ties).

    Returns:
        Tuple of (DataFrame, locations list)
    """
    today = _get_today_date()

    with _da_cache_lock:
        # Check if cache is valid for today
        if _da_cache["date"] == today and _da_cache["data"] is not None:
            return _da_cache["data"], _da_cache["locations"]

    # Cache miss or stale - fetch fresh data
    try:
        ercot = get_ercot()

        # Fetch Day-Ahead SPP for today (has settlement points like LZ_*, HB_*, DC_*)
        da_df = ercot.get_spp(
            start="today",
            market=Market.DAY_AHEAD_HOURLY,
        )

        if da_df.empty:
            return None, []

        # Filter to only load zones, trading hubs, and DC ties
        all_locations = set(LOAD_ZONES) | set(TRADING_HUBS) | set(DC_TIES)

        # Find location column
        loc_col = None
        for col in [
            "Location",
            "Settlement Point",
            "SettlementPoint",
            "SettlementPointName",
        ]:
            if col in da_df.columns:
                loc_col = col
                break

        if loc_col:
            da_df = da_df[da_df[loc_col].isin(all_locations)]
            locations = sorted(da_df[loc_col].unique().tolist())
        else:
            locations = []

        # Update cache
        with _da_cache_lock:
            _da_cache["date"] = today
            _da_cache["data"] = da_df.copy()
            _da_cache["locations"] = locations

        return da_df, locations

    except Exception:
        # Return empty on error - we'll show RT data only
        return None, []


def prefetch_da_lmp() -> None:
    """Prefetch Day-Ahead SPP data for today.

    Call this on app startup to warm the cache.
    We use SPP for DA because DA LMP returns electrical buses,
    while we want settlement points (load zones, hubs, DC ties).
    """
    _get_cached_da_spp()


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


class LMPCombinedResponse(BaseModel):
    """Response model for combined DA+RT LMP data."""

    data: list[dict[str, Any]]
    locations: list[str]
    latest_rt_time: str | None = None
    count: int


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Find the first matching column name from a list of candidates."""
    for col in candidates:
        if col in df.columns:
            return col
    return None


@router.get("/lmp-combined", response_model=LMPCombinedResponse)
def get_lmp_combined(
    location_type: Literal["load_zone", "trading_hub", "dc_tie"] = Query(
        default="load_zone",
        description="Location type: load_zone, trading_hub, or dc_tie",
    ),
    location: str | None = Query(
        default=None,
        description="Specific location to filter (e.g., LZ_WEST, HB_NORTH, DC_E)",
    ),
) -> dict[str, Any]:
    """Get combined Day-Ahead and Real-Time price data for today.

    Returns both DA (SPP) and RT (LMP) prices on the same timeline for comparison.
    - Real-Time: Uses LMP (Locational Marginal Prices) for SCED interval data
    - Day-Ahead: Uses SPP (Settlement Point Prices) since DA LMP is by electrical bus

    Day-Ahead data is cached for the day since it doesn't change.
    Real-Time data is fetched fresh up to the latest available interval.
    """
    try:
        ercot = get_ercot()
        ct = pytz.timezone("America/Chicago")
        now = datetime.now(ct)

        # Determine which locations to filter by
        if location_type == "load_zone":
            type_locations = set(LOAD_ZONES)
        elif location_type == "trading_hub":
            type_locations = set(TRADING_HUBS)
        elif location_type == "dc_tie":
            type_locations = set(DC_TIES)
        else:
            type_locations = set(LOAD_ZONES)

        # Use current timestamp to get latest RT data
        start_ts = now.strftime("%Y-%m-%dT00:00")

        # Fetch Real-Time LMP data (has node/zone/hub)
        rt_df = ercot.get_lmp(
            start=start_ts,
            market=Market.REAL_TIME_SCED,
        )

        # Filter RT data by location type
        if not rt_df.empty:
            loc_col = _find_column(
                rt_df, ["Location", "Settlement Point", "SettlementPoint"]
            )
            if loc_col:
                rt_df = rt_df[rt_df[loc_col].isin(type_locations)]

        # Get cached Day-Ahead SPP data (has settlement points)
        da_df, _all_da_locations = _get_cached_da_spp()

        # Filter DA data by location type
        if da_df is not None and not da_df.empty:
            loc_col = _find_column(
                da_df, ["Location", "Settlement Point", "SettlementPoint"]
            )
            if loc_col:
                da_df = da_df[da_df[loc_col].isin(type_locations)]

        # Get unique locations for this type
        locations_in_type = set()
        if not rt_df.empty:
            loc_col = _find_column(
                rt_df, ["Location", "Settlement Point", "SettlementPoint"]
            )
            if loc_col:
                locations_in_type.update(rt_df[loc_col].unique())
        if da_df is not None and not da_df.empty:
            loc_col = _find_column(
                da_df, ["Location", "Settlement Point", "SettlementPoint"]
            )
            if loc_col:
                locations_in_type.update(da_df[loc_col].unique())

        locations_list = sorted(locations_in_type)

        # Filter by specific location if provided
        if location:
            if not rt_df.empty:
                loc_col = _find_column(
                    rt_df, ["Location", "Settlement Point", "SettlementPoint"]
                )
                if loc_col:
                    rt_df = rt_df[rt_df[loc_col] == location]
            if da_df is not None and not da_df.empty:
                loc_col = _find_column(
                    da_df, ["Location", "Settlement Point", "SettlementPoint"]
                )
                if loc_col:
                    da_df = da_df[da_df[loc_col] == location]

        # Build combined data structure
        combined_data = []

        # Process RT data (LMP uses "Time" or "SCED Time Stamp")
        latest_rt_time = None
        if not rt_df.empty:
            loc_col = _find_column(
                rt_df, ["Location", "Settlement Point", "SettlementPoint"]
            )
            time_col = _find_column(rt_df, ["Time", "SCED Time Stamp", "Timestamp"])

            for _, row in rt_df.iterrows():
                time_val = row.get(time_col, "") if time_col else ""
                time_str = str(time_val) if time_val is not None else ""

                if time_str and time_str > (latest_rt_time or ""):
                    latest_rt_time = time_str

                combined_data.append(
                    {
                        "time": time_str,
                        "location": str(row.get(loc_col, "")) if loc_col else "",
                        "rt_price": float(row.get("Price", row.get("LMP", 0))),
                        "da_price": None,
                        "market": "RT",
                    }
                )

        # Process DA data (SPP uses "Time" or "Hour Ending")
        if da_df is not None and not da_df.empty:
            loc_col = _find_column(
                da_df, ["Location", "Settlement Point", "SettlementPoint"]
            )
            time_col = _find_column(da_df, ["Time", "Hour Ending", "Timestamp"])

            for _, row in da_df.iterrows():
                time_val = row.get(time_col, "") if time_col else ""
                time_str = str(time_val) if time_val is not None else ""

                combined_data.append(
                    {
                        "time": time_str,
                        "location": str(row.get(loc_col, "")) if loc_col else "",
                        "rt_price": None,
                        "da_price": float(
                            row.get("Price", row.get("SettlementPointPrice", 0))
                        ),
                        "market": "DA",
                    }
                )

        # Format latest RT time for display
        formatted_latest = None
        if latest_rt_time:
            try:
                # Handle various timestamp formats
                if "T" in latest_rt_time:
                    dt = datetime.fromisoformat(latest_rt_time.replace("Z", "+00:00"))
                else:
                    dt = datetime.fromisoformat(latest_rt_time)
                formatted_latest = dt.strftime("%H:%M CT")
            except Exception:
                formatted_latest = latest_rt_time

        return {
            "data": combined_data,
            "locations": locations_list,
            "latest_rt_time": formatted_latest,
            "count": len(combined_data),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch combined price data: {e}"
        )


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
