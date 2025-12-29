"""Tests for tinygrid.ercot.dashboard module."""

from __future__ import annotations

from unittest.mock import patch

import pandas as pd
import pytest

from tinygrid.ercot.dashboard import (
    ERCOTDashboardMixin,
    FuelMixEntry,
    GridCondition,
    GridStatus,
    RenewableStatus,
    _fetch_json,
    _parse_timestamp,
    _safe_float,
)


class TestGridCondition:
    """Tests for GridCondition enum."""

    def test_normal_condition(self):
        """Test normal condition value."""
        assert GridCondition.NORMAL.value == "normal"

    def test_conservation_condition(self):
        """Test conservation condition value."""
        assert GridCondition.CONSERVATION.value == "conservation"

    def test_watch_condition(self):
        """Test watch condition value."""
        assert GridCondition.WATCH.value == "watch"

    def test_emergency_condition(self):
        """Test emergency condition value."""
        assert GridCondition.EMERGENCY.value == "emergency"

    def test_unknown_condition(self):
        """Test unknown condition value."""
        assert GridCondition.UNKNOWN.value == "unknown"


class TestGridStatus:
    """Tests for GridStatus dataclass."""

    def test_create_grid_status(self):
        """Test creating GridStatus instance."""
        ts = pd.Timestamp.now(tz="US/Central")
        status = GridStatus(
            condition=GridCondition.NORMAL,
            current_frequency=60.0,
            current_load=50000.0,
            capacity=70000.0,
            reserves=20000.0,
            timestamp=ts,
        )
        assert status.condition == GridCondition.NORMAL
        assert status.current_frequency == 60.0
        assert status.current_load == 50000.0

    def test_grid_status_with_message(self):
        """Test GridStatus with message."""
        status = GridStatus(
            condition=GridCondition.WATCH,
            current_frequency=59.95,
            current_load=60000.0,
            capacity=65000.0,
            reserves=5000.0,
            timestamp=pd.Timestamp.now(tz="US/Central"),
            message="Conservation appeal in effect",
        )
        assert status.message == "Conservation appeal in effect"

    def test_unavailable_factory(self):
        """Test unavailable class method."""
        status = GridStatus.unavailable()
        assert status.condition == GridCondition.UNKNOWN
        assert status.current_frequency == 0.0
        assert status.current_load == 0.0
        assert "not available" in status.message


class TestERCOTDashboardMixin:
    """Tests for ERCOTDashboardMixin class."""

    @pytest.fixture
    def mixin_instance(self):
        """Create a test instance with the mixin."""

        class TestClass(ERCOTDashboardMixin):
            pass

        return TestClass()

    def test_get_status_returns_grid_status(self, mixin_instance):
        """Test get_status returns GridStatus object."""
        status = mixin_instance.get_status()
        assert isinstance(status, GridStatus)
        # Status may be UNKNOWN if API is unavailable, or a real condition if it works
        assert isinstance(status.condition, GridCondition)

    def test_get_fuel_mix_returns_dataframe(self, mixin_instance):
        """Test get_fuel_mix returns DataFrame (may be empty if API unavailable)."""
        df = mixin_instance.get_fuel_mix()
        assert isinstance(df, pd.DataFrame)

    def test_get_fuel_mix_with_as_dataframe_false(self, mixin_instance):
        """Test get_fuel_mix returns list when as_dataframe=False."""
        result = mixin_instance.get_fuel_mix(as_dataframe=False)
        assert isinstance(result, list)

    def test_get_energy_storage_resources_returns_dataframe(self, mixin_instance):
        """Test get_energy_storage_resources returns DataFrame."""
        df = mixin_instance.get_energy_storage_resources()
        assert isinstance(df, pd.DataFrame)

    def test_get_system_wide_demand_returns_dataframe(self, mixin_instance):
        """Test get_system_wide_demand returns DataFrame."""
        df = mixin_instance.get_system_wide_demand()
        assert isinstance(df, pd.DataFrame)

    def test_get_renewable_generation_returns_status(self, mixin_instance):
        """Test get_renewable_generation returns RenewableStatus."""
        result = mixin_instance.get_renewable_generation()
        assert isinstance(result, RenewableStatus)
        assert hasattr(result, "wind_mw")
        assert hasattr(result, "solar_mw")

    def test_get_capacity_committed_returns_dataframe(self, mixin_instance):
        """Test get_capacity_committed returns DataFrame."""
        df = mixin_instance.get_capacity_committed()
        assert isinstance(df, pd.DataFrame)

    def test_get_capacity_forecast_returns_dataframe(self, mixin_instance):
        """Test get_capacity_forecast returns DataFrame."""
        df = mixin_instance.get_capacity_forecast()
        assert isinstance(df, pd.DataFrame)

    def test_get_supply_demand_returns_dataframe(self, mixin_instance):
        """Test get_supply_demand returns DataFrame."""
        df = mixin_instance.get_supply_demand()
        assert isinstance(df, pd.DataFrame)

    def test_get_daily_prices_returns_dataframe(self, mixin_instance):
        """Test get_daily_prices returns DataFrame."""
        df = mixin_instance.get_daily_prices()
        assert isinstance(df, pd.DataFrame)


class TestGridConditionFromString:
    """Tests for GridCondition.from_string method."""

    def test_from_string_normal(self):
        """Test parsing normal condition."""
        assert GridCondition.from_string("normal") == GridCondition.NORMAL
        assert GridCondition.from_string("Normal Operations") == GridCondition.NORMAL

    def test_from_string_conservation(self):
        """Test parsing conservation condition."""
        assert GridCondition.from_string("conservation") == GridCondition.CONSERVATION
        assert (
            GridCondition.from_string("conservation appeal")
            == GridCondition.CONSERVATION
        )

    def test_from_string_watch(self):
        """Test parsing watch condition."""
        assert GridCondition.from_string("watch") == GridCondition.WATCH
        assert GridCondition.from_string("weather watch") == GridCondition.WATCH

    def test_from_string_advisory(self):
        """Test parsing advisory condition."""
        assert GridCondition.from_string("advisory") == GridCondition.ADVISORY
        assert (
            GridCondition.from_string("operating condition notice")
            == GridCondition.ADVISORY
        )

    def test_from_string_emergency(self):
        """Test parsing emergency condition."""
        assert GridCondition.from_string("emergency") == GridCondition.EMERGENCY

    def test_from_string_eea_levels(self):
        """Test parsing EEA levels."""
        assert GridCondition.from_string("eea1") == GridCondition.EEA1
        assert GridCondition.from_string("EEA 1") == GridCondition.EEA1
        assert (
            GridCondition.from_string("energy emergency alert 1") == GridCondition.EEA1
        )
        assert GridCondition.from_string("eea2") == GridCondition.EEA2
        assert GridCondition.from_string("eea3") == GridCondition.EEA3

    def test_from_string_unknown(self):
        """Test parsing unknown condition."""
        assert GridCondition.from_string("unknown_value") == GridCondition.UNKNOWN
        assert GridCondition.from_string(None) == GridCondition.UNKNOWN
        assert GridCondition.from_string("") == GridCondition.UNKNOWN


class TestSafeFloat:
    """Tests for _safe_float helper function."""

    def test_safe_float_valid_float(self):
        """Test with valid float."""
        assert _safe_float(3.14) == 3.14

    def test_safe_float_valid_int(self):
        """Test with valid int."""
        assert _safe_float(42) == 42.0

    def test_safe_float_valid_string(self):
        """Test with valid numeric string."""
        assert _safe_float("3.14") == 3.14

    def test_safe_float_none_returns_default(self):
        """Test None returns default."""
        assert _safe_float(None) == 0.0
        assert _safe_float(None, default=99.0) == 99.0

    def test_safe_float_invalid_returns_default(self):
        """Test invalid value returns default."""
        assert _safe_float("not a number") == 0.0
        assert _safe_float({}) == 0.0
        assert _safe_float([]) == 0.0


class TestParseTimestamp:
    """Tests for _parse_timestamp helper function."""

    def test_parse_timestamp_none_returns_now(self):
        """Test None returns current timestamp."""
        result = _parse_timestamp(None)
        assert isinstance(result, pd.Timestamp)
        assert result.tzinfo is not None

    def test_parse_timestamp_epoch_ms(self):
        """Test parsing epoch milliseconds."""
        # 2024-01-01 00:00:00 UTC in milliseconds
        epoch_ms = 1704067200000
        result = _parse_timestamp(epoch_ms)
        assert isinstance(result, pd.Timestamp)

    def test_parse_timestamp_epoch_s(self):
        """Test parsing epoch seconds."""
        epoch_s = 1704067200
        result = _parse_timestamp(epoch_s)
        assert isinstance(result, pd.Timestamp)

    def test_parse_timestamp_string(self):
        """Test parsing string timestamp."""
        result = _parse_timestamp("2024-01-01T12:00:00")
        assert isinstance(result, pd.Timestamp)

    def test_parse_timestamp_invalid_returns_now(self):
        """Test invalid value returns current timestamp."""
        result = _parse_timestamp("not a date")
        assert isinstance(result, pd.Timestamp)


class TestFetchJson:
    """Tests for _fetch_json helper function."""

    @patch("tinygrid.ercot.dashboard.httpx.Client")
    def test_fetch_json_success(self, mock_client_class):
        """Test successful JSON fetch."""
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": "test"}
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client_class.return_value = mock_client

        result = _fetch_json("https://example.com/api")

        assert result == {"data": "test"}

    @patch("tinygrid.ercot.dashboard.httpx.Client")
    def test_fetch_json_timeout(self, mock_client_class):
        """Test timeout returns None."""
        from unittest.mock import MagicMock

        import httpx

        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.TimeoutException("Timeout")
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client_class.return_value = mock_client

        result = _fetch_json("https://example.com/api")

        assert result is None

    @patch("tinygrid.ercot.dashboard.httpx.Client")
    def test_fetch_json_http_error(self, mock_client_class):
        """Test HTTP error returns None."""
        from unittest.mock import MagicMock

        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error",
            request=MagicMock(),
            response=mock_response,
        )
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client_class.return_value = mock_client

        result = _fetch_json("https://example.com/api")

        assert result is None


class TestFuelMixEntry:
    """Tests for FuelMixEntry dataclass."""

    def test_create_fuel_mix_entry(self):
        """Test creating FuelMixEntry."""
        ts = pd.Timestamp.now(tz="US/Central")
        entry = FuelMixEntry(
            fuel_type="natural_gas",
            generation_mw=25000.0,
            percentage=45.5,
            timestamp=ts,
        )

        assert entry.fuel_type == "natural_gas"
        assert entry.generation_mw == 25000.0
        assert entry.percentage == 45.5
        assert entry.timestamp == ts


class TestRenewableStatus:
    """Tests for RenewableStatus dataclass."""

    def test_create_renewable_status(self):
        """Test creating RenewableStatus."""
        ts = pd.Timestamp.now(tz="US/Central")
        status = RenewableStatus(
            wind_mw=18000.0,
            solar_mw=8000.0,
            wind_forecast_mw=19000.0,
            solar_forecast_mw=7500.0,
            wind_capacity_mw=35000.0,
            solar_capacity_mw=20000.0,
            timestamp=ts,
        )

        assert status.wind_mw == 18000.0
        assert status.solar_mw == 8000.0
        assert status.wind_forecast_mw == 19000.0
        assert status.additional_data == {}

    def test_renewable_status_with_additional_data(self):
        """Test RenewableStatus with additional data."""
        ts = pd.Timestamp.now(tz="US/Central")
        status = RenewableStatus(
            wind_mw=18000.0,
            solar_mw=8000.0,
            wind_forecast_mw=19000.0,
            solar_forecast_mw=7500.0,
            wind_capacity_mw=35000.0,
            solar_capacity_mw=20000.0,
            timestamp=ts,
            additional_data={"extra": "data"},
        )

        assert status.additional_data == {"extra": "data"}


class TestDashboardWithMocking:
    """Tests for dashboard methods with mocked HTTP responses."""

    @pytest.fixture
    def mixin_instance(self):
        """Create a test instance with the mixin."""

        class TestClass(ERCOTDashboardMixin):
            pass

        return TestClass()

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_status_success(self, mock_fetch, mixin_instance):
        """Test get_status with successful response."""
        mock_fetch.return_value = {
            "current": {
                "condition": "normal",
                "demand": 50000,
                "capacity": 70000,
                "reserves": 20000,
                "lastUpdated": 1704067200000,
            }
        }

        status = mixin_instance.get_status()

        assert status.condition == GridCondition.NORMAL
        assert status.current_load == 50000.0
        assert status.capacity == 70000.0
        assert status.reserves == 20000.0

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_status_calculates_reserves(self, mock_fetch, mixin_instance):
        """Test get_status calculates reserves when not provided."""
        mock_fetch.return_value = {
            "current": {
                "condition": "normal",
                "demand": 50000,
                "capacity": 70000,
            }
        }

        status = mixin_instance.get_status()

        # Reserves should be calculated as capacity - load
        assert status.reserves == 20000.0

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_status_failure(self, mock_fetch, mixin_instance):
        """Test get_status returns unavailable on failure."""
        mock_fetch.return_value = None

        status = mixin_instance.get_status()

        assert status.condition == GridCondition.UNKNOWN
        assert "not available" in status.message

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_fuel_mix_success(self, mock_fetch, mixin_instance):
        """Test get_fuel_mix with successful response."""
        mock_fetch.return_value = {
            "data": [
                {"fuel": "gas", "gen": 25000, "percent": 45},
                {"fuel": "wind", "gen": 18000, "percent": 32},
            ],
            "lastUpdated": 1704067200000,
        }

        df = mixin_instance.get_fuel_mix()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "fuel_type" in df.columns
        assert "generation_mw" in df.columns

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_fuel_mix_calculates_percentage(self, mock_fetch, mixin_instance):
        """Test get_fuel_mix calculates percentage when not provided."""
        mock_fetch.return_value = {
            "data": [
                {"fuel": "gas", "gen": 50000},
                {"fuel": "wind", "gen": 50000},
            ],
            "lastUpdated": 1704067200000,
        }

        df = mixin_instance.get_fuel_mix()

        # Each should be 50%
        assert df["percentage"].iloc[0] == 50.0
        assert df["percentage"].iloc[1] == 50.0

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_fuel_mix_as_list(self, mock_fetch, mixin_instance):
        """Test get_fuel_mix returns list when as_dataframe=False."""
        mock_fetch.return_value = {
            "data": [
                {"fuel": "gas", "gen": 25000, "percent": 45},
            ],
            "lastUpdated": 1704067200000,
        }

        result = mixin_instance.get_fuel_mix(as_dataframe=False)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], FuelMixEntry)

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_renewable_generation_success(self, mock_fetch, mixin_instance):
        """Test get_renewable_generation with successful response."""
        mock_fetch.return_value = {
            "current": {
                "windActual": 18000,
                "solarActual": 8000,
                "windForecast": 19000,
                "solarForecast": 7500,
                "windCapacity": 35000,
                "solarCapacity": 20000,
            },
            "lastUpdated": 1704067200000,
        }

        status = mixin_instance.get_renewable_generation()

        assert isinstance(status, RenewableStatus)
        assert status.wind_mw == 18000.0
        assert status.solar_mw == 8000.0
        assert status.wind_forecast_mw == 19000.0

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_supply_demand_success(self, mock_fetch, mixin_instance):
        """Test get_supply_demand with successful response."""
        mock_fetch.return_value = {
            "data": [
                {"hour": 1, "demand": 45000, "supply": 60000, "reserves": 15000},
                {"hour": 2, "demand": 46000, "supply": 60000, "reserves": 14000},
            ],
            "lastUpdated": 1704067200000,
        }

        df = mixin_instance.get_supply_demand()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "hour" in df.columns
        assert "demand" in df.columns
        assert "supply" in df.columns

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_daily_prices_success(self, mock_fetch, mixin_instance):
        """Test get_daily_prices with successful response."""
        mock_fetch.return_value = {
            "data": [
                {"settlementPoint": "HB_HOUSTON", "price": 25.50},
                {"settlementPoint": "HB_NORTH", "price": 24.00},
            ],
            "lastUpdated": 1704067200000,
        }

        df = mixin_instance.get_daily_prices()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "settlement_point" in df.columns
        assert "price" in df.columns

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_system_wide_demand_success(self, mock_fetch, mixin_instance):
        """Test get_system_wide_demand with successful response."""
        mock_fetch.return_value = {
            "current": {
                "demand": 50000,
                "capacity": 70000,
                "reserves": 20000,
            },
            "hourly": [
                {"hour": 1, "demand": 45000, "capacity": 70000, "reserves": 25000},
            ],
            "lastUpdated": 1704067200000,
        }

        df = mixin_instance.get_system_wide_demand()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2  # current + 1 hourly
        assert "hour" in df.columns
        assert "demand" in df.columns

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_energy_storage_with_data(self, mock_fetch, mixin_instance):
        """Test get_energy_storage_resources with ESR data."""
        mock_fetch.return_value = {
            "current": {
                "esr": {
                    "charging": 500,
                    "discharging": 1000,
                    "net": 500,
                    "capacity": 3000,
                }
            },
            "lastUpdated": 1704067200000,
        }

        df = mixin_instance.get_energy_storage_resources()

        assert isinstance(df, pd.DataFrame)
        if len(df) > 0:
            assert "charging_mw" in df.columns

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_capacity_committed_success(self, mock_fetch, mixin_instance):
        """Test get_capacity_committed with successful response."""
        mock_fetch.return_value = {
            "data": [
                {"hour": 1, "committed": 60000, "available": 70000},
                {"hour": 2, "committed": 61000, "available": 70000},
            ],
            "lastUpdated": 1704067200000,
        }

        df = mixin_instance.get_capacity_committed()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "hour" in df.columns

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_status_exception_handling(self, mock_fetch, mixin_instance):
        """Test get_status handles exceptions gracefully."""
        mock_fetch.return_value = {"current": {"invalid": "data"}}
        # Should not raise - returns valid status with defaults
        status = mixin_instance.get_status()
        assert isinstance(status, GridStatus)

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_status_non_normal_condition_with_no_message(
        self, mock_fetch, mixin_instance
    ):
        """Test get_status builds message for non-normal conditions."""
        mock_fetch.return_value = {
            "current": {
                "condition": "watch",
                "demand": 50000,
                "capacity": 70000,
            }
        }
        status = mixin_instance.get_status()
        assert status.condition == GridCondition.WATCH
        assert "watch" in status.message.lower()

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_status_with_prc_and_renewable(self, mock_fetch, mixin_instance):
        """Test get_status extracts PRC and renewable data."""
        mock_fetch.return_value = {
            "current": {
                "condition": "normal",
                "demand": 50000,
                "capacity": 70000,
                "prc": 5000,
                "windOutput": 12000,
                "solarOutput": 8000,
                "peakForecast": 75000,
            }
        }
        status = mixin_instance.get_status()
        assert status.prc == 5000.0
        assert status.wind_output == 12000.0
        assert status.solar_output == 8000.0
        assert status.peak_forecast == 75000.0

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_fuel_mix_failure_returns_empty(self, mock_fetch, mixin_instance):
        """Test get_fuel_mix returns empty DataFrame on failure."""
        mock_fetch.return_value = None
        df = mixin_instance.get_fuel_mix()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_fuel_mix_failure_as_list(self, mock_fetch, mixin_instance):
        """Test get_fuel_mix returns empty list on failure with as_dataframe=False."""
        mock_fetch.return_value = None
        result = mixin_instance.get_fuel_mix(as_dataframe=False)
        assert isinstance(result, list)
        assert len(result) == 0

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_fuel_mix_exception_handling(self, mock_fetch, mixin_instance):
        """Test get_fuel_mix handles parsing exceptions."""
        # Return invalid data that will cause parsing exception
        mock_fetch.return_value = {"data": "invalid"}
        df = mixin_instance.get_fuel_mix()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_fuel_mix_exception_as_list(self, mock_fetch, mixin_instance):
        """Test get_fuel_mix returns empty list on exception with as_dataframe=False."""
        mock_fetch.return_value = {"data": "invalid"}
        result = mixin_instance.get_fuel_mix(as_dataframe=False)
        assert isinstance(result, list)
        assert len(result) == 0

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_fuel_mix_empty_data(self, mock_fetch, mixin_instance):
        """Test get_fuel_mix with empty data list."""
        mock_fetch.return_value = {"data": [], "lastUpdated": 1704067200000}
        df = mixin_instance.get_fuel_mix()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_renewable_generation_failure(self, mock_fetch, mixin_instance):
        """Test get_renewable_generation returns defaults on failure."""
        mock_fetch.return_value = None
        status = mixin_instance.get_renewable_generation()
        assert isinstance(status, RenewableStatus)
        assert status.wind_mw == 0.0

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_renewable_generation_exception(self, mock_fetch, mixin_instance):
        """Test get_renewable_generation handles exceptions gracefully."""
        # Return data that will cause parsing exception
        mock_fetch.return_value = {"current": None}
        status = mixin_instance.get_renewable_generation()
        assert isinstance(status, RenewableStatus)
        assert status.wind_mw == 0.0

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_supply_demand_failure(self, mock_fetch, mixin_instance):
        """Test get_supply_demand returns empty DataFrame on failure."""
        mock_fetch.return_value = None
        df = mixin_instance.get_supply_demand()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_supply_demand_empty_data(self, mock_fetch, mixin_instance):
        """Test get_supply_demand with empty data list."""
        mock_fetch.return_value = {"data": [], "lastUpdated": 1704067200000}
        df = mixin_instance.get_supply_demand()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_supply_demand_exception(self, mock_fetch, mixin_instance):
        """Test get_supply_demand handles exceptions gracefully."""
        mock_fetch.return_value = {"data": None}
        df = mixin_instance.get_supply_demand()
        assert isinstance(df, pd.DataFrame)

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_daily_prices_failure(self, mock_fetch, mixin_instance):
        """Test get_daily_prices returns empty DataFrame on failure."""
        mock_fetch.return_value = None
        df = mixin_instance.get_daily_prices()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_daily_prices_empty_data(self, mock_fetch, mixin_instance):
        """Test get_daily_prices with empty data list."""
        mock_fetch.return_value = {"data": [], "lastUpdated": 1704067200000}
        df = mixin_instance.get_daily_prices()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_daily_prices_exception(self, mock_fetch, mixin_instance):
        """Test get_daily_prices handles exceptions gracefully."""
        mock_fetch.return_value = {"data": None}
        df = mixin_instance.get_daily_prices()
        assert isinstance(df, pd.DataFrame)

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_system_wide_demand_failure(self, mock_fetch, mixin_instance):
        """Test get_system_wide_demand returns empty DataFrame on failure."""
        mock_fetch.return_value = None
        df = mixin_instance.get_system_wide_demand()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_system_wide_demand_empty_data(self, mock_fetch, mixin_instance):
        """Test get_system_wide_demand with empty data."""
        mock_fetch.return_value = {"current": {}, "hourly": []}
        df = mixin_instance.get_system_wide_demand()
        assert isinstance(df, pd.DataFrame)

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_system_wide_demand_exception(self, mock_fetch, mixin_instance):
        """Test get_system_wide_demand handles exceptions gracefully."""
        mock_fetch.return_value = {"invalid": "data"}
        df = mixin_instance.get_system_wide_demand()
        assert isinstance(df, pd.DataFrame)

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_energy_storage_resources_failure(self, mock_fetch, mixin_instance):
        """Test get_energy_storage_resources returns empty DataFrame on failure."""
        mock_fetch.return_value = None
        df = mixin_instance.get_energy_storage_resources()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_energy_storage_resources_no_esr(self, mock_fetch, mixin_instance):
        """Test get_energy_storage_resources when ESR data not present."""
        mock_fetch.return_value = {"current": {"demand": 50000}}
        df = mixin_instance.get_energy_storage_resources()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_energy_storage_resources_exception(self, mock_fetch, mixin_instance):
        """Test get_energy_storage_resources handles exceptions gracefully."""
        mock_fetch.return_value = {"current": {"esr": "invalid"}}
        df = mixin_instance.get_energy_storage_resources()
        assert isinstance(df, pd.DataFrame)

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_capacity_committed_failure(self, mock_fetch, mixin_instance):
        """Test get_capacity_committed returns empty DataFrame on failure."""
        mock_fetch.return_value = None
        df = mixin_instance.get_capacity_committed()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_capacity_committed_empty_data(self, mock_fetch, mixin_instance):
        """Test get_capacity_committed with empty data list."""
        mock_fetch.return_value = {"data": [], "lastUpdated": 1704067200000}
        df = mixin_instance.get_capacity_committed()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_capacity_committed_exception(self, mock_fetch, mixin_instance):
        """Test get_capacity_committed handles exceptions gracefully."""
        mock_fetch.return_value = {"data": None}
        df = mixin_instance.get_capacity_committed()
        assert isinstance(df, pd.DataFrame)

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_status_with_alternative_field_names(self, mock_fetch, mixin_instance):
        """Test get_status parses alternative field names correctly."""
        mock_fetch.return_value = {
            "status": "normal",
            "load": 55000,
            "totalCapacity": 80000,
            "operatingReserves": 25000,
            "wind": 15000,
            "solar": 9000,
            "peak": 78000,
            "physicalResponsive": 4500,
            "timestamp": 1704067200000,
            "alert": "Test alert message",
        }
        status = mixin_instance.get_status()
        assert status.current_load == 55000.0
        assert status.capacity == 80000.0
        assert status.reserves == 25000.0


class TestFetchJsonGenericException:
    """Tests for _fetch_json generic exception handling."""

    @patch("tinygrid.ercot.dashboard.httpx.Client")
    def test_fetch_json_generic_exception(self, mock_client_class):
        """Test generic exception returns None."""
        from unittest.mock import MagicMock

        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("Unexpected error")
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client_class.return_value = mock_client

        result = _fetch_json("https://example.com/api")

        assert result is None


class TestDashboardAlternativeParsing:
    """Tests for alternative data structure parsing in dashboard methods."""

    @pytest.fixture
    def mixin_instance(self):
        """Create a test instance with the mixin."""

        class TestClass(ERCOTDashboardMixin):
            pass

        return TestClass()

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_fuel_mix_with_fuelMix_key(self, mock_fetch, mixin_instance):
        """Test get_fuel_mix parsing with 'fuelMix' key."""
        mock_fetch.return_value = {
            "fuelMix": [
                {"fuelType": "natural_gas", "generation": 30000},
            ],
            "timestamp": 1704067200000,
        }
        df = mixin_instance.get_fuel_mix()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]["fuel_type"] == "natural_gas"

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_fuel_mix_with_mw_key(self, mock_fetch, mixin_instance):
        """Test get_fuel_mix parsing with 'mw' key."""
        mock_fetch.return_value = {
            "data": [
                {"type": "coal", "mw": 20000, "percentage": 35},
            ],
            "lastUpdated": 1704067200000,
        }
        df = mixin_instance.get_fuel_mix()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]["generation_mw"] == 20000.0

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_supply_demand_with_hourly_key(self, mock_fetch, mixin_instance):
        """Test get_supply_demand parsing with 'hourly' key."""
        mock_fetch.return_value = {
            "hourly": [
                {"hourEnding": 1, "load": 45000, "capacity": 60000, "reserves": 15000},
            ],
            "lastUpdated": 1704067200000,
        }
        df = mixin_instance.get_supply_demand()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_daily_prices_with_prices_key(self, mock_fetch, mixin_instance):
        """Test get_daily_prices parsing with 'prices' key."""
        mock_fetch.return_value = {
            "prices": [
                {"sp": "HB_HOUSTON", "spp": 30.50, "peakPrice": 45.0, "avgPrice": 28.0},
            ],
            "lastUpdated": 1704067200000,
        }
        df = mixin_instance.get_daily_prices()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_renewable_with_alternative_keys(self, mock_fetch, mixin_instance):
        """Test get_renewable_generation parsing with alternative keys."""
        mock_fetch.return_value = {
            "current": {
                "wind": 18000,
                "solar": 8000,
                "windFcst": 19000,
                "solarFcst": 7500,
                "windCap": 35000,
                "solarCap": 20000,
            },
            "lastUpdated": 1704067200000,
        }
        status = mixin_instance.get_renewable_generation()
        assert status.wind_mw == 18000.0
        assert status.solar_mw == 8000.0
        assert status.wind_forecast_mw == 19000.0

    @patch("tinygrid.ercot.dashboard._fetch_json")
    def test_get_capacity_committed_with_hourly_key(self, mock_fetch, mixin_instance):
        """Test get_capacity_committed parsing with 'hourly' key."""
        mock_fetch.return_value = {
            "hourly": [
                {"hourEnding": 1, "supply": 60000, "capacity": 70000},
            ],
            "lastUpdated": 1704067200000,
        }
        df = mixin_instance.get_capacity_committed()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
