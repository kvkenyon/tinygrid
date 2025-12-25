"""Pytest configuration and shared fixtures"""

from unittest.mock import MagicMock

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

