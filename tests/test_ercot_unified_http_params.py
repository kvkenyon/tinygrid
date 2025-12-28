"""Tests for unified method parameter validation via HTTP interception.

These tests validate that unified methods (get_spp, get_lmp, get_as_prices, get_as_plan)
correctly transform their parameters and pass them to the underlying API endpoints.
"""

from unittest.mock import patch

import httpx
import pandas as pd
import respx

from tinygrid import ERCOT, LocationType, Market

# Base URLs for ERCOT API
ERCOT_API_BASE_URL = "https://api.ercot.com/api/public-reports"
ERCOT_PUBLIC_API_BASE_URL = "https://api.ercot.com/api/public-reports"


class TestUnifiedSPPParameters:
    """Test parameter passing for get_spp unified method."""

    @respx.mock
    def test_get_spp_real_time_passes_correct_date_params(self, sample_rtm_response):
        """Test get_spp (real-time) passes correctly formatted date parameters."""
        route = respx.get(f"{ERCOT_API_BASE_URL}/np6-905-cd/spp_node_zone_hub").mock(
            return_value=httpx.Response(200, json=sample_rtm_response)
        )

        ercot = ERCOT()
        # Patch _needs_historical at the class level to return False
        with patch("tinygrid.ercot.ERCOT._needs_historical", return_value=False):
            ercot.get_spp(
                start="2024-01-15",
                end="2024-01-16",
                market=Market.REAL_TIME_15_MIN,
            )

        assert route.called
        request = route.calls.last.request
        assert "deliveryDateFrom" in request.url.params
        assert request.url.params["deliveryDateFrom"] == "2024-01-15"
        assert "deliveryDateTo" in request.url.params
        assert request.url.params["deliveryDateTo"] == "2024-01-16"
        assert "deliveryHourFrom" in request.url.params
        assert request.url.params["deliveryHourFrom"] == "1"
        assert "deliveryHourTo" in request.url.params
        assert request.url.params["deliveryHourTo"] == "24"

    @respx.mock
    def test_get_spp_real_time_passes_interval_params(self, sample_rtm_response):
        """Test get_spp (real-time) passes delivery interval parameters."""
        route = respx.get(f"{ERCOT_API_BASE_URL}/np6-905-cd/spp_node_zone_hub").mock(
            return_value=httpx.Response(200, json=sample_rtm_response)
        )

        ercot = ERCOT()
        # Patch _needs_historical at the class level to return False
        with patch("tinygrid.ercot.ERCOT._needs_historical", return_value=False):
            ercot.get_spp(start="2024-01-15", market=Market.REAL_TIME_15_MIN)

        assert route.called
        request = route.calls.last.request
        assert "deliveryIntervalFrom" in request.url.params
        assert request.url.params["deliveryIntervalFrom"] == "1"
        assert "deliveryIntervalTo" in request.url.params
        assert request.url.params["deliveryIntervalTo"] == "4"

    @respx.mock
    def test_get_spp_day_ahead_passes_correct_date_params(self, sample_dam_response):
        """Test get_spp (day-ahead) passes correctly formatted date parameters."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np4-190-cd/dam_stlmnt_pnt_prices"
        ).mock(return_value=httpx.Response(200, json=sample_dam_response))

        ercot = ERCOT()
        # Use today to avoid historical path
        # Note: parse_date_range ensures end > start, so end becomes tomorrow
        ercot.get_spp(start="today", end="today", market=Market.DAY_AHEAD_HOURLY)

        assert route.called
        request = route.calls.last.request
        assert "deliveryDateFrom" in request.url.params
        # Date should be formatted as YYYY-MM-DD
        today_str = pd.Timestamp.now(tz="US/Central").strftime("%Y-%m-%d")
        tomorrow_str = (
            pd.Timestamp.now(tz="US/Central") + pd.Timedelta(days=1)
        ).strftime("%Y-%m-%d")
        assert request.url.params["deliveryDateFrom"] == today_str
        assert "deliveryDateTo" in request.url.params
        assert request.url.params["deliveryDateTo"] == tomorrow_str

    @respx.mock
    def test_get_spp_parses_today_keyword(self, sample_rtm_response):
        """Test get_spp correctly parses 'today' keyword and formats date."""
        route = respx.get(f"{ERCOT_API_BASE_URL}/np6-905-cd/spp_node_zone_hub").mock(
            return_value=httpx.Response(200, json=sample_rtm_response)
        )

        ercot = ERCOT()
        today_str = pd.Timestamp.now(tz="US/Central").strftime("%Y-%m-%d")
        ercot.get_spp(start="today", market=Market.REAL_TIME_15_MIN)

        assert route.called
        request = route.calls.last.request
        assert request.url.params["deliveryDateFrom"] == today_str

    @respx.mock
    def test_get_spp_parses_yesterday_keyword(self, sample_rtm_response):
        """Test get_spp correctly parses 'yesterday' keyword and formats date."""
        route = respx.get(f"{ERCOT_API_BASE_URL}/np6-905-cd/spp_node_zone_hub").mock(
            return_value=httpx.Response(200, json=sample_rtm_response)
        )

        ercot = ERCOT()
        yesterday_str = (
            pd.Timestamp.now(tz="US/Central") - pd.Timedelta(days=1)
        ).strftime("%Y-%m-%d")
        # Patch _needs_historical at the class level to return False
        with patch("tinygrid.ercot.ERCOT._needs_historical", return_value=False):
            ercot.get_spp(start="yesterday", market=Market.REAL_TIME_15_MIN)

        assert route.called
        request = route.calls.last.request
        assert request.url.params["deliveryDateFrom"] == yesterday_str

    @respx.mock
    def test_get_spp_defaults_end_to_start_plus_one_day(self, sample_rtm_response):
        """Test get_spp defaults end date to start + 1 day when not provided."""
        route = respx.get(f"{ERCOT_API_BASE_URL}/np6-905-cd/spp_node_zone_hub").mock(
            return_value=httpx.Response(200, json=sample_rtm_response)
        )

        ercot = ERCOT()
        # Patch _needs_historical at the class level to return False
        with patch("tinygrid.ercot.ERCOT._needs_historical", return_value=False):
            ercot.get_spp(start="2024-01-15", market=Market.REAL_TIME_15_MIN)

        assert route.called
        request = route.calls.last.request
        assert request.url.params["deliveryDateFrom"] == "2024-01-15"
        assert request.url.params["deliveryDateTo"] == "2024-01-16"


class TestUnifiedLMPParameters:
    """Test parameter passing for get_lmp unified method."""

    @respx.mock
    def test_get_lmp_real_time_node_passes_sced_timestamp_params(
        self, sample_rtm_response
    ):
        """Test get_lmp (real-time, node) passes sced_timestamp parameters."""
        route = respx.get(f"{ERCOT_API_BASE_URL}/np6-788-cd/lmp_node_zone_hub").mock(
            return_value=httpx.Response(200, json=sample_rtm_response)
        )

        ercot = ERCOT()
        # Use "today" to ensure we use live API, not historical
        # Note: end defaults to start + 1 day when not provided
        ercot.get_lmp(
            start="today",
            market=Market.REAL_TIME_SCED,
            location_type=LocationType.RESOURCE_NODE,
        )

        assert route.called
        request = route.calls.last.request
        # API uses SCEDTimestampFrom (uppercase) - pyercot converts snake_case to camelCase
        assert "SCEDTimestampFrom" in request.url.params
        # Date should be formatted as YYYY-MM-DD
        today_str = pd.Timestamp.now(tz="US/Central").strftime("%Y-%m-%d")
        tomorrow_str = (
            pd.Timestamp.now(tz="US/Central") + pd.Timedelta(days=1)
        ).strftime("%Y-%m-%d")
        assert request.url.params["SCEDTimestampFrom"] == today_str
        assert "SCEDTimestampTo" in request.url.params
        assert request.url.params["SCEDTimestampTo"] == tomorrow_str

    @respx.mock
    def test_get_lmp_real_time_electrical_bus_passes_sced_timestamp_params(
        self, sample_rtm_response
    ):
        """Test get_lmp (real-time, electrical bus) passes sced_timestamp parameters."""
        route = respx.get(f"{ERCOT_API_BASE_URL}/np6-787-cd/lmp_electrical_bus").mock(
            return_value=httpx.Response(200, json=sample_rtm_response)
        )

        ercot = ERCOT()
        # Use "today" to ensure we use live API, not historical
        # Note: end defaults to start + 1 day when not provided
        ercot.get_lmp(
            start="today",
            market=Market.REAL_TIME_SCED,
            location_type=LocationType.ELECTRICAL_BUS,
        )

        assert route.called
        request = route.calls.last.request
        # API uses SCEDTimestampFrom (uppercase) - pyercot converts snake_case to camelCase
        assert "SCEDTimestampFrom" in request.url.params
        # Date should be formatted as YYYY-MM-DD
        today_str = pd.Timestamp.now(tz="US/Central").strftime("%Y-%m-%d")
        tomorrow_str = (
            pd.Timestamp.now(tz="US/Central") + pd.Timedelta(days=1)
        ).strftime("%Y-%m-%d")
        assert request.url.params["SCEDTimestampFrom"] == today_str
        assert "SCEDTimestampTo" in request.url.params
        assert request.url.params["SCEDTimestampTo"] == tomorrow_str

    @respx.mock
    def test_get_lmp_day_ahead_passes_start_end_date_params(self, sample_dam_response):
        """Test get_lmp (day-ahead) passes start_date and end_date parameters."""
        route = respx.get(f"{ERCOT_API_BASE_URL}/np4-183-cd/dam_hourly_lmp").mock(
            return_value=httpx.Response(200, json=sample_dam_response)
        )

        ercot = ERCOT()
        # Patch _needs_historical at the class level to return False
        with patch("tinygrid.ercot.ERCOT._needs_historical", return_value=False):
            ercot.get_lmp(
                start="2024-01-15",
                end="2024-01-16",
                market=Market.DAY_AHEAD_HOURLY,
            )

        assert route.called
        request = route.calls.last.request
        # DAM hourly LMP uses deliveryDateFrom, not startDate
        assert "deliveryDateFrom" in request.url.params
        assert request.url.params["deliveryDateFrom"] == "2024-01-15"
        assert "deliveryDateTo" in request.url.params
        assert request.url.params["deliveryDateTo"] == "2024-01-16"

    @respx.mock
    def test_get_lmp_parses_date_keywords(self, sample_rtm_response):
        """Test get_lmp correctly parses date keywords."""
        route = respx.get(f"{ERCOT_API_BASE_URL}/np6-788-cd/lmp_node_zone_hub").mock(
            return_value=httpx.Response(200, json=sample_rtm_response)
        )

        ercot = ERCOT()
        today_str = pd.Timestamp.now(tz="US/Central").strftime("%Y-%m-%d")
        ercot.get_lmp(start="today", market=Market.REAL_TIME_SCED)

        assert route.called
        request = route.calls.last.request
        # API uses SCEDTimestampFrom (uppercase)
        assert request.url.params["SCEDTimestampFrom"] == today_str


class TestUnifiedASPricesParameters:
    """Test parameter passing for get_as_prices unified method."""

    @respx.mock
    def test_get_as_prices_passes_delivery_date_params(self, sample_dam_response):
        """Test get_as_prices passes delivery_date parameters."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np4-188-cd/dam_clear_price_for_cap"
        ).mock(return_value=httpx.Response(200, json=sample_dam_response))

        ercot = ERCOT()
        # Patch _needs_historical at the class level to return False
        with patch("tinygrid.ercot.ERCOT._needs_historical", return_value=False):
            ercot.get_as_prices(start="2024-01-15", end="2024-01-16")

        assert route.called
        request = route.calls.last.request
        assert "deliveryDateFrom" in request.url.params
        assert request.url.params["deliveryDateFrom"] == "2024-01-15"
        assert "deliveryDateTo" in request.url.params
        assert request.url.params["deliveryDateTo"] == "2024-01-16"

    @respx.mock
    def test_get_as_prices_parses_date_keywords(self, sample_dam_response):
        """Test get_as_prices correctly parses date keywords."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np4-188-cd/dam_clear_price_for_cap"
        ).mock(return_value=httpx.Response(200, json=sample_dam_response))

        ercot = ERCOT()
        today_str = pd.Timestamp.now(tz="US/Central").strftime("%Y-%m-%d")
        ercot.get_as_prices(start="today")

        assert route.called
        request = route.calls.last.request
        assert request.url.params["deliveryDateFrom"] == today_str


class TestUnifiedASPlanParameters:
    """Test parameter passing for get_as_plan unified method."""

    @respx.mock
    def test_get_as_plan_passes_delivery_date_params(self, sample_dam_response):
        """Test get_as_plan passes delivery_date parameters."""
        route = respx.get(f"{ERCOT_API_BASE_URL}/np4-33-cd/dam_as_plan").mock(
            return_value=httpx.Response(200, json=sample_dam_response)
        )

        ercot = ERCOT()
        # Patch _needs_historical at the class level to return False
        with patch("tinygrid.ercot.ERCOT._needs_historical", return_value=False):
            ercot.get_as_plan(start="2024-01-15", end="2024-01-16")

        assert route.called
        request = route.calls.last.request
        assert "deliveryDateFrom" in request.url.params
        assert request.url.params["deliveryDateFrom"] == "2024-01-15"
        assert "deliveryDateTo" in request.url.params
        assert request.url.params["deliveryDateTo"] == "2024-01-16"

    @respx.mock
    def test_get_as_plan_parses_date_keywords(self, sample_dam_response):
        """Test get_as_plan correctly parses date keywords."""
        route = respx.get(f"{ERCOT_API_BASE_URL}/np4-33-cd/dam_as_plan").mock(
            return_value=httpx.Response(200, json=sample_dam_response)
        )

        ercot = ERCOT()
        today_str = pd.Timestamp.now(tz="US/Central").strftime("%Y-%m-%d")
        ercot.get_as_plan(start="today")

        assert route.called
        request = route.calls.last.request
        assert request.url.params["deliveryDateFrom"] == today_str


class TestUnifiedHistoricalParameters:
    """Test parameter passing for unified methods when using historical archive."""

    @respx.mock
    def test_get_spp_real_time_historical_passes_correct_params(
        self, sample_archive_listing_response, create_mock_zip_response
    ):
        """Test get_spp (real-time, historical) passes correct archive parameters."""
        # Mock archive listing
        listing_route = respx.get(
            f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np6-905-cd"
        ).mock(return_value=httpx.Response(200, json=sample_archive_listing_response))

        # Mock bulk download
        download_route = respx.post(
            f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np6-905-cd/download"
        ).mock(return_value=httpx.Response(200, content=create_mock_zip_response()))

        ercot = ERCOT()
        # Use old date to trigger historical path
        old_date = pd.Timestamp.now(tz="US/Central") - pd.Timedelta(days=100)
        ercot.get_spp(
            start=old_date,
            end=old_date + pd.Timedelta(days=1),
            market=Market.REAL_TIME_15_MIN,
        )

        # Verify archive listing was called with correct datetime params
        assert listing_route.called
        listing_request = listing_route.calls.last.request
        assert "postDatetimeFrom" in listing_request.url.params
        assert "postDatetimeTo" in listing_request.url.params
        # Verify datetime format (YYYY-MM-DDTHH:MM:SS)
        post_datetime_from = listing_request.url.params["postDatetimeFrom"]
        assert "T" in post_datetime_from
        assert len(post_datetime_from) == 19  # YYYY-MM-DDTHH:MM:SS format
        # Verify datetime format (YYYY-MM-DDTHH:MM:SS)
        post_datetime_from = listing_request.url.params["postDatetimeFrom"]
        assert "T" in post_datetime_from
        assert len(post_datetime_from) == 19  # YYYY-MM-DDTHH:MM:SS format

        # Verify bulk download was called
        assert download_route.called
        download_request = download_route.calls.last.request
        assert download_request.method == "POST"
        # Verify docIds are in the request body (JSON format)
        import json

        body = download_request.content
        assert body is not None
        body_json = json.loads(body.decode())
        assert "docIds" in body_json
        assert isinstance(body_json["docIds"], list)

    @respx.mock
    def test_get_spp_day_ahead_historical_passes_correct_params(
        self, sample_archive_listing_response, create_mock_zip_response
    ):
        """Test get_spp (day-ahead, historical) passes correct archive parameters."""
        listing_route = respx.get(
            f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np4-190-cd"
        ).mock(return_value=httpx.Response(200, json=sample_archive_listing_response))

        respx.post(f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np4-190-cd/download").mock(
            return_value=httpx.Response(200, content=create_mock_zip_response())
        )

        ercot = ERCOT()
        old_date = pd.Timestamp.now(tz="US/Central") - pd.Timedelta(days=100)
        ercot.get_spp(
            start=old_date,
            end=old_date + pd.Timedelta(days=1),
            market=Market.DAY_AHEAD_HOURLY,
        )

        assert listing_route.called
        listing_request = listing_route.calls.last.request
        assert "postDatetimeFrom" in listing_request.url.params
        assert "postDatetimeTo" in listing_request.url.params
        # Verify datetime format (YYYY-MM-DDTHH:MM:SS)
        post_datetime_from = listing_request.url.params["postDatetimeFrom"]
        assert "T" in post_datetime_from
        assert len(post_datetime_from) == 19  # YYYY-MM-DDTHH:MM:SS format

    @respx.mock
    def test_get_lmp_real_time_historical_passes_correct_params(
        self, sample_archive_listing_response, create_mock_zip_response
    ):
        """Test get_lmp (real-time, historical) passes correct archive parameters."""
        listing_route = respx.get(
            f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np6-788-cd"
        ).mock(return_value=httpx.Response(200, json=sample_archive_listing_response))

        respx.post(f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np6-788-cd/download").mock(
            return_value=httpx.Response(200, content=create_mock_zip_response())
        )

        ercot = ERCOT()
        old_date = pd.Timestamp.now(tz="US/Central") - pd.Timedelta(days=100)
        ercot.get_lmp(
            start=old_date,
            end=old_date + pd.Timedelta(days=1),
            market=Market.REAL_TIME_SCED,
            location_type=LocationType.RESOURCE_NODE,
        )

        assert listing_route.called
        listing_request = listing_route.calls.last.request
        assert "postDatetimeFrom" in listing_request.url.params
        assert "postDatetimeTo" in listing_request.url.params
        # Verify datetime format (YYYY-MM-DDTHH:MM:SS)
        post_datetime_from = listing_request.url.params["postDatetimeFrom"]
        assert "T" in post_datetime_from
        assert len(post_datetime_from) == 19  # YYYY-MM-DDTHH:MM:SS format

    @respx.mock
    def test_get_lmp_electrical_bus_historical_passes_correct_params(
        self, sample_archive_listing_response, create_mock_zip_response
    ):
        """Test get_lmp (electrical bus, historical) passes correct archive parameters."""
        listing_route = respx.get(
            f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np6-787-cd"
        ).mock(return_value=httpx.Response(200, json=sample_archive_listing_response))

        respx.post(f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np6-787-cd/download").mock(
            return_value=httpx.Response(200, content=create_mock_zip_response())
        )

        ercot = ERCOT()
        old_date = pd.Timestamp.now(tz="US/Central") - pd.Timedelta(days=100)
        ercot.get_lmp(
            start=old_date,
            end=old_date + pd.Timedelta(days=1),
            market=Market.REAL_TIME_SCED,
            location_type=LocationType.ELECTRICAL_BUS,
        )

        assert listing_route.called
        listing_request = listing_route.calls.last.request
        assert "postDatetimeFrom" in listing_request.url.params
        assert "postDatetimeTo" in listing_request.url.params
        # Verify datetime format (YYYY-MM-DDTHH:MM:SS)
        post_datetime_from = listing_request.url.params["postDatetimeFrom"]
        assert "T" in post_datetime_from
        assert len(post_datetime_from) == 19  # YYYY-MM-DDTHH:MM:SS format

    @respx.mock
    def test_get_lmp_day_ahead_historical_passes_correct_params(
        self, sample_archive_listing_response, create_mock_zip_response
    ):
        """Test get_lmp (day-ahead, historical) passes correct archive parameters."""
        listing_route = respx.get(
            f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np4-183-cd"
        ).mock(return_value=httpx.Response(200, json=sample_archive_listing_response))

        respx.post(f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np4-183-cd/download").mock(
            return_value=httpx.Response(200, content=create_mock_zip_response())
        )

        ercot = ERCOT()
        old_date = pd.Timestamp.now(tz="US/Central") - pd.Timedelta(days=100)
        ercot.get_lmp(
            start=old_date,
            end=old_date + pd.Timedelta(days=1),
            market=Market.DAY_AHEAD_HOURLY,
        )

        assert listing_route.called
        listing_request = listing_route.calls.last.request
        assert "postDatetimeFrom" in listing_request.url.params
        assert "postDatetimeTo" in listing_request.url.params
        # Verify datetime format (YYYY-MM-DDTHH:MM:SS)
        post_datetime_from = listing_request.url.params["postDatetimeFrom"]
        assert "T" in post_datetime_from
        assert len(post_datetime_from) == 19  # YYYY-MM-DDTHH:MM:SS format

    @respx.mock
    def test_get_as_prices_historical_passes_correct_params(
        self, sample_archive_listing_response, create_mock_zip_response
    ):
        """Test get_as_prices (historical) passes correct archive parameters."""
        listing_route = respx.get(
            f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np4-188-cd"
        ).mock(return_value=httpx.Response(200, json=sample_archive_listing_response))

        respx.post(f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np4-188-cd/download").mock(
            return_value=httpx.Response(200, content=create_mock_zip_response())
        )

        ercot = ERCOT()
        old_date = pd.Timestamp.now(tz="US/Central") - pd.Timedelta(days=100)
        ercot.get_as_prices(start=old_date, end=old_date + pd.Timedelta(days=1))

        assert listing_route.called
        listing_request = listing_route.calls.last.request
        assert "postDatetimeFrom" in listing_request.url.params
        assert "postDatetimeTo" in listing_request.url.params
        # Verify datetime format (YYYY-MM-DDTHH:MM:SS)
        post_datetime_from = listing_request.url.params["postDatetimeFrom"]
        assert "T" in post_datetime_from
        assert len(post_datetime_from) == 19  # YYYY-MM-DDTHH:MM:SS format

    @respx.mock
    def test_get_as_plan_historical_passes_correct_params(
        self, sample_archive_listing_response, create_mock_zip_response
    ):
        """Test get_as_plan (historical) passes correct archive parameters."""
        listing_route = respx.get(
            f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np4-33-cd"
        ).mock(return_value=httpx.Response(200, json=sample_archive_listing_response))

        respx.post(f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np4-33-cd/download").mock(
            return_value=httpx.Response(200, content=create_mock_zip_response())
        )

        ercot = ERCOT()
        old_date = pd.Timestamp.now(tz="US/Central") - pd.Timedelta(days=100)
        ercot.get_as_plan(start=old_date, end=old_date + pd.Timedelta(days=1))

        assert listing_route.called
        listing_request = listing_route.calls.last.request
        assert "postDatetimeFrom" in listing_request.url.params
        assert "postDatetimeTo" in listing_request.url.params
        # Verify datetime format (YYYY-MM-DDTHH:MM:SS)
        post_datetime_from = listing_request.url.params["postDatetimeFrom"]
        assert "T" in post_datetime_from
        assert len(post_datetime_from) == 19  # YYYY-MM-DDTHH:MM:SS format
