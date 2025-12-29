"""Tests for tinygrid.ercot.documents module."""

from __future__ import annotations

import io
import zipfile
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from tinygrid.ercot.documents import (
    REPORT_TYPE_IDS,
    Document,
    ERCOTDocumentsMixin,
    build_download_url,
    parse_timestamp_from_friendly_name,
)


class TestBuildDownloadUrl:
    """Tests for build_download_url function."""

    def test_builds_correct_url(self):
        """Test URL is built correctly."""
        url = build_download_url("12345")
        assert (
            url
            == "https://www.ercot.com/misdownload/servlets/mirDownload?doclookupId=12345"
        )

    def test_handles_long_doc_id(self):
        """Test with long doc ID."""
        url = build_download_url("1172152090")
        assert "doclookupId=1172152090" in url


class TestParseTimestampFromFriendlyName:
    """Tests for parse_timestamp_from_friendly_name function."""

    def test_parses_yyyymm_format(self):
        """Test parsing YYYYMM format."""
        result = parse_timestamp_from_friendly_name("RTMLZHBSPP_202301")
        assert result is not None
        assert result.year == 2023
        assert result.month == 1

    def test_parses_yyyymmdd_format(self):
        """Test parsing YYYYMMDD format."""
        result = parse_timestamp_from_friendly_name("Report_20230115")
        assert result is not None
        assert result.year == 2023
        assert result.month == 1
        assert result.day == 15

    def test_parses_yyyy_mm_dd_format(self):
        """Test parsing YYYY-MM-DD format."""
        result = parse_timestamp_from_friendly_name("Report_2023-01-15_data")
        assert result is not None
        assert result.year == 2023
        assert result.month == 1
        assert result.day == 15

    def test_returns_none_for_empty_string(self):
        """Test returns None for empty string."""
        result = parse_timestamp_from_friendly_name("")
        assert result is None

    def test_returns_none_for_no_date(self):
        """Test returns None when no date pattern found."""
        result = parse_timestamp_from_friendly_name("SomeReportName")
        assert result is None


class TestDocument:
    """Tests for Document dataclass."""

    def test_from_json_with_nested_document(self):
        """Test creating Document from nested JSON structure."""
        data = {
            "Document": {
                "DocID": "12345",
                "PublishDate": "2023-01-15T10:00:00-06:00",
                "ConstructedName": "report.zip",
                "FriendlyName": "RTMLZHBSPP_2023",
            }
        }
        doc = Document.from_json(data)
        assert doc.doc_id == "12345"
        assert doc.friendly_name == "RTMLZHBSPP_2023"
        assert doc.constructed_name == "report.zip"
        assert "doclookupId=12345" in doc.url

    def test_from_json_with_flat_structure(self):
        """Test creating Document from flat JSON structure."""
        data = {
            "DocID": "67890",
            "PublishDate": "2023-06-01T08:00:00-06:00",
            "ConstructedName": "data.csv",
            "FriendlyName": "TestReport",
        }
        doc = Document.from_json(data)
        assert doc.doc_id == "67890"
        assert doc.friendly_name == "TestReport"

    def test_from_json_with_download_link(self):
        """Test that existing DownloadLink is used if present."""
        data = {
            "DocID": "12345",
            "DownloadLink": "https://example.com/download/12345",
            "PublishDate": "2023-01-15T10:00:00-06:00",
            "ConstructedName": "report.zip",
            "FriendlyName": "Report",
        }
        doc = Document.from_json(data)
        assert doc.url == "https://example.com/download/12345"

    def test_from_json_with_empty_publish_date(self):
        """Test handling empty publish date."""
        data = {
            "DocID": "12345",
            "PublishDate": "",
            "ConstructedName": "report.zip",
            "FriendlyName": "Report",
        }
        doc = Document.from_json(data)
        assert pd.isna(doc.publish_date)

    def test_from_json_parses_friendly_name_timestamp(self):
        """Test that friendly name timestamp is parsed."""
        data = {
            "DocID": "12345",
            "PublishDate": "2023-01-15T10:00:00-06:00",
            "FriendlyName": "RTMLZHBSPP_202306",
        }
        doc = Document.from_json(data)
        assert doc.friendly_name_timestamp is not None
        assert doc.friendly_name_timestamp.year == 2023
        assert doc.friendly_name_timestamp.month == 6


class TestERCOTDocumentsMixin:
    """Tests for ERCOTDocumentsMixin class."""

    @pytest.fixture
    def mixin_instance(self):
        """Create a test instance with the mixin."""

        class TestClass(ERCOTDocumentsMixin):
            pass

        return TestClass()

    def test_get_documents_success(self, mixin_instance):
        """Test successful document listing."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "ListDocsByRptTypeRes": {
                "DocumentList": [
                    {
                        "Document": {
                            "DocID": "12345",
                            "PublishDate": "2023-01-15T10:00:00-06:00",
                            "FriendlyName": "Report_2023",
                        }
                    },
                    {
                        "Document": {
                            "DocID": "67890",
                            "PublishDate": "2023-02-15T10:00:00-06:00",
                            "FriendlyName": "Report_2023_02",
                        }
                    },
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("tinygrid.ercot.documents.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = (
                mock_response
            )
            docs = mixin_instance._get_documents(13061, max_documents=10)

        assert len(docs) == 2
        assert docs[0].doc_id == "12345"
        assert docs[1].doc_id == "67890"

    def test_get_documents_with_date_filter(self, mixin_instance):
        """Test document listing with date filter."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "ListDocsByRptTypeRes": {
                "DocumentList": [
                    {
                        "Document": {
                            "DocID": "12345",
                            "PublishDate": "2023-01-15T10:00:00-06:00",
                            "FriendlyName": "Report_2023",
                        }
                    },
                    {
                        "Document": {
                            "DocID": "67890",
                            "PublishDate": "2023-06-15T10:00:00-06:00",
                            "FriendlyName": "Report_2023_06",
                        }
                    },
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("tinygrid.ercot.documents.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = (
                mock_response
            )
            docs = mixin_instance._get_documents(
                13061,
                date_from=pd.Timestamp("2023-05-01", tz="UTC"),
                max_documents=10,
            )

        # Only the June document should pass the filter
        assert len(docs) == 1
        assert docs[0].doc_id == "67890"

    def test_get_documents_http_error(self, mixin_instance):
        """Test document listing handles HTTP errors."""
        with patch("tinygrid.ercot.documents.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = Exception(
                "Network error"
            )
            docs = mixin_instance._get_documents(13061)

        assert docs == []

    def test_get_document_returns_latest(self, mixin_instance):
        """Test _get_document returns latest document."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "ListDocsByRptTypeRes": {
                "DocumentList": [
                    {
                        "Document": {
                            "DocID": "old",
                            "PublishDate": "2023-01-15T10:00:00-06:00",
                            "FriendlyName": "Report",
                        }
                    },
                    {
                        "Document": {
                            "DocID": "new",
                            "PublishDate": "2023-06-15T10:00:00-06:00",
                            "FriendlyName": "Report",
                        }
                    },
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("tinygrid.ercot.documents.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = (
                mock_response
            )
            doc = mixin_instance._get_document(13061, latest=True)

        assert doc is not None
        assert doc.doc_id == "new"

    def test_get_document_returns_none_when_empty(self, mixin_instance):
        """Test _get_document returns None when no documents."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"ListDocsByRptTypeRes": {"DocumentList": []}}
        mock_response.raise_for_status = MagicMock()

        with patch("tinygrid.ercot.documents.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = (
                mock_response
            )
            doc = mixin_instance._get_document(13061)

        assert doc is None

    def test_read_doc_csv(self, mixin_instance):
        """Test reading CSV document."""
        csv_content = b"col1,col2\n1,2\n3,4"
        mock_response = MagicMock()
        mock_response.content = csv_content
        mock_response.raise_for_status = MagicMock()

        doc = Document(
            url="https://example.com/doc.csv",
            publish_date=pd.Timestamp("2023-01-15"),
            doc_id="12345",
            constructed_name="report.csv",
            friendly_name="Report",
        )

        with patch("tinygrid.ercot.documents.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = (
                mock_response
            )
            df = mixin_instance.read_doc(doc)

        assert len(df) == 2
        assert list(df.columns) == ["col1", "col2"]

    def test_read_doc_excel_in_zip(self, mixin_instance):
        """Test reading Excel file inside ZIP."""
        # Create a ZIP with an Excel file
        excel_buffer = io.BytesIO()
        pd.DataFrame({"a": [1, 2], "b": [3, 4]}).to_excel(excel_buffer, index=False)
        excel_content = excel_buffer.getvalue()

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("data.xlsx", excel_content)
        zip_content = zip_buffer.getvalue()

        mock_response = MagicMock()
        mock_response.content = zip_content
        mock_response.raise_for_status = MagicMock()

        doc = Document(
            url="https://example.com/doc.zip",
            publish_date=pd.Timestamp("2023-01-15"),
            doc_id="12345",
            constructed_name="report.zip",
            friendly_name="Report",
        )

        with patch("tinygrid.ercot.documents.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = (
                mock_response
            )
            df = mixin_instance.read_doc(doc)

        assert len(df) == 2
        assert list(df.columns) == ["a", "b"]

    def test_read_doc_csv_in_zip(self, mixin_instance):
        """Test reading CSV file inside ZIP."""
        csv_content = b"x,y\n10,20\n30,40"

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("data.csv", csv_content)
        zip_content = zip_buffer.getvalue()

        mock_response = MagicMock()
        mock_response.content = zip_content
        mock_response.raise_for_status = MagicMock()

        doc = Document(
            url="https://example.com/doc.zip",
            publish_date=pd.Timestamp("2023-01-15"),
            doc_id="12345",
            constructed_name="report.zip",
            friendly_name="Report",
        )

        with patch("tinygrid.ercot.documents.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = (
                mock_response
            )
            df = mixin_instance.read_doc(doc)

        assert len(df) == 2
        assert list(df.columns) == ["x", "y"]

    def test_read_doc_empty_zip(self, mixin_instance):
        """Test reading empty ZIP file."""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w"):
            pass
        zip_content = zip_buffer.getvalue()

        mock_response = MagicMock()
        mock_response.content = zip_content
        mock_response.raise_for_status = MagicMock()

        doc = Document(
            url="https://example.com/doc.zip",
            publish_date=pd.Timestamp("2023-01-15"),
            doc_id="12345",
            constructed_name="report.zip",
            friendly_name="Report",
        )

        with patch("tinygrid.ercot.documents.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = (
                mock_response
            )
            df = mixin_instance.read_doc(doc)

        assert df.empty

    def test_read_doc_download_error(self, mixin_instance):
        """Test read_doc handles download errors."""
        doc = Document(
            url="https://example.com/doc.csv",
            publish_date=pd.Timestamp("2023-01-15"),
            doc_id="12345",
            constructed_name="report.csv",
            friendly_name="Report",
        )

        with patch("tinygrid.ercot.documents.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = Exception(
                "Download failed"
            )
            df = mixin_instance.read_doc(doc)

        assert df.empty

    def test_get_rtm_spp_historical(self, mixin_instance):
        """Test getting RTM SPP historical data."""
        # Create mock CSV content
        csv_content = b"Date,Price\n2023-01-01,10.5\n2023-01-02,11.0"

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("data.csv", csv_content)
        zip_content = zip_buffer.getvalue()

        # Mock the document listing
        mock_list_response = MagicMock()
        mock_list_response.json.return_value = {
            "ListDocsByRptTypeRes": {
                "DocumentList": [
                    {
                        "Document": {
                            "DocID": "12345",
                            "PublishDate": "2024-01-01T10:00:00-06:00",
                            "FriendlyName": "RTMLZHBSPP_2023",
                        }
                    },
                ]
            }
        }
        mock_list_response.raise_for_status = MagicMock()

        # Mock the download
        mock_download_response = MagicMock()
        mock_download_response.content = zip_content
        mock_download_response.raise_for_status = MagicMock()

        with patch("tinygrid.ercot.documents.httpx.Client") as mock_client:
            mock_get = mock_client.return_value.__enter__.return_value.get
            mock_get.side_effect = [mock_list_response, mock_download_response]

            df = mixin_instance.get_rtm_spp_historical(2023)

        assert len(df) == 2
        assert "Price" in df.columns

    def test_get_rtm_spp_historical_not_found(self, mixin_instance):
        """Test RTM SPP historical returns empty when year not found."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "ListDocsByRptTypeRes": {
                "DocumentList": [
                    {
                        "Document": {
                            "DocID": "12345",
                            "PublishDate": "2024-01-01T10:00:00-06:00",
                            "FriendlyName": "RTMLZHBSPP_2024",
                        }
                    },
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("tinygrid.ercot.documents.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = (
                mock_response
            )
            df = mixin_instance.get_rtm_spp_historical(2020)

        assert df.empty

    def test_get_dam_spp_historical(self, mixin_instance):
        """Test getting DAM SPP historical data."""
        csv_content = b"Date,Price\n2023-01-01,15.5"

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("data.csv", csv_content)
        zip_content = zip_buffer.getvalue()

        mock_list_response = MagicMock()
        mock_list_response.json.return_value = {
            "ListDocsByRptTypeRes": {
                "DocumentList": [
                    {
                        "Document": {
                            "DocID": "67890",
                            "PublishDate": "2024-01-01T10:00:00-06:00",
                            "FriendlyName": "DAMLZHBSPP_2023",
                        }
                    },
                ]
            }
        }
        mock_list_response.raise_for_status = MagicMock()

        mock_download_response = MagicMock()
        mock_download_response.content = zip_content
        mock_download_response.raise_for_status = MagicMock()

        with patch("tinygrid.ercot.documents.httpx.Client") as mock_client:
            mock_get = mock_client.return_value.__enter__.return_value.get
            mock_get.side_effect = [mock_list_response, mock_download_response]

            df = mixin_instance.get_dam_spp_historical(2023)

        assert len(df) == 1

    def test_get_settlement_point_mapping(self, mixin_instance):
        """Test getting settlement point mapping."""
        # Create ZIP with multiple CSVs
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr(
                "SP_List_EB_Mapping/Settlement_Points_123.csv",
                b"BUS,NODE\nBUS1,NODE1\nBUS2,NODE2",
            )
            zf.writestr(
                "SP_List_EB_Mapping/Hub_Name_AND_DC_Ties_123.csv",
                b"NAME\nHUB1\nHUB2",
            )
            zf.writestr(
                "SP_List_EB_Mapping/CCP_Resource_Names_123.csv",
                b"CCP_NAME,NODE\nCCP1,N1",
            )
        zip_content = zip_buffer.getvalue()

        mock_list_response = MagicMock()
        mock_list_response.json.return_value = {
            "ListDocsByRptTypeRes": {
                "DocumentList": [
                    {
                        "Document": {
                            "DocID": "99999",
                            "PublishDate": "2024-01-01T10:00:00-06:00",
                            "FriendlyName": "SP_Mapping",
                        }
                    },
                ]
            }
        }
        mock_list_response.raise_for_status = MagicMock()

        mock_download_response = MagicMock()
        mock_download_response.content = zip_content
        mock_download_response.raise_for_status = MagicMock()

        with patch("tinygrid.ercot.documents.httpx.Client") as mock_client:
            mock_get = mock_client.return_value.__enter__.return_value.get
            mock_get.side_effect = [mock_list_response, mock_download_response]

            result = mixin_instance.get_settlement_point_mapping()

        assert isinstance(result, dict)
        assert "settlement_points" in result
        assert "hubs" in result
        assert "ccp" in result
        assert len(result["settlement_points"]) == 2
        assert len(result["hubs"]) == 2

    def test_get_settlement_point_mapping_not_found(self, mixin_instance):
        """Test settlement point mapping returns empty dict when not found."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"ListDocsByRptTypeRes": {"DocumentList": []}}
        mock_response.raise_for_status = MagicMock()

        with patch("tinygrid.ercot.documents.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = (
                mock_response
            )
            result = mixin_instance.get_settlement_point_mapping()

        assert result == {}

    def test_get_settlement_point_mapping_download_error(self, mixin_instance):
        """Test settlement point mapping handles download errors."""
        mock_list_response = MagicMock()
        mock_list_response.json.return_value = {
            "ListDocsByRptTypeRes": {
                "DocumentList": [
                    {
                        "Document": {
                            "DocID": "99999",
                            "PublishDate": "2024-01-01T10:00:00-06:00",
                            "FriendlyName": "SP_Mapping",
                        }
                    },
                ]
            }
        }
        mock_list_response.raise_for_status = MagicMock()

        with patch("tinygrid.ercot.documents.httpx.Client") as mock_client:
            mock_get = mock_client.return_value.__enter__.return_value.get
            mock_get.side_effect = [
                mock_list_response,
                Exception("Download failed"),
            ]
            result = mixin_instance.get_settlement_point_mapping()

        assert result == {}


class TestReportTypeIds:
    """Tests for REPORT_TYPE_IDS constant."""

    def test_historical_rtm_spp_id(self):
        """Test historical RTM SPP report ID."""
        assert REPORT_TYPE_IDS["historical_rtm_spp"] == 13061

    def test_historical_dam_spp_id(self):
        """Test historical DAM SPP report ID."""
        assert REPORT_TYPE_IDS["historical_dam_spp"] == 13060

    def test_settlement_points_mapping_id(self):
        """Test settlement points mapping report ID."""
        assert REPORT_TYPE_IDS["settlement_points_mapping"] == 10008
