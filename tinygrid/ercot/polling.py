"""Polling utilities for real-time ERCOT data access.

ERCOT does not provide WebSocket or streaming endpoints. For real-time
data access, polling is required. This module provides utilities to
efficiently poll the ERCOT API with:

- Rate limit awareness (30 requests/minute)
- Configurable poll intervals
- Exponential backoff on errors
- Callback-based or generator patterns
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Generator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar

import pandas as pd

from ..errors import GridError

if TYPE_CHECKING:
    from . import ERCOT

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Minimum poll interval in seconds (to respect rate limits)
MIN_POLL_INTERVAL = 2.0  # ~30 requests per minute

# Default poll interval in seconds
DEFAULT_POLL_INTERVAL = 60.0  # 1 minute

# Maximum consecutive errors before stopping
MAX_CONSECUTIVE_ERRORS = 5


@dataclass
class PollResult:
    """Result of a single poll iteration."""

    data: pd.DataFrame | None
    timestamp: pd.Timestamp
    success: bool
    error: Exception | None = None
    iteration: int = 0


class ERCOTPoller:
    """Utility for polling ERCOT data at regular intervals.

    Provides a convenient way to continuously fetch data from the ERCOT API
    with proper rate limiting and error handling.

    Args:
        client: ERCOT client instance
        interval: Poll interval in seconds. Minimum 2 seconds to respect rate limits.
        max_errors: Maximum consecutive errors before stopping. Default 5.
        backoff_factor: Multiplier for exponential backoff on errors. Default 2.0.
        max_backoff: Maximum backoff delay in seconds. Default 300.

    Example:
        ```python
        from tinygrid import ERCOT
        from tinygrid.ercot.polling import ERCOTPoller

        ercot = ERCOT(auth=auth)
        poller = ERCOTPoller(client=ercot, interval=60)

        # Using callback pattern
        def handle_data(result):
            if result.success:
                print(f"Got {len(result.data)} rows at {result.timestamp}")
            else:
                print(f"Error: {result.error}")

        poller.poll(
            method=ercot.get_spp,
            callback=handle_data,
            max_iterations=10,
        )

        # Using generator pattern
        for result in poller.poll_iter(method=ercot.get_spp, max_iterations=10):
            if result.success:
                process_data(result.data)
        ```
    """

    def __init__(
        self,
        client: ERCOT,
        interval: float = DEFAULT_POLL_INTERVAL,
        max_errors: int = MAX_CONSECUTIVE_ERRORS,
        backoff_factor: float = 2.0,
        max_backoff: float = 300.0,
    ) -> None:
        """Initialize the poller.

        Args:
            client: ERCOT client instance
            interval: Poll interval in seconds (minimum 2 seconds)
            max_errors: Maximum consecutive errors before stopping
            backoff_factor: Multiplier for exponential backoff
            max_backoff: Maximum backoff delay in seconds
        """
        self.client = client
        self.interval = max(interval, MIN_POLL_INTERVAL)
        self.max_errors = max_errors
        self.backoff_factor = backoff_factor
        self.max_backoff = max_backoff

        self._running = False
        self._consecutive_errors = 0
        self._current_backoff = 0.0

    def poll(
        self,
        method: Callable[..., pd.DataFrame],
        callback: Callable[[PollResult], Any],
        max_iterations: int | None = None,
        **kwargs: Any,
    ) -> None:
        """Poll an ERCOT method continuously with a callback.

        Args:
            method: ERCOT client method to call (e.g., client.get_spp)
            callback: Function to call with each PollResult
            max_iterations: Maximum number of iterations (None = infinite)
            **kwargs: Arguments to pass to the method

        Example:
            ```python
            def handle_spp(result):
                if result.success:
                    df = result.data
                    print(f"Latest SPP: {df['Price'].mean():.2f}")

            poller.poll(
                method=ercot.get_spp,
                callback=handle_spp,
                market=Market.REAL_TIME_15_MIN,
            )
            ```
        """
        self._running = True
        iteration = 0

        try:
            while self._running:
                if max_iterations is not None and iteration >= max_iterations:
                    break

                result = self._poll_once(method, iteration, **kwargs)
                callback(result)

                if not result.success:
                    self._handle_error()
                else:
                    self._reset_backoff()

                iteration += 1

                # Check if we should stop due to too many errors
                if self._consecutive_errors >= self.max_errors:
                    logger.error(
                        f"Stopping poller after {self.max_errors} consecutive errors"
                    )
                    break

                # Wait for next poll
                wait_time = self.interval + self._current_backoff
                time.sleep(wait_time)

        finally:
            self._running = False

    def poll_iter(
        self,
        method: Callable[..., pd.DataFrame],
        max_iterations: int | None = None,
        **kwargs: Any,
    ) -> Generator[PollResult, None, None]:
        """Poll an ERCOT method as a generator.

        Yields PollResult objects for each iteration. Use this pattern when
        you want more control over the polling loop.

        Args:
            method: ERCOT client method to call
            max_iterations: Maximum number of iterations (None = infinite)
            **kwargs: Arguments to pass to the method

        Yields:
            PollResult for each poll iteration

        Example:
            ```python
            for result in poller.poll_iter(method=ercot.get_spp, max_iterations=5):
                if result.success:
                    print(f"Iteration {result.iteration}: {len(result.data)} rows")
                if some_condition:
                    break  # Can exit early
            ```
        """
        self._running = True
        iteration = 0

        try:
            while self._running:
                if max_iterations is not None and iteration >= max_iterations:
                    break

                result = self._poll_once(method, iteration, **kwargs)
                yield result

                if not result.success:
                    self._handle_error()
                else:
                    self._reset_backoff()

                iteration += 1

                if self._consecutive_errors >= self.max_errors:
                    logger.error(
                        f"Stopping poller after {self.max_errors} consecutive errors"
                    )
                    break

                wait_time = self.interval + self._current_backoff
                time.sleep(wait_time)

        finally:
            self._running = False

    def stop(self) -> None:
        """Stop the poller gracefully."""
        self._running = False

    def _poll_once(
        self,
        method: Callable[..., pd.DataFrame],
        iteration: int,
        **kwargs: Any,
    ) -> PollResult:
        """Execute a single poll iteration."""
        timestamp = pd.Timestamp.now(tz="US/Central")

        try:
            # For polling, we typically want the most recent data
            # If start/end not provided, default to "today"
            if "start" not in kwargs:
                kwargs["start"] = "today"

            data = method(**kwargs)

            return PollResult(
                data=data,
                timestamp=timestamp,
                success=True,
                iteration=iteration,
            )

        except GridError as e:
            logger.warning(f"Poll iteration {iteration} failed: {e}")
            return PollResult(
                data=None,
                timestamp=timestamp,
                success=False,
                error=e,
                iteration=iteration,
            )
        except Exception as e:
            logger.error(f"Unexpected error in poll iteration {iteration}: {e}")
            return PollResult(
                data=None,
                timestamp=timestamp,
                success=False,
                error=e,
                iteration=iteration,
            )

    def _handle_error(self) -> None:
        """Handle a poll error by incrementing backoff."""
        self._consecutive_errors += 1
        self._current_backoff = min(
            self._current_backoff * self.backoff_factor + self.interval,
            self.max_backoff,
        )
        logger.debug(
            f"Poll error {self._consecutive_errors}, backoff: {self._current_backoff:.1f}s"
        )

    def _reset_backoff(self) -> None:
        """Reset error tracking after successful poll."""
        self._consecutive_errors = 0
        self._current_backoff = 0.0


def poll_latest(
    client: ERCOT,
    method: Callable[..., pd.DataFrame],
    interval: float = DEFAULT_POLL_INTERVAL,
    max_iterations: int | None = None,
    **kwargs: Any,
) -> Generator[pd.DataFrame, None, None]:
    """Simple generator for polling latest data.

    A convenience function for simple polling use cases.

    Args:
        client: ERCOT client instance
        method: Method to poll (e.g., client.get_spp)
        interval: Poll interval in seconds
        max_iterations: Maximum iterations (None = infinite)
        **kwargs: Arguments to pass to the method

    Yields:
        DataFrame for each successful poll (skips failures)

    Example:
        ```python
        from tinygrid import ERCOT
        from tinygrid.ercot.polling import poll_latest

        ercot = ERCOT(auth=auth)

        for df in poll_latest(ercot, ercot.get_spp, interval=60, max_iterations=10):
            print(f"Got {len(df)} rows")
            # Process the data...
        ```
    """
    poller = ERCOTPoller(client=client, interval=interval)

    for result in poller.poll_iter(
        method=method, max_iterations=max_iterations, **kwargs
    ):
        if result.success and result.data is not None:
            yield result.data
