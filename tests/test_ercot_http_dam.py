"""Tests for ERCOT SDK Day-Ahead Market (DAM) HTTP requests.

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
def sample_dam_response():
    """Standard DAM response structure."""
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
            {"name": "settlementPoint", "label": "Settlement Point"},
            {"name": "settlementPointPrice", "label": "Settlement Point Price"},
        ],
        "data": {
            "records": [
                ["2024-01-01", "1", "LZ_HOUSTON", 45.50],
            ]
        },
    }


class TestDAMPricingHTTPRequests:
    """Test HTTP requests for DAM Pricing endpoints."""

    @respx.mock
    def test_get_dam_hourly_lmp_dispatches_correct_url(self, sample_dam_response):
        """Test get_dam_hourly_lmp calls correct endpoint."""
        route = respx.get(f"{ERCOT_API_BASE_URL}/np4-183-cd/dam_hourly_lmp").mock(
            return_value=httpx.Response(200, json=sample_dam_response)
        )

        ercot = ERCOT()
        ercot.get_dam_hourly_lmp(
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert route.called
        request = route.calls.last.request
        assert "/np4-183-cd/dam_hourly_lmp" in request.url.path

    @respx.mock
    def test_get_dam_hourly_lmp_passes_date_params(self, sample_dam_response):
        """Test get_dam_hourly_lmp passes date parameters correctly."""
        route = respx.get(f"{ERCOT_API_BASE_URL}/np4-183-cd/dam_hourly_lmp").mock(
            return_value=httpx.Response(200, json=sample_dam_response)
        )

        ercot = ERCOT()
        ercot.get_dam_hourly_lmp(
            start_date="2024-01-01",
            end_date="2024-01-07",
        )

        assert route.called
        request = route.calls.last.request
        query_str = str(request.url)
        assert "deliveryDateFrom=2024-01-01" in query_str
        assert "deliveryDateTo=2024-01-07" in query_str

    @respx.mock
    def test_get_dam_clear_price_for_cap_dispatches_correct_url(
        self, sample_dam_response
    ):
        """Test get_dam_clear_price_for_cap calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np4-188-cd/dam_clear_price_for_cap"
        ).mock(return_value=httpx.Response(200, json=sample_dam_response))

        ercot = ERCOT()
        ercot.get_dam_clear_price_for_cap()

        assert route.called
        request = route.calls.last.request
        assert "/np4-188-cd/dam_clear_price_for_cap" in request.url.path

    @respx.mock
    def test_get_dam_settlement_point_prices_dispatches_correct_url(
        self, sample_dam_response
    ):
        """Test get_dam_settlement_point_prices calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np4-190-cd/dam_stlmnt_pnt_prices"
        ).mock(return_value=httpx.Response(200, json=sample_dam_response))

        ercot = ERCOT()
        ercot.get_dam_settlement_point_prices()

        assert route.called
        request = route.calls.last.request
        assert "/np4-190-cd/dam_stlmnt_pnt_prices" in request.url.path

    @respx.mock
    def test_get_dam_shadow_prices_dispatches_correct_url(self, sample_dam_response):
        """Test get_dam_shadow_prices calls correct endpoint."""
        route = respx.get(f"{ERCOT_API_BASE_URL}/np4-191-cd/dam_shadow_prices").mock(
            return_value=httpx.Response(200, json=sample_dam_response)
        )

        ercot = ERCOT()
        ercot.get_dam_shadow_prices()

        assert route.called
        request = route.calls.last.request
        assert "/np4-191-cd/dam_shadow_prices" in request.url.path

    @respx.mock
    def test_get_dam_as_plan_dispatches_correct_url(self, sample_dam_response):
        """Test get_dam_as_plan calls correct endpoint."""
        route = respx.get(f"{ERCOT_API_BASE_URL}/np4-33-cd/dam_as_plan").mock(
            return_value=httpx.Response(200, json=sample_dam_response)
        )

        ercot = ERCOT()
        ercot.get_dam_as_plan()

        assert route.called
        request = route.calls.last.request
        assert "/np4-33-cd/dam_as_plan" in request.url.path

    @respx.mock
    def test_get_dam_system_lambda_dispatches_correct_url(self, sample_dam_response):
        """Test get_dam_system_lambda calls correct endpoint."""
        route = respx.get(f"{ERCOT_API_BASE_URL}/np4-523-cd/dam_system_lambda").mock(
            return_value=httpx.Response(200, json=sample_dam_response)
        )

        ercot = ERCOT()
        ercot.get_dam_system_lambda()

        assert route.called
        request = route.calls.last.request
        assert "/np4-523-cd/dam_system_lambda" in request.url.path


class TestDAMLoadDistributionHTTPRequests:
    """Test HTTP requests for Load Distribution and AS Service endpoints."""

    @respx.mock
    def test_get_load_distribution_factors_dispatches_correct_url(
        self, sample_dam_response
    ):
        """Test get_load_distribution_factors calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np4-159-cd/load_distribution_factors"
        ).mock(return_value=httpx.Response(200, json=sample_dam_response))

        ercot = ERCOT()
        ercot.get_load_distribution_factors()

        assert route.called
        request = route.calls.last.request
        assert "/np4-159-cd/load_distribution_factors" in request.url.path

    @respx.mock
    def test_get_total_as_service_offers_dispatches_correct_url(
        self, sample_dam_response
    ):
        """Test get_total_as_service_offers calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np4-179-cd/total_as_service_offers"
        ).mock(return_value=httpx.Response(200, json=sample_dam_response))

        ercot = ERCOT()
        ercot.get_total_as_service_offers()

        assert route.called
        request = route.calls.last.request
        assert "/np4-179-cd/total_as_service_offers" in request.url.path


class TestDAMPriceCorrectionsHTTPRequests:
    """Test HTTP requests for DAM Price Corrections endpoints."""

    @respx.mock
    def test_get_dam_price_corrections_eblmp_dispatches_correct_url(
        self, sample_dam_response
    ):
        """Test get_dam_price_corrections_eblmp calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np4-196-m/dam_price_corrections_eblmp"
        ).mock(return_value=httpx.Response(200, json=sample_dam_response))

        ercot = ERCOT()
        ercot.get_dam_price_corrections_eblmp()

        assert route.called
        request = route.calls.last.request
        assert "/np4-196-m/dam_price_corrections_eblmp" in request.url.path

    @respx.mock
    def test_get_dam_price_corrections_mcpc_dispatches_correct_url(
        self, sample_dam_response
    ):
        """Test get_dam_price_corrections_mcpc calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np4-196-m/dam_price_corrections_mcpc"
        ).mock(return_value=httpx.Response(200, json=sample_dam_response))

        ercot = ERCOT()
        ercot.get_dam_price_corrections_mcpc()

        assert route.called
        request = route.calls.last.request
        assert "/np4-196-m/dam_price_corrections_mcpc" in request.url.path

    @respx.mock
    def test_get_dam_price_corrections_spp_dispatches_correct_url(
        self, sample_dam_response
    ):
        """Test get_dam_price_corrections_spp calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np4-196-m/dam_price_corrections_spp"
        ).mock(return_value=httpx.Response(200, json=sample_dam_response))

        ercot = ERCOT()
        ercot.get_dam_price_corrections_spp()

        assert route.called
        request = route.calls.last.request
        assert "/np4-196-m/dam_price_corrections_spp" in request.url.path


class TestDAM60DayDisclosureHTTPRequests:
    """Test HTTP requests for 60-Day DAM Disclosure endpoints."""

    @respx.mock
    def test_get_dam_energy_bid_awards_dispatches_correct_url(
        self, sample_dam_response
    ):
        """Test get_dam_energy_bid_awards calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-966-er/60_dam_energy_bid_awards"
        ).mock(return_value=httpx.Response(200, json=sample_dam_response))

        ercot = ERCOT()
        ercot.get_dam_energy_bid_awards()

        assert route.called
        request = route.calls.last.request
        assert "/np3-966-er/60_dam_energy_bid_awards" in request.url.path

    @respx.mock
    def test_get_dam_energy_bids_dispatches_correct_url(self, sample_dam_response):
        """Test get_dam_energy_bids calls correct endpoint."""
        route = respx.get(f"{ERCOT_API_BASE_URL}/np3-966-er/60_dam_energy_bids").mock(
            return_value=httpx.Response(200, json=sample_dam_response)
        )

        ercot = ERCOT()
        ercot.get_dam_energy_bids()

        assert route.called
        request = route.calls.last.request
        assert "/np3-966-er/60_dam_energy_bids" in request.url.path

    @respx.mock
    def test_get_dam_energy_only_offer_awards_dispatches_correct_url(
        self, sample_dam_response
    ):
        """Test get_dam_energy_only_offer_awards calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-966-er/60_dam_energy_only_offer_awards"
        ).mock(return_value=httpx.Response(200, json=sample_dam_response))

        ercot = ERCOT()
        ercot.get_dam_energy_only_offer_awards()

        assert route.called
        request = route.calls.last.request
        assert "/np3-966-er/60_dam_energy_only_offer_awards" in request.url.path

    @respx.mock
    def test_get_dam_energy_only_offers_dispatches_correct_url(
        self, sample_dam_response
    ):
        """Test get_dam_energy_only_offers calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-966-er/60_dam_energy_only_offers"
        ).mock(return_value=httpx.Response(200, json=sample_dam_response))

        ercot = ERCOT()
        ercot.get_dam_energy_only_offers()

        assert route.called
        request = route.calls.last.request
        assert "/np3-966-er/60_dam_energy_only_offers" in request.url.path

    @respx.mock
    def test_get_dam_gen_res_as_offers_dispatches_correct_url(
        self, sample_dam_response
    ):
        """Test get_dam_gen_res_as_offers calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-966-er/60_dam_gen_res_as_offers"
        ).mock(return_value=httpx.Response(200, json=sample_dam_response))

        ercot = ERCOT()
        ercot.get_dam_gen_res_as_offers()

        assert route.called
        request = route.calls.last.request
        assert "/np3-966-er/60_dam_gen_res_as_offers" in request.url.path

    @respx.mock
    def test_get_dam_gen_res_data_dispatches_correct_url(self, sample_dam_response):
        """Test get_dam_gen_res_data calls correct endpoint."""
        route = respx.get(f"{ERCOT_API_BASE_URL}/np3-966-er/60_dam_gen_res_data").mock(
            return_value=httpx.Response(200, json=sample_dam_response)
        )

        ercot = ERCOT()
        ercot.get_dam_gen_res_data()

        assert route.called
        request = route.calls.last.request
        assert "/np3-966-er/60_dam_gen_res_data" in request.url.path

    @respx.mock
    def test_get_dam_load_res_as_offers_dispatches_correct_url(
        self, sample_dam_response
    ):
        """Test get_dam_load_res_as_offers calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-966-er/60_dam_load_res_as_offers"
        ).mock(return_value=httpx.Response(200, json=sample_dam_response))

        ercot = ERCOT()
        ercot.get_dam_load_res_as_offers()

        assert route.called
        request = route.calls.last.request
        assert "/np3-966-er/60_dam_load_res_as_offers" in request.url.path

    @respx.mock
    def test_get_dam_load_res_data_dispatches_correct_url(self, sample_dam_response):
        """Test get_dam_load_res_data calls correct endpoint."""
        route = respx.get(f"{ERCOT_API_BASE_URL}/np3-966-er/60_dam_load_res_data").mock(
            return_value=httpx.Response(200, json=sample_dam_response)
        )

        ercot = ERCOT()
        ercot.get_dam_load_res_data()

        assert route.called
        request = route.calls.last.request
        assert "/np3-966-er/60_dam_load_res_data" in request.url.path

    @respx.mock
    def test_get_dam_ptp_obl_bid_awards_dispatches_correct_url(
        self, sample_dam_response
    ):
        """Test get_dam_ptp_obl_bid_awards calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-966-er/60_dam_ptp_obl_bid_awards"
        ).mock(return_value=httpx.Response(200, json=sample_dam_response))

        ercot = ERCOT()
        ercot.get_dam_ptp_obl_bid_awards()

        assert route.called
        request = route.calls.last.request
        assert "/np3-966-er/60_dam_ptp_obl_bid_awards" in request.url.path

    @respx.mock
    def test_get_dam_ptp_obl_bids_dispatches_correct_url(self, sample_dam_response):
        """Test get_dam_ptp_obl_bids calls correct endpoint."""
        route = respx.get(f"{ERCOT_API_BASE_URL}/np3-966-er/60_dam_ptp_obl_bids").mock(
            return_value=httpx.Response(200, json=sample_dam_response)
        )

        ercot = ERCOT()
        ercot.get_dam_ptp_obl_bids()

        assert route.called
        request = route.calls.last.request
        assert "/np3-966-er/60_dam_ptp_obl_bids" in request.url.path

    @respx.mock
    def test_get_dam_ptp_obl_opt_dispatches_correct_url(self, sample_dam_response):
        """Test get_dam_ptp_obl_opt calls correct endpoint."""
        route = respx.get(f"{ERCOT_API_BASE_URL}/np3-966-er/60_dam_ptp_obl_opt").mock(
            return_value=httpx.Response(200, json=sample_dam_response)
        )

        ercot = ERCOT()
        ercot.get_dam_ptp_obl_opt()

        assert route.called
        request = route.calls.last.request
        assert "/np3-966-er/60_dam_ptp_obl_opt" in request.url.path

    @respx.mock
    def test_get_dam_ptp_obl_opt_awards_dispatches_correct_url(
        self, sample_dam_response
    ):
        """Test get_dam_ptp_obl_opt_awards calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-966-er/60_dam_ptp_obl_opt_awards"
        ).mock(return_value=httpx.Response(200, json=sample_dam_response))

        ercot = ERCOT()
        ercot.get_dam_ptp_obl_opt_awards()

        assert route.called
        request = route.calls.last.request
        assert "/np3-966-er/60_dam_ptp_obl_opt_awards" in request.url.path

    @respx.mock
    def test_get_dam_qse_self_as_dispatches_correct_url(self, sample_dam_response):
        """Test get_dam_qse_self_as calls correct endpoint."""
        route = respx.get(f"{ERCOT_API_BASE_URL}/np3-966-er/60_dam_qse_self_as").mock(
            return_value=httpx.Response(200, json=sample_dam_response)
        )

        ercot = ERCOT()
        ercot.get_dam_qse_self_as()

        assert route.called
        request = route.calls.last.request
        assert "/np3-966-er/60_dam_qse_self_as" in request.url.path


class TestDAMAggregatedASOffersHTTPRequests:
    """Test HTTP requests for 2-Day Aggregated AS Offers endpoints."""

    @respx.mock
    def test_get_aggregated_as_offers_ecrsm_dispatches_correct_url(
        self, sample_dam_response
    ):
        """Test get_aggregated_as_offers_ecrsm calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-911-er/2d_agg_as_offers_ecrsm"
        ).mock(return_value=httpx.Response(200, json=sample_dam_response))

        ercot = ERCOT()
        ercot.get_aggregated_as_offers_ecrsm()

        assert route.called
        request = route.calls.last.request
        assert "/np3-911-er/2d_agg_as_offers_ecrsm" in request.url.path

    @respx.mock
    def test_get_aggregated_as_offers_ecrss_dispatches_correct_url(
        self, sample_dam_response
    ):
        """Test get_aggregated_as_offers_ecrss calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-911-er/2d_agg_as_offers_ecrss"
        ).mock(return_value=httpx.Response(200, json=sample_dam_response))

        ercot = ERCOT()
        ercot.get_aggregated_as_offers_ecrss()

        assert route.called
        request = route.calls.last.request
        assert "/np3-911-er/2d_agg_as_offers_ecrss" in request.url.path

    @respx.mock
    def test_get_aggregated_as_offers_regup_dispatches_correct_url(
        self, sample_dam_response
    ):
        """Test get_aggregated_as_offers_regup calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-911-er/2d_agg_as_offers_regup"
        ).mock(return_value=httpx.Response(200, json=sample_dam_response))

        ercot = ERCOT()
        ercot.get_aggregated_as_offers_regup()

        assert route.called
        request = route.calls.last.request
        assert "/np3-911-er/2d_agg_as_offers_regup" in request.url.path

    @respx.mock
    def test_get_aggregated_as_offers_regdn_dispatches_correct_url(
        self, sample_dam_response
    ):
        """Test get_aggregated_as_offers_regdn calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-911-er/2d_agg_as_offers_regdn"
        ).mock(return_value=httpx.Response(200, json=sample_dam_response))

        ercot = ERCOT()
        ercot.get_aggregated_as_offers_regdn()

        assert route.called
        request = route.calls.last.request
        assert "/np3-911-er/2d_agg_as_offers_regdn" in request.url.path


class TestDAMClearedASHTTPRequests:
    """Test HTTP requests for 2-Day Cleared DAM AS endpoints."""

    @respx.mock
    def test_get_cleared_dam_as_ecrsm_dispatches_correct_url(self, sample_dam_response):
        """Test get_cleared_dam_as_ecrsm calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-911-er/2d_cleared_dam_as_ecrsm"
        ).mock(return_value=httpx.Response(200, json=sample_dam_response))

        ercot = ERCOT()
        ercot.get_cleared_dam_as_ecrsm()

        assert route.called
        request = route.calls.last.request
        assert "/np3-911-er/2d_cleared_dam_as_ecrsm" in request.url.path

    @respx.mock
    def test_get_cleared_dam_as_regup_dispatches_correct_url(self, sample_dam_response):
        """Test get_cleared_dam_as_regup calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-911-er/2d_cleared_dam_as_regup"
        ).mock(return_value=httpx.Response(200, json=sample_dam_response))

        ercot = ERCOT()
        ercot.get_cleared_dam_as_regup()

        assert route.called
        request = route.calls.last.request
        assert "/np3-911-er/2d_cleared_dam_as_regup" in request.url.path

    @respx.mock
    def test_get_cleared_dam_as_nspin_dispatches_correct_url(self, sample_dam_response):
        """Test get_cleared_dam_as_nspin calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-911-er/2d_cleared_dam_as_nspin"
        ).mock(return_value=httpx.Response(200, json=sample_dam_response))

        ercot = ERCOT()
        ercot.get_cleared_dam_as_nspin()

        assert route.called
        request = route.calls.last.request
        assert "/np3-911-er/2d_cleared_dam_as_nspin" in request.url.path


class TestDAMSelfArrangedASHTTPRequests:
    """Test HTTP requests for 2-Day Self-Arranged AS endpoints."""

    @respx.mock
    def test_get_self_arranged_as_ecrsm_dispatches_correct_url(
        self, sample_dam_response
    ):
        """Test get_self_arranged_as_ecrsm calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-911-er/2d_self_arranged_as_ecrsm"
        ).mock(return_value=httpx.Response(200, json=sample_dam_response))

        ercot = ERCOT()
        ercot.get_self_arranged_as_ecrsm()

        assert route.called
        request = route.calls.last.request
        assert "/np3-911-er/2d_self_arranged_as_ecrsm" in request.url.path

    @respx.mock
    def test_get_self_arranged_as_regup_dispatches_correct_url(
        self, sample_dam_response
    ):
        """Test get_self_arranged_as_regup calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-911-er/2d_self_arranged_as_regup"
        ).mock(return_value=httpx.Response(200, json=sample_dam_response))

        ercot = ERCOT()
        ercot.get_self_arranged_as_regup()

        assert route.called
        request = route.calls.last.request
        assert "/np3-911-er/2d_self_arranged_as_regup" in request.url.path

    @respx.mock
    def test_get_self_arranged_as_nspin_dispatches_correct_url(
        self, sample_dam_response
    ):
        """Test get_self_arranged_as_nspin calls correct endpoint."""
        route = respx.get(
            f"{ERCOT_API_BASE_URL}/np3-911-er/2d_self_arranged_as_nspin"
        ).mock(return_value=httpx.Response(200, json=sample_dam_response))

        ercot = ERCOT()
        ercot.get_self_arranged_as_nspin()

        assert route.called
        request = route.calls.last.request
        assert "/np3-911-er/2d_self_arranged_as_nspin" in request.url.path


class TestDAMHTTPMethod:
    """Test that DAM endpoints use correct HTTP methods."""

    @respx.mock
    def test_dam_pricing_uses_get_method(self, sample_dam_response):
        """Test that DAM pricing endpoints use GET method."""
        route = respx.get(f"{ERCOT_API_BASE_URL}/np4-183-cd/dam_hourly_lmp").mock(
            return_value=httpx.Response(200, json=sample_dam_response)
        )

        ercot = ERCOT()
        ercot.get_dam_hourly_lmp(
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert route.called
        request = route.calls.last.request
        assert request.method == "GET"


class TestDAMPaginationParams:
    """Test that DAM endpoints include proper pagination parameters."""

    @respx.mock
    def test_dam_pricing_includes_pagination_params(self, sample_dam_response):
        """Test that DAM pricing includes page and size in request."""
        route = respx.get(f"{ERCOT_API_BASE_URL}/np4-183-cd/dam_hourly_lmp").mock(
            return_value=httpx.Response(200, json=sample_dam_response)
        )

        ercot = ERCOT(page_size=5000)
        ercot.get_dam_hourly_lmp(
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert route.called
        request = route.calls.last.request
        query_str = str(request.url)
        assert "page=1" in query_str
        assert "size=5000" in query_str
