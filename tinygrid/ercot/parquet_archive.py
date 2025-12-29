"""Parquet-based historical archive access using DuckDB."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import pandas as pd
from attrs import define, field

from ..constants.ercot import ERCOT_TIMEZONE

if TYPE_CHECKING:
    from .client import ERCOTBase

logger = logging.getLogger(__name__)

# Default S3 bucket for Tinygrid's public archive
DEFAULT_ARCHIVE_BUCKET = "s3://tinygrid-ercot"


@define
class ParquetArchive:
    """Access historical data via S3 Parquet lake using DuckDB.

    This acts as a drop-in replacement for ERCOTArchive but queries
    pre-processed Parquet files in S3 instead of downloading zip files
    from ERCOT's API.

    Requires:
        duckdb: for efficient S3 querying
        fsspec: for S3 filesystem access (via duckdb or pandas)
    """

    client: ERCOTBase | None = field(default=None)
    bucket_url: str = field(default=DEFAULT_ARCHIVE_BUCKET)
    use_duckdb: bool = field(default=True)

    def fetch_historical(
        self,
        endpoint: str,
        start: pd.Timestamp,
        end: pd.Timestamp,
        add_post_datetime: bool = False,
    ) -> pd.DataFrame:
        """Fetch historical data from Parquet archive.

        Args:
            endpoint: API endpoint (e.g., "/np6-905-cd/spp_node_zone_hub")
            start: Start timestamp
            end: End timestamp
            add_post_datetime: If True, add postDatetime column (mocked or from parquet)

        Returns:
            DataFrame with all historical data
        """
        # Map endpoint to parquet path structure
        # Example: /np6-905-cd/spp_node_zone_hub -> spp/
        # This mapping needs to be robust. For now, we use a simple heuristic or a map.
        dataset_path = self._map_endpoint_to_path(endpoint)
        if not dataset_path:
            logger.warning(f"No Parquet mapping found for {endpoint}")
            return pd.DataFrame()

        s3_path = f"{self.bucket_url}/{dataset_path}/*/*/*/*.parquet"

        # Format dates for query
        start_str = start.strftime("%Y-%m-%d")
        end_str = end.strftime("%Y-%m-%d")

        try:
            if self.use_duckdb:
                return self._query_duckdb(s3_path, start_str, end_str)
            else:
                return self._query_pandas(s3_path, start, end)
        except Exception as e:
            logger.warning(f"Failed to fetch from Parquet archive: {e}")
            return pd.DataFrame()

    def _query_duckdb(self, s3_path: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Query S3 using DuckDB."""
        try:
            import duckdb
        except ImportError:
            logger.warning("duckdb not installed, falling back to empty result")
            return pd.DataFrame()

        # DuckDB query with hive partitioning
        # We assume partition keys are year, month, day
        # DeliveryDate is inside the file
        query = f"""
        SELECT *
        FROM read_parquet('{s3_path}', hive_partitioning=1)
        WHERE DeliveryDate >= '{start_date}'
          AND DeliveryDate <= '{end_date}'
        """
        
        # In a real implementation, we would configure S3 credentials here if needed
        # duckdb.sql("INSTALL httpfs; LOAD httpfs;")
        
        return duckdb.sql(query).df()

    def _query_pandas(self, s3_path: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
        """Fallback using Pandas (reads all files, slow!)."""
        # This is inefficient without precise file listing, included only as fallback
        # Real implementation should list keys in S3 matching the date range first
        logger.warning("Pandas fallback for S3 Parquet is not fully implemented (inefficient)")
        return pd.DataFrame()

    def _map_endpoint_to_path(self, endpoint: str) -> str | None:
        """Map ERCOT endpoint to S3 prefix."""
        # Simple mapping for POC
        mapping = {
            "/np6-905-cd/spp_node_zone_hub": "real_time_spp",
            "/np4-190-cd/dam_stlmnt_pnt_prices": "dam_spp",
            "/np6-788-cd/lmp_node_zone_hub": "real_time_lmp_node",
        }
        return mapping.get(endpoint)
