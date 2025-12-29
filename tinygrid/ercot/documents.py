"""MIS (Market Information System) document fetching for ERCOT.

This module provides methods for accessing ERCOT's MIS document system
to fetch reports by report_type_id. This is useful for:
- Historical yearly data (SPP, LMP, etc.)
- Settlement point mappings
- GIS/interconnection queue data
"""

from __future__ import annotations

import io
import logging
import re
from dataclasses import dataclass
from typing import Any

import httpx
import pandas as pd

logger = logging.getLogger(__name__)

# MIS (Market Information System) base URLs
MIS_BASE_URL = "https://www.ercot.com/misapp/servlets/IceDocListJsonWS"
DOWNLOAD_BASE_URL = "https://www.ercot.com/misdownload/servlets/mirDownload"


def build_download_url(doc_id: str) -> str:
    """Build the download URL for a document.

    Args:
        doc_id: The document ID from MIS

    Returns:
        Full download URL
    """
    return f"{DOWNLOAD_BASE_URL}?doclookupId={doc_id}"


# Report Type IDs for various ERCOT reports
# See: https://www.ercot.com/services/comm/mkt_notices/archives
REPORT_TYPE_IDS = {
    # Historical Settlement Point Prices
    "historical_rtm_spp": 13061,  # NP6-785-ER - Historical RTM LZ/Hub SPP
    "historical_dam_spp": 13060,  # NP4-180-ER - Historical DAM LZ/Hub SPP
    # Real-time and Day-Ahead SPP
    "rtm_spp": 12301,  # NP6-905-CD - RTM SPP
    "dam_spp": 12331,  # NP4-190-CD - DAM SPP
    # GIS/Interconnection
    "gis_report": 15933,  # PG7-200-ER - GIS Report
    # Settlement Point Mapping
    "settlement_points_mapping": 10008,  # NP4-160-SG
    # Load Zone info
    "load_zone_info": 10000,  # NP4-33-CD
}


@dataclass
class Document:
    """Represents a document from the MIS system."""

    url: str
    publish_date: pd.Timestamp
    doc_id: str
    constructed_name: str
    friendly_name: str
    friendly_name_timestamp: pd.Timestamp | None = None

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Document:
        """Create a Document from MIS JSON response."""
        doc = data.get("Document", data)

        # Parse publish date
        publish_date_str = doc.get("PublishDate", "")
        publish_date = pd.Timestamp(publish_date_str) if publish_date_str else pd.NaT

        # Parse friendly name timestamp
        friendly_name = doc.get("FriendlyName", "")
        friendly_ts = parse_timestamp_from_friendly_name(friendly_name)

        # Get or construct download URL
        doc_id = doc.get("DocID", "")
        url = doc.get("DownloadLink", "")
        if not url and doc_id:
            url = build_download_url(doc_id)

        return cls(
            url=url,
            publish_date=publish_date,
            doc_id=doc_id,
            constructed_name=doc.get("ConstructedName", ""),
            friendly_name=friendly_name,
            friendly_name_timestamp=friendly_ts,
        )


def parse_timestamp_from_friendly_name(
    friendly_name: str,
) -> pd.Timestamp | None:
    """Parse timestamp from friendly name like '202401' or '2024-01-01'.

    Args:
        friendly_name: The friendly name string from MIS

    Returns:
        Parsed timestamp or None if parsing fails
    """
    if not friendly_name:
        return None

    # Try various date patterns
    patterns = [
        (r"(\d{4})(\d{2})$", "%Y%m"),  # 202401
        (r"(\d{4})-(\d{2})-(\d{2})", "%Y-%m-%d"),  # 2024-01-01
        (r"(\d{4})(\d{2})(\d{2})", "%Y%m%d"),  # 20240101
    ]

    for pattern, date_format in patterns:
        match = re.search(pattern, friendly_name)
        if match:
            try:
                date_str = "".join(match.groups())
                return pd.to_datetime(date_str, format=date_format.replace("-", ""))
            except Exception:
                pass

    return None


class ERCOTDocumentsMixin:
    """Mixin class providing MIS document fetching methods.

    These methods access ERCOT's Market Information System (MIS) to
    fetch reports that aren't available through the REST API.
    """

    def _get_documents(
        self,
        report_type_id: int,
        date_from: pd.Timestamp | None = None,
        date_to: pd.Timestamp | None = None,
        max_documents: int = 100,
    ) -> list[Document]:
        """Fetch documents from MIS for a report type.

        Args:
            report_type_id: The MIS report type ID
            date_from: Optional start date filter
            date_to: Optional end date filter
            max_documents: Maximum number of documents to return

        Returns:
            List of Document objects
        """
        params: dict[str, Any] = {
            "reportTypeId": report_type_id,
            "_": int(pd.Timestamp.now().timestamp() * 1000),  # Cache buster
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(MIS_BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            logger.error(f"Failed to fetch documents for report {report_type_id}: {e}")
            return []

        # Parse documents
        documents: list[Document] = []
        doc_list = data.get("ListDocsByRptTypeRes", {}).get("DocumentList", [])

        for doc_data in doc_list[:max_documents]:
            try:
                doc = Document.from_json(doc_data)

                # Apply date filters
                if date_from and doc.publish_date < date_from:
                    continue
                if date_to and doc.publish_date > date_to:
                    continue

                documents.append(doc)
            except Exception as e:
                logger.warning(f"Failed to parse document: {e}")

        return documents

    def _get_document(
        self,
        report_type_id: int,
        date: pd.Timestamp | None = None,
        latest: bool = True,
    ) -> Document | None:
        """Fetch a single document from MIS.

        Args:
            report_type_id: The MIS report type ID
            date: Optional date to filter by
            latest: If True, return the most recent document

        Returns:
            Document object or None if not found
        """
        documents = self._get_documents(
            report_type_id=report_type_id,
            date_from=date,
            date_to=date + pd.Timedelta(days=1) if date else None,
            max_documents=10,
        )

        if not documents:
            return None

        if latest:
            # Return most recent by publish date
            return max(documents, key=lambda d: d.publish_date)

        return documents[0]

    def read_doc(
        self,
        doc: Document,
        sheet_name: str | int = 0,
    ) -> pd.DataFrame:
        """Download and read a document from MIS.

        Supports CSV, Excel, and ZIP files containing CSV or Excel.

        Args:
            doc: The Document to download
            sheet_name: Sheet name for Excel files

        Returns:
            DataFrame with document contents
        """
        import zipfile

        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.get(doc.url)
                response.raise_for_status()
                content = response.content
        except Exception as e:
            logger.error(f"Failed to download document {doc.doc_id}: {e}")
            return pd.DataFrame()

        # Check if content is a ZIP file (by magic bytes)
        is_zip = content[:4] == b"PK\x03\x04"

        try:
            if is_zip:
                # Handle ZIP file
                with zipfile.ZipFile(io.BytesIO(content)) as zf:
                    file_list = zf.namelist()
                    if not file_list:
                        logger.warning(f"Empty ZIP file for document {doc.doc_id}")
                        return pd.DataFrame()

                    # Find the first data file (prefer CSV, then Excel)
                    target_file = None
                    for name in file_list:
                        name_lower = name.lower()
                        if name_lower.endswith(".csv"):
                            target_file = name
                            break
                        elif name_lower.endswith((".xlsx", ".xls")):
                            target_file = name
                            # Don't break - keep looking for CSV

                    if not target_file:
                        # Use first file
                        target_file = file_list[0]

                    with zf.open(target_file) as f:
                        file_content = f.read()

                    # Parse based on file extension
                    if target_file.lower().endswith(".csv"):
                        return pd.read_csv(io.BytesIO(file_content))
                    elif target_file.lower().endswith((".xlsx", ".xls")):
                        return pd.read_excel(
                            io.BytesIO(file_content), sheet_name=sheet_name
                        )
                    else:
                        # Try CSV first
                        try:
                            return pd.read_csv(io.BytesIO(file_content))
                        except Exception:
                            return pd.read_excel(
                                io.BytesIO(file_content), sheet_name=sheet_name
                            )
            else:
                # Not a ZIP - try to parse directly
                # Check constructed name for file extension hint
                name_lower = doc.constructed_name.lower()

                if name_lower.endswith(".csv"):
                    return pd.read_csv(io.BytesIO(content))
                elif name_lower.endswith((".xlsx", ".xls")):
                    return pd.read_excel(io.BytesIO(content), sheet_name=sheet_name)
                else:
                    # Try CSV first, then Excel
                    try:
                        return pd.read_csv(io.BytesIO(content))
                    except Exception:
                        return pd.read_excel(io.BytesIO(content), sheet_name=sheet_name)

        except Exception as e:
            logger.error(f"Failed to parse document {doc.doc_id}: {e}")
            return pd.DataFrame()

    def get_rtm_spp_historical(self, year: int) -> pd.DataFrame:
        """Get historical RTM settlement point prices for a year.

        This fetches data from ERCOT's MIS system, which provides
        complete yearly archives of RTM prices.

        Args:
            year: The year to fetch (e.g., 2023)

        Returns:
            DataFrame with settlement point prices
        """
        report_type_id = REPORT_TYPE_IDS["historical_rtm_spp"]
        documents = self._get_documents(report_type_id)

        # Find document matching the year
        target_doc = None
        for doc in documents:
            if doc.friendly_name_timestamp:
                if doc.friendly_name_timestamp.year == year:
                    target_doc = doc
                    break
            elif str(year) in doc.friendly_name:
                target_doc = doc
                break

        if not target_doc:
            logger.warning(f"No historical RTM SPP data found for {year}")
            return pd.DataFrame()

        return self.read_doc(target_doc)

    def get_dam_spp_historical(self, year: int) -> pd.DataFrame:
        """Get historical DAM settlement point prices for a year.

        This fetches data from ERCOT's MIS system, which provides
        complete yearly archives of DAM prices.

        Args:
            year: The year to fetch (e.g., 2023)

        Returns:
            DataFrame with day-ahead settlement point prices
        """
        report_type_id = REPORT_TYPE_IDS["historical_dam_spp"]
        documents = self._get_documents(report_type_id)

        # Find document matching the year
        target_doc = None
        for doc in documents:
            if doc.friendly_name_timestamp:
                if doc.friendly_name_timestamp.year == year:
                    target_doc = doc
                    break
            elif str(year) in doc.friendly_name:
                target_doc = doc
                break

        if not target_doc:
            logger.warning(f"No historical DAM SPP data found for {year}")
            return pd.DataFrame()

        return self.read_doc(target_doc)

    def get_settlement_point_mapping(self) -> dict[str, pd.DataFrame]:
        """Get the current settlement point mapping.

        Returns a dict of DataFrames with different mapping types:
        - 'settlement_points': Main settlement points list
        - 'resource_nodes': Resource node to unit mapping
        - 'hubs': Hub names and DC ties
        - 'ccp': CCP resource names
        - 'noie': Non-Opt-In Entity mapping

        Returns:
            Dict mapping name to DataFrame
        """
        import zipfile

        report_type_id = REPORT_TYPE_IDS["settlement_points_mapping"]
        doc = self._get_document(report_type_id, latest=True)

        if not doc:
            logger.warning("No settlement point mapping found")
            return {}

        # Download the ZIP
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.get(doc.url)
                response.raise_for_status()
                content = response.content
        except Exception as e:
            logger.error(f"Failed to download settlement point mapping: {e}")
            return {}

        # Read all CSV files from the ZIP
        result: dict[str, pd.DataFrame] = {}
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                for name in zf.namelist():
                    if not name.lower().endswith(".csv"):
                        continue

                    # Determine the key name from filename
                    base_name = name.split("/")[-1].lower()
                    if "settlement_point" in base_name:
                        key = "settlement_points"
                    elif "resource_node" in base_name:
                        key = "resource_nodes"
                    elif "hub" in base_name or "dc_tie" in base_name:
                        key = "hubs"
                    elif "ccp" in base_name:
                        key = "ccp"
                    elif "noie" in base_name:
                        key = "noie"
                    else:
                        key = base_name.replace(".csv", "")

                    with zf.open(name) as f:
                        result[key] = pd.read_csv(f)

        except Exception as e:
            logger.error(f"Failed to parse settlement point mapping: {e}")
            return {}

        return result
