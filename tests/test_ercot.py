"""Tests for ERCOT SDK client"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from tinygrid import ERCOT
from tinygrid.errors import (
    GridAPIError,
    GridRetryExhaustedError,
    GridTimeoutError,
)


class TestERCOT:
    """Test the ERCOT SDK client"""

    def test_initialization_default(self):
        """Test initializing ERCOT with default parameters."""
        ercot = ERCOT()
        assert ercot.base_url == "https://api.ercot.com/api/public-reports"
        assert ercot.timeout == 30.0
        assert ercot.verify_ssl is True
        assert ercot.raise_on_error is True
        assert ercot.max_retries == 3
        assert ercot.page_size == 10000

    def test_initialization_custom(self):
        """Test initializing ERCOT with custom parameters."""
        ercot = ERCOT(
            base_url="https://custom.api.com",
            timeout=60.0,
            verify_ssl=False,
            raise_on_error=False,
            max_retries=5,
            page_size=1000,
        )
        assert ercot.base_url == "https://custom.api.com"
        assert ercot.timeout == 60.0
        assert ercot.verify_ssl is False
        assert ercot.raise_on_error is False
        assert ercot.max_retries == 5
        assert ercot.page_size == 1000

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


class TestEndpointMethods:
    """Test endpoint methods return DataFrames."""

    @patch("tinygrid.ercot.lf_by_model_weather_zone")
    def test_get_load_forecast_by_weather_zone_success(
        self, mock_endpoint, sample_single_page_response
    ):
        """Test successful load forecast retrieval returns DataFrame."""
        mock_response = MagicMock()
        mock_response.to_dict.return_value = sample_single_page_response
        mock_endpoint.sync.return_value = mock_response

        ercot = ERCOT(retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        result = ercot.get_load_forecast_by_weather_zone(
            start_date="2024-01-01",
            end_date="2024-01-07",
            model="WEATHERZONE",
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5
        mock_endpoint.sync.assert_called()

    @patch("tinygrid.ercot.lf_by_model_weather_zone")
    def test_get_load_forecast_by_weather_zone_empty_response(
        self, mock_endpoint, sample_empty_response
    ):
        """Test handling of empty response returns empty DataFrame."""
        mock_response = MagicMock()
        mock_response.to_dict.return_value = sample_empty_response
        mock_endpoint.sync.return_value = mock_response

        ercot = ERCOT(retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        result = ercot.get_load_forecast_by_weather_zone(
            start_date="2024-01-01",
            end_date="2024-01-07",
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @patch("tinygrid.ercot.lf_by_model_weather_zone")
    def test_get_load_forecast_by_weather_zone_normalizes_dates(
        self, mock_endpoint, sample_single_page_response
    ):
        """Test that dates are normalized."""
        mock_response = MagicMock()
        mock_response.to_dict.return_value = sample_single_page_response
        mock_endpoint.sync.return_value = mock_response

        ercot = ERCOT(retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        ercot.get_load_forecast_by_weather_zone(
            start_date=" 2024-01-01 ",
            end_date=" 2024-01-07 ",
        )

        call_args = mock_endpoint.sync.call_args
        assert call_args.kwargs["delivery_date_from"] == "2024-01-01"
        assert call_args.kwargs["delivery_date_to"] == "2024-01-07"

    @patch("tinygrid.ercot.lf_by_model_weather_zone")
    def test_get_load_forecast_by_weather_zone_handles_unexpected_status(
        self, mock_endpoint
    ):
        """Test handling of UnexpectedStatus errors."""
        from pyercot.errors import UnexpectedStatus

        mock_endpoint.sync.side_effect = UnexpectedStatus(
            status_code=500, content=b"Server error"
        )

        ercot = ERCOT(max_retries=0, retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        with pytest.raises((GridAPIError, GridRetryExhaustedError)):
            ercot.get_load_forecast_by_weather_zone(
                start_date="2024-01-01",
                end_date="2024-01-07",
            )

    @patch("tinygrid.ercot.lf_by_model_weather_zone")
    def test_get_load_forecast_by_weather_zone_handles_timeout(
        self, mock_endpoint
    ):
        """Test handling of timeout errors."""
        mock_endpoint.sync.side_effect = TimeoutError("Request timed out")

        ercot = ERCOT(max_retries=0, retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        with pytest.raises((GridTimeoutError, GridRetryExhaustedError)):
            ercot.get_load_forecast_by_weather_zone(
                start_date="2024-01-01",
                end_date="2024-01-07",
            )


class TestExtractResponseData:
    """Test the _extract_response_data helper method."""

    def test_extract_response_data_with_report(self, sample_report):
        """Test _extract_response_data with Report object."""
        ercot = ERCOT()
        result = ercot._extract_response_data(sample_report)
        assert isinstance(result, dict)

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


class TestParameterizedEndpoints:
    """Test various endpoint methods with parameterization."""

    @pytest.mark.parametrize(
        "method_name,endpoint_name",
        [
            ("get_aggregated_dsr_loads", "endpoint_2d_agg_dsr_loads"),
            (
                "get_aggregated_generation_summary",
                "endpoint_2d_agg_gen_summary",
            ),
            ("get_aggregated_load_summary", "endpoint_2d_agg_load_summary"),
            ("get_aggregated_outage_schedule", "endpoint_2d_agg_out_sched"),
        ],
    )
    def test_real_time_operations_endpoints_return_dataframe(
        self, method_name, endpoint_name, sample_single_page_response
    ):
        """Test real-time operations endpoints return DataFrames."""
        ercot = ERCOT(retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()
        method = getattr(ercot, method_name)

        with patch(f"tinygrid.ercot.{endpoint_name}") as mock_endpoint:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = sample_single_page_response
            mock_endpoint.sync.return_value = mock_response

            result = method()
            assert isinstance(result, pd.DataFrame)
            mock_endpoint.sync.assert_called()

    @pytest.mark.parametrize(
        "method_name,endpoint_name",
        [
            ("get_sced_system_lambda", "sced_system_lambda"),
            ("get_lmp_electrical_bus", "lmp_electrical_bus"),
            ("get_lmp_node_zone_hub", "lmp_node_zone_hub"),
            ("get_spp_node_zone_hub", "spp_node_zone_hub"),
        ],
    )
    def test_rtm_endpoints_return_dataframe(
        self, method_name, endpoint_name, sample_single_page_response
    ):
        """Test real-time market endpoints return DataFrames."""
        ercot = ERCOT(retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()
        method = getattr(ercot, method_name)

        with patch(f"tinygrid.ercot.{endpoint_name}") as mock_endpoint:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = sample_single_page_response
            mock_endpoint.sync.return_value = mock_response

            result = method()
            assert isinstance(result, pd.DataFrame)
            mock_endpoint.sync.assert_called()

    @pytest.mark.parametrize(
        "method_name,endpoint_name",
        [
            ("get_dam_clear_price_for_cap", "dam_clear_price_for_cap"),
            ("get_dam_settlement_point_prices", "dam_stlmnt_pnt_prices"),
            ("get_dam_shadow_prices", "dam_shadow_prices"),
            ("get_dam_as_plan", "dam_as_plan"),
            ("get_dam_system_lambda", "dam_system_lambda"),
        ],
    )
    def test_dam_pricing_endpoints_return_dataframe(
        self, method_name, endpoint_name, sample_single_page_response
    ):
        """Test DAM pricing endpoints return DataFrames."""
        ercot = ERCOT(retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()
        method = getattr(ercot, method_name)

        with patch(f"tinygrid.ercot.{endpoint_name}") as mock_endpoint:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = sample_single_page_response
            mock_endpoint.sync.return_value = mock_response

            result = method()
            assert isinstance(result, pd.DataFrame)
            mock_endpoint.sync.assert_called()

    @pytest.mark.parametrize(
        "method_name,endpoint_name",
        [
            (
                "get_wpp_hourly_average_actual_forecast",
                "wpp_hrly_avrg_actl_fcast",
            ),
            ("get_wpp_actual_5min_avg_values", "wpp_actual_5min_avg_values"),
            (
                "get_spp_hourly_average_actual_forecast",
                "spp_hrly_avrg_actl_fcast",
            ),
            ("get_spp_actual_5min_avg_values", "spp_actual_5min_avg_values"),
        ],
    )
    def test_wind_solar_endpoints_return_dataframe(
        self, method_name, endpoint_name, sample_single_page_response
    ):
        """Test wind and solar power endpoints return DataFrames."""
        ercot = ERCOT(retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()
        method = getattr(ercot, method_name)

        with patch(f"tinygrid.ercot.{endpoint_name}") as mock_endpoint:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = sample_single_page_response
            mock_endpoint.sync.return_value = mock_response

            result = method()
            assert isinstance(result, pd.DataFrame)
            mock_endpoint.sync.assert_called()


class TestDateNormalization:
    """Test date normalization in methods that accept dates."""

    @patch("tinygrid.ercot.dam_hourly_lmp")
    def test_get_dam_hourly_lmp_normalizes_dates(
        self, mock_endpoint, sample_single_page_response
    ):
        """Test get_dam_hourly_lmp normalizes date parameters."""
        mock_response = MagicMock()
        mock_response.to_dict.return_value = sample_single_page_response
        mock_endpoint.sync.return_value = mock_response

        ercot = ERCOT(retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        ercot.get_dam_hourly_lmp(
            start_date=" 2024-01-01 ",
            end_date=" 2024-01-07 ",
        )

        call_args = mock_endpoint.sync.call_args
        assert call_args.kwargs["delivery_date_from"] == "2024-01-01"
        assert call_args.kwargs["delivery_date_to"] == "2024-01-07"

    @patch("tinygrid.ercot.lf_by_model_study_area")
    def test_get_load_forecast_by_study_area_normalizes_dates(
        self, mock_endpoint, sample_single_page_response
    ):
        """Test get_load_forecast_by_study_area normalizes date parameters."""
        mock_response = MagicMock()
        mock_response.to_dict.return_value = sample_single_page_response
        mock_endpoint.sync.return_value = mock_response

        ercot = ERCOT(retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        ercot.get_load_forecast_by_study_area(
            start_date=" 2024-01-01 ",
            end_date=" 2024-01-07 ",
        )

        call_args = mock_endpoint.sync.call_args
        assert call_args.kwargs["delivery_date_from"] == "2024-01-01"
        assert call_args.kwargs["delivery_date_to"] == "2024-01-07"
