"""Tests for tinygrid.utils.rate_limiter module."""

from __future__ import annotations

import time

import pytest

from tinygrid.utils.rate_limiter import (
    ERCOT_REQUESTS_PER_MINUTE,
    AsyncRateLimiter,
    RateLimiter,
    rate_limited,
)


class TestRateLimiterConstants:
    """Tests for rate limiter constants."""

    def test_ercot_requests_per_minute(self):
        """Test ERCOT rate limit constant."""
        assert ERCOT_REQUESTS_PER_MINUTE == 30


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_initialization_defaults(self):
        """Test default initialization."""
        limiter = RateLimiter()
        assert limiter.requests_per_minute == 30
        assert limiter.burst_size == 30
        assert limiter.available_tokens == 30

    def test_initialization_custom_rate(self):
        """Test custom rate initialization."""
        limiter = RateLimiter(requests_per_minute=60)
        assert limiter.requests_per_minute == 60
        assert limiter.burst_size == 60

    def test_initialization_custom_burst_size(self):
        """Test custom burst size initialization."""
        limiter = RateLimiter(requests_per_minute=30, burst_size=10)
        assert limiter.burst_size == 10
        assert limiter.available_tokens == 10

    def test_min_interval(self):
        """Test min_interval property."""
        limiter = RateLimiter(requests_per_minute=60)
        assert limiter.min_interval == 1.0  # 60 seconds / 60 requests

        limiter = RateLimiter(requests_per_minute=30)
        assert limiter.min_interval == 2.0  # 60 seconds / 30 requests

    def test_acquire_consumes_token(self):
        """Test that acquire consumes a token."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=10)
        initial_tokens = limiter.available_tokens

        limiter.acquire()

        assert limiter.available_tokens < initial_tokens

    def test_acquire_burst(self):
        """Test acquiring multiple tokens in burst."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=5)

        # Should be able to acquire 5 tokens immediately
        for _ in range(5):
            result = limiter.acquire(timeout=0.01)
            assert result is True

    def test_acquire_with_timeout_fails_when_empty(self):
        """Test that acquire with timeout returns False when no tokens."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=1)
        limiter.acquire()  # Consume the only token

        # Should timeout waiting for another token
        result = limiter.acquire(timeout=0.01)
        assert result is False

    def test_tokens_refill_over_time(self):
        """Test that tokens refill over time."""
        limiter = RateLimiter(requests_per_minute=600, burst_size=10)  # 10/second

        # Consume all tokens
        for _ in range(10):
            limiter.acquire()

        assert limiter.available_tokens < 1

        # Wait for refill
        time.sleep(0.2)

        # Should have refilled some tokens
        assert limiter.available_tokens >= 1

    def test_context_manager(self):
        """Test context manager usage."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=10)
        initial = limiter.available_tokens

        with limiter:
            pass

        assert limiter.available_tokens < initial

    def test_release_is_noop(self):
        """Test that release does nothing (token bucket pattern)."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=10)
        limiter.acquire()

        # Store count, call release immediately
        initial_count = limiter._tokens  # Use internal state, not property
        limiter.release()

        # Release should not change token count (internal state unchanged)
        assert limiter._tokens == initial_count

    def test_reset(self):
        """Test reset restores full capacity."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=10)

        # Consume some tokens
        for _ in range(5):
            limiter.acquire()

        limiter.reset()

        assert limiter.available_tokens == 10


class TestAsyncRateLimiter:
    """Tests for AsyncRateLimiter class."""

    def test_initialization_defaults(self):
        """Test default initialization."""
        limiter = AsyncRateLimiter()
        assert limiter.requests_per_minute == 30
        assert limiter.burst_size == 30

    def test_initialization_custom(self):
        """Test custom initialization."""
        limiter = AsyncRateLimiter(requests_per_minute=60, burst_size=10)
        assert limiter.requests_per_minute == 60
        assert limiter.burst_size == 10

    @pytest.mark.asyncio
    async def test_acquire_consumes_token(self):
        """Test that acquire consumes a token."""
        limiter = AsyncRateLimiter(requests_per_minute=60, burst_size=10)
        initial = limiter.available_tokens

        await limiter.acquire()

        assert limiter.available_tokens < initial

    @pytest.mark.asyncio
    async def test_acquire_burst(self):
        """Test acquiring multiple tokens in burst."""
        limiter = AsyncRateLimiter(requests_per_minute=60, burst_size=5)

        # Should be able to acquire 5 tokens immediately
        for _ in range(5):
            result = await limiter.acquire(timeout=0.01)
            assert result is True

    @pytest.mark.asyncio
    async def test_acquire_with_timeout_fails_when_empty(self):
        """Test that acquire with timeout returns False when no tokens."""
        limiter = AsyncRateLimiter(requests_per_minute=60, burst_size=1)
        await limiter.acquire()  # Consume the only token

        # Should timeout waiting for another token
        result = await limiter.acquire(timeout=0.01)
        assert result is False

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test async context manager usage."""
        limiter = AsyncRateLimiter(requests_per_minute=60, burst_size=10)
        initial = limiter.available_tokens

        async with limiter:
            pass

        assert limiter.available_tokens < initial

    @pytest.mark.asyncio
    async def test_release_is_noop(self):
        """Test that release does nothing."""
        limiter = AsyncRateLimiter(requests_per_minute=60, burst_size=10)
        await limiter.acquire()

        # Store internal count, call release immediately
        initial_count = limiter._tokens  # Use internal state
        await limiter.release()

        # Release should not change token count
        assert limiter._tokens == initial_count

    def test_reset(self):
        """Test reset restores full capacity."""
        limiter = AsyncRateLimiter(requests_per_minute=60, burst_size=10)

        # Manually reduce tokens
        limiter._tokens = 2

        limiter.reset()

        assert limiter.available_tokens == 10


class TestRateLimitedDecorator:
    """Tests for rate_limited decorator."""

    def test_decorator_with_default_limiter(self):
        """Test decorator creates default limiter."""
        call_count = 0

        @rate_limited()
        def my_func():
            nonlocal call_count
            call_count += 1
            return "result"

        result = my_func()

        assert result == "result"
        assert call_count == 1

    def test_decorator_with_custom_rate(self):
        """Test decorator with custom rate."""

        @rate_limited(requests_per_minute=60)
        def my_func():
            return "result"

        result = my_func()
        assert result == "result"

    def test_decorator_with_existing_limiter(self):
        """Test decorator with existing limiter."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=10)
        initial = limiter.available_tokens

        @rate_limited(limiter=limiter)
        def my_func():
            return "result"

        result = my_func()

        assert result == "result"
        assert limiter.available_tokens < initial

    def test_decorator_preserves_function_metadata(self):
        """Test decorator preserves function name and docstring."""

        @rate_limited()
        def my_documented_func():
            """This is my docstring."""
            return "result"

        assert my_documented_func.__name__ == "my_documented_func"
        assert my_documented_func.__doc__ == """This is my docstring."""

    def test_decorator_passes_arguments(self):
        """Test decorator passes args and kwargs correctly."""

        @rate_limited()
        def add(a, b, c=0):
            return a + b + c

        assert add(1, 2) == 3
        assert add(1, 2, c=3) == 6


class TestRateLimiterEdgeCases:
    """Edge case tests for rate limiter."""

    def test_very_high_rate(self):
        """Test with very high rate limit."""
        limiter = RateLimiter(requests_per_minute=6000)  # 100/second
        assert limiter.min_interval == 0.01

    def test_very_low_rate(self):
        """Test with very low rate limit."""
        limiter = RateLimiter(requests_per_minute=1)
        assert limiter.min_interval == 60.0

    def test_fractional_burst_size(self):
        """Test with fractional burst size."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=1.5)
        assert limiter.burst_size == 1.5

    def test_concurrent_acquire(self):
        """Test thread safety with concurrent acquires."""
        import threading

        limiter = RateLimiter(requests_per_minute=600, burst_size=100)
        results = []

        def acquire_token():
            result = limiter.acquire(timeout=1.0)
            results.append(result)

        threads = [threading.Thread(target=acquire_token) for _ in range(50)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should succeed since we have 100 burst capacity
        assert all(results)
        assert len(results) == 50
