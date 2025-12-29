"""Rate limiting utilities for API requests.

ERCOT's Public API has a rate limit of 30 requests per minute. This module
provides a token bucket rate limiter to proactively enforce this limit and
avoid 429 errors.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from collections.abc import Callable
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

# Default rate limit for ERCOT API (30 requests per minute)
ERCOT_REQUESTS_PER_MINUTE = 30
ERCOT_MIN_INTERVAL = 60.0 / ERCOT_REQUESTS_PER_MINUTE  # ~2 seconds

T = TypeVar("T")


class RateLimiter:
    """Thread-safe token bucket rate limiter for API requests.

    Implements a token bucket algorithm where:
    - Tokens are added at a fixed rate (requests_per_minute / 60 per second)
    - Each request consumes one token
    - If no tokens are available, the request blocks until one is available

    This proactively prevents rate limit errors (HTTP 429) by throttling
    requests before they hit the API.

    Args:
        requests_per_minute: Maximum requests allowed per minute. Defaults to 30.
        burst_size: Maximum tokens that can accumulate (burst capacity).
            Defaults to requests_per_minute (allows full burst at start).

    Example:
        ```python
        from tinygrid.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(requests_per_minute=30)

        # Use as context manager
        with limiter:
            response = make_api_request()

        # Or call acquire/release manually
        limiter.acquire()
        try:
            response = make_api_request()
        finally:
            limiter.release()
        ```
    """

    def __init__(
        self,
        requests_per_minute: float = ERCOT_REQUESTS_PER_MINUTE,
        burst_size: float | None = None,
    ) -> None:
        """Initialize the rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute
            burst_size: Maximum burst capacity (tokens). Defaults to requests_per_minute.
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size if burst_size is not None else requests_per_minute

        # Token bucket state
        self._tokens = self.burst_size
        self._last_update = time.monotonic()
        self._lock = threading.Lock()

        # Calculate refill rate (tokens per second)
        self._refill_rate = requests_per_minute / 60.0

    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_update
        self._tokens = min(self.burst_size, self._tokens + elapsed * self._refill_rate)
        self._last_update = now

    def acquire(self, timeout: float | None = None) -> bool:
        """Acquire a token, blocking if necessary.

        Args:
            timeout: Maximum time to wait for a token (seconds). None means wait forever.

        Returns:
            True if token was acquired, False if timeout occurred
        """
        deadline = None if timeout is None else time.monotonic() + timeout

        while True:
            with self._lock:
                self._refill_tokens()

                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return True

                # Calculate wait time for next token
                wait_time = (1.0 - self._tokens) / self._refill_rate

            # Check timeout
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                wait_time = min(wait_time, remaining)

            # Wait for token refill
            logger.debug(f"Rate limiter: waiting {wait_time:.2f}s for token")
            time.sleep(wait_time)

    def release(self) -> None:
        """Release is a no-op for token bucket (tokens are consumed, not borrowed)."""
        pass

    def __enter__(self) -> RateLimiter:
        """Context manager entry - acquires a token."""
        self.acquire()
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.release()

    @property
    def available_tokens(self) -> float:
        """Get the current number of available tokens."""
        with self._lock:
            self._refill_tokens()
            return self._tokens

    @property
    def min_interval(self) -> float:
        """Minimum interval between requests in seconds."""
        return 60.0 / self.requests_per_minute

    def reset(self) -> None:
        """Reset the rate limiter to full capacity."""
        with self._lock:
            self._tokens = self.burst_size
            self._last_update = time.monotonic()


class AsyncRateLimiter:
    """Async-compatible token bucket rate limiter.

    Same algorithm as RateLimiter but uses asyncio for non-blocking waits.

    Args:
        requests_per_minute: Maximum requests allowed per minute
        burst_size: Maximum burst capacity

    Example:
        ```python
        from tinygrid.utils.rate_limiter import AsyncRateLimiter

        limiter = AsyncRateLimiter(requests_per_minute=30)

        async def fetch_data():
            async with limiter:
                return await make_api_request()
        ```
    """

    def __init__(
        self,
        requests_per_minute: float = ERCOT_REQUESTS_PER_MINUTE,
        burst_size: float | None = None,
    ) -> None:
        """Initialize the async rate limiter."""
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size if burst_size is not None else requests_per_minute

        self._tokens = self.burst_size
        self._last_update = time.monotonic()
        self._lock = asyncio.Lock()
        self._refill_rate = requests_per_minute / 60.0

    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_update
        self._tokens = min(self.burst_size, self._tokens + elapsed * self._refill_rate)
        self._last_update = now

    async def acquire(self, timeout: float | None = None) -> bool:
        """Acquire a token, awaiting if necessary.

        Args:
            timeout: Maximum time to wait for a token (seconds)

        Returns:
            True if token was acquired, False if timeout occurred
        """
        deadline = None if timeout is None else time.monotonic() + timeout

        while True:
            async with self._lock:
                self._refill_tokens()

                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return True

                wait_time = (1.0 - self._tokens) / self._refill_rate

            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                wait_time = min(wait_time, remaining)

            logger.debug(f"Async rate limiter: waiting {wait_time:.2f}s for token")
            await asyncio.sleep(wait_time)

    async def release(self) -> None:
        """Release is a no-op for token bucket."""
        pass

    async def __aenter__(self) -> AsyncRateLimiter:
        """Async context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.release()

    @property
    def available_tokens(self) -> float:
        """Get the current number of available tokens (sync access)."""
        self._refill_tokens()
        return self._tokens

    def reset(self) -> None:
        """Reset the rate limiter to full capacity."""
        self._tokens = self.burst_size
        self._last_update = time.monotonic()


def rate_limited(
    limiter: RateLimiter | None = None,
    requests_per_minute: float = ERCOT_REQUESTS_PER_MINUTE,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to apply rate limiting to a function.

    Args:
        limiter: Existing RateLimiter to use. If None, creates a new one.
        requests_per_minute: Rate limit if creating new limiter

    Returns:
        Decorated function that respects rate limits

    Example:
        ```python
        from tinygrid.utils.rate_limiter import rate_limited

        @rate_limited(requests_per_minute=30)
        def make_api_call(endpoint: str):
            return requests.get(endpoint)
        ```
    """
    _limiter = limiter or RateLimiter(requests_per_minute=requests_per_minute)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            with _limiter:
                return func(*args, **kwargs)

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    return decorator
