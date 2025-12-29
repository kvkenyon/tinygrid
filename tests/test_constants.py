"""Tests for ERCOT constants and enums."""

from tinygrid.constants.ercot import (
    COLUMN_MAPPINGS,
    EMIL_IDS,
    ENDPOINT_MAPPINGS,
    ERCOT_TIMEZONE,
    ESR_INTEGRATION_DATE,
    HISTORICAL_THRESHOLD_DAYS,
    LIVE_API_RETENTION,
    LOAD_ZONES,
    PUBLIC_API_BASE_URL,
    RTC_B_LAUNCH_DATE,
    TRADING_HUBS,
    AncillaryServiceType,
    LocationType,
    Market,
    ResourceType,
    SettlementPointType,
)


class TestMarketEnum:
    """Test Market enum."""

    def test_market_enum_values(self):
        """Test that Market enum has expected values."""
        assert Market.REAL_TIME_SCED == "REAL_TIME_SCED"
        assert Market.REAL_TIME_15_MIN == "REAL_TIME_15_MIN"
        assert Market.DAY_AHEAD_HOURLY == "DAY_AHEAD_HOURLY"

    def test_market_enum_is_string(self):
        """Test that Market enum values are strings."""
        assert isinstance(Market.REAL_TIME_SCED, str)
        assert isinstance(Market.REAL_TIME_15_MIN, str)
        assert isinstance(Market.DAY_AHEAD_HOURLY, str)

    def test_market_enum_str_representation(self):
        """Test string representation of Market enum."""
        assert str(Market.REAL_TIME_SCED) == "REAL_TIME_SCED"


class TestLocationTypeEnum:
    """Test LocationType enum."""

    def test_location_type_values(self):
        """Test that LocationType enum has expected values."""
        assert LocationType.LOAD_ZONE == "Load Zone"
        assert LocationType.TRADING_HUB == "Trading Hub"
        assert LocationType.RESOURCE_NODE == "Resource Node"
        assert LocationType.ELECTRICAL_BUS == "Electrical Bus"

    def test_location_type_is_string(self):
        """Test that LocationType enum values are strings."""
        assert isinstance(LocationType.LOAD_ZONE, str)
        assert isinstance(LocationType.TRADING_HUB, str)

    def test_location_type_str_representation(self):
        """Test string representation of LocationType enum."""
        assert str(LocationType.LOAD_ZONE) == "Load Zone"


class TestSettlementPointTypeEnum:
    """Test SettlementPointType enum."""

    def test_settlement_point_type_values(self):
        """Test that SettlementPointType enum has expected values."""
        assert SettlementPointType.LZ == "LZ"
        assert SettlementPointType.HB == "HB"
        assert SettlementPointType.RN == "RN"

    def test_settlement_point_type_is_string(self):
        """Test that SettlementPointType values are strings."""
        assert isinstance(SettlementPointType.LZ, str)
        assert isinstance(SettlementPointType.HB, str)


class TestConstants:
    """Test ERCOT constants."""

    def test_ercot_timezone(self):
        """Test ERCOT timezone constant."""
        assert ERCOT_TIMEZONE == "US/Central"

    def test_historical_threshold_days(self):
        """Test historical threshold constant."""
        assert HISTORICAL_THRESHOLD_DAYS == 90
        assert isinstance(HISTORICAL_THRESHOLD_DAYS, int)

    def test_public_api_base_url(self):
        """Test public API base URL."""
        assert PUBLIC_API_BASE_URL == "https://api.ercot.com/api/public-reports"
        assert PUBLIC_API_BASE_URL.startswith("https://")

    def test_load_zones_list(self):
        """Test LOAD_ZONES list."""
        assert isinstance(LOAD_ZONES, list)
        assert len(LOAD_ZONES) == 8
        assert "LZ_HOUSTON" in LOAD_ZONES
        assert "LZ_NORTH" in LOAD_ZONES
        assert "LZ_SOUTH" in LOAD_ZONES
        assert "LZ_WEST" in LOAD_ZONES

    def test_trading_hubs_list(self):
        """Test TRADING_HUBS list."""
        assert isinstance(TRADING_HUBS, list)
        assert len(TRADING_HUBS) == 7
        assert "HB_HOUSTON" in TRADING_HUBS
        assert "HB_NORTH" in TRADING_HUBS
        assert "HB_SOUTH" in TRADING_HUBS
        assert "HB_WEST" in TRADING_HUBS


class TestEndpointMappings:
    """Test ENDPOINT_MAPPINGS dictionary."""

    def test_endpoint_mappings_has_spp(self):
        """Test SPP endpoint mappings."""
        assert "spp" in ENDPOINT_MAPPINGS
        assert Market.REAL_TIME_15_MIN in ENDPOINT_MAPPINGS["spp"]
        assert Market.DAY_AHEAD_HOURLY in ENDPOINT_MAPPINGS["spp"]

    def test_endpoint_mappings_has_lmp(self):
        """Test LMP endpoint mappings."""
        assert "lmp" in ENDPOINT_MAPPINGS
        assert Market.REAL_TIME_SCED in ENDPOINT_MAPPINGS["lmp"]
        assert Market.DAY_AHEAD_HOURLY in ENDPOINT_MAPPINGS["lmp"]

    def test_endpoint_mappings_has_as_prices(self):
        """Test AS prices endpoint mapping."""
        assert "as_prices" in ENDPOINT_MAPPINGS
        assert isinstance(ENDPOINT_MAPPINGS["as_prices"], str)

    def test_endpoint_mappings_has_as_plan(self):
        """Test AS plan endpoint mapping."""
        assert "as_plan" in ENDPOINT_MAPPINGS
        assert isinstance(ENDPOINT_MAPPINGS["as_plan"], str)

    def test_endpoint_mappings_has_wind_solar(self):
        """Test wind and solar endpoint mappings."""
        assert "wind_forecast" in ENDPOINT_MAPPINGS
        assert "wind_forecast_geo" in ENDPOINT_MAPPINGS
        assert "solar_forecast" in ENDPOINT_MAPPINGS
        assert "solar_forecast_geo" in ENDPOINT_MAPPINGS


class TestLiveAPIRetention:
    """Test LIVE_API_RETENTION dictionary."""

    def test_live_api_retention_has_expected_keys(self):
        """Test that LIVE_API_RETENTION has expected categories."""
        assert "real_time" in LIVE_API_RETENTION
        assert "day_ahead" in LIVE_API_RETENTION
        assert "forecast" in LIVE_API_RETENTION
        assert "load" in LIVE_API_RETENTION
        assert "default" in LIVE_API_RETENTION

    def test_live_api_retention_values(self):
        """Test LIVE_API_RETENTION values."""
        assert LIVE_API_RETENTION["real_time"] == 1
        assert LIVE_API_RETENTION["day_ahead"] == 2
        assert LIVE_API_RETENTION["forecast"] == 3
        assert LIVE_API_RETENTION["load"] == 3
        assert LIVE_API_RETENTION["default"] == 1

    def test_live_api_retention_all_positive(self):
        """Test that all retention values are positive."""
        for value in LIVE_API_RETENTION.values():
            assert value > 0


class TestEmilIDs:
    """Test EMIL_IDs dictionary."""

    def test_emil_ids_has_disclosure_reports(self):
        """Test EMIL IDs for disclosure reports."""
        assert "as_reports_dam" in EMIL_IDS
        assert "as_reports_sced" in EMIL_IDS
        assert "dam_disclosure" in EMIL_IDS
        assert "sced_disclosure" in EMIL_IDS

    def test_emil_ids_has_real_time_endpoints(self):
        """Test EMIL IDs for real-time endpoints."""
        assert "np6-905-cd" in EMIL_IDS
        assert "np6-788-cd" in EMIL_IDS
        assert "np6-787-cd" in EMIL_IDS

    def test_emil_ids_has_dam_endpoints(self):
        """Test EMIL IDs for DAM endpoints."""
        assert "np4-190-cd" in EMIL_IDS
        assert "np4-183-cd" in EMIL_IDS
        assert "np4-188-cd" in EMIL_IDS
        assert "np4-33-cd" in EMIL_IDS

    def test_emil_ids_has_forecast_endpoints(self):
        """Test EMIL IDs for forecast endpoints."""
        assert "np4-732-cd" in EMIL_IDS
        assert "np4-742-cd" in EMIL_IDS
        assert "np4-737-cd" in EMIL_IDS
        assert "np4-745-cd" in EMIL_IDS

    def test_emil_ids_values_are_strings(self):
        """Test that all EMIL ID values are strings."""
        for value in EMIL_IDS.values():
            assert isinstance(value, str)


class TestColumnMappings:
    """Test COLUMN_MAPPINGS dictionary."""

    def test_column_mappings_has_location_columns(self):
        """Test column mappings for location fields."""
        assert "ElectricalBus" in COLUMN_MAPPINGS
        assert "SettlementPoint" in COLUMN_MAPPINGS
        assert "SettlementPointName" in COLUMN_MAPPINGS
        assert COLUMN_MAPPINGS["SettlementPoint"] == "Location"

    def test_column_mappings_has_price_columns(self):
        """Test column mappings for price fields."""
        assert "SettlementPointPrice" in COLUMN_MAPPINGS
        assert "LMP" in COLUMN_MAPPINGS
        assert "ShadowPrice" in COLUMN_MAPPINGS
        assert COLUMN_MAPPINGS["LMP"] == "Price"

    def test_column_mappings_has_time_columns(self):
        """Test column mappings for time fields."""
        assert "SCEDTimestamp" in COLUMN_MAPPINGS
        assert "DeliveryDate" in COLUMN_MAPPINGS
        assert "DeliveryHour" in COLUMN_MAPPINGS
        assert "PostedDatetime" in COLUMN_MAPPINGS
        assert COLUMN_MAPPINGS["SCEDTimestamp"] == "Timestamp"

    def test_column_mappings_has_flag_columns(self):
        """Test column mappings for flag fields."""
        assert "DSTFlag" in COLUMN_MAPPINGS
        assert "RepeatedHourFlag" in COLUMN_MAPPINGS
        assert COLUMN_MAPPINGS["DSTFlag"] == "DST"

    def test_column_mappings_values_are_strings(self):
        """Test that all column mapping values are strings."""
        for value in COLUMN_MAPPINGS.values():
            assert isinstance(value, str)


class TestResourceTypeEnum:
    """Test ResourceType enum (RTC+B).

    RTC+B (Real-Time Co-optimization + Batteries) introduced ESR as a new
    resource type for batteries in December 2024.
    """

    def test_resource_type_generation_values(self):
        """Test generation resource type values."""
        assert ResourceType.GEN == "GEN"
        assert ResourceType.WGR == "WGR"
        assert ResourceType.PVGR == "PVGR"
        assert ResourceType.SMNE == "SMNE"

    def test_resource_type_load_values(self):
        """Test load resource type values."""
        assert ResourceType.CLR == "CLR"
        assert ResourceType.LR == "LR"
        assert ResourceType.DSR == "DSR"

    def test_resource_type_esr_values(self):
        """Test ESR resource type values (RTC+B addition)."""
        assert ResourceType.ESR == "ESR"
        assert ResourceType.DESR == "DESR"
        assert ResourceType.DGR == "DGR"

    def test_resource_type_is_string(self):
        """Test that ResourceType enum values are strings."""
        assert isinstance(ResourceType.ESR, str)
        assert isinstance(ResourceType.GEN, str)

    def test_resource_type_str_representation(self):
        """Test string representation of ResourceType enum."""
        assert str(ResourceType.ESR) == "ESR"
        assert str(ResourceType.GEN) == "GEN"


class TestAncillaryServiceTypeEnum:
    """Test AncillaryServiceType enum.

    RTC+B modified how ancillary services are procured in real-time with
    co-optimization of energy and AS.
    """

    def test_as_type_regulation_values(self):
        """Test regulation service type values."""
        assert AncillaryServiceType.REGUP == "REGUP"
        assert AncillaryServiceType.REGDN == "REGDN"

    def test_as_type_rrs_values(self):
        """Test responsive reserve service type values."""
        assert AncillaryServiceType.RRSPFR == "RRSPFR"
        assert AncillaryServiceType.RRSFFR == "RRSFFR"
        assert AncillaryServiceType.RRSUFR == "RRSUFR"

    def test_as_type_nspin_values(self):
        """Test non-spinning reserve type values."""
        assert AncillaryServiceType.NSPIN == "NSPIN"
        assert AncillaryServiceType.NSPNM == "NSPNM"
        assert AncillaryServiceType.ONNS == "ONNS"
        assert AncillaryServiceType.OFFNS == "OFFNS"

    def test_as_type_ecrs_values(self):
        """Test ECRS type values."""
        assert AncillaryServiceType.ECRSM == "ECRSM"
        assert AncillaryServiceType.ECRSS == "ECRSS"

    def test_as_type_is_string(self):
        """Test that AncillaryServiceType enum values are strings."""
        assert isinstance(AncillaryServiceType.REGUP, str)
        assert isinstance(AncillaryServiceType.NSPIN, str)

    def test_as_type_str_representation(self):
        """Test string representation of AncillaryServiceType enum."""
        assert str(AncillaryServiceType.REGUP) == "REGUP"
        assert str(AncillaryServiceType.ECRSM) == "ECRSM"


class TestRTCBConstants:
    """Test RTC+B (Real-Time Co-optimization + Batteries) constants."""

    def test_rtc_b_launch_date(self):
        """Test RTC+B launch date constant."""
        assert RTC_B_LAUNCH_DATE == "2024-12-04"
        assert isinstance(RTC_B_LAUNCH_DATE, str)

    def test_esr_integration_date(self):
        """Test ESR integration date constant."""
        assert ESR_INTEGRATION_DATE == "2024-06-01"
        assert isinstance(ESR_INTEGRATION_DATE, str)

    def test_dates_are_valid_iso_format(self):
        """Test that RTC+B dates are valid ISO format."""
        import datetime

        # Should not raise exception
        datetime.date.fromisoformat(RTC_B_LAUNCH_DATE)
        datetime.date.fromisoformat(ESR_INTEGRATION_DATE)

    def test_esr_integration_before_rtc_b(self):
        """Test that ESR integration date is before RTC+B launch."""
        import datetime

        esr_date = datetime.date.fromisoformat(ESR_INTEGRATION_DATE)
        rtc_b_date = datetime.date.fromisoformat(RTC_B_LAUNCH_DATE)
        assert esr_date < rtc_b_date
