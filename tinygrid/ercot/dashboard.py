"""Dashboard/JSON methods for ERCOT data access.

NOTE: ERCOT's public dashboard data is not available via documented JSON endpoints.
The methods in this module are placeholders that return empty data or default values.

For real-time grid data, use the authenticated API methods instead:
- System load: get_actual_system_load_by_weather_zone()
- Generation: get_generation_by_resource_type()
- Forecasts: get_load_forecast_by_weather_zone(), get_wpp_hourly_average_actual_forecast()

These dashboard methods may be implemented in the future if ERCOT provides public
JSON endpoints, or by scraping the ERCOT dashboard website.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

import pandas as pd

logger = logging.getLogger(__name__)


class GridCondition(str, Enum):
    """ERCOT grid operating conditions."""

    NORMAL = "normal"
    CONSERVATION = "conservation"
    WATCH = "watch"
    EMERGENCY = "emergency"
    UNKNOWN = "unknown"


@dataclass
class GridStatus:
    """Current grid operating status."""

    condition: GridCondition
    current_frequency: float
    current_load: float
    capacity: float
    reserves: float
    timestamp: pd.Timestamp
    message: str = ""

    @classmethod
    def unavailable(cls) -> GridStatus:
        """Create an unavailable GridStatus placeholder."""
        return cls(
            condition=GridCondition.UNKNOWN,
            current_frequency=0.0,
            current_load=0.0,
            capacity=0.0,
            reserves=0.0,
            timestamp=pd.Timestamp.now(tz="US/Central"),
            message="Dashboard data not available - use authenticated API methods instead",
        )


class ERCOTDashboardMixin:
    """Mixin class providing dashboard/JSON methods.

    NOTE: These methods are placeholders. ERCOT does not provide documented
    public JSON endpoints for dashboard data. Use authenticated API methods
    for real data:

    - System load: get_actual_system_load_by_weather_zone()
    - Forecasts: get_load_forecast_by_weather_zone()
    - Wind/Solar: get_wpp_hourly_average_actual_forecast(), get_spp_hourly_average_actual_forecast()
    """

    def get_status(self) -> GridStatus:
        """Get current grid operating status.

        NOTE: This method returns placeholder data. ERCOT does not provide
        a public JSON API for grid status. For real data, use:
        - get_actual_system_load_by_weather_zone() for current load
        - Check ercot.com dashboard for grid conditions

        Returns:
            GridStatus object (placeholder with unavailable message)
        """
        logger.warning(
            "get_status() returns placeholder data - "
            "ERCOT does not provide public JSON endpoints for dashboard data"
        )
        return GridStatus.unavailable()

    def get_fuel_mix(self, date: str = "today") -> pd.DataFrame:
        """Get generation fuel mix data.

        NOTE: This method returns empty DataFrame. ERCOT does not provide
        a public JSON API for fuel mix. For real data, use:
        - get_generation_by_resource_type() (requires auth)
        - Check ercot.com fuel mix dashboard

        Args:
            date: Date to fetch ("today", "yesterday", or YYYY-MM-DD)

        Returns:
            Empty DataFrame (placeholder - endpoint not available)
        """
        logger.warning(
            "get_fuel_mix() returns empty data - "
            "ERCOT does not provide public JSON endpoints for fuel mix. "
            "Use get_generation_by_resource_type() with authentication instead."
        )
        return pd.DataFrame()

    def get_energy_storage_resources(self) -> pd.DataFrame:
        """Get energy storage resource (ESR) data.

        NOTE: This method returns empty DataFrame. For ESR data, use
        authenticated API methods.

        Returns:
            Empty DataFrame (placeholder - endpoint not available)
        """
        logger.warning(
            "get_energy_storage_resources() returns empty data - "
            "use authenticated API methods for ESR data"
        )
        return pd.DataFrame()

    def get_system_wide_demand(self) -> pd.DataFrame:
        """Get system-wide demand data.

        NOTE: This method returns empty DataFrame. For demand data, use:
        - get_actual_system_load_by_weather_zone() (current load)
        - get_load_forecast_by_weather_zone() (forecasts)

        Returns:
            Empty DataFrame (placeholder - endpoint not available)
        """
        logger.warning(
            "get_system_wide_demand() returns empty data - "
            "use get_actual_system_load_by_weather_zone() instead"
        )
        return pd.DataFrame()

    def get_renewable_generation(self) -> pd.DataFrame:
        """Get renewable generation data (wind and solar).

        NOTE: This method returns empty DataFrame. For renewable data, use:
        - get_wpp_hourly_average_actual_forecast() (wind)
        - get_spp_hourly_average_actual_forecast() (solar)

        Returns:
            Empty DataFrame (placeholder - endpoint not available)
        """
        logger.warning(
            "get_renewable_generation() returns empty data - "
            "use get_wpp_hourly_average_actual_forecast() or "
            "get_spp_hourly_average_actual_forecast() instead"
        )
        return pd.DataFrame()

    def get_capacity_committed(self) -> pd.DataFrame:
        """Get committed generation capacity data.

        NOTE: This method returns empty DataFrame.

        Returns:
            Empty DataFrame (placeholder - endpoint not available)
        """
        logger.warning(
            "get_capacity_committed() returns empty data - endpoint not available"
        )
        return pd.DataFrame()

    def get_capacity_forecast(self) -> pd.DataFrame:
        """Get capacity forecast data.

        NOTE: This method returns empty DataFrame.

        Returns:
            Empty DataFrame (placeholder - endpoint not available)
        """
        logger.warning(
            "get_capacity_forecast() returns empty data - endpoint not available"
        )
        return pd.DataFrame()
