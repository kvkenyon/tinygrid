"""Tests for ERCOT SDK Real-Time Market (RTM) HTTP requests.

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
def sample_rtm_response():
    """Standard RTM response structure."""
    return {
        "_meta": {
            "totalRecords": 1,
            "pageSize": 10000,
            "totalPages": 1,
            "currentPage": 1,
        },
        "fields": [
            {"name": "SCEDTimestamp", "label": "SCED Time Stamp"},
            {"name": "settlementPoint", "label": "Settlement Point"},
            {"name": "LMP", "label": "LMP"},
        ],
        "data": {
            "records": [
                ["2024-01-01T08:00:00", "LZ_HOUSTON", 45.50],
            ]
        },
    }


class TestRTMPricingHTTPRequests:
    """Test HTTP requests for RTM Pricing endpoints."""

    @respx.mock
    def test_get_spp_node_zone_hub_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_spp_node_zone_hub calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np6-905-cd/spp_node_zone_hub"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_spp_node_zone_hub()

        assert route.called
        request = route.calls.last.request
        assert "/np6-905-cd/spp_node_zone_hub" in request.url.path

    @respx.mock
    def test_get_spp_node_zone_hub_passes_date_params(
        self, sample_rtm_response
    ):
        """Test get_spp_node_zone_hub passes date parameters correctly."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np6-905-cd/spp_node_zone_hub"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_spp_node_zone_hub(
            delivery_date_from="2024-01-01",
            delivery_date_to="2024-01-02",
        )

        assert route.called
        request = route.calls.last.request
        query_str = str(request.url)
        assert "deliveryDateFrom=2024-01-01" in query_str
        assert "deliveryDateTo=2024-01-02" in query_str

    @respx.mock
    def test_get_spp_node_zone_hub_passes_settlement_point(
        self, sample_rtm_response
    ):
        """Test get_spp_node_zone_hub passes settlement_point parameter."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np6-905-cd/spp_node_zone_hub"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_spp_node_zone_hub(settlement_point="LZ_HOUSTON")

        assert route.called
        request = route.calls.last.request
        query_str = str(request.url)
        assert "settlementPoint=LZ_HOUSTON" in query_str

    @respx.mock
    def test_get_lmp_node_zone_hub_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_lmp_node_zone_hub calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np6-788-cd/lmp_node_zone_hub"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_lmp_node_zone_hub()

        assert route.called
        request = route.calls.last.request
        assert "/np6-788-cd/lmp_node_zone_hub" in request.url.path

    @respx.mock
    def test_get_lmp_electrical_bus_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_lmp_electrical_bus calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np6-787-cd/lmp_electrical_bus"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_lmp_electrical_bus()

        assert route.called
        request = route.calls.last.request
        assert "/np6-787-cd/lmp_electrical_bus" in request.url.path

    @respx.mock
    def test_get_sced_system_lambda_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_sced_system_lambda calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np6-322-cd/sced_system_lambda"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_sced_system_lambda()

        assert route.called
        request = route.calls.last.request
        assert "/np6-322-cd/sced_system_lambda" in request.url.path

    @respx.mock
    def test_get_shadow_prices_bound_transmission_constraint_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_shadow_prices_bound_transmission_constraint calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np6-86-cd/shdw_prices_bnd_trns_const"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_shadow_prices_bound_transmission_constraint()

        assert route.called
        request = route.calls.last.request
        assert "/np6-86-cd/shdw_prices_bnd_trns_const" in request.url.path

    @respx.mock
    def test_get_rtd_lmp_node_zone_hub_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_rtd_lmp_node_zone_hub calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np6-970-cd/rtd_lmp_node_zone_hub"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_rtd_lmp_node_zone_hub()

        assert route.called
        request = route.calls.last.request
        assert "/np6-970-cd/rtd_lmp_node_zone_hub" in request.url.path


class TestRTMOperationsHTTPRequests:
    """Test HTTP requests for RTM Operations endpoints (2-day aggregate)."""

    @respx.mock
    def test_get_aggregated_dsr_loads_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_aggregated_dsr_loads calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-910-er/2d_agg_dsr_loads"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_aggregated_dsr_loads()

        assert route.called
        request = route.calls.last.request
        assert "/np3-910-er/2d_agg_dsr_loads" in request.url.path

    @respx.mock
    def test_get_aggregated_generation_summary_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_aggregated_generation_summary calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-910-er/2d_agg_gen_summary"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_aggregated_generation_summary()

        assert route.called
        request = route.calls.last.request
        assert "/np3-910-er/2d_agg_gen_summary" in request.url.path

    @respx.mock
    def test_get_aggregated_generation_summary_houston_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_aggregated_generation_summary_houston calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-910-er/2d_agg_gen_summary_houston"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_aggregated_generation_summary_houston()

        assert route.called
        request = route.calls.last.request
        assert "/np3-910-er/2d_agg_gen_summary_houston" in request.url.path

    @respx.mock
    def test_get_aggregated_load_summary_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_aggregated_load_summary calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-910-er/2d_agg_load_summary"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_aggregated_load_summary()

        assert route.called
        request = route.calls.last.request
        assert "/np3-910-er/2d_agg_load_summary" in request.url.path

    @respx.mock
    def test_get_aggregated_outage_schedule_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_aggregated_outage_schedule calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-910-er/2d_agg_out_sched"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_aggregated_outage_schedule()

        assert route.called
        request = route.calls.last.request
        assert "/np3-910-er/2d_agg_out_sched" in request.url.path


class TestRTM60DaySCEDDisclosureHTTPRequests:
    """Test HTTP requests for 60-Day SCED Disclosure endpoints."""

    @respx.mock
    def test_get_sced_dsr_load_data_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_sced_dsr_load_data calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-965-er/60_sced_dsr_load_data"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_sced_dsr_load_data()

        assert route.called
        request = route.calls.last.request
        assert "/np3-965-er/60_sced_dsr_load_data" in request.url.path

    @respx.mock
    def test_get_sced_gen_res_data_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_sced_gen_res_data calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-965-er/60_sced_gen_res_data"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_sced_gen_res_data()

        assert route.called
        request = route.calls.last.request
        assert "/np3-965-er/60_sced_gen_res_data" in request.url.path

    @respx.mock
    def test_get_sced_smne_gen_res_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_sced_smne_gen_res calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-965-er/60_sced_smne_gen_res"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_sced_smne_gen_res()

        assert route.called
        request = route.calls.last.request
        assert "/np3-965-er/60_sced_smne_gen_res" in request.url.path

    @respx.mock
    def test_get_load_res_data_in_sced_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_load_res_data_in_sced calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-965-er/60_load_res_data_in_sced"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_load_res_data_in_sced()

        assert route.called
        request = route.calls.last.request
        assert "/np3-965-er/60_load_res_data_in_sced" in request.url.path

    @respx.mock
    def test_get_hdl_ldl_manual_override_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_hdl_ldl_manual_override calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-965-er/60_hdl_ldl_man_override"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_hdl_ldl_manual_override()

        assert route.called
        request = route.calls.last.request
        assert "/np3-965-er/60_hdl_ldl_man_override" in request.url.path

    @respx.mock
    def test_get_sced_qse_self_arranged_as_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_sced_qse_self_arranged_as calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-965-er/60_sced_qse_self_arranged_as"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_sced_qse_self_arranged_as()

        assert route.called
        request = route.calls.last.request
        assert "/np3-965-er/60_sced_qse_self_arranged_as" in request.url.path


class TestRTMSASMHTTPRequests:
    """Test HTTP requests for SASM (Supplemental Ancillary Services Market) endpoints."""

    @respx.mock
    def test_get_sasm_gen_res_as_offers_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_sasm_gen_res_as_offers calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-990-ex/60_sasm_gen_res_as_offers"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_sasm_gen_res_as_offers()

        assert route.called
        request = route.calls.last.request
        assert "/np3-990-ex/60_sasm_gen_res_as_offers" in request.url.path

    @respx.mock
    def test_get_sasm_gen_res_as_offer_awards_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_sasm_gen_res_as_offer_awards calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-990-ex/60_sasm_gen_res_as_offer_awards"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_sasm_gen_res_as_offer_awards()

        assert route.called
        request = route.calls.last.request
        assert "/np3-990-ex/60_sasm_gen_res_as_offer_awards" in request.url.path

    @respx.mock
    def test_get_sasm_load_res_as_offers_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_sasm_load_res_as_offers calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-990-ex/60_sasm_load_res_as_offers"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_sasm_load_res_as_offers()

        assert route.called
        request = route.calls.last.request
        assert "/np3-990-ex/60_sasm_load_res_as_offers" in request.url.path

    @respx.mock
    def test_get_sasm_load_res_as_offer_awards_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_sasm_load_res_as_offer_awards calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-990-ex/60_sasm_load_res_as_offer_awards"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_sasm_load_res_as_offer_awards()

        assert route.called
        request = route.calls.last.request
        assert (
            "/np3-990-ex/60_sasm_load_res_as_offer_awards" in request.url.path
        )


class TestRTMPriceCorrectionsHTTPRequests:
    """Test HTTP requests for RTM Price Corrections endpoints."""

    @respx.mock
    def test_get_rtm_price_corrections_eblmp_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_rtm_price_corrections_eblmp calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np4-197-m/rtm_price_corrections_eblmp"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_rtm_price_corrections_eblmp()

        assert route.called
        request = route.calls.last.request
        assert "/np4-197-m/rtm_price_corrections_eblmp" in request.url.path

    @respx.mock
    def test_get_rtm_price_corrections_spp_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_rtm_price_corrections_spp calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np4-197-m/rtm_price_corrections_spp"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_rtm_price_corrections_spp()

        assert route.called
        request = route.calls.last.request
        assert "/np4-197-m/rtm_price_corrections_spp" in request.url.path

    @respx.mock
    def test_get_rtm_price_corrections_shadow_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_rtm_price_corrections_shadow calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np4-197-m/rtm_price_corrections_shadow"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_rtm_price_corrections_shadow()

        assert route.called
        request = route.calls.last.request
        assert "/np4-197-m/rtm_price_corrections_shadow" in request.url.path

    @respx.mock
    def test_get_rtm_price_corrections_soglmp_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_rtm_price_corrections_soglmp calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np4-197-m/rtm_price_corrections_soglmp"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_rtm_price_corrections_soglmp()

        assert route.called
        request = route.calls.last.request
        assert "/np4-197-m/rtm_price_corrections_soglmp" in request.url.path

    @respx.mock
    def test_get_rtm_price_corrections_sogprice_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_rtm_price_corrections_sogprice calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np4-197-m/rtm_price_corrections_sogprice"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_rtm_price_corrections_sogprice()

        assert route.called
        request = route.calls.last.request
        assert "/np4-197-m/rtm_price_corrections_sogprice" in request.url.path

    @respx.mock
    def test_get_rtm_price_corrections_splmp_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_rtm_price_corrections_splmp calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np4-197-m/rtm_price_corrections_splmp"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_rtm_price_corrections_splmp()

        assert route.called
        request = route.calls.last.request
        assert "/np4-197-m/rtm_price_corrections_splmp" in request.url.path


class TestRTMOutageCapacityHTTPRequests:
    """Test HTTP requests for Outage Capacity endpoints."""

    @respx.mock
    def test_get_hourly_res_outage_cap_dispatches_correct_url(
        self, sample_rtm_response
    ):
        """Test get_hourly_res_outage_cap calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-233-cd/hourly_res_outage_cap"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_hourly_res_outage_cap()

        assert route.called
        request = route.calls.last.request
        assert "/np3-233-cd/hourly_res_outage_cap" in request.url.path


class TestRTMHTTPMethod:
    """Test that RTM endpoints use correct HTTP methods."""

    @respx.mock
    def test_rtm_pricing_uses_get_method(self, sample_rtm_response):
        """Test that RTM pricing endpoints use GET method."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np6-905-cd/spp_node_zone_hub"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT()
        ercot.get_spp_node_zone_hub()

        assert route.called
        request = route.calls.last.request
        assert request.method == "GET"


class TestRTMPaginationParams:
    """Test that RTM endpoints include proper pagination parameters."""

    @respx.mock
    def test_rtm_pricing_includes_pagination_params(self, sample_rtm_response):
        """Test that RTM pricing includes page and size in request."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np6-905-cd/spp_node_zone_hub"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT(page_size=5000)
        ercot.get_spp_node_zone_hub()

        assert route.called
        request = route.calls.last.request
        query_str = str(request.url)
        assert "page=1" in query_str
        assert "size=5000" in query_str

    @respx.mock
    def test_lmp_includes_custom_page_size(self, sample_rtm_response):
        """Test that LMP endpoints respect custom page size."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np6-787-cd/lmp_electrical_bus"
        ).mock(return_value=httpx.Response(200, json=sample_rtm_response))

        ercot = ERCOT(page_size=2500)
        ercot.get_lmp_electrical_bus()

        assert route.called
        request = route.calls.last.request
        query_str = str(request.url)
        assert "size=2500" in query_str
