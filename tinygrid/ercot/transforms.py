"""Data transformation and filtering utilities for ERCOT data.

This module contains functions for:
- Filtering DataFrames by location and date
- Standardizing column names
- Adding computed time columns

These are separated from api.py to keep the API methods focused on
data sourcing/dispatch logic rather than data manipulation.
"""

from __future__ import annotations

import pandas as pd

from ..constants.ercot import (
    COLUMN_MAPPINGS,
    ERCOT_TIMEZONE,
    LOAD_ZONES,
    TRADING_HUBS,
    LocationType,
)


def filter_by_location(
    df: pd.DataFrame,
    locations: list[str] | None = None,
    location_type: LocationType | list[LocationType] | None = None,
    location_column: str = "Settlement Point",
) -> pd.DataFrame:
    """Filter DataFrame by location names or type.

    Args:
        df: DataFrame to filter
        locations: Specific location names to include
        location_type: Type(s) of locations to include (single or list)
        location_column: Name of the location column

    Returns:
        Filtered DataFrame
    """
    if df.empty:
        return df

    # Find the actual location column name (may vary between live and historical APIs)
    loc_col = None
    for col in [
        location_column,
        "Location",
        "Settlement Point Name",
        "SettlementPointName",  # Historical archive format
        "SettlementPoint",  # Alternative camelCase
    ]:
        if col in df.columns:
            loc_col = col
            break

    if loc_col is None:
        return df

    # Filter by specific locations
    if locations:
        filtered = df[df[loc_col].isin(locations)]
        assert isinstance(filtered, pd.DataFrame)
        df = filtered

    # Filter by location type(s)
    if location_type:
        # Normalize to list for uniform handling
        types = (
            [location_type]
            if isinstance(location_type, LocationType)
            else list(location_type)
        )

        # Build set of allowed locations based on types
        allowed: set[str] = set()
        exclude_mode = False

        for lt in types:
            if lt == LocationType.LOAD_ZONE:
                allowed.update(LOAD_ZONES)
            elif lt == LocationType.TRADING_HUB:
                allowed.update(TRADING_HUBS)
            elif lt == LocationType.RESOURCE_NODE:
                exclude_mode = True

        if exclude_mode and not allowed:
            # Only RESOURCE_NODE requested - exclude zones and hubs
            filtered = df[
                ~df[loc_col].isin(LOAD_ZONES) & ~df[loc_col].isin(TRADING_HUBS)
            ]
            assert isinstance(filtered, pd.DataFrame)
            df = filtered
        elif allowed:
            filtered = df[df[loc_col].isin(allowed)]
            assert isinstance(filtered, pd.DataFrame)
            df = filtered

    return df


def filter_by_date(
    df: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    date_column: str = "Delivery Date",
) -> pd.DataFrame:
    """Filter DataFrame to date range [start, end).

    Uses Python convention: inclusive start, exclusive end.

    Args:
        df: DataFrame to filter
        start: Start date (inclusive)
        end: End date (exclusive)
        date_column: Name of the date column

    Returns:
        Filtered DataFrame
    """
    if df.empty:
        return df

    # Find the actual date column name (may vary between live and historical APIs)
    actual_col = None
    for col in [
        date_column,
        "DeliveryDate",
        "Delivery Date",
        "Oper Day",
        "OperDay",
        "Posted Datetime",
        "PostedDatetime",
    ]:
        if col in df.columns:
            actual_col = col
            break

    if actual_col is None:
        return df

    # Convert column to datetime if needed
    dates = pd.to_datetime(df[actual_col])

    # Use tz-naive dates for comparison (API returns naive dates)
    start_date = start.normalize().tz_localize(None)
    end_date = end.normalize().tz_localize(None)

    # Filter to [start, end) - include start date, exclude end date
    mask = (dates >= start_date) & (dates < end_date)
    result = df[mask]
    assert isinstance(result, pd.DataFrame)
    return result


def add_time_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add Time and End Time columns based on available time fields.

    Converts raw ERCOT time columns into proper timestamps:
    - Date + Hour + Interval → 15-minute intervals
    - Date + Hour Ending → hourly intervals
    - Timestamp → parse as Time (no End Time for SCED)

    Args:
        df: DataFrame with raw time columns

    Returns:
        DataFrame with Time and optionally End Time columns added
    """
    if df.empty:
        return df

    tz = ERCOT_TIMEZONE

    # Case 1: Date + Hour + Interval (15-minute real-time data)
    if "Date" in df.columns and "Hour" in df.columns and "Interval" in df.columns:
        # Hour 1, Interval 1 = 00:00-00:15
        # Hour is 1-24, Interval is 1-4
        dates = pd.to_datetime(df["Date"])
        hours = df["Hour"].astype(int) - 1  # Convert 1-24 to 0-23
        intervals = df["Interval"].astype(int) - 1  # Convert 1-4 to 0-3
        minutes = intervals * 15

        # Build start timestamps
        start_times = (
            dates
            + pd.to_timedelta(hours, unit="h")
            + pd.to_timedelta(minutes, unit="m")
        )
        end_times = start_times + pd.Timedelta(minutes=15)

        # Localize to ERCOT timezone
        df["Time"] = start_times.dt.tz_localize(tz, ambiguous="infer")
        df["End Time"] = end_times.dt.tz_localize(tz, ambiguous="infer")

    # Case 2: Date + Hour Ending (hourly data - DAM, AS, Load)
    elif "Date" in df.columns and "Hour Ending" in df.columns:
        dates = pd.to_datetime(df["Date"])
        # Hour Ending can be "01:00" string or integer 1-24
        hour_ending = df["Hour Ending"]
        if hour_ending.dtype == object:
            # Parse "01:00" format - extract hour
            hours = hour_ending.str.extract(r"(\d+)")[0].astype(int)
        else:
            hours = hour_ending.astype(int)

        # Hour Ending 1 means 00:00-01:00, Hour Ending 24 means 23:00-00:00
        start_hours = hours - 1  # Convert to 0-23

        start_times = dates + pd.to_timedelta(start_hours, unit="h")
        end_times = start_times + pd.Timedelta(hours=1)

        df["Time"] = start_times.dt.tz_localize(tz, ambiguous="infer")
        df["End Time"] = end_times.dt.tz_localize(tz, ambiguous="infer")

    # Case 3: Timestamp already exists (SCED data)
    elif "Timestamp" in df.columns:
        timestamps = pd.to_datetime(df["Timestamp"])
        if timestamps.dt.tz is None:
            df["Time"] = timestamps.dt.tz_localize(tz, ambiguous="infer")
        else:
            df["Time"] = timestamps.dt.tz_convert(tz)
        # No End Time for SCED - it's a point-in-time snapshot

    # Case 4: Posted Time (forecasts)
    elif "Posted Time" in df.columns:
        timestamps = pd.to_datetime(df["Posted Time"])
        if timestamps.dt.tz is None:
            df["Time"] = timestamps.dt.tz_localize(tz, ambiguous="infer")
        else:
            df["Time"] = timestamps.dt.tz_convert(tz)
        # No End Time for forecasts - it's when the forecast was posted

    return df


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names and add time columns.

    Renames raw API column names to consistent, readable names,
    adds Time/End Time columns, and reorders for better UX.

    Args:
        df: DataFrame with raw column names

    Returns:
        DataFrame with standardized column names and ordering
    """
    if df.empty:
        return df

    # Build rename dict for columns that exist in the DataFrame
    rename_map = {
        col: COLUMN_MAPPINGS[col] for col in df.columns if col in COLUMN_MAPPINGS
    }

    if rename_map:
        df = df.rename(columns=rename_map)

    # Add Time and End Time columns
    df = add_time_columns(df)

    # Drop raw time columns now that we have proper timestamps
    raw_time_cols = [
        "Date",
        "Hour",
        "Interval",
        "Hour Ending",
        "DST",
        "Timestamp",
        "Posted Time",
        "Repeated Hour",
    ]
    dropped = df.drop(columns=[c for c in raw_time_cols if c in df.columns])
    assert isinstance(dropped, pd.DataFrame)
    df = dropped

    # Reorder columns for better UX: Time first, then key data, then metadata
    priority_cols = ["Time", "End Time", "Location", "Price", "Market"]
    existing_priority = [c for c in priority_cols if c in df.columns]
    other_cols = [c for c in df.columns if c not in priority_cols]
    reordered = df[existing_priority + other_cols]
    assert isinstance(reordered, pd.DataFrame)
    df = reordered

    result = df.reset_index(drop=True)
    assert isinstance(result, pd.DataFrame)
    return result
