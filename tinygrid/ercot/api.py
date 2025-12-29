"""Primary user interface for ERCOT data access.

This module contains the high-level API methods that users interact with.
These methods intelligently dispatch to the appropriate data source:
- Recent data → Live REST API (via endpoints)
- Historical data (>90 days) → Archive API
- Real-time status/fuel mix → Dashboard JSON
- Yearly historical → MIS documents
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from ..constants.ercot import (
    LocationType,
    Market,
)
from ..utils.dates import format_api_date, parse_date, parse_date_range
from .transforms import filter_by_date, filter_by_location, standardize_columns

if TYPE_CHECKING:
    pass


class ERCOTAPIMixin:
    """Mixin class providing high-level API methods.

    These are the primary methods users interact with. They provide:
    - Unified interface across different data sources
    - Automatic historical dispatch
    - Location filtering
    - Column standardization

    Requires methods from ERCOTBase and ERCOTEndpointsMixin.
    """

    def get_spp(
        self,
        start: str | pd.Timestamp = "today",
        end: str | pd.Timestamp | None = None,
        market: Market = Market.REAL_TIME_15_MIN,
        locations: list[str] | None = None,
        location_type: LocationType | list[LocationType] | None = None,
    ) -> pd.DataFrame:
        """Get Settlement Point Prices

        Routes to the appropriate endpoint based on market type and handles
        date parsing, filtering, and historical data routing automatically.

        Args:
            start: Start date - "today", "yesterday", or ISO format
            end: End date (defaults to start + 1 day)
            market: Market type:
                - Market.REAL_TIME_15_MIN: 15-minute real-time prices
                - Market.DAY_AHEAD_HOURLY: Day-ahead hourly prices
            locations: Filter to specific settlement points (e.g., ["LZ_HOUSTON"])
            location_type: Filter by type (single or list):
                - LocationType.LOAD_ZONE: Load zones (LZ_*)
                - LocationType.TRADING_HUB: Trading hubs (HB_*)
                - LocationType.RESOURCE_NODE: Resource nodes
                - Or combine: [LocationType.LOAD_ZONE, LocationType.TRADING_HUB]

        Returns:
            DataFrame with settlement point prices

        Example:
            ```python
            from tinygrid import ERCOT
            from tinygrid.constants import Market, LocationType

            ercot = ERCOT()

            # Get real-time prices for today
            df = ercot.get_spp()

            # Get day-ahead prices for load zones only
            df = ercot.get_spp(
                start="2024-01-15",
                market=Market.DAY_AHEAD_HOURLY,
                location_type=LocationType.LOAD_ZONE,
            )

            # Get both load zones and trading hubs
            df = ercot.get_spp(
                start="yesterday",
                location_type=[LocationType.LOAD_ZONE, LocationType.TRADING_HUB],
            )
            ```
        """
        start_ts, end_ts = parse_date_range(start, end)

        if market == Market.REAL_TIME_15_MIN:
            if self._needs_historical(start_ts, "real_time"):
                # Use historical archive for past data
                df = self._get_archive().fetch_historical(
                    endpoint="/np6-905-cd/spp_node_zone_hub",
                    start=start_ts,
                    end=end_ts,
                )
            else:
                df = self.get_spp_node_zone_hub(
                    delivery_date_from=format_api_date(start_ts),
                    delivery_date_to=format_api_date(end_ts),
                    delivery_hour_from=1,
                    delivery_hour_to=24,
                    delivery_interval_from=1,
                    delivery_interval_to=4,
                )
        elif market == Market.DAY_AHEAD_HOURLY:
            if self._needs_historical(start_ts, "day_ahead"):
                df = self._get_archive().fetch_historical(
                    endpoint="/np4-190-cd/dam_stlmnt_pnt_prices",
                    start=start_ts,
                    end=end_ts,
                )
            else:
                df = self.get_dam_settlement_point_prices(
                    delivery_date_from=format_api_date(start_ts),
                    delivery_date_to=format_api_date(end_ts),
                )
        else:
            raise ValueError(f"Unsupported market type for SPP: {market}")

        # Filter to [start, end) - exclude end date
        df = filter_by_date(df, start_ts, end_ts)

        # Add market column
        if not df.empty:
            df["Market"] = market.value

        df = filter_by_location(df, locations, location_type)
        return standardize_columns(df)

    def get_lmp(
        self,
        start: str | pd.Timestamp = "today",
        end: str | pd.Timestamp | None = None,
        market: Market = Market.REAL_TIME_SCED,
        location_type: LocationType = LocationType.RESOURCE_NODE,
    ) -> pd.DataFrame:
        """Get Locational Marginal Prices with unified interface.

        Routes to the appropriate endpoint based on market and location type.

        Args:
            start: Start date - "today", "yesterday", or ISO format
            end: End date (defaults to start + 1 day)
            market: Market type:
                - Market.REAL_TIME_SCED: Real-time SCED LMP
                - Market.DAY_AHEAD_HOURLY: Day-ahead hourly LMP
            location_type: Location type:
                - LocationType.RESOURCE_NODE: Node/zone/hub LMP
                - LocationType.ELECTRICAL_BUS: Electrical bus LMP

        Returns:
            DataFrame with LMP data

        Example:
            ```python
            from tinygrid import ERCOT
            from tinygrid.constants import Market, LocationType

            ercot = ERCOT()

            # Real-time LMP by settlement point
            df = ercot.get_lmp()

            # Day-ahead LMP by electrical bus
            df = ercot.get_lmp(
                start="2024-01-15",
                market=Market.DAY_AHEAD_HOURLY,
            )
            ```
        """
        start_ts, end_ts = parse_date_range(start, end)

        if market == Market.REAL_TIME_SCED:
            if self._needs_historical(start_ts, "real_time"):
                # Use historical archive for past data
                if location_type == LocationType.ELECTRICAL_BUS:
                    df = self._get_archive().fetch_historical(
                        endpoint="/np6-787-cd/lmp_electrical_bus",
                        start=start_ts,
                        end=end_ts,
                    )
                else:
                    df = self._get_archive().fetch_historical(
                        endpoint="/np6-788-cd/lmp_node_zone_hub",
                        start=start_ts,
                        end=end_ts,
                    )
            else:
                if location_type == LocationType.ELECTRICAL_BUS:
                    df = self.get_lmp_electrical_bus(
                        sced_timestamp_from=format_api_date(start_ts),
                        sced_timestamp_to=format_api_date(end_ts),
                    )
                else:
                    df = self.get_lmp_node_zone_hub(
                        sced_timestamp_from=format_api_date(start_ts),
                        sced_timestamp_to=format_api_date(end_ts),
                    )
        elif market == Market.DAY_AHEAD_HOURLY:
            if self._needs_historical(start_ts, "day_ahead"):
                df = self._get_archive().fetch_historical(
                    endpoint="/np4-183-cd/dam_hourly_lmp",
                    start=start_ts,
                    end=end_ts,
                )
            else:
                df = self.get_dam_hourly_lmp(
                    start_date=format_api_date(start_ts),
                    end_date=format_api_date(end_ts),
                )
        else:
            raise ValueError(f"Unsupported market type for LMP: {market}")

        # Filter to [start, end) - exclude end date
        df = filter_by_date(df, start_ts, end_ts)

        # Add market column
        if not df.empty:
            df["Market"] = market.value

        return standardize_columns(df)

    def get_as_prices(
        self,
        start: str | pd.Timestamp = "today",
        end: str | pd.Timestamp | None = None,
    ) -> pd.DataFrame:
        """Get Day-Ahead Ancillary Service MCPC Prices.

        Fetches Market Clearing Price for Capacity (MCPC) for all
        ancillary service types.

        Args:
            start: Start date - "today", "yesterday", or ISO format
            end: End date (defaults to start + 1 day)

        Returns:
            DataFrame with ancillary service prices

        Example:
            ```python
            ercot = ERCOT()
            df = ercot.get_as_prices(start="2024-01-15")
            ```
        """
        start_ts, end_ts = parse_date_range(start, end)

        if self._needs_historical(start_ts, "day_ahead"):
            df = self._get_archive().fetch_historical(
                endpoint="/np4-188-cd/dam_clear_price_for_cap",
                start=start_ts,
                end=end_ts,
            )
        else:
            df = self.get_dam_clear_price_for_cap(
                delivery_date_from=format_api_date(start_ts),
                delivery_date_to=format_api_date(end_ts),
            )

        df = filter_by_date(df, start_ts, end_ts)
        return standardize_columns(df)

    def get_as_plan(
        self,
        start: str | pd.Timestamp = "today",
        end: str | pd.Timestamp | None = None,
    ) -> pd.DataFrame:
        """Get Day-Ahead Ancillary Service Plan.

        Fetches AS requirements by type and quantity for each hour.

        Args:
            start: Start date - "today", "yesterday", or ISO format
            end: End date (defaults to start + 1 day)

        Returns:
            DataFrame with ancillary service plan

        Example:
            ```python
            ercot = ERCOT()
            df = ercot.get_as_plan(start="2024-01-15")
            ```
        """
        start_ts, end_ts = parse_date_range(start, end)

        if self._needs_historical(start_ts, "day_ahead"):
            df = self._get_archive().fetch_historical(
                endpoint="/np4-33-cd/dam_as_plan",
                start=start_ts,
                end=end_ts,
            )
        else:
            df = self.get_dam_as_plan(
                delivery_date_from=format_api_date(start_ts),
                delivery_date_to=format_api_date(end_ts),
            )

        df = filter_by_date(df, start_ts, end_ts)
        return standardize_columns(df)

    def get_shadow_prices(
        self,
        start: str | pd.Timestamp = "today",
        end: str | pd.Timestamp | None = None,
        market: Market = Market.REAL_TIME_SCED,
    ) -> pd.DataFrame:
        """Get Shadow Prices for transmission constraints.

        Args:
            start: Start date - "today", "yesterday", or ISO format
            end: End date (defaults to start + 1 day)
            market: Market type:
                - Market.REAL_TIME_SCED: SCED shadow prices
                - Market.DAY_AHEAD_HOURLY: DAM shadow prices

        Returns:
            DataFrame with shadow price data
        """
        start_ts, end_ts = parse_date_range(start, end)

        if market == Market.DAY_AHEAD_HOURLY:
            if self._needs_historical(start_ts, "day_ahead"):
                df = self._get_archive().fetch_historical(
                    endpoint="/np4-191-cd/dam_shadow_prices",
                    start=start_ts,
                    end=end_ts,
                )
            else:
                df = self.get_dam_shadow_prices(
                    delivery_date_from=format_api_date(start_ts),
                    delivery_date_to=format_api_date(end_ts),
                )
        else:
            if self._needs_historical(start_ts, "real_time"):
                df = self._get_archive().fetch_historical(
                    endpoint="/np6-86-cd/shdw_prices_bnd_trns_const",
                    start=start_ts,
                    end=end_ts,
                )
            else:
                df = self.get_shadow_prices_bound_transmission_constraint(
                    sced_timestamp_from=format_api_date(start_ts),
                    sced_timestamp_to=format_api_date(end_ts),
                )

        df = filter_by_date(df, start_ts, end_ts)
        return standardize_columns(df)

    def get_load(
        self,
        start: str | pd.Timestamp = "today",
        end: str | pd.Timestamp | None = None,
        by: str = "weather_zone",
    ) -> pd.DataFrame:
        """Get actual system load.

        Args:
            start: Start date - "today", "yesterday", or ISO format
            end: End date (defaults to start + 1 day)
            by: Grouping - "weather_zone" or "forecast_zone"

        Returns:
            DataFrame with system load data
        """
        start_ts, end_ts = parse_date_range(start, end)

        if by == "forecast_zone":
            if self._needs_historical(start_ts, "load"):
                df = self._get_archive().fetch_historical(
                    endpoint="/np6-346-cd/act_sys_load_by_fzn",
                    start=start_ts,
                    end=end_ts,
                )
            else:
                df = self.get_actual_system_load_by_forecast_zone(
                    operating_day_from=format_api_date(start_ts),
                    operating_day_to=format_api_date(end_ts),
                )
        else:
            if self._needs_historical(start_ts, "load"):
                df = self._get_archive().fetch_historical(
                    endpoint="/np6-345-cd/act_sys_load_by_wzn",
                    start=start_ts,
                    end=end_ts,
                )
            else:
                df = self.get_actual_system_load_by_weather_zone(
                    operating_day_from=format_api_date(start_ts),
                    operating_day_to=format_api_date(end_ts),
                )

        df = filter_by_date(df, start_ts, end_ts, date_column="Oper Day")
        return standardize_columns(df)

    def get_wind_forecast(
        self,
        start: str | pd.Timestamp = "today",
        end: str | pd.Timestamp | None = None,
        by_region: bool = False,
        resolution: str = "hourly",
    ) -> pd.DataFrame:
        """Get wind power production forecast.

        Args:
            start: Start date
            end: End date (defaults to start + 1 day)
            by_region: If True, get by geographical region
            resolution: Data resolution - "hourly" (default) or "5min" for 5-minute data

        Returns:
            DataFrame with wind forecast data

        Example:
            ```python
            ercot = ERCOT()

            # Hourly wind forecast (default)
            df = ercot.get_wind_forecast(start="2024-01-15")

            # 5-minute wind data
            df = ercot.get_wind_forecast(start="2024-01-15", resolution="5min")

            # 5-minute wind data by geographic region
            df = ercot.get_wind_forecast(
                start="2024-01-15",
                resolution="5min",
                by_region=True,
            )
            ```
        """
        start_ts, end_ts = parse_date_range(start, end)

        # Validate resolution
        resolution = resolution.lower()
        if resolution not in ("hourly", "5min", "5-min", "5_min"):
            raise ValueError(
                f"Invalid resolution: {resolution}. Use 'hourly' or '5min'."
            )

        use_5min = resolution in ("5min", "5-min", "5_min")

        if use_5min:
            # 5-minute data endpoints
            if by_region:
                if self._needs_historical(start_ts, "forecast"):
                    df = self._get_archive().fetch_historical(
                        endpoint="/np4-743-cd/wpp_actual_5min_avg_values_geo",
                        start=start_ts,
                        end=end_ts,
                    )
                else:
                    df = self.get_wpp_actual_5min_avg_values_geo(
                        posted_datetime_from=format_api_date(start_ts),
                        posted_datetime_to=format_api_date(end_ts),
                    )
            else:
                if self._needs_historical(start_ts, "forecast"):
                    df = self._get_archive().fetch_historical(
                        endpoint="/np4-733-cd/wpp_actual_5min_avg_values",
                        start=start_ts,
                        end=end_ts,
                    )
                else:
                    df = self.get_wpp_actual_5min_avg_values(
                        posted_datetime_from=format_api_date(start_ts),
                        posted_datetime_to=format_api_date(end_ts),
                    )
        else:
            # Hourly data endpoints (default)
            if by_region:
                if self._needs_historical(start_ts, "forecast"):
                    df = self._get_archive().fetch_historical(
                        endpoint="/np4-742-cd/wpp_hrly_actual_fcast_geo",
                        start=start_ts,
                        end=end_ts,
                    )
                else:
                    df = self.get_wpp_hourly_actual_forecast_geo(
                        posted_datetime_from=format_api_date(start_ts),
                        posted_datetime_to=format_api_date(end_ts),
                    )
            else:
                if self._needs_historical(start_ts, "forecast"):
                    df = self._get_archive().fetch_historical(
                        endpoint="/np4-732-cd/wpp_hrly_avrg_actl_fcast",
                        start=start_ts,
                        end=end_ts,
                    )
                else:
                    df = self.get_wpp_hourly_average_actual_forecast(
                        posted_datetime_from=format_api_date(start_ts),
                        posted_datetime_to=format_api_date(end_ts),
                    )

        df = filter_by_date(df, start_ts, end_ts, date_column="Posted Datetime")
        return standardize_columns(df)

    def get_solar_forecast(
        self,
        start: str | pd.Timestamp = "today",
        end: str | pd.Timestamp | None = None,
        by_region: bool = False,
        resolution: str = "hourly",
    ) -> pd.DataFrame:
        """Get solar power production forecast.

        Args:
            start: Start date
            end: End date (defaults to start + 1 day)
            by_region: If True, get by geographical region
            resolution: Data resolution - "hourly" (default) or "5min" for 5-minute data

        Returns:
            DataFrame with solar forecast data

        Example:
            ```python
            ercot = ERCOT()

            # Hourly solar forecast (default)
            df = ercot.get_solar_forecast(start="2024-01-15")

            # 5-minute solar data
            df = ercot.get_solar_forecast(start="2024-01-15", resolution="5min")

            # 5-minute solar data by geographic region
            df = ercot.get_solar_forecast(
                start="2024-01-15",
                resolution="5min",
                by_region=True,
            )
            ```
        """
        start_ts, end_ts = parse_date_range(start, end)

        # Validate resolution
        resolution = resolution.lower()
        if resolution not in ("hourly", "5min", "5-min", "5_min"):
            raise ValueError(
                f"Invalid resolution: {resolution}. Use 'hourly' or '5min'."
            )

        use_5min = resolution in ("5min", "5-min", "5_min")

        if use_5min:
            # 5-minute data endpoints
            if by_region:
                if self._needs_historical(start_ts, "forecast"):
                    df = self._get_archive().fetch_historical(
                        endpoint="/np4-746-cd/spp_actual_5min_avg_values_geo",
                        start=start_ts,
                        end=end_ts,
                    )
                else:
                    df = self.get_spp_actual_5min_avg_values_geo(
                        posted_datetime_from=format_api_date(start_ts),
                        posted_datetime_to=format_api_date(end_ts),
                    )
            else:
                if self._needs_historical(start_ts, "forecast"):
                    df = self._get_archive().fetch_historical(
                        endpoint="/np4-738-cd/spp_actual_5min_avg_values",
                        start=start_ts,
                        end=end_ts,
                    )
                else:
                    df = self.get_spp_actual_5min_avg_values(
                        posted_datetime_from=format_api_date(start_ts),
                        posted_datetime_to=format_api_date(end_ts),
                    )
        else:
            # Hourly data endpoints (default)
            if by_region:
                if self._needs_historical(start_ts, "forecast"):
                    df = self._get_archive().fetch_historical(
                        endpoint="/np4-745-cd/spp_hrly_actual_fcast_geo",
                        start=start_ts,
                        end=end_ts,
                    )
                else:
                    df = self.get_spp_hourly_actual_forecast_geo(
                        posted_datetime_from=format_api_date(start_ts),
                        posted_datetime_to=format_api_date(end_ts),
                    )
            else:
                if self._needs_historical(start_ts, "forecast"):
                    df = self._get_archive().fetch_historical(
                        endpoint="/np4-737-cd/spp_hrly_avrg_actl_fcast",
                        start=start_ts,
                        end=end_ts,
                    )
                else:
                    df = self.get_spp_hourly_average_actual_forecast(
                        posted_datetime_from=format_api_date(start_ts),
                        posted_datetime_to=format_api_date(end_ts),
                    )

        df = filter_by_date(df, start_ts, end_ts, date_column="Posted Datetime")
        return standardize_columns(df)

    # ============================================================================
    # System-Wide Generation and Transmission Data
    # ============================================================================

    def get_dc_tie_flows(
        self,
        start: str | pd.Timestamp = "today",
        end: str | pd.Timestamp | None = None,
    ) -> pd.DataFrame:
        """Get DC Tie flow data from state estimator.

        DC Ties connect ERCOT to neighboring grids (Eastern Interconnection
        and Mexico). This endpoint provides the scheduled and actual flows
        across these ties.

        EMIL ID: NP6-626-CD

        Args:
            start: Start date - "today", "yesterday", or ISO format
            end: End date (defaults to start + 1 day)

        Returns:
            DataFrame with DC tie flow data

        Note:
            This data is only available through the archive API for historical
            dates. Real-time access may require pyercot updates.

        Example:
            ```python
            ercot = ERCOT(auth=auth)
            dc_ties = ercot.get_dc_tie_flows(start="2024-01-15")
            ```
        """
        start_ts, end_ts = parse_date_range(start, end)

        # DC tie data via archive API
        df = self._get_archive().fetch_historical(
            endpoint="/np6-626-cd/dc_tie",
            start=start_ts,
            end=end_ts,
        )

        df = filter_by_date(df, start_ts, end_ts)
        return standardize_columns(df)

    def get_total_generation(
        self,
        start: str | pd.Timestamp = "today",
        end: str | pd.Timestamp | None = None,
    ) -> pd.DataFrame:
        """Get total ERCOT system generation.

        Provides the total MW generation across the ERCOT system from
        the state estimator.

        EMIL ID: NP6-625-CD

        Args:
            start: Start date - "today", "yesterday", or ISO format
            end: End date (defaults to start + 1 day)

        Returns:
            DataFrame with total system generation data

        Note:
            This data is only available through the archive API for historical
            dates. Real-time access may require pyercot updates.

        Example:
            ```python
            ercot = ERCOT(auth=auth)
            total_gen = ercot.get_total_generation(start="2024-01-15")
            ```
        """
        start_ts, end_ts = parse_date_range(start, end)

        # Total generation via archive API
        df = self._get_archive().fetch_historical(
            endpoint="/np6-625-cd/se_totalgen",
            start=start_ts,
            end=end_ts,
        )

        df = filter_by_date(df, start_ts, end_ts)
        return standardize_columns(df)

    def get_system_wide_actuals(
        self,
        start: str | pd.Timestamp = "today",
        end: str | pd.Timestamp | None = None,
    ) -> pd.DataFrame:
        """Get system-wide actual values per SCED interval.

        Provides actual system-wide metrics from each SCED execution
        including load, generation, and reserves.

        EMIL ID: NP6-235-CD

        Args:
            start: Start date - "today", "yesterday", or ISO format
            end: End date (defaults to start + 1 day)

        Returns:
            DataFrame with system-wide actual data

        Note:
            This data is only available through the archive API for historical
            dates. Real-time access may require pyercot updates.

        Example:
            ```python
            ercot = ERCOT(auth=auth)
            actuals = ercot.get_system_wide_actuals(start="2024-01-15")
            ```
        """
        start_ts, end_ts = parse_date_range(start, end)

        # System-wide actuals via archive API
        df = self._get_archive().fetch_historical(
            endpoint="/np6-235-cd/sys_wide_actuals",
            start=start_ts,
            end=end_ts,
        )

        df = filter_by_date(df, start_ts, end_ts)
        return standardize_columns(df)

    # ============================================================================
    # 60-Day Disclosure Reports
    # ============================================================================

    def get_60_day_dam_disclosure(
        self,
        date: str | pd.Timestamp = "today",
    ) -> dict[str, pd.DataFrame]:
        """Get 60-Day DAM (Day-Ahead Market) Disclosure Reports.

        ERCOT publishes these reports with a 60-day delay. This method
        automatically adjusts the date to fetch the correct historical data.

        Returns a dictionary containing multiple DataFrames:
        - dam_gen_resource: Generation resource data
        - dam_gen_resource_as_offers: Generation resource AS offers
        - dam_load_resource: Load resource data
        - dam_load_resource_as_offers: Load resource AS offers
        - dam_energy_only_offers: Energy-only offers
        - dam_energy_only_offer_awards: Energy-only offer awards
        - dam_energy_bids: Energy bids
        - dam_energy_bid_awards: Energy bid awards
        - dam_ptp_obligation_bids: PTP obligation bids
        - dam_ptp_obligation_bid_awards: PTP obligation bid awards
        - dam_ptp_obligation_options: PTP obligation options
        - dam_ptp_obligation_option_awards: PTP obligation option awards

        Args:
            date: Date to fetch disclosure for (data is 60 days delayed)

        Returns:
            Dictionary of DataFrames keyed by report name

        Example:
            ```python
            ercot = ERCOT(auth=auth)

            # Get disclosure for 60 days ago
            reports = ercot.get_60_day_dam_disclosure("today")

            # Access specific reports
            gen_offers = reports["dam_gen_resource_as_offers"]
            load_data = reports["dam_load_resource"]
            ```
        """
        date_ts = parse_date(date)

        # Data is published 60 days after the operating day
        report_date = date_ts + pd.Timedelta(days=60)
        end_date = report_date + pd.Timedelta(days=1)

        archive = self._get_archive()

        # Fetch from archive
        df = archive.fetch_historical(
            endpoint="/np3-966-er/60_dam_gen_res_data",
            start=report_date,
            end=end_date,
        )

        # For now, return a single DataFrame
        # Full implementation would parse the zip and extract multiple files
        return {
            "dam_gen_resource": df,
            "dam_gen_resource_as_offers": self.get_dam_gen_res_as_offers(),
            "dam_load_resource": self.get_dam_load_res_data(),
            "dam_load_resource_as_offers": self.get_dam_load_res_as_offers(),
            "dam_energy_only_offers": self.get_dam_energy_only_offers(),
            "dam_energy_only_offer_awards": self.get_dam_energy_only_offer_awards(),
            "dam_energy_bids": self.get_dam_energy_bids(),
            "dam_energy_bid_awards": self.get_dam_energy_bid_awards(),
            "dam_ptp_obligation_bids": self.get_dam_ptp_obl_bids(),
            "dam_ptp_obligation_bid_awards": self.get_dam_ptp_obl_bid_awards(),
            "dam_ptp_obligation_options": self.get_dam_ptp_obl_opt(),
            "dam_ptp_obligation_option_awards": self.get_dam_ptp_obl_opt_awards(),
        }

    def get_60_day_sced_disclosure(
        self,
        date: str | pd.Timestamp = "today",
    ) -> dict[str, pd.DataFrame]:
        """Get 60-Day SCED Disclosure Reports.

        ERCOT publishes these reports with a 60-day delay. This method
        automatically adjusts the date to fetch the correct historical data.

        Returns a dictionary containing:
        - sced_gen_resource: SCED generation resource data
        - sced_load_resource: SCED load resource data
        - sced_smne: SCED SMNE generation resource data

        Args:
            date: Date to fetch disclosure for (data is 60 days delayed)

        Returns:
            Dictionary of DataFrames keyed by report name

        Example:
            ```python
            ercot = ERCOT(auth=auth)

            # Get SCED disclosure
            reports = ercot.get_60_day_sced_disclosure("2024-01-15")

            # Access specific reports
            gen_data = reports["sced_gen_resource"]
            ```
        """
        date_ts = parse_date(date)

        # Data is published 60 days after the operating day
        report_date = date_ts + pd.Timedelta(days=60)
        end_date = report_date + pd.Timedelta(days=1)

        archive = self._get_archive()

        # Fetch SMNE data from archive
        smne_df = archive.fetch_historical(
            endpoint="/np3-965-er/60_sced_smne_gen_res",
            start=report_date,
            end=end_date,
        )

        return {
            "sced_gen_resource": self.get_sced_gen_res_data(),
            "sced_load_resource": self.get_load_res_data_in_sced(),
            "sced_smne": smne_df,
        }
