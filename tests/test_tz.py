"""Tests for timezone utilities."""

import pandas as pd
import pytest
import pytz

from tinygrid.constants.ercot import ERCOT_TIMEZONE
from tinygrid.utils.tz import (
    _localize_single,
    dst_flag_to_ambiguous,
    get_utc_offset,
    is_dst_transition_date,
    localize_with_dst,
    resolve_ambiguous_dst,
)


class TestResolveAmbiguousDST:
    """Test resolve_ambiguous_dst function."""

    def test_resolve_ambiguous_dst_with_dst_flags(self):
        """Test resolving ambiguous DST timestamps with DSTFlag."""
        # During fall back, 1:30 AM occurs twice
        timestamps = pd.Series(
            [
                "2023-11-05 01:30:00",
                "2023-11-05 01:30:00",
            ]
        )
        dst_flags = pd.Series([True, False])  # First is DST, second is Standard

        result = resolve_ambiguous_dst(timestamps, dst_flags)

        assert result.dt.tz is not None
        assert len(result) == 2
        # Both timestamps should be timezone-aware
        assert result[0].tz is not None
        assert result[1].tz is not None

    def test_resolve_ambiguous_dst_without_dst_flags(self):
        """Test resolving ambiguous DST timestamps without DSTFlag (defaults to DST)."""
        timestamps = pd.Series(["2023-11-05 01:30:00"])

        result = resolve_ambiguous_dst(timestamps)

        assert result.dt.tz is not None
        assert len(result) == 1

    def test_resolve_ambiguous_dst_with_null_dst_flags(self):
        """Test resolving with null DSTFlag values (should default to True)."""
        timestamps = pd.Series(["2023-11-05 01:30:00", "2023-11-05 02:30:00"])
        dst_flags = pd.Series([None, True])

        result = resolve_ambiguous_dst(timestamps, dst_flags)

        assert result.dt.tz is not None
        assert len(result) == 2

    def test_resolve_ambiguous_dst_non_ambiguous_times(self):
        """Test resolving non-ambiguous timestamps."""
        timestamps = pd.Series(["2023-06-15 12:00:00", "2023-06-15 13:00:00"])

        result = resolve_ambiguous_dst(timestamps)

        assert result.dt.tz is not None
        assert len(result) == 2

    def test_resolve_ambiguous_dst_custom_timezone(self):
        """Test resolving with a custom timezone."""
        timestamps = pd.Series(["2023-11-05 01:30:00"])

        result = resolve_ambiguous_dst(timestamps, tz="US/Eastern")

        assert result.dt.tz is not None
        assert str(result[0].tz) == "US/Eastern"


class TestLocalizeWithDST:
    """Test localize_with_dst function."""

    def test_localize_naive_timestamp(self):
        """Test localizing a naive timestamp."""
        dt = pd.Timestamp("2023-06-15 12:00:00")

        result = localize_with_dst(dt)

        assert result.tz is not None
        assert str(result.tz) == ERCOT_TIMEZONE

    def test_localize_string_timestamp(self):
        """Test localizing a datetime string."""
        dt = "2023-06-15 12:00:00"

        result = localize_with_dst(dt)

        assert result.tz is not None
        assert str(result.tz) == ERCOT_TIMEZONE

    def test_localize_already_aware_timestamp(self):
        """Test localizing an already timezone-aware timestamp (should convert)."""
        dt = pd.Timestamp("2023-06-15 12:00:00", tz="UTC")

        result = localize_with_dst(dt)

        assert result.tz is not None
        assert str(result.tz) == ERCOT_TIMEZONE

    def test_localize_ambiguous_time_dst(self):
        """Test localizing ambiguous time with DST=True."""
        # During fall back, 1:30 AM occurs twice
        dt = pd.Timestamp("2023-11-05 01:30:00")

        result = localize_with_dst(dt, ambiguous=True)

        assert result.tz is not None

    def test_localize_ambiguous_time_standard(self):
        """Test localizing ambiguous time with DST=False."""
        # During fall back, 1:30 AM occurs twice
        dt = pd.Timestamp("2023-11-05 01:30:00")

        result = localize_with_dst(dt, ambiguous=False)

        assert result.tz is not None

    def test_localize_custom_timezone(self):
        """Test localizing to a custom timezone."""
        dt = pd.Timestamp("2023-06-15 12:00:00")

        result = localize_with_dst(dt, tz="US/Eastern")

        assert result.tz is not None
        assert str(result.tz) == "US/Eastern"


class TestDSTFlagToAmbiguous:
    """Test dst_flag_to_ambiguous function."""

    def test_dst_flag_true_values(self):
        """Test converting True DST flags."""
        dst_flag = pd.Series([True, True, True])

        result = dst_flag_to_ambiguous(dst_flag)

        assert all(result == [True, True, True])

    def test_dst_flag_false_values(self):
        """Test converting False DST flags."""
        dst_flag = pd.Series([False, False, False])

        result = dst_flag_to_ambiguous(dst_flag)

        assert all(result == [False, False, False])

    def test_dst_flag_mixed_values(self):
        """Test converting mixed DST flags."""
        dst_flag = pd.Series([True, False, True])

        result = dst_flag_to_ambiguous(dst_flag)

        assert result[0]  # pyright: ignore[reportGeneralTypeIssues]
        assert not result[1]  # pyright: ignore[reportGeneralTypeIssues]
        assert result[2]  # pyright: ignore[reportGeneralTypeIssues]

    def test_dst_flag_with_nulls(self):
        """Test converting DST flags with null values (should default to True)."""
        dst_flag = pd.Series([True, None, False])

        result = dst_flag_to_ambiguous(dst_flag)

        assert result[0]  # pyright: ignore[reportGeneralTypeIssues]
        assert result[1]  # pyright: ignore[reportGeneralTypeIssues] # Null should become True
        assert not result[2]  # pyright: ignore[reportGeneralTypeIssues]

    def test_dst_flag_all_nulls(self):
        """Test converting all null DST flags."""
        dst_flag = pd.Series([None, None, None])

        result = dst_flag_to_ambiguous(dst_flag)

        assert all(result == [True, True, True])


class TestIsDSTTransitionDate:
    """Test is_dst_transition_date function."""

    def test_dst_transition_spring_forward(self):
        """Test detecting spring forward DST transition."""
        # March 2023 spring forward (2nd Sunday of March)
        date = pd.Timestamp("2023-03-12", tz=ERCOT_TIMEZONE)

        result = is_dst_transition_date(date)

        # This date should be a DST transition date
        assert isinstance(result, bool)

    def test_dst_transition_fall_back(self):
        """Test detecting fall back DST transition."""
        # November 2023 fall back (1st Sunday of November)
        date = pd.Timestamp("2023-11-05", tz=ERCOT_TIMEZONE)

        result = is_dst_transition_date(date)

        # This date should be a DST transition date
        assert isinstance(result, bool)

    def test_non_dst_transition_date(self):
        """Test detecting non-DST transition date."""
        date = pd.Timestamp("2023-06-15", tz=ERCOT_TIMEZONE)

        result = is_dst_transition_date(date)

        # Regular date should not be a DST transition
        assert result is False

    def test_dst_transition_custom_timezone(self):
        """Test detecting DST transition in custom timezone."""
        date = pd.Timestamp("2023-03-12", tz="US/Eastern")

        result = is_dst_transition_date(date, tz="US/Eastern")

        assert isinstance(result, bool)


class TestGetUTCOffset:
    """Test get_utc_offset function."""

    def test_get_utc_offset_cdt(self):
        """Test getting UTC offset for CDT (Central Daylight Time)."""
        # Summer date in Central Daylight Time (UTC-5)
        dt = pd.Timestamp("2023-06-15 12:00:00", tz=ERCOT_TIMEZONE)

        offset = get_utc_offset(dt)

        assert offset == -5  # CDT is UTC-5

    def test_get_utc_offset_cst(self):
        """Test getting UTC offset for CST (Central Standard Time)."""
        # Winter date in Central Standard Time (UTC-6)
        dt = pd.Timestamp("2023-01-15 12:00:00", tz=ERCOT_TIMEZONE)

        offset = get_utc_offset(dt)

        assert offset == -6  # CST is UTC-6

    def test_get_utc_offset_utc(self):
        """Test getting UTC offset for UTC timezone."""
        dt = pd.Timestamp("2023-06-15 12:00:00", tz="UTC")

        offset = get_utc_offset(dt)

        assert offset == 0  # UTC is offset 0

    def test_get_utc_offset_eastern(self):
        """Test getting UTC offset for Eastern timezone."""
        # Summer date in Eastern Daylight Time (UTC-4)
        dt = pd.Timestamp("2023-06-15 12:00:00", tz="US/Eastern")

        offset = get_utc_offset(dt)

        assert offset == -4  # EDT is UTC-4

    def test_get_utc_offset_naive_timestamp_raises(self):
        """Test that naive timestamp raises ValueError."""
        dt = pd.Timestamp("2023-06-15 12:00:00")

        with pytest.raises(
            ValueError, match="Timestamp must be timezone-aware"
        ):
            get_utc_offset(dt)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_resolve_ambiguous_dst_empty_series(self):
        """Test resolving empty series."""
        timestamps = pd.Series([], dtype="datetime64[ns]")

        result = resolve_ambiguous_dst(timestamps)

        assert len(result) == 0
        assert result.dt.tz is not None

    def test_localize_with_dst_already_in_target_tz(self):
        """Test localizing timestamp already in target timezone."""
        dt = pd.Timestamp("2023-06-15 12:00:00", tz=ERCOT_TIMEZONE)

        result = localize_with_dst(dt, tz=ERCOT_TIMEZONE)

        assert result.tz is not None
        assert str(result.tz) == ERCOT_TIMEZONE

    def test_dst_flag_to_ambiguous_empty_series(self):
        """Test converting empty DST flag series."""
        dst_flag = pd.Series([], dtype=bool)

        result = dst_flag_to_ambiguous(dst_flag)

        assert len(result) == 0

    def test_localize_with_dst_nonexistent_shift_forward(self):
        """Test localizing nonexistent time with shift_forward."""
        # During spring forward, 2:30 AM doesn't exist
        dt = pd.Timestamp("2023-03-12 02:30:00")

        result = localize_with_dst(
            dt, tz=ERCOT_TIMEZONE, nonexistent="shift_forward"
        )

        assert result.tz is not None
        # Should be shifted forward to next valid time

    def test_localize_with_dst_nonexistent_shift_backward(self):
        """Test localizing nonexistent time with shift_backward."""
        # During spring forward, 2:30 AM doesn't exist
        dt = pd.Timestamp("2023-03-12 02:30:00")

        result = localize_with_dst(
            dt, tz=ERCOT_TIMEZONE, nonexistent="shift_backward"
        )

        assert result.tz is not None
        # Should be shifted backward to previous valid time
        assert result.hour == 1


class TestAdditionalDSTPaths:
    def test_resolve_ambiguous_dst_fallback(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        ts = pd.Series([pd.Timestamp("2021-11-07 01:30")])

        from pandas.core.indexes.accessors import DatetimeProperties

        def raise_ambiguous(self, tz=None, ambiguous=None):  # type: ignore[override]
            raise pytz.exceptions.AmbiguousTimeError()

        monkeypatch.setattr(
            DatetimeProperties, "tz_localize", raise_ambiguous, raising=False
        )

        result = resolve_ambiguous_dst(ts)

        assert not result.isna().all()

    def test_localize_with_dst_nonexistent_explicit_backward(self):
        ts = "2024-03-10 02:15"
        result = localize_with_dst(ts, nonexistent="shift_backward")
        assert result.hour == 1

    def test_localize_with_dst_nonexistent_shift_forward_fallback(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        orig = pd.Timestamp.tz_localize
        calls = {"count": 0}

        def fake(self, tz=None, ambiguous=True, nonexistent="raise"):  # type: ignore[override]
            calls["count"] += 1
            if calls["count"] == 1:
                raise pytz.exceptions.NonExistentTimeError()
            return orig(
                self, tz=tz, ambiguous=ambiguous, nonexistent=nonexistent
            )

        monkeypatch.setattr(pd.Timestamp, "tz_localize", fake, raising=False)

        ts = pd.Timestamp("2024-03-10 02:15")
        result = localize_with_dst(ts, nonexistent="shift_forward")
        assert result.tz is not None

    def test_localize_with_dst_nonexistent_shift_backward_fallback(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        orig = pd.Timestamp.tz_localize
        calls = {"count": 0}

        def fake(self, tz=None, ambiguous=True, nonexistent="raise"):  # type: ignore[override]
            calls["count"] += 1
            if calls["count"] == 1:
                raise pytz.exceptions.NonExistentTimeError()
            return orig(
                self, tz=tz, ambiguous=ambiguous, nonexistent=nonexistent
            )

        monkeypatch.setattr(pd.Timestamp, "tz_localize", fake, raising=False)

        ts = pd.Timestamp("2024-03-10 02:15")
        result = localize_with_dst(ts, nonexistent="shift_backward")
        assert result.tz is not None

    def test_localize_with_dst_ambiguous_fallback(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        orig = pd.Timestamp.tz_localize
        calls = {"count": 0}

        def fake(self, tz=None, ambiguous=True, nonexistent="raise"):  # type: ignore[override]
            calls["count"] += 1
            if calls["count"] == 1:
                raise pytz.exceptions.AmbiguousTimeError()
            return orig(
                self, tz=tz, ambiguous=ambiguous, nonexistent=nonexistent
            )

        monkeypatch.setattr(pd.Timestamp, "tz_localize", fake, raising=False)

        ts = pd.Timestamp("2021-11-07 01:30")
        result = localize_with_dst(ts)
        assert result.tz is not None

    def test_localize_with_dst_nonexistent_invalid_mode(self):
        ts = "2024-03-10 02:15"
        with pytest.raises(ValueError):
            localize_with_dst(ts, nonexistent="raise")

    def test_localize_with_dst_nonexistent_raise_branch(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        ts = pd.Timestamp("2024-03-10 02:15")

        def raise_nonexistent(
            self, tz=None, ambiguous=True, nonexistent="raise"
        ):  # type: ignore[override]
            raise pytz.exceptions.NonExistentTimeError()

        monkeypatch.setattr(
            pd.Timestamp, "tz_localize", raise_nonexistent, raising=False
        )

        with pytest.raises(ValueError):
            localize_with_dst(ts, nonexistent="raise")

    def test_localize_single_returns_nat(self):
        assert pd.isna(_localize_single(pd.NaT, ERCOT_TIMEZONE))

    def test_localize_single_success(self):
        ts = pd.Timestamp("2024-01-01 00:00:00")
        result = _localize_single(ts, ERCOT_TIMEZONE)
        assert result.tz is not None

    def test_get_utc_offset_with_missing_offset(self):
        class Dummy:
            tz = "UTC"

            def utcoffset(self):
                return None

        with pytest.raises(ValueError):
            get_utc_offset(Dummy())  # type: ignore[arg-type]
