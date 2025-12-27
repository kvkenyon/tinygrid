"""Timezone and DST handling utilities."""

from __future__ import annotations

import pandas as pd
import pytz

from ..constants.ercot import ERCOT_TIMEZONE


def resolve_ambiguous_dst(
    timestamps: pd.Series,
    dst_flags: pd.Series | None = None,
    tz: str = ERCOT_TIMEZONE,
) -> pd.Series:
    """Resolve ambiguous DST timestamps to timezone-aware values.

    During DST transitions, times between 1:00-2:00 AM occur twice.
    This function resolves them using DSTFlag if available, or defaults to DST.

    Args:
        timestamps: Series of datetime strings or timestamps
        dst_flags: Optional series of DST flags (True=DST/CDT, False=Standard/CST)
        tz: Timezone to localize to

    Returns:
        Series of timezone-aware timestamps

    Example:
        During fall back, 1:30 AM occurs twice:
        - DSTFlag=True → 1:30 AM CDT (before transition)
        - DSTFlag=False → 1:30 AM CST (after transition)
    """
    # Convert to datetime if strings
    dt_series = pd.to_datetime(timestamps)

    # Use DSTFlag to resolve ambiguous times (DST=True, Standard=False)
    ambiguous = (
        dst_flags.fillna(True).astype(bool) if dst_flags is not None else True
    )

    try:
        return dt_series.dt.tz_localize(tz, ambiguous=ambiguous)
    except pytz.exceptions.AmbiguousTimeError:
        # Fallback: handle row by row
        return dt_series.apply(
            lambda x: _localize_single(x, tz, ambiguous=True)
        )


def localize_with_dst(
    dt: pd.Timestamp | str,
    tz: str = ERCOT_TIMEZONE,
    ambiguous: bool = True,
    nonexistent: str = "shift_forward",
) -> pd.Timestamp:
    """Safely localize a timestamp handling DST edge cases.

    Args:
        dt: Timestamp or datetime string to localize
        tz: Target timezone
        ambiguous: How to handle ambiguous times (fall back):
            - True: Assume DST (e.g., CDT)
            - False: Assume standard time (e.g., CST)
        nonexistent: How to handle nonexistent times (spring forward):
            - "shift_forward": Shift to next valid time
            - "shift_backward": Shift to previous valid time
            - "NaT": Return NaT

    Returns:
        Timezone-aware timestamp
    """
    ts = pd.Timestamp(dt)

    if ts.tz is not None:
        return ts.tz_convert(tz)

    try:
        return ts.tz_localize(tz, ambiguous=ambiguous, nonexistent=nonexistent)
    except pytz.exceptions.AmbiguousTimeError:
        # Force the ambiguous resolution
        return ts.tz_localize(tz, ambiguous=ambiguous)
    except pytz.exceptions.NonExistentTimeError:
        # Handle spring forward gap
        if nonexistent == "shift_forward":
            return ts.tz_localize(tz, nonexistent="shift_forward")
        elif nonexistent == "shift_backward":
            return ts.tz_localize(tz, nonexistent="shift_backward")
        return pd.NaT


def _localize_single(
    dt: pd.Timestamp,
    tz: str,
    ambiguous: bool = True,
) -> pd.Timestamp:
    """Localize a single timestamp with fallback handling."""
    try:
        return dt.tz_localize(tz, ambiguous=ambiguous)
    except Exception:
        return pd.NaT


def dst_flag_to_ambiguous(dst_flag: pd.Series) -> pd.Series:
    """Convert ERCOT DSTFlag column to ambiguous parameter for localization.

    ERCOT uses DSTFlag where:
    - True/1 = DST is in effect (e.g., CDT)
    - False/0 = Standard time (e.g., CST)

    For pandas tz_localize ambiguous parameter:
    - True = interpret as DST
    - False = interpret as standard time

    Args:
        dst_flag: Series of DSTFlag values

    Returns:
        Boolean series for use with tz_localize(ambiguous=...)
    """
    return dst_flag.fillna(True).astype(bool)


def is_dst_transition_date(date: pd.Timestamp, tz: str = ERCOT_TIMEZONE) -> bool:
    """Check if a date is a DST transition date.

    Args:
        date: Date to check
        tz: Timezone to check

    Returns:
        True if this date has a DST transition
    """
    date = date.normalize()
    timezone = pytz.timezone(tz)

    # Check if there's a transition on this date
    transitions = timezone._utc_transition_times
    for trans in transitions:
        if trans is not None:
            trans_local = pd.Timestamp(trans, tz="UTC").tz_convert(tz)
            if trans_local.normalize() == date:
                return True
    return False


def get_utc_offset(dt: pd.Timestamp) -> int:
    """Get the UTC offset in hours for a timestamp.

    Args:
        dt: Timezone-aware timestamp

    Returns:
        Offset from UTC in hours (e.g., -5 for CDT, -6 for CST)
    """
    if dt.tz is None:
        raise ValueError("Timestamp must be timezone-aware")
    return int(dt.utcoffset().total_seconds() / 3600)
