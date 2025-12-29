"""Decorators for tinygrid methods."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING

import pandas as pd

from .dates import date_chunks, parse_date_range

if TYPE_CHECKING:
    pass


def with_date_range(freq: str | None = None):
    """Decorator that enables date range queries with automatic chunking.

    When a method is decorated with this, it will:
    1. Parse start/end parameters using parse_date_range
    2. If freq is specified and range exceeds freq, chunk and concat results

    Args:
        freq: Optional chunk frequency (e.g., "1D", "7D"). If None, no chunking.

    Example:
        ```python
        @with_date_range(freq="7D")
        def get_spp(self, start, end, **kwargs):
            # Will be called once per 7-day chunk
            ...
        ```
    """

    def decorator(func: Callable[..., pd.DataFrame]) -> Callable[..., pd.DataFrame]:
        @wraps(func)
        def wrapper(
            self,
            start: str | pd.Timestamp = "today",
            end: str | pd.Timestamp | None = None,
            *args,
            **kwargs,
        ) -> pd.DataFrame:
            # Parse the date range
            start_ts, end_ts = parse_date_range(start, end)

            # If no frequency or range is small, just call once
            if freq is None:
                return func(self, start_ts, end_ts, *args, **kwargs)

            freq_delta = pd.Timedelta(freq)
            if (end_ts - start_ts) <= freq_delta:
                return func(self, start_ts, end_ts, *args, **kwargs)

            # Chunk and concat results
            dfs: list[pd.DataFrame] = []
            for chunk_start, chunk_end in date_chunks(start_ts, end_ts, freq):
                try:
                    df = func(self, chunk_start, chunk_end, *args, **kwargs)
                    if not df.empty:
                        dfs.append(df)
                except Exception as e:
                    # Log but continue with other chunks
                    import logging

                    logging.getLogger(__name__).warning(
                        f"Failed to fetch chunk {chunk_start} to {chunk_end}: {e}"
                    )

            if not dfs:
                return pd.DataFrame()

            return pd.concat(dfs, ignore_index=True)

        return wrapper

    return decorator


# Backward compatibility alias
support_date_range = with_date_range
