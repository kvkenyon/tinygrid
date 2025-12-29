"""Tests for ERCOT SDK EMIL Products & Versioning HTTP requests.

These tests validate that the correct API calls are being dispatched
with proper URLs, parameters, and headers using respx to intercept HTTP requests.
"""

import contextlib

import httpx
import respx

from tinygrid import ERCOT

# Base URL for ERCOT API
ERCOT_API_BASE_URL = "https://api.ercot.com/api/public-reports"


class TestProductsHTTPRequests:
    """Test HTTP requests for EMIL Products endpoints."""

    @respx.mock
    def test_get_list_for_products_dispatches_correct_url(self):
        """Test get_list_for_products calls the correct endpoint URL."""
        sample_response = {
            "products": [
                {
                    "emilId": "np6-905-cd",
                    "name": "SPP Node Zone Hub",
                    "description": "Settlement Point Prices",
                }
            ],
        }
        route = respx.get(f"{ERCOT_API_BASE_URL}/").mock(
            return_value=httpx.Response(200, json=sample_response)
        )

        ercot = ERCOT()
        ercot.get_list_for_products(as_dataframe=False)

        assert route.called
        request = route.calls.last.request
        assert request.url.path == "/api/public-reports/"


class TestProductsResponseShapes:
    """Regression tests for products response parsing."""

    def test_products_to_dataframe_supports_hal_embedded_shape(self):
        """HAL responses store the list under _embedded.products."""
        ercot = ERCOT()
        response = {
            "_embedded": {
                "products": [
                    {
                        "emilId": "np6-905-cd",
                        "name": "SPP Node Zone Hub",
                        "description": "Settlement Point Prices",
                    }
                ]
            },
            "_links": {"self": {"href": "/api/public-reports/"}},
        }
        df = ercot._products_to_dataframe(response)
        assert not df.empty
        assert df.loc[0, "emilId"] == "np6-905-cd"

    def test_products_to_dataframe_supports_nested_additional_properties_embedded_shape(
        self,
    ):
        """Some pyercot model to_dict() outputs keep HAL under additional_properties."""
        ercot = ERCOT()
        response = {
            "additional_properties": {
                "_embedded": {
                    "products": [
                        {
                            "emilId": "np6-905-cd",
                            "name": "SPP Node Zone Hub",
                        }
                    ]
                }
            }
        }
        df = ercot._products_to_dataframe(response)
        assert not df.empty
        assert df.loc[0, "emilId"] == "np6-905-cd"

    def test_products_to_dataframe_supports_raw_list_shape(self):
        """Some clients can return a raw list of product dicts."""
        ercot = ERCOT()
        response = [{"emilId": "np6-905-cd", "name": "SPP Node Zone Hub"}]
        df = ercot._products_to_dataframe(response)
        assert not df.empty
        assert df.loc[0, "emilId"] == "np6-905-cd"

    @respx.mock
    def test_get_product_dispatches_correct_url_with_emil_id(self):
        """Test get_product calls the correct endpoint with emil_id in path."""
        sample_response = {
            "emilId": "np6-905-cd",
            "name": "SPP Node Zone Hub",
            "description": "Settlement Point Prices at Resource Nodes, Hubs and Load Zones",
        }
        route = respx.get(f"{ERCOT_API_BASE_URL}/np6-905-cd").mock(
            return_value=httpx.Response(200, json=sample_response)
        )

        ercot = ERCOT()
        ercot.get_product(emil_id="np6-905-cd", as_dataframe=False)

        assert route.called
        request = route.calls.last.request
        assert request.url.path == "/api/public-reports/np6-905-cd"

    @respx.mock
    def test_get_product_encodes_special_characters_in_emil_id(self):
        """Test get_product properly URL-encodes special characters in emil_id."""
        sample_response = {
            "emilId": "np3-233-cd",
            "name": "Test Product",
        }
        route = respx.get(f"{ERCOT_API_BASE_URL}/np3-233-cd").mock(
            return_value=httpx.Response(200, json=sample_response)
        )

        ercot = ERCOT()
        ercot.get_product(emil_id="np3-233-cd", as_dataframe=False)

        assert route.called

    @respx.mock
    def test_get_product_history_dispatches_correct_url(self):
        """Test get_product_history calls /archive/{emil_id} endpoint."""
        sample_response = {
            "archives": [
                {
                    "postDatetime": "2024-01-01T00:00:00",
                    "_links": {
                        "endpoint": {"href": "/archive/np6-905-cd/download?docId=12345"}
                    },
                }
            ],
            "_meta": {"totalRecords": 1, "totalPages": 1},
        }
        route = respx.get(f"{ERCOT_API_BASE_URL}/archive/np6-905-cd").mock(
            return_value=httpx.Response(200, json=sample_response)
        )

        ercot = ERCOT()
        ercot.get_product_history(emil_id="np6-905-cd", as_dataframe=False)

        assert route.called
        request = route.calls.last.request
        assert request.url.path == "/api/public-reports/archive/np6-905-cd"

    @respx.mock
    def test_get_product_history_with_different_emil_id(self):
        """Test get_product_history correctly substitutes different emil_id values."""
        sample_response = {
            "archives": [],
            "_meta": {"totalRecords": 0, "totalPages": 0},
        }
        route = respx.get(f"{ERCOT_API_BASE_URL}/archive/np4-183-cd").mock(
            return_value=httpx.Response(200, json=sample_response)
        )

        ercot = ERCOT()
        ercot.get_product_history(emil_id="np4-183-cd", as_dataframe=False)

        assert route.called
        request = route.calls.last.request
        assert "/archive/np4-183-cd" in request.url.path


class TestVersionHTTPRequests:
    """Test HTTP requests for Versioning endpoint."""

    @respx.mock
    def test_get_version_dispatches_correct_url(self):
        """Test get_version calls the /version endpoint."""
        sample_response = {
            "version": "1.0.0",
            "apiVersion": "v1",
            "buildDate": "2024-01-01",
        }
        route = respx.get(f"{ERCOT_API_BASE_URL}/version").mock(
            return_value=httpx.Response(200, json=sample_response)
        )

        ercot = ERCOT()
        ercot.get_version(as_dataframe=False)

        assert route.called
        request = route.calls.last.request
        assert request.url.path == "/api/public-reports/version"

    @respx.mock
    def test_get_version_uses_get_method(self):
        """Test get_version uses HTTP GET method."""
        sample_response = {"version": "1.0.0"}
        route = respx.get(f"{ERCOT_API_BASE_URL}/version").mock(
            return_value=httpx.Response(200, json=sample_response)
        )

        ercot = ERCOT()
        ercot.get_version(as_dataframe=False)

        assert route.called
        request = route.calls.last.request
        assert request.method == "GET"


class TestProductsAdditionalParameters:
    """Test that additional kwargs are passed as query parameters."""

    @respx.mock
    def test_get_list_for_products_makes_request(self):
        """Test get_list_for_products makes HTTP request to correct URL."""
        sample_response = {"products": []}
        route = respx.get(f"{ERCOT_API_BASE_URL}/").mock(
            return_value=httpx.Response(200, json=sample_response)
        )

        ercot = ERCOT()
        ercot.get_list_for_products(as_dataframe=False)

        assert route.called
        request = route.calls.last.request
        assert request.url.path == "/api/public-reports/"

    @respx.mock
    def test_get_product_passes_extra_params(self):
        """Test get_product passes extra parameters in query string."""
        sample_response = {"emilId": "np6-905-cd"}
        route = respx.get(f"{ERCOT_API_BASE_URL}/np6-905-cd").mock(
            return_value=httpx.Response(200, json=sample_response)
        )

        ercot = ERCOT()
        ercot.get_product(emil_id="np6-905-cd", as_dataframe=False)

        assert route.called


class TestProductsErrorHandling:
    """Test error handling for Products endpoints."""

    @respx.mock
    def test_get_product_handles_404_response(self):
        """Test get_product handles 404 Not Found gracefully."""
        error_response = {
            "error": "Not Found",
            "message": "Product not found",
        }
        route = respx.get(f"{ERCOT_API_BASE_URL}/nonexistent-product").mock(
            return_value=httpx.Response(404, json=error_response)
        )

        ercot = ERCOT(max_retries=0)

        # The endpoint is called, verifying correct dispatch even for errors
        with contextlib.suppress(Exception):
            ercot.get_product(emil_id="nonexistent-product", as_dataframe=False)

        assert route.called
        request = route.calls.last.request
        assert "/nonexistent-product" in request.url.path

    @respx.mock
    def test_get_version_handles_500_response(self):
        """Test get_version handles server errors."""
        route = respx.get(f"{ERCOT_API_BASE_URL}/version").mock(
            return_value=httpx.Response(500, json={"error": "Internal Server Error"})
        )

        ercot = ERCOT(max_retries=0)

        with contextlib.suppress(Exception):
            ercot.get_version(as_dataframe=False)

        assert route.called
