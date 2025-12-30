"""Core ERCOT client implementation with authentication and retry logic."""

from __future__ import annotations

import inspect
import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, Any

import httpx
import pandas as pd
from attrs import define, field
from pyercot.errors import UnexpectedStatus
from tenacity import (
    RetryError,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from pyercot import AuthenticatedClient
from pyercot import Client as ERCOTClient

from ..auth import ERCOTAuth
from ..base import BaseISOClient
from ..constants.ercot import (
    ERCOT_TIMEZONE,
    HISTORICAL_THRESHOLD_DAYS,
)
from ..errors import (
    GridAPIError,
    GridAuthenticationError,
    GridError,
    GridRateLimitError,
    GridRetryExhaustedError,
    GridTimeoutError,
)
from ..utils.rate_limiter import ERCOT_REQUESTS_PER_MINUTE, RateLimiter

if TYPE_CHECKING:
    from .archive import ERCOTArchive

logger = logging.getLogger(__name__)


def _is_retryable_error(exception: BaseException) -> bool:
    """Check if an exception is retryable.

    Args:
        exception: The exception to check

    Returns:
        True if the exception is retryable (rate limit or server error)
    """
    if isinstance(exception, GridRateLimitError):
        return True
    if isinstance(exception, GridAPIError):
        return exception.status_code in (429, 500, 502, 503, 504)
    return False


@define
class ERCOTBase(BaseISOClient):
    """Base ERCOT client with authentication, retry logic, and lifecycle management.

    This class provides the core infrastructure for communicating with the ERCOT API.
    Endpoint methods and high-level API methods are provided by mixin classes.

    Args:
        base_url: Base URL for the ERCOT API. Defaults to the official ERCOT API URL.
        timeout: Request timeout in seconds. Defaults to 30.0.
        verify_ssl: Whether to verify SSL certificates. Defaults to True.
        raise_on_error: Whether to raise exceptions on errors. Defaults to True.
        auth: Optional ERCOTAuth instance for authenticated requests.
        max_retries: Maximum number of retry attempts for transient failures. Defaults to 3.
        retry_min_wait: Minimum wait time between retries in seconds. Defaults to 1.0.
        retry_max_wait: Maximum wait time between retries in seconds. Defaults to 60.0.
        page_size: Number of records per page when fetching data. Defaults to 10000.
        max_concurrent_requests: Maximum number of concurrent page requests. Defaults to 5.
        rate_limit_enabled: Whether to enforce rate limiting. Defaults to True.
        requests_per_minute: Maximum requests per minute. Defaults to 30 (ERCOT limit).
    """

    base_url: str = field(default="https://api.ercot.com/api/public-reports")
    timeout: float | None = field(default=30.0, kw_only=True)
    verify_ssl: bool = field(default=True, kw_only=True)
    raise_on_error: bool = field(default=True, kw_only=True)
    auth: ERCOTAuth | None = field(default=None, kw_only=True)

    # Retry configuration
    max_retries: int = field(default=3, kw_only=True)
    retry_min_wait: float = field(default=1.0, kw_only=True)
    retry_max_wait: float = field(default=60.0, kw_only=True)

    # Pagination configuration
    page_size: int = field(default=10000, kw_only=True)
    max_concurrent_requests: int = field(default=5, kw_only=True)

    # Rate limiting configuration
    rate_limit_enabled: bool = field(default=True, kw_only=True)
    requests_per_minute: float = field(default=ERCOT_REQUESTS_PER_MINUTE, kw_only=True)

    _client: ERCOTClient | AuthenticatedClient | None = field(
        default=None, init=False, repr=False
    )
    _entered_client: ERCOTClient | AuthenticatedClient | None = field(
        default=None, init=False, repr=False
    )
    _archive: Any = field(default=None, init=False, repr=False)
    _rate_limiter: RateLimiter | None = field(default=None, init=False, repr=False)

    @property
    def iso_name(self) -> str:
        """Return the name of the ISO."""
        return "ERCOT"

    def _get_client(self) -> ERCOTClient | AuthenticatedClient:
        """Get or create the underlying ERCOT API client.

        Automatically refreshes token if using authentication and token is expired.

        Returns:
            Configured ERCOTClient or AuthenticatedClient instance
        """

        if self.auth is not None:
            # Ensure we have a valid token (will refresh if expired)
            try:
                token = self.auth.get_token()
                subscription_key = self.auth.get_subscription_key()

                # Recreate client if token changed or client doesn't exist
                if (
                    self._client is None
                    or not isinstance(self._client, AuthenticatedClient)
                    or self._client.token != token
                ):
                    # Close existing client if it exists
                    if self._client is not None:
                        try:
                            if hasattr(self._client, "__exit__"):
                                self._client.__exit__(None, None, None)
                        except Exception:
                            pass  # Ignore errors when closing

                    # Create authenticated client with token
                    self._client = AuthenticatedClient(
                        base_url=self.base_url,
                        token=token,
                        timeout=self.timeout,
                        verify_ssl=self.verify_ssl,
                        raise_on_unexpected_status=False,  # We handle errors ourselves
                    )

                    # Add subscription key header
                    self._client = self._client.with_headers(
                        {"Ocp-Apim-Subscription-Key": subscription_key}
                    )
            except GridAuthenticationError:
                raise
            except Exception as e:
                raise GridAuthenticationError(
                    f"Failed to initialize authenticated client: {e}"
                ) from e
        else:
            # Use unauthenticated client
            if self._client is None:
                self._client = ERCOTClient(
                    base_url=self.base_url,
                    timeout=self.timeout,
                    verify_ssl=self.verify_ssl,
                    raise_on_unexpected_status=False,  # We handle errors ourselves
                )

        return self._client

    def _get_rate_limiter(self) -> RateLimiter | None:
        """Get or create the rate limiter.

        Returns:
            RateLimiter instance if rate limiting is enabled, None otherwise
        """
        if not self.rate_limit_enabled:
            return None

        if self._rate_limiter is None:
            self._rate_limiter = RateLimiter(
                requests_per_minute=self.requests_per_minute
            )
        return self._rate_limiter

    def __enter__(self) -> ERCOTBase:
        """Enter a context manager for the client."""
        self._entered_client = self._get_client()
        self._entered_client.__enter__()
        return self

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        """Exit a context manager for the client."""
        if hasattr(self, "_entered_client") and self._entered_client is not None:
            self._entered_client.__exit__(*args, **kwargs)
            self._entered_client = None

    async def __aenter__(self) -> ERCOTBase:
        """Enter an async context manager for the client."""
        self._entered_client = self._get_client()
        await self._entered_client.__aenter__()
        return self

    async def __aexit__(self, *args: Any, **kwargs: Any) -> None:
        """Exit an async context manager for the client."""
        if hasattr(self, "_entered_client") and self._entered_client is not None:
            await self._entered_client.__aexit__(*args, **kwargs)
            self._entered_client = None

    def _handle_api_error(self, error: Exception, endpoint: str | None = None) -> None:
        """Handle API errors and convert them to GridError types.

        Args:
            error: The exception that occurred
            endpoint: Optional endpoint that was being called

        Raises:
            GridError: Appropriate GridError subclass
        """
        if isinstance(error, UnexpectedStatus):
            raise GridAPIError(
                f"ERCOT API returned unexpected status {error.status_code}",
                status_code=error.status_code,
                response_body=error.content,
                endpoint=endpoint,
            ) from error

        if isinstance(error, TimeoutError):
            raise GridTimeoutError(
                "Request to ERCOT API timed out",
                timeout=self.timeout,
            ) from error

        # Re-raise GridErrors as-is
        if isinstance(error, GridError):
            raise error

        # Wrap other errors
        raise GridAPIError(
            f"Unexpected error calling ERCOT API: {error}",
            endpoint=endpoint,
        ) from error

    def _extract_response_data(self, response: Any) -> dict[str, Any]:
        """Extract data from API response.

        Handles different response types (Report, Product, etc.) and extracts
        the underlying data structure.

        Args:
            response: The API response object

        Returns:
            Dictionary containing the extracted data
        """
        if response is None:
            return {}

        # First priority: Use to_dict() if available (handles Report, Product, etc.)
        if hasattr(response, "to_dict"):
            try:
                result = response.to_dict()
                if isinstance(result, dict):
                    return result
            except Exception:
                pass

        # Handle Report objects - extract data field if present
        if hasattr(response, "data") and response.data is not None:
            # If data has to_dict, use it
            if hasattr(response.data, "to_dict"):
                try:
                    data_dict = response.data.to_dict()
                    if isinstance(data_dict, dict):
                        return data_dict
                except Exception:
                    pass
            # Otherwise try to get additional_properties from data
            if hasattr(response.data, "additional_properties"):
                props = response.data.additional_properties
                if isinstance(props, dict):
                    return props

        # Handle objects with additional_properties at top level
        if hasattr(response, "additional_properties"):
            props = response.additional_properties
            if isinstance(props, dict):
                return props

        # Fallback: try to convert to dict
        if isinstance(response, dict):
            return response

        return {}

    def _call_with_retry(
        self,
        func: Any,  # pyercot endpoint module
        endpoint_name: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Call an endpoint function with retry logic using tenacity.

        Args:
            func: The function to call
            endpoint_name: Name of the endpoint for error reporting
            **kwargs: Arguments to pass to the function

        Returns:
            Dictionary containing the response data

        Raises:
            GridRetryExhaustedError: If all retry attempts fail
            GridAPIError: If a non-retryable error occurs
        """

        @retry(
            stop=stop_after_attempt(self.max_retries + 1),
            wait=wait_exponential(
                multiplier=1,
                min=self.retry_min_wait,
                max=self.retry_max_wait,
            ),
            retry=retry_if_exception(_is_retryable_error),
            reraise=False,
        )
        def _execute() -> dict[str, Any]:
            return self._call_endpoint_raw(func, endpoint_name, **kwargs)

        try:
            return _execute()
        except RetryError as e:
            # Extract the last exception from the retry chain
            last_exception = e.last_attempt.exception()
            status_code = None
            response_body = None
            if isinstance(last_exception, GridAPIError):
                status_code = last_exception.status_code
                response_body = last_exception.response_body

            raise GridRetryExhaustedError(
                f"All {self.max_retries + 1} retry attempts exhausted for {endpoint_name}",
                status_code=status_code,
                response_body=response_body,
                endpoint=endpoint_name,
                attempts=self.max_retries + 1,
            ) from last_exception

    def _supports_pagination(self, endpoint_module: Any) -> bool:
        """Check if an endpoint module's sync function supports pagination.

        Args:
            endpoint_module: The endpoint module containing a sync function

        Returns:
            True if the endpoint accepts 'page' and 'size' parameters, False otherwise
        """
        try:
            # endpoint_module is a module, the actual function is .sync
            func = getattr(endpoint_module, "sync", endpoint_module)
            sig = inspect.signature(func)
            params = sig.parameters
            return "page" in params and "size" in params
        except (ValueError, TypeError):
            # If we can't inspect the signature, assume no pagination
            return False

    def _returns_report_model(self, endpoint_module: Any) -> bool:
        """Check if an endpoint module's sync function returns a Report model.

        Args:
            endpoint_module: The endpoint module containing a sync function

        Returns:
            True if the endpoint returns a Report model, False otherwise
        """
        try:
            # endpoint_module is a module, the actual function is .sync
            func = getattr(endpoint_module, "sync", endpoint_module)
            sig = inspect.signature(func)
            return_annotation = sig.return_annotation
            # Check if return type annotation mentions Report
            if return_annotation:
                return_str = str(return_annotation)
                # Report endpoints typically return Exception_ | Report | None
                # or Response[Exception_ | Report]
                return "Report" in return_str and "Product" not in return_str
        except (ValueError, TypeError, AttributeError):
            pass
        # Default: assume it's a Report endpoint if we can't determine
        # This is safer for existing endpoints
        return True

    def _fetch_all_pages(
        self,
        endpoint_func: Callable[..., Any],
        endpoint_name: str,
        **kwargs: Any,
    ) -> tuple[list[list[Any]], list[dict[str, Any]]]:
        """Fetch all pages of data from a paginated endpoint.

        Uses concurrent requests to fetch pages in parallel for better performance.

        Args:
            endpoint_func: The endpoint function to call (should be the module, not .sync)
            endpoint_name: Name of the endpoint for error reporting
            **kwargs: Arguments to pass to the endpoint

        Returns:
            Tuple of (all_data_rows, all_fields) from all pages
        """
        all_data: list[list[Any]] = []
        all_fields: list[dict[str, Any]] = []

        # First request to get total pages
        # Allow kwargs to override default page_size
        size = kwargs.pop("size", self.page_size)
        first_response = self._call_with_retry(
            endpoint_func,
            endpoint_name,
            page=1,
            size=size,
            **kwargs,
        )

        # Extract data and fields from first page
        # Note: pyercot may return data as {"records": [...]} or [...]
        raw_data = first_response.get("data", [])
        if isinstance(raw_data, dict):
            data = raw_data.get("records", [])
        else:
            data = raw_data
        fields = first_response.get("fields", [])
        if data:
            all_data.extend(data)
        if fields:
            all_fields = fields

        # Get total pages from meta
        meta = first_response.get("_meta", {})
        total_pages = meta.get("totalPages", 1)

        if total_pages <= 1:
            return all_data, all_fields

        # Fetch remaining pages in parallel
        def fetch_page(page: int) -> list[Any]:
            response = self._call_with_retry(
                endpoint_func,
                endpoint_name,
                page=page,
                size=size,
                **kwargs,
            )
            raw = response.get("data", [])
            if isinstance(raw, dict):
                return raw.get("records", [])
            return raw

        with ThreadPoolExecutor(max_workers=self.max_concurrent_requests) as executor:
            # Submit all remaining page requests
            futures = {
                executor.submit(fetch_page, page): page
                for page in range(2, total_pages + 1)
            }

            # Collect results as they complete
            for future in as_completed(futures):
                page_data = future.result()
                if page_data:
                    all_data.extend(page_data)

        return all_data, all_fields

    def _call_endpoint_raw(
        self,
        endpoint_module: Any,
        endpoint_name: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Call an endpoint without retry logic and return raw response.

        Args:
            endpoint_module: The pyercot endpoint module
            endpoint_name: Name of the endpoint for error reporting
            **kwargs: Arguments to pass to the endpoint

        Returns:
            Dictionary containing the response data
        """
        try:
            # Apply rate limiting before making the request
            rate_limiter = self._get_rate_limiter()
            if rate_limiter is not None:
                rate_limiter.acquire()

            client = self._get_client()
            response = endpoint_module.sync(client=client, **kwargs)

            # Handle error responses
            if response is None:
                return {}

            # Check for API error response (status_code must be int, not MagicMock)
            status_code = getattr(response, "status_code", None)
            if isinstance(status_code, int):
                if status_code == 429:
                    raise GridRateLimitError(
                        "Rate limited by ERCOT API",
                        endpoint=endpoint_name,
                    )
                if status_code >= 400:
                    body = getattr(response, "content", None) or getattr(
                        response, "text", None
                    )
                    raise GridAPIError(
                        f"ERCOT API returned status {status_code}",
                        status_code=status_code,
                        response_body=body,
                        endpoint=endpoint_name,
                    )

            return self._extract_response_data(response)

        except Exception as e:
            if isinstance(e, GridError):
                raise
            self._handle_api_error(e, endpoint=endpoint_name)
            return {}  # Never reached, but helps type checker

    def _call_endpoint(
        self,
        endpoint_module: Any,
        endpoint_name: str,
        fetch_all: bool = True,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """Call an endpoint with retry and pagination, return DataFrame.

        This is the main method for calling endpoints. It automatically handles:
        - Retry with exponential backoff
        - Pagination (fetching all pages)
        - DataFrame conversion

        Args:
            endpoint_module: The pyercot endpoint module
            endpoint_name: Name of the endpoint for error reporting
            fetch_all: If True, fetch all pages. If False, only fetch first page.
            **kwargs: Arguments to pass to the endpoint

        Returns:
            DataFrame containing the response data
        """
        if fetch_all and self._supports_pagination(endpoint_module):
            all_data, fields = self._fetch_all_pages(
                endpoint_module, endpoint_name, **kwargs
            )
            return self._to_dataframe(all_data, fields)
        else:
            response = self._call_with_retry(endpoint_module, endpoint_name, **kwargs)
            raw_data = response.get("data", [])
            if isinstance(raw_data, dict):
                data = raw_data.get("records", [])
            else:
                data = raw_data
            fields = response.get("fields", [])
            return self._to_dataframe(data, fields)

    def _to_dataframe(
        self,
        data: list[list[Any]],
        fields: list[dict[str, Any]],
    ) -> pd.DataFrame:
        """Convert API response data to a pandas DataFrame.

        Args:
            data: List of data rows (each row is a list of values)
            fields: List of field definitions with 'name' and 'label' keys

        Returns:
            DataFrame with properly labeled columns
        """
        if not fields:
            # No field definitions - use numeric columns if data exists
            if data:
                return pd.DataFrame(data)
            return pd.DataFrame()

        # Extract column names - prefer label over name for readability
        columns = [
            f.get("label", f.get("name", f"col_{i}")) for i, f in enumerate(fields)
        ]

        if not data:
            # Return empty DataFrame with columns preserved
            return pd.DataFrame(columns=columns)

        df = pd.DataFrame(data, columns=columns)
        return df

    def _should_use_historical(self, date: pd.Timestamp) -> bool:
        """Check if a date should use the historical archive API.

        Args:
            date: Date to check

        Returns:
            True if date is older than HISTORICAL_THRESHOLD_DAYS
        """
        threshold = pd.Timestamp.now(tz=ERCOT_TIMEZONE) - pd.Timedelta(
            days=HISTORICAL_THRESHOLD_DAYS
        )
        return date < threshold

    def _needs_historical(
        self, date: pd.Timestamp, data_type: str = "real_time"
    ) -> bool:
        """Check if date requires historical archive API.

        Uses LIVE_API_RETENTION to determine if the requested date is older
        than what's available on the live API.

        Args:
            date: Date to check
            data_type: Type of data - "real_time", "day_ahead", "forecast", "load"

        Returns:
            True if date is older than live API retention for this data type
        """
        from ..constants.ercot import LIVE_API_RETENTION

        retention_days = LIVE_API_RETENTION.get(
            data_type, LIVE_API_RETENTION["default"]
        )
        cutoff = pd.Timestamp.now(tz=ERCOT_TIMEZONE).normalize() - pd.Timedelta(
            days=retention_days - 1
        )
        return date.normalize() < cutoff

    def _get_archive(self) -> ERCOTArchive:
        """Get or create the historical archive client."""
        if not hasattr(self, "_archive") or self._archive is None:
            from .archive import ERCOTArchive

            self._archive = ERCOTArchive(ercot=self)
        return self._archive

    def _call_endpoint_model(
        self,
        endpoint_module: Any,
        endpoint_name: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Call an endpoint that returns a model (not Report data).

        Used for endpoints like get_product, get_version that return
        different response structures.

        Args:
            endpoint_module: The pyercot endpoint module
            endpoint_name: Name of the endpoint for error reporting
            **kwargs: Arguments to pass to the endpoint

        Returns:
            Dictionary containing the response data
        """
        return self._call_with_retry(endpoint_module, endpoint_name, **kwargs)

    def _products_to_dataframe(self, response: Any) -> pd.DataFrame:
        """Convert products list response to DataFrame.

        The ERCOT products endpoint can return multiple shapes depending on the
        upstream client (pyercot) and API format:
        - Plain dict: {"products": [...]}
        - HAL dict: {"_embedded": {"products": [...]}, ...}
        - Nested HAL in to_dict(): {"additional_properties": {"_embedded": {"products": [...]}}}
        - Raw list: [...]
        """

        def _as_products_list(value: Any) -> list[dict[str, Any]]:
            if not value:
                return []
            if isinstance(value, list):
                # Best effort: only keep mapping-like entries
                return [item for item in value if isinstance(item, dict)]
            return []

        if response is None:
            return pd.DataFrame()

        # Some clients can return a raw list response
        if isinstance(response, list):
            products = _as_products_list(response)
            return pd.DataFrame(products) if products else pd.DataFrame()

        if not isinstance(response, dict):
            return pd.DataFrame()

        # Common shape: {"products": [...]}
        products = _as_products_list(response.get("products"))
        if products:
            return pd.DataFrame(products)

        # HAL shape: {"_embedded": {"products": [...]}}
        embedded = response.get("_embedded")
        if isinstance(embedded, dict):
            products = _as_products_list(embedded.get("products"))
            if products:
                return pd.DataFrame(products)

        # Some model to_dict() outputs store HAL payload under additional_properties
        additional_properties = response.get("additional_properties")
        if isinstance(additional_properties, dict):
            products = _as_products_list(additional_properties.get("products"))
            if products:
                return pd.DataFrame(products)
            embedded = additional_properties.get("_embedded")
            if isinstance(embedded, dict):
                products = _as_products_list(embedded.get("products"))
                if products:
                    return pd.DataFrame(products)

        return pd.DataFrame()

    def _model_to_dataframe(self, response: dict[str, Any]) -> pd.DataFrame:
        """Convert a single model response to a one-row DataFrame."""
        if not response:
            return pd.DataFrame()
        return pd.DataFrame([response])

    def _product_history_to_dataframe(self, response: dict[str, Any]) -> pd.DataFrame:
        """Convert product history response to DataFrame."""
        archives = response.get("archives", [])
        if not archives:
            return pd.DataFrame()
        return pd.DataFrame(archives)

    def make_request(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        method: str = "GET",
        parse_json: bool = True,
    ) -> dict[str, Any] | bytes:
        """Make an authenticated request to the ERCOT API.

        Args:
            url: Request URL
            params: Query parameters (GET) or body (POST)
            method: HTTP method
            parse_json: If True, parse response as JSON

        Returns:
            Parsed JSON dict or raw bytes
        """

        try:
            client = self._get_client().get_httpx_client()

            request = client.build_request(
                method=method,
                url=url,
                params=params if method == "GET" else None,
                json=params if method == "POST" else None,
            )

            response = client.send(request)

            if response.status_code == 429:
                raise GridRetryExhaustedError(
                    "Rate limited by ERCOT API",
                    status_code=429,
                    endpoint=url,
                )

            if response.status_code != 200:
                raise GridAPIError(
                    f"ERCOT API returned {response.status_code}",
                    status_code=response.status_code,
                    response_body=response.text[:500],
                    endpoint=url,
                )

            if parse_json:
                return response.json()
            return response.content

        except httpx.TimeoutException as e:
            raise GridAPIError(f"Request timed out: {e}", endpoint=url) from e
        except httpx.RequestError as e:
            raise GridAPIError(f"Request failed: {e}", endpoint=url) from e
