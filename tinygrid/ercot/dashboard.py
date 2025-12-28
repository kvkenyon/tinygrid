"""Dashboard/JSON methods for ERCOT data access (no authentication required).

This module contains methods that access ERCOT's public dashboard endpoints
at https://www.ercot.com/api/1/services/read/dashboards/

These methods don't require API authentication and provide real-time
grid status and operational data.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import httpx
import pandas as pd

logger = logging.getLogger(__name__)

# Dashboard base URL
DASHBOARD_BASE = "https://www.ercot.com/api/1/services/read/dashboards"


class GridCondition(str, Enum):
    """ERCOT grid operating conditions."""

    NORMAL = "normal"
    CONSERVATION = "conservation"
    WATCH = "watch"
    EMERGENCY = "emergency"


@dataclass
class GridStatus:
    """Current grid operating status."""

    condition: GridCondition
    current_frequency: float
    current_load: float
    capacity: float
    reserves: float
    timestamp: pd.Timestamp

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> GridStatus:
        """Create GridStatus from dashboard JSON response."""
        return cls(
            condition=GridCondition(data.get("condition", "normal").lower()),
            current_frequency=float(data.get("currentFrequency", 60.0)),
            current_load=float(data.get("currentLoad", 0)),
            capacity=float(data.get("capacity", 0)),
            reserves=float(data.get("reserves", 0)),
            timestamp=pd.Timestamp.now(tz="US/Central"),
        )


class ERCOTDashboardMixin:
    """Mixin class providing dashboard/JSON methods.

    These methods access ERCOT's public dashboard endpoints
    and don't require authentication.
    """

    def get_status(self) -> GridStatus:
        """Get current grid operating status.

        Returns real-time grid conditions including:
        - Operating condition (normal, watch, emergency, etc.)
        - Current frequency
        - Current load
        - Available capacity
        - Operating reserves

        Returns:
            GridStatus object with current grid state
        """
        url = f"{DASHBOARD_BASE}/current-conditions.json"

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            logger.error(f"Failed to fetch grid status: {e}")
            # Return a default status on error
            return GridStatus(
                condition=GridCondition.NORMAL,
                current_frequency=60.0,
                current_load=0,
                capacity=0,
                reserves=0,
                timestamp=pd.Timestamp.now(tz="US/Central"),
            )

        return GridStatus.from_json(data)

    def get_fuel_mix(self, date: str = "today") -> pd.DataFrame:
        """Get generation fuel mix data.

        Returns 5-minute interval data for generation by fuel type:
        - Wind
        - Solar
        - Natural Gas
        - Coal
        - Nuclear
        - Hydro
        - Other

        Args:
            date: Date to fetch ("today", "yesterday", or YYYY-MM-DD)

        Returns:
            DataFrame with columns: Time, Wind, Solar, Gas, Coal, Nuclear, etc.
        """
        url = f"{DASHBOARD_BASE}/fuel-mix.json"

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            logger.error(f"Failed to fetch fuel mix: {e}")
            return pd.DataFrame()

        # Parse fuel mix data
        rows = []
        for entry in data.get("data", []):
            row = {
                "Timestamp": pd.Timestamp(entry.get("timestamp", "")),
            }
            for fuel, value in entry.get("fuels", {}).items():
                row[fuel.title()] = float(value)
            rows.append(row)

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        if "Timestamp" in df.columns:
            df = df.sort_values("Timestamp")

        return df

    def get_energy_storage_resources(self) -> pd.DataFrame:
        """Get energy storage resource (ESR) data.

        Returns current state of grid-connected battery storage:
        - Total capacity
        - Current charge level
        - Charging/discharging status

        Returns:
            DataFrame with ESR data
        """
        url = f"{DASHBOARD_BASE}/energy-storage.json"

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            logger.error(f"Failed to fetch ESR data: {e}")
            return pd.DataFrame()

        # Parse ESR data
        records = data.get("data", [])
        if not records:
            return pd.DataFrame()

        return pd.DataFrame(records)

    def get_system_wide_demand(self) -> pd.DataFrame:
        """Get system-wide demand data.

        Returns current and forecasted system demand.

        Returns:
            DataFrame with demand data
        """
        url = f"{DASHBOARD_BASE}/system-wide-demand.json"

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            logger.error(f"Failed to fetch system demand: {e}")
            return pd.DataFrame()

        records = data.get("data", [])
        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records)
        return df

    def get_renewable_generation(self) -> pd.DataFrame:
        """Get renewable generation data (wind and solar).

        Returns current and forecasted renewable generation.

        Returns:
            DataFrame with renewable generation data
        """
        url = f"{DASHBOARD_BASE}/renewable-generation.json"

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            logger.error(f"Failed to fetch renewable generation: {e}")
            return pd.DataFrame()

        records = data.get("data", [])
        if not records:
            return pd.DataFrame()

        return pd.DataFrame(records)

    def get_capacity_committed(self) -> pd.DataFrame:
        """Get committed generation capacity data.

        Returns:
            DataFrame with capacity commitment data
        """
        url = f"{DASHBOARD_BASE}/capacity-committed.json"

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            logger.error(f"Failed to fetch capacity committed: {e}")
            return pd.DataFrame()

        records = data.get("data", [])
        if not records:
            return pd.DataFrame()

        return pd.DataFrame(records)

    def get_capacity_forecast(self) -> pd.DataFrame:
        """Get capacity forecast data.

        Returns:
            DataFrame with capacity forecast data
        """
        url = f"{DASHBOARD_BASE}/capacity-forecast.json"

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            logger.error(f"Failed to fetch capacity forecast: {e}")
            return pd.DataFrame()

        records = data.get("data", [])
        if not records:
            return pd.DataFrame()

        return pd.DataFrame(records)
