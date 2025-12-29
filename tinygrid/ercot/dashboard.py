"""Dashboard/JSON methods for ERCOT data access.

This module provides access to ERCOT's public dashboard data via undocumented
JSON endpoints. These endpoints do NOT require authentication and provide
real-time grid status information.

Endpoints used:
- https://www.ercot.com/api/1/services/read/dashboards/todays-outlook.json
- https://www.ercot.com/api/1/services/read/dashboards/daily-prc.json
- https://www.ercot.com/api/1/services/read/dashboards/combinedWindSolar.json
- https://www.ercot.com/api/1/services/read/dashboards/supplyDemand.json

Note: These are undocumented endpoints that power ERCOT's public dashboard.
They may change without notice.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import httpx
import pandas as pd

from ..constants.ercot import ERCOT_TIMEZONE

logger = logging.getLogger(__name__)

# Dashboard JSON endpoints (undocumented but functional)
DASHBOARD_BASE_URL = "https://www.ercot.com/api/1/services/read/dashboards"
TODAYS_OUTLOOK_URL = f"{DASHBOARD_BASE_URL}/todays-outlook.json"
DAILY_PRC_URL = f"{DASHBOARD_BASE_URL}/daily-prc.json"
COMBINED_WIND_SOLAR_URL = f"{DASHBOARD_BASE_URL}/combinedWindSolar.json"
SUPPLY_DEMAND_URL = f"{DASHBOARD_BASE_URL}/supplyDemand.json"
FUEL_MIX_URL = f"{DASHBOARD_BASE_URL}/fuel-mix.json"

# Default timeout for dashboard requests
DASHBOARD_TIMEOUT = 15.0


class GridCondition(str, Enum):
    """ERCOT grid operating conditions."""

    NORMAL = "normal"
    CONSERVATION = "conservation"
    WATCH = "watch"
    ADVISORY = "advisory"
    EMERGENCY = "emergency"
    EEA1 = "eea1"
    EEA2 = "eea2"
    EEA3 = "eea3"
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, value: str | None) -> GridCondition:
        """Parse a condition string from the API."""
        if not value:
            return cls.UNKNOWN
        value_lower = value.lower().strip()
        # Map common variations
        mappings = {
            "normal": cls.NORMAL,
            "normal operations": cls.NORMAL,
            "conservation": cls.CONSERVATION,
            "conservation appeal": cls.CONSERVATION,
            "watch": cls.WATCH,
            "weather watch": cls.WATCH,
            "advisory": cls.ADVISORY,
            "operating condition notice": cls.ADVISORY,
            "emergency": cls.EMERGENCY,
            "eea1": cls.EEA1,
            "eea 1": cls.EEA1,
            "energy emergency alert 1": cls.EEA1,
            "eea2": cls.EEA2,
            "eea 2": cls.EEA2,
            "energy emergency alert 2": cls.EEA2,
            "eea3": cls.EEA3,
            "eea 3": cls.EEA3,
            "energy emergency alert 3": cls.EEA3,
        }
        return mappings.get(value_lower, cls.UNKNOWN)


@dataclass
class GridStatus:
    """Current grid operating status."""

    condition: GridCondition
    current_load: float
    capacity: float
    reserves: float
    timestamp: pd.Timestamp
    current_frequency: float = 60.0
    message: str = ""
    peak_forecast: float = 0.0
    wind_output: float = 0.0
    solar_output: float = 0.0
    prc: float = 0.0  # Physical Responsive Capability

    @classmethod
    def unavailable(cls) -> GridStatus:
        """Create an unavailable GridStatus placeholder."""
        return cls(
            condition=GridCondition.UNKNOWN,
            current_frequency=0.0,
            current_load=0.0,
            capacity=0.0,
            reserves=0.0,
            timestamp=pd.Timestamp.now(tz=ERCOT_TIMEZONE),
            message="Dashboard data not available",
        )


@dataclass
class FuelMixEntry:
    """A single fuel type entry in the fuel mix."""

    fuel_type: str
    generation_mw: float
    percentage: float
    timestamp: pd.Timestamp


@dataclass
class RenewableStatus:
    """Current renewable generation status."""

    wind_mw: float
    solar_mw: float
    wind_forecast_mw: float
    solar_forecast_mw: float
    wind_capacity_mw: float
    solar_capacity_mw: float
    timestamp: pd.Timestamp
    additional_data: dict[str, Any] = field(default_factory=dict)


def _fetch_json(url: str, timeout: float = DASHBOARD_TIMEOUT) -> dict[str, Any] | None:
    """Fetch JSON data from a dashboard endpoint.

    Args:
        url: The endpoint URL
        timeout: Request timeout in seconds

    Returns:
        Parsed JSON dict or None if request fails
    """
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        logger.warning(f"Dashboard request timed out: {url}")
        return None
    except httpx.HTTPStatusError as e:
        logger.warning(
            f"Dashboard request failed with status {e.response.status_code}: {url}"
        )
        return None
    except Exception as e:
        logger.warning(f"Dashboard request failed: {url} - {e}")
        return None


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _parse_timestamp(value: Any) -> pd.Timestamp:
    """Parse a timestamp from the API response."""
    now: pd.Timestamp = pd.Timestamp.now(tz=ERCOT_TIMEZONE)
    if value is None:
        return now
    try:
        # Try parsing as epoch milliseconds first
        if isinstance(value, (int, float)) and value > 1_000_000_000_000:
            result = pd.Timestamp(value, unit="ms", tz=ERCOT_TIMEZONE)
        elif isinstance(value, (int, float)):
            result = pd.Timestamp(value, unit="s", tz=ERCOT_TIMEZONE)
        else:
            result = pd.Timestamp(value, tz=ERCOT_TIMEZONE)
        # Handle NaT case - result is pd.NaT doesn't work with pyright
        # so we use the hash comparison trick
        if result is pd.NaT or str(result) == "NaT":
            return now
        # Cast to Timestamp to satisfy type checker
        return pd.Timestamp(result)
    except Exception:
        return now


class ERCOTDashboardMixin:
    """Mixin class providing dashboard/JSON methods.

    These methods access ERCOT's public dashboard JSON endpoints which do NOT
    require authentication. They provide real-time grid status information
    that powers the ERCOT dashboard at ercot.com.

    Note: These endpoints are undocumented and may change without notice.
    For production use with SLA requirements, consider using the authenticated
    API endpoints instead.
    """

    def get_status(self) -> GridStatus:
        """Get current grid operating status from ERCOT dashboard.

        Fetches real-time grid status including:
        - Operating condition (normal, conservation, emergency, EEA levels)
        - Current system load
        - Available capacity
        - Operating reserves
        - Wind and solar output

        Returns:
            GridStatus object with current grid conditions

        Example:
            ```python
            ercot = ERCOT()
            status = ercot.get_status()
            print(f"Condition: {status.condition}")
            print(f"Current Load: {status.current_load:,.0f} MW")
            print(f"Reserves: {status.reserves:,.0f} MW")
            ```
        """
        # Fetch today's outlook data
        data = _fetch_json(TODAYS_OUTLOOK_URL)
        if not data:
            logger.warning("Failed to fetch grid status from dashboard")
            return GridStatus.unavailable()

        try:
            # Parse the response - structure varies by time of day
            current = data.get("current", data)

            # Extract values with safe defaults
            condition_str = current.get("condition") or current.get("status") or ""
            condition = GridCondition.from_string(condition_str)

            # Get load and capacity values
            current_load = _safe_float(current.get("demand") or current.get("load"))
            capacity = _safe_float(
                current.get("capacity") or current.get("totalCapacity")
            )
            reserves = _safe_float(
                current.get("reserves") or current.get("operatingReserves")
            )

            # Calculate reserves if not directly available
            if reserves == 0.0 and capacity > 0 and current_load > 0:
                reserves = capacity - current_load

            # Get renewable data if available
            wind = _safe_float(current.get("windOutput") or current.get("wind"))
            solar = _safe_float(current.get("solarOutput") or current.get("solar"))

            # Get peak forecast
            peak = _safe_float(current.get("peakForecast") or current.get("peak"))

            # Get timestamp
            ts = _parse_timestamp(
                current.get("lastUpdated") or current.get("timestamp")
            )

            # Get PRC (Physical Responsive Capability) if available
            prc = _safe_float(current.get("prc") or current.get("physicalResponsive"))

            # Build message from any alerts
            message = current.get("message") or current.get("alert") or ""
            if condition != GridCondition.NORMAL and not message:
                message = f"Grid operating in {condition.value} condition"

            return GridStatus(
                condition=condition,
                current_load=current_load,
                capacity=capacity,
                reserves=reserves,
                timestamp=ts,
                peak_forecast=peak,
                wind_output=wind,
                solar_output=solar,
                prc=prc,
                message=message,
            )

        except Exception as e:
            logger.warning(f"Failed to parse grid status: {e}")
            return GridStatus.unavailable()

    def get_fuel_mix(
        self, as_dataframe: bool = True
    ) -> pd.DataFrame | list[FuelMixEntry]:
        """Get current generation fuel mix data.

        Fetches the current generation breakdown by fuel type from the
        ERCOT dashboard. This shows real-time MW output by fuel source.

        Args:
            as_dataframe: If True, return results as DataFrame. If False,
                return list of FuelMixEntry objects.

        Returns:
            DataFrame or list with fuel mix data including:
            - fuel_type: Type of fuel (gas, coal, nuclear, wind, solar, etc.)
            - generation_mw: Current generation in MW
            - percentage: Percentage of total generation

        Example:
            ```python
            ercot = ERCOT()
            fuel_mix = ercot.get_fuel_mix()
            print(fuel_mix)
            #   fuel_type  generation_mw  percentage
            # 0       gas        25000.0        45.2
            # 1      wind        18000.0        32.5
            # 2     solar         8000.0        14.5
            # ...
            ```
        """
        data = _fetch_json(FUEL_MIX_URL)
        if not data:
            logger.warning("Failed to fetch fuel mix from dashboard")
            if as_dataframe:
                return pd.DataFrame(
                    columns=["fuel_type", "generation_mw", "percentage", "timestamp"]
                )
            return []

        try:
            entries: list[FuelMixEntry] = []
            ts = _parse_timestamp(data.get("lastUpdated") or data.get("timestamp"))

            # Parse fuel mix entries - structure may be list or nested
            fuel_data = data.get("data") or data.get("fuelMix") or data
            if isinstance(fuel_data, list):
                total_gen = sum(
                    _safe_float(f.get("gen") or f.get("generation") or f.get("mw"))
                    for f in fuel_data
                )

                for item in fuel_data:
                    fuel_type = (
                        item.get("fuel")
                        or item.get("fuelType")
                        or item.get("type")
                        or "unknown"
                    )
                    gen_mw = _safe_float(
                        item.get("gen") or item.get("generation") or item.get("mw")
                    )
                    pct = _safe_float(item.get("percent") or item.get("percentage"))
                    if pct == 0.0 and total_gen > 0:
                        pct = (gen_mw / total_gen) * 100

                    entries.append(
                        FuelMixEntry(
                            fuel_type=fuel_type,
                            generation_mw=gen_mw,
                            percentage=pct,
                            timestamp=ts,
                        )
                    )

            if as_dataframe:
                if not entries:
                    return pd.DataFrame(
                        columns=[
                            "fuel_type",
                            "generation_mw",
                            "percentage",
                            "timestamp",
                        ]
                    )
                return pd.DataFrame(
                    [
                        {
                            "fuel_type": e.fuel_type,
                            "generation_mw": e.generation_mw,
                            "percentage": e.percentage,
                            "timestamp": e.timestamp,
                        }
                        for e in entries
                    ]
                )
            return entries

        except Exception as e:
            logger.warning(f"Failed to parse fuel mix: {e}")
            if as_dataframe:
                return pd.DataFrame(
                    columns=["fuel_type", "generation_mw", "percentage", "timestamp"]
                )
            return []

    def get_renewable_generation(self) -> RenewableStatus:
        """Get current renewable generation data (wind and solar).

        Fetches combined wind and solar generation data including current
        output, forecasts, and installed capacity.

        Returns:
            RenewableStatus object with current renewable data

        Example:
            ```python
            ercot = ERCOT()
            renewable = ercot.get_renewable_generation()
            print(f"Wind: {renewable.wind_mw:,.0f} MW")
            print(f"Solar: {renewable.solar_mw:,.0f} MW")
            print(f"Total Renewable: {renewable.wind_mw + renewable.solar_mw:,.0f} MW")
            ```
        """
        data = _fetch_json(COMBINED_WIND_SOLAR_URL)
        if not data:
            logger.warning("Failed to fetch renewable generation from dashboard")
            return RenewableStatus(
                wind_mw=0.0,
                solar_mw=0.0,
                wind_forecast_mw=0.0,
                solar_forecast_mw=0.0,
                wind_capacity_mw=0.0,
                solar_capacity_mw=0.0,
                timestamp=pd.Timestamp.now(tz=ERCOT_TIMEZONE),
            )

        try:
            current = data.get("current", data)
            ts = _parse_timestamp(current.get("lastUpdated") or data.get("lastUpdated"))

            return RenewableStatus(
                wind_mw=_safe_float(current.get("windActual") or current.get("wind")),
                solar_mw=_safe_float(
                    current.get("solarActual") or current.get("solar")
                ),
                wind_forecast_mw=_safe_float(
                    current.get("windForecast") or current.get("windFcst")
                ),
                solar_forecast_mw=_safe_float(
                    current.get("solarForecast") or current.get("solarFcst")
                ),
                wind_capacity_mw=_safe_float(
                    current.get("windCapacity") or current.get("windCap")
                ),
                solar_capacity_mw=_safe_float(
                    current.get("solarCapacity") or current.get("solarCap")
                ),
                timestamp=ts,
                additional_data=current,
            )

        except Exception as e:
            logger.warning(f"Failed to parse renewable generation: {e}")
            return RenewableStatus(
                wind_mw=0.0,
                solar_mw=0.0,
                wind_forecast_mw=0.0,
                solar_forecast_mw=0.0,
                wind_capacity_mw=0.0,
                solar_capacity_mw=0.0,
                timestamp=pd.Timestamp.now(tz=ERCOT_TIMEZONE),
            )

    def get_supply_demand(self) -> pd.DataFrame:
        """Get supply and demand curve data.

        Fetches the current supply/demand balance including hourly forecasts
        and capacity projections.

        Returns:
            DataFrame with supply and demand data by hour

        Example:
            ```python
            ercot = ERCOT()
            supply_demand = ercot.get_supply_demand()
            print(supply_demand.columns)
            # ['hour', 'demand', 'supply', 'reserves', 'timestamp']
            ```
        """
        data = _fetch_json(SUPPLY_DEMAND_URL)
        if not data:
            logger.warning("Failed to fetch supply/demand from dashboard")
            return pd.DataFrame(
                columns=["hour", "demand", "supply", "reserves", "timestamp"]
            )

        try:
            records = []
            ts = _parse_timestamp(data.get("lastUpdated"))

            hourly_data = data.get("data") or data.get("hourly") or []
            for item in hourly_data:
                records.append(
                    {
                        "hour": item.get("hour") or item.get("hourEnding"),
                        "demand": _safe_float(item.get("demand") or item.get("load")),
                        "supply": _safe_float(
                            item.get("supply") or item.get("capacity")
                        ),
                        "reserves": _safe_float(item.get("reserves")),
                        "timestamp": ts,
                    }
                )

            if not records:
                return pd.DataFrame(
                    columns=["hour", "demand", "supply", "reserves", "timestamp"]
                )

            return pd.DataFrame(records)

        except Exception as e:
            logger.warning(f"Failed to parse supply/demand: {e}")
            return pd.DataFrame(
                columns=["hour", "demand", "supply", "reserves", "timestamp"]
            )

    def get_daily_prices(self) -> pd.DataFrame:
        """Get daily price summary from dashboard.

        Fetches the daily price summary including peak and average prices
        from the ERCOT dashboard.

        Returns:
            DataFrame with daily price data

        Example:
            ```python
            ercot = ERCOT()
            prices = ercot.get_daily_prices()
            ```
        """
        data = _fetch_json(DAILY_PRC_URL)
        if not data:
            logger.warning("Failed to fetch daily prices from dashboard")
            return pd.DataFrame()

        try:
            records = []
            ts = _parse_timestamp(data.get("lastUpdated"))

            price_data = data.get("data") or data.get("prices") or data
            if isinstance(price_data, list):
                for item in price_data:
                    records.append(
                        {
                            "settlement_point": item.get("settlementPoint")
                            or item.get("sp"),
                            "price": _safe_float(item.get("price") or item.get("spp")),
                            "peak_price": _safe_float(item.get("peakPrice")),
                            "avg_price": _safe_float(item.get("avgPrice")),
                            "timestamp": ts,
                        }
                    )

            if not records:
                return pd.DataFrame()

            return pd.DataFrame(records)

        except Exception as e:
            logger.warning(f"Failed to parse daily prices: {e}")
            return pd.DataFrame()

    def get_system_wide_demand(self) -> pd.DataFrame:
        """Get system-wide demand data from dashboard.

        Fetches current and forecasted system-wide demand from the
        ERCOT dashboard.

        Returns:
            DataFrame with system-wide demand data
        """
        data = _fetch_json(TODAYS_OUTLOOK_URL)
        if not data:
            logger.warning("Failed to fetch system-wide demand from dashboard")
            return pd.DataFrame()

        try:
            records = []
            ts = _parse_timestamp(data.get("lastUpdated"))

            # Get current and forecasted demand
            current = data.get("current", {})
            hourly = data.get("hourly") or data.get("data") or []

            # Add current demand
            if current:
                records.append(
                    {
                        "hour": "current",
                        "demand": _safe_float(
                            current.get("demand") or current.get("load")
                        ),
                        "capacity": _safe_float(current.get("capacity")),
                        "reserves": _safe_float(current.get("reserves")),
                        "timestamp": ts,
                    }
                )

            # Add hourly forecasts
            for item in hourly:
                records.append(
                    {
                        "hour": item.get("hour") or item.get("hourEnding"),
                        "demand": _safe_float(item.get("demand") or item.get("load")),
                        "capacity": _safe_float(item.get("capacity")),
                        "reserves": _safe_float(item.get("reserves")),
                        "timestamp": ts,
                    }
                )

            if not records:
                return pd.DataFrame()

            return pd.DataFrame(records)

        except Exception as e:
            logger.warning(f"Failed to parse system-wide demand: {e}")
            return pd.DataFrame()

    def get_energy_storage_resources(self) -> pd.DataFrame:
        """Get energy storage resource (ESR) data.

        Note: ESR data may not be available via dashboard endpoints.
        Use authenticated API methods for detailed ESR data.

        Returns:
            DataFrame with ESR data if available, empty DataFrame otherwise
        """
        # ESR data is typically not in the public dashboard
        # Try to get it from the supply/demand or outlook data
        data = _fetch_json(TODAYS_OUTLOOK_URL)
        if not data:
            return pd.DataFrame()

        try:
            current = data.get("current", {})
            esr = current.get("esr") or current.get("storage") or current.get("battery")

            if esr is None:
                return pd.DataFrame()

            if isinstance(esr, dict):
                return pd.DataFrame(
                    [
                        {
                            "charging_mw": _safe_float(esr.get("charging")),
                            "discharging_mw": _safe_float(esr.get("discharging")),
                            "net_mw": _safe_float(esr.get("net")),
                            "capacity_mw": _safe_float(esr.get("capacity")),
                            "timestamp": _parse_timestamp(data.get("lastUpdated")),
                        }
                    ]
                )

            return pd.DataFrame()

        except Exception as e:
            logger.warning(f"Failed to parse ESR data: {e}")
            return pd.DataFrame()

    def get_capacity_committed(self) -> pd.DataFrame:
        """Get committed generation capacity data.

        Returns:
            DataFrame with committed capacity data if available
        """
        data = _fetch_json(SUPPLY_DEMAND_URL)
        if not data:
            return pd.DataFrame()

        try:
            records = []
            ts = _parse_timestamp(data.get("lastUpdated"))

            hourly = data.get("data") or data.get("hourly") or []
            for item in hourly:
                records.append(
                    {
                        "hour": item.get("hour") or item.get("hourEnding"),
                        "committed_capacity": _safe_float(
                            item.get("committed") or item.get("supply")
                        ),
                        "available_capacity": _safe_float(
                            item.get("available") or item.get("capacity")
                        ),
                        "timestamp": ts,
                    }
                )

            if not records:
                return pd.DataFrame()

            return pd.DataFrame(records)

        except Exception as e:
            logger.warning(f"Failed to parse committed capacity: {e}")
            return pd.DataFrame()

    def get_capacity_forecast(self) -> pd.DataFrame:
        """Get capacity forecast data.

        Returns:
            DataFrame with capacity forecast data if available
        """
        # Use the same data as supply/demand
        return self.get_supply_demand()
