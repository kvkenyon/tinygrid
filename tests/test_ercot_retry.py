"""Tests for ERCOT client retry logic"""

from unittest.mock import MagicMock, patch

import pytest

from tinygrid import ERCOT
from tinygrid.errors import (
    GridAPIError,
    GridRateLimitError,
)


class TestRetryLogic:
    """Test the retry logic with tenacity."""

    def test_retry_config_defaults(self):
        """Test default retry configuration values."""
        ercot = ERCOT()
        assert ercot.max_retries == 3
        assert ercot.retry_min_wait == 1.0
        assert ercot.retry_max_wait == 60.0

    def test_retry_config_custom(self):
        """Test custom retry configuration values."""
        ercot = ERCOT(
            max_retries=5,
            retry_min_wait=0.5,
            retry_max_wait=30.0,
        )
        assert ercot.max_retries == 5
        assert ercot.retry_min_wait == 0.5
        assert ercot.retry_max_wait == 30.0

    @patch("tinygrid.ercot.endpoints.lmp_electrical_bus")
    def test_successful_request_no_retry(
        self, mock_endpoint, sample_single_page_response
    ):
        """Test that successful requests don't trigger retries."""
        mock_endpoint.sync.return_value = MagicMock()
        mock_endpoint.sync.return_value.to_dict.return_value = (
            sample_single_page_response
        )

        ercot = ERCOT()
        ercot._client = MagicMock()

        result = ercot._call_with_retry(mock_endpoint, "test_endpoint", page=1)

        assert mock_endpoint.sync.call_count == 1
        assert "_meta" in result

    @patch("tinygrid.ercot.endpoints.lmp_electrical_bus")
    def test_retry_on_500_error(self, mock_endpoint, sample_single_page_response):
        """Test that 500 errors trigger retries."""
        # First call fails, second succeeds
        mock_response = MagicMock()
        mock_response.to_dict.return_value = sample_single_page_response

        mock_endpoint.sync.side_effect = [
            GridAPIError("Server error", status_code=500),
            mock_response,
        ]

        ercot = ERCOT(max_retries=2, retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        result = ercot._call_with_retry(mock_endpoint, "test_endpoint", page=1)

        assert mock_endpoint.sync.call_count == 2
        assert "_meta" in result

    @patch("tinygrid.ercot.endpoints.lmp_electrical_bus")
    def test_retry_on_429_rate_limit(self, mock_endpoint, sample_single_page_response):
        """Test that 429 rate limit errors trigger retries."""
        mock_response = MagicMock()
        mock_response.to_dict.return_value = sample_single_page_response

        mock_endpoint.sync.side_effect = [
            GridRateLimitError("Rate limited", status_code=429),
            mock_response,
        ]

        ercot = ERCOT(max_retries=2, retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        result = ercot._call_with_retry(mock_endpoint, "test_endpoint", page=1)

        assert mock_endpoint.sync.call_count == 2
        assert "_meta" in result

    @patch("tinygrid.ercot.endpoints.lmp_electrical_bus")
    def test_retry_on_502_gateway_error(
        self, mock_endpoint, sample_single_page_response
    ):
        """Test that 502 gateway errors trigger retries."""
        mock_response = MagicMock()
        mock_response.to_dict.return_value = sample_single_page_response

        mock_endpoint.sync.side_effect = [
            GridAPIError("Bad gateway", status_code=502),
            mock_response,
        ]

        ercot = ERCOT(max_retries=2, retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        ercot._call_with_retry(mock_endpoint, "test_endpoint", page=1)

        assert mock_endpoint.sync.call_count == 2

    @patch("tinygrid.ercot.endpoints.lmp_electrical_bus")
    def test_retry_on_503_service_unavailable(
        self, mock_endpoint, sample_single_page_response
    ):
        """Test that 503 service unavailable errors trigger retries."""
        mock_response = MagicMock()
        mock_response.to_dict.return_value = sample_single_page_response

        mock_endpoint.sync.side_effect = [
            GridAPIError("Service unavailable", status_code=503),
            mock_response,
        ]

        ercot = ERCOT(max_retries=2, retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        ercot._call_with_retry(mock_endpoint, "test_endpoint", page=1)

        assert mock_endpoint.sync.call_count == 2

    @patch("tinygrid.ercot.endpoints.lmp_electrical_bus")
    def test_retry_on_504_gateway_timeout(
        self, mock_endpoint, sample_single_page_response
    ):
        """Test that 504 gateway timeout errors trigger retries."""
        mock_response = MagicMock()
        mock_response.to_dict.return_value = sample_single_page_response

        mock_endpoint.sync.side_effect = [
            GridAPIError("Gateway timeout", status_code=504),
            mock_response,
        ]

        ercot = ERCOT(max_retries=2, retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        ercot._call_with_retry(mock_endpoint, "test_endpoint", page=1)

        assert mock_endpoint.sync.call_count == 2

    @patch("tinygrid.ercot.endpoints.lmp_electrical_bus")
    def test_no_retry_on_400_client_error(self, mock_endpoint):
        """Test that 400 client errors do not trigger retries."""
        mock_endpoint.sync.side_effect = GridAPIError("Bad request", status_code=400)

        ercot = ERCOT(max_retries=3, retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        with pytest.raises(GridAPIError) as exc_info:
            ercot._call_with_retry(mock_endpoint, "test_endpoint", page=1)

        assert exc_info.value.status_code == 400
        # Should only be called once (no retries for 400)
        assert mock_endpoint.sync.call_count == 1

    @patch("tinygrid.ercot.endpoints.lmp_electrical_bus")
    def test_no_retry_on_401_unauthorized(self, mock_endpoint):
        """Test that 401 unauthorized errors do not trigger retries."""
        mock_endpoint.sync.side_effect = GridAPIError("Unauthorized", status_code=401)

        ercot = ERCOT(max_retries=3, retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        with pytest.raises(GridAPIError) as exc_info:
            ercot._call_with_retry(mock_endpoint, "test_endpoint", page=1)

        assert exc_info.value.status_code == 401
        assert mock_endpoint.sync.call_count == 1

    @patch("tinygrid.ercot.endpoints.lmp_electrical_bus")
    def test_no_retry_on_404_not_found(self, mock_endpoint):
        """Test that 404 not found errors do not trigger retries."""
        mock_endpoint.sync.side_effect = GridAPIError("Not found", status_code=404)

        ercot = ERCOT(max_retries=3, retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        with pytest.raises(GridAPIError) as exc_info:
            ercot._call_with_retry(mock_endpoint, "test_endpoint", page=1)

        assert exc_info.value.status_code == 404
        assert mock_endpoint.sync.call_count == 1

    @patch("tinygrid.ercot.endpoints.lmp_electrical_bus")
    def test_retry_exhausted_raises_error(self, mock_endpoint):
        """Test that exhausting retries raises GridAPIError (the last error)."""
        mock_endpoint.sync.side_effect = GridAPIError("Server error", status_code=500)

        ercot = ERCOT(max_retries=2, retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        # tenacity with reraise=True re-raises the original exception
        with pytest.raises(GridAPIError) as exc_info:
            ercot._call_with_retry(mock_endpoint, "test_endpoint", page=1)

        assert exc_info.value.status_code == 500
        # Should be called max_retries + 1 times
        assert mock_endpoint.sync.call_count == 3

    @patch("tinygrid.ercot.endpoints.lmp_electrical_bus")
    def test_retry_exhausted_includes_endpoint_name(self, mock_endpoint):
        """Test that retry exhausted error includes status code."""
        mock_endpoint.sync.side_effect = GridAPIError("Server error", status_code=500)

        ercot = ERCOT(max_retries=1, retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        # tenacity with reraise=True re-raises the original exception
        with pytest.raises(GridAPIError) as exc_info:
            ercot._call_with_retry(mock_endpoint, "my_custom_endpoint", page=1)

        assert exc_info.value.status_code == 500

    @patch("tinygrid.ercot.endpoints.lmp_electrical_bus")
    def test_multiple_retries_before_success(
        self, mock_endpoint, sample_single_page_response
    ):
        """Test successful recovery after multiple retries."""
        mock_response = MagicMock()
        mock_response.to_dict.return_value = sample_single_page_response

        mock_endpoint.sync.side_effect = [
            GridAPIError("Server error", status_code=500),
            GridAPIError("Server error", status_code=503),
            mock_response,
        ]

        ercot = ERCOT(max_retries=3, retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        result = ercot._call_with_retry(mock_endpoint, "test_endpoint", page=1)

        assert mock_endpoint.sync.call_count == 3
        assert "_meta" in result
