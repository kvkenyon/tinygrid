"""Parametrized tests to cover ERCOT endpoint wrapper methods."""

from unittest.mock import patch

import pandas as pd
import pytest

from tinygrid import ERCOT

# List of simple endpoint wrapper methods that just call _call_endpoint
SIMPLE_ENDPOINT_METHODS = [
    # Aggregated endpoints
    "get_aggregated_dsr_loads",
    "get_aggregated_generation_summary",
    "get_aggregated_generation_summary_houston",
    "get_aggregated_generation_summary_north",
    "get_aggregated_generation_summary_south",
    "get_aggregated_generation_summary_west",
    "get_aggregated_load_summary",
    "get_aggregated_load_summary_houston",
    "get_aggregated_load_summary_north",
    "get_aggregated_load_summary_south",
    "get_aggregated_load_summary_west",
    "get_aggregated_outage_schedule",
    "get_aggregated_outage_schedule_houston",
    "get_aggregated_outage_schedule_north",
    "get_aggregated_outage_schedule_south",
    "get_aggregated_outage_schedule_west",
    # AS Offers
    "get_aggregated_as_offers_ecrsm",
    "get_aggregated_as_offers_ecrss",
    "get_aggregated_as_offers_offns",
    "get_aggregated_as_offers_onns",
    "get_aggregated_as_offers_regdn",
    "get_aggregated_as_offers_regup",
    "get_aggregated_as_offers_rrsffr",
    "get_aggregated_as_offers_rrspfr",
    "get_aggregated_as_offers_rrsufr",
    # SCED Disclosure
    "get_sced_dsr_load_data",
    "get_sced_gen_res_data",
    "get_sced_smne_gen_res",
    "get_load_res_data_in_sced",
    "get_hdl_ldl_manual_override",
    "get_sced_qse_self_arranged_as",
    # SASM
    "get_sasm_gen_res_as_offers",
    "get_sasm_gen_res_as_offer_awards",
    "get_sasm_load_res_as_offers",
    "get_sasm_load_res_as_offer_awards",
    # Price Corrections
    "get_rtm_price_corrections_eblmp",
    "get_rtm_price_corrections_spp",
    "get_rtm_price_corrections_shadow",
    "get_rtm_price_corrections_soglmp",
    "get_rtm_price_corrections_sogprice",
    "get_rtm_price_corrections_splmp",
    "get_dam_price_corrections_eblmp",
    "get_dam_price_corrections_mcpc",
    "get_dam_price_corrections_spp",
    # Cleared AS
    "get_cleared_dam_as_ecrsm",
    "get_cleared_dam_as_ecrss",
    "get_cleared_dam_as_nspin",
    "get_cleared_dam_as_regdn",
    "get_cleared_dam_as_regup",
    "get_cleared_dam_as_rrsffr",
    "get_cleared_dam_as_rrspfr",
    "get_cleared_dam_as_rrsufr",
    # Self-arranged AS
    "get_self_arranged_as_ecrsm",
    "get_self_arranged_as_ecrss",
    "get_self_arranged_as_nspin",
    "get_self_arranged_as_nspnm",
    "get_self_arranged_as_regdn",
    "get_self_arranged_as_regup",
    "get_self_arranged_as_rrsffr",
    "get_self_arranged_as_rrspfr",
    "get_self_arranged_as_rrsufr",
    # DAM Disclosure
    "get_dam_energy_bid_awards",
    "get_dam_energy_bids",
    "get_dam_energy_only_offer_awards",
    "get_dam_energy_only_offers",
    "get_dam_gen_res_as_offers",
    "get_dam_gen_res_data",
    "get_dam_load_res_as_offers",
    "get_dam_load_res_data",
    "get_dam_ptp_obl_bid_awards",
    "get_dam_ptp_obl_bids",
    "get_dam_ptp_obl_opt",
    "get_dam_ptp_obl_opt_awards",
    "get_dam_qse_self_as",
    # Load and forecasting
    "get_actual_system_load_by_weather_zone",
    "get_actual_system_load_by_forecast_zone",
    "get_wpp_hourly_average_actual_forecast",
    "get_wpp_actual_5min_avg_values",
    "get_wpp_hourly_actual_forecast_geo",
    "get_wpp_actual_5min_avg_values_geo",
    "get_spp_hourly_average_actual_forecast",
    "get_spp_actual_5min_avg_values",
    "get_spp_hourly_actual_forecast_geo",
    "get_spp_actual_5min_avg_values_geo",
    # Pricing
    "get_dam_settlement_point_prices",
    "get_dam_shadow_prices",
    "get_dam_clear_price_for_cap",
    "get_dam_system_lambda",
    "get_sced_system_lambda",
    "get_lmp_electrical_bus",
    "get_lmp_node_zone_hub",
    "get_spp_node_zone_hub",
    "get_rtd_lmp_node_zone_hub",
    "get_shadow_prices_bound_transmission_constraint",
    # Other
    "get_hourly_res_outage_cap",
    "get_total_as_service_offers",
    "get_load_distribution_factors",
]


class TestSimpleEndpointWrappers:
    """Test simple endpoint wrapper methods using parametrization."""

    @pytest.mark.parametrize("method_name", SIMPLE_ENDPOINT_METHODS)
    @patch.object(ERCOT, "_call_endpoint")
    def test_endpoint_wrapper(self, mock_call_endpoint, method_name):
        """Test that endpoint wrapper methods call _call_endpoint and return DataFrame."""
        # Setup mock
        mock_call_endpoint.return_value = pd.DataFrame({"test": [1, 2, 3]})

        # Create client and call method
        ercot = ERCOT()
        method = getattr(ercot, method_name)
        result = method()

        # Verify
        assert isinstance(result, pd.DataFrame)
        mock_call_endpoint.assert_called_once()
