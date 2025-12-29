"""Forecasts routes - Load and renewable generation forecast endpoints.

These endpoints provide access to ERCOT load and renewable generation
forecasts with various filtering options.
"""

from typing import Any, Literal

from client import get_ercot
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()


class LoadResponse(BaseModel):
    """Response model for load data."""

    data: list[dict[str, Any]]
    count: int
    zone_type: str
    start_date: str
    end_date: str | None = None


class WindForecastResponse(BaseModel):
    """Response model for wind forecast."""

    data: list[dict[str, Any]]
    count: int
    resolution: str
    by_region: bool
    start_date: str
    end_date: str | None = None


class SolarForecastResponse(BaseModel):
    """Response model for solar forecast."""

    data: list[dict[str, Any]]
    count: int
    resolution: str
    by_region: bool
    start_date: str
    end_date: str | None = None


class LoadForecastResponse(BaseModel):
    """Response model for load forecast."""

    data: list[dict[str, Any]]
    count: int
    zone_type: str
    start_date: str
    end_date: str | None = None


@router.get("/load-forecast", response_model=LoadForecastResponse)
def get_load_forecast(
    start: str = Query(
        default="today", description="Start date (YYYY-MM-DD, 'today', or 'yesterday')"
    ),
    end: str | None = Query(default=None, description="End date (YYYY-MM-DD)"),
    by: Literal["weather_zone", "study_area"] = Query(
        default="weather_zone",
        description="Group load data by weather zone or study area",
    ),
) -> dict[str, Any]:
    """Get load forecast data.

    Returns system load forecast data - useful when actual load data isn't available yet.
    """
    from datetime import date, timedelta

    try:
        ercot = get_ercot()

        # Parse start date
        if start == "today":
            start_date = date.today().strftime("%Y-%m-%d")
        elif start == "yesterday":
            start_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            start_date = start

        # Parse end date - default to same day
        if end:
            if end == "today":
                end_date = date.today().strftime("%Y-%m-%d")
            elif end == "yesterday":
                end_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
            else:
                end_date = end
        else:
            end_date = start_date

        if by == "weather_zone":
            df = ercot.get_load_forecast_by_weather_zone(
                start_date=start_date,
                end_date=end_date,
            )
        else:
            df = ercot.get_load_forecast_by_study_area(
                start_date=start_date,
                end_date=end_date,
            )

        # Convert DataFrame to list of dicts
        data = df.to_dict(orient="records") if not df.empty else []

        return {
            "data": data,
            "count": len(data),
            "zone_type": by,
            "start_date": start,
            "end_date": end,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch load forecast: {e}"
        )


@router.get("/load", response_model=LoadResponse)
def get_load(
    start: str = Query(
        default="today", description="Start date (YYYY-MM-DD, 'today', or 'yesterday')"
    ),
    end: str | None = Query(default=None, description="End date (YYYY-MM-DD)"),
    by: Literal["weather_zone", "forecast_zone"] = Query(
        default="weather_zone",
        description="Group load data by weather zone or forecast zone",
    ),
) -> dict[str, Any]:
    """Get actual system load data.

    Returns system load data grouped by weather zone or forecast zone.
    """
    try:
        ercot = get_ercot()

        df = ercot.get_load(
            start=start,
            end=end,
            by=by,
        )

        # Convert DataFrame to list of dicts
        data = df.to_dict(orient="records") if not df.empty else []

        return {
            "data": data,
            "count": len(data),
            "zone_type": by,
            "start_date": start,
            "end_date": end,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch load data: {e}")


@router.get("/wind-forecast", response_model=WindForecastResponse)
def get_wind_forecast(
    start: str = Query(
        default="today", description="Start date (YYYY-MM-DD, 'today', or 'yesterday')"
    ),
    end: str | None = Query(default=None, description="End date (YYYY-MM-DD)"),
    resolution: Literal["hourly", "5min"] = Query(
        default="hourly",
        description="Data resolution - hourly or 5-minute",
    ),
    by_region: bool = Query(
        default=False,
        description="If true, get data by geographical region",
    ),
) -> dict[str, Any]:
    """Get wind power production forecast.

    Returns wind forecast data with configurable resolution and
    optional regional breakdown.
    """
    try:
        ercot = get_ercot()

        df = ercot.get_wind_forecast(
            start=start,
            end=end,
            by_region=by_region,
            resolution=resolution,
        )

        # Convert DataFrame to list of dicts
        data = df.to_dict(orient="records") if not df.empty else []

        return {
            "data": data,
            "count": len(data),
            "resolution": resolution,
            "by_region": by_region,
            "start_date": start,
            "end_date": end,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch wind forecast: {e}"
        )


@router.get("/solar-forecast", response_model=SolarForecastResponse)
def get_solar_forecast(
    start: str = Query(
        default="today", description="Start date (YYYY-MM-DD, 'today', or 'yesterday')"
    ),
    end: str | None = Query(default=None, description="End date (YYYY-MM-DD)"),
    resolution: Literal["hourly", "5min"] = Query(
        default="hourly",
        description="Data resolution - hourly or 5-minute",
    ),
    by_region: bool = Query(
        default=False,
        description="If true, get data by geographical region",
    ),
) -> dict[str, Any]:
    """Get solar power production forecast.

    Returns solar forecast data with configurable resolution and
    optional regional breakdown.
    """
    try:
        ercot = get_ercot()

        df = ercot.get_solar_forecast(
            start=start,
            end=end,
            by_region=by_region,
            resolution=resolution,
        )

        # Convert DataFrame to list of dicts
        data = df.to_dict(orient="records") if not df.empty else []

        return {
            "data": data,
            "count": len(data),
            "resolution": resolution,
            "by_region": by_region,
            "start_date": start,
            "end_date": end,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch solar forecast: {e}"
        )
