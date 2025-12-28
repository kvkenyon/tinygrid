import io
from zipfile import ZipFile

import httpx
import pandas as pd
import pytest

from tinygrid.errors import GridAPIError
from tinygrid.historical.ercot import ArchiveLink, ERCOTArchive


class DummyClient:
    def __init__(self, auth=None) -> None:
        self.auth = auth


def make_zip_bytes(csv: str) -> io.BytesIO:
    """Create a zip file in memory containing a CSV payload."""
    buf = io.BytesIO()
    with ZipFile(buf, "w") as zf:
        zf.writestr("data.csv", csv)
    buf.seek(0)
    return buf


def test_fetch_historical_returns_empty_when_no_links() -> None:
    class NoLinksArchive(ERCOTArchive):
        def get_archive_links(self, emil_id, start, end):  # type: ignore[override]
            return []

    archive = NoLinksArchive(client=DummyClient())

    df = archive.fetch_historical(
        "/np6-905-cd/spp_node_zone_hub",
        pd.Timestamp("2024-01-01"),
        pd.Timestamp("2024-01-02"),
    )

    assert df.empty


def test_fetch_historical_adds_post_datetime() -> None:
    class DownloadArchive(ERCOTArchive):
        def get_archive_links(self, emil_id, start, end):  # type: ignore[override]
            return [
                ArchiveLink(
                    doc_id="123",
                    url="https://example.com/doc?id=123",
                    post_datetime="2024-01-01T00:00:00Z",
                )
            ]

        def bulk_download(self, doc_ids, emil_id):  # type: ignore[override]
            csv_bytes = make_zip_bytes("col1,col2\n1,2\n")
            return [(csv_bytes, "123.zip")]

    archive = DownloadArchive(client=DummyClient())

    df = archive.fetch_historical(
        "/np6-905-cd/spp_node_zone_hub",
        pd.Timestamp("2024-01-01"),
        pd.Timestamp("2024-01-02"),
        add_post_datetime=True,
    )

    assert not df.empty
    assert df["postDatetime"].iloc[0] == "2024-01-01T00:00:00Z"


def test_fetch_historical_parallel_handles_partial_failures() -> None:
    class ParallelArchive(ERCOTArchive):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.links = [
                ArchiveLink(
                    doc_id="ok", url="http://example.com/ok", post_datetime="2024-01-01"
                ),
                ArchiveLink(
                    doc_id="fail",
                    url="http://example.com/fail",
                    post_datetime="2024-01-02",
                ),
            ]

        def get_archive_links(self, emil_id, start, end):  # type: ignore[override]
            return self.links

        def _download_single(self, link: ArchiveLink) -> pd.DataFrame:  # type: ignore[override]
            if link.doc_id == "fail":
                raise ValueError("boom")
            return pd.DataFrame({"DeliveryDate": ["2024-01-01"], "val": [1]})

    archive = ParallelArchive(client=DummyClient(), max_concurrent=2)

    df = archive.fetch_historical_parallel(
        "/np6-905-cd/spp_node_zone_hub",
        pd.Timestamp("2024-01-01"),
        pd.Timestamp("2024-01-02"),
        add_post_datetime=True,
    )

    assert len(df) == 1
    assert df["postDatetime"].iloc[0] == "2024-01-01"


def test_fetch_historical_parallel_returns_empty_when_no_links() -> None:
    class NoLinksArchive(ERCOTArchive):
        def get_archive_links(self, emil_id, start, end):  # type: ignore[override]
            return []

    archive = NoLinksArchive(client=DummyClient())
    df = archive.fetch_historical_parallel(
        "/np6-905-cd/spp_node_zone_hub",
        pd.Timestamp("2024-01-01"),
        pd.Timestamp("2024-01-02"),
    )

    assert df.empty


def test_fetch_historical_handles_parse_failure() -> None:
    class BadDownloadArchive(ERCOTArchive):
        def get_archive_links(self, emil_id, start, end):  # type: ignore[override]
            return [
                ArchiveLink(
                    doc_id="bad",
                    url="https://example.com/bad",
                    post_datetime="2024-01-01",
                ),
            ]

        def bulk_download(self, doc_ids, emil_id):  # type: ignore[override]
            # Return invalid zip content to trigger parse failure
            return [(io.BytesIO(b"not-a-zip"), "bad.zip")]

    archive = BadDownloadArchive(client=DummyClient())

    df = archive.fetch_historical(
        "/np6-905-cd/spp_node_zone_hub",
        pd.Timestamp("2024-01-01"),
        pd.Timestamp("2024-01-02"),
        add_post_datetime=True,
    )

    assert df.empty


def test_fetch_historical_parallel_all_failures_returns_empty() -> None:
    class AllFailArchive(ERCOTArchive):
        def get_archive_links(self, emil_id, start, end):  # type: ignore[override]
            return [
                ArchiveLink(
                    doc_id="bad",
                    url="http://example.com/bad",
                    post_datetime="2024-01-01",
                ),
            ]

        def _download_single(self, link: ArchiveLink) -> pd.DataFrame:  # type: ignore[override]
            raise RuntimeError("fail")

    archive = AllFailArchive(client=DummyClient(), max_concurrent=1)

    df = archive.fetch_historical_parallel(
        "/np6-905-cd/spp_node_zone_hub",
        pd.Timestamp("2024-01-01"),
        pd.Timestamp("2024-01-02"),
    )

    assert df.empty


def test_download_single_reads_zip(monkeypatch: pytest.MonkeyPatch) -> None:
    class DownloadArchive(ERCOTArchive):
        def _make_request(self, url, parse_json=True):  # type: ignore[override]
            return make_zip_bytes("col1\n1\n").getvalue()

    archive = DownloadArchive(client=DummyClient())
    link = ArchiveLink(
        doc_id="1", url="http://example.com/1", post_datetime="2024-01-01"
    )

    df = archive._download_single(link)

    assert df.iloc[0]["col1"] == 1


def test_make_request_handles_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    class TimeoutClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            raise httpx.TimeoutException("timeout")

        def __exit__(self, exc_type, exc, tb):
            return False

    archive = ERCOTArchive(client=DummyClient())
    monkeypatch.setattr(httpx, "Client", TimeoutClient)

    with pytest.raises(GridAPIError):
        archive._make_request("http://example.com")


def test_make_request_handles_request_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class ErrorClient:
        def __init__(self, *args, **kwargs):
            self

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, *args, **kwargs):
            raise httpx.RequestError("fail", request=None)

    archive = ERCOTArchive(client=DummyClient())
    monkeypatch.setattr(httpx, "Client", ErrorClient)

    with pytest.raises(GridAPIError):
        archive._make_request("http://example.com")


def test_get_auth_headers_uses_client_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    auth = type(
        "Auth",
        (),
        {"get_token": lambda self: "token", "get_subscription_key": lambda self: "sub"},
    )()
    archive = ERCOTArchive(client=DummyClient(auth=auth))

    headers = archive._get_auth_headers()

    assert headers["Authorization"] == "Bearer token"
    assert headers["Ocp-Apim-Subscription-Key"] == "sub"
