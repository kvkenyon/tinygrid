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

        return cls(
            url=doc.get("DownloadLink", ""),
            publish_date=publish_date,
            doc_id=doc.get("DocID", ""),
            constructed_name=doc.get("ConstructedName", ""),
            friendly_name=friendly_name,
            friendly_name_timestamp=friendly_ts,
        )


def parse_timestamp_from_friendly_name(friendly_name: str) -> pd.Timestamp | None:
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

        Supports CSV and Excel files.

        Args:
            doc: The Document to download
            sheet_name: Sheet name for Excel files

        Returns:
            DataFrame with document contents
        """
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.get(doc.url)
                response.raise_for_status()
                content = response.content
        except Exception as e:
            logger.error(f"Failed to download document {doc.doc_id}: {e}")
            return pd.DataFrame()

        # Determine file type from URL or content
        url_lower = doc.url.lower()
        try:
            if ".csv" in url_lower:
                return pd.read_csv(io.BytesIO(content))
            elif ".xlsx" in url_lower or ".xls" in url_lower:
                return pd.read_excel(io.BytesIO(content), sheet_name=sheet_name)
            elif ".zip" in url_lower:
                # Handle zipped CSV
                import zipfile

                with zipfile.ZipFile(io.BytesIO(content)) as zf:
                    # Find CSV file in zip
                    csv_files = [n for n in zf.namelist() if n.endswith(".csv")]
                    if csv_files:
                        with zf.open(csv_files[0]) as f:
                            return pd.read_csv(f)
            else:
                # Try CSV first, then Excel
                try:
                    return pd.read_csv(io.BytesIO(content))
                except Exception:
                    return pd.read_excel(io.BytesIO(content), sheet_name=sheet_name)
        except Exception as e:
            logger.error(f"Failed to parse document {doc.doc_id}: {e}")
            return pd.DataFrame()

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

    def get_settlement_point_mapping(self) -> pd.DataFrame:
        """Get the current settlement point mapping.

        Returns a DataFrame with settlement point names, types, and
        associated electrical buses.

        Returns:
            DataFrame with settlement point mapping
        """
        report_type_id = REPORT_TYPE_IDS["settlement_points_mapping"]
        doc = self._get_document(report_type_id, latest=True)

        if not doc:
            logger.warning("No settlement point mapping found")
            return pd.DataFrame()

        return self.read_doc(doc)
