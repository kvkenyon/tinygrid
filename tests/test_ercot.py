"""Tests for ERCOT SDK client"""

from unittest.mock import patch

import pytest

from tinygrid import ERCOT
from tinygrid.errors import GridAPIError, GridTimeoutError


class TestERCOT:
    """Test the ERCOT SDK client"""

    def test_initialization_default(self):
        """Test initializing ERCOT with default parameters."""
        ercot = ERCOT()
        assert ercot.base_url == "https://api.ercot.com/api/public-reports"
        assert ercot.timeout == 30.0
        assert ercot.verify_ssl is True
        assert ercot.raise_on_error is True

    def test_initialization_custom(self):
        """Test initializing ERCOT with custom parameters."""
        ercot = ERCOT(
            base_url="https://custom.api.com",
            timeout=60.0,
            verify_ssl=False,
            raise_on_error=False,
        )
        assert ercot.base_url == "https://custom.api.com"
        assert ercot.timeout == 60.0
        assert ercot.verify_ssl is False
        assert ercot.raise_on_error is False

    def test_iso_name(self):
        """Test the iso_name property."""
        ercot = ERCOT()
        assert ercot.iso_name == "ERCOT"

    def test_repr(self):
        """Test the string representation."""
        ercot = ERCOT()
        repr_str = repr(ercot)
        assert "ERCOT" in repr_str
        assert "api.ercot.com" in repr_str

    def test_get_client_creates_new_client(self):
        """Test that _get_client creates a new client when needed."""
        ercot = ERCOT()
        assert ercot._client is None

        client = ercot._get_client()
        assert ercot._client is not None
        assert isinstance(client, type(ercot._client))

    def test_get_client_reuses_existing_client(self):
        """Test that _get_client reuses existing client."""
        ercot = ERCOT()
        client1 = ercot._get_client()
        client2 = ercot._get_client()
        assert client1 is client2

    def test_context_manager_sync(self):
        """Test using ERCOT as a synchronous context manager."""
        ercot = ERCOT()
        with ercot:
            assert ercot._client is not None

    @pytest.mark.asyncio
    async def test_context_manager_async(self):
        """Test using ERCOT as an asynchronous context manager."""
        ercot = ERCOT()
        async with ercot:
            assert ercot._client is not None

    @patch("tinygrid.ercot.lf_by_model_weather_zone")
    def test_get_load_forecast_by_weather_zone_success(self, mock_endpoint, sample_report):
        """Test successful load forecast retrieval."""
        mock_endpoint.sync.return_value = sample_report

        ercot = ERCOT()
        result = ercot.get_load_forecast_by_weather_zone(
            start_date="2024-01-01",
            end_date="2024-01-07",
            model="WEATHERZONE",
        )

        assert isinstance(result, dict)
        assert "deliveryDate" in result
        assert "systemTotal" in result
        mock_endpoint.sync.assert_called_once()

    @patch("tinygrid.ercot.lf_by_model_weather_zone")
    def test_get_load_forecast_by_weather_zone_none_response(self, mock_endpoint):
        """Test handling of None response."""
        mock_endpoint.sync.return_value = None

        ercot = ERCOT()
        result = ercot.get_load_forecast_by_weather_zone(
            start_date="2024-01-01",
            end_date="2024-01-07",
        )

        assert result == {}

    @patch("tinygrid.ercot.lf_by_model_weather_zone")
    def test_get_load_forecast_by_weather_zone_normalizes_dates(self, mock_endpoint, sample_report):
        """Test that dates are normalized."""
        mock_endpoint.sync.return_value = sample_report

        ercot = ERCOT()
        ercot.get_load_forecast_by_weather_zone(
            start_date=" 2024-01-01 ",
            end_date=" 2024-01-07 ",
        )

        call_args = mock_endpoint.sync.call_args
        assert call_args.kwargs["delivery_date_from"] == "2024-01-01"
        assert call_args.kwargs["delivery_date_to"] == "2024-01-07"

    @patch("tinygrid.ercot.lf_by_model_weather_zone")
    def test_get_load_forecast_by_weather_zone_passes_kwargs(self, mock_endpoint, sample_report):
        """Test that additional kwargs are passed through."""
        mock_endpoint.sync.return_value = sample_report

        ercot = ERCOT()
        ercot.get_load_forecast_by_weather_zone(
            start_date="2024-01-01",
            end_date="2024-01-07",
            hour_ending="1",
            page=1,
        )

        call_args = mock_endpoint.sync.call_args
        assert call_args.kwargs["hour_ending"] == "1"
        assert call_args.kwargs["page"] == 1

    @patch("tinygrid.ercot.lf_by_model_weather_zone")
    def test_get_load_forecast_by_weather_zone_handles_unexpected_status(
        self, mock_endpoint
    ):
        """Test handling of UnexpectedStatus errors."""
        from pyercot.errors import UnexpectedStatus

        mock_endpoint.sync.side_effect = UnexpectedStatus(
            status_code=500, content=b"Server error"
        )

        ercot = ERCOT()
        with pytest.raises(GridAPIError) as exc_info:
            ercot.get_load_forecast_by_weather_zone(
                start_date="2024-01-01",
                end_date="2024-01-07",
            )

        assert exc_info.value.status_code == 500
        assert "unexpected status" in exc_info.value.message.lower()

    @patch("tinygrid.ercot.lf_by_model_weather_zone")
    def test_get_load_forecast_by_weather_zone_handles_timeout(self, mock_endpoint):
        """Test handling of timeout errors."""
        mock_endpoint.sync.side_effect = TimeoutError("Request timed out")

        ercot = ERCOT()
        with pytest.raises(GridTimeoutError) as exc_info:
            ercot.get_load_forecast_by_weather_zone(
                start_date="2024-01-01",
                end_date="2024-01-07",
            )

        assert exc_info.value.timeout == 30.0

    @patch("tinygrid.ercot.lf_by_model_weather_zone")
    def test_get_load_forecast_by_weather_zone_handles_generic_error(
        self, mock_endpoint
    ):
        """Test handling of generic errors."""
        mock_endpoint.sync.side_effect = ValueError("Unexpected error")

        ercot = ERCOT()
        with pytest.raises(GridAPIError) as exc_info:
            ercot.get_load_forecast_by_weather_zone(
                start_date="2024-01-01",
                end_date="2024-01-07",
            )

        assert "unexpected error" in exc_info.value.message.lower()

    # ============================================================================
    # Helper Methods Tests
    # ============================================================================

    def test_extract_response_data_with_report(self, sample_report):
        """Test _extract_response_data with Report object."""
        ercot = ERCOT()
        result = ercot._extract_response_data(sample_report)
        assert isinstance(result, dict)
        assert "deliveryDate" in result
        assert "systemTotal" in result

    def test_extract_response_data_with_none(self):
        """Test _extract_response_data with None."""
        ercot = ERCOT()
        result = ercot._extract_response_data(None)
        assert result == {}

    def test_extract_response_data_with_dict(self):
        """Test _extract_response_data with dict."""
        ercot = ERCOT()
        data = {"key": "value"}
        result = ercot._extract_response_data(data)
        assert result == data

    def test_extract_response_data_with_product(self):
        """Test _extract_response_data with Product object."""
        from pyercot.models.product import Product

        ercot = ERCOT()
        product = Product()
        product.emil_id = "TEST123"
        product.name = "Test Product"
        result = ercot._extract_response_data(product)
        assert isinstance(result, dict)
        assert "emil_id" in result or "emilId" in result

    def test_call_endpoint_success(self, sample_report):
        """Test _call_endpoint with successful response."""
        from unittest.mock import MagicMock

        ercot = ERCOT()
        mock_endpoint = MagicMock()
        mock_endpoint.sync.return_value = sample_report

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        ercot._client = mock_client

        result = ercot._call_endpoint(mock_endpoint, "test_endpoint")
        assert isinstance(result, dict)
        mock_endpoint.sync.assert_called_once_with(client=mock_client)

    def test_call_endpoint_error_handling(self):
        """Test _call_endpoint error handling."""
        from unittest.mock import MagicMock

        from pyercot.errors import UnexpectedStatus

        ercot = ERCOT()
        mock_endpoint = MagicMock()
        mock_endpoint.sync.side_effect = UnexpectedStatus(
            status_code=500, content=b"Error"
        )

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        ercot._client = mock_client

        with pytest.raises(GridAPIError):
            ercot._call_endpoint(mock_endpoint, "test_endpoint")

    # ============================================================================
    # EMIL Products Endpoints Tests
    # ============================================================================

    @patch("tinygrid.ercot.get_list_for_products")
    def test_get_list_for_products(self, mock_endpoint, sample_report):
        """Test get_list_for_products."""
        mock_endpoint.sync.return_value = sample_report
        ercot = ERCOT()
        result = ercot.get_list_for_products()
        assert isinstance(result, dict)
        mock_endpoint.sync.assert_called_once()

    @patch("tinygrid.ercot.get_product")
    def test_get_product(self, mock_endpoint, sample_report):
        """Test get_product."""
        mock_endpoint.sync.return_value = sample_report
        ercot = ERCOT()
        result = ercot.get_product("TEST123")
        assert isinstance(result, dict)
        mock_endpoint.sync.assert_called_once_with(client=mock_endpoint.sync.call_args[1]["client"], emil_id="TEST123")

    @patch("tinygrid.ercot.get_product_history")
    def test_get_product_history(self, mock_endpoint, sample_report):
        """Test get_product_history."""
        mock_endpoint.sync.return_value = sample_report
        ercot = ERCOT()
        result = ercot.get_product_history("TEST123")
        assert isinstance(result, dict)
        mock_endpoint.sync.assert_called_once()

    @patch("tinygrid.ercot.get_version")
    def test_get_version(self, mock_endpoint, sample_report):
        """Test get_version."""
        mock_endpoint.sync.return_value = sample_report
        ercot = ERCOT()
        result = ercot.get_version()
        assert isinstance(result, dict)
        mock_endpoint.sync.assert_called_once()

    # ============================================================================
    # Load Forecasting Endpoints Tests
    # ============================================================================

    @patch("tinygrid.ercot.lf_by_model_study_area")
    def test_get_load_forecast_by_study_area(self, mock_endpoint, sample_report):
        """Test get_load_forecast_by_study_area."""
        mock_endpoint.sync.return_value = sample_report
        ercot = ERCOT()
        result = ercot.get_load_forecast_by_study_area(
            start_date="2024-01-01",
            end_date="2024-01-07",
        )
        assert isinstance(result, dict)
        call_args = mock_endpoint.sync.call_args
        assert call_args.kwargs["delivery_date_from"] == "2024-01-01"
        assert call_args.kwargs["delivery_date_to"] == "2024-01-07"

    # ============================================================================
    # Real-Time Operations Endpoints Tests
    # ============================================================================

    @pytest.mark.parametrize(
        "method_name,endpoint_name",
        [
            ("get_aggregated_dsr_loads", "endpoint_2d_agg_dsr_loads"),
            ("get_aggregated_generation_summary", "endpoint_2d_agg_gen_summary"),
            ("get_aggregated_generation_summary_houston", "endpoint_2d_agg_gen_summary_houston"),
            ("get_aggregated_generation_summary_north", "endpoint_2d_agg_gen_summary_north"),
            ("get_aggregated_generation_summary_south", "endpoint_2d_agg_gen_summary_south"),
            ("get_aggregated_generation_summary_west", "endpoint_2d_agg_gen_summary_west"),
            ("get_aggregated_load_summary", "endpoint_2d_agg_load_summary"),
            ("get_aggregated_load_summary_houston", "endpoint_2d_agg_load_summary_houston"),
            ("get_aggregated_load_summary_north", "endpoint_2d_agg_load_summary_north"),
            ("get_aggregated_load_summary_south", "endpoint_2d_agg_load_summary_south"),
            ("get_aggregated_load_summary_west", "endpoint_2d_agg_load_summary_west"),
            ("get_aggregated_outage_schedule", "endpoint_2d_agg_out_sched"),
            ("get_aggregated_outage_schedule_houston", "endpoint_2d_agg_out_sched_houston"),
            ("get_aggregated_outage_schedule_north", "endpoint_2d_agg_out_sched_north"),
            ("get_aggregated_outage_schedule_south", "endpoint_2d_agg_out_sched_south"),
            ("get_aggregated_outage_schedule_west", "endpoint_2d_agg_out_sched_west"),
        ],
    )
    def test_real_time_operations_endpoints(self, method_name, endpoint_name, sample_report):
        """Test real-time operations endpoints."""
        ercot = ERCOT()
        method = getattr(ercot, method_name)

        with patch(f"tinygrid.ercot.{endpoint_name}") as mock_endpoint:
            mock_endpoint.sync.return_value = sample_report
            result = method()
            assert isinstance(result, dict)
            mock_endpoint.sync.assert_called_once()

    # ============================================================================
    # Ancillary Services Endpoints Tests
    # ============================================================================

    @pytest.mark.parametrize(
        "method_name,endpoint_name",
        [
            ("get_aggregated_as_offers_ecrsm", "endpoint_2d_agg_as_offers_ecrsm"),
            ("get_aggregated_as_offers_ecrss", "endpoint_2d_agg_as_offers_ecrss"),
            ("get_aggregated_as_offers_offns", "endpoint_2d_agg_as_offers_offns"),
            ("get_aggregated_as_offers_onns", "endpoint_2d_agg_as_offers_onns"),
            ("get_aggregated_as_offers_regdn", "endpoint_2d_agg_as_offers_regdn"),
            ("get_aggregated_as_offers_regup", "endpoint_2d_agg_as_offers_regup"),
            ("get_aggregated_as_offers_rrsffr", "endpoint_2d_agg_as_offers_rrsffr"),
            ("get_aggregated_as_offers_rrspfr", "endpoint_2d_agg_as_offers_rrspfr"),
            ("get_aggregated_as_offers_rrsufr", "endpoint_2d_agg_as_offers_rrsufr"),
            ("get_cleared_dam_as_ecrsm", "endpoint_2d_cleared_dam_as_ecrsm"),
            ("get_cleared_dam_as_ecrss", "endpoint_2d_cleared_dam_as_ecrss"),
            ("get_cleared_dam_as_nspin", "endpoint_2d_cleared_dam_as_nspin"),
            ("get_cleared_dam_as_regdn", "endpoint_2d_cleared_dam_as_regdn"),
            ("get_cleared_dam_as_regup", "endpoint_2d_cleared_dam_as_regup"),
            ("get_cleared_dam_as_rrsffr", "endpoint_2d_cleared_dam_as_rrsffr"),
            ("get_cleared_dam_as_rrspfr", "endpoint_2d_cleared_dam_as_rrspfr"),
            ("get_cleared_dam_as_rrsufr", "endpoint_2d_cleared_dam_as_rrsufr"),
            ("get_self_arranged_as_ecrsm", "endpoint_2d_self_arranged_as_ecrsm"),
            ("get_self_arranged_as_ecrss", "endpoint_2d_self_arranged_as_ecrss"),
            ("get_self_arranged_as_nspin", "endpoint_2d_self_arranged_as_nspin"),
            ("get_self_arranged_as_nspnm", "endpoint_2d_self_arranged_as_nspnm"),
            ("get_self_arranged_as_regdn", "endpoint_2d_self_arranged_as_regdn"),
            ("get_self_arranged_as_regup", "endpoint_2d_self_arranged_as_regup"),
            ("get_self_arranged_as_rrsffr", "endpoint_2d_self_arranged_as_rrsffr"),
            ("get_self_arranged_as_rrspfr", "endpoint_2d_self_arranged_as_rrspfr"),
            ("get_self_arranged_as_rrsufr", "endpoint_2d_self_arranged_as_rrsufr"),
        ],
    )
    def test_ancillary_services_endpoints(self, method_name, endpoint_name, sample_report):
        """Test ancillary services endpoints."""
        ercot = ERCOT()
        method = getattr(ercot, method_name)

        with patch(f"tinygrid.ercot.{endpoint_name}") as mock_endpoint:
            mock_endpoint.sync.return_value = sample_report
            result = method()
            assert isinstance(result, dict)
            mock_endpoint.sync.assert_called_once()

    # ============================================================================
    # SCED Endpoints Tests
    # ============================================================================

    @pytest.mark.parametrize(
        "method_name,endpoint_name",
        [
            ("get_hdl_ldl_manual_override", "endpoint_60_hdl_ldl_man_override"),
            ("get_load_res_data_in_sced", "endpoint_60_load_res_data_in_sced"),
            ("get_sced_dsr_load_data", "endpoint_60_sced_dsr_load_data"),
            ("get_sced_gen_res_data", "endpoint_60_sced_gen_res_data"),
            ("get_sced_qse_self_arranged_as", "endpoint_60_sced_qse_self_arranged_as"),
            ("get_sced_smne_gen_res", "endpoint_60_sced_smne_gen_res"),
        ],
    )
    def test_sced_endpoints(self, method_name, endpoint_name, sample_report):
        """Test SCED endpoints."""
        ercot = ERCOT()
        method = getattr(ercot, method_name)

        with patch(f"tinygrid.ercot.{endpoint_name}") as mock_endpoint:
            mock_endpoint.sync.return_value = sample_report
            result = method()
            assert isinstance(result, dict)
            mock_endpoint.sync.assert_called_once()

    # ============================================================================
    # Day-Ahead Market Endpoints Tests
    # ============================================================================

    @pytest.mark.parametrize(
        "method_name,endpoint_name",
        [
            ("get_dam_energy_bid_awards", "endpoint_60_dam_energy_bid_awards"),
            ("get_dam_energy_bids", "endpoint_60_dam_energy_bids"),
            ("get_dam_energy_only_offer_awards", "endpoint_60_dam_energy_only_offer_awards"),
            ("get_dam_energy_only_offers", "endpoint_60_dam_energy_only_offers"),
            ("get_dam_gen_res_as_offers", "endpoint_60_dam_gen_res_as_offers"),
            ("get_dam_gen_res_data", "endpoint_60_dam_gen_res_data"),
            ("get_dam_load_res_as_offers", "endpoint_60_dam_load_res_as_offers"),
            ("get_dam_load_res_data", "endpoint_60_dam_load_res_data"),
            ("get_dam_ptp_obl_bid_awards", "endpoint_60_dam_ptp_obl_bid_awards"),
            ("get_dam_ptp_obl_bids", "endpoint_60_dam_ptp_obl_bids"),
            ("get_dam_ptp_obl_opt_awards", "endpoint_60_dam_ptp_obl_opt_awards"),
            ("get_dam_ptp_obl_opt", "endpoint_60_dam_ptp_obl_opt"),
            ("get_dam_qse_self_as", "endpoint_60_dam_qse_self_as"),
        ],
    )
    def test_dam_endpoints(self, method_name, endpoint_name, sample_report):
        """Test day-ahead market endpoints."""
        ercot = ERCOT()
        method = getattr(ercot, method_name)

        with patch(f"tinygrid.ercot.{endpoint_name}") as mock_endpoint:
            mock_endpoint.sync.return_value = sample_report
            result = method()
            assert isinstance(result, dict)
            mock_endpoint.sync.assert_called_once()

    # ============================================================================
    # SASM Endpoints Tests
    # ============================================================================

    @pytest.mark.parametrize(
        "method_name,endpoint_name",
        [
            ("get_sasm_gen_res_as_offer_awards", "endpoint_60_sasm_gen_res_as_offer_awards"),
            ("get_sasm_gen_res_as_offers", "endpoint_60_sasm_gen_res_as_offers"),
            ("get_sasm_load_res_as_offer_awards", "endpoint_60_sasm_load_res_as_offer_awards"),
            ("get_sasm_load_res_as_offers", "endpoint_60_sasm_load_res_as_offers"),
            ("get_cop_all_updates", "endpoint_60_cop_all_updates"),
        ],
    )
    def test_sasm_endpoints(self, method_name, endpoint_name, sample_report):
        """Test SASM endpoints."""
        ercot = ERCOT()
        method = getattr(ercot, method_name)

        with patch(f"tinygrid.ercot.{endpoint_name}") as mock_endpoint:
            mock_endpoint.sync.return_value = sample_report
            result = method()
            assert isinstance(result, dict)
            mock_endpoint.sync.assert_called_once()

    # ============================================================================
    # DAM Pricing Endpoints Tests
    # ============================================================================

    @patch("tinygrid.ercot.dam_hourly_lmp")
    def test_get_dam_hourly_lmp(self, mock_endpoint, sample_report):
        """Test get_dam_hourly_lmp."""
        mock_endpoint.sync.return_value = sample_report
        ercot = ERCOT()
        result = ercot.get_dam_hourly_lmp(
            start_date="2024-01-01",
            end_date="2024-01-07",
        )
        assert isinstance(result, dict)
        call_args = mock_endpoint.sync.call_args
        assert call_args.kwargs["delivery_date_from"] == "2024-01-01"
        assert call_args.kwargs["delivery_date_to"] == "2024-01-07"

    @pytest.mark.parametrize(
        "method_name,endpoint_name",
        [
            ("get_dam_clear_price_for_cap", "dam_clear_price_for_cap"),
            ("get_dam_settlement_point_prices", "dam_stlmnt_pnt_prices"),
            ("get_dam_shadow_prices", "dam_shadow_prices"),
            ("get_dam_as_plan", "dam_as_plan"),
            ("get_dam_system_lambda", "dam_system_lambda"),
            ("get_load_distribution_factors", "load_distribution_factors"),
            ("get_total_as_service_offers", "total_as_service_offers"),
        ],
    )
    def test_dam_pricing_endpoints(self, method_name, endpoint_name, sample_report):
        """Test DAM pricing endpoints."""
        ercot = ERCOT()
        method = getattr(ercot, method_name)

        with patch(f"tinygrid.ercot.{endpoint_name}") as mock_endpoint:
            mock_endpoint.sync.return_value = sample_report
            result = method()
            assert isinstance(result, dict)
            mock_endpoint.sync.assert_called_once()

    # ============================================================================
    # Price Corrections Endpoints Tests
    # ============================================================================

    @pytest.mark.parametrize(
        "method_name,endpoint_name",
        [
            ("get_dam_price_corrections_eblmp", "dam_price_corrections_eblmp"),
            ("get_dam_price_corrections_mcpc", "dam_price_corrections_mcpc"),
            ("get_dam_price_corrections_spp", "dam_price_corrections_spp"),
            ("get_rtm_price_corrections_eblmp", "rtm_price_corrections_eblmp"),
            ("get_rtm_price_corrections_shadow", "rtm_price_corrections_shadow"),
            ("get_rtm_price_corrections_soglmp", "rtm_price_corrections_soglmp"),
            ("get_rtm_price_corrections_sogprice", "rtm_price_corrections_sogprice"),
            ("get_rtm_price_corrections_splmp", "rtm_price_corrections_splmp"),
            ("get_rtm_price_corrections_spp", "rtm_price_corrections_spp"),
        ],
    )
    def test_price_corrections_endpoints(self, method_name, endpoint_name, sample_report):
        """Test price corrections endpoints."""
        ercot = ERCOT()
        method = getattr(ercot, method_name)

        with patch(f"tinygrid.ercot.{endpoint_name}") as mock_endpoint:
            mock_endpoint.sync.return_value = sample_report
            result = method()
            assert isinstance(result, dict)
            mock_endpoint.sync.assert_called_once()

    # ============================================================================
    # Wind and Solar Power Endpoints Tests
    # ============================================================================

    @pytest.mark.parametrize(
        "method_name,endpoint_name",
        [
            ("get_wpp_hourly_average_actual_forecast", "wpp_hrly_avrg_actl_fcast"),
            ("get_wpp_actual_5min_avg_values", "wpp_actual_5min_avg_values"),
            ("get_spp_hourly_average_actual_forecast", "spp_hrly_avrg_actl_fcast"),
            ("get_spp_actual_5min_avg_values", "spp_actual_5min_avg_values"),
            ("get_wpp_hourly_actual_forecast_geo", "wpp_hrly_actual_fcast_geo"),
            ("get_wpp_actual_5min_avg_values_geo", "wpp_actual_5min_avg_values_geo"),
            ("get_spp_hourly_actual_forecast_geo", "spp_hrly_actual_fcast_geo"),
            ("get_spp_actual_5min_avg_values_geo", "spp_actual_5min_avg_values_geo"),
        ],
    )
    def test_wind_solar_endpoints(self, method_name, endpoint_name, sample_report):
        """Test wind and solar power endpoints."""
        ercot = ERCOT()
        method = getattr(ercot, method_name)

        with patch(f"tinygrid.ercot.{endpoint_name}") as mock_endpoint:
            mock_endpoint.sync.return_value = sample_report
            result = method()
            assert isinstance(result, dict)
            mock_endpoint.sync.assert_called_once()

    # ============================================================================
    # Real-Time Market Endpoints Tests
    # ============================================================================

    @pytest.mark.parametrize(
        "method_name,endpoint_name",
        [
            ("get_sced_system_lambda", "sced_system_lambda"),
            ("get_actual_system_load_by_weather_zone", "act_sys_load_by_wzn"),
            ("get_actual_system_load_by_forecast_zone", "act_sys_load_by_fzn"),
            ("get_lmp_electrical_bus", "lmp_electrical_bus"),
            ("get_lmp_node_zone_hub", "lmp_node_zone_hub"),
            ("get_shadow_prices_bound_transmission_constraint", "shdw_prices_bnd_trns_const"),
            ("get_spp_node_zone_hub", "spp_node_zone_hub"),
            ("get_data", "get_data"),
        ],
    )
    def test_rtm_endpoints(self, method_name, endpoint_name, sample_report):
        """Test real-time market endpoints."""
        ercot = ERCOT()
        method = getattr(ercot, method_name)

        with patch(f"tinygrid.ercot.{endpoint_name}") as mock_endpoint:
            mock_endpoint.sync.return_value = sample_report
            result = method()
            assert isinstance(result, dict)
            mock_endpoint.sync.assert_called_once()

    # ============================================================================
    # Outage Management Endpoints Tests
    # ============================================================================

    @patch("tinygrid.ercot.hourly_res_outage_cap")
    def test_get_hourly_res_outage_cap(self, mock_endpoint, sample_report):
        """Test get_hourly_res_outage_cap."""
        mock_endpoint.sync.return_value = sample_report
        ercot = ERCOT()
        result = ercot.get_hourly_res_outage_cap()
        assert isinstance(result, dict)
        mock_endpoint.sync.assert_called_once()

    # ============================================================================
    # Error Handling Tests for All Endpoints
    # ============================================================================

    @patch("tinygrid.ercot.get_list_for_products")
    def test_get_list_for_products_handles_unexpected_status(self, mock_endpoint):
        """Test that get_list_for_products handles UnexpectedStatus errors."""
        from pyercot.errors import UnexpectedStatus

        mock_endpoint.sync.side_effect = UnexpectedStatus(
            status_code=500, content=b"Server error"
        )

        ercot = ERCOT()
        with pytest.raises(GridAPIError) as exc_info:
            ercot.get_list_for_products()

        assert exc_info.value.status_code == 500

    @patch("tinygrid.ercot.endpoint_2d_agg_dsr_loads")
    def test_get_aggregated_dsr_loads_handles_timeout(self, mock_endpoint):
        """Test that get_aggregated_dsr_loads handles timeout errors."""
        mock_endpoint.sync.side_effect = TimeoutError("Request timed out")

        ercot = ERCOT()
        with pytest.raises(GridTimeoutError) as exc_info:
            ercot.get_aggregated_dsr_loads()

        assert exc_info.value.timeout == 30.0

    @patch("tinygrid.ercot.dam_hourly_lmp")
    def test_get_dam_hourly_lmp_handles_unexpected_status(self, mock_endpoint):
        """Test that get_dam_hourly_lmp handles UnexpectedStatus errors."""
        from pyercot.errors import UnexpectedStatus

        mock_endpoint.sync.side_effect = UnexpectedStatus(
            status_code=500, content=b"Server error"
        )

        ercot = ERCOT()
        with pytest.raises(GridAPIError) as exc_info:
            ercot.get_dam_hourly_lmp(start_date="2024-01-01", end_date="2024-01-07")

        assert exc_info.value.status_code == 500

    # ============================================================================
    # Edge Cases Tests
    # ============================================================================

    @patch("tinygrid.ercot.get_list_for_products")
    def test_endpoint_with_none_response(self, mock_endpoint):
        """Test endpoint handling None response."""
        mock_endpoint.sync.return_value = None
        ercot = ERCOT()
        result = ercot.get_list_for_products()
        assert result == {}

    @patch("tinygrid.ercot.get_list_for_products")
    def test_endpoint_passes_kwargs(self, mock_endpoint, sample_report):
        """Test that endpoints pass kwargs correctly."""
        mock_endpoint.sync.return_value = sample_report
        ercot = ERCOT()
        ercot.get_list_for_products(page=1, size=10, sort="date")
        call_args = mock_endpoint.sync.call_args
        assert call_args.kwargs["page"] == 1
        assert call_args.kwargs["size"] == 10
        assert call_args.kwargs["sort"] == "date"

