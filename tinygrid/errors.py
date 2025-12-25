"""Custom error types for the Tiny Grid SDK"""

from typing import Any


class GridError(Exception):
    """Base exception for all Tiny Grid SDK errors"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        """Initialize a GridError.

        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class GridTimeoutError(GridError):
    """Raised when a request to the grid API times out"""

    def __init__(self, message: str = "Request to grid API timed out", timeout: float | None = None):
        """Initialize a GridTimeoutError.

        Args:
            message: Human-readable error message
            timeout: The timeout value that was exceeded (in seconds)
        """
        details = {"timeout": timeout} if timeout is not None else {}
        super().__init__(message, details)
        self.timeout = timeout


class GridAPIError(GridError):
    """Raised when the grid API returns an error response"""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: str | bytes | None = None,
        endpoint: str | None = None,
    ):
        """Initialize a GridAPIError.

        Args:
            message: Human-readable error message
            status_code: HTTP status code from the API response
            response_body: Response body from the API
            endpoint: The endpoint that was called
        """
        details: dict[str, Any] = {}
        if status_code is not None:
            details["status_code"] = status_code
        if response_body is not None:
            details["response_body"] = response_body.decode("utf-8") if isinstance(response_body, bytes) else response_body
        if endpoint is not None:
            details["endpoint"] = endpoint

        super().__init__(message, details)
        self.status_code = status_code
        self.response_body = response_body
        self.endpoint = endpoint


class GridAuthenticationError(GridAPIError):
    """Raised when authentication fails"""

    def __init__(self, message: str = "Authentication failed", **kwargs):
        """Initialize a GridAuthenticationError.

        Args:
            message: Human-readable error message
            **kwargs: Additional arguments passed to GridAPIError
        """
        super().__init__(message, **kwargs)


class GridRateLimitError(GridAPIError):
    """Raised when the API rate limit is exceeded"""

    def __init__(
        self,
        message: str = "API rate limit exceeded",
        status_code: int | None = None,
        response_body: str | bytes | None = None,
        endpoint: str | None = None,
        retry_after: int | None = None,
    ):
        """Initialize a GridRateLimitError.

        Args:
            message: Human-readable error message
            status_code: HTTP status code from the API response
            response_body: Response body from the API
            endpoint: The endpoint that was called
            retry_after: Number of seconds to wait before retrying
        """
        super().__init__(message, status_code=status_code, response_body=response_body, endpoint=endpoint)
        self.retry_after = retry_after
        if retry_after is not None:
            self.details["retry_after"] = retry_after

