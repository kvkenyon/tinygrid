"""Tests for ERCOT SDK Historical Archive HTTP requests.

These tests validate that the correct API calls are being dispatched
with proper URLs, parameters, and headers using respx to intercept HTTP requests
for the ERCOTArchive historical data access.
"""

import io
import json
from unittest.mock import MagicMock
from zipfile import ZipFile

import httpx
import pandas as pd
import pytest
import respx

from tinygrid import ERCOT, GridError
from tinygrid.ercot.archive import ERCOTArchive
from tinygrid.errors import GridRetryExhaustedError

# Base URL for ERCOT Public API (used by historical endpoints)
ERCOT_PUBLIC_API_BASE_URL = "https://api.ercot.com/api/public-reports"


@pytest.fixture
def mock_ercot_client():
    """Create a mock ERCOT client with no auth for testing."""
    client = ERCOT()
    client.auth = None
    return client


@pytest.fixture
def sample_archive_listing_response():
    """Sample archive listing response."""
    return {
        "_meta": {
            "totalRecords": 2,
            "totalPages": 1,
            "currentPage": 1,
        },
        "archives": [
            {
                "postDatetime": "2024-01-01T00:00:00",
                "_links": {
                    "endpoint": {"href": "/archive/np6-905-cd/download?docId=12345"}
                },
            },
            {
                "postDatetime": "2024-01-02T00:00:00",
                "_links": {
                    "endpoint": {"href": "/archive/np6-905-cd/download?docId=12346"}
                },
            },
        ],
    }


@pytest.fixture
def sample_multi_page_archive_response():
    """Sample multi-page archive listing response (first page)."""
    return {
        "_meta": {
            "totalRecords": 2000,
            "totalPages": 2,
            "currentPage": 1,
        },
        "archives": [
            {
                "postDatetime": f"2024-01-{i:02d}T00:00:00",
                "_links": {
                    "endpoint": {
                        "href": f"/archive/np6-905-cd/download?docId={10000 + i}"
                    }
                },
            }
            for i in range(1, 11)
        ],
    }


def create_mock_zip_response():
    """Create a mock zip file response for bulk download."""
    # Create an outer zip containing inner zips
    outer_buffer = io.BytesIO()
    with ZipFile(outer_buffer, "w") as outer_zip:
        # Create inner zip for doc 12345
        inner_buffer1 = io.BytesIO()
        with ZipFile(inner_buffer1, "w") as inner_zip:
            csv_data = "col1,col2\nvalue1,value2\n"
            inner_zip.writestr("data.csv", csv_data)
        inner_buffer1.seek(0)
        outer_zip.writestr("12345.zip", inner_buffer1.getvalue())

        # Create inner zip for doc 12346
        inner_buffer2 = io.BytesIO()
        with ZipFile(inner_buffer2, "w") as inner_zip:
            csv_data = "col1,col2\nvalue3,value4\n"
            inner_zip.writestr("data.csv", csv_data)
        inner_buffer2.seek(0)
        outer_zip.writestr("12346.zip", inner_buffer2.getvalue())

    outer_buffer.seek(0)
    return outer_buffer.getvalue()


class TestArchiveLinksHTTPRequests:
    """Test HTTP requests for get_archive_links endpoint."""

    @respx.mock
    def test_get_archive_links_dispatches_correct_url(
        self, mock_ercot_client, sample_archive_listing_response
    ):
        """Test get_archive_links calls correct endpoint URL."""
        route = respx.get(f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np6-905-cd").mock(
            return_value=httpx.Response(200, json=sample_archive_listing_response)
        )

        archive = ERCOTArchive(client=mock_ercot_client)
        archive.get_archive_links(
            emil_id="np6-905-cd",
            start=pd.Timestamp("2024-01-01", tz="US/Central"),
            end=pd.Timestamp("2024-01-07", tz="US/Central"),
        )

        assert route.called
        request = route.calls.last.request
        assert "/archive/np6-905-cd" in str(request.url)

    @respx.mock
    def test_get_archive_links_passes_date_params(
        self, mock_ercot_client, sample_archive_listing_response
    ):
        """Test get_archive_links passes date parameters correctly."""
        route = respx.get(f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np6-905-cd").mock(
            return_value=httpx.Response(200, json=sample_archive_listing_response)
        )

        archive = ERCOTArchive(client=mock_ercot_client)
        archive.get_archive_links(
            emil_id="np6-905-cd",
            start=pd.Timestamp("2024-01-01", tz="US/Central"),
            end=pd.Timestamp("2024-01-07", tz="US/Central"),
        )

        assert route.called
        request = route.calls.last.request
        query_str = str(request.url)
        assert "postDatetimeFrom=" in query_str
        assert "postDatetimeTo=" in query_str

    @respx.mock
    def test_get_archive_links_includes_pagination_params(
        self, mock_ercot_client, sample_archive_listing_response
    ):
        """Test get_archive_links includes page and size parameters."""
        route = respx.get(f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np6-905-cd").mock(
            return_value=httpx.Response(200, json=sample_archive_listing_response)
        )

        archive = ERCOTArchive(client=mock_ercot_client)
        archive.get_archive_links(
            emil_id="np6-905-cd",
            start=pd.Timestamp("2024-01-01", tz="US/Central"),
            end=pd.Timestamp("2024-01-07", tz="US/Central"),
        )

        assert route.called
        request = route.calls.last.request
        query_str = str(request.url)
        assert "page=1" in query_str
        assert "size=1000" in query_str

    @respx.mock
    def test_get_archive_links_uses_get_method(
        self, mock_ercot_client, sample_archive_listing_response
    ):
        """Test get_archive_links uses HTTP GET method."""
        route = respx.get(f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np6-905-cd").mock(
            return_value=httpx.Response(200, json=sample_archive_listing_response)
        )

        archive = ERCOTArchive(client=mock_ercot_client)
        archive.get_archive_links(
            emil_id="np6-905-cd",
            start=pd.Timestamp("2024-01-01", tz="US/Central"),
            end=pd.Timestamp("2024-01-07", tz="US/Central"),
        )

        assert route.called
        request = route.calls.last.request
        assert request.method == "GET"

    @respx.mock
    def test_get_archive_links_handles_different_emil_ids(
        self, mock_ercot_client, sample_archive_listing_response
    ):
        """Test get_archive_links correctly substitutes different emil_id values."""
        route = respx.get(f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np4-183-cd").mock(
            return_value=httpx.Response(200, json=sample_archive_listing_response)
        )

        archive = ERCOTArchive(client=mock_ercot_client)
        archive.get_archive_links(
            emil_id="np4-183-cd",
            start=pd.Timestamp("2024-01-01", tz="US/Central"),
            end=pd.Timestamp("2024-01-07", tz="US/Central"),
        )

        assert route.called
        request = route.calls.last.request
        assert "/archive/np4-183-cd" in str(request.url)

    @respx.mock
    def test_get_archive_links_paginates_multi_page_response(
        self, mock_ercot_client, sample_multi_page_archive_response
    ):
        """Test get_archive_links fetches all pages when multiple pages exist."""
        # First page response
        page1_response = sample_multi_page_archive_response.copy()
        page1_response["_meta"]["currentPage"] = 1

        # Second page response
        page2_response = {
            "_meta": {
                "totalRecords": 2000,
                "totalPages": 2,
                "currentPage": 2,
            },
            "archives": [
                {
                    "postDatetime": f"2024-01-{i:02d}T00:00:00",
                    "_links": {
                        "endpoint": {
                            "href": f"/archive/np6-905-cd/download?docId={20000 + i}"
                        }
                    },
                }
                for i in range(1, 11)
            ],
        }

        # Set up routes for both pages
        route = respx.get(f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np6-905-cd").mock(
            side_effect=[
                httpx.Response(200, json=page1_response),
                httpx.Response(200, json=page2_response),
            ]
        )

        archive = ERCOTArchive(client=mock_ercot_client)
        links = archive.get_archive_links(
            emil_id="np6-905-cd",
            start=pd.Timestamp("2024-01-01", tz="US/Central"),
            end=pd.Timestamp("2024-01-31", tz="US/Central"),
        )

        # Should have made 2 requests (one for each page)
        assert route.call_count == 2
        # Should have collected links from both pages
        assert len(links) == 20


class TestBulkDownloadHTTPRequests:
    """Test HTTP requests for bulk_download endpoint."""

    @respx.mock
    def test_bulk_download_dispatches_correct_url(self, mock_ercot_client):
        """Test bulk_download calls correct endpoint URL."""
        mock_zip = create_mock_zip_response()
        route = respx.post(
            f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np6-905-cd/download"
        ).mock(return_value=httpx.Response(200, content=mock_zip))

        archive = ERCOTArchive(client=mock_ercot_client)
        archive.bulk_download(
            doc_ids=["12345", "12346"],
            emil_id="np6-905-cd",
        )

        assert route.called
        request = route.calls.last.request
        assert "/archive/np6-905-cd/download" in str(request.url)

    @respx.mock
    def test_bulk_download_uses_post_method(self, mock_ercot_client):
        """Test bulk_download uses HTTP POST method."""
        mock_zip = create_mock_zip_response()
        route = respx.post(
            f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np6-905-cd/download"
        ).mock(return_value=httpx.Response(200, content=mock_zip))

        archive = ERCOTArchive(client=mock_ercot_client)
        archive.bulk_download(
            doc_ids=["12345", "12346"],
            emil_id="np6-905-cd",
        )

        assert route.called
        request = route.calls.last.request
        assert request.method == "POST"

    @respx.mock
    def test_bulk_download_sends_doc_ids_in_body(self, mock_ercot_client):
        """Test bulk_download sends docIds in request body."""
        mock_zip = create_mock_zip_response()
        route = respx.post(
            f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np6-905-cd/download"
        ).mock(return_value=httpx.Response(200, content=mock_zip))

        archive = ERCOTArchive(client=mock_ercot_client)
        archive.bulk_download(
            doc_ids=["12345", "12346"],
            emil_id="np6-905-cd",
        )

        assert route.called
        request = route.calls.last.request
        # Parse the request body
        body = json.loads(request.content)
        assert "docIds" in body
        assert body["docIds"] == ["12345", "12346"]

    @respx.mock
    def test_bulk_download_batches_large_requests(self, mock_ercot_client):
        """Test bulk_download batches requests when doc_ids exceeds batch_size."""
        mock_zip = create_mock_zip_response()
        route = respx.post(
            f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np6-905-cd/download"
        ).mock(return_value=httpx.Response(200, content=mock_zip))

        # Create archive with small batch size for testing
        archive = ERCOTArchive(client=mock_ercot_client, batch_size=2)

        # Request 4 docs, should result in 2 batched requests
        archive.bulk_download(
            doc_ids=["12345", "12346", "12347", "12348"],
            emil_id="np6-905-cd",
        )

        # Should have made 2 POST requests (2 docs per batch)
        assert route.call_count == 2


class TestFetchHistoricalHTTPRequests:
    """Test HTTP requests for fetch_historical combined operation."""

    @respx.mock
    def test_fetch_historical_calls_archive_links_first(
        self, mock_ercot_client, sample_archive_listing_response
    ):
        """Test fetch_historical first calls get_archive_links."""
        mock_zip = create_mock_zip_response()

        # Mock archive listing
        archive_route = respx.get(
            f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np6-905-cd"
        ).mock(return_value=httpx.Response(200, json=sample_archive_listing_response))

        # Mock bulk download
        download_route = respx.post(
            f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np6-905-cd/download"
        ).mock(return_value=httpx.Response(200, content=mock_zip))

        archive = ERCOTArchive(client=mock_ercot_client)
        archive.fetch_historical(
            endpoint="/np6-905-cd/spp_node_zone_hub",
            start=pd.Timestamp("2024-01-01", tz="US/Central"),
            end=pd.Timestamp("2024-01-07", tz="US/Central"),
        )

        # Archive listing should be called first
        assert archive_route.called
        # Then bulk download should be called
        assert download_route.called

    @respx.mock
    def test_fetch_historical_extracts_emil_id_from_endpoint(
        self, mock_ercot_client, sample_archive_listing_response
    ):
        """Test fetch_historical extracts emil_id from endpoint path."""
        mock_zip = create_mock_zip_response()

        # Mock archive listing - should extract np6-905-cd from endpoint
        archive_route = respx.get(
            f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np6-905-cd"
        ).mock(return_value=httpx.Response(200, json=sample_archive_listing_response))

        respx.post(f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np6-905-cd/download").mock(
            return_value=httpx.Response(200, content=mock_zip)
        )

        archive = ERCOTArchive(client=mock_ercot_client)
        archive.fetch_historical(
            endpoint="/np6-905-cd/spp_node_zone_hub",  # Full endpoint path
            start=pd.Timestamp("2024-01-01", tz="US/Central"),
            end=pd.Timestamp("2024-01-07", tz="US/Central"),
        )

        # Should have extracted np6-905-cd and called that endpoint
        assert archive_route.called
        request = archive_route.calls.last.request
        assert "/archive/np6-905-cd" in str(request.url)


class TestHistoricalAuthHeaders:
    """Test authentication headers for historical endpoints."""

    @respx.mock
    def test_authenticated_request_includes_auth_headers(
        self, sample_archive_listing_response
    ):
        """Test that authenticated requests include proper headers."""
        # Create a client with mock auth
        client = ERCOT()
        client.auth = MagicMock()
        client.auth.get_token.return_value = "test-token-123"
        client.auth.get_subscription_key.return_value = "test-subscription-key"

        route = respx.get(f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np6-905-cd").mock(
            return_value=httpx.Response(200, json=sample_archive_listing_response)
        )

        archive = ERCOTArchive(client=client)
        archive.get_archive_links(
            emil_id="np6-905-cd",
            start=pd.Timestamp("2024-01-01", tz="US/Central"),
            end=pd.Timestamp("2024-01-07", tz="US/Central"),
        )

        assert route.called
        request = route.calls.last.request
        # Check auth headers are present
        assert "Authorization" in request.headers
        assert request.headers["Authorization"] == "Bearer test-token-123"
        assert "Ocp-Apim-Subscription-Key" in request.headers
        assert request.headers["Ocp-Apim-Subscription-Key"] == "test-subscription-key"

    @respx.mock
    def test_unauthenticated_request_has_no_auth_headers(
        self, mock_ercot_client, sample_archive_listing_response
    ):
        """Test that unauthenticated requests don't include auth headers."""
        route = respx.get(f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np6-905-cd").mock(
            return_value=httpx.Response(200, json=sample_archive_listing_response)
        )

        archive = ERCOTArchive(client=mock_ercot_client)
        archive.get_archive_links(
            emil_id="np6-905-cd",
            start=pd.Timestamp("2024-01-01", tz="US/Central"),
            end=pd.Timestamp("2024-01-07", tz="US/Central"),
        )

        assert route.called
        request = route.calls.last.request
        # Auth headers should not be present when auth is None
        assert "Authorization" not in request.headers


class TestHistoricalErrorHandling:
    """Test error handling for historical endpoints."""

    @respx.mock
    def test_get_archive_links_handles_404(self, mock_ercot_client):
        """Test get_archive_links handles 404 Not Found."""
        route = respx.get(f"{ERCOT_PUBLIC_API_BASE_URL}/archive/nonexistent-id").mock(
            return_value=httpx.Response(404, json={"error": "Not Found"})
        )

        archive = ERCOTArchive(client=mock_ercot_client)

        with pytest.raises(GridError):  # Should raise GridAPIError
            archive.get_archive_links(
                emil_id="nonexistent-id",
                start=pd.Timestamp("2024-01-01", tz="US/Central"),
                end=pd.Timestamp("2024-01-07", tz="US/Central"),
            )

        assert route.called

    @respx.mock
    def test_bulk_download_handles_rate_limit(self, mock_ercot_client):
        """Test bulk_download handles 429 Rate Limit."""
        route = respx.post(
            f"{ERCOT_PUBLIC_API_BASE_URL}/archive/np6-905-cd/download"
        ).mock(return_value=httpx.Response(429, json={"error": "Rate limited"}))

        archive = ERCOTArchive(client=mock_ercot_client)

        with pytest.raises(
            GridRetryExhaustedError
        ):  # Should raise GridRetryExhaustedError
            archive.bulk_download(
                doc_ids=["12345"],
                emil_id="np6-905-cd",
            )

        assert route.called
