"""Tests for base ISO client classes"""

import pytest

from tinygrid.base import BaseISOClient
from tinygrid.errors import GridError


class ConcreteISOClient(BaseISOClient):
    """Concrete implementation for testing"""

    @property
    def iso_name(self) -> str:
        return "TEST_ISO"


class TestBaseISOClient:
    """Test the BaseISOClient class"""

    def test_initialization(self):
        """Test initializing a BaseISOClient."""
        client = ConcreteISOClient(base_url="https://api.test.com")
        assert client.base_url == "https://api.test.com"
        assert client.timeout == 30.0
        assert client.verify_ssl is True
        assert client.raise_on_error is True

    def test_initialization_custom_params(self):
        """Test initializing with custom parameters."""
        client = ConcreteISOClient(
            base_url="https://api.test.com",
            timeout=60.0,
            verify_ssl=False,
            raise_on_error=False,
        )
        assert client.timeout == 60.0
        assert client.verify_ssl is False
        assert client.raise_on_error is False

    def test_iso_name_property(self):
        """Test the iso_name property."""
        client = ConcreteISOClient(base_url="https://api.test.com")
        assert client.iso_name == "TEST_ISO"

    def test_repr(self):
        """Test the string representation."""
        client = ConcreteISOClient(base_url="https://api.test.com")
        repr_str = repr(client)
        assert "ConcreteISOClient" in repr_str
        assert "https://api.test.com" in repr_str

    def test_normalize_date(self):
        """Test date normalization."""
        client = ConcreteISOClient(base_url="https://api.test.com")
        assert client._normalize_date("2024-01-01") == "2024-01-01"
        assert client._normalize_date(" 2024-01-01 ") == "2024-01-01"

    def test_normalize_date_invalid_type(self):
        """Test date normalization with invalid type."""
        client = ConcreteISOClient(base_url="https://api.test.com")
        with pytest.raises(ValueError, match="Date must be a string"):
            client._normalize_date(123)

    def test_normalize_datetime(self):
        """Test datetime normalization."""
        client = ConcreteISOClient(base_url="https://api.test.com")
        assert (
            client._normalize_datetime("2024-01-01T00:00:00") == "2024-01-01T00:00:00"
        )
        assert (
            client._normalize_datetime(" 2024-01-01T00:00:00 ") == "2024-01-01T00:00:00"
        )

    def test_normalize_datetime_invalid_type(self):
        """Test datetime normalization with invalid type."""
        client = ConcreteISOClient(base_url="https://api.test.com")
        with pytest.raises(ValueError, match="Datetime must be a string"):
            client._normalize_datetime(123)

    def test_handle_error_raises_when_enabled(self):
        """Test error handling raises when raise_on_error is True."""
        client = ConcreteISOClient(base_url="https://api.test.com", raise_on_error=True)
        error = ValueError("Test error")

        with pytest.raises(GridError):
            client._handle_error(error, endpoint="/test")

    def test_handle_error_silent_when_disabled(self):
        """Test error handling is silent when raise_on_error is False."""
        client = ConcreteISOClient(
            base_url="https://api.test.com", raise_on_error=False
        )
        error = ValueError("Test error")

        # Should not raise
        client._handle_error(error, endpoint="/test")

    def test_handle_error_preserves_grid_error(self):
        """Test that GridErrors are preserved."""
        from tinygrid.errors import GridAPIError

        client = ConcreteISOClient(base_url="https://api.test.com", raise_on_error=True)
        original_error = GridAPIError("Original error", status_code=500)

        with pytest.raises(GridAPIError) as exc_info:
            client._handle_error(original_error, endpoint="/test")

        assert exc_info.value.status_code == 500
