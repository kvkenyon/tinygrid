"""Prices routes - SPP and LMP endpoints.

These endpoints provide access to ERCOT settlement point prices and
locational marginal prices.
"""

import asyncio
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
# Comprehensive Caching Strategy
# ============================================================================
# - Day-Ahead data: Cached for the entire day (doesn't change after publication)
# - Real-Time data: Incremental append-only caching
#   - First request: fetch from 00:00 to now
#   - Subsequent requests: fetch only new data since last fetch, append to cache
#   - Reset at midnight (date change)

_cache_lock = Lock()
_cache: dict[str, Any] = {
    # Day-Ahead SPP (cached all day)
    "da_spp": {
        "date": None,
        "data": None,
        "locations": [],
    },
    # Real-Time SPP (append-only incremental)
    "rt_spp": {
        "date": None,
        "last_time": None,  # Last timestamp fetched
        "data": None,  # Accumulated DataFrame
    },
    # Real-Time LMP (append-only incremental)
    "rt_lmp": {
        "date": None,
        "last_time": None,
        "data": None,
    },
}

# All supported locations for filtering
ALL_LOCATIONS = set(LOAD_ZONES) | set(TRADING_HUBS) | set(DC_TIES)


def _get_ct_timezone():
    """Get Central Time timezone."""
    return pytz.timezone("America/Chicago")


def _get_today_date() -> str:
    """Get today's date string in CT timezone."""
    return datetime.now(_get_ct_timezone()).strftime("%Y-%m-%d")


def _get_current_timestamp() -> str:
    """Get current timestamp in CT timezone as ISO format."""
    return datetime.now(_get_ct_timezone()).strftime("%Y-%m-%dT%H:%M")


def _find_loc_column(df: pd.DataFrame) -> str | None:
    """Find the location column in a DataFrame."""
    for col in [
        "Location",
        "Settlement Point",
        "SettlementPoint",
        "SettlementPointName",
    ]:
        if col in df.columns:
            return col
    return None


def _find_time_column(
    df: pd.DataFrame, candidates: list[str] | None = None
) -> str | None:
    """Find the time column in a DataFrame."""
    if candidates is None:
        candidates = ["Time", "SCED Time Stamp", "Timestamp", "Hour Ending"]
    for col in candidates:
        if col in df.columns:
            return col
    return None


async def _get_cached_da_spp() -> tuple[pd.DataFrame | None, list[str]]:
    """Get cached Day-Ahead SPP data, fetching if needed.

    Note: We use SPP for Day-Ahead because DA LMP returns electrical buses,
    while we want settlement points (load zones, trading hubs, DC ties).

    Returns:
        Tuple of (DataFrame, locations list)
    """
    today = _get_today_date()
    cache = _cache["da_spp"]

    with _cache_lock:
        # Check if cache is valid for today
        if cache["date"] == today and cache["data"] is not None:
            return cache["data"], cache["locations"]

    # Cache miss or stale - fetch fresh data
    try:
        ercot = get_ercot()

        # Fetch Day-Ahead SPP for today (has settlement points like LZ_*, HB_*, DC_*)
        da_df = await ercot.get_spp_async(
            start="today",
            market=Market.DAY_AHEAD_HOURLY,
        )

        if da_df.empty:
            return None, []

        # Find location column and filter to supported locations
        loc_col = _find_loc_column(da_df)
        if loc_col:
            da_df = da_df[da_df[loc_col].isin(ALL_LOCATIONS)]
            locations = sorted(da_df[loc_col].unique().tolist())
        else:
            locations = []

        # Update cache
        with _cache_lock:
            cache["date"] = today
            cache["data"] = da_df.copy()
            cache["locations"] = locations

        return da_df, locations

    except Exception:
        # Return empty on error - we'll show RT data only
        return None, []


async def _get_cached_rt_lmp() -> pd.DataFrame:
    """Get cached Real-Time LMP data with incremental fetching.

    First request: fetches from 00:00 to now
    Subsequent requests: fetches only new data since last fetch, appends to cache
    Resets at midnight (date change)

    Returns:
        DataFrame with RT LMP data for today (filtered to supported locations)
    """
    today = _get_today_date()
    cache = _cache["rt_lmp"]
    ct = _get_ct_timezone()
    now = datetime.now(ct)

    with _cache_lock:
        # Check if we need to reset cache (new day)
        if cache["date"] != today:
            cache["date"] = today
            cache["last_time"] = None
            cache["data"] = None

        cached_df = cache["data"]
        last_time = cache["last_time"]

    try:
        ercot = get_ercot()

        if last_time is None:
            # First fetch: get all data from midnight to now
            start_ts = now.strftime("%Y-%m-%dT00:00")
        else:
            # Incremental fetch: get data from last_time to now
            start_ts = last_time

        # Fetch RT LMP data
        new_df = await ercot.get_lmp_async(
            start=start_ts,
            market=Market.REAL_TIME_SCED,
        )

        if new_df.empty:
            return cached_df if cached_df is not None else pd.DataFrame()

        # Filter to supported locations
        loc_col = _find_loc_column(new_df)
        if loc_col:
            new_df = new_df[new_df[loc_col].isin(ALL_LOCATIONS)]

        # Find latest timestamp in new data
        time_col = _find_time_column(new_df)
        new_last_time = None
        if time_col and not new_df.empty:
            times = new_df[time_col].astype(str)
            new_last_time = times.max()

        # Merge with cached data
        with _cache_lock:
            if cached_df is not None and not cached_df.empty:
                # Append new data, drop duplicates
                combined = pd.concat([cached_df, new_df], ignore_index=True)
                # Deduplicate based on time and location
                if time_col and loc_col:
                    combined = combined.drop_duplicates(
                        subset=[time_col, loc_col], keep="last"
                    )
                cache["data"] = combined
            else:
                cache["data"] = new_df.copy()

            if new_last_time:
                cache["last_time"] = new_last_time

            return cache["data"]

    except Exception:
        return cached_df if cached_df is not None else pd.DataFrame()


async def _get_cached_rt_spp() -> pd.DataFrame:
    """Get cached Real-Time SPP data with incremental fetching.

    First request: fetches from 00:00 to now
    Subsequent requests: fetches only new data since last fetch, appends to cache
    Resets at midnight (date change)

    Returns:
        DataFrame with RT SPP data for today (filtered to supported locations)
    """
    today = _get_today_date()
    cache = _cache["rt_spp"]
    ct = _get_ct_timezone()
    now = datetime.now(ct)

    with _cache_lock:
        # Check if we need to reset cache (new day)
        if cache["date"] != today:
            cache["date"] = today
            cache["last_time"] = None
            cache["data"] = None

        cached_df = cache["data"]
        last_time = cache["last_time"]

    try:
        ercot = get_ercot()

        if last_time is None:
            # First fetch: get all data from midnight to now
            start_ts = now.strftime("%Y-%m-%dT00:00")
        else:
            # Incremental fetch: get data from last_time to now
            start_ts = last_time

        # Fetch RT SPP data
        new_df = await ercot.get_spp_async(
            start=start_ts,
            market=Market.REAL_TIME_15_MIN,
        )

        if new_df.empty:
            return cached_df if cached_df is not None else pd.DataFrame()

        # Filter to supported locations
        loc_col = _find_loc_column(new_df)
        if loc_col:
            new_df = new_df[new_df[loc_col].isin(ALL_LOCATIONS)]

        # Find latest timestamp in new data
        time_col = _find_time_column(new_df)
        new_last_time = None
        if time_col and not new_df.empty:
            times = new_df[time_col].astype(str)
            new_last_time = times.max()

        # Merge with cached data
        with _cache_lock:
            if cached_df is not None and not cached_df.empty:
                # Append new data, drop duplicates
                combined = pd.concat([cached_df, new_df], ignore_index=True)
                # Deduplicate based on time and location
                if time_col and loc_col:
                    combined = combined.drop_duplicates(
                        subset=[time_col, loc_col], keep="last"
                    )
                cache["data"] = combined
            else:
                cache["data"] = new_df.copy()

            if new_last_time:
                cache["last_time"] = new_last_time

            return cache["data"]

    except Exception:
        return cached_df if cached_df is not None else pd.DataFrame()


def prefetch_all_data() -> None:
    """Prefetch all cacheable data on startup.

    Call this on app startup to warm all caches:
    - DA SPP for today
    - RT LMP from 00:00 to now
    - RT SPP from 00:00 to now
    """
    # Note: prefetch_all_data is called from a synchronous context in main.py
    # using asyncio.create_task(asyncio.to_thread(prefetch_all_data))
    # Since we've updated the _get_cached_* functions to be async,
    # we need to run them in an event loop here if called synchronously

    # However, since this is running in a thread (via to_thread), we can create a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(
            asyncio.gather(
                _get_cached_da_spp(), _get_cached_rt_lmp(), _get_cached_rt_spp()
            )
        )
    finally:
        loop.close()


# Keep old function name for backwards compatibility
def prefetch_da_lmp() -> None:
    """Prefetch Day-Ahead SPP data for today (legacy function).

    Use prefetch_all_data() instead for complete cache warming.
    """
    prefetch_all_data()


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
async def get_spp(
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

        # Use new async SDK method
        ercot = get_ercot()
        df = await ercot.get_spp_async(
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
async def get_lmp(
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

        # Use new async SDK method
        ercot = get_ercot()
        df = await ercot.get_lmp_async(
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


@router.get("/lmp-combined", response_model=LMPCombinedResponse)
async def get_lmp_combined(
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
    - Real-Time: Uses cached LMP data with incremental updates
    - Day-Ahead: Uses cached SPP data (published once daily)

    Both caches are warmed on startup and updated incrementally.
    """
    try:
        # Determine which locations to filter by
        if location_type == "load_zone":
            type_locations = set(LOAD_ZONES)
        elif location_type == "trading_hub":
            type_locations = set(TRADING_HUBS)
        elif location_type == "dc_tie":
            type_locations = set(DC_TIES)
        else:
            type_locations = set(LOAD_ZONES)

        # Get cached RT LMP data (incremental) - direct await since it's now async
        rt_df = await _get_cached_rt_lmp()

        # Filter RT data by location type
        if not rt_df.empty:
            loc_col = _find_loc_column(rt_df)
            if loc_col:
                rt_df = rt_df[rt_df[loc_col].isin(type_locations)]

        # Get cached Day-Ahead SPP data - direct await since it's now async
        da_df, _all_da_locations = await _get_cached_da_spp()

        # Filter DA data by location type
        if da_df is not None and not da_df.empty:
            loc_col = _find_loc_column(da_df)
            if loc_col:
                da_df = da_df[da_df[loc_col].isin(type_locations)]

        # Get unique locations for this type
        locations_in_type = set()
        if not rt_df.empty:
            loc_col = _find_loc_column(rt_df)
            if loc_col:
                locations_in_type.update(rt_df[loc_col].unique())
        if da_df is not None and not da_df.empty:
            loc_col = _find_loc_column(da_df)
            if loc_col:
                locations_in_type.update(da_df[loc_col].unique())

        locations_list = sorted(locations_in_type)

        # Filter by specific location if provided
        if location:
            if not rt_df.empty:
                loc_col = _find_loc_column(rt_df)
                if loc_col:
                    rt_df = rt_df[rt_df[loc_col] == location]
            if da_df is not None and not da_df.empty:
                loc_col = _find_loc_column(da_df)
                if loc_col:
                    da_df = da_df[da_df[loc_col] == location]

        # Build combined data structure
        combined_data = []

        # Process RT data (LMP uses "Time" or "SCED Time Stamp")
        latest_rt_time = None
        if not rt_df.empty:
            loc_col = _find_loc_column(rt_df)
            time_col = _find_time_column(
                rt_df, ["Time", "SCED Time Stamp", "Timestamp"]
            )

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
            loc_col = _find_loc_column(da_df)
            time_col = _find_time_column(da_df, ["Time", "Hour Ending", "Timestamp"])

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
async def get_daily_prices() -> dict[str, Any]:
    """Get daily price summary from ERCOT dashboard.

    Returns the daily price summary including peak and average prices.
    This endpoint uses dashboard data and does not require authentication.
    """
    try:
        # Currently daily prices isn't asyncified in api.py, so we use to_thread
        # but if get_daily_prices was available async we'd use it.
        # However, checking api.py, get_daily_prices is not in the mixin yet.
        # It's likely in ercot/dashboard.py. Let's assume sync for now.

        # Actually, let's just keep using to_thread for this one as it's not in our list of async methods
        def _fetch_daily_prices_sync() -> pd.DataFrame:
            ercot = get_ercot()
            return ercot.get_daily_prices()

        df = await asyncio.to_thread(_fetch_daily_prices_sync)

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


# ============================================================================
# Grid Endpoints - Optimized for mini-chart grid display
# ============================================================================


class LocationPriceData(BaseModel):
    """Price data for a single location."""

    location: str
    location_type: str  # "load_zone", "trading_hub", or "dc_tie"
    data: list[dict[str, Any]]  # Time series data
    latest_price: float | None = None
    latest_time: str | None = None
    avg_price: float | None = None
    min_price: float | None = None
    max_price: float | None = None


class PriceGridResponse(BaseModel):
    """Response model for grid endpoints."""

    locations: list[LocationPriceData]
    latest_update: str | None = None
    count: int
    start_date: str
    end_date: str | None = None


def _get_location_type(loc: str) -> str:
    """Determine the location type for a given location name."""
    if loc in LOAD_ZONES:
        return "load_zone"
    elif loc in TRADING_HUBS:
        return "trading_hub"
    elif loc in DC_TIES:
        return "dc_tie"
    return "unknown"


def _calculate_stats(prices: list[float]) -> dict[str, float | None]:
    """Calculate statistics for a list of prices."""
    if not prices:
        return {"avg": None, "min": None, "max": None}
    return {
        "avg": sum(prices) / len(prices),
        "min": min(prices),
        "max": max(prices),
    }


def _parse_date_range(start: str, end: str | None) -> tuple[str, str]:
    """Parse and validate date range (max 7 days)."""
    ct = _get_ct_timezone()
    today = datetime.now(ct).date()

    # Parse start date
    if start == "today":
        start_date = today
    elif start == "yesterday":
        start_date = today - pd.Timedelta(days=1)
    else:
        try:
            start_date = pd.to_datetime(start).date()
        except Exception:
            start_date = today

    # Parse end date
    if end is None or end == "today":
        end_date = today
    else:
        try:
            end_date = pd.to_datetime(end).date()
        except Exception:
            end_date = today

    # Ensure max 7 days range
    max_range = pd.Timedelta(days=7)
    if (end_date - start_date) > max_range:
        start_date = end_date - max_range

    return str(start_date), str(end_date)


async def _fetch_lmp_grid_data(start_date: str, end_date: str) -> pd.DataFrame:
    """Async helper to fetch LMP grid data."""
    is_today_only = start_date == end_date == _get_today_date()

    if is_today_only:
        return await _get_cached_rt_lmp()

    ercot = get_ercot()
    df = await ercot.get_lmp_async(
        start=start_date,
        end=end_date,
        market=Market.REAL_TIME_SCED,
    )
    # Filter to supported locations
    loc_col = _find_loc_column(df)
    if loc_col and not df.empty:
        df = df[df[loc_col].isin(ALL_LOCATIONS)]
    return df


@router.get("/lmp-grid", response_model=PriceGridResponse)
async def get_lmp_grid(
    start: str = Query(
        default="today",
        description="Start date (YYYY-MM-DD, 'today', or 'yesterday')",
    ),
    end: str | None = Query(
        default=None,
        description="End date (YYYY-MM-DD, defaults to today)",
    ),
) -> dict[str, Any]:
    """Get LMP data for all locations, optimized for grid display.

    Returns LMP data grouped by location with summary statistics.
    Supports date ranges up to 7 days.
    Uses cached data when available for better performance.
    """
    try:
        start_date, end_date = _parse_date_range(start, end)

        # Run async data fetch directly
        df = await _fetch_lmp_grid_data(start_date, end_date)

        if df.empty:
            return {
                "locations": [],
                "latest_update": None,
                "count": 0,
                "start_date": start_date,
                "end_date": end_date,
            }

        loc_col = _find_loc_column(df)
        time_col = _find_time_column(df, ["Time", "SCED Time Stamp", "Timestamp"])
        price_col = "Price" if "Price" in df.columns else "LMP"

        # Group by location
        locations_data = []
        latest_update = None

        for loc in sorted(df[loc_col].unique()):
            loc_df = df[df[loc_col] == loc].copy()

            # Sort by time
            if time_col:
                loc_df = loc_df.sort_values(time_col)

            # Build time series data
            time_series = []
            prices = []
            latest_time = None
            latest_price = None

            for _, row in loc_df.iterrows():
                time_val = str(row.get(time_col, "")) if time_col else ""
                price_val = float(row.get(price_col, 0))

                time_series.append(
                    {
                        "time": time_val,
                        "price": price_val,
                    }
                )
                prices.append(price_val)

                if time_val and (latest_time is None or time_val > latest_time):
                    latest_time = time_val
                    latest_price = price_val

            if latest_time and (latest_update is None or latest_time > latest_update):
                latest_update = latest_time

            stats = _calculate_stats(prices)

            locations_data.append(
                {
                    "location": loc,
                    "location_type": _get_location_type(loc),
                    "data": time_series,
                    "latest_price": latest_price,
                    "latest_time": latest_time,
                    "avg_price": stats["avg"],
                    "min_price": stats["min"],
                    "max_price": stats["max"],
                }
            )

        return {
            "locations": locations_data,
            "latest_update": latest_update,
            "count": len(df),
            "start_date": start_date,
            "end_date": end_date,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch LMP grid data: {e}"
        )


async def _fetch_spp_grid_data(
    start_date: str, end_date: str, market: str
) -> pd.DataFrame:
    """Async helper to fetch SPP grid data."""
    is_today_only = start_date == end_date == _get_today_date()

    if is_today_only:
        if market == "day_ahead_hourly":
            df, _ = await _get_cached_da_spp()
            return df if df is not None else pd.DataFrame()
        else:
            return await _get_cached_rt_spp()

    ercot = get_ercot()
    market_enum = (
        Market.REAL_TIME_15_MIN
        if market == "real_time_15_min"
        else Market.DAY_AHEAD_HOURLY
    )
    df = await ercot.get_spp_async(
        start=start_date,
        end=end_date,
        market=market_enum,
    )
    # Filter to supported locations
    loc_col = _find_loc_column(df)
    if loc_col and not df.empty:
        df = df[df[loc_col].isin(ALL_LOCATIONS)]
    return df


@router.get("/spp-grid", response_model=PriceGridResponse)
async def get_spp_grid(
    start: str = Query(
        default="today",
        description="Start date (YYYY-MM-DD, 'today', or 'yesterday')",
    ),
    end: str | None = Query(
        default=None,
        description="End date (YYYY-MM-DD, defaults to today)",
    ),
    market: Literal["real_time_15_min", "day_ahead_hourly"] = Query(
        default="real_time_15_min",
        description="Market type",
    ),
) -> dict[str, Any]:
    """Get SPP data for all locations, optimized for grid display.

    Returns SPP data grouped by location with summary statistics.
    Supports date ranges up to 7 days.
    Uses cached data when available for better performance.
    """
    try:
        start_date, end_date = _parse_date_range(start, end)

        # Run async data fetch directly
        df = await _fetch_spp_grid_data(start_date, end_date, market)

        if df.empty:
            return {
                "locations": [],
                "latest_update": None,
                "count": 0,
                "start_date": start_date,
                "end_date": end_date,
            }

        loc_col = _find_loc_column(df)
        time_col = _find_time_column(df, ["Time", "Hour Ending", "Timestamp"])
        price_col = "Price" if "Price" in df.columns else "SettlementPointPrice"

        # Group by location
        locations_data = []
        latest_update = None

        for loc in sorted(df[loc_col].unique()):
            loc_df = df[df[loc_col] == loc].copy()

            # Sort by time
            if time_col:
                loc_df = loc_df.sort_values(time_col)

            # Build time series data
            time_series = []
            prices = []
            latest_time = None
            latest_price = None

            for _, row in loc_df.iterrows():
                time_val = str(row.get(time_col, "")) if time_col else ""
                price_val = float(row.get(price_col, 0))

                time_series.append(
                    {
                        "time": time_val,
                        "price": price_val,
                    }
                )
                prices.append(price_val)

                if time_val and (latest_time is None or time_val > latest_time):
                    latest_time = time_val
                    latest_price = price_val

            if latest_time and (latest_update is None or latest_time > latest_update):
                latest_update = latest_time

            stats = _calculate_stats(prices)

            locations_data.append(
                {
                    "location": loc,
                    "location_type": _get_location_type(loc),
                    "data": time_series,
                    "latest_price": latest_price,
                    "latest_time": latest_time,
                    "avg_price": stats["avg"],
                    "min_price": stats["min"],
                    "max_price": stats["max"],
                }
            )

        return {
            "locations": locations_data,
            "latest_update": latest_update,
            "count": len(df),
            "start_date": start_date,
            "end_date": end_date,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch SPP grid data: {e}"
        )
