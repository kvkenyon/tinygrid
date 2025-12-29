"""Tests for new ERCOT API methods (dc_tie, total_gen, system_actuals, 5min resolution)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pandas as pd
import pytest

from tinygrid.ercot.api import ERCOTAPIMixin


class TestableERCOTAPIMixin(ERCOTAPIMixin):
    """Testable version of ERCOTAPIMixin with mocked dependencies."""

    def __init__(self):
        self._mock_archive = MagicMock()
        self._mock_archive.fetch_historical = MagicMock(return_value=pd.DataFrame())

    def _get_archive(self):
        return self._mock_archive

    def _needs_historical(self, date, data_type):
        return True  # Always use archive for testing

    # Mock the pyercot endpoint methods
    def get_wpp_hourly_average_actual_forecast(self, **kwargs):
        return pd.DataFrame()

    def get_wpp_hourly_actual_forecast_geo(self, **kwargs):
        return pd.DataFrame()

    def get_wpp_actual_5min_avg_values(self, **kwargs):
        return pd.DataFrame()

    def get_wpp_actual_5min_avg_values_geo(self, **kwargs):
        return pd.DataFrame()

    def get_spp_hourly_average_actual_forecast(self, **kwargs):
        return pd.DataFrame()

    def get_spp_hourly_actual_forecast_geo(self, **kwargs):
        return pd.DataFrame()

    def get_spp_actual_5min_avg_values(self, **kwargs):
        return pd.DataFrame()

    def get_spp_actual_5min_avg_values_geo(self, **kwargs):
        return pd.DataFrame()


class TestGetDCTieFlows:
    """Tests for get_dc_tie_flows method."""

    @pytest.fixture
    def mixin(self):
        return TestableERCOTAPIMixin()

    def test_get_dc_tie_flows_returns_dataframe(self, mixin):
        """Test get_dc_tie_flows returns DataFrame."""
        mixin._mock_archive.fetch_historical.return_value = pd.DataFrame(
            {"col1": [1, 2], "col2": [3, 4]}
        )

        result = mixin.get_dc_tie_flows(start="2024-01-01")

        assert isinstance(result, pd.DataFrame)

    def test_get_dc_tie_flows_calls_archive(self, mixin):
        """Test get_dc_tie_flows uses archive API."""
        mixin.get_dc_tie_flows(start="2024-01-01")

        mixin._mock_archive.fetch_historical.assert_called_once()
        call_args = mixin._mock_archive.fetch_historical.call_args
        assert "/np6-626-cd/dc_tie" in call_args[1]["endpoint"]

    def test_get_dc_tie_flows_with_date_range(self, mixin):
        """Test get_dc_tie_flows with start and end dates."""
        mixin.get_dc_tie_flows(start="2024-01-01", end="2024-01-07")

        call_args = mixin._mock_archive.fetch_historical.call_args
        assert call_args[1]["start"] is not None
        assert call_args[1]["end"] is not None


class TestGetTotalGeneration:
    """Tests for get_total_generation method."""

    @pytest.fixture
    def mixin(self):
        return TestableERCOTAPIMixin()

    def test_get_total_generation_returns_dataframe(self, mixin):
        """Test get_total_generation returns DataFrame."""
        mixin._mock_archive.fetch_historical.return_value = pd.DataFrame(
            {"col1": [1, 2], "col2": [3, 4]}
        )

        result = mixin.get_total_generation(start="2024-01-01")

        assert isinstance(result, pd.DataFrame)

    def test_get_total_generation_calls_archive(self, mixin):
        """Test get_total_generation uses archive API."""
        mixin.get_total_generation(start="2024-01-01")

        mixin._mock_archive.fetch_historical.assert_called_once()
        call_args = mixin._mock_archive.fetch_historical.call_args
        assert "/np6-625-cd/se_totalgen" in call_args[1]["endpoint"]


class TestGetSystemWideActuals:
    """Tests for get_system_wide_actuals method."""

    @pytest.fixture
    def mixin(self):
        return TestableERCOTAPIMixin()

    def test_get_system_wide_actuals_returns_dataframe(self, mixin):
        """Test get_system_wide_actuals returns DataFrame."""
        mixin._mock_archive.fetch_historical.return_value = pd.DataFrame(
            {"col1": [1, 2], "col2": [3, 4]}
        )

        result = mixin.get_system_wide_actuals(start="2024-01-01")

        assert isinstance(result, pd.DataFrame)

    def test_get_system_wide_actuals_calls_archive(self, mixin):
        """Test get_system_wide_actuals uses archive API."""
        mixin.get_system_wide_actuals(start="2024-01-01")

        mixin._mock_archive.fetch_historical.assert_called_once()
        call_args = mixin._mock_archive.fetch_historical.call_args
        assert "/np6-235-cd/sys_wide_actuals" in call_args[1]["endpoint"]


class TestWindForecastResolution:
    """Tests for get_wind_forecast 5-minute resolution."""

    @pytest.fixture
    def mixin(self):
        return TestableERCOTAPIMixin()

    def test_wind_forecast_invalid_resolution_raises(self, mixin):
        """Test that invalid resolution raises ValueError."""
        with pytest.raises(ValueError, match="Invalid resolution"):
            mixin.get_wind_forecast(start="2024-01-01", resolution="invalid")

    def test_wind_forecast_5min_resolution(self, mixin):
        """Test 5-minute resolution uses correct endpoint."""
        mixin.get_wind_forecast(start="2024-01-01", resolution="5min")

        call_args = mixin._mock_archive.fetch_historical.call_args
        assert "np4-733-cd" in call_args[1]["endpoint"]

    def test_wind_forecast_5min_by_region(self, mixin):
        """Test 5-minute resolution by region uses correct endpoint."""
        mixin.get_wind_forecast(start="2024-01-01", resolution="5min", by_region=True)

        call_args = mixin._mock_archive.fetch_historical.call_args
        assert "np4-743-cd" in call_args[1]["endpoint"]

    def test_wind_forecast_hourly_resolution(self, mixin):
        """Test hourly resolution uses correct endpoint."""
        mixin.get_wind_forecast(start="2024-01-01", resolution="hourly")

        call_args = mixin._mock_archive.fetch_historical.call_args
        assert "np4-732-cd" in call_args[1]["endpoint"]

    def test_wind_forecast_accepts_various_5min_formats(self, mixin):
        """Test 5-minute resolution accepts various formats."""
        # Test different formats
        for fmt in ["5min", "5-min", "5_min"]:
            mixin._mock_archive.fetch_historical.reset_mock()
            mixin.get_wind_forecast(start="2024-01-01", resolution=fmt)
            call_args = mixin._mock_archive.fetch_historical.call_args
            assert "np4-733-cd" in call_args[1]["endpoint"]


class TestSolarForecastResolution:
    """Tests for get_solar_forecast 5-minute resolution."""

    @pytest.fixture
    def mixin(self):
        return TestableERCOTAPIMixin()

    def test_solar_forecast_invalid_resolution_raises(self, mixin):
        """Test that invalid resolution raises ValueError."""
        with pytest.raises(ValueError, match="Invalid resolution"):
            mixin.get_solar_forecast(start="2024-01-01", resolution="invalid")

    def test_solar_forecast_5min_resolution(self, mixin):
        """Test 5-minute resolution uses correct endpoint."""
        mixin.get_solar_forecast(start="2024-01-01", resolution="5min")

        call_args = mixin._mock_archive.fetch_historical.call_args
        assert "np4-738-cd" in call_args[1]["endpoint"]

    def test_solar_forecast_5min_by_region(self, mixin):
        """Test 5-minute resolution by region uses correct endpoint."""
        mixin.get_solar_forecast(start="2024-01-01", resolution="5min", by_region=True)

        call_args = mixin._mock_archive.fetch_historical.call_args
        assert "np4-746-cd" in call_args[1]["endpoint"]

    def test_solar_forecast_hourly_resolution(self, mixin):
        """Test hourly resolution uses correct endpoint."""
        mixin.get_solar_forecast(start="2024-01-01", resolution="hourly")

        call_args = mixin._mock_archive.fetch_historical.call_args
        assert "np4-737-cd" in call_args[1]["endpoint"]


class TestAPIMethodDefaults:
    """Tests for API method default behaviors."""

    @pytest.fixture
    def mixin(self):
        return TestableERCOTAPIMixin()

    def test_wind_forecast_default_resolution_is_hourly(self, mixin):
        """Test wind forecast defaults to hourly resolution."""
        # Call without specifying resolution
        mixin.get_wind_forecast(start="2024-01-01")

        call_args = mixin._mock_archive.fetch_historical.call_args
        # Should use hourly endpoint
        assert "np4-732-cd" in call_args[1]["endpoint"]

    def test_solar_forecast_default_resolution_is_hourly(self, mixin):
        """Test solar forecast defaults to hourly resolution."""
        # Call without specifying resolution
        mixin.get_solar_forecast(start="2024-01-01")

        call_args = mixin._mock_archive.fetch_historical.call_args
        # Should use hourly endpoint
        assert "np4-737-cd" in call_args[1]["endpoint"]

    def test_wind_forecast_default_by_region_is_false(self, mixin):
        """Test wind forecast defaults to non-regional data."""
        mixin.get_wind_forecast(start="2024-01-01")

        call_args = mixin._mock_archive.fetch_historical.call_args
        # Should NOT use geo endpoint
        assert "geo" not in call_args[1]["endpoint"]

    def test_solar_forecast_default_by_region_is_false(self, mixin):
        """Test solar forecast defaults to non-regional data."""
        mixin.get_solar_forecast(start="2024-01-01")

        call_args = mixin._mock_archive.fetch_historical.call_args
        # Should NOT use geo endpoint
        assert "geo" not in call_args[1]["endpoint"]

    def test_wind_forecast_hourly_by_region(self, mixin):
        """Test hourly wind forecast by region."""
        mixin.get_wind_forecast(start="2024-01-01", by_region=True)

        call_args = mixin._mock_archive.fetch_historical.call_args
        assert "np4-742-cd" in call_args[1]["endpoint"]

    def test_solar_forecast_hourly_by_region(self, mixin):
        """Test hourly solar forecast by region."""
        mixin.get_solar_forecast(start="2024-01-01", by_region=True)

        call_args = mixin._mock_archive.fetch_historical.call_args
        assert "np4-745-cd" in call_args[1]["endpoint"]


class NonHistoricalMixin(ERCOTAPIMixin):
    """Testable mixin that always uses non-historical (live API) path."""

    def __init__(self):
        self._mock_archive = MagicMock()
        self._mock_archive.fetch_historical = MagicMock(return_value=pd.DataFrame())
        self._endpoint_calls = []

    def _get_archive(self):
        return self._mock_archive

    def _needs_historical(self, date, data_type):
        return False  # Always use live API for testing

    # Mock the pyercot endpoint methods
    def get_wpp_hourly_average_actual_forecast(self, **kwargs):
        self._endpoint_calls.append(("wpp_hourly", kwargs))
        return pd.DataFrame()

    def get_wpp_hourly_actual_forecast_geo(self, **kwargs):
        self._endpoint_calls.append(("wpp_hourly_geo", kwargs))
        return pd.DataFrame()

    def get_wpp_actual_5min_avg_values(self, **kwargs):
        self._endpoint_calls.append(("wpp_5min", kwargs))
        return pd.DataFrame()

    def get_wpp_actual_5min_avg_values_geo(self, **kwargs):
        self._endpoint_calls.append(("wpp_5min_geo", kwargs))
        return pd.DataFrame()

    def get_spp_hourly_average_actual_forecast(self, **kwargs):
        self._endpoint_calls.append(("spp_hourly", kwargs))
        return pd.DataFrame()

    def get_spp_hourly_actual_forecast_geo(self, **kwargs):
        self._endpoint_calls.append(("spp_hourly_geo", kwargs))
        return pd.DataFrame()

    def get_spp_actual_5min_avg_values(self, **kwargs):
        self._endpoint_calls.append(("spp_5min", kwargs))
        return pd.DataFrame()

    def get_spp_actual_5min_avg_values_geo(self, **kwargs):
        self._endpoint_calls.append(("spp_5min_geo", kwargs))
        return pd.DataFrame()


class TestNonHistoricalWindForecast:
    """Tests for get_wind_forecast using live API (non-historical) path."""

    @pytest.fixture
    def mixin(self):
        return NonHistoricalMixin()

    def test_wind_forecast_hourly_live(self, mixin):
        """Test wind forecast hourly uses live endpoint."""
        mixin.get_wind_forecast(start="today", resolution="hourly")

        assert len(mixin._endpoint_calls) == 1
        assert mixin._endpoint_calls[0][0] == "wpp_hourly"

    def test_wind_forecast_hourly_by_region_live(self, mixin):
        """Test wind forecast hourly by region uses live endpoint."""
        mixin.get_wind_forecast(start="today", resolution="hourly", by_region=True)

        assert len(mixin._endpoint_calls) == 1
        assert mixin._endpoint_calls[0][0] == "wpp_hourly_geo"

    def test_wind_forecast_5min_live(self, mixin):
        """Test wind forecast 5min uses live endpoint."""
        mixin.get_wind_forecast(start="today", resolution="5min")

        assert len(mixin._endpoint_calls) == 1
        assert mixin._endpoint_calls[0][0] == "wpp_5min"

    def test_wind_forecast_5min_by_region_live(self, mixin):
        """Test wind forecast 5min by region uses live endpoint."""
        mixin.get_wind_forecast(start="today", resolution="5min", by_region=True)

        assert len(mixin._endpoint_calls) == 1
        assert mixin._endpoint_calls[0][0] == "wpp_5min_geo"


class TestNonHistoricalSolarForecast:
    """Tests for get_solar_forecast using live API (non-historical) path."""

    @pytest.fixture
    def mixin(self):
        return NonHistoricalMixin()

    def test_solar_forecast_hourly_live(self, mixin):
        """Test solar forecast hourly uses live endpoint."""
        mixin.get_solar_forecast(start="today", resolution="hourly")

        assert len(mixin._endpoint_calls) == 1
        assert mixin._endpoint_calls[0][0] == "spp_hourly"

    def test_solar_forecast_hourly_by_region_live(self, mixin):
        """Test solar forecast hourly by region uses live endpoint."""
        mixin.get_solar_forecast(start="today", resolution="hourly", by_region=True)

        assert len(mixin._endpoint_calls) == 1
        assert mixin._endpoint_calls[0][0] == "spp_hourly_geo"

    def test_solar_forecast_5min_live(self, mixin):
        """Test solar forecast 5min uses live endpoint."""
        mixin.get_solar_forecast(start="today", resolution="5min")

        assert len(mixin._endpoint_calls) == 1
        assert mixin._endpoint_calls[0][0] == "spp_5min"

    def test_solar_forecast_5min_by_region_live(self, mixin):
        """Test solar forecast 5min by region uses live endpoint."""
        mixin.get_solar_forecast(start="today", resolution="5min", by_region=True)

        assert len(mixin._endpoint_calls) == 1
        assert mixin._endpoint_calls[0][0] == "spp_5min_geo"
