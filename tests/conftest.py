"""Pytest configuration and shared fixtures"""

from unittest.mock import MagicMock

import pandas as pd
import pytest
import respx

from pyercot import Client as ERCOTClient
from pyercot.models.report import Report
from pyercot.models.report_data import ReportData


@pytest.fixture
def mock_ercot_client():
    """Create a mock ERCOT client for testing."""
    client = MagicMock(spec=ERCOTClient)
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=None)
    return client


@pytest.fixture
def sample_report_data():
    """Create sample report data for testing."""
    report_data = ReportData()
    report_data.additional_properties = {
        "deliveryDate": "2024-01-01",
        "hourEnding": "1",
        "coast": 1000.0,
        "east": 2000.0,
        "north": 3000.0,
        "systemTotal": 10000.0,
    }
    return report_data


@pytest.fixture
def sample_report(sample_report_data):
    """Create a sample Report object for testing."""
    report = Report()
    report.data = sample_report_data
    return report


@pytest.fixture
def ercot_base_url():
    """Return the default ERCOT API base URL."""
    return "https://api.ercot.com/api/public-reports"


@pytest.fixture
def sample_product():
    """Create a sample Product object for testing."""
    from pyercot.models.product import Product

    product = Product()
    product.emil_id = "TEST123"
    product.name = "Test Product"
    product.description = "Test Description"
    return product


@pytest.fixture
def sample_fields():
    """Create sample field metadata for testing DataFrame conversion."""
    return [
        {"name": "SCEDTimestamp", "label": "SCED Time Stamp"},
        {"name": "repeatHourFlag", "label": "Repeat Hour Flag"},
        {"name": "electricalBus", "label": "Electrical Bus"},
        {"name": "LMP", "label": "LMP"},
    ]


@pytest.fixture
def sample_records():
    """Create sample records for testing DataFrame conversion."""
    return [
        ["2024-01-01T08:00:00", False, "BUS001", 25.50],
        ["2024-01-01T08:15:00", False, "BUS001", 26.75],
        ["2024-01-01T08:30:00", False, "BUS001", 24.00],
        ["2024-01-01T08:45:00", False, "BUS002", 27.25],
        ["2024-01-01T09:00:00", True, "BUS002", 28.50],
    ]


@pytest.fixture
def sample_paginated_response(sample_fields, sample_records):
    """Create a sample paginated API response."""
    return {
        "_meta": {
            "totalRecords": 50,
            "pageSize": 10,
            "totalPages": 5,
            "currentPage": 1,
        },
        "fields": sample_fields,
        "data": {"records": sample_records},
    }


@pytest.fixture
def sample_single_page_response(sample_fields, sample_records):
    """Create a sample single-page API response."""
    return {
        "_meta": {
            "totalRecords": 5,
            "pageSize": 10,
            "totalPages": 1,
            "currentPage": 1,
        },
        "fields": sample_fields,
        "data": {"records": sample_records},
    }


@pytest.fixture
def sample_empty_response(sample_fields):
    """Create a sample empty API response."""
    return {
        "_meta": {
            "totalRecords": 0,
            "pageSize": 10,
            "totalPages": 0,
            "currentPage": 1,
        },
        "fields": sample_fields,
        "data": {"records": []},
    }


@pytest.fixture
def expected_dataframe(sample_records, sample_fields):
    """Create expected DataFrame from sample data."""
    df = pd.DataFrame(sample_records)
    column_mapping = {i: f["label"] for i, f in enumerate(sample_fields)}
    df.rename(columns=column_mapping, inplace=True)
    return df


# ============================================================================
# HTTP Request Interception Fixtures (respx)
# ============================================================================

ERCOT_API_BASE_URL = "https://api.ercot.com/api/public-reports"
ERCOT_PUBLIC_API_BASE_URL = "https://api.ercot.com/api/public-reports"


@pytest.fixture
def mock_ercot_api():
    """Create a respx mock for the ERCOT API.

    Usage:
        def test_something(mock_ercot_api, sample_api_response):
            mock_ercot_api.get("/np6-905-cd/spp_node_zone_hub").mock(
                return_value=httpx.Response(200, json=sample_api_response)
            )
            # ... test code
    """
    with respx.mock(base_url=ERCOT_API_BASE_URL) as respx_mock:
        yield respx_mock


@pytest.fixture
def sample_api_response():
    """Standard ERCOT paginated response structure for HTTP tests."""
    return {
        "_meta": {
            "totalRecords": 1,
            "pageSize": 10000,
            "totalPages": 1,
            "currentPage": 1,
        },
        "fields": [
            {"name": "deliveryDate", "label": "Delivery Date"},
            {"name": "settlementPoint", "label": "Settlement Point"},
            {"name": "settlementPointPrice", "label": "Settlement Point Price"},
        ],
        "data": {
            "records": [
                ["2024-01-01", "LZ_HOUSTON", 45.50],
            ]
        },
    }


@pytest.fixture
def sample_product_response():
    """Sample product list response for EMIL products endpoint."""
    return {
        "products": [
            {
                "emilId": "np6-905-cd",
                "name": "Settlement Point Prices at Resource Nodes, Hubs and Load Zones",
                "description": "SPP data",
            }
        ],
        "_meta": {"totalRecords": 1},
    }


@pytest.fixture
def sample_version_response():
    """Sample version response for versioning endpoint."""
    return {
        "version": "1.0.0",
        "apiVersion": "v1",
        "buildDate": "2024-01-01",
    }


@pytest.fixture
def sample_archive_response():
    """Sample archive listing response for historical API."""
    return {
        "_meta": {
            "totalRecords": 2,
            "totalPages": 1,
            "currentPage": 1,
        },
        "archives": [
            {
                "postDatetime": "2024-01-01T00:00:00",
                "_links": {
                    "endpoint": {"href": "/archive/np6-905-cd/download?docId=12345"}
                },
            },
            {
                "postDatetime": "2024-01-02T00:00:00",
                "_links": {
                    "endpoint": {"href": "/archive/np6-905-cd/download?docId=12346"}
                },
            },
        ],
    }


@pytest.fixture
def sample_archive_listing_response():
    """Sample archive listing response."""
    return {
        "_meta": {
            "totalRecords": 2,
            "totalPages": 1,
            "currentPage": 1,
        },
        "archives": [
            {
                "postDatetime": "2024-01-01T00:00:00",
                "_links": {
                    "endpoint": {"href": "/archive/np6-905-cd/download?docId=12345"}
                },
            },
            {
                "postDatetime": "2024-01-02T00:00:00",
                "_links": {
                    "endpoint": {"href": "/archive/np6-905-cd/download?docId=12346"}
                },
            },
        ],
    }


@pytest.fixture
def sample_rtm_response():
    """Standard RTM response structure."""
    return {
        "_meta": {
            "totalRecords": 1,
            "pageSize": 10000,
            "totalPages": 1,
            "currentPage": 1,
        },
        "fields": [
            {"name": "SCEDTimestamp", "label": "SCED Time Stamp"},
            {"name": "settlementPoint", "label": "Settlement Point"},
            {"name": "LMP", "label": "LMP"},
        ],
        "data": {
            "records": [
                ["2024-01-01T08:00:00", "LZ_HOUSTON", 45.50],
            ]
        },
    }


@pytest.fixture
def sample_dam_response():
    """Standard DAM response structure."""
    return {
        "_meta": {
            "totalRecords": 1,
            "pageSize": 10000,
            "totalPages": 1,
            "currentPage": 1,
        },
        "fields": [
            {"name": "deliveryDate", "label": "Delivery Date"},
            {"name": "hourEnding", "label": "Hour Ending"},
            {"name": "settlementPoint", "label": "Settlement Point"},
            {"name": "settlementPointPrice", "label": "Settlement Point Price"},
        ],
        "data": {
            "records": [
                ["2024-01-01", "1", "LZ_HOUSTON", 45.50],
            ]
        },
    }


@pytest.fixture
def create_mock_zip_response():
    """Create a mock zip file response for bulk download."""
    import io
    from zipfile import ZipFile

    def _create():
        # Create an outer zip containing inner zips
        outer_buffer = io.BytesIO()
        with ZipFile(outer_buffer, "w") as outer_zip:
            # Create inner zip for doc 12345
            inner_buffer1 = io.BytesIO()
            with ZipFile(inner_buffer1, "w") as inner_zip:
                csv_data = "col1,col2\nvalue1,value2\n"
                inner_zip.writestr("data.csv", csv_data)
            inner_buffer1.seek(0)
            outer_zip.writestr("12345.zip", inner_buffer1.getvalue())

            # Create inner zip for doc 12346
            inner_buffer2 = io.BytesIO()
            with ZipFile(inner_buffer2, "w") as inner_zip:
                csv_data = "col1,col2\nvalue3,value4\n"
                inner_zip.writestr("data.csv", csv_data)
            inner_buffer2.seek(0)
            outer_zip.writestr("12346.zip", inner_buffer2.getvalue())

        outer_buffer.seek(0)
        return outer_buffer.getvalue()

    return _create
