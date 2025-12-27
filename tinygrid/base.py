"""Base classes for ISO clients"""

from abc import ABC, abstractmethod

from attrs import define, field


@define
class BaseISOClient(ABC):
    """Base class for all ISO clients in the Tiny Grid SDK.

    This class provides common functionality and defines the interface that all
    ISO-specific clients must implement.
    """

    base_url: str = field()
    timeout: float | None = field(default=30.0, kw_only=True)
    verify_ssl: bool = field(default=True, kw_only=True)
    raise_on_error: bool = field(default=True, kw_only=True)

    @property
    @abstractmethod
    def iso_name(self) -> str:
        """Return the name of the ISO (e.g., 'ERCOT', 'CAISO')."""
        ...

    def __repr__(self) -> str:
        """Return a string representation of the client."""
        return f"{self.__class__.__name__}(base_url={self.base_url!r})"

    def _normalize_date(self, date: str) -> str:
        """Normalize date strings to ISO 8601 format.

        Args:
            date: Date string in various formats

        Returns:
            Normalized date string in YYYY-MM-DD format
        """
        # Basic validation - can be extended for more formats
        if not isinstance(date, str):
            raise ValueError(f"Date must be a string, got {type(date)}")
        return date.strip()

    def _normalize_datetime(self, datetime: str) -> str:
        """Normalize datetime strings to ISO 8601 format.

        Args:
            datetime: Datetime string in various formats

        Returns:
            Normalized datetime string
        """
        if not isinstance(datetime, str):
            raise ValueError(f"Datetime must be a string, got {type(datetime)}")
        return datetime.strip()

    def _handle_error(
        self, error: Exception, endpoint: str | None = None
    ) -> None:
        """Handle errors according to the client's error handling policy.

        Args:
            error: The exception that occurred
            endpoint: Optional endpoint that was being called

        Raises:
            GridError: If raise_on_error is True
        """
        if self.raise_on_error:
            from .errors import GridAPIError, GridError, GridTimeoutError

            if isinstance(error, GridError):
                raise error

            # Convert common HTTP errors to GridError types
            if isinstance(error, TimeoutError):
                raise GridTimeoutError(
                    f"Request timed out: {error}", timeout=self.timeout
                ) from error

            # For other errors, wrap in GridAPIError
            raise GridAPIError(
                f"Unexpected error: {error}",
                endpoint=endpoint,
            ) from error
