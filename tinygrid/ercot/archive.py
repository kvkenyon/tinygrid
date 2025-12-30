"""ERCOT historical data archive access."""

from __future__ import annotations

import io
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING
from zipfile import ZipFile

import pandas as pd
from attrs import define, field

from ..constants.ercot import PUBLIC_API_BASE_URL
from ..utils.dates import format_api_datetime

if TYPE_CHECKING:
    from . import ERCOT

logger = logging.getLogger(__name__)

# Maximum batch size for bulk downloads (ERCOT limit)
MAX_BATCH_SIZE = 1000

# Default page size for archive listings
DEFAULT_ARCHIVE_PAGE_SIZE = 1000


@define
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
        from tinygrid.ercot import ERCOTArchive

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

    ercot: ERCOT
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

            response = self.ercot.make_request(url, params)

            if page == 1:
                meta = response.get("_meta", {})
                total_pages = meta.get("totalPages", 1)
                logger.debug(f"Archive listing: {total_pages} pages for {emil_id}")

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

        logger.debug(f"Fetching from {url = }")
        logger.debug(f"Batch size = {self.batch_size}")

        # Batch the downloads
        for batch_start in range(0, len(doc_ids), self.batch_size):
            batch_end = min(batch_start + self.batch_size, len(doc_ids))
            batch = doc_ids[batch_start:batch_end]

            payload = {"docIds": batch}
            logger.debug(f"{payload = }")
            response_bytes = self.ercot.make_request(
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
    ) -> dict[str, pd.DataFrame]:
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

        logger.info(f"Fetching {len(links)} links")

        if not links:
            logger.warning(f"No archives found for {endpoint} from {start} to {end}")
            return {}

        # Extract doc IDs and bulk download
        doc_ids = [link.doc_id for link in links]
        post_datetimes = {link.doc_id: link.post_datetime for link in links}

        files = self.bulk_download(doc_ids, emil_id)

        logger.info(f"Downloaded {len(files)} for {emil_id = }")

        # Parse CSVs from zip files
        dfs: dict[str, pd.DataFrame] = {}
        for bytes_io, filename in files:
            logger.debug(f"{filename = }")
            try:
                doc_id = filename.split(".")[0]
                with ZipFile(bytes_io) as zfile:
                    if len(zfile.namelist()) > 1:
                        files = self._extract_multiple_files_from_zip(zfile)
                        for file, name in files:
                            logger.debug(f"Extracting {name = }")
                            df = pd.read_csv(file)
                            if add_post_datetime and doc_id in post_datetimes:
                                df["postDatetime"] = post_datetimes[doc_id]
                            dfs[name] = df
                    else:
                        df = pd.read_csv(bytes_io, compression="zip")
                        if add_post_datetime and doc_id in post_datetimes:
                            df["postDatetime"] = post_datetimes[doc_id]
                        dfs["archive"] = df
            except Exception as e:
                logger.warning(f"Failed to parse {filename}: {e}")

        return dfs

    def _extract_multiple_files_from_zip(
        self, zfile: ZipFile
    ) -> list[tuple[io.BytesIO, str]]:
        results = []
        with zfile as zf:
            for inner_name in zf.namelist():
                with zf.open(inner_name) as inner_file:
                    results.append(
                        (
                            io.BytesIO(inner_file.read()),
                            inner_name,
                        )
                    )
        return results

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
                executor.submit(self._download_single, link): link for link in links
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
        response = self.ercot.make_request(link.url, parse_json=False)
        return pd.read_csv(io.BytesIO(response), compression="zip")


@define
class BundleLink:
    doc_id: str
    publish_date: pd.Timestamp
    download_url: str


@define
class Bundles:
    emil_id: str
    links: list[BundleLink]


@define
class ERCOTArchiveBundle:
    """The most effective way to download historic data in large quantities"""

    ercot: ERCOT

    def bundles(self, emil_id: str) -> Bundles:
        bundle_url = f"{PUBLIC_API_BASE_URL}/bundle/{emil_id}"
        response = self.ercot.make_request(bundle_url, parse_json=True)
        bundles = response.get("bundles", [])
        links = []
        for bundle in bundles:
            doc_id = bundle.get("docId")
            post_datetime = bundle.get("postDatetime")
            download_url = bundle["_links"]["endpoint"]["href"]
            if doc_id is not None and post_datetime is not None and download_url:
                links.append(
                    BundleLink(
                        doc_id=str(doc_id),
                        publish_date=post_datetime,
                        download_url=download_url,
                    )
                )
        return Bundles(emil_id=emil_id, links=links)

    def one_bundle(self, bundle_link: BundleLink) -> pd.DataFrame:
        """Download a single bundle (zip of zips of CSVs) and extract all CSVs as DataFrames.

        Args:
            bundle_link: BundleLink

        Returns:
            DataFrame containing all rows from all CSV files in all inner zip archives
        """
        dataframes: list[pd.DataFrame] = []
        response = self.ercot.make_request(bundle_link.download_url, parse_json=False)
        # Unzip the outer zip (contains inner zips)
        with ZipFile(io.BytesIO(response)) as zfile:
            for inner_zip_name in zfile.namelist():
                with zfile.open(inner_zip_name) as inner_zip_bytes:
                    with ZipFile(inner_zip_bytes) as inner_zip:
                        for csv_name in inner_zip.namelist():
                            with inner_zip.open(csv_name) as csv_file:
                                try:
                                    df = pd.read_csv(csv_file)
                                    dataframes.append(df)
                                except Exception as e:
                                    logger.error(
                                        f"Failed to parse CSV {csv_name} in bundle {bundle_link.doc_id}: {e}"
                                    )
        if not dataframes:
            return pd.DataFrame()
        return pd.concat(dataframes, ignore_index=True)

    def all(self, bundles: Bundles) -> list[pd.DataFrame]:
        """Download all bundle links from the given Bundle and extract all CSVs as DataFrames.

        Args:
            bundles: Bundles

        Returns:
            List of DataFrames, one per CSV file in all inner zip archives
        """
        all_dataframes: list[pd.DataFrame] = []
        for bundle_link in bundles.links:
            dfs = self.one(bundle_link)
            all_dataframes.extend(dfs)
        return all_dataframes
