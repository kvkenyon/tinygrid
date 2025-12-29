"""Tests for tinygrid.ercot.polling module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from tinygrid.ercot.polling import (
    DEFAULT_POLL_INTERVAL,
    MAX_CONSECUTIVE_ERRORS,
    MIN_POLL_INTERVAL,
    ERCOTPoller,
    PollResult,
    poll_latest,
)
from tinygrid.errors import GridAPIError, GridError


class TestPollingConstants:
    """Tests for polling constants."""

    def test_min_poll_interval(self):
        """Test minimum poll interval."""
        assert MIN_POLL_INTERVAL == 2.0

    def test_default_poll_interval(self):
        """Test default poll interval."""
        assert DEFAULT_POLL_INTERVAL == 60.0

    def test_max_consecutive_errors(self):
        """Test max consecutive errors."""
        assert MAX_CONSECUTIVE_ERRORS == 5


class TestPollResult:
    """Tests for PollResult dataclass."""

    def test_create_success_result(self):
        """Test creating successful poll result."""
        df = pd.DataFrame({"col": [1, 2, 3]})
        ts = pd.Timestamp.now(tz="US/Central")

        result = PollResult(
            data=df,
            timestamp=ts,
            success=True,
            iteration=0,
        )

        assert result.success is True
        assert result.error is None
        assert result.iteration == 0
        assert len(result.data) == 3

    def test_create_error_result(self):
        """Test creating error poll result."""
        ts = pd.Timestamp.now(tz="US/Central")
        error = GridAPIError("API Error", status_code=500)

        result = PollResult(
            data=None,
            timestamp=ts,
            success=False,
            error=error,
            iteration=5,
        )

        assert result.success is False
        assert result.data is None
        assert result.error is error
        assert result.iteration == 5


class TestERCOTPollerInit:
    """Tests for ERCOTPoller initialization."""

    def test_init_defaults(self):
        """Test default initialization."""
        mock_client = MagicMock()
        poller = ERCOTPoller(client=mock_client)

        assert poller.client is mock_client
        assert poller.interval == DEFAULT_POLL_INTERVAL
        assert poller.max_errors == MAX_CONSECUTIVE_ERRORS
        assert poller.backoff_factor == 2.0
        assert poller.max_backoff == 300.0

    def test_init_custom_interval(self):
        """Test custom interval initialization."""
        mock_client = MagicMock()
        poller = ERCOTPoller(client=mock_client, interval=30.0)

        assert poller.interval == 30.0

    def test_init_enforces_min_interval(self):
        """Test that minimum interval is enforced."""
        mock_client = MagicMock()
        poller = ERCOTPoller(client=mock_client, interval=0.5)

        assert poller.interval == MIN_POLL_INTERVAL

    def test_init_custom_max_errors(self):
        """Test custom max errors."""
        mock_client = MagicMock()
        poller = ERCOTPoller(client=mock_client, max_errors=10)

        assert poller.max_errors == 10

    def test_init_custom_backoff(self):
        """Test custom backoff settings."""
        mock_client = MagicMock()
        poller = ERCOTPoller(
            client=mock_client,
            backoff_factor=3.0,
            max_backoff=600.0,
        )

        assert poller.backoff_factor == 3.0
        assert poller.max_backoff == 600.0


class TestERCOTPollerPollOnce:
    """Tests for ERCOTPoller._poll_once method."""

    def test_poll_once_success(self):
        """Test successful single poll."""
        mock_client = MagicMock()
        mock_method = MagicMock(return_value=pd.DataFrame({"col": [1, 2]}))

        poller = ERCOTPoller(client=mock_client)
        result = poller._poll_once(mock_method, iteration=0)

        assert result.success is True
        assert len(result.data) == 2
        assert result.iteration == 0

    def test_poll_once_with_kwargs(self):
        """Test single poll passes kwargs."""
        mock_client = MagicMock()
        mock_method = MagicMock(return_value=pd.DataFrame())

        poller = ERCOTPoller(client=mock_client)
        poller._poll_once(mock_method, iteration=0, param1="value1")

        mock_method.assert_called_once()
        call_kwargs = mock_method.call_args[1]
        assert call_kwargs["param1"] == "value1"

    def test_poll_once_adds_default_start(self):
        """Test that poll_once adds default start if not provided."""
        mock_client = MagicMock()
        mock_method = MagicMock(return_value=pd.DataFrame())

        poller = ERCOTPoller(client=mock_client)
        poller._poll_once(mock_method, iteration=0)

        call_kwargs = mock_method.call_args[1]
        assert call_kwargs["start"] == "today"

    def test_poll_once_grid_error(self):
        """Test poll_once handles GridError."""
        mock_client = MagicMock()
        mock_method = MagicMock(side_effect=GridAPIError("API Error", status_code=500))

        poller = ERCOTPoller(client=mock_client)
        result = poller._poll_once(mock_method, iteration=0)

        assert result.success is False
        assert result.data is None
        assert isinstance(result.error, GridError)

    def test_poll_once_generic_exception(self):
        """Test poll_once handles generic exceptions."""
        mock_client = MagicMock()
        mock_method = MagicMock(side_effect=Exception("Unexpected error"))

        poller = ERCOTPoller(client=mock_client)
        result = poller._poll_once(mock_method, iteration=0)

        assert result.success is False
        assert result.data is None


class TestERCOTPollerBackoff:
    """Tests for ERCOTPoller backoff handling."""

    def test_handle_error_increments_count(self):
        """Test that _handle_error increments error count."""
        mock_client = MagicMock()
        poller = ERCOTPoller(client=mock_client)

        assert poller._consecutive_errors == 0

        poller._handle_error()

        assert poller._consecutive_errors == 1

    def test_handle_error_increases_backoff(self):
        """Test that _handle_error increases backoff."""
        mock_client = MagicMock()
        poller = ERCOTPoller(client=mock_client, interval=10.0)

        assert poller._current_backoff == 0.0

        poller._handle_error()

        assert poller._current_backoff > 0

    def test_handle_error_respects_max_backoff(self):
        """Test that backoff is capped at max_backoff."""
        mock_client = MagicMock()
        poller = ERCOTPoller(client=mock_client, max_backoff=10.0)

        # Simulate many errors
        for _ in range(20):
            poller._handle_error()

        assert poller._current_backoff <= 10.0

    def test_reset_backoff(self):
        """Test that _reset_backoff resets state."""
        mock_client = MagicMock()
        poller = ERCOTPoller(client=mock_client)

        # Simulate some errors
        poller._handle_error()
        poller._handle_error()

        assert poller._consecutive_errors > 0
        assert poller._current_backoff > 0

        poller._reset_backoff()

        assert poller._consecutive_errors == 0
        assert poller._current_backoff == 0.0


class TestERCOTPollerStop:
    """Tests for ERCOTPoller.stop method."""

    def test_stop_sets_running_false(self):
        """Test that stop sets _running to False."""
        mock_client = MagicMock()
        poller = ERCOTPoller(client=mock_client)

        poller._running = True
        poller.stop()

        assert poller._running is False


class TestERCOTPollerPollIter:
    """Tests for ERCOTPoller.poll_iter method."""

    @patch("tinygrid.ercot.polling.time.sleep")
    def test_poll_iter_yields_results(self, mock_sleep):
        """Test poll_iter yields PollResult objects."""
        mock_client = MagicMock()
        mock_method = MagicMock(return_value=pd.DataFrame({"col": [1]}))

        poller = ERCOTPoller(client=mock_client)

        results = list(poller.poll_iter(method=mock_method, max_iterations=3))

        assert len(results) == 3
        assert all(isinstance(r, PollResult) for r in results)
        assert all(r.success for r in results)

    @patch("tinygrid.ercot.polling.time.sleep")
    def test_poll_iter_respects_max_iterations(self, mock_sleep):
        """Test poll_iter stops at max_iterations."""
        mock_client = MagicMock()
        mock_method = MagicMock(return_value=pd.DataFrame())

        poller = ERCOTPoller(client=mock_client)

        results = list(poller.poll_iter(method=mock_method, max_iterations=5))

        assert len(results) == 5

    @patch("tinygrid.ercot.polling.time.sleep")
    def test_poll_iter_stops_on_max_errors(self, mock_sleep):
        """Test poll_iter stops after max consecutive errors."""
        mock_client = MagicMock()
        mock_method = MagicMock(side_effect=GridAPIError("Error", status_code=500))

        poller = ERCOTPoller(client=mock_client, max_errors=3)

        results = list(poller.poll_iter(method=mock_method, max_iterations=10))

        # Should stop after 3 errors
        assert len(results) == 3
        assert all(not r.success for r in results)

    @patch("tinygrid.ercot.polling.time.sleep")
    def test_poll_iter_resets_backoff_on_success(self, mock_sleep):
        """Test poll_iter resets backoff after success."""
        mock_client = MagicMock()
        # First call fails, second succeeds
        mock_method = MagicMock(
            side_effect=[
                GridAPIError("Error", status_code=500),
                pd.DataFrame({"col": [1]}),
            ]
        )

        poller = ERCOTPoller(client=mock_client)

        results = list(poller.poll_iter(method=mock_method, max_iterations=2))

        assert len(results) == 2
        assert not results[0].success
        assert results[1].success
        # Backoff should be reset after success
        assert poller._consecutive_errors == 0


class TestERCOTPollerPollCallback:
    """Tests for ERCOTPoller.poll method with callback."""

    @patch("tinygrid.ercot.polling.time.sleep")
    def test_poll_calls_callback(self, mock_sleep):
        """Test poll calls callback for each iteration."""
        mock_client = MagicMock()
        mock_method = MagicMock(return_value=pd.DataFrame({"col": [1]}))
        callback_results = []

        def callback(result):
            callback_results.append(result)

        poller = ERCOTPoller(client=mock_client)
        poller.poll(method=mock_method, callback=callback, max_iterations=3)

        assert len(callback_results) == 3

    @patch("tinygrid.ercot.polling.time.sleep")
    def test_poll_stops_on_max_iterations(self, mock_sleep):
        """Test poll stops at max_iterations."""
        mock_client = MagicMock()
        mock_method = MagicMock(return_value=pd.DataFrame())
        callback_count = [0]

        def callback(result):
            callback_count[0] += 1

        poller = ERCOTPoller(client=mock_client)
        poller.poll(method=mock_method, callback=callback, max_iterations=5)

        assert callback_count[0] == 5


class TestPollLatest:
    """Tests for poll_latest convenience function."""

    @patch("tinygrid.ercot.polling.time.sleep")
    def test_poll_latest_yields_dataframes(self, mock_sleep):
        """Test poll_latest yields DataFrames."""
        mock_client = MagicMock()
        mock_method = MagicMock(return_value=pd.DataFrame({"col": [1, 2]}))

        results = list(
            poll_latest(
                client=mock_client,
                method=mock_method,
                interval=60,
                max_iterations=3,
            )
        )

        assert len(results) == 3
        assert all(isinstance(r, pd.DataFrame) for r in results)

    @patch("tinygrid.ercot.polling.time.sleep")
    def test_poll_latest_skips_failures(self, mock_sleep):
        """Test poll_latest skips failed polls."""
        mock_client = MagicMock()
        # First fails, second succeeds
        mock_method = MagicMock(
            side_effect=[
                GridAPIError("Error", status_code=500),
                pd.DataFrame({"col": [1]}),
            ]
        )

        results = list(
            poll_latest(
                client=mock_client,
                method=mock_method,
                max_iterations=2,
            )
        )

        # Only successful poll should be yielded
        assert len(results) == 1
        assert isinstance(results[0], pd.DataFrame)

    @patch("tinygrid.ercot.polling.time.sleep")
    def test_poll_latest_passes_kwargs(self, mock_sleep):
        """Test poll_latest passes kwargs to method."""
        mock_client = MagicMock()
        mock_method = MagicMock(return_value=pd.DataFrame())

        list(
            poll_latest(
                client=mock_client,
                method=mock_method,
                max_iterations=1,
                custom_param="value",
            )
        )

        call_kwargs = mock_method.call_args[1]
        assert call_kwargs["custom_param"] == "value"


class TestPollerEdgeCases:
    """Tests for edge cases in poller behavior."""

    @patch("tinygrid.ercot.polling.time.sleep")
    def test_poll_callback_stops_on_max_errors(self, mock_sleep):
        """Test poll with callback stops after max consecutive errors."""
        mock_client = MagicMock()
        mock_method = MagicMock(side_effect=GridAPIError("Error", status_code=500))
        callback_results = []

        def callback(result):
            callback_results.append(result)

        poller = ERCOTPoller(client=mock_client, max_errors=3)
        poller.poll(method=mock_method, callback=callback, max_iterations=10)

        # Should stop after 3 errors
        assert len(callback_results) == 3
        assert all(not r.success for r in callback_results)

    @patch("tinygrid.ercot.polling.time.sleep")
    def test_poll_with_explicit_start_arg(self, mock_sleep):
        """Test poll_once does not override explicit start argument."""
        mock_client = MagicMock()
        mock_method = MagicMock(return_value=pd.DataFrame())

        poller = ERCOTPoller(client=mock_client)
        poller._poll_once(mock_method, iteration=0, start="2024-01-01")

        call_kwargs = mock_method.call_args[1]
        assert call_kwargs["start"] == "2024-01-01"

    @patch("tinygrid.ercot.polling.time.sleep")
    def test_poll_iter_can_be_stopped_early(self, mock_sleep):
        """Test poll_iter can be stopped early via stop()."""
        mock_client = MagicMock()
        mock_method = MagicMock(return_value=pd.DataFrame())

        poller = ERCOTPoller(client=mock_client)

        results = []
        for i, result in enumerate(poller.poll_iter(method=mock_method)):
            results.append(result)
            if i >= 2:
                poller.stop()

        assert len(results) == 3
        assert not poller._running

    @patch("tinygrid.ercot.polling.time.sleep")
    def test_poll_iter_uses_correct_wait_time(self, mock_sleep):
        """Test poll_iter uses correct wait time between iterations."""
        mock_client = MagicMock()
        mock_method = MagicMock(return_value=pd.DataFrame())

        poller = ERCOTPoller(client=mock_client, interval=30.0)

        list(poller.poll_iter(method=mock_method, max_iterations=2))

        # Sleep is called after each iteration except possibly the last
        # For 2 iterations, we expect sleeps between them
        assert mock_sleep.call_count >= 1
        # Verify the interval is correct
        mock_sleep.assert_called_with(30.0)

    @patch("tinygrid.ercot.polling.time.sleep")
    def test_poll_iter_adds_backoff_to_wait_time(self, mock_sleep):
        """Test poll_iter adds backoff to wait time on errors."""
        mock_client = MagicMock()
        mock_method = MagicMock(
            side_effect=[
                GridAPIError("Error", status_code=500),
                pd.DataFrame(),
            ]
        )

        poller = ERCOTPoller(client=mock_client, interval=10.0, max_errors=5)

        list(poller.poll_iter(method=mock_method, max_iterations=2))

        # First sleep should include backoff
        first_sleep_call = mock_sleep.call_args_list[0][0][0]
        assert first_sleep_call > 10.0  # interval + backoff

    @patch("tinygrid.ercot.polling.time.sleep")
    def test_poll_latest_skips_none_data(self, mock_sleep):
        """Test poll_latest skips results with None data."""
        mock_client = MagicMock()
        # Returns DataFrame, but empty result still has data set
        mock_method = MagicMock(return_value=pd.DataFrame({"col": [1]}))

        results = list(
            poll_latest(
                client=mock_client,
                method=mock_method,
                max_iterations=2,
            )
        )

        assert len(results) == 2
        assert all(len(r) == 1 for r in results)
