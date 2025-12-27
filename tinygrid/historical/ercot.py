"""ERCOT historical data archive access."""

from __future__ import annotations

import io
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from zipfile import ZipFile

import httpx
import pandas as pd
from attrs import define, field

from ..constants.ercot import PUBLIC_API_BASE_URL
from ..errors import GridAPIError, GridRetryExhaustedError
from ..utils.dates import format_api_datetime

if TYPE_CHECKING:
    from ..ercot import ERCOT

logger = logging.getLogger(__name__)

# Maximum batch size for bulk downloads (ERCOT limit)
MAX_BATCH_SIZE = 1000

# Default page size for archive listings
DEFAULT_ARCHIVE_PAGE_SIZE = 1000


@dataclass
class ArchiveLink:
    """Represents a link to an archived document."""

    doc_id: str
    url: str
    post_datetime: str
    filename: str | None = None


@define
class ERCOTArchive:
    """Access ERCOT historical data archives.

    Provides efficient bulk download of historical data using ERCOT's
    archive API with POST-based batch downloads.

    Example:
        ```python
        from tinygrid import ERCOT
        from tinygrid.historical import ERCOTArchive

        ercot = ERCOT(auth=auth)
        archive = ERCOTArchive(client=ercot)

        # Fetch historical SPP data
        df = archive.fetch_historical(
            endpoint="/np6-905-cd/spp_node_zone_hub",
            start=pd.Timestamp("2024-01-01"),
            end=pd.Timestamp("2024-01-07"),
        )
        ```
    """

    client: ERCOT
    batch_size: int = field(default=MAX_BATCH_SIZE)
    max_concurrent: int = field(default=5)
    timeout: float = field(default=60.0)

    def get_archive_links(
        self,
        emil_id: str,
        start: pd.Timestamp,
        end: pd.Timestamp,
    ) -> list[ArchiveLink]:
        """Fetch archive download links for a date range.

        Args:
            emil_id: ERCOT EMIL ID (e.g., "np6-905-cd")
            start: Start timestamp
            end: End timestamp

        Returns:
            List of ArchiveLink objects with download URLs
        """
        url = f"{PUBLIC_API_BASE_URL}/archive/{emil_id}"
        all_archives: list[ArchiveLink] = []

        page = 1
        total_pages = 1

        while page <= total_pages:
            params = {
                "postDatetimeFrom": format_api_datetime(start),
                "postDatetimeTo": format_api_datetime(end),
                "size": DEFAULT_ARCHIVE_PAGE_SIZE,
                "page": page,
            }

            response = self._make_request(url, params)

            if page == 1:
                meta = response.get("_meta", {})
                total_pages = meta.get("totalPages", 1)
                logger.debug(
                    f"Archive listing: {total_pages} pages for {emil_id}"
                )

            archives = response.get("archives", [])
            for archive in archives:
                links = archive.get("_links", {})
                endpoint = links.get("endpoint", {})
                href = endpoint.get("href", "")

                if href:
                    doc_id = href.split("=")[-1] if "=" in href else ""
                    all_archives.append(
                        ArchiveLink(
                            doc_id=doc_id,
                            url=href,
                            post_datetime=archive.get("postDatetime", ""),
                        )
                    )

            page += 1

        logger.info(f"Found {len(all_archives)} archives for {emil_id}")
        return all_archives

    def bulk_download(
        self,
        doc_ids: list[str],
        emil_id: str,
    ) -> list[tuple[io.BytesIO, str]]:
        """Bulk download documents using POST endpoint.

        More efficient than individual downloads - fetches up to 1000 docs per request.

        Args:
            doc_ids: List of document IDs to download
            emil_id: ERCOT EMIL ID

        Returns:
            List of (bytes_io, filename) tuples in the same order as doc_ids
        """
        url = f"{PUBLIC_API_BASE_URL}/archive/{emil_id}/download"
        results: list[tuple[io.BytesIO, str] | None] = [None] * len(doc_ids)

        # Batch the downloads
        for batch_start in range(0, len(doc_ids), self.batch_size):
            batch_end = min(batch_start + self.batch_size, len(doc_ids))
            batch = doc_ids[batch_start:batch_end]

            payload = {"docIds": batch}
            response_bytes = self._make_request(
                url, payload, method="POST", parse_json=False
            )

            # Response is a zip of zips
            with ZipFile(io.BytesIO(response_bytes)) as outer_zip:
                for inner_name in outer_zip.namelist():
                    # Extract doc_id from filename
                    inner_doc_id = inner_name.split(".")[0]

                    if inner_doc_id in doc_ids:
                        idx = doc_ids.index(inner_doc_id)
                        with outer_zip.open(inner_name) as inner_file:
                            results[idx] = (
                                io.BytesIO(inner_file.read()),
                                inner_name,
                            )

        # Verify all documents were fetched
        missing = [doc_ids[i] for i, r in enumerate(results) if r is None]
        if missing:
            logger.warning(f"Missing {len(missing)} documents in bulk download")

        return [r for r in results if r is not None]

    def fetch_historical(
        self,
        endpoint: str,
        start: pd.Timestamp,
        end: pd.Timestamp,
        add_post_datetime: bool = False,
    ) -> pd.DataFrame:
        """Fetch historical data from archive.

        Combines archive link fetching and bulk download into a single operation.

        Args:
            endpoint: API endpoint (e.g., "/np6-905-cd/spp_node_zone_hub")
            start: Start timestamp
            end: End timestamp
            add_post_datetime: If True, add postDatetime column

        Returns:
            DataFrame with all historical data
        """
        # Extract EMIL ID from endpoint
        emil_id = endpoint.split("/")[1] if "/" in endpoint else endpoint

        # Get archive links
        links = self.get_archive_links(emil_id, start, end)

        if not links:
            logger.warning(
                f"No archives found for {endpoint} from {start} to {end}"
            )
            return pd.DataFrame()

        # Extract doc IDs and bulk download
        doc_ids = [link.doc_id for link in links]
        post_datetimes = {link.doc_id: link.post_datetime for link in links}

        files = self.bulk_download(doc_ids, emil_id)

        # Parse CSVs from zip files
        dfs: list[pd.DataFrame] = []
        for bytes_io, filename in files:
            try:
                doc_id = filename.split(".")[0]
                df = pd.read_csv(bytes_io, compression="zip")

                if add_post_datetime and doc_id in post_datetimes:
                    df["postDatetime"] = post_datetimes[doc_id]

                dfs.append(df)
            except Exception as e:
                logger.warning(f"Failed to parse {filename}: {e}")

        if not dfs:
            return pd.DataFrame()

        result = pd.concat(dfs, ignore_index=True)
        logger.info(f"Fetched {len(result)} records from {len(files)} archives")

        return result

    def fetch_historical_parallel(
        self,
        endpoint: str,
        start: pd.Timestamp,
        end: pd.Timestamp,
        add_post_datetime: bool = False,
    ) -> pd.DataFrame:
        """Fetch historical data with parallel individual downloads.

        Fallback for when bulk download is not available or fails.

        Args:
            endpoint: API endpoint
            start: Start timestamp
            end: End timestamp
            add_post_datetime: If True, add postDatetime column

        Returns:
            DataFrame with all historical data
        """
        emil_id = endpoint.split("/")[1] if "/" in endpoint else endpoint
        links = self.get_archive_links(emil_id, start, end)

        if not links:
            return pd.DataFrame()

        dfs: list[pd.DataFrame] = []

        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            futures = {
                executor.submit(self._download_single, link): link
                for link in links
            }

            for future in as_completed(futures):
                link = futures[future]
                try:
                    df = future.result()
                    if add_post_datetime:
                        df["postDatetime"] = link.post_datetime
                    dfs.append(df)
                except Exception as e:
                    logger.warning(f"Failed to download {link.doc_id}: {e}")

        if not dfs:
            return pd.DataFrame()

        return pd.concat(dfs, ignore_index=True)

    def _download_single(self, link: ArchiveLink) -> pd.DataFrame:
        """Download a single archive file."""
        response = self._make_request(link.url, parse_json=False)
        return pd.read_csv(io.BytesIO(response), compression="zip")

    def _make_request(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        method: str = "GET",
        parse_json: bool = True,
    ) -> dict[str, Any] | bytes:
        """Make an authenticated request to the ERCOT API.

        Args:
            url: Request URL
            params: Query parameters (GET) or body (POST)
            method: HTTP method
            parse_json: If True, parse response as JSON

        Returns:
            Parsed JSON dict or raw bytes
        """
        headers = self._get_auth_headers()

        try:
            with httpx.Client(timeout=self.timeout) as http_client:
                if method == "POST":
                    response = http_client.post(
                        url, json=params, headers=headers
                    )
                else:
                    response = http_client.get(
                        url, params=params, headers=headers
                    )

                if response.status_code == 429:
                    raise GridRetryExhaustedError(
                        "Rate limited by ERCOT API",
                        status_code=429,
                        endpoint=url,
                    )

                if response.status_code != 200:
                    raise GridAPIError(
                        f"ERCOT API returned {response.status_code}",
                        status_code=response.status_code,
                        response_body=response.text[:500],
                        endpoint=url,
                    )

                if parse_json:
                    return response.json()
                return response.content

        except httpx.TimeoutException as e:
            raise GridAPIError(f"Request timed out: {e}", endpoint=url) from e
        except httpx.RequestError as e:
            raise GridAPIError(f"Request failed: {e}", endpoint=url) from e

    def _get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers from the client."""
        if self.client.auth is None:
            return {}

        token = self.client.auth.get_token()
        subscription_key = self.client.auth.get_subscription_key()

        return {
            "Authorization": f"Bearer {token}",
            "Ocp-Apim-Subscription-Key": subscription_key,
        }
