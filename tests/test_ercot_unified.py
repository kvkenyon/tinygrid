"""Tests for the unified ERCOT API methods."""

from unittest.mock import patch

import pandas as pd
import pytest

from tinygrid import ERCOT, LocationType, Market
from tinygrid.constants.ercot import LOAD_ZONES, TRADING_HUBS
from tinygrid.utils.dates import parse_date, parse_date_range


class TestDateUtilities:
    """Tests for date parsing utilities."""

    def test_parse_date_today(self):
        """Test parsing 'today' keyword."""
        result = parse_date("today")
        expected = pd.Timestamp.now(tz="US/Central").normalize()
        assert result == expected

    def test_parse_date_latest(self):
        """Test parsing 'latest' keyword (alias for today)."""
        result = parse_date("latest")
        expected = pd.Timestamp.now(tz="US/Central").normalize()
        assert result == expected

    def test_parse_date_yesterday(self):
        """Test parsing 'yesterday' keyword."""
        result = parse_date("yesterday")
        expected = (
            pd.Timestamp.now(tz="US/Central") - pd.Timedelta(days=1)
        ).normalize()
        assert result == expected

    def test_parse_date_iso_string(self):
        """Test parsing ISO format date string."""
        result = parse_date("2024-01-15")
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.tz is not None

    def test_parse_date_range_default_end(self):
        """Test that end defaults to start + 1 day."""
        start, end = parse_date_range("2024-01-15")
        assert start.day == 15
        assert end.day == 16

    def test_parse_date_range_explicit_end(self):
        """Test explicit end date."""
        start, end = parse_date_range("2024-01-15", "2024-01-20")
        assert start.day == 15
        assert end.day == 20


class TestMarketEnum:
    """Tests for Market enum."""

    def test_market_values(self):
        """Test that Market enum has expected values."""
        assert Market.REAL_TIME_SCED == "REAL_TIME_SCED"
        assert Market.REAL_TIME_15_MIN == "REAL_TIME_15_MIN"
        assert Market.DAY_AHEAD_HOURLY == "DAY_AHEAD_HOURLY"

    def test_market_is_string(self):
        """Test that Market enum values are strings."""
        assert isinstance(Market.REAL_TIME_SCED.value, str)


class TestLocationTypeEnum:
    """Tests for LocationType enum."""

    def test_location_type_values(self):
        """Test that LocationType enum has expected values."""
        assert LocationType.LOAD_ZONE == "Load Zone"
        assert LocationType.TRADING_HUB == "Trading Hub"
        assert LocationType.RESOURCE_NODE == "Resource Node"
        assert LocationType.ELECTRICAL_BUS == "Electrical Bus"


class TestERCOTUnifiedMethods:
    """Tests for ERCOT unified methods."""

    @pytest.fixture
    def ercot(self):
        """Create an ERCOT client instance."""
        return ERCOT()

    def test_filter_by_location_load_zones(self, ercot):
        """Test filtering DataFrame by load zones."""
        df = pd.DataFrame(
            {
                "Settlement Point": [
                    "LZ_HOUSTON",
                    "HB_NORTH",
                    "RESOURCE_1",
                    "LZ_NORTH",
                ],
                "Price": [10, 20, 30, 40],
            }
        )

        result = ercot._filter_by_location(
            df, location_type=LocationType.LOAD_ZONE
        )

        assert len(result) == 2
        assert set(result["Settlement Point"]) == {"LZ_HOUSTON", "LZ_NORTH"}

    def test_filter_by_location_trading_hubs(self, ercot):
        """Test filtering DataFrame by trading hubs."""
        df = pd.DataFrame(
            {
                "Settlement Point": [
                    "LZ_HOUSTON",
                    "HB_NORTH",
                    "HB_SOUTH",
                    "RESOURCE_1",
                ],
                "Price": [10, 20, 30, 40],
            }
        )

        result = ercot._filter_by_location(
            df, location_type=LocationType.TRADING_HUB
        )

        assert len(result) == 2
        assert set(result["Settlement Point"]) == {"HB_NORTH", "HB_SOUTH"}

    def test_filter_by_specific_locations(self, ercot):
        """Test filtering DataFrame by specific location names."""
        df = pd.DataFrame(
            {
                "Settlement Point": [
                    "LZ_HOUSTON",
                    "LZ_NORTH",
                    "LZ_SOUTH",
                    "LZ_WEST",
                ],
                "Price": [10, 20, 30, 40],
            }
        )

        result = ercot._filter_by_location(
            df, locations=["LZ_HOUSTON", "LZ_NORTH"]
        )

        assert len(result) == 2
        assert set(result["Settlement Point"]) == {"LZ_HOUSTON", "LZ_NORTH"}

    def test_filter_by_location_empty_df(self, ercot):
        """Test filtering empty DataFrame."""
        df = pd.DataFrame()
        result = ercot._filter_by_location(
            df, location_type=LocationType.LOAD_ZONE
        )
        assert result.empty

    def test_should_use_historical_old_date(self, ercot):
        """Test that old dates use historical API."""
        old_date = pd.Timestamp.now(tz="US/Central") - pd.Timedelta(days=100)
        assert ercot._should_use_historical(old_date) is True

    def test_should_use_historical_recent_date(self, ercot):
        """Test that recent dates don't use historical API."""
        recent_date = pd.Timestamp.now(tz="US/Central") - pd.Timedelta(days=30)
        assert ercot._should_use_historical(recent_date) is False

    def test_needs_historical_today(self, ercot):
        """Test that today's date doesn't need historical for real-time."""
        today = pd.Timestamp.now(tz="US/Central").normalize()
        assert ercot._needs_historical(today, "real_time") is False

    def test_needs_historical_yesterday(self, ercot):
        """Test that yesterday needs historical for real-time data."""
        yesterday = pd.Timestamp.now(
            tz="US/Central"
        ).normalize() - pd.Timedelta(days=1)
        assert ercot._needs_historical(yesterday, "real_time") is True

    def test_needs_historical_day_ahead_recent(self, ercot):
        """Test that today doesn't need historical for day-ahead."""
        today = pd.Timestamp.now(tz="US/Central").normalize()
        assert ercot._needs_historical(today, "day_ahead") is False

    def test_needs_historical_day_ahead_old(self, ercot):
        """Test that old dates need historical for day-ahead."""
        old = pd.Timestamp.now(tz="US/Central").normalize() - pd.Timedelta(
            days=10
        )
        assert ercot._needs_historical(old, "day_ahead") is True

    @patch.object(ERCOT, "get_spp_node_zone_hub")
    def test_get_spp_real_time_today(self, mock_method, ercot):
        """Test get_spp uses live API for today's real-time data."""
        mock_method.return_value = pd.DataFrame(
            {
                "Settlement Point": ["LZ_HOUSTON"],
                "SPP": [50.0],
                "Delivery Date": [pd.Timestamp.now().strftime("%Y-%m-%d")],
            }
        )

        ercot.get_spp(start="today", market=Market.REAL_TIME_15_MIN)

        mock_method.assert_called_once()

    @patch.object(ERCOT, "_get_archive")
    def test_get_spp_real_time_yesterday_uses_historical(
        self, mock_archive, ercot
    ):
        """Test get_spp uses historical archive for yesterday's real-time data."""
        mock_archive.return_value.fetch_historical.return_value = pd.DataFrame(
            {
                "Settlement Point": ["LZ_HOUSTON"],
                "SPP": [50.0],
                "Delivery Date": [
                    (pd.Timestamp.now() - pd.Timedelta(days=1)).strftime(
                        "%Y-%m-%d"
                    )
                ],
            }
        )

        ercot.get_spp(start="yesterday", market=Market.REAL_TIME_15_MIN)

        mock_archive.return_value.fetch_historical.assert_called_once()
        call_args = mock_archive.return_value.fetch_historical.call_args
        assert "/np6-905-cd/spp_node_zone_hub" in call_args.kwargs["endpoint"]

    @patch.object(ERCOT, "_needs_historical", return_value=False)
    @patch.object(ERCOT, "get_dam_settlement_point_prices")
    def test_get_spp_day_ahead(self, mock_method, mock_needs_hist, ercot):
        """Test get_spp routes to correct endpoint for day-ahead market."""
        mock_method.return_value = pd.DataFrame(
            {
                "Settlement Point": ["LZ_HOUSTON"],
                "SPP": [50.0],
                "Delivery Date": ["2024-01-15"],
            }
        )

        ercot.get_spp(start="today", market=Market.DAY_AHEAD_HOURLY)

        mock_method.assert_called_once()

    @patch.object(ERCOT, "_needs_historical", return_value=False)
    @patch.object(ERCOT, "get_lmp_node_zone_hub")
    def test_get_lmp_real_time_node(self, mock_method, mock_needs_hist, ercot):
        """Test get_lmp routes to node/zone/hub endpoint."""
        mock_method.return_value = pd.DataFrame(
            {
                "Location": ["NODE_1"],
                "LMP": [50.0],
                "Delivery Date": ["2024-01-15"],
            }
        )

        ercot.get_lmp(start="today", market=Market.REAL_TIME_SCED)

        mock_method.assert_called_once()

    @patch.object(ERCOT, "_needs_historical", return_value=False)
    @patch.object(ERCOT, "get_lmp_electrical_bus")
    def test_get_lmp_electrical_bus(self, mock_method, mock_needs_hist, ercot):
        """Test get_lmp routes to electrical bus endpoint."""
        mock_method.return_value = pd.DataFrame(
            {
                "Location": ["BUS_1"],
                "LMP": [50.0],
                "Delivery Date": ["2024-01-15"],
            }
        )

        ercot.get_lmp(
            start="today",
            market=Market.REAL_TIME_SCED,
            location_type=LocationType.ELECTRICAL_BUS,
        )

        mock_method.assert_called_once()

    @patch.object(ERCOT, "_needs_historical", return_value=False)
    @patch.object(ERCOT, "get_dam_clear_price_for_cap")
    def test_get_as_prices(self, mock_method, mock_needs_hist, ercot):
        """Test get_as_prices calls correct endpoint."""
        mock_method.return_value = pd.DataFrame(
            {
                "AS Type": ["REGUP"],
                "MCPC": [10.0],
                "Delivery Date": ["2024-01-15"],
            }
        )

        ercot.get_as_prices(start="today")

        mock_method.assert_called_once()

    @patch.object(ERCOT, "_needs_historical", return_value=False)
    @patch.object(ERCOT, "get_dam_as_plan")
    def test_get_as_plan(self, mock_method, mock_needs_hist, ercot):
        """Test get_as_plan calls correct endpoint."""
        mock_method.return_value = pd.DataFrame(
            {"Hour": [1], "REGUP": [100.0], "Delivery Date": ["2024-01-15"]}
        )

        ercot.get_as_plan(start="today")

        mock_method.assert_called_once()


class TestConstants:
    """Tests for ERCOT constants."""

    def test_load_zones_list(self):
        """Test that load zones list contains expected values."""
        assert "LZ_HOUSTON" in LOAD_ZONES
        assert "LZ_NORTH" in LOAD_ZONES
        assert "LZ_SOUTH" in LOAD_ZONES
        assert "LZ_WEST" in LOAD_ZONES

    def test_trading_hubs_list(self):
        """Test that trading hubs list contains expected values."""
        assert "HB_HOUSTON" in TRADING_HUBS
        assert "HB_NORTH" in TRADING_HUBS
        assert "HB_SOUTH" in TRADING_HUBS
        assert "HB_WEST" in TRADING_HUBS
