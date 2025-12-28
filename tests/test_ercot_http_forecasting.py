"""Tests for ERCOT SDK Load/Wind/Solar Forecasting HTTP requests.

These tests validate that the correct API calls are being dispatched
with proper URLs, parameters, and headers using respx to intercept HTTP requests.
"""

import httpx
import pytest
import respx

from tinygrid import ERCOT

# Base URL for ERCOT API
ERCOT_API_BASE_URL = "https://api.ercot.com/api/public-reports"


@pytest.fixture
def sample_forecast_response():
    """Standard forecast response structure."""
    return {
        "_meta": {
            "totalRecords": 1,
            "pageSize": 10000,
            "totalPages": 1,
            "currentPage": 1,
        },
        "fields": [
            {"name": "deliveryDate", "label": "Delivery Date"},
            {"name": "hourEnding", "label": "Hour Ending"},
            {"name": "systemTotal", "label": "System Total"},
        ],
        "data": {
            "records": [
                ["2024-01-01", "1", 45000.0],
            ]
        },
    }


class TestLoadForecastHTTPRequests:
    """Test HTTP requests for Load Forecast endpoints."""

    @respx.mock
    def test_get_load_forecast_by_weather_zone_dispatches_correct_url(
        self, sample_forecast_response
    ):
        """Test get_load_forecast_by_weather_zone calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-565-cd/lf_by_model_weather_zone"
        ).mock(return_value=httpx.Response(200, json=sample_forecast_response))

        ercot = ERCOT()
        ercot.get_load_forecast_by_weather_zone(
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert route.called
        request = route.calls.last.request
        assert "/np3-565-cd/lf_by_model_weather_zone" in request.url.path

    @respx.mock
    def test_get_load_forecast_by_weather_zone_passes_date_params(
        self, sample_forecast_response
    ):
        """Test get_load_forecast_by_weather_zone passes date parameters correctly."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-565-cd/lf_by_model_weather_zone"
        ).mock(return_value=httpx.Response(200, json=sample_forecast_response))

        ercot = ERCOT()
        ercot.get_load_forecast_by_weather_zone(
            start_date="2024-01-01",
            end_date="2024-01-07",
        )

        assert route.called
        request = route.calls.last.request
        query_str = str(request.url)
        assert "deliveryDateFrom=2024-01-01" in query_str
        assert "deliveryDateTo=2024-01-07" in query_str

    @respx.mock
    def test_get_load_forecast_by_weather_zone_normalizes_dates(
        self, sample_forecast_response
    ):
        """Test date normalization strips whitespace."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-565-cd/lf_by_model_weather_zone"
        ).mock(return_value=httpx.Response(200, json=sample_forecast_response))

        ercot = ERCOT()
        ercot.get_load_forecast_by_weather_zone(
            start_date=" 2024-01-01 ",
            end_date=" 2024-01-07 ",
        )

        assert route.called
        request = route.calls.last.request
        query_str = str(request.url)
        assert "deliveryDateFrom=2024-01-01" in query_str
        assert "deliveryDateTo=2024-01-07" in query_str

    @respx.mock
    def test_get_load_forecast_by_study_area_dispatches_correct_url(
        self, sample_forecast_response
    ):
        """Test get_load_forecast_by_study_area calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-566-cd/lf_by_model_study_area"
        ).mock(return_value=httpx.Response(200, json=sample_forecast_response))

        ercot = ERCOT()
        ercot.get_load_forecast_by_study_area(
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert route.called
        request = route.calls.last.request
        assert "/np3-566-cd/lf_by_model_study_area" in request.url.path

    @respx.mock
    def test_get_load_forecast_by_study_area_passes_model_param(
        self, sample_forecast_response
    ):
        """Test get_load_forecast_by_study_area passes model parameter."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-566-cd/lf_by_model_study_area"
        ).mock(return_value=httpx.Response(200, json=sample_forecast_response))

        ercot = ERCOT()
        ercot.get_load_forecast_by_study_area(
            start_date="2024-01-01",
            end_date="2024-01-02",
            model="STUDYAREA",
        )

        assert route.called
        request = route.calls.last.request
        query_str = str(request.url)
        assert "model=STUDYAREA" in query_str


class TestActualSystemLoadHTTPRequests:
    """Test HTTP requests for Actual System Load endpoints."""

    @respx.mock
    def test_get_actual_system_load_by_weather_zone_dispatches_correct_url(
        self, sample_forecast_response
    ):
        """Test get_actual_system_load_by_weather_zone calls correct endpoint."""
        route = respx.get(f"{ERCOT_API_BASE_URL}/np6-345-cd/act_sys_load_by_wzn").mock(
            return_value=httpx.Response(200, json=sample_forecast_response)
        )

        ercot = ERCOT()
        ercot.get_actual_system_load_by_weather_zone()

        assert route.called
        request = route.calls.last.request
        assert "/np6-345-cd/act_sys_load_by_wzn" in request.url.path

    @respx.mock
    def test_get_actual_system_load_by_forecast_zone_dispatches_correct_url(
        self, sample_forecast_response
    ):
        """Test get_actual_system_load_by_forecast_zone calls correct endpoint."""
        route = respx.get(f"{ERCOT_API_BASE_URL}/np6-346-cd/act_sys_load_by_fzn").mock(
            return_value=httpx.Response(200, json=sample_forecast_response)
        )

        ercot = ERCOT()
        ercot.get_actual_system_load_by_forecast_zone()

        assert route.called
        request = route.calls.last.request
        assert "/np6-346-cd/act_sys_load_by_fzn" in request.url.path


class TestWindPowerForecastHTTPRequests:
    """Test HTTP requests for Wind Power Forecast endpoints."""

    @respx.mock
    def test_get_wpp_hourly_average_actual_forecast_dispatches_correct_url(
        self, sample_forecast_response
    ):
        """Test get_wpp_hourly_average_actual_forecast calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np4-732-cd/wpp_hrly_avrg_actl_fcast"
        ).mock(return_value=httpx.Response(200, json=sample_forecast_response))

        ercot = ERCOT()
        ercot.get_wpp_hourly_average_actual_forecast()

        assert route.called
        request = route.calls.last.request
        assert "/np4-732-cd/wpp_hrly_avrg_actl_fcast" in request.url.path

    @respx.mock
    def test_get_wpp_actual_5min_avg_values_dispatches_correct_url(
        self, sample_forecast_response
    ):
        """Test get_wpp_actual_5min_avg_values calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np4-733-cd/wpp_actual_5min_avg_values"
        ).mock(return_value=httpx.Response(200, json=sample_forecast_response))

        ercot = ERCOT()
        ercot.get_wpp_actual_5min_avg_values()

        assert route.called
        request = route.calls.last.request
        assert "/np4-733-cd/wpp_actual_5min_avg_values" in request.url.path

    @respx.mock
    def test_get_wpp_hourly_actual_forecast_geo_dispatches_correct_url(
        self, sample_forecast_response
    ):
        """Test get_wpp_hourly_actual_forecast_geo calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np4-742-cd/wpp_hrly_actual_fcast_geo"
        ).mock(return_value=httpx.Response(200, json=sample_forecast_response))

        ercot = ERCOT()
        ercot.get_wpp_hourly_actual_forecast_geo()

        assert route.called
        request = route.calls.last.request
        assert "/np4-742-cd/wpp_hrly_actual_fcast_geo" in request.url.path

    @respx.mock
    def test_get_wpp_actual_5min_avg_values_geo_dispatches_correct_url(
        self, sample_forecast_response
    ):
        """Test get_wpp_actual_5min_avg_values_geo calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np4-743-cd/wpp_actual_5min_avg_values_geo"
        ).mock(return_value=httpx.Response(200, json=sample_forecast_response))

        ercot = ERCOT()
        ercot.get_wpp_actual_5min_avg_values_geo()

        assert route.called
        request = route.calls.last.request
        assert "/np4-743-cd/wpp_actual_5min_avg_values_geo" in request.url.path


class TestSolarPowerForecastHTTPRequests:
    """Test HTTP requests for Solar Power Forecast endpoints."""

    @respx.mock
    def test_get_spp_hourly_average_actual_forecast_dispatches_correct_url(
        self, sample_forecast_response
    ):
        """Test get_spp_hourly_average_actual_forecast calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np4-737-cd/spp_hrly_avrg_actl_fcast"
        ).mock(return_value=httpx.Response(200, json=sample_forecast_response))

        ercot = ERCOT()
        ercot.get_spp_hourly_average_actual_forecast()

        assert route.called
        request = route.calls.last.request
        assert "/np4-737-cd/spp_hrly_avrg_actl_fcast" in request.url.path

    @respx.mock
    def test_get_spp_actual_5min_avg_values_dispatches_correct_url(
        self, sample_forecast_response
    ):
        """Test get_spp_actual_5min_avg_values calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np4-738-cd/spp_actual_5min_avg_values"
        ).mock(return_value=httpx.Response(200, json=sample_forecast_response))

        ercot = ERCOT()
        ercot.get_spp_actual_5min_avg_values()

        assert route.called
        request = route.calls.last.request
        assert "/np4-738-cd/spp_actual_5min_avg_values" in request.url.path

    @respx.mock
    def test_get_spp_hourly_actual_forecast_geo_dispatches_correct_url(
        self, sample_forecast_response
    ):
        """Test get_spp_hourly_actual_forecast_geo calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np4-745-cd/spp_hrly_actual_fcast_geo"
        ).mock(return_value=httpx.Response(200, json=sample_forecast_response))

        ercot = ERCOT()
        ercot.get_spp_hourly_actual_forecast_geo()

        assert route.called
        request = route.calls.last.request
        assert "/np4-745-cd/spp_hrly_actual_fcast_geo" in request.url.path

    @respx.mock
    def test_get_spp_actual_5min_avg_values_geo_dispatches_correct_url(
        self, sample_forecast_response
    ):
        """Test get_spp_actual_5min_avg_values_geo calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np4-746-cd/spp_actual_5min_avg_values_geo"
        ).mock(return_value=httpx.Response(200, json=sample_forecast_response))

        ercot = ERCOT()
        ercot.get_spp_actual_5min_avg_values_geo()

        assert route.called
        request = route.calls.last.request
        assert "/np4-746-cd/spp_actual_5min_avg_values_geo" in request.url.path


class TestForecastPaginationParams:
    """Test that forecast endpoints include proper pagination parameters."""

    @respx.mock
    def test_load_forecast_includes_pagination_params(self, sample_forecast_response):
        """Test that load forecast includes page and size in request."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-565-cd/lf_by_model_weather_zone"
        ).mock(return_value=httpx.Response(200, json=sample_forecast_response))

        ercot = ERCOT(page_size=5000)
        ercot.get_load_forecast_by_weather_zone(
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert route.called
        request = route.calls.last.request
        query_str = str(request.url)
        assert "page=1" in query_str
        assert "size=5000" in query_str

    @respx.mock
    def test_wind_forecast_includes_pagination_params(self, sample_forecast_response):
        """Test that wind forecast includes pagination parameters."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np4-732-cd/wpp_hrly_avrg_actl_fcast"
        ).mock(return_value=httpx.Response(200, json=sample_forecast_response))

        ercot = ERCOT(page_size=1000)
        ercot.get_wpp_hourly_average_actual_forecast()

        assert route.called
        request = route.calls.last.request
        query_str = str(request.url)
        assert "size=1000" in query_str


class TestForecastHTTPMethod:
    """Test that forecast endpoints use correct HTTP methods."""

    @respx.mock
    def test_load_forecast_uses_get_method(self, sample_forecast_response):
        """Test that load forecast uses GET method."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-565-cd/lf_by_model_weather_zone"
        ).mock(return_value=httpx.Response(200, json=sample_forecast_response))

        ercot = ERCOT()
        ercot.get_load_forecast_by_weather_zone(
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert route.called
        request = route.calls.last.request
        assert request.method == "GET"

    @respx.mock
    def test_wind_forecast_uses_get_method(self, sample_forecast_response):
        """Test that wind forecast uses GET method."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np4-732-cd/wpp_hrly_avrg_actl_fcast"
        ).mock(return_value=httpx.Response(200, json=sample_forecast_response))

        ercot = ERCOT()
        ercot.get_wpp_hourly_average_actual_forecast()

        assert route.called
        request = route.calls.last.request
        assert request.method == "GET"
