"""ERCOT SDK client for accessing ERCOT grid data"""

from collections.abc import Callable
from typing import Any

from attrs import define, field

# Import endpoint modules (they have .sync() methods)
from pyercot.api.emil_products import get_list_for_products, get_product, get_product_history
from pyercot.api.np3_233_cd import hourly_res_outage_cap
from pyercot.api.np3_565_cd import lf_by_model_weather_zone
from pyercot.api.np3_566_cd import lf_by_model_study_area
from pyercot.api.np3_910_er import (
    endpoint_2d_agg_dsr_loads,
    endpoint_2d_agg_gen_summary,
    endpoint_2d_agg_gen_summary_houston,
    endpoint_2d_agg_gen_summary_north,
    endpoint_2d_agg_gen_summary_south,
    endpoint_2d_agg_gen_summary_west,
    endpoint_2d_agg_load_summary,
    endpoint_2d_agg_load_summary_houston,
    endpoint_2d_agg_load_summary_north,
    endpoint_2d_agg_load_summary_south,
    endpoint_2d_agg_load_summary_west,
    endpoint_2d_agg_out_sched,
    endpoint_2d_agg_out_sched_houston,
    endpoint_2d_agg_out_sched_north,
    endpoint_2d_agg_out_sched_south,
    endpoint_2d_agg_out_sched_west,
)
from pyercot.api.np3_911_er import (
    endpoint_2d_agg_as_offers_ecrsm,
    endpoint_2d_agg_as_offers_ecrss,
    endpoint_2d_agg_as_offers_offns,
    endpoint_2d_agg_as_offers_onns,
    endpoint_2d_agg_as_offers_regdn,
    endpoint_2d_agg_as_offers_regup,
    endpoint_2d_agg_as_offers_rrsffr,
    endpoint_2d_agg_as_offers_rrspfr,
    endpoint_2d_agg_as_offers_rrsufr,
    endpoint_2d_cleared_dam_as_ecrsm,
    endpoint_2d_cleared_dam_as_ecrss,
    endpoint_2d_cleared_dam_as_nspin,
    endpoint_2d_cleared_dam_as_regdn,
    endpoint_2d_cleared_dam_as_regup,
    endpoint_2d_cleared_dam_as_rrsffr,
    endpoint_2d_cleared_dam_as_rrspfr,
    endpoint_2d_cleared_dam_as_rrsufr,
    endpoint_2d_self_arranged_as_ecrsm,
    endpoint_2d_self_arranged_as_ecrss,
    endpoint_2d_self_arranged_as_nspin,
    endpoint_2d_self_arranged_as_nspnm,
    endpoint_2d_self_arranged_as_regdn,
    endpoint_2d_self_arranged_as_regup,
    endpoint_2d_self_arranged_as_rrsffr,
    endpoint_2d_self_arranged_as_rrspfr,
    endpoint_2d_self_arranged_as_rrsufr,
)
from pyercot.api.np3_965_er import (
    endpoint_60_hdl_ldl_man_override,
    endpoint_60_load_res_data_in_sced,
    endpoint_60_sced_dsr_load_data,
    endpoint_60_sced_gen_res_data,
    endpoint_60_sced_qse_self_arranged_as,
    endpoint_60_sced_smne_gen_res,
)
from pyercot.api.np3_966_er import (
    endpoint_60_dam_energy_bid_awards,
    endpoint_60_dam_energy_bids,
    endpoint_60_dam_energy_only_offer_awards,
    endpoint_60_dam_energy_only_offers,
    endpoint_60_dam_gen_res_as_offers,
    endpoint_60_dam_gen_res_data,
    endpoint_60_dam_load_res_as_offers,
    endpoint_60_dam_load_res_data,
    endpoint_60_dam_ptp_obl_bid_awards,
    endpoint_60_dam_ptp_obl_bids,
    endpoint_60_dam_ptp_obl_opt,
    endpoint_60_dam_ptp_obl_opt_awards,
    endpoint_60_dam_qse_self_as,
)
from pyercot.api.np3_990_ex import (
    endpoint_60_sasm_gen_res_as_offer_awards,
    endpoint_60_sasm_gen_res_as_offers,
    endpoint_60_sasm_load_res_as_offer_awards,
    endpoint_60_sasm_load_res_as_offers,
)
from pyercot.api.np3_991_ex import endpoint_60_cop_all_updates
from pyercot.api.np4_33_cd import dam_as_plan
from pyercot.api.np4_159_cd import load_distribution_factors
from pyercot.api.np4_179_cd import total_as_service_offers
from pyercot.api.np4_183_cd import dam_hourly_lmp
from pyercot.api.np4_188_cd import dam_clear_price_for_cap
from pyercot.api.np4_190_cd import dam_stlmnt_pnt_prices
from pyercot.api.np4_191_cd import dam_shadow_prices
from pyercot.api.np4_196_m import (
    dam_price_corrections_eblmp,
    dam_price_corrections_mcpc,
    dam_price_corrections_spp,
)
from pyercot.api.np4_197_m import (
    rtm_price_corrections_eblmp,
    rtm_price_corrections_shadow,
    rtm_price_corrections_soglmp,
    rtm_price_corrections_sogprice,
    rtm_price_corrections_splmp,
    rtm_price_corrections_spp,
)
from pyercot.api.np4_523_cd import dam_system_lambda
from pyercot.api.np4_732_cd import wpp_hrly_avrg_actl_fcast
from pyercot.api.np4_733_cd import wpp_actual_5min_avg_values
from pyercot.api.np4_737_cd import spp_hrly_avrg_actl_fcast
from pyercot.api.np4_738_cd import spp_actual_5min_avg_values
from pyercot.api.np4_742_cd import wpp_hrly_actual_fcast_geo
from pyercot.api.np4_743_cd import wpp_actual_5min_avg_values_geo
from pyercot.api.np4_745_cd import spp_hrly_actual_fcast_geo
from pyercot.api.np4_746_cd import spp_actual_5min_avg_values_geo
from pyercot.api.np6_86_cd import shdw_prices_bnd_trns_const
from pyercot.api.np6_322_cd import sced_system_lambda
from pyercot.api.np6_345_cd import act_sys_load_by_wzn
from pyercot.api.np6_346_cd import act_sys_load_by_fzn
from pyercot.api.np6_787_cd import lmp_electrical_bus
from pyercot.api.np6_788_cd import lmp_node_zone_hub
from pyercot.api.np6_905_cd import spp_node_zone_hub
from pyercot.api.np6_970_cd import get_data
from pyercot.api.versioning import get_version
from pyercot.errors import UnexpectedStatus

from pyercot import AuthenticatedClient
from pyercot import Client as ERCOTClient

from .auth import ERCOTAuth
from .base import BaseISOClient
from .errors import GridAPIError, GridAuthenticationError, GridError, GridTimeoutError


@define
class ERCOT(BaseISOClient):
    """ERCOT (Electric Reliability Council of Texas) SDK client.

    Provides a clean, intuitive interface for accessing ERCOT grid data without
    needing to know about endpoint paths, API categories, or client lifecycle management.

    Example:
        ```python
        from tinygrid import ERCOT

        ercot = ERCOT()
        forecast = ercot.get_load_forecast_by_weather_zone(
            start_date="2024-01-01",
            end_date="2024-01-07",
            model="WEATHERZONE"
        )
        ```

    Args:
        base_url: Base URL for the ERCOT API. Defaults to the official ERCOT API URL.
        timeout: Request timeout in seconds. Defaults to 30.0.
        verify_ssl: Whether to verify SSL certificates. Defaults to True.
        raise_on_error: Whether to raise exceptions on errors. Defaults to True.
        auth: Optional ERCOTAuth instance for authenticated requests. If provided,
            all requests will include the ID token and subscription key.
    """

    base_url: str = field(default="https://api.ercot.com/api/public-reports")
    timeout: float | None = field(default=30.0, kw_only=True)
    verify_ssl: bool = field(default=True, kw_only=True)
    raise_on_error: bool = field(default=True, kw_only=True)
    auth: ERCOTAuth | None = field(default=None, kw_only=True)

    _client: ERCOTClient | AuthenticatedClient | None = field(default=None, init=False, repr=False)

    @property
    def iso_name(self) -> str:
        """Return the name of the ISO."""
        return "ERCOT"

    def _get_client(self) -> ERCOTClient | AuthenticatedClient:
        """Get or create the underlying ERCOT API client.

        Automatically refreshes token if using authentication and token is expired.

        Returns:
            Configured ERCOTClient or AuthenticatedClient instance
        """
        if self.auth is not None:
            # Ensure we have a valid token (will refresh if expired)
            try:
                token = self.auth.get_token()
                subscription_key = self.auth.get_subscription_key()

                # Recreate client if token changed or client doesn't exist
                if (
                    self._client is None
                    or not isinstance(self._client, AuthenticatedClient)
                    or self._client.token != token
                ):
                    # Close existing client if it exists
                    if self._client is not None:
                        try:
                            if hasattr(self._client, "__exit__"):
                                self._client.__exit__(None, None, None)
                        except Exception:
                            pass  # Ignore errors when closing

                    # Create authenticated client with token
                    self._client = AuthenticatedClient(
                        base_url=self.base_url,
                        token=token,
                        timeout=self.timeout,
                        verify_ssl=self.verify_ssl,
                        raise_on_unexpected_status=False,  # We handle errors ourselves
                    )

                    # Add subscription key header
                    self._client = self._client.with_headers({"Ocp-Apim-Subscription-Key": subscription_key})
            except GridAuthenticationError:
                raise
            except Exception as e:
                raise GridAuthenticationError(f"Failed to initialize authenticated client: {e}") from e
        else:
            # Use unauthenticated client
            if self._client is None:
                self._client = ERCOTClient(
                    base_url=self.base_url,
                    timeout=self.timeout,
                    verify_ssl=self.verify_ssl,
                    raise_on_unexpected_status=False,  # We handle errors ourselves
                )

        return self._client

    def __enter__(self) -> "ERCOT":
        """Enter a context manager for the client.

        Stores a reference to the entered client to ensure proper cleanup,
        even if the client is recreated during the context (e.g., token refresh).
        """
        self._entered_client = self._get_client()
        self._entered_client.__enter__()
        return self

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        """Exit a context manager for the client.

        Cleans up the client that was entered, not necessarily the current client.
        """
        if hasattr(self, "_entered_client") and self._entered_client is not None:
            self._entered_client.__exit__(*args, **kwargs)
            self._entered_client = None

    async def __aenter__(self) -> "ERCOT":
        """Enter an async context manager for the client.

        Stores a reference to the entered client to ensure proper cleanup.
        """
        self._entered_client = self._get_client()
        await self._entered_client.__aenter__()
        return self

    async def __aexit__(self, *args: Any, **kwargs: Any) -> None:
        """Exit an async context manager for the client.

        Cleans up the client that was entered, not necessarily the current client.
        """
        if hasattr(self, "_entered_client") and self._entered_client is not None:
            await self._entered_client.__aexit__(*args, **kwargs)
            self._entered_client = None

    def _handle_api_error(self, error: Exception, endpoint: str | None = None) -> None:
        """Handle API errors and convert them to GridError types.

        Args:
            error: The exception that occurred
            endpoint: Optional endpoint that was being called

        Raises:
            GridError: Appropriate GridError subclass
        """
        if isinstance(error, UnexpectedStatus):
            raise GridAPIError(
                f"ERCOT API returned unexpected status {error.status_code}",
                status_code=error.status_code,
                response_body=error.content,
                endpoint=endpoint,
            ) from error

        if isinstance(error, TimeoutError):
            raise GridTimeoutError(
                "Request to ERCOT API timed out",
                timeout=self.timeout,
            ) from error

        # Re-raise GridErrors as-is
        if isinstance(error, GridError):
            raise error

        # Wrap other errors
        raise GridAPIError(
            f"Unexpected error calling ERCOT API: {error}",
            endpoint=endpoint,
        ) from error

    def _extract_response_data(self, response: Any) -> dict[str, Any]:
        """Extract data from API response.

        Handles different response types (Report, Product, etc.) and extracts
        the underlying data structure.

        Args:
            response: The API response object

        Returns:
            Dictionary containing the extracted data
        """
        if response is None:
            return {}

        # First priority: Use to_dict() if available (handles Report, Product, etc.)
        if hasattr(response, "to_dict"):
            try:
                result = response.to_dict()
                if isinstance(result, dict):
                    return result
            except Exception:
                pass

        # Handle Report objects - extract data field if present
        if hasattr(response, "data") and response.data is not None:
            # If data has to_dict, use it
            if hasattr(response.data, "to_dict"):
                try:
                    data_dict = response.data.to_dict()
                    if isinstance(data_dict, dict):
                        return data_dict
                except Exception:
                    pass
            # Otherwise try to get additional_properties from data
            if hasattr(response.data, "additional_properties"):
                props = response.data.additional_properties
                if isinstance(props, dict):
                    return props

        # Handle objects with additional_properties at top level
        if hasattr(response, "additional_properties"):
            props = response.additional_properties
            if isinstance(props, dict):
                return props

        # Fallback: try to convert to dict
        if isinstance(response, dict):
            return response

        return {}

    def _call_endpoint(
        self,
        endpoint_func: Callable[..., Any],
        endpoint_name: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generic method to call an endpoint function.

        Args:
            endpoint_func: The endpoint function to call
            endpoint_name: Name of the endpoint for error reporting
            **kwargs: Arguments to pass to the endpoint function

        Returns:
            Dictionary containing the response data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        client = self._get_client()

        try:
            # Don't use 'with client:' here - the client is managed at a higher level
            # Using 'with' would close the client, preventing reuse for subsequent calls
            response = endpoint_func.sync(client=client, **kwargs)
            return self._extract_response_data(response)

        except Exception as e:
            self._handle_api_error(e, endpoint=endpoint_name)
            return {}  # Never reached, but helps type checker

    # ============================================================================
    # EMIL Products Endpoints
    # ============================================================================

    def get_list_for_products(self, **kwargs: Any) -> dict[str, Any]:
        """Get list of available products.

        Returns:
            Dictionary containing the list of products

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(get_list_for_products, "get_list_for_products", **kwargs)

    def get_product(self, emil_id: str, **kwargs: Any) -> dict[str, Any]:
        """Get product information by EMIL ID.

        Args:
            emil_id: The EMIL product ID
            **kwargs: Additional query parameters

        Returns:
            Dictionary containing the product data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(get_product, "get_product", emil_id=emil_id, **kwargs)

    def get_product_history(self, emil_id: str, **kwargs: Any) -> dict[str, Any]:
        """Get product history by EMIL ID.

        Args:
            emil_id: The EMIL product ID
            **kwargs: Additional query parameters

        Returns:
            Dictionary containing the product history data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(get_product_history, "get_product_history", emil_id=emil_id, **kwargs)

    def get_version(self, **kwargs: Any) -> dict[str, Any]:
        """Get API version information.

        Returns:
            Dictionary containing version information

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(get_version, "get_version", **kwargs)

    # ============================================================================
    # Load Forecasting Endpoints
    # ============================================================================

    def get_load_forecast_by_weather_zone(
        self,
        start_date: str,
        end_date: str,
        model: str = "WEATHERZONE",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Get load forecast by weather zone.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            model: Forecast model name. Defaults to "WEATHERZONE".
            **kwargs: Additional query parameters (e.g., hour_ending, zone filters)

        Returns:
            Dictionary containing the forecast data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out

        Example:
            ```python
            ercot = ERCOT()
            forecast = ercot.get_load_forecast_by_weather_zone(
                start_date="2024-01-01",
                end_date="2024-01-07",
                model="WEATHERZONE"
            )
            ```
        """
        start_date = self._normalize_date(start_date)
        end_date = self._normalize_date(end_date)
        return self._call_endpoint(
            lf_by_model_weather_zone,
            "get_load_forecast_by_weather_zone",
            delivery_date_from=start_date,
            delivery_date_to=end_date,
            model=model,
            **kwargs,
        )

    def get_load_forecast_by_study_area(
        self,
        start_date: str,
        end_date: str,
        model: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Get load forecast by study area.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            model: Forecast model name
            **kwargs: Additional query parameters

        Returns:
            Dictionary containing the forecast data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        start_date = self._normalize_date(start_date)
        end_date = self._normalize_date(end_date)
        if model is not None:
            kwargs["model"] = model
        return self._call_endpoint(
            lf_by_model_study_area,
            "get_load_forecast_by_study_area",
            delivery_date_from=start_date,
            delivery_date_to=end_date,
            **kwargs,
        )

    # ============================================================================
    # Real-Time Operations Endpoints (np3_910_er, np3_911_er)
    # ============================================================================

    def get_aggregated_dsr_loads(self, **kwargs: Any) -> dict[str, Any]:
        """Get aggregated DSR (Demand Side Response) loads.

        Returns:
            Dictionary containing aggregated DSR load data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_agg_dsr_loads, "get_aggregated_dsr_loads", **kwargs)

    def get_aggregated_generation_summary(self, **kwargs: Any) -> dict[str, Any]:
        """Get aggregated generation summary.

        Returns:
            Dictionary containing aggregated generation summary data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_agg_gen_summary, "get_aggregated_generation_summary", **kwargs)

    def get_aggregated_generation_summary_houston(self, **kwargs: Any) -> dict[str, Any]:
        """Get aggregated generation summary for Houston zone.

        Returns:
            Dictionary containing aggregated generation summary data for Houston

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(
            endpoint_2d_agg_gen_summary_houston, "get_aggregated_generation_summary_houston", **kwargs
        )

    def get_aggregated_generation_summary_north(self, **kwargs: Any) -> dict[str, Any]:
        """Get aggregated generation summary for North zone.

        Returns:
            Dictionary containing aggregated generation summary data for North zone

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(
            endpoint_2d_agg_gen_summary_north, "get_aggregated_generation_summary_north", **kwargs
        )

    def get_aggregated_generation_summary_south(self, **kwargs: Any) -> dict[str, Any]:
        """Get aggregated generation summary for South zone.

        Returns:
            Dictionary containing aggregated generation summary data for South zone

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(
            endpoint_2d_agg_gen_summary_south, "get_aggregated_generation_summary_south", **kwargs
        )

    def get_aggregated_generation_summary_west(self, **kwargs: Any) -> dict[str, Any]:
        """Get aggregated generation summary for West zone.

        Returns:
            Dictionary containing aggregated generation summary data for West zone

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_agg_gen_summary_west, "get_aggregated_generation_summary_west", **kwargs)

    def get_aggregated_load_summary(self, **kwargs: Any) -> dict[str, Any]:
        """Get aggregated load summary.

        Returns:
            Dictionary containing aggregated load summary data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_agg_load_summary, "get_aggregated_load_summary", **kwargs)

    def get_aggregated_load_summary_houston(self, **kwargs: Any) -> dict[str, Any]:
        """Get aggregated load summary for Houston zone.

        Returns:
            Dictionary containing aggregated load summary data for Houston

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(
            endpoint_2d_agg_load_summary_houston, "get_aggregated_load_summary_houston", **kwargs
        )

    def get_aggregated_load_summary_north(self, **kwargs: Any) -> dict[str, Any]:
        """Get aggregated load summary for North zone.

        Returns:
            Dictionary containing aggregated load summary data for North zone

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_agg_load_summary_north, "get_aggregated_load_summary_north", **kwargs)

    def get_aggregated_load_summary_south(self, **kwargs: Any) -> dict[str, Any]:
        """Get aggregated load summary for South zone.

        Returns:
            Dictionary containing aggregated load summary data for South zone

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_agg_load_summary_south, "get_aggregated_load_summary_south", **kwargs)

    def get_aggregated_load_summary_west(self, **kwargs: Any) -> dict[str, Any]:
        """Get aggregated load summary for West zone.

        Returns:
            Dictionary containing aggregated load summary data for West zone

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_agg_load_summary_west, "get_aggregated_load_summary_west", **kwargs)

    def get_aggregated_outage_schedule(self, **kwargs: Any) -> dict[str, Any]:
        """Get aggregated outage schedule.

        Returns:
            Dictionary containing aggregated outage schedule data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_agg_out_sched, "get_aggregated_outage_schedule", **kwargs)

    def get_aggregated_outage_schedule_houston(self, **kwargs: Any) -> dict[str, Any]:
        """Get aggregated outage schedule for Houston zone.

        Returns:
            Dictionary containing aggregated outage schedule data for Houston

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(
            endpoint_2d_agg_out_sched_houston, "get_aggregated_outage_schedule_houston", **kwargs
        )

    def get_aggregated_outage_schedule_north(self, **kwargs: Any) -> dict[str, Any]:
        """Get aggregated outage schedule for North zone.

        Returns:
            Dictionary containing aggregated outage schedule data for North zone

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_agg_out_sched_north, "get_aggregated_outage_schedule_north", **kwargs)

    def get_aggregated_outage_schedule_south(self, **kwargs: Any) -> dict[str, Any]:
        """Get aggregated outage schedule for South zone.

        Returns:
            Dictionary containing aggregated outage schedule data for South zone

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_agg_out_sched_south, "get_aggregated_outage_schedule_south", **kwargs)

    def get_aggregated_outage_schedule_west(self, **kwargs: Any) -> dict[str, Any]:
        """Get aggregated outage schedule for West zone.

        Returns:
            Dictionary containing aggregated outage schedule data for West zone

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_agg_out_sched_west, "get_aggregated_outage_schedule_west", **kwargs)

    # ============================================================================
    # Ancillary Services Endpoints (np3_911_er)
    # ============================================================================

    def get_aggregated_as_offers_ecrsm(self, **kwargs: Any) -> dict[str, Any]:
        """Get aggregated ancillary service offers for ECRSM (Emergency Contingency Reserve - Slow).

        Returns:
            Dictionary containing aggregated AS offers data for ECRSM

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_agg_as_offers_ecrsm, "get_aggregated_as_offers_ecrsm", **kwargs)

    def get_aggregated_as_offers_ecrss(self, **kwargs: Any) -> dict[str, Any]:
        """Get aggregated ancillary service offers for ECRSS (Emergency Contingency Reserve - Super Slow).

        Returns:
            Dictionary containing aggregated AS offers data for ECRSS

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_agg_as_offers_ecrss, "get_aggregated_as_offers_ecrss", **kwargs)

    def get_aggregated_as_offers_offns(self, **kwargs: Any) -> dict[str, Any]:
        """Get aggregated ancillary service offers for OFFNS (Off-Line Non-Spinning Reserve).

        Returns:
            Dictionary containing aggregated AS offers data for OFFNS

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_agg_as_offers_offns, "get_aggregated_as_offers_offns", **kwargs)

    def get_aggregated_as_offers_onns(self, **kwargs: Any) -> dict[str, Any]:
        """Get aggregated ancillary service offers for ONNS (On-Line Non-Spinning Reserve).

        Returns:
            Dictionary containing aggregated AS offers data for ONNS

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_agg_as_offers_onns, "get_aggregated_as_offers_onns", **kwargs)

    def get_aggregated_as_offers_regdn(self, **kwargs: Any) -> dict[str, Any]:
        """Get aggregated ancillary service offers for REGDN (Regulation Down).

        Returns:
            Dictionary containing aggregated AS offers data for REGDN

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_agg_as_offers_regdn, "get_aggregated_as_offers_regdn", **kwargs)

    def get_aggregated_as_offers_regup(self, **kwargs: Any) -> dict[str, Any]:
        """Get aggregated ancillary service offers for REGUP (Regulation Up).

        Returns:
            Dictionary containing aggregated AS offers data for REGUP

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_agg_as_offers_regup, "get_aggregated_as_offers_regup", **kwargs)

    def get_aggregated_as_offers_rrsffr(self, **kwargs: Any) -> dict[str, Any]:
        """Get aggregated ancillary service offers for RRSFFR (Responsive Reserve - Fast Frequency Response).

        Returns:
            Dictionary containing aggregated AS offers data for RRSFFR

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_agg_as_offers_rrsffr, "get_aggregated_as_offers_rrsffr", **kwargs)

    def get_aggregated_as_offers_rrspfr(self, **kwargs: Any) -> dict[str, Any]:
        """Get aggregated ancillary service offers for RRSPFR (Responsive Reserve - Primary Frequency Response).

        Returns:
            Dictionary containing aggregated AS offers data for RRSPFR

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_agg_as_offers_rrspfr, "get_aggregated_as_offers_rrspfr", **kwargs)

    def get_aggregated_as_offers_rrsufr(self, **kwargs: Any) -> dict[str, Any]:
        """Get aggregated ancillary service offers for RRSUFR (Responsive Reserve - Ultra-Fast Frequency Response).

        Returns:
            Dictionary containing aggregated AS offers data for RRSUFR

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_agg_as_offers_rrsufr, "get_aggregated_as_offers_rrsufr", **kwargs)

    def get_cleared_dam_as_ecrsm(self, **kwargs: Any) -> dict[str, Any]:
        """Get cleared day-ahead market ancillary services for ECRSM.

        Returns:
            Dictionary containing cleared DAM AS data for ECRSM

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_cleared_dam_as_ecrsm, "get_cleared_dam_as_ecrsm", **kwargs)

    def get_cleared_dam_as_ecrss(self, **kwargs: Any) -> dict[str, Any]:
        """Get cleared day-ahead market ancillary services for ECRSS.

        Returns:
            Dictionary containing cleared DAM AS data for ECRSS

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_cleared_dam_as_ecrss, "get_cleared_dam_as_ecrss", **kwargs)

    def get_cleared_dam_as_nspin(self, **kwargs: Any) -> dict[str, Any]:
        """Get cleared day-ahead market ancillary services for NSPIN.

        Returns:
            Dictionary containing cleared DAM AS data for NSPIN

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_cleared_dam_as_nspin, "get_cleared_dam_as_nspin", **kwargs)

    def get_cleared_dam_as_regdn(self, **kwargs: Any) -> dict[str, Any]:
        """Get cleared day-ahead market ancillary services for REGDN.

        Returns:
            Dictionary containing cleared DAM AS data for REGDN

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_cleared_dam_as_regdn, "get_cleared_dam_as_regdn", **kwargs)

    def get_cleared_dam_as_regup(self, **kwargs: Any) -> dict[str, Any]:
        """Get cleared day-ahead market ancillary services for REGUP.

        Returns:
            Dictionary containing cleared DAM AS data for REGUP

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_cleared_dam_as_regup, "get_cleared_dam_as_regup", **kwargs)

    def get_cleared_dam_as_rrsffr(self, **kwargs: Any) -> dict[str, Any]:
        """Get cleared day-ahead market ancillary services for RRSFFR.

        Returns:
            Dictionary containing cleared DAM AS data for RRSFFR

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_cleared_dam_as_rrsffr, "get_cleared_dam_as_rrsffr", **kwargs)

    def get_cleared_dam_as_rrspfr(self, **kwargs: Any) -> dict[str, Any]:
        """Get cleared day-ahead market ancillary services for RRSPFR.

        Returns:
            Dictionary containing cleared DAM AS data for RRSPFR

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_cleared_dam_as_rrspfr, "get_cleared_dam_as_rrspfr", **kwargs)

    def get_cleared_dam_as_rrsufr(self, **kwargs: Any) -> dict[str, Any]:
        """Get cleared day-ahead market ancillary services for RRSUFR.

        Returns:
            Dictionary containing cleared DAM AS data for RRSUFR

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_cleared_dam_as_rrsufr, "get_cleared_dam_as_rrsufr", **kwargs)

    def get_self_arranged_as_ecrsm(self, **kwargs: Any) -> dict[str, Any]:
        """Get self-arranged ancillary services for ECRSM.

        Returns:
            Dictionary containing self-arranged AS data for ECRSM

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_self_arranged_as_ecrsm, "get_self_arranged_as_ecrsm", **kwargs)

    def get_self_arranged_as_ecrss(self, **kwargs: Any) -> dict[str, Any]:
        """Get self-arranged ancillary services for ECRSS.

        Returns:
            Dictionary containing self-arranged AS data for ECRSS

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_self_arranged_as_ecrss, "get_self_arranged_as_ecrss", **kwargs)

    def get_self_arranged_as_nspin(self, **kwargs: Any) -> dict[str, Any]:
        """Get self-arranged ancillary services for NSPIN.

        Returns:
            Dictionary containing self-arranged AS data for NSPIN

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_self_arranged_as_nspin, "get_self_arranged_as_nspin", **kwargs)

    def get_self_arranged_as_nspnm(self, **kwargs: Any) -> dict[str, Any]:
        """Get self-arranged ancillary services for NSPNM.

        Returns:
            Dictionary containing self-arranged AS data for NSPNM

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_self_arranged_as_nspnm, "get_self_arranged_as_nspnm", **kwargs)

    def get_self_arranged_as_regdn(self, **kwargs: Any) -> dict[str, Any]:
        """Get self-arranged ancillary services for REGDN.

        Returns:
            Dictionary containing self-arranged AS data for REGDN

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_self_arranged_as_regdn, "get_self_arranged_as_regdn", **kwargs)

    def get_self_arranged_as_regup(self, **kwargs: Any) -> dict[str, Any]:
        """Get self-arranged ancillary services for REGUP.

        Returns:
            Dictionary containing self-arranged AS data for REGUP

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_self_arranged_as_regup, "get_self_arranged_as_regup", **kwargs)

    def get_self_arranged_as_rrsffr(self, **kwargs: Any) -> dict[str, Any]:
        """Get self-arranged ancillary services for RRSFFR.

        Returns:
            Dictionary containing self-arranged AS data for RRSFFR

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_self_arranged_as_rrsffr, "get_self_arranged_as_rrsffr", **kwargs)

    def get_self_arranged_as_rrspfr(self, **kwargs: Any) -> dict[str, Any]:
        """Get self-arranged ancillary services for RRSPFR.

        Returns:
            Dictionary containing self-arranged AS data for RRSPFR

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_self_arranged_as_rrspfr, "get_self_arranged_as_rrspfr", **kwargs)

    def get_self_arranged_as_rrsufr(self, **kwargs: Any) -> dict[str, Any]:
        """Get self-arranged ancillary services for RRSUFR.

        Returns:
            Dictionary containing self-arranged AS data for RRSUFR

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_2d_self_arranged_as_rrsufr, "get_self_arranged_as_rrsufr", **kwargs)

    # ============================================================================
    # SCED (Security Constrained Economic Dispatch) Endpoints (np3_965_er)
    # ============================================================================

    def get_hdl_ldl_manual_override(self, **kwargs: Any) -> dict[str, Any]:
        """Get HDL/LDL manual override data.

        Returns:
            Dictionary containing HDL/LDL manual override data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_60_hdl_ldl_man_override, "get_hdl_ldl_manual_override", **kwargs)

    def get_load_res_data_in_sced(self, **kwargs: Any) -> dict[str, Any]:
        """Get load resource data in SCED.

        Returns:
            Dictionary containing load resource data in SCED

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_60_load_res_data_in_sced, "get_load_res_data_in_sced", **kwargs)

    def get_sced_dsr_load_data(self, **kwargs: Any) -> dict[str, Any]:
        """Get SCED DSR (Demand Side Response) load data.

        Returns:
            Dictionary containing SCED DSR load data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_60_sced_dsr_load_data, "get_sced_dsr_load_data", **kwargs)

    def get_sced_gen_res_data(self, **kwargs: Any) -> dict[str, Any]:
        """Get SCED generation resource data.

        Returns:
            Dictionary containing SCED generation resource data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_60_sced_gen_res_data, "get_sced_gen_res_data", **kwargs)

    def get_sced_qse_self_arranged_as(self, **kwargs: Any) -> dict[str, Any]:
        """Get SCED QSE self-arranged ancillary services.

        Returns:
            Dictionary containing SCED QSE self-arranged AS data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_60_sced_qse_self_arranged_as, "get_sced_qse_self_arranged_as", **kwargs)

    def get_sced_smne_gen_res(self, **kwargs: Any) -> dict[str, Any]:
        """Get SCED SMNE (Small Non-Exempt) generation resource data.

        Returns:
            Dictionary containing SCED SMNE generation resource data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_60_sced_smne_gen_res, "get_sced_smne_gen_res", **kwargs)

    # ============================================================================
    # Day-Ahead Market (DAM) Endpoints (np3_966_er)
    # ============================================================================

    def get_dam_energy_bid_awards(self, **kwargs: Any) -> dict[str, Any]:
        """Get day-ahead market energy bid awards.

        Returns:
            Dictionary containing DAM energy bid awards data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_60_dam_energy_bid_awards, "get_dam_energy_bid_awards", **kwargs)

    def get_dam_energy_bids(self, **kwargs: Any) -> dict[str, Any]:
        """Get day-ahead market energy bids.

        Returns:
            Dictionary containing DAM energy bids data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_60_dam_energy_bids, "get_dam_energy_bids", **kwargs)

    def get_dam_energy_only_offer_awards(self, **kwargs: Any) -> dict[str, Any]:
        """Get day-ahead market energy-only offer awards.

        Returns:
            Dictionary containing DAM energy-only offer awards data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(
            endpoint_60_dam_energy_only_offer_awards, "get_dam_energy_only_offer_awards", **kwargs
        )

    def get_dam_energy_only_offers(self, **kwargs: Any) -> dict[str, Any]:
        """Get day-ahead market energy-only offers.

        Returns:
            Dictionary containing DAM energy-only offers data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_60_dam_energy_only_offers, "get_dam_energy_only_offers", **kwargs)

    def get_dam_gen_res_as_offers(self, **kwargs: Any) -> dict[str, Any]:
        """Get day-ahead market generation resource ancillary service offers.

        Returns:
            Dictionary containing DAM generation resource AS offers data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_60_dam_gen_res_as_offers, "get_dam_gen_res_as_offers", **kwargs)

    def get_dam_gen_res_data(self, **kwargs: Any) -> dict[str, Any]:
        """Get day-ahead market generation resource data.

        Returns:
            Dictionary containing DAM generation resource data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_60_dam_gen_res_data, "get_dam_gen_res_data", **kwargs)

    def get_dam_load_res_as_offers(self, **kwargs: Any) -> dict[str, Any]:
        """Get day-ahead market load resource ancillary service offers.

        Returns:
            Dictionary containing DAM load resource AS offers data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_60_dam_load_res_as_offers, "get_dam_load_res_as_offers", **kwargs)

    def get_dam_load_res_data(self, **kwargs: Any) -> dict[str, Any]:
        """Get day-ahead market load resource data.

        Returns:
            Dictionary containing DAM load resource data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_60_dam_load_res_data, "get_dam_load_res_data", **kwargs)

    def get_dam_ptp_obl_bid_awards(self, **kwargs: Any) -> dict[str, Any]:
        """Get day-ahead market point-to-point obligation bid awards.

        Returns:
            Dictionary containing DAM PTP obligation bid awards data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_60_dam_ptp_obl_bid_awards, "get_dam_ptp_obl_bid_awards", **kwargs)

    def get_dam_ptp_obl_bids(self, **kwargs: Any) -> dict[str, Any]:
        """Get day-ahead market point-to-point obligation bids.

        Returns:
            Dictionary containing DAM PTP obligation bids data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_60_dam_ptp_obl_bids, "get_dam_ptp_obl_bids", **kwargs)

    def get_dam_ptp_obl_opt_awards(self, **kwargs: Any) -> dict[str, Any]:
        """Get day-ahead market point-to-point obligation option awards.

        Returns:
            Dictionary containing DAM PTP obligation option awards data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_60_dam_ptp_obl_opt_awards, "get_dam_ptp_obl_opt_awards", **kwargs)

    def get_dam_ptp_obl_opt(self, **kwargs: Any) -> dict[str, Any]:
        """Get day-ahead market point-to-point obligation options.

        Returns:
            Dictionary containing DAM PTP obligation options data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_60_dam_ptp_obl_opt, "get_dam_ptp_obl_opt", **kwargs)

    def get_dam_qse_self_as(self, **kwargs: Any) -> dict[str, Any]:
        """Get day-ahead market QSE self-arranged ancillary services.

        Returns:
            Dictionary containing DAM QSE self-arranged AS data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_60_dam_qse_self_as, "get_dam_qse_self_as", **kwargs)

    # ============================================================================
    # SASM (Settlement and Ancillary Service Market) Endpoints (np3_990_ex)
    # ============================================================================

    def get_sasm_gen_res_as_offer_awards(self, **kwargs: Any) -> dict[str, Any]:
        """Get SASM generation resource ancillary service offer awards.

        Returns:
            Dictionary containing SASM generation resource AS offer awards data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(
            endpoint_60_sasm_gen_res_as_offer_awards, "get_sasm_gen_res_as_offer_awards", **kwargs
        )

    def get_sasm_gen_res_as_offers(self, **kwargs: Any) -> dict[str, Any]:
        """Get SASM generation resource ancillary service offers.

        Returns:
            Dictionary containing SASM generation resource AS offers data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_60_sasm_gen_res_as_offers, "get_sasm_gen_res_as_offers", **kwargs)

    def get_sasm_load_res_as_offer_awards(self, **kwargs: Any) -> dict[str, Any]:
        """Get SASM load resource ancillary service offer awards.

        Returns:
            Dictionary containing SASM load resource AS offer awards data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(
            endpoint_60_sasm_load_res_as_offer_awards, "get_sasm_load_res_as_offer_awards", **kwargs
        )

    def get_sasm_load_res_as_offers(self, **kwargs: Any) -> dict[str, Any]:
        """Get SASM load resource ancillary service offers.

        Returns:
            Dictionary containing SASM load resource AS offers data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_60_sasm_load_res_as_offers, "get_sasm_load_res_as_offers", **kwargs)

    def get_cop_all_updates(self, **kwargs: Any) -> dict[str, Any]:
        """Get COP (Change of Plan) all updates.

        Returns:
            Dictionary containing COP all updates data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(endpoint_60_cop_all_updates, "get_cop_all_updates", **kwargs)

    # ============================================================================
    # Day-Ahead Market Pricing Endpoints (np4_*)
    # ============================================================================

    def get_dam_hourly_lmp(
        self,
        start_date: str,
        end_date: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Get day-ahead market hourly LMP (Locational Marginal Price).

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            **kwargs: Additional query parameters (e.g., hour_ending, bus_name, lmp_from, lmp_to)

        Returns:
            Dictionary containing DAM hourly LMP data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        start_date = self._normalize_date(start_date)
        end_date = self._normalize_date(end_date)
        return self._call_endpoint(
            dam_hourly_lmp,
            "get_dam_hourly_lmp",
            delivery_date_from=start_date,
            delivery_date_to=end_date,
            **kwargs,
        )

    def get_dam_clear_price_for_cap(self, **kwargs: Any) -> dict[str, Any]:
        """Get day-ahead market clear price for capacity.

        Returns:
            Dictionary containing DAM clear price for capacity data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(dam_clear_price_for_cap, "get_dam_clear_price_for_cap", **kwargs)

    def get_dam_settlement_point_prices(self, **kwargs: Any) -> dict[str, Any]:
        """Get day-ahead market settlement point prices.

        Returns:
            Dictionary containing DAM settlement point prices data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(dam_stlmnt_pnt_prices, "get_dam_settlement_point_prices", **kwargs)

    def get_dam_shadow_prices(self, **kwargs: Any) -> dict[str, Any]:
        """Get day-ahead market shadow prices.

        Returns:
            Dictionary containing DAM shadow prices data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(dam_shadow_prices, "get_dam_shadow_prices", **kwargs)

    def get_dam_as_plan(self, **kwargs: Any) -> dict[str, Any]:
        """Get day-ahead market ancillary service plan.

        Returns:
            Dictionary containing DAM AS plan data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(dam_as_plan, "get_dam_as_plan", **kwargs)

    def get_dam_system_lambda(self, **kwargs: Any) -> dict[str, Any]:
        """Get day-ahead market system lambda.

        Returns:
            Dictionary containing DAM system lambda data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(dam_system_lambda, "get_dam_system_lambda", **kwargs)

    def get_load_distribution_factors(self, **kwargs: Any) -> dict[str, Any]:
        """Get load distribution factors.

        Returns:
            Dictionary containing load distribution factors data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(load_distribution_factors, "get_load_distribution_factors", **kwargs)

    def get_total_as_service_offers(self, **kwargs: Any) -> dict[str, Any]:
        """Get total ancillary service offers.

        Returns:
            Dictionary containing total AS service offers data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(total_as_service_offers, "get_total_as_service_offers", **kwargs)

    # ============================================================================
    # Price Corrections Endpoints (np4_196_m, np4_197_m)
    # ============================================================================

    def get_dam_price_corrections_eblmp(self, **kwargs: Any) -> dict[str, Any]:
        """Get day-ahead market price corrections for EBLMP (Energy Bus LMP).

        Returns:
            Dictionary containing DAM price corrections for EBLMP data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(dam_price_corrections_eblmp, "get_dam_price_corrections_eblmp", **kwargs)

    def get_dam_price_corrections_mcpc(self, **kwargs: Any) -> dict[str, Any]:
        """Get day-ahead market price corrections for MCPC (Market Clearing Price for Capacity).

        Returns:
            Dictionary containing DAM price corrections for MCPC data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(dam_price_corrections_mcpc, "get_dam_price_corrections_mcpc", **kwargs)

    def get_dam_price_corrections_spp(self, **kwargs: Any) -> dict[str, Any]:
        """Get day-ahead market price corrections for SPP (Settlement Point Price).

        Returns:
            Dictionary containing DAM price corrections for SPP data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(dam_price_corrections_spp, "get_dam_price_corrections_spp", **kwargs)

    def get_rtm_price_corrections_eblmp(self, **kwargs: Any) -> dict[str, Any]:
        """Get real-time market price corrections for EBLMP.

        Returns:
            Dictionary containing RTM price corrections for EBLMP data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(rtm_price_corrections_eblmp, "get_rtm_price_corrections_eblmp", **kwargs)

    def get_rtm_price_corrections_shadow(self, **kwargs: Any) -> dict[str, Any]:
        """Get real-time market price corrections for shadow prices.

        Returns:
            Dictionary containing RTM price corrections for shadow prices data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(rtm_price_corrections_shadow, "get_rtm_price_corrections_shadow", **kwargs)

    def get_rtm_price_corrections_soglmp(self, **kwargs: Any) -> dict[str, Any]:
        """Get real-time market price corrections for SOGLMP (System Operator Generated LMP).

        Returns:
            Dictionary containing RTM price corrections for SOGLMP data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(rtm_price_corrections_soglmp, "get_rtm_price_corrections_soglmp", **kwargs)

    def get_rtm_price_corrections_sogprice(self, **kwargs: Any) -> dict[str, Any]:
        """Get real-time market price corrections for SOG price.

        Returns:
            Dictionary containing RTM price corrections for SOG price data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(rtm_price_corrections_sogprice, "get_rtm_price_corrections_sogprice", **kwargs)

    def get_rtm_price_corrections_splmp(self, **kwargs: Any) -> dict[str, Any]:
        """Get real-time market price corrections for SPLMP (Settlement Point LMP).

        Returns:
            Dictionary containing RTM price corrections for SPLMP data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(rtm_price_corrections_splmp, "get_rtm_price_corrections_splmp", **kwargs)

    def get_rtm_price_corrections_spp(self, **kwargs: Any) -> dict[str, Any]:
        """Get real-time market price corrections for SPP.

        Returns:
            Dictionary containing RTM price corrections for SPP data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(rtm_price_corrections_spp, "get_rtm_price_corrections_spp", **kwargs)

    # ============================================================================
    # Wind and Solar Power Endpoints
    # (np4_732_cd, np4_733_cd, np4_737_cd, np4_738_cd, np4_742_cd, np4_743_cd,
    #  np4_745_cd, np4_746_cd)
    # ============================================================================

    def get_wpp_hourly_average_actual_forecast(self, **kwargs: Any) -> dict[str, Any]:
        """Get wind power plant hourly average actual forecast.

        Returns:
            Dictionary containing WPP hourly average actual forecast data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(wpp_hrly_avrg_actl_fcast, "get_wpp_hourly_average_actual_forecast", **kwargs)

    def get_wpp_actual_5min_avg_values(self, **kwargs: Any) -> dict[str, Any]:
        """Get wind power plant actual 5-minute average values.

        Returns:
            Dictionary containing WPP actual 5-minute average values data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(wpp_actual_5min_avg_values, "get_wpp_actual_5min_avg_values", **kwargs)

    def get_spp_hourly_average_actual_forecast(self, **kwargs: Any) -> dict[str, Any]:
        """Get solar power plant hourly average actual forecast.

        Returns:
            Dictionary containing SPP hourly average actual forecast data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(spp_hrly_avrg_actl_fcast, "get_spp_hourly_average_actual_forecast", **kwargs)

    def get_spp_actual_5min_avg_values(self, **kwargs: Any) -> dict[str, Any]:
        """Get solar power plant actual 5-minute average values.

        Returns:
            Dictionary containing SPP actual 5-minute average values data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(spp_actual_5min_avg_values, "get_spp_actual_5min_avg_values", **kwargs)

    def get_wpp_hourly_actual_forecast_geo(self, **kwargs: Any) -> dict[str, Any]:
        """Get wind power plant hourly actual forecast by geography.

        Returns:
            Dictionary containing WPP hourly actual forecast by geography data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(wpp_hrly_actual_fcast_geo, "get_wpp_hourly_actual_forecast_geo", **kwargs)

    def get_wpp_actual_5min_avg_values_geo(self, **kwargs: Any) -> dict[str, Any]:
        """Get wind power plant actual 5-minute average values by geography.

        Returns:
            Dictionary containing WPP actual 5-minute average values by geography data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(wpp_actual_5min_avg_values_geo, "get_wpp_actual_5min_avg_values_geo", **kwargs)

    def get_spp_hourly_actual_forecast_geo(self, **kwargs: Any) -> dict[str, Any]:
        """Get solar power plant hourly actual forecast by geography.

        Returns:
            Dictionary containing SPP hourly actual forecast by geography data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(spp_hrly_actual_fcast_geo, "get_spp_hourly_actual_forecast_geo", **kwargs)

    def get_spp_actual_5min_avg_values_geo(self, **kwargs: Any) -> dict[str, Any]:
        """Get solar power plant actual 5-minute average values by geography.

        Returns:
            Dictionary containing SPP actual 5-minute average values by geography data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(spp_actual_5min_avg_values_geo, "get_spp_actual_5min_avg_values_geo", **kwargs)

    # ============================================================================
    # Real-Time Market Endpoints (np6_*)
    # ============================================================================

    def get_sced_system_lambda(self, **kwargs: Any) -> dict[str, Any]:
        """Get SCED system lambda.

        Returns:
            Dictionary containing SCED system lambda data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(sced_system_lambda, "get_sced_system_lambda", **kwargs)

    def get_actual_system_load_by_weather_zone(self, **kwargs: Any) -> dict[str, Any]:
        """Get actual system load by weather zone.

        Returns:
            Dictionary containing actual system load by weather zone data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(act_sys_load_by_wzn, "get_actual_system_load_by_weather_zone", **kwargs)

    def get_actual_system_load_by_forecast_zone(self, **kwargs: Any) -> dict[str, Any]:
        """Get actual system load by forecast zone.

        Returns:
            Dictionary containing actual system load by forecast zone data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(act_sys_load_by_fzn, "get_actual_system_load_by_forecast_zone", **kwargs)

    def get_lmp_electrical_bus(self, **kwargs: Any) -> dict[str, Any]:
        """Get LMP (Locational Marginal Price) for electrical bus.

        Returns:
            Dictionary containing LMP electrical bus data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(lmp_electrical_bus, "get_lmp_electrical_bus", **kwargs)

    def get_lmp_node_zone_hub(self, **kwargs: Any) -> dict[str, Any]:
        """Get LMP for node, zone, and hub.

        Returns:
            Dictionary containing LMP node, zone, and hub data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(lmp_node_zone_hub, "get_lmp_node_zone_hub", **kwargs)

    def get_shadow_prices_bound_transmission_constraint(self, **kwargs: Any) -> dict[str, Any]:
        """Get shadow prices for bound transmission constraint.

        Returns:
            Dictionary containing shadow prices for bound transmission constraint data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(
            shdw_prices_bnd_trns_const, "get_shadow_prices_bound_transmission_constraint", **kwargs
        )

    def get_spp_node_zone_hub(self, **kwargs: Any) -> dict[str, Any]:
        """Get SPP (Settlement Point Price) for node, zone, and hub.

        Returns:
            Dictionary containing SPP node, zone, and hub data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(spp_node_zone_hub, "get_spp_node_zone_hub", **kwargs)

    def get_data(self, **kwargs: Any) -> dict[str, Any]:
        """Get data from np6_970_cd endpoint.

        Returns:
            Dictionary containing data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(get_data, "get_data", **kwargs)

    # ============================================================================
    # Outage Management Endpoints (np3_233_cd)
    # ============================================================================

    def get_hourly_res_outage_cap(self, **kwargs: Any) -> dict[str, Any]:
        """Get hourly resource outage capacity.

        Returns:
            Dictionary containing hourly resource outage capacity data

        Raises:
            GridAPIError: If the API request fails
            GridTimeoutError: If the request times out
        """
        return self._call_endpoint(hourly_res_outage_cap, "get_hourly_res_outage_cap", **kwargs)
