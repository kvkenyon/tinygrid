
import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from tenacity import RetryError, Future
from pyercot.errors import UnexpectedStatus

from tinygrid.ercot.client import ERCOTBase, _is_retryable_error
from tinygrid.errors import (
    GridAPIError,
    GridAuthenticationError,
    GridRateLimitError,
    GridRetryExhaustedError,
    GridTimeoutError,
    GridError,
)
from tinygrid.auth import ERCOTAuth

class TestERCOTClientCoverage:

    def test_is_retryable_error(self):
        # Test GridRateLimitError
        assert _is_retryable_error(GridRateLimitError("Limit exceeded")) is True
        
        # Test GridAPIError with retryable status codes
        for status in [429, 500, 502, 503, 504]:
            assert _is_retryable_error(GridAPIError("Error", status_code=status)) is True
            
        # Test GridAPIError with non-retryable status codes
        assert _is_retryable_error(GridAPIError("Error", status_code=400)) is False
        assert _is_retryable_error(GridAPIError("Error", status_code=404)) is False
        
        # Test other exceptions
        assert _is_retryable_error(ValueError("Error")) is False

    def test_get_client_auth_flow(self):
        # Mock auth
        auth = MagicMock(spec=ERCOTAuth)
        auth.get_token.return_value = "token1"
        auth.get_subscription_key.return_value = "key1"
        
        client = ERCOTBase(auth=auth)
        
        # Mock exit tracker
        exit_mock = MagicMock()
        
        class MockClient:
            def __init__(self, base_url=None, token=None, **kwargs):
                self.token = token
            
            def with_headers(self, headers):
                return self
                
            def __enter__(self):
                return self
                
            def __exit__(self, *args):
                exit_mock()

        with patch("tinygrid.ercot.client.AuthenticatedClient", new=MockClient):
            # First call - creates client
            c1 = client._get_client()
            assert c1.token == "token1"
            
            # Second call - reuses client
            c2 = client._get_client()
            assert c1 is c2
            
            # Token change triggers client recreation
            auth.get_token.return_value = "token2"
            
            c3 = client._get_client()
            assert c3 is not c1
            assert c3.token == "token2"
            assert exit_mock.called

    def test_get_client_auth_error(self):
        auth = MagicMock(spec=ERCOTAuth)
        auth.get_token.side_effect = Exception("Auth failed")
        
        client = ERCOTBase(auth=auth)
        
        with pytest.raises(GridAuthenticationError, match="Failed to initialize authenticated client"):
            client._get_client()
            
    def test_get_client_grid_auth_error(self):
        auth = MagicMock(spec=ERCOTAuth)
        auth.get_token.side_effect = GridAuthenticationError("Auth failed")
        
        client = ERCOTBase(auth=auth)
        
        with pytest.raises(GridAuthenticationError):
            client._get_client()

    def test_handle_api_error(self):
        client = ERCOTBase()
        
        # UnexpectedStatus
        err = UnexpectedStatus(status_code=418, content=b"Im a teapot")
        with pytest.raises(GridAPIError) as exc:
            client._handle_api_error(err, endpoint="test")
        assert exc.value.status_code == 418
        
        # TimeoutError
        err = TimeoutError("Timed out")
        with pytest.raises(GridTimeoutError):
            client._handle_api_error(err)
            
        # GridError (re-raise)
        err = GridRateLimitError("Limit")
        with pytest.raises(GridRateLimitError):
            client._handle_api_error(err)
            
        # Other error
        err = ValueError("Something wrong")
        with pytest.raises(GridAPIError, match="Unexpected error"):
            client._handle_api_error(err)

    def test_extract_response_data(self):
        client = ERCOTBase()
        
        # None
        assert client._extract_response_data(None) == {}
        
        # Dict
        assert client._extract_response_data({"a": 1}) == {"a": 1}
        
        # Object with to_dict
        class ObjWithDict:
            def to_dict(self):
                return {"b": 2}
        assert client._extract_response_data(ObjWithDict()) == {"b": 2}
        
        # Report object structure
        class ReportData:
            def to_dict(self):
                return {"c": 3}
        class Report:
            data = ReportData()
        assert client._extract_response_data(Report()) == {"c": 3}
        
        # Report with additional properties in data
        class ReportDataProps:
            additional_properties = {"d": 4}
        class ReportProps:
            data = ReportDataProps()
        assert client._extract_response_data(ReportProps()) == {"d": 4}

        # Object with additional_properties at top level
        class TopProps:
            additional_properties = {"e": 5}
        assert client._extract_response_data(TopProps()) == {"e": 5}

    def test_supports_pagination(self):
        client = ERCOTBase()
        
        class ModuleWithPagination:
            def sync(self, client, page, size, **kwargs):
                pass
                
        class ModuleWithoutPagination:
            def sync(self, client, **kwargs):
                pass
                
        assert client._supports_pagination(ModuleWithPagination) is True
        assert client._supports_pagination(ModuleWithoutPagination) is False

    def test_returns_report_model(self):
        client = ERCOTBase()
        
        # Mocking signature is tricky with dynamic classes, so we rely on the heuristic
        # If we can't inspect, it returns True (default)
        assert client._returns_report_model(object()) is True
        
    def test_call_endpoint_raw_errors(self):
        client = ERCOTBase()
        mock_module = MagicMock()
        
        # Mock response with status code 429
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_module.sync.return_value = mock_response
        
        with pytest.raises(GridRateLimitError):
            client._call_endpoint_raw(mock_module, "test")
            
        # Mock response with status code 500
        mock_response.status_code = 500
        mock_response.content = b"Error"
        mock_module.sync.return_value = mock_response
        
        with pytest.raises(GridAPIError) as exc:
            client._call_endpoint_raw(mock_module, "test")
        assert exc.value.status_code == 500

    def test_call_with_retry_exhausted(self):
        client = ERCOTBase(max_retries=1, retry_min_wait=0.01)
        mock_module = MagicMock()
        
        # Always fail with 500
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_module.sync.return_value = mock_response
        
        with pytest.raises(GridRetryExhaustedError) as exc:
            client._call_with_retry(mock_module, "test")
        
        assert exc.value.attempts == 2  # Initial + 1 retry

    def test_products_to_dataframe(self):
        client = ERCOTBase()
        
        assert client._products_to_dataframe({}).empty
        assert client._products_to_dataframe({"products": []}).empty
        
        df = client._products_to_dataframe({"products": [{"id": 1}]})
        assert not df.empty
        assert df.iloc[0]["id"] == 1

    def test_model_to_dataframe(self):
        client = ERCOTBase()
        
        assert client._model_to_dataframe(None).empty
        assert client._model_to_dataframe({}).empty
        
        df = client._model_to_dataframe({"id": 1})
        assert not df.empty
        assert df.iloc[0]["id"] == 1

    def test_product_history_to_dataframe(self):
        client = ERCOTBase()
        
        assert client._product_history_to_dataframe({}).empty
        
        df = client._product_history_to_dataframe({"archives": [{"id": 1}]})
        assert not df.empty
        assert df.iloc[0]["id"] == 1

    def test_to_dataframe_empty(self):
        client = ERCOTBase()
        assert client._to_dataframe([], []).empty
        
        # With columns but no data
        df = client._to_dataframe([], [{"name": "col1"}])
        assert df.empty
        assert "col1" in df.columns
        
        # No fields, but data (should imply numeric cols)
        df = client._to_dataframe([[1, 2]], [])
        assert not df.empty
        assert df.shape == (1, 2)

