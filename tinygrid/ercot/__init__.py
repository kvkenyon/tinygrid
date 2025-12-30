"""ERCOT SDK client for accessing ERCOT grid data.

This package provides a comprehensive interface for accessing ERCOT data
through multiple sources:
- Live REST API for recent data
- Archive API for historical data (>90 days)
- Dashboard JSON for real-time status (no auth required)
- MIS Documents for yearly historical data
"""

from __future__ import annotations

from attrs import define

# Re-export pyercot endpoints for backward compatibility with tests
# IMPORTANT: These must be imported BEFORE the mixin classes because
# endpoints.py imports from this package namespace
from pyercot.api.emil_products import (
    get_list_for_products,
    get_product,
    get_product_history,
)
from pyercot.api.np3_233_cd import hourly_res_outage_cap
from pyercot.api.np3_565_cd import lf_by_model_weather_zone
from pyercot.api.np3_566_cd import lf_by_model_study_area
from pyercot.api.np3_910_er import (
    endpoint_2d_agg_dsr_loads,
    endpoint_2d_agg_gen_summary,
    endpoint_2d_agg_gen_summary_houston,
    endpoint_2d_agg_gen_summary_north,
    endpoint_2d_agg_gen_summary_south,
    endpoint_2d_agg_gen_summary_west,
    endpoint_2d_agg_load_summary,
    endpoint_2d_agg_load_summary_houston,
    endpoint_2d_agg_load_summary_north,
    endpoint_2d_agg_load_summary_south,
    endpoint_2d_agg_load_summary_west,
    endpoint_2d_agg_out_sched,
    endpoint_2d_agg_out_sched_houston,
    endpoint_2d_agg_out_sched_north,
    endpoint_2d_agg_out_sched_south,
    endpoint_2d_agg_out_sched_west,
)
from pyercot.api.np3_911_er import (
    endpoint_2d_agg_as_offers_ecrsm,
    endpoint_2d_agg_as_offers_ecrss,
    endpoint_2d_agg_as_offers_offns,
    endpoint_2d_agg_as_offers_onns,
    endpoint_2d_agg_as_offers_regdn,
    endpoint_2d_agg_as_offers_regup,
    endpoint_2d_agg_as_offers_rrsffr,
    endpoint_2d_agg_as_offers_rrspfr,
    endpoint_2d_agg_as_offers_rrsufr,
    endpoint_2d_cleared_dam_as_ecrsm,
    endpoint_2d_cleared_dam_as_ecrss,
    endpoint_2d_cleared_dam_as_nspin,
    endpoint_2d_cleared_dam_as_regdn,
    endpoint_2d_cleared_dam_as_regup,
    endpoint_2d_cleared_dam_as_rrsffr,
    endpoint_2d_cleared_dam_as_rrspfr,
    endpoint_2d_cleared_dam_as_rrsufr,
    endpoint_2d_self_arranged_as_ecrsm,
    endpoint_2d_self_arranged_as_ecrss,
    endpoint_2d_self_arranged_as_nspin,
    endpoint_2d_self_arranged_as_nspnm,
    endpoint_2d_self_arranged_as_regdn,
    endpoint_2d_self_arranged_as_regup,
    endpoint_2d_self_arranged_as_rrsffr,
    endpoint_2d_self_arranged_as_rrspfr,
    endpoint_2d_self_arranged_as_rrsufr,
)
from pyercot.api.np3_965_er import (
    endpoint_60_hdl_ldl_man_override,
    endpoint_60_load_res_data_in_sced,
    endpoint_60_sced_dsr_load_data,
    endpoint_60_sced_gen_res_data,
    endpoint_60_sced_qse_self_arranged_as,
    endpoint_60_sced_smne_gen_res,
)
from pyercot.api.np3_966_er import (
    endpoint_60_dam_energy_bid_awards,
    endpoint_60_dam_energy_bids,
    endpoint_60_dam_energy_only_offer_awards,
    endpoint_60_dam_energy_only_offers,
    endpoint_60_dam_gen_res_as_offers,
    endpoint_60_dam_gen_res_data,
    endpoint_60_dam_load_res_as_offers,
    endpoint_60_dam_load_res_data,
    endpoint_60_dam_ptp_obl_bid_awards,
    endpoint_60_dam_ptp_obl_bids,
    endpoint_60_dam_ptp_obl_opt,
    endpoint_60_dam_ptp_obl_opt_awards,
    endpoint_60_dam_qse_self_as,
)
from pyercot.api.np3_990_ex import (
    endpoint_60_sasm_gen_res_as_offer_awards,
    endpoint_60_sasm_gen_res_as_offers,
    endpoint_60_sasm_load_res_as_offer_awards,
    endpoint_60_sasm_load_res_as_offers,
)
from pyercot.api.np3_991_ex import endpoint_60_cop_all_updates
from pyercot.api.np4_33_cd import dam_as_plan
from pyercot.api.np4_159_cd import load_distribution_factors
from pyercot.api.np4_179_cd import total_as_service_offers
from pyercot.api.np4_183_cd import dam_hourly_lmp
from pyercot.api.np4_188_cd import dam_clear_price_for_cap
from pyercot.api.np4_190_cd import dam_stlmnt_pnt_prices
from pyercot.api.np4_191_cd import dam_shadow_prices
from pyercot.api.np4_196_m import (
    dam_price_corrections_eblmp,
    dam_price_corrections_mcpc,
    dam_price_corrections_spp,
)
from pyercot.api.np4_197_m import (
    rtm_price_corrections_eblmp,
    rtm_price_corrections_shadow,
    rtm_price_corrections_soglmp,
    rtm_price_corrections_sogprice,
    rtm_price_corrections_splmp,
    rtm_price_corrections_spp,
)
from pyercot.api.np4_523_cd import dam_system_lambda
from pyercot.api.np4_732_cd import wpp_hrly_avrg_actl_fcast
from pyercot.api.np4_733_cd import wpp_actual_5min_avg_values
from pyercot.api.np4_737_cd import spp_hrly_avrg_actl_fcast
from pyercot.api.np4_738_cd import spp_actual_5min_avg_values
from pyercot.api.np4_742_cd import wpp_hrly_actual_fcast_geo
from pyercot.api.np4_743_cd import wpp_actual_5min_avg_values_geo
from pyercot.api.np4_745_cd import spp_hrly_actual_fcast_geo
from pyercot.api.np4_746_cd import spp_actual_5min_avg_values_geo
from pyercot.api.np6_86_cd import shdw_prices_bnd_trns_const
from pyercot.api.np6_322_cd import sced_system_lambda
from pyercot.api.np6_345_cd import act_sys_load_by_wzn
from pyercot.api.np6_346_cd import act_sys_load_by_fzn
from pyercot.api.np6_787_cd import lmp_electrical_bus
from pyercot.api.np6_788_cd import lmp_node_zone_hub
from pyercot.api.np6_905_cd import spp_node_zone_hub
from pyercot.api.np6_970_cd import rtd_lmp_node_zone_hub
from pyercot.api.versioning import get_version

from pyercot import AuthenticatedClient
from pyercot import Client as ERCOTClient

# Re-export constants for convenience
from ..constants.ercot import (
    ERCOT_TIMEZONE,
    HISTORICAL_THRESHOLD_DAYS,
    LOAD_ZONES,
    TRADING_HUBS,
    LocationType,
    Market,
    SettlementPointType,
)

# Now import the mixin classes (after pyercot modules are in namespace)
from .api import ERCOTAPIMixin
from .archive import ERCOTArchive
from .client import ERCOTBase
from .dashboard import (
    ERCOTDashboardMixin,
    FuelMixEntry,
    GridCondition,
    GridStatus,
    RenewableStatus,
)
from .documents import REPORT_TYPE_IDS, ERCOTDocumentsMixin
from .eia import EIAClient
from .endpoints import ERCOTEndpointsMixin
from .polling import ERCOTPoller, PollResult, poll_latest


@define
class ERCOT(
    ERCOTBase,
    ERCOTEndpointsMixin,
    ERCOTAPIMixin,
    ERCOTDocumentsMixin,
    ERCOTDashboardMixin,
):
    """ERCOT (Electricity Reliability Council of Texas) SDK client.

    Provides a clean, intuitive interface for accessing ERCOT grid data without
    needing to know about endpoint paths, API categories, or client lifecycle management.

    Features:
        - Automatic retry with exponential backoff for transient failures
        - Automatic pagination to fetch all records across multiple pages
        - DataFrame output with human-readable column labels
        - Parallel page fetching for improved performance
        - Intelligent dispatching to appropriate data source

    Example:
        ```python
        from tinygrid import ERCOT

        ercot = ERCOT()

        # High-level API (recommended)
        df = ercot.get_spp(start="2024-01-01", market=Market.REAL_TIME_15_MIN)
        df = ercot.get_lmp(start="today")

        # Low-level endpoint access
        df = ercot.get_lmp_electrical_bus(
            sced_timestamp_from="2024-01-01T08:00:00",
            sced_timestamp_to="2024-01-01T12:00:00",
        )
        ```

    Args:
        base_url: Base URL for the ERCOT API. Defaults to the official ERCOT API URL.
        timeout: Request timeout in seconds. Defaults to 30.0.
        verify_ssl: Whether to verify SSL certificates. Defaults to True.
        raise_on_error: Whether to raise exceptions on errors. Defaults to True.
        auth: Optional ERCOTAuth instance for authenticated requests.
        max_retries: Maximum number of retry attempts for transient failures. Defaults to 3.
        retry_min_wait: Minimum wait time between retries in seconds. Defaults to 1.0.
        retry_max_wait: Maximum wait time between retries in seconds. Defaults to 60.0.
        page_size: Number of records per page when fetching data. Defaults to 10000.
        max_concurrent_requests: Maximum number of concurrent page requests. Defaults to 5.
        rate_limit_enabled: Whether to enforce rate limiting. Defaults to True.
            ERCOT's API has a limit of 30 requests per minute.
        requests_per_minute: Maximum requests per minute when rate limiting is enabled.
            Defaults to 30 (ERCOT's documented limit).
    """

    pass  # All functionality comes from mixins


__all__ = [
    # Main client
    "ERCOT",
    # Constants
    "ERCOT_TIMEZONE",
    "HISTORICAL_THRESHOLD_DAYS",
    "LOAD_ZONES",
    "REPORT_TYPE_IDS",
    "TRADING_HUBS",
    # EIA integration
    "EIAClient",
    # Archive access
    "ERCOTArchive",
    # Polling utilities
    "ERCOTPoller",
    # Dashboard types
    "FuelMixEntry",
    "GridCondition",
    "GridStatus",
    "LocationType",
    "Market",
    "PollResult",
    "RenewableStatus",
    "SettlementPointType",
    "poll_latest",
]
