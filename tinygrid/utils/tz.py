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
    if dst_flags is None:
        ambiguous = True
    else:
        # Normalize to pandas nullable boolean to avoid downcast warnings, then
        # fill missing values as True (DST).
        normalized_flags = dst_flags.astype("boolean").fillna(True)
        ambiguous = normalized_flags.astype(bool)

    try:
        localized = dt_series.dt.tz_localize(tz, ambiguous=ambiguous)
        assert isinstance(localized, pd.Series)
        return localized
    except pytz.exceptions.AmbiguousTimeError:
        # Fallback: handle row by row
        result = dt_series.apply(lambda x: _localize_single(x, tz, ambiguous=True))
        assert isinstance(result, pd.Series)
        return result


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
        result = ts.tz_convert(tz)
        assert isinstance(result, pd.Timestamp) and not pd.isna(result)
        return result

    try:
        result = ts.tz_localize(tz, ambiguous=ambiguous, nonexistent=nonexistent)
        assert isinstance(result, pd.Timestamp) and not pd.isna(result)
        return result
    except pytz.exceptions.AmbiguousTimeError:
        # Force the ambiguous resolution
        result = ts.tz_localize(tz, ambiguous=ambiguous)
        assert isinstance(result, pd.Timestamp) and not pd.isna(result)
        return result
    except pytz.exceptions.NonExistentTimeError:
        # Handle spring forward gap
        if nonexistent == "shift_forward":
            result = ts.tz_localize(tz, nonexistent="shift_forward")
            assert isinstance(result, pd.Timestamp) and not pd.isna(result)
            return result
        elif nonexistent == "shift_backward":
            result = ts.tz_localize(tz, nonexistent="shift_backward")
            assert isinstance(result, pd.Timestamp) and not pd.isna(result)
            return result
        # This should never be reached in practice as nonexistent should be handled
        raise ValueError(
            f"Unable to localize timestamp {dt} with nonexistent={nonexistent}"
        )


def _localize_single(
    dt: pd.Timestamp,
    tz: str,
    ambiguous: bool = True,
) -> pd.Timestamp | pd.NaTType:
    """Localize a single timestamp with fallback handling."""
    try:
        result = dt.tz_localize(tz, ambiguous=ambiguous)
        assert isinstance(result, pd.Timestamp) and not pd.isna(result)
        return result
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
    normalized_flags = dst_flag.astype("boolean").fillna(True)
    return normalized_flags.astype(bool)


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
    offset = dt.utcoffset()
    if offset is None:
        raise ValueError("Unable to determine UTC offset for timestamp")
    return int(offset.total_seconds() / 3600)
