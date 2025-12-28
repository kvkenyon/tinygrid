"""Tests for ERCOT client pagination logic"""

import inspect
from unittest.mock import MagicMock

from tinygrid import ERCOT


def create_paginated_mock():
    """Create a mock endpoint that appears to support pagination.

    The ERCOT client uses inspect.signature() to check if an endpoint
    supports pagination by looking for 'page' and 'size' parameters.
    We need to create a mock with a proper signature for this to work.
    """

    # Define a function with the signature we need
    def sync_func(
        client,
        *,
        page: int = 1,
        size: int = 10000,
        **kwargs,
    ):
        pass

    # Create a mock that will have this signature
    mock_endpoint = MagicMock()
    mock_endpoint.sync = MagicMock()
    # Set the spec to our function so inspect.signature works
    mock_endpoint.sync.__signature__ = inspect.signature(sync_func)

    return mock_endpoint


class TestPaginationConfig:
    """Test pagination configuration."""

    def test_pagination_config_defaults(self):
        """Test default pagination configuration values."""
        ercot = ERCOT()
        assert ercot.page_size == 10000
        assert ercot.max_concurrent_requests == 5

    def test_pagination_config_custom(self):
        """Test custom pagination configuration values."""
        ercot = ERCOT(
            page_size=1000,
            max_concurrent_requests=10,
        )
        assert ercot.page_size == 1000
        assert ercot.max_concurrent_requests == 10


class TestFetchAllPages:
    """Test the _fetch_all_pages method."""

    def test_single_page_response(self, sample_single_page_response):
        """Test fetching data when there's only one page."""
        mock_endpoint = create_paginated_mock()

        mock_response = MagicMock()
        mock_response.to_dict.return_value = sample_single_page_response

        mock_endpoint.sync.return_value = mock_response

        ercot = ERCOT(retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        records, fields = ercot._fetch_all_pages(mock_endpoint, "test_endpoint")

        # Should only call once for single page
        assert mock_endpoint.sync.call_count == 1
        assert len(records) == 5
        assert len(fields) == 4

    def test_multiple_pages_response(self, sample_fields):
        """Test fetching data across multiple pages."""
        mock_endpoint = create_paginated_mock()

        # Create responses for 3 pages
        page1_response = {
            "_meta": {
                "totalRecords": 15,
                "pageSize": 5,
                "totalPages": 3,
                "currentPage": 1,
            },
            "fields": sample_fields,
            "data": {
                "records": [["2024-01-01", False, "BUS001", 25.0] for _ in range(5)]
            },
        }
        page2_response = {
            "_meta": {
                "totalRecords": 15,
                "pageSize": 5,
                "totalPages": 3,
                "currentPage": 2,
            },
            "fields": sample_fields,
            "data": {
                "records": [["2024-01-01", False, "BUS002", 26.0] for _ in range(5)]
            },
        }
        page3_response = {
            "_meta": {
                "totalRecords": 15,
                "pageSize": 5,
                "totalPages": 3,
                "currentPage": 3,
            },
            "fields": sample_fields,
            "data": {
                "records": [["2024-01-01", False, "BUS003", 27.0] for _ in range(5)]
            },
        }

        def make_mock_response(response_dict):
            mock = MagicMock()
            mock.to_dict.return_value = response_dict
            return mock

        # Return different responses based on page parameter
        def side_effect(*args, **kwargs):
            page = kwargs.get("page", 1)
            if page == 1:
                return make_mock_response(page1_response)
            elif page == 2:
                return make_mock_response(page2_response)
            else:
                return make_mock_response(page3_response)

        mock_endpoint.sync.side_effect = side_effect

        ercot = ERCOT(retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        records, fields = ercot._fetch_all_pages(mock_endpoint, "test_endpoint")

        # Should call 3 times (once per page)
        assert mock_endpoint.sync.call_count == 3
        assert len(records) == 15  # 5 records per page * 3 pages
        assert len(fields) == 4

    def test_empty_response(self, sample_empty_response):
        """Test fetching data when response is empty."""
        mock_endpoint = create_paginated_mock()

        mock_response = MagicMock()
        mock_response.to_dict.return_value = sample_empty_response

        mock_endpoint.sync.return_value = mock_response

        ercot = ERCOT(retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        records, fields = ercot._fetch_all_pages(mock_endpoint, "test_endpoint")

        assert len(records) == 0
        assert len(fields) == 4

    def test_page_size_parameter_passed(self, sample_single_page_response):
        """Test that page_size is passed to the endpoint."""
        mock_endpoint = create_paginated_mock()

        mock_response = MagicMock()
        mock_response.to_dict.return_value = sample_single_page_response

        mock_endpoint.sync.return_value = mock_response

        ercot = ERCOT(page_size=1000, retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        ercot._fetch_all_pages(mock_endpoint, "test_endpoint")

        # Check that size parameter was passed
        call_kwargs = mock_endpoint.sync.call_args[1]
        assert call_kwargs["size"] == 1000

    def test_custom_size_overrides_default(self, sample_single_page_response):
        """Test that custom size parameter overrides default page_size."""
        mock_endpoint = create_paginated_mock()

        mock_response = MagicMock()
        mock_response.to_dict.return_value = sample_single_page_response

        mock_endpoint.sync.return_value = mock_response

        ercot = ERCOT(page_size=10000, retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        ercot._fetch_all_pages(mock_endpoint, "test_endpoint", size=500)

        # Custom size should be used
        call_kwargs = mock_endpoint.sync.call_args[1]
        assert call_kwargs["size"] == 500

    def test_fields_from_first_page_only(self, sample_fields):
        """Test that fields are only taken from the first page."""
        mock_endpoint = create_paginated_mock()

        page1_response = {
            "_meta": {
                "totalRecords": 10,
                "pageSize": 5,
                "totalPages": 2,
                "currentPage": 1,
            },
            "fields": sample_fields,
            "data": {
                "records": [["2024-01-01", False, "BUS001", 25.0] for _ in range(5)]
            },
        }
        page2_response = {
            "_meta": {
                "totalRecords": 10,
                "pageSize": 5,
                "totalPages": 2,
                "currentPage": 2,
            },
            "fields": [
                {"name": "different", "label": "Different Field"}
            ],  # Different fields
            "data": {
                "records": [["2024-01-01", False, "BUS002", 26.0] for _ in range(5)]
            },
        }

        def make_mock_response(response_dict):
            mock = MagicMock()
            mock.to_dict.return_value = response_dict
            return mock

        def side_effect(*args, **kwargs):
            page = kwargs.get("page", 1)
            if page == 1:
                return make_mock_response(page1_response)
            return make_mock_response(page2_response)

        mock_endpoint.sync.side_effect = side_effect

        ercot = ERCOT(retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        records, fields = ercot._fetch_all_pages(mock_endpoint, "test_endpoint")

        # Fields should be from first page
        assert fields == sample_fields
        assert len(records) == 10


class TestCallEndpoint:
    """Test the _call_endpoint method."""

    def test_returns_dataframe(self, sample_single_page_response):
        """Test that _call_endpoint returns a DataFrame."""
        import pandas as pd

        mock_endpoint = create_paginated_mock()

        mock_response = MagicMock()
        mock_response.to_dict.return_value = sample_single_page_response

        mock_endpoint.sync.return_value = mock_response

        ercot = ERCOT(retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        result = ercot._call_endpoint(mock_endpoint, "test_endpoint", fetch_all=True)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5

    def test_fetch_all_false(self, sample_paginated_response):
        """Test that fetch_all=False only fetches first page."""
        import pandas as pd

        mock_endpoint = create_paginated_mock()

        mock_response = MagicMock()
        mock_response.to_dict.return_value = sample_paginated_response

        mock_endpoint.sync.return_value = mock_response

        ercot = ERCOT(retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        result = ercot._call_endpoint(mock_endpoint, "test_endpoint", fetch_all=False)

        # Should only be called once
        assert mock_endpoint.sync.call_count == 1
        assert isinstance(result, pd.DataFrame)
