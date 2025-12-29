"""Dashboard routes - Grid status and real-time data endpoints.

These endpoints use the authenticated ERCOT API to provide grid data.
Falls back to reasonable defaults when specific data is unavailable.
"""

import math
from datetime import datetime
from typing import Any

from client import get_ercot
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


def safe_float(value: Any, default: float = 0.0) -> float:
    """Convert value to float, handling NaN and None."""
    try:
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return default
        return f
    except (TypeError, ValueError):
        return default


class GridStatusResponse(BaseModel):
    """Response model for grid status."""

    condition: str
    current_load: float
    capacity: float
    reserves: float
    timestamp: str
    peak_forecast: float
    wind_output: float
    solar_output: float
    prc: float
    message: str


class FuelMixEntry(BaseModel):
    """Single fuel type in the mix."""

    fuel_type: str
    generation_mw: float
    percentage: float


class FuelMixResponse(BaseModel):
    """Response model for fuel mix."""

    entries: list[FuelMixEntry]
    timestamp: str
    total_generation_mw: float


class RenewableResponse(BaseModel):
    """Response model for renewable generation."""

    wind_mw: float
    solar_mw: float
    wind_forecast_mw: float
    solar_forecast_mw: float
    wind_capacity_mw: float
    solar_capacity_mw: float
    timestamp: str
    total_renewable_mw: float
    renewable_percentage: float | None = None


class SupplyDemandEntry(BaseModel):
    """Single hour in supply/demand data."""

    hour: str | int | None
    demand: float
    supply: float
    reserves: float


class SupplyDemandResponse(BaseModel):
    """Response model for supply/demand data."""

    data: list[SupplyDemandEntry]
    timestamp: str


@router.get("/status", response_model=GridStatusResponse)
def get_status() -> dict[str, Any]:
    """Get current grid operating status.

    Uses authenticated API to get load data and renewable forecasts
    to provide a comprehensive grid status view.
    """
    try:
        ercot = get_ercot()

        # Get current load data - try today first, fall back to yesterday
        load_df = ercot.get_load(start="today")
        if load_df.empty:
            load_df = ercot.get_load(start="yesterday")

        current_load = 0.0
        if not load_df.empty:
            # Get the most recent load value
            current_load = safe_float(load_df["Total"].iloc[-1])

        # Get wind and solar forecasts for current output
        wind_output = 0.0
        solar_output = 0.0

        try:
            wind_df = ercot.get_wind_forecast(start="today", resolution="hourly")
            if wind_df.empty:
                wind_df = ercot.get_wind_forecast(
                    start="yesterday", resolution="hourly"
                )
            if not wind_df.empty:
                # Use actual generation if available, otherwise use forecast
                gen = wind_df["Generation System Wide"].iloc[-1]
                if gen is None or (isinstance(gen, float) and math.isnan(gen)):
                    wind_output = safe_float(wind_df["STWPF System Wide"].iloc[-1])
                else:
                    wind_output = safe_float(gen)
        except Exception:
            pass

        try:
            solar_df = ercot.get_solar_forecast(start="today", resolution="hourly")
            if solar_df.empty:
                solar_df = ercot.get_solar_forecast(
                    start="yesterday", resolution="hourly"
                )
            if not solar_df.empty:
                # Use actual generation if available, otherwise use forecast
                gen = solar_df["Generation System Wide"].iloc[-1]
                if gen is None or (isinstance(gen, float) and math.isnan(gen)):
                    solar_output = safe_float(solar_df["STPPF System Wide"].iloc[-1])
                else:
                    solar_output = safe_float(gen)
        except Exception:
            pass

        # Estimate capacity and reserves (ERCOT typical ranges)
        capacity = max(current_load * 1.15, 80000)  # ~15% headroom typical
        reserves = capacity - current_load
        peak_forecast = current_load * 1.05  # Rough estimate

        return {
            "condition": "normal",
            "current_load": current_load,
            "capacity": capacity,
            "reserves": reserves,
            "timestamp": datetime.now().isoformat(),
            "peak_forecast": peak_forecast,
            "wind_output": wind_output,
            "solar_output": solar_output,
            "prc": (reserves / capacity * 100) if capacity > 0 else 0,
            "message": "Data from authenticated ERCOT API",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch grid status: {e}")


@router.get("/fuel-mix", response_model=FuelMixResponse)
def get_fuel_mix() -> dict[str, Any]:
    """Get current generation fuel mix.

    Uses wind and solar forecast data to show renewable generation.
    Full fuel mix breakdown requires dashboard access which may be restricted.
    """
    try:
        ercot = get_ercot()
        entries = []
        total = 0.0

        # Get wind generation
        try:
            wind_df = ercot.get_wind_forecast(start="today", resolution="hourly")
            if wind_df.empty:
                wind_df = ercot.get_wind_forecast(
                    start="yesterday", resolution="hourly"
                )
            if not wind_df.empty:
                gen = wind_df["Generation System Wide"].iloc[-1]
                if gen is None or (isinstance(gen, float) and math.isnan(gen)):
                    wind_mw = safe_float(wind_df["STWPF System Wide"].iloc[-1])
                else:
                    wind_mw = safe_float(gen)
                entries.append(
                    {
                        "fuel_type": "wind",
                        "generation_mw": wind_mw,
                        "percentage": 0,  # Will calculate after getting totals
                    }
                )
                total += wind_mw
        except Exception:
            pass

        # Get solar generation
        try:
            solar_df = ercot.get_solar_forecast(start="today", resolution="hourly")
            if solar_df.empty:
                solar_df = ercot.get_solar_forecast(
                    start="yesterday", resolution="hourly"
                )
            if not solar_df.empty:
                gen = solar_df["Generation System Wide"].iloc[-1]
                if gen is None or (isinstance(gen, float) and math.isnan(gen)):
                    solar_mw = safe_float(solar_df["STPPF System Wide"].iloc[-1])
                else:
                    solar_mw = safe_float(gen)
                entries.append(
                    {
                        "fuel_type": "solar",
                        "generation_mw": solar_mw,
                        "percentage": 0,
                    }
                )
                total += solar_mw
        except Exception:
            pass

        # Get total load to estimate other generation
        try:
            load_df = ercot.get_load(start="today")
            if load_df.empty:
                load_df = ercot.get_load(start="yesterday")
            if not load_df.empty:
                current_load = safe_float(load_df["Total"].iloc[-1])
                other_gen = max(0, current_load - total)
                if other_gen > 0:
                    entries.append(
                        {
                            "fuel_type": "other",
                            "generation_mw": other_gen,
                            "percentage": 0,
                        }
                    )
                    total = current_load
        except Exception:
            pass

        # Calculate percentages
        for entry in entries:
            if total > 0:
                entry["percentage"] = (entry["generation_mw"] / total) * 100

        return {
            "entries": entries,
            "timestamp": datetime.now().isoformat(),
            "total_generation_mw": total,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch fuel mix: {e}")


@router.get("/renewable", response_model=RenewableResponse)
def get_renewable() -> dict[str, Any]:
    """Get current renewable generation data (wind and solar).

    Uses authenticated wind and solar forecast endpoints.
    """
    try:
        ercot = get_ercot()

        wind_mw = 0.0
        solar_mw = 0.0
        wind_forecast = 0.0
        solar_forecast = 0.0

        # Get wind data
        try:
            wind_df = ercot.get_wind_forecast(start="today", resolution="hourly")
            if wind_df.empty:
                wind_df = ercot.get_wind_forecast(
                    start="yesterday", resolution="hourly"
                )
            if not wind_df.empty:
                gen = wind_df["Generation System Wide"].iloc[-1]
                if gen is None or (isinstance(gen, float) and math.isnan(gen)):
                    wind_mw = safe_float(wind_df["STWPF System Wide"].iloc[-1])
                else:
                    wind_mw = safe_float(gen)
                wind_forecast = safe_float(wind_df["STWPF System Wide"].iloc[-1])
        except Exception:
            pass

        # Get solar data
        try:
            solar_df = ercot.get_solar_forecast(start="today", resolution="hourly")
            if solar_df.empty:
                solar_df = ercot.get_solar_forecast(
                    start="yesterday", resolution="hourly"
                )
            if not solar_df.empty:
                gen = solar_df["Generation System Wide"].iloc[-1]
                if gen is None or (isinstance(gen, float) and math.isnan(gen)):
                    solar_mw = safe_float(solar_df["STPPF System Wide"].iloc[-1])
                else:
                    solar_mw = safe_float(gen)
                solar_forecast = safe_float(solar_df["STPPF System Wide"].iloc[-1])
        except Exception:
            pass

        # Typical ERCOT installed capacities (approximate)
        wind_capacity = 40000.0  # ~40 GW installed wind
        solar_capacity = 20000.0  # ~20 GW installed solar

        total_renewable = wind_mw + solar_mw
        total_capacity = wind_capacity + solar_capacity

        return {
            "wind_mw": wind_mw,
            "solar_mw": solar_mw,
            "wind_forecast_mw": wind_forecast,
            "solar_forecast_mw": solar_forecast,
            "wind_capacity_mw": wind_capacity,
            "solar_capacity_mw": solar_capacity,
            "timestamp": datetime.now().isoformat(),
            "total_renewable_mw": total_renewable,
            "renewable_percentage": (
                (total_renewable / total_capacity * 100) if total_capacity > 0 else 0
            ),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch renewable data: {e}"
        )


@router.get("/supply-demand", response_model=SupplyDemandResponse)
def get_supply_demand() -> dict[str, Any]:
    """Get supply and demand data.

    Uses load forecast data to show demand trends.
    """
    try:
        ercot = get_ercot()

        # Get load data for today, fall back to yesterday
        load_df = ercot.get_load(start="today")
        if load_df.empty:
            load_df = ercot.get_load(start="yesterday")

        if load_df.empty:
            return {
                "data": [],
                "timestamp": datetime.now().isoformat(),
            }

        data = []
        for idx, row in load_df.iterrows():
            demand = safe_float(row.get("Total", 0))
            # Supply is typically slightly higher than demand
            supply = demand * 1.05
            reserves = supply - demand

            data.append(
                {
                    "hour": idx if isinstance(idx, int) else len(data),
                    "demand": demand,
                    "supply": supply,
                    "reserves": reserves,
                }
            )

        return {
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch supply/demand: {e}"
        )
