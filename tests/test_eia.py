"""Tests for tinygrid.ercot.eia module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from tinygrid.ercot.eia import (
    EIA_API_BASE_URL,
    EIA_BULK_DOWNLOAD_URL,
    ERCOT_BA_CODE,
    EIAClient,
    _map_fuel_type,
)


class TestEIAConstants:
    """Tests for EIA constants."""

    def test_eia_api_base_url(self):
        """Test EIA API base URL."""
        assert EIA_API_BASE_URL == "https://api.eia.gov/v2"

    def test_ercot_ba_code(self):
        """Test ERCOT balancing authority code."""
        assert ERCOT_BA_CODE == "ERCO"

    def test_eia_bulk_download_url(self):
        """Test EIA bulk download URL."""
        assert EIA_BULK_DOWNLOAD_URL == "https://www.eia.gov/opendata/bulk/EBA.zip"


class TestMapFuelType:
    """Tests for _map_fuel_type function."""

    def test_map_coal(self):
        """Test mapping coal fuel type."""
        assert _map_fuel_type("COL") == "coal"
        assert _map_fuel_type("col") == "coal"

    def test_map_natural_gas(self):
        """Test mapping natural gas fuel type."""
        assert _map_fuel_type("NG") == "natural_gas"
        assert _map_fuel_type("ng") == "natural_gas"

    def test_map_nuclear(self):
        """Test mapping nuclear fuel type."""
        assert _map_fuel_type("NUC") == "nuclear"

    def test_map_oil(self):
        """Test mapping oil fuel type."""
        assert _map_fuel_type("OIL") == "oil"

    def test_map_hydro(self):
        """Test mapping hydro fuel type."""
        assert _map_fuel_type("WAT") == "hydro"

    def test_map_wind(self):
        """Test mapping wind fuel type."""
        assert _map_fuel_type("WND") == "wind"

    def test_map_solar(self):
        """Test mapping solar fuel type."""
        assert _map_fuel_type("SUN") == "solar"

    def test_map_other(self):
        """Test mapping other fuel type."""
        assert _map_fuel_type("OTH") == "other"

    def test_map_unknown(self):
        """Test mapping unknown fuel type."""
        assert _map_fuel_type("UNK") == "unknown"

    def test_map_unmapped_returns_lowercase(self):
        """Test unmapped fuel types return lowercase."""
        assert _map_fuel_type("XYZ") == "xyz"
        assert _map_fuel_type("NewType") == "newtype"


class TestEIAClientInit:
    """Tests for EIAClient initialization."""

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        client = EIAClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.timeout == 30.0

    def test_init_with_custom_timeout(self):
        """Test initialization with custom timeout."""
        client = EIAClient(api_key="test-key", timeout=60.0)
        assert client.timeout == 60.0

    def test_init_without_api_key(self):
        """Test initialization without API key."""
        client = EIAClient()
        assert client.api_key is None


class TestEIAClientMakeRequest:
    """Tests for EIAClient._make_request method."""

    def test_make_request_without_api_key_raises(self):
        """Test that make_request raises without API key."""
        client = EIAClient()

        with pytest.raises(ValueError, match="EIA API key required"):
            client._make_request("test-endpoint")

    @patch("tinygrid.ercot.eia.httpx.Client")
    def test_make_request_success(self, mock_client_class):
        """Test successful API request."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": {"data": []}}
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client_class.return_value = mock_client

        client = EIAClient(api_key="test-key")
        result = client._make_request("test-endpoint", {"param": "value"})

        assert result == {"response": {"data": []}}
        mock_client.get.assert_called_once()

    @patch("tinygrid.ercot.eia.httpx.Client")
    def test_make_request_timeout(self, mock_client_class):
        """Test request timeout handling."""
        import httpx

        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.TimeoutException("Timeout")
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client_class.return_value = mock_client

        client = EIAClient(api_key="test-key")

        with pytest.raises(httpx.TimeoutException):
            client._make_request("test-endpoint")

    @patch("tinygrid.ercot.eia.httpx.Client")
    def test_make_request_http_error(self, mock_client_class):
        """Test HTTP error handling."""
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error",
            request=MagicMock(),
            response=mock_response,
        )
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client_class.return_value = mock_client

        client = EIAClient(api_key="test-key")

        with pytest.raises(httpx.HTTPStatusError):
            client._make_request("test-endpoint")


class TestEIAClientGetDemand:
    """Tests for EIAClient.get_demand method."""

    @patch.object(EIAClient, "_make_request")
    def test_get_demand_success(self, mock_request):
        """Test successful demand data fetch."""
        mock_request.return_value = {
            "response": {
                "data": [
                    {"period": "2024-01-01T12:00:00", "value": 50000},
                    {"period": "2024-01-01T13:00:00", "value": 51000},
                ]
            }
        }

        client = EIAClient(api_key="test-key")
        result = client.get_demand(start="2024-01-01", end="2024-01-02")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "timestamp" in result.columns
        assert "demand_mw" in result.columns
        assert result["demand_mw"].iloc[0] == 50000

    @patch.object(EIAClient, "_make_request")
    def test_get_demand_empty_response(self, mock_request):
        """Test empty demand response."""
        mock_request.return_value = {"response": {"data": []}}

        client = EIAClient(api_key="test-key")
        result = client.get_demand(start="2024-01-01")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @patch.object(EIAClient, "_make_request")
    def test_get_demand_with_default_end(self, mock_request):
        """Test demand fetch with default end date."""
        mock_request.return_value = {"response": {"data": []}}

        client = EIAClient(api_key="test-key")
        result = client.get_demand(start="2024-01-01")

        # Should have called with end = start + 7 days
        assert isinstance(result, pd.DataFrame)

    @patch.object(EIAClient, "_make_request")
    def test_get_demand_exception_returns_empty(self, mock_request):
        """Test that exceptions return empty DataFrame."""
        mock_request.side_effect = Exception("API Error")

        client = EIAClient(api_key="test-key")
        result = client.get_demand(start="2024-01-01")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
        assert "demand_mw" in result.columns


class TestEIAClientGetGeneration:
    """Tests for EIAClient.get_generation method."""

    @patch.object(EIAClient, "_make_request")
    def test_get_generation_success(self, mock_request):
        """Test successful generation data fetch."""
        mock_request.return_value = {
            "response": {
                "data": [
                    {"period": "2024-01-01T12:00:00", "value": 48000},
                    {"period": "2024-01-01T13:00:00", "value": 49000},
                ]
            }
        }

        client = EIAClient(api_key="test-key")
        result = client.get_generation(start="2024-01-01")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "generation_mw" in result.columns

    @patch.object(EIAClient, "_make_request")
    def test_get_generation_empty_response(self, mock_request):
        """Test empty generation response."""
        mock_request.return_value = {"response": {"data": []}}

        client = EIAClient(api_key="test-key")
        result = client.get_generation(start="2024-01-01")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @patch.object(EIAClient, "_make_request")
    def test_get_generation_exception_returns_empty(self, mock_request):
        """Test that exceptions return empty DataFrame."""
        mock_request.side_effect = Exception("API Error")

        client = EIAClient(api_key="test-key")
        result = client.get_generation(start="2024-01-01")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


class TestEIAClientGetGenerationByFuel:
    """Tests for EIAClient.get_generation_by_fuel method."""

    @patch.object(EIAClient, "_make_request")
    def test_get_generation_by_fuel_success(self, mock_request):
        """Test successful fuel mix data fetch."""
        mock_request.return_value = {
            "response": {
                "data": [
                    {"period": "2024-01-01T12:00:00", "fueltype": "NG", "value": 25000},
                    {
                        "period": "2024-01-01T12:00:00",
                        "fueltype": "WND",
                        "value": 18000,
                    },
                ]
            }
        }

        client = EIAClient(api_key="test-key")
        result = client.get_generation_by_fuel(start="2024-01-01")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "fuel_type" in result.columns
        assert "generation_mw" in result.columns
        assert result["fuel_type"].iloc[0] == "natural_gas"
        assert result["fuel_type"].iloc[1] == "wind"

    @patch.object(EIAClient, "_make_request")
    def test_get_generation_by_fuel_empty(self, mock_request):
        """Test empty fuel mix response."""
        mock_request.return_value = {"response": {"data": []}}

        client = EIAClient(api_key="test-key")
        result = client.get_generation_by_fuel(start="2024-01-01")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @patch.object(EIAClient, "_make_request")
    def test_get_generation_by_fuel_exception(self, mock_request):
        """Test that exceptions return empty DataFrame."""
        mock_request.side_effect = Exception("API Error")

        client = EIAClient(api_key="test-key")
        result = client.get_generation_by_fuel(start="2024-01-01")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


class TestEIAClientGetInterchange:
    """Tests for EIAClient.get_interchange method."""

    @patch.object(EIAClient, "_make_request")
    def test_get_interchange_success(self, mock_request):
        """Test successful interchange data fetch."""
        mock_request.return_value = {
            "response": {
                "data": [
                    {"period": "2024-01-01T12:00:00", "value": 500},
                    {"period": "2024-01-01T13:00:00", "value": -200},
                ]
            }
        }

        client = EIAClient(api_key="test-key")
        result = client.get_interchange(start="2024-01-01")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "interchange_mw" in result.columns
        assert result["interchange_mw"].iloc[0] == 500

    @patch.object(EIAClient, "_make_request")
    def test_get_interchange_empty(self, mock_request):
        """Test empty interchange response."""
        mock_request.return_value = {"response": {"data": []}}

        client = EIAClient(api_key="test-key")
        result = client.get_interchange(start="2024-01-01")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @patch.object(EIAClient, "_make_request")
    def test_get_interchange_exception(self, mock_request):
        """Test that exceptions return empty DataFrame."""
        mock_request.side_effect = Exception("API Error")

        client = EIAClient(api_key="test-key")
        result = client.get_interchange(start="2024-01-01")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
