"""Date parsing and manipulation utilities."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

import pandas as pd

from ..constants.ercot import ERCOT_TIMEZONE

if TYPE_CHECKING:
    from collections.abc import Iterator

# Type alias for date-like inputs
DateLike = str | pd.Timestamp | datetime | date | None


def parse_date(
    value: DateLike,
    tz: str = ERCOT_TIMEZONE,
    default: str = "today",
) -> pd.Timestamp:
    """Parse a date value with support for special keywords.

    Args:
        value: Date input - can be:
            - "today" or "latest": Current date
            - "yesterday": Previous day
            - ISO format string: "2024-01-15"
            - pd.Timestamp or datetime object
            - None: Uses default
        tz: Timezone to localize to (default: US/Central)
        default: Default value if None ("today" or "yesterday")

    Returns:
        Timezone-aware pd.Timestamp normalized to midnight

    Examples:
        >>> parse_date("today")
        Timestamp('2024-12-27 00:00:00-0600', tz='US/Central')
        >>> parse_date("2024-01-15")
        Timestamp('2024-01-15 00:00:00-0600', tz='US/Central')
    """
    if value is None:
        value = default

    now = pd.Timestamp.now(tz=tz)

    # Handle special keywords
    if isinstance(value, str):
        value_lower = value.lower().strip()
        if value_lower in ("today", "latest"):
            return now.normalize()
        if value_lower == "yesterday":
            return (now - pd.Timedelta(days=1)).normalize()

    # Parse string or convert timestamp
    ts = pd.Timestamp(value)

    # Localize if naive
    ts = ts.tz_localize(tz) if ts.tz is None else ts.tz_convert(tz)

    return ts.normalize()


def parse_date_range(
    start: DateLike,
    end: DateLike = None,
    tz: str = ERCOT_TIMEZONE,
    days_forward: int = 1,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Parse a date range with sensible defaults.

    Args:
        start: Start date (supports "today", "latest", "yesterday", ISO strings)
        end: End date. If None, defaults to start + days_forward
        tz: Timezone to use
        days_forward: Days to add to start if end is None

    Returns:
        Tuple of (start_timestamp, end_timestamp)

    Examples:
        >>> parse_date_range("2024-01-15")
        (Timestamp('2024-01-15...'), Timestamp('2024-01-16...'))
        >>> parse_date_range("2024-01-15", "2024-01-20")
        (Timestamp('2024-01-15...'), Timestamp('2024-01-20...'))
    """
    start_ts = parse_date(start, tz=tz, default="today")
    if end is None:
        end_ts_temp = start_ts + pd.Timedelta(days=days_forward)
    else:
        end_ts_temp = parse_date(end, tz=tz, default="today")

    # Type assert: pandas operations on valid timestamps don't produce NaT
    assert isinstance(end_ts_temp, pd.Timestamp) and not pd.isna(end_ts_temp)
    end_ts: pd.Timestamp = end_ts_temp

    # Ensure end is after start
    if end_ts <= start_ts:
        end_ts_adjusted = start_ts + pd.Timedelta(days=days_forward)
        assert isinstance(end_ts_adjusted, pd.Timestamp) and not pd.isna(
            end_ts_adjusted
        )
        end_ts = end_ts_adjusted

    return start_ts, end_ts


def date_chunks(
    start: pd.Timestamp,
    end: pd.Timestamp,
    freq: str = "1D",
) -> Iterator[tuple[pd.Timestamp, pd.Timestamp]]:
    """Split a date range into chunks.

    Useful for parallel fetching or avoiding API limits.

    Args:
        start: Start timestamp
        end: End timestamp
        freq: Chunk frequency (e.g., "1D", "7D", "1H")

    Yields:
        Tuples of (chunk_start, chunk_end)

    Examples:
        >>> list(date_chunks(start, end, "7D"))
        [(start, start+7d), (start+7d, start+14d), ...]
    """
    delta = pd.Timedelta(freq)
    current = start

    while current < end:
        next_ts = current + delta
        assert isinstance(next_ts, pd.Timestamp) and not pd.isna(next_ts)
        chunk_end: pd.Timestamp = min(next_ts, end)  # type: ignore[assignment]
        yield current, chunk_end
        current = chunk_end


def format_api_date(ts: pd.Timestamp) -> str:
    """Format timestamp for ERCOT API parameters.

    Args:
        ts: Timestamp to format

    Returns:
        ISO format string suitable for API calls
    """
    return ts.strftime("%Y-%m-%d")


def format_api_datetime(ts: pd.Timestamp) -> str:
    """Format timestamp with time for ERCOT API parameters.

    Args:
        ts: Timestamp to format

    Returns:
        ISO format datetime string
    """
    return ts.strftime("%Y-%m-%dT%H:%M:%S")
