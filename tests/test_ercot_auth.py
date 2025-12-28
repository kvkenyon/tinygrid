"""Tests for ERCOT authentication module."""

import time

import httpx
import pytest
import respx

from tinygrid.auth import ERCOTAuth, ERCOTAuthConfig
from tinygrid.errors import GridAuthenticationError


class TestERCOTAuthConfig:
    """Test ERCOTAuthConfig configuration."""

    def test_auth_config_defaults(self):
        """Test that ERCOTAuthConfig has correct default values."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="key123",
        )

        assert config.username == "test@example.com"
        assert config.password == "password123"
        assert config.subscription_key == "key123"
        assert (
            config.auth_url
            == "https://ercotb2c.b2clogin.com/ercotb2c.onmicrosoft.com/B2C_1_PUBAPI-ROPC-FLOW/oauth2/v2.0/token"
        )
        assert config.client_id == "fec253ea-0d06-4272-a5e6-b478baeecd70"
        assert config.token_cache_ttl == 3300

    def test_auth_config_custom_values(self):
        """Test ERCOTAuthConfig with custom values."""
        config = ERCOTAuthConfig(
            username="custom@example.com",
            password="custompass",
            subscription_key="customkey",
            auth_url="https://custom.auth.url",
            client_id="custom-client-id",
            token_cache_ttl=1800,
        )

        assert config.username == "custom@example.com"
        assert config.password == "custompass"
        assert config.subscription_key == "customkey"
        assert config.auth_url == "https://custom.auth.url"
        assert config.client_id == "custom-client-id"
        assert config.token_cache_ttl == 1800


class TestERCOTAuthTokenCaching:
    """Test ERCOT authentication token caching logic."""

    def test_is_token_valid_no_token(self):
        """Test that _is_token_valid returns False when no token is cached."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="key123",
        )
        auth = ERCOTAuth(config)

        assert auth._is_token_valid() is False

    def test_is_token_valid_expired_token(self):
        """Test that _is_token_valid returns False when token is expired."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="key123",
        )
        auth = ERCOTAuth(config)
        auth._cached_token = "expired-token"
        auth._token_expires_at = time.time() - 100  # Expired 100 seconds ago

        assert auth._is_token_valid() is False

    def test_is_token_valid_current_token(self):
        """Test that _is_token_valid returns True when token is still valid."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="key123",
        )
        auth = ERCOTAuth(config)
        auth._cached_token = "valid-token"
        auth._token_expires_at = time.time() + 1000  # Expires in 1000 seconds

        assert auth._is_token_valid() is True

    def test_clear_token_cache(self):
        """Test that clear_token_cache clears the cached token."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="key123",
        )
        auth = ERCOTAuth(config)
        auth._cached_token = "valid-token"
        auth._token_expires_at = time.time() + 1000

        auth.clear_token_cache()

        assert auth._cached_token is None
        assert auth._token_expires_at is None

    def test_get_subscription_key(self):
        """Test that get_subscription_key returns the subscription key."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="my-sub-key",
        )
        auth = ERCOTAuth(config)

        assert auth.get_subscription_key() == "my-sub-key"


class TestERCOTAuthSyncTokenFetch:
    """Test ERCOT authentication synchronous token fetching."""

    @respx.mock
    def test_fetch_token_sync_success_access_token(self):
        """Test successful token fetch with access_token in response."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="key123",
        )
        auth = ERCOTAuth(config)

        # Mock the authentication endpoint
        respx.post(url__regex=r".*ercotb2c\.b2clogin\.com.*").mock(
            return_value=httpx.Response(200, json={"access_token": "test-access-token"})
        )

        token = auth._fetch_token_sync()

        assert token == "test-access-token"

    @respx.mock
    def test_fetch_token_sync_success_id_token(self):
        """Test successful token fetch with id_token in response."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="key123",
        )
        auth = ERCOTAuth(config)

        # Mock the authentication endpoint
        respx.post(url__regex=r".*ercotb2c\.b2clogin\.com.*").mock(
            return_value=httpx.Response(200, json={"id_token": "test-id-token"})
        )

        token = auth._fetch_token_sync()

        assert token == "test-id-token"

    @respx.mock
    def test_fetch_token_sync_http_error(self):
        """Test token fetch with HTTP error response."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="key123",
        )
        auth = ERCOTAuth(config)

        # Mock a 401 unauthorized response
        respx.post(url__regex=r".*ercotb2c\.b2clogin\.com.*").mock(
            return_value=httpx.Response(
                401,
                json={
                    "error": "invalid_credentials",
                    "error_description": "Invalid username or password",
                },
            )
        )

        with pytest.raises(GridAuthenticationError) as exc_info:
            auth._fetch_token_sync()

        assert exc_info.value.status_code == 401
        assert "ERCOT authentication failed with status 401" in str(exc_info.value)

    @respx.mock
    def test_fetch_token_sync_invalid_json(self):
        """Test token fetch with invalid JSON response."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="key123",
        )
        auth = ERCOTAuth(config)

        # Mock a response with invalid JSON
        respx.post(url__regex=r".*ercotb2c\.b2clogin\.com.*").mock(
            return_value=httpx.Response(200, text="invalid json response")
        )

        with pytest.raises(GridAuthenticationError) as exc_info:
            auth._fetch_token_sync()

        assert "Failed to parse authentication response as JSON" in str(exc_info.value)

    @respx.mock
    def test_fetch_token_sync_no_token_in_response(self):
        """Test token fetch when response has no access_token or id_token."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="key123",
        )
        auth = ERCOTAuth(config)

        # Mock a response without token
        respx.post(url__regex=r".*ercotb2c\.b2clogin\.com.*").mock(
            return_value=httpx.Response(200, json={"some_field": "some_value"})
        )

        with pytest.raises(GridAuthenticationError) as exc_info:
            auth._fetch_token_sync()

        assert "No access token in ERCOT authentication response" in str(exc_info.value)

    @respx.mock
    def test_fetch_token_sync_timeout(self):
        """Test token fetch with timeout."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="key123",
        )
        auth = ERCOTAuth(config)

        # Mock a timeout
        respx.post(url__regex=r".*ercotb2c\.b2clogin\.com.*").mock(
            side_effect=httpx.TimeoutException("Timeout")
        )

        with pytest.raises(GridAuthenticationError) as exc_info:
            auth._fetch_token_sync()

        assert "ERCOT authentication request timed out" in str(exc_info.value)

    @respx.mock
    def test_fetch_token_sync_request_error(self):
        """Test token fetch with request error."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="key123",
        )
        auth = ERCOTAuth(config)

        # Mock a request error
        respx.post(url__regex=r".*ercotb2c\.b2clogin\.com.*").mock(
            side_effect=httpx.ConnectError("Connection failed")
        )

        with pytest.raises(GridAuthenticationError) as exc_info:
            auth._fetch_token_sync()

        assert "ERCOT authentication request failed" in str(exc_info.value)

    @respx.mock
    def test_fetch_token_sync_unexpected_error(self):
        """Test token fetch with unexpected error."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="key123",
        )
        auth = ERCOTAuth(config)

        # Mock an unexpected error
        respx.post(url__regex=r".*ercotb2c\.b2clogin\.com.*").mock(
            side_effect=RuntimeError("Unexpected error")
        )

        with pytest.raises(GridAuthenticationError) as exc_info:
            auth._fetch_token_sync()

        assert "Unexpected error during ERCOT authentication" in str(exc_info.value)


class TestERCOTAuthAsyncTokenFetch:
    """Test ERCOT authentication asynchronous token fetching."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_token_async_success_access_token(self):
        """Test successful async token fetch with access_token in response."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="key123",
        )
        auth = ERCOTAuth(config)

        # Mock the authentication endpoint
        respx.post(url__regex=r".*ercotb2c\.b2clogin\.com.*").mock(
            return_value=httpx.Response(
                200, json={"access_token": "test-access-token-async"}
            )
        )

        token = await auth._fetch_token_async()

        assert token == "test-access-token-async"

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_token_async_success_id_token(self):
        """Test successful async token fetch with id_token in response."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="key123",
        )
        auth = ERCOTAuth(config)

        # Mock the authentication endpoint
        respx.post(url__regex=r".*ercotb2c\.b2clogin\.com.*").mock(
            return_value=httpx.Response(200, json={"id_token": "test-id-token-async"})
        )

        token = await auth._fetch_token_async()

        assert token == "test-id-token-async"

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_token_async_http_error(self):
        """Test async token fetch with HTTP error response."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="key123",
        )
        auth = ERCOTAuth(config)

        # Mock a 401 unauthorized response
        respx.post(url__regex=r".*ercotb2c\.b2clogin\.com.*").mock(
            return_value=httpx.Response(
                401,
                json={
                    "error": "invalid_credentials",
                    "error_description": "Invalid username or password",
                },
            )
        )

        with pytest.raises(GridAuthenticationError) as exc_info:
            await auth._fetch_token_async()

        assert exc_info.value.status_code == 401
        assert "ERCOT authentication failed with status 401" in str(exc_info.value)

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_token_async_invalid_json(self):
        """Test async token fetch with invalid JSON response."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="key123",
        )
        auth = ERCOTAuth(config)

        # Mock a response with invalid JSON
        respx.post(url__regex=r".*ercotb2c\.b2clogin\.com.*").mock(
            return_value=httpx.Response(200, text="invalid json response")
        )

        with pytest.raises(GridAuthenticationError) as exc_info:
            await auth._fetch_token_async()

        assert "Failed to parse authentication response as JSON" in str(exc_info.value)

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_token_async_no_token_in_response(self):
        """Test async token fetch when response has no access_token or id_token."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="key123",
        )
        auth = ERCOTAuth(config)

        # Mock a response without token
        respx.post(url__regex=r".*ercotb2c\.b2clogin\.com.*").mock(
            return_value=httpx.Response(200, json={"some_field": "some_value"})
        )

        with pytest.raises(GridAuthenticationError) as exc_info:
            await auth._fetch_token_async()

        assert "No access token in ERCOT authentication response" in str(exc_info.value)

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_token_async_timeout(self):
        """Test async token fetch with timeout."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="key123",
        )
        auth = ERCOTAuth(config)

        # Mock a timeout
        respx.post(url__regex=r".*ercotb2c\.b2clogin\.com.*").mock(
            side_effect=httpx.TimeoutException("Timeout")
        )

        with pytest.raises(GridAuthenticationError) as exc_info:
            await auth._fetch_token_async()

        assert "ERCOT authentication request timed out" in str(exc_info.value)

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_token_async_request_error(self):
        """Test async token fetch with request error."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="key123",
        )
        auth = ERCOTAuth(config)

        # Mock a request error
        respx.post(url__regex=r".*ercotb2c\.b2clogin\.com.*").mock(
            side_effect=httpx.ConnectError("Connection failed")
        )

        with pytest.raises(GridAuthenticationError) as exc_info:
            await auth._fetch_token_async()

        assert "ERCOT authentication request failed" in str(exc_info.value)

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_token_async_unexpected_error(self):
        """Test async token fetch with unexpected error."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="key123",
        )
        auth = ERCOTAuth(config)

        # Mock an unexpected error
        respx.post(url__regex=r".*ercotb2c\.b2clogin\.com.*").mock(
            side_effect=RuntimeError("Unexpected error")
        )

        with pytest.raises(GridAuthenticationError) as exc_info:
            await auth._fetch_token_async()

        assert "Unexpected error during ERCOT authentication" in str(exc_info.value)


class TestERCOTAuthGetToken:
    """Test ERCOT authentication get_token methods."""

    @respx.mock
    def test_get_token_fetches_new_token(self):
        """Test that get_token fetches a new token when cache is empty."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="key123",
        )
        auth = ERCOTAuth(config)

        # Mock the authentication endpoint
        respx.post(url__regex=r".*ercotb2c\.b2clogin\.com.*").mock(
            return_value=httpx.Response(200, json={"access_token": "new-token"})
        )

        token = auth.get_token()

        assert token == "new-token"
        assert auth._cached_token == "new-token"
        assert auth._token_expires_at is not None

    @respx.mock
    def test_get_token_uses_cached_token(self):
        """Test that get_token uses cached token when valid."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="key123",
        )
        auth = ERCOTAuth(config)

        # Set a valid cached token
        auth._cached_token = "cached-token"
        auth._token_expires_at = time.time() + 1000

        # Mock should not be called
        respx.post(url__regex=r".*ercotb2c\.b2clogin\.com.*").mock(
            return_value=httpx.Response(
                200, json={"access_token": "should-not-be-called"}
            )
        )

        token = auth.get_token()

        assert token == "cached-token"

    @respx.mock
    def test_get_token_refreshes_expired_token(self):
        """Test that get_token fetches a new token when cached token is expired."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="key123",
        )
        auth = ERCOTAuth(config)

        # Set an expired cached token
        auth._cached_token = "expired-token"
        auth._token_expires_at = time.time() - 100

        # Mock the authentication endpoint
        respx.post(url__regex=r".*ercotb2c\.b2clogin\.com.*").mock(
            return_value=httpx.Response(200, json={"access_token": "refreshed-token"})
        )

        token = auth.get_token()

        assert token == "refreshed-token"
        assert auth._cached_token == "refreshed-token"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_token_async_fetches_new_token(self):
        """Test that get_token_async fetches a new token when cache is empty."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="key123",
        )
        auth = ERCOTAuth(config)

        # Mock the authentication endpoint
        respx.post(url__regex=r".*ercotb2c\.b2clogin\.com.*").mock(
            return_value=httpx.Response(200, json={"access_token": "new-async-token"})
        )

        token = await auth.get_token_async()

        assert token == "new-async-token"
        assert auth._cached_token == "new-async-token"
        assert auth._token_expires_at is not None

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_token_async_uses_cached_token(self):
        """Test that get_token_async uses cached token when valid."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="key123",
        )
        auth = ERCOTAuth(config)

        # Set a valid cached token
        auth._cached_token = "cached-async-token"
        auth._token_expires_at = time.time() + 1000

        # Mock should not be called
        respx.post(url__regex=r".*ercotb2c\.b2clogin\.com.*").mock(
            return_value=httpx.Response(
                200, json={"access_token": "should-not-be-called"}
            )
        )

        token = await auth.get_token_async()

        assert token == "cached-async-token"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_token_async_refreshes_expired_token(self):
        """Test that get_token_async fetches a new token when cached token is expired."""
        config = ERCOTAuthConfig(
            username="test@example.com",
            password="password123",
            subscription_key="key123",
        )
        auth = ERCOTAuth(config)

        # Set an expired cached token
        auth._cached_token = "expired-async-token"
        auth._token_expires_at = time.time() - 100

        # Mock the authentication endpoint
        respx.post(url__regex=r".*ercotb2c\.b2clogin\.com.*").mock(
            return_value=httpx.Response(
                200, json={"access_token": "refreshed-async-token"}
            )
        )

        token = await auth.get_token_async()

        assert token == "refreshed-async-token"
        assert auth._cached_token == "refreshed-async-token"
