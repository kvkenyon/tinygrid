"""Historical routes - Archive data access endpoints.

These endpoints provide access to ERCOT historical data through the
archive API for data older than 90 days.
"""

from typing import Any, Literal

from client import get_ercot
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()

# Available endpoints for historical data
AVAILABLE_ENDPOINTS = {
    "spp_node_zone_hub": "/np6-905-cd/spp_node_zone_hub",
    "lmp_node_zone_hub": "/np6-788-cd/lmp_node_zone_hub",
    "lmp_electrical_bus": "/np6-787-cd/lmp_electrical_bus",
    "dam_stlmnt_pnt_prices": "/np4-190-cd/dam_stlmnt_pnt_prices",
    "dam_hourly_lmp": "/np4-183-cd/dam_hourly_lmp",
    "dam_clear_price_for_cap": "/np4-188-cd/dam_clear_price_for_cap",
    "dam_shadow_prices": "/np4-191-cd/dam_shadow_prices",
    "act_sys_load_by_wzn": "/np6-345-cd/act_sys_load_by_wzn",
    "act_sys_load_by_fzn": "/np6-346-cd/act_sys_load_by_fzn",
    "wpp_hrly_avrg_actl_fcast": "/np4-732-cd/wpp_hrly_avrg_actl_fcast",
    "spp_hrly_avrg_actl_fcast": "/np4-737-cd/spp_hrly_avrg_actl_fcast",
}


class HistoricalResponse(BaseModel):
    """Response model for historical data."""

    data: list[dict[str, Any]]
    count: int
    endpoint: str
    start_date: str
    end_date: str


class EndpointInfo(BaseModel):
    """Information about an available endpoint."""

    name: str
    path: str
    description: str


class AvailableEndpointsResponse(BaseModel):
    """Response model for available endpoints."""

    endpoints: list[EndpointInfo]


ENDPOINT_DESCRIPTIONS = {
    "spp_node_zone_hub": "Real-time 15-minute settlement point prices",
    "lmp_node_zone_hub": "Real-time LMP by node/zone/hub",
    "lmp_electrical_bus": "Real-time LMP by electrical bus",
    "dam_stlmnt_pnt_prices": "Day-ahead settlement point prices",
    "dam_hourly_lmp": "Day-ahead hourly LMP",
    "dam_clear_price_for_cap": "Day-ahead ancillary service MCPC",
    "dam_shadow_prices": "Day-ahead shadow prices",
    "act_sys_load_by_wzn": "Actual system load by weather zone",
    "act_sys_load_by_fzn": "Actual system load by forecast zone",
    "wpp_hrly_avrg_actl_fcast": "Wind power production hourly forecast",
    "spp_hrly_avrg_actl_fcast": "Solar power production hourly forecast",
}


@router.get("/historical/endpoints", response_model=AvailableEndpointsResponse)
def get_available_endpoints() -> dict[str, Any]:
    """Get list of available historical endpoints.

    Returns a list of all endpoints that can be queried for historical data.
    """
    endpoints = []
    for name, path in AVAILABLE_ENDPOINTS.items():
        endpoints.append(
            {
                "name": name,
                "path": path,
                "description": ENDPOINT_DESCRIPTIONS.get(name, ""),
            }
        )

    return {"endpoints": endpoints}


@router.get("/historical", response_model=HistoricalResponse)
def get_historical(
    endpoint: Literal[
        "spp_node_zone_hub",
        "lmp_node_zone_hub",
        "lmp_electrical_bus",
        "dam_stlmnt_pnt_prices",
        "dam_hourly_lmp",
        "dam_clear_price_for_cap",
        "dam_shadow_prices",
        "act_sys_load_by_wzn",
        "act_sys_load_by_fzn",
        "wpp_hrly_avrg_actl_fcast",
        "spp_hrly_avrg_actl_fcast",
    ] = Query(description="Historical endpoint to query"),
    start: str = Query(description="Start date (YYYY-MM-DD)"),
    end: str = Query(description="End date (YYYY-MM-DD)"),
) -> dict[str, Any]:
    """Fetch historical data from ERCOT archive.

    Returns archived data for the specified endpoint and date range.
    This is useful for accessing data older than 90 days.

    Note: This endpoint requires ERCOT API authentication to be configured.
    """
    try:
        import pandas as pd

        ercot = get_ercot()

        # Get the archive client
        archive = ercot._get_archive()

        # Convert dates to Timestamps
        start_ts = pd.Timestamp(start, tz="US/Central")
        end_ts = pd.Timestamp(end, tz="US/Central")

        # Get the endpoint path
        endpoint_path = AVAILABLE_ENDPOINTS.get(endpoint)
        if not endpoint_path:
            raise HTTPException(status_code=400, detail=f"Unknown endpoint: {endpoint}")

        # Fetch historical data
        df = archive.fetch_historical(
            endpoint=endpoint_path,
            start=start_ts,
            end=end_ts,
        )

        # Convert DataFrame to list of dicts
        data = df.to_dict(orient="records") if not df.empty else []

        return {
            "data": data,
            "count": len(data),
            "endpoint": endpoint,
            "start_date": start,
            "end_date": end,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch historical data: {e}"
        )
