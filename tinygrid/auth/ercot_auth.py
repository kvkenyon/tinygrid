"""ERCOT API authentication handler"""

import time

import httpx
from attrs import define, field

from ..errors import GridAuthenticationError


@define
class ERCOTAuthConfig:
    """Configuration for ERCOT API authentication.

    Args:
        username: ERCOT API username (email)
        password: ERCOT API password
        subscription_key: ERCOT API subscription key (obtained from API Explorer)
        auth_url: Authentication endpoint URL. Defaults to ERCOT's Azure B2C endpoint.
        client_id: Azure B2C client ID. Defaults to ERCOT's public API client ID.
        token_cache_ttl: Token cache time-to-live in seconds. Defaults to 3300 (55 minutes)
            to refresh before the 1-hour token expires.
    """

    username: str
    password: str
    subscription_key: str
    auth_url: str = field(
        default="https://ercotb2c.b2clogin.com/ercotb2c.onmicrosoft.com/B2C_1_PUBAPI-ROPC-FLOW/oauth2/v2.0/token",
        kw_only=True,
    )
    client_id: str = field(
        default="fec253ea-0d06-4272-a5e6-b478baeecd70",
        kw_only=True,
    )
    token_cache_ttl: int = field(default=3300, kw_only=True)  # 55 minutes


@define
class ERCOTAuth:
    """Handles ERCOT API authentication and token management.

    Manages the authentication flow for ERCOT API:
    1. Obtains ID token using username/password
    2. Caches token for reuse
    3. Automatically refreshes token when expired

    Example:
        ```python
        from tinygrid.auth import ERCOTAuth, ERCOTAuthConfig

        config = ERCOTAuthConfig(
            username="user@example.com",
            password="password",
            subscription_key="your-subscription-key"
        )
        auth = ERCOTAuth(config)
        token = await auth.get_token()  # or auth.get_token() for sync
        ```
    """

    config: ERCOTAuthConfig
    _cached_token: str | None = field(default=None, init=False, repr=False)
    _token_expires_at: float | None = field(
        default=None, init=False, repr=False
    )

    def _is_token_valid(self) -> bool:
        """Check if the cached token is still valid.

        Returns:
            True if token exists and hasn't expired, False otherwise
        """
        if self._cached_token is None or self._token_expires_at is None:
            return False
        return time.time() < self._token_expires_at

    def _fetch_token_sync(self) -> str:
        """Fetch a new ID token from ERCOT API (synchronous).

        Returns:
            ID token string

        Raises:
            GridAuthenticationError: If authentication fails
        """
        try:
            with httpx.Client(timeout=30.0) as client:
                # ERCOT uses Azure B2C ROPC flow with query parameters in URL
                scope = f"openid+{self.config.client_id}+offline_access"
                # Build URL with query parameters (as per ERCOT documentation)
                # URL-encode values to handle special characters
                auth_url_with_params = (
                    f"{self.config.auth_url}"
                    f"?username={self.config.username}"
                    f"&password={self.config.password}"
                    f"&grant_type=password"
                    f"&scope={scope}"
                    f"&client_id={self.config.client_id}"
                    f"&response_type=id_token"
                )
                response = client.post(
                    auth_url_with_params,
                )

                if response.status_code != 200:
                    error_msg = (
                        f"ERCOT authentication failed with status {response.status_code}. "
                        f"URL: {self.config.auth_url}. "
                        f"Response: {response.text[:500]}"
                    )
                    raise GridAuthenticationError(
                        error_msg,
                        status_code=response.status_code,
                        response_body=response.text,
                        endpoint=self.config.auth_url,
                    )

                try:
                    data = response.json()
                except Exception as e:
                    raise GridAuthenticationError(
                        f"Failed to parse authentication response as JSON: {e}. "
                        f"Response: {response.text[:500]}",
                        status_code=response.status_code,
                        response_body=response.text,
                        endpoint=self.config.auth_url,
                    ) from e

                # ERCOT Azure B2C may return access_token or id_token
                access_token = data.get("access_token") or data.get("id_token")

                if not access_token:
                    raise GridAuthenticationError(
                        "No access token in ERCOT authentication response",
                        status_code=response.status_code,
                        response_body=response.text,
                        endpoint=self.config.auth_url,
                    )

                return access_token

        except httpx.TimeoutException as e:
            raise GridAuthenticationError(
                "ERCOT authentication request timed out",
                endpoint=self.config.auth_url,
            ) from e
        except httpx.RequestError as e:
            raise GridAuthenticationError(
                f"ERCOT authentication request failed: {e}",
                endpoint=self.config.auth_url,
            ) from e
        except Exception as e:
            if isinstance(e, GridAuthenticationError):
                raise
            raise GridAuthenticationError(
                f"Unexpected error during ERCOT authentication: {e}",
                endpoint=self.config.auth_url,
            ) from e

    async def _fetch_token_async(self) -> str:
        """Fetch a new ID token from ERCOT API (asynchronous).

        Returns:
            ID token string

        Raises:
            GridAuthenticationError: If authentication fails
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # ERCOT uses Azure B2C ROPC flow with query parameters in URL
                scope = f"openid+{self.config.client_id}+offline_access"
                # Build URL with query parameters (as per ERCOT documentation)
                # URL-encode values to handle special characters
                auth_url_with_params = (
                    f"{self.config.auth_url}"
                    f"?username={self.config.username}"
                    f"&password={self.config.password}"
                    f"&grant_type=password"
                    f"&scope={scope}"
                    f"&client_id={self.config.client_id}"
                    f"&response_type=id_token"
                )
                response = await client.post(
                    auth_url_with_params,
                )

                if response.status_code != 200:
                    error_msg = (
                        f"ERCOT authentication failed with status {response.status_code}. "
                        f"URL: {self.config.auth_url}. "
                        f"Response: {response.text[:500]}"
                    )
                    raise GridAuthenticationError(
                        error_msg,
                        status_code=response.status_code,
                        response_body=response.text,
                        endpoint=self.config.auth_url,
                    )

                try:
                    data = response.json()
                except Exception as e:
                    raise GridAuthenticationError(
                        f"Failed to parse authentication response as JSON: {e}. "
                        f"Response: {response.text[:500]}",
                        status_code=response.status_code,
                        response_body=response.text,
                        endpoint=self.config.auth_url,
                    ) from e

                # ERCOT Azure B2C may return access_token or id_token
                access_token = data.get("access_token") or data.get("id_token")

                if not access_token:
                    raise GridAuthenticationError(
                        "No access token in ERCOT authentication response",
                        status_code=response.status_code,
                        response_body=response.text,
                        endpoint=self.config.auth_url,
                    )

                return access_token

        except httpx.TimeoutException as e:
            raise GridAuthenticationError(
                "ERCOT authentication request timed out",
                endpoint=self.config.auth_url,
            ) from e
        except httpx.RequestError as e:
            raise GridAuthenticationError(
                f"ERCOT authentication request failed: {e}",
                endpoint=self.config.auth_url,
            ) from e
        except Exception as e:
            if isinstance(e, GridAuthenticationError):
                raise
            raise GridAuthenticationError(
                f"Unexpected error during ERCOT authentication: {e}",
                endpoint=self.config.auth_url,
            ) from e

    def get_token(self) -> str:
        """Get a valid ID token (synchronous).

        Returns cached token if valid, otherwise fetches a new one.

        Returns:
            ID token string

        Raises:
            GridAuthenticationError: If authentication fails
        """
        if self._is_token_valid():
            return self._cached_token  # type: ignore[return-value]

        token = self._fetch_token_sync()
        self._cached_token = token
        self._token_expires_at = time.time() + self.config.token_cache_ttl
        return token

    async def get_token_async(self) -> str:
        """Get a valid ID token (asynchronous).

        Returns cached token if valid, otherwise fetches a new one.

        Returns:
            ID token string

        Raises:
            GridAuthenticationError: If authentication fails
        """
        if self._is_token_valid():
            return self._cached_token  # type: ignore[return-value]

        token = await self._fetch_token_async()
        self._cached_token = token
        self._token_expires_at = time.time() + self.config.token_cache_ttl
        return token

    def get_subscription_key(self) -> str:
        """Get the subscription key.

        Returns:
            Subscription key string
        """
        return self.config.subscription_key

    def clear_token_cache(self) -> None:
        """Clear the cached token, forcing a refresh on next request."""
        self._cached_token = None
        self._token_expires_at = None
