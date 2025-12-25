"""Tests for error handling"""


from tinygrid.errors import (
    GridAPIError,
    GridAuthenticationError,
    GridError,
    GridRateLimitError,
    GridTimeoutError,
)


class TestGridError:
    """Test the base GridError class"""

    def test_basic_error(self):
        """Test creating a basic GridError."""
        error = GridError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details == {}

    def test_error_with_details(self):
        """Test creating a GridError with details."""
        details = {"key": "value", "code": 123}
        error = GridError("Test error", details=details)
        assert error.message == "Test error"
        assert error.details == details


class TestGridTimeoutError:
    """Test the GridTimeoutError class"""

    def test_timeout_error(self):
        """Test creating a GridTimeoutError."""
        error = GridTimeoutError(timeout=30.0)
        assert "timed out" in error.message.lower()
        assert error.timeout == 30.0
        assert error.details["timeout"] == 30.0

    def test_timeout_error_custom_message(self):
        """Test creating a GridTimeoutError with custom message."""
        error = GridTimeoutError("Custom timeout message", timeout=60.0)
        assert error.message == "Custom timeout message"
        assert error.timeout == 60.0


class TestGridAPIError:
    """Test the GridAPIError class"""

    def test_api_error_basic(self):
        """Test creating a basic GridAPIError."""
        error = GridAPIError("API error")
        assert error.message == "API error"
        assert error.status_code is None
        assert error.response_body is None
        assert error.endpoint is None

    def test_api_error_with_status_code(self):
        """Test creating a GridAPIError with status code."""
        error = GridAPIError("API error", status_code=404)
        assert error.status_code == 404
        assert error.details["status_code"] == 404

    def test_api_error_with_response_body(self):
        """Test creating a GridAPIError with response body."""
        error = GridAPIError("API error", response_body="Error details")
        assert error.response_body == "Error details"
        assert error.details["response_body"] == "Error details"

    def test_api_error_with_bytes_response_body(self):
        """Test creating a GridAPIError with bytes response body."""
        error = GridAPIError("API error", response_body=b"Error details")
        assert error.response_body == b"Error details"
        assert error.details["response_body"] == "Error details"

    def test_api_error_with_endpoint(self):
        """Test creating a GridAPIError with endpoint."""
        error = GridAPIError("API error", endpoint="/api/test")
        assert error.endpoint == "/api/test"
        assert error.details["endpoint"] == "/api/test"

    def test_api_error_full(self):
        """Test creating a GridAPIError with all parameters."""
        error = GridAPIError(
            "API error",
            status_code=500,
            response_body="Server error",
            endpoint="/api/test",
        )
        assert error.status_code == 500
        assert error.response_body == "Server error"
        assert error.endpoint == "/api/test"
        assert error.details["status_code"] == 500
        assert error.details["response_body"] == "Server error"
        assert error.details["endpoint"] == "/api/test"


class TestGridAuthenticationError:
    """Test the GridAuthenticationError class"""

    def test_authentication_error(self):
        """Test creating a GridAuthenticationError."""
        error = GridAuthenticationError()
        assert "authentication" in error.message.lower()

    def test_authentication_error_custom_message(self):
        """Test creating a GridAuthenticationError with custom message."""
        error = GridAuthenticationError("Custom auth error", status_code=401)
        assert error.message == "Custom auth error"
        assert error.status_code == 401


class TestGridRateLimitError:
    """Test the GridRateLimitError class"""

    def test_rate_limit_error(self):
        """Test creating a GridRateLimitError."""
        error = GridRateLimitError(retry_after=60)
        assert "rate limit" in error.message.lower()
        assert error.retry_after == 60
        assert error.details["retry_after"] == 60

    def test_rate_limit_error_custom_message(self):
        """Test creating a GridRateLimitError with custom message."""
        error = GridRateLimitError("Custom rate limit error", retry_after=120)
        assert error.message == "Custom rate limit error"
        assert error.retry_after == 120

