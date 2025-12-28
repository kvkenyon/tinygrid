"""Tests for decorators module."""

import logging

import pandas as pd

from tinygrid.utils.decorators import support_date_range


class MockClient:
    """Mock client for testing decorators."""

    def __init__(self):
        self.call_count = 0
        self.calls = []

    @support_date_range(freq=None)
    def no_chunking(
        self,
        start: str | pd.Timestamp = "today",
        end: str | pd.Timestamp | None = None,
        **kwargs,
    ) -> pd.DataFrame:
        """Method with no chunking."""
        self.call_count += 1
        self.calls.append((start, end, kwargs))
        return pd.DataFrame({"value": [1, 2, 3]})

    @support_date_range(freq="7D")
    def with_chunking_7days(
        self,
        start: str | pd.Timestamp = "today",
        end: str | pd.Timestamp | None = None,
        **kwargs,
    ) -> pd.DataFrame:
        """Method with 7-day chunking."""
        self.call_count += 1
        self.calls.append((start, end, kwargs))
        return pd.DataFrame({"date": [start], "value": [self.call_count]})

    @support_date_range(freq="1D")
    def with_chunking_1day(
        self,
        start: str | pd.Timestamp = "today",
        end: str | pd.Timestamp | None = None,
        **kwargs,
    ) -> pd.DataFrame:
        """Method with 1-day chunking."""
        self.call_count += 1
        self.calls.append((start, end, kwargs))
        return pd.DataFrame({"date": [start], "value": [self.call_count]})

    @support_date_range(freq="7D")
    def with_empty_results(
        self,
        start: str | pd.Timestamp = "today",
        end: str | pd.Timestamp | None = None,
        **kwargs,
    ) -> pd.DataFrame:
        """Method that returns empty DataFrames."""
        self.call_count += 1
        self.calls.append((start, end, kwargs))
        return pd.DataFrame()

    @support_date_range(freq="7D")
    def with_errors(
        self,
        start: str | pd.Timestamp = "today",
        end: str | pd.Timestamp | None = None,
        **kwargs,
    ) -> pd.DataFrame:
        """Method that raises errors for certain chunks."""
        self.call_count += 1
        self.calls.append((start, end, kwargs))
        if self.call_count == 2:
            raise RuntimeError("Simulated error for chunk 2")
        return pd.DataFrame({"date": [start], "value": [self.call_count]})


class TestSupportDateRangeNoChunking:
    """Test support_date_range decorator without chunking."""

    def test_no_chunking_single_call(self):
        """Test that no chunking mode calls function once."""
        client = MockClient()

        result = client.no_chunking(start="2024-01-01", end="2024-01-31")

        assert client.call_count == 1
        assert len(result) == 3
        assert list(result["value"]) == [1, 2, 3]

    def test_no_chunking_default_end(self):
        """Test no chunking with default end parameter."""
        client = MockClient()

        result = client.no_chunking(start="2024-01-01")

        assert client.call_count == 1
        assert len(result) == 3

    def test_no_chunking_preserves_kwargs(self):
        """Test that kwargs are passed through correctly."""
        client = MockClient()

        result = client.no_chunking(
            start="2024-01-01", end="2024-01-31", extra_param="value"
        )

        assert client.call_count == 1
        assert client.calls[0][2]["extra_param"] == "value"


class TestSupportDateRangeWithChunking:
    """Test support_date_range decorator with chunking."""

    def test_chunking_small_range_no_split(self):
        """Test that small date ranges don't get chunked."""
        client = MockClient()

        # 3 days should not be chunked with 7D freq
        result = client.with_chunking_7days(start="2024-01-01", end="2024-01-03")

        assert client.call_count == 1

    def test_chunking_large_range_splits(self):
        """Test that large date ranges get chunked."""
        client = MockClient()

        # 20 days with 7D freq should create 3 chunks
        result = client.with_chunking_7days(start="2024-01-01", end="2024-01-21")

        assert client.call_count == 3
        assert len(result) == 3  # One row per chunk

    def test_chunking_1day_freq(self):
        """Test chunking with 1-day frequency."""
        client = MockClient()

        # 3 days with 1D freq should create 3 chunks
        result = client.with_chunking_1day(start="2024-01-01", end="2024-01-04")

        assert client.call_count == 3
        assert len(result) == 3

    def test_chunking_concatenates_results(self):
        """Test that chunked results are concatenated correctly."""
        client = MockClient()

        result = client.with_chunking_7days(start="2024-01-01", end="2024-01-21")

        # Should have 3 chunks with sequential values
        assert len(result) == 3
        assert list(result["value"]) == [1, 2, 3]

    def test_chunking_preserves_kwargs(self):
        """Test that kwargs are passed to each chunk."""
        client = MockClient()

        result = client.with_chunking_7days(
            start="2024-01-01", end="2024-01-21", extra_param="test_value"
        )

        assert client.call_count == 3
        # Check that each chunk received the kwargs
        for call in client.calls:
            assert call[2]["extra_param"] == "test_value"

    def test_chunking_empty_results(self):
        """Test handling of empty DataFrames in chunks."""
        client = MockClient()

        result = client.with_empty_results(start="2024-01-01", end="2024-01-21")

        # Should call multiple times but return empty DataFrame
        assert client.call_count == 3
        assert len(result) == 0
        assert isinstance(result, pd.DataFrame)


class TestSupportDateRangeErrorHandling:
    """Test error handling in support_date_range decorator."""

    def test_chunking_continues_on_error(self, caplog):
        """Test that errors in one chunk don't stop other chunks."""
        client = MockClient()

        with caplog.at_level(logging.WARNING):
            result = client.with_errors(start="2024-01-01", end="2024-01-21")

        # Should have attempted 3 chunks
        assert client.call_count == 3
        # Should only have 2 results (chunk 2 failed)
        assert len(result) == 2
        assert list(result["value"]) == [1, 3]
        # Should have logged the error
        assert "Failed to fetch chunk" in caplog.text

    def test_chunking_all_errors_returns_empty(self):
        """Test that if all chunks error, returns empty DataFrame."""

        class AlwaysErrorClient:
            @support_date_range(freq="7D")
            def always_errors(
                self,
                start: str | pd.Timestamp = "today",
                end: str | pd.Timestamp | None = None,
                **kwargs,
            ) -> pd.DataFrame:
                raise RuntimeError("Always fails")

        client = AlwaysErrorClient()
        result = client.always_errors(start="2024-01-01", end="2024-01-21")

        assert len(result) == 0
        assert isinstance(result, pd.DataFrame)


class TestSupportDateRangeDateParsing:
    """Test date parsing in support_date_range decorator."""

    def test_parses_string_dates(self):
        """Test that string dates are parsed correctly."""
        client = MockClient()

        result = client.no_chunking(start="2024-01-01", end="2024-01-31")

        # Check that dates were converted to Timestamps
        assert isinstance(client.calls[0][0], pd.Timestamp)
        assert isinstance(client.calls[0][1], pd.Timestamp)

    def test_parses_timestamp_dates(self):
        """Test that Timestamp dates are handled correctly."""
        client = MockClient()
        start_ts = pd.Timestamp("2024-01-01")
        end_ts = pd.Timestamp("2024-01-31")

        result = client.no_chunking(start=start_ts, end=end_ts)

        assert client.call_count == 1

    def test_parses_today_keyword(self):
        """Test that 'today' keyword is parsed."""
        client = MockClient()

        result = client.no_chunking(start="today")

        assert client.call_count == 1
        assert isinstance(client.calls[0][0], pd.Timestamp)

    def test_default_end_is_parsed(self):
        """Test that default end parameter is handled correctly."""
        client = MockClient()

        result = client.no_chunking(start="2024-01-01", end=None)

        assert client.call_count == 1
        # End should be defaulted to start + 1 day
        assert isinstance(client.calls[0][1], pd.Timestamp)


class TestSupportDateRangeEdgeCases:
    """Test edge cases for support_date_range decorator."""

    def test_exact_chunk_boundary(self):
        """Test date range that's exactly on chunk boundary."""
        client = MockClient()

        # Exactly 7 days with 7D freq should create 1 chunk (<=)
        result = client.with_chunking_7days(start="2024-01-01", end="2024-01-08")

        assert client.call_count == 1

    def test_one_day_over_boundary(self):
        """Test date range that's one day over chunk boundary."""
        client = MockClient()

        # 8 days with 7D freq should create 2 chunks
        result = client.with_chunking_7days(start="2024-01-01", end="2024-01-09")

        assert client.call_count == 2

    def test_preserves_function_metadata(self):
        """Test that decorator preserves function metadata."""
        client = MockClient()

        # Check that functools.wraps preserved the metadata
        assert client.no_chunking.__name__ == "no_chunking"
        assert "Method with no chunking" in client.no_chunking.__doc__  # pyright: ignore[reportOperatorIssue]

    def test_with_args(self):
        """Test that positional args are passed through."""

        class ClientWithArgs:
            @support_date_range(freq=None)
            def method_with_args(
                self,
                start: str | pd.Timestamp = "today",
                end: str | pd.Timestamp | None = None,
                *args,
                **kwargs,
            ) -> pd.DataFrame:
                return pd.DataFrame({"args": list(args)})

        client = ClientWithArgs()
        result = client.method_with_args("2024-01-01", "2024-01-31", "extra_arg")

        # Extra positional arg should be passed through
        assert "extra_arg" in result["args"].tolist()
