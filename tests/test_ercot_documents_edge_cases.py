from unittest.mock import MagicMock, patch

import pandas as pd

from tinygrid.ercot.documents import (
    Document,
    ERCOTDocumentsMixin,
    build_download_url,
    parse_timestamp_from_friendly_name,
)


class TestDocumentsCoverage:
    def test_document_from_json_coverage(self):
        # Missing DownloadLink -> build from DocID
        data = {
            "Document": {
                "DocID": "123",
                "PublishDate": "",
                "FriendlyName": "Report",
                "ConstructedName": "report.zip",
                # No DownloadLink
            }
        }
        doc = Document.from_json(data)
        assert doc.url == build_download_url("123")
        assert pd.isna(doc.publish_date)

        # Test empty everything
        doc = Document.from_json({})
        assert doc.doc_id == ""

    def test_parse_timestamp_coverage(self):
        assert parse_timestamp_from_friendly_name("") is None
        assert parse_timestamp_from_friendly_name("No Date Here") is None

        # Test exception in parsing (though regex ensures format usually)
        # We can force it by mocking
        with patch("pandas.to_datetime", side_effect=Exception("Boom")):
            assert parse_timestamp_from_friendly_name("202401") is None

    def test_get_documents_exceptions(self):
        mixin = ERCOTDocumentsMixin()

        # Test HTTP error
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = Exception(
                "Net error"
            )
            docs = mixin._get_documents(123)
            assert docs == []

        # Test JSON parse error or bad structure (exception in loop)
        with patch("httpx.Client") as mock_client:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {
                "ListDocsByRptTypeRes": {"DocumentList": [{"Bad": "Data"}]}
            }
            mock_client.return_value.__enter__.return_value.get.return_value = mock_resp

            with patch(
                "tinygrid.ercot.documents.Document.from_json",
                side_effect=Exception("Parse error"),
            ):
                docs = mixin._get_documents(123)
                assert docs == []

    def test_read_doc_coverage(self):
        mixin = ERCOTDocumentsMixin()
        doc = Document("url", pd.Timestamp.now(), "id", "name", "friendly")

        # Test download exception
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = Exception(
                "Download failed"
            )
            df = mixin.read_doc(doc)
            assert df.empty

        # Test empty ZIP
        with patch("httpx.Client") as mock_client:
            mock_resp = MagicMock()
            mock_resp.content = b"PK\x03\x04" + b"\x00" * 100  # Minimal fake zip header
            mock_client.return_value.__enter__.return_value.get.return_value = mock_resp

            with patch("zipfile.ZipFile") as mock_zip:
                mock_zip.return_value.__enter__.return_value.namelist.return_value = []
                df = mixin.read_doc(doc)
                assert df.empty

        # Test ZIP parsing exceptions (csv read fail)
        with patch("httpx.Client") as mock_client:
            mock_resp = MagicMock()
            mock_resp.content = b"PK\x03\x04"  # Zip magic
            mock_client.return_value.__enter__.return_value.get.return_value = mock_resp

            with patch("zipfile.ZipFile") as mock_zip:
                zf_mock = mock_zip.return_value.__enter__.return_value
                zf_mock.namelist.return_value = ["test.txt"]  # No csv/xlsx
                zf_mock.open.return_value.__enter__.return_value.read.return_value = (
                    b"garbage"
                )

                # Should fallback to trying read_csv then read_excel on garbage
                # pd.read_csv might succeed with garbage as 1-col dataframe, or fail.
                # pd.read_excel will likely fail.

                with patch("pandas.read_csv", side_effect=Exception("CSV Fail")):
                    with patch(
                        "pandas.read_excel", side_effect=Exception("Excel Fail")
                    ):
                        df = mixin.read_doc(doc)
                        # Should return empty DF on exception in the nested try/except block
                        # Wait, the code catches Exception and logs error in the OUTER block?
                        # No, inside read_doc:
                        # try: ... return pd.read_csv ... except: return pd.read_excel
                        # if read_excel fails, it bubbles up to the outer try/except block which catches it
                        assert df.empty

    def test_get_historical_not_found(self):
        mixin = ERCOTDocumentsMixin()

        # Mock _get_documents returning empty list
        with patch.object(mixin, "_get_documents", return_value=[]):
            assert mixin.get_rtm_spp_historical(2020).empty
            assert mixin.get_dam_spp_historical(2020).empty

        # Mock _get_documents returning docs but none match year
        doc = Document("url", pd.Timestamp("2021-01-01"), "id", "name", "friendly 2021")
        with patch.object(mixin, "_get_documents", return_value=[doc]):
            assert mixin.get_rtm_spp_historical(2020).empty

    def test_get_mapping_coverage(self):
        mixin = ERCOTDocumentsMixin()

        # No doc found
        with patch.object(mixin, "_get_document", return_value=None):
            assert mixin.get_settlement_point_mapping() == {}

        # Download fail
        with patch.object(
            mixin,
            "_get_document",
            return_value=Document("url", pd.Timestamp.now(), "id", "name", "friendly"),
        ):
            with patch("httpx.Client") as mock_client:
                mock_client.return_value.__enter__.return_value.get.side_effect = (
                    Exception("Fail")
                )
                assert mixin.get_settlement_point_mapping() == {}

        # Parse fail (bad zip content)
        with patch.object(
            mixin,
            "_get_document",
            return_value=Document("url", pd.Timestamp.now(), "id", "name", "friendly"),
        ):
            with patch("httpx.Client") as mock_client:
                mock_client.return_value.__enter__.return_value.get.return_value.content = b"garbage"
                # This will fail zipfile.ZipFile
                assert mixin.get_settlement_point_mapping() == {}
