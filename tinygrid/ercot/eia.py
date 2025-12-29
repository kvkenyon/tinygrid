"""EIA (Energy Information Administration) API integration for ERCOT data.

The EIA provides supplementary data for ERCOT including:
- Hourly demand and generation (from 2019)
- Historical capacity and fuel mix data
- Retail electricity sales

This module provides access to EIA data as an alternative or supplement
to ERCOT's native API, especially useful for:
- Data before December 2023 (when ERCOT's API launched)
- Cross-validation of ERCOT data
- Additional metrics not in ERCOT's API

API Documentation: https://www.eia.gov/opendata/documentation.php
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
import pandas as pd

from ..constants.ercot import ERCOT_TIMEZONE

logger = logging.getLogger(__name__)

# EIA API endpoints
EIA_API_BASE_URL = "https://api.eia.gov/v2"

# ERCOT is identified as "ERCO" balancing authority in EIA data
ERCOT_BA_CODE = "ERCO"

# EIA bulk download URL for Electric Balancing Authority data
EIA_BULK_DOWNLOAD_URL = "https://www.eia.gov/opendata/bulk/EBA.zip"


class EIAClient:
    """Client for accessing ERCOT data via the EIA API.

    The EIA (Energy Information Administration) provides free access to
    US energy data including hourly electricity demand and generation
    by balancing authority.

    ERCOT data is available under the balancing authority code "ERCO".

    Note: Requires a free API key from https://www.eia.gov/opendata/register.php

    Args:
        api_key: EIA API key (required for most endpoints)
        timeout: Request timeout in seconds

    Example:
        ```python
        from tinygrid.ercot.eia import EIAClient

        eia = EIAClient(api_key="your-api-key")

        # Get hourly demand for ERCOT
        demand = eia.get_demand(start="2024-01-01", end="2024-01-07")

        # Get generation by fuel type
        gen = eia.get_generation_by_fuel(start="2024-01-01", end="2024-01-07")
        ```
    """

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the EIA client.

        Args:
            api_key: EIA API key. Get one at https://www.eia.gov/opendata/register.php
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.timeout = timeout
        self._base_url = EIA_API_BASE_URL

    def _make_request(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a request to the EIA API.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            Parsed JSON response

        Raises:
            ValueError: If API key is required but not provided
            httpx.HTTPError: If request fails
        """
        if self.api_key is None:
            raise ValueError(
                "EIA API key required. Get one at https://www.eia.gov/opendata/register.php"
            )

        url = f"{self._base_url}/{endpoint}"
        request_params = {"api_key": self.api_key}
        if params:
            request_params.update(params)

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, params=request_params)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            logger.error(f"EIA API request timed out: {url}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"EIA API request failed: {e.response.status_code} - {url}")
            raise

    def get_demand(
        self,
        start: str | pd.Timestamp,
        end: str | pd.Timestamp | None = None,
    ) -> pd.DataFrame:
        """Get hourly demand data for ERCOT.

        Fetches hourly electricity demand (load) for the ERCOT balancing
        authority from the EIA API.

        Args:
            start: Start date (YYYY-MM-DD format or Timestamp)
            end: End date (defaults to start + 7 days)

        Returns:
            DataFrame with columns: timestamp, demand_mw

        Example:
            ```python
            eia = EIAClient(api_key="your-key")
            demand = eia.get_demand(start="2024-01-01", end="2024-01-07")
            ```
        """
        start_ts = pd.Timestamp(start)
        end_ts = pd.Timestamp(end) if end else start_ts + pd.Timedelta(days=7)

        params = {
            "frequency": "hourly",
            "data[0]": "value",
            "facets[respondent][]": ERCOT_BA_CODE,
            "facets[type][]": "D",  # Demand
            "start": start_ts.strftime("%Y-%m-%dT00"),
            "end": end_ts.strftime("%Y-%m-%dT23"),
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
        }

        try:
            response = self._make_request("electricity/rto/region-data/data", params)
            data = response.get("response", {}).get("data", [])

            if not data:
                return pd.DataFrame(columns=["timestamp", "demand_mw"])

            records = []
            for item in data:
                records.append(
                    {
                        "timestamp": pd.Timestamp(
                            item.get("period"), tz=ERCOT_TIMEZONE
                        ),
                        "demand_mw": float(item.get("value", 0)),
                    }
                )

            return pd.DataFrame(records)

        except Exception as e:
            logger.error(f"Failed to fetch EIA demand data: {e}")
            return pd.DataFrame(columns=["timestamp", "demand_mw"])

    def get_generation(
        self,
        start: str | pd.Timestamp,
        end: str | pd.Timestamp | None = None,
    ) -> pd.DataFrame:
        """Get hourly net generation data for ERCOT.

        Fetches hourly electricity generation for the ERCOT balancing
        authority from the EIA API.

        Args:
            start: Start date
            end: End date (defaults to start + 7 days)

        Returns:
            DataFrame with columns: timestamp, generation_mw
        """
        start_ts = pd.Timestamp(start)
        end_ts = pd.Timestamp(end) if end else start_ts + pd.Timedelta(days=7)

        params = {
            "frequency": "hourly",
            "data[0]": "value",
            "facets[respondent][]": ERCOT_BA_CODE,
            "facets[type][]": "NG",  # Net Generation
            "start": start_ts.strftime("%Y-%m-%dT00"),
            "end": end_ts.strftime("%Y-%m-%dT23"),
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
        }

        try:
            response = self._make_request("electricity/rto/region-data/data", params)
            data = response.get("response", {}).get("data", [])

            if not data:
                return pd.DataFrame(columns=["timestamp", "generation_mw"])

            records = []
            for item in data:
                records.append(
                    {
                        "timestamp": pd.Timestamp(
                            item.get("period"), tz=ERCOT_TIMEZONE
                        ),
                        "generation_mw": float(item.get("value", 0)),
                    }
                )

            return pd.DataFrame(records)

        except Exception as e:
            logger.error(f"Failed to fetch EIA generation data: {e}")
            return pd.DataFrame(columns=["timestamp", "generation_mw"])

    def get_generation_by_fuel(
        self,
        start: str | pd.Timestamp,
        end: str | pd.Timestamp | None = None,
    ) -> pd.DataFrame:
        """Get hourly generation by fuel type for ERCOT.

        Fetches hourly electricity generation broken down by fuel source
        (coal, natural gas, nuclear, wind, solar, etc.).

        Args:
            start: Start date
            end: End date (defaults to start + 7 days)

        Returns:
            DataFrame with columns: timestamp, fuel_type, generation_mw
        """
        start_ts = pd.Timestamp(start)
        end_ts = pd.Timestamp(end) if end else start_ts + pd.Timedelta(days=7)

        params = {
            "frequency": "hourly",
            "data[0]": "value",
            "facets[respondent][]": ERCOT_BA_CODE,
            "start": start_ts.strftime("%Y-%m-%dT00"),
            "end": end_ts.strftime("%Y-%m-%dT23"),
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
        }

        try:
            response = self._make_request("electricity/rto/fuel-type-data/data", params)
            data = response.get("response", {}).get("data", [])

            if not data:
                return pd.DataFrame(columns=["timestamp", "fuel_type", "generation_mw"])

            records = []
            for item in data:
                fuel_type = item.get("fueltype", "unknown")
                # Map EIA fuel type codes to readable names
                fuel_name = _map_fuel_type(fuel_type)

                records.append(
                    {
                        "timestamp": pd.Timestamp(
                            item.get("period"), tz=ERCOT_TIMEZONE
                        ),
                        "fuel_type": fuel_name,
                        "generation_mw": float(item.get("value", 0)),
                    }
                )

            return pd.DataFrame(records)

        except Exception as e:
            logger.error(f"Failed to fetch EIA generation by fuel: {e}")
            return pd.DataFrame(columns=["timestamp", "fuel_type", "generation_mw"])

    def get_interchange(
        self,
        start: str | pd.Timestamp,
        end: str | pd.Timestamp | None = None,
    ) -> pd.DataFrame:
        """Get hourly interchange data for ERCOT.

        Fetches net interchange (imports minus exports) with neighboring
        regions. Note: ERCOT has limited interconnections due to Texas's
        isolated grid.

        Args:
            start: Start date
            end: End date (defaults to start + 7 days)

        Returns:
            DataFrame with columns: timestamp, interchange_mw
        """
        start_ts = pd.Timestamp(start)
        end_ts = pd.Timestamp(end) if end else start_ts + pd.Timedelta(days=7)

        params = {
            "frequency": "hourly",
            "data[0]": "value",
            "facets[respondent][]": ERCOT_BA_CODE,
            "facets[type][]": "TI",  # Total Interchange
            "start": start_ts.strftime("%Y-%m-%dT00"),
            "end": end_ts.strftime("%Y-%m-%dT23"),
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
        }

        try:
            response = self._make_request("electricity/rto/region-data/data", params)
            data = response.get("response", {}).get("data", [])

            if not data:
                return pd.DataFrame(columns=["timestamp", "interchange_mw"])

            records = []
            for item in data:
                records.append(
                    {
                        "timestamp": pd.Timestamp(
                            item.get("period"), tz=ERCOT_TIMEZONE
                        ),
                        "interchange_mw": float(item.get("value", 0)),
                    }
                )

            return pd.DataFrame(records)

        except Exception as e:
            logger.error(f"Failed to fetch EIA interchange data: {e}")
            return pd.DataFrame(columns=["timestamp", "interchange_mw"])


def _map_fuel_type(code: str) -> str:
    """Map EIA fuel type code to readable name."""
    mapping = {
        "COL": "coal",
        "NG": "natural_gas",
        "NUC": "nuclear",
        "OIL": "oil",
        "WAT": "hydro",
        "WND": "wind",
        "SUN": "solar",
        "OTH": "other",
        "UNK": "unknown",
    }
    return mapping.get(code.upper(), code.lower())
