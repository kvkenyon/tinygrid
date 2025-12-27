"""Pytest configuration and shared fixtures"""

from unittest.mock import MagicMock

import pandas as pd
import pytest
from pyercot.models.report import Report
from pyercot.models.report_data import ReportData

from pyercot import Client as ERCOTClient


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
