"""Tests for ERCOT client DataFrame conversion"""

from unittest.mock import MagicMock, patch

import pandas as pd

from tinygrid import ERCOT


class TestResponseToDataFrame:
    """Test the _response_to_dataframe method."""

    def test_empty_records_with_fields(self, sample_fields):
        """Test converting empty records with field metadata."""
        ercot = ERCOT()
        df = ercot._response_to_dataframe([], sample_fields)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert list(df.columns) == [
            "SCED Time Stamp",
            "Repeat Hour Flag",
            "Electrical Bus",
            "LMP",
        ]

    def test_empty_records_without_fields(self):
        """Test converting empty records without field metadata."""
        ercot = ERCOT()
        df = ercot._response_to_dataframe([], [])

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert len(df.columns) == 0

    def test_records_with_fields(self, sample_records, sample_fields):
        """Test converting records with field metadata."""
        ercot = ERCOT()
        df = ercot._response_to_dataframe(sample_records, sample_fields)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5
        assert list(df.columns) == [
            "SCED Time Stamp",
            "Repeat Hour Flag",
            "Electrical Bus",
            "LMP",
        ]
        assert df["LMP"].iloc[0] == 25.50
        assert df["Electrical Bus"].iloc[0] == "BUS001"

    def test_records_without_fields(self, sample_records):
        """Test converting records without field metadata uses numeric columns."""
        ercot = ERCOT()
        df = ercot._response_to_dataframe(sample_records, [])

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5
        # Columns should be numeric indices
        assert list(df.columns) == [0, 1, 2, 3]

    def test_field_label_fallback_to_name(self):
        """Test that field name is used if label is missing."""
        ercot = ERCOT()
        fields = [
            {"name": "field1"},  # No label
            {"name": "field2", "label": "Field 2 Label"},
        ]
        records = [["value1", "value2"]]

        df = ercot._response_to_dataframe(records, fields)

        assert list(df.columns) == ["field1", "Field 2 Label"]

    def test_field_fallback_to_index(self):
        """Test that index is used if both name and label are missing."""
        ercot = ERCOT()
        fields = [
            {},  # No name or label
            {"label": "Has Label"},
        ]
        records = [["value1", "value2"]]

        df = ercot._response_to_dataframe(records, fields)

        assert list(df.columns) == ["0", "Has Label"]


class TestEndpointReturnsDataFrame:
    """Test that endpoint methods return DataFrames."""

    @patch("tinygrid.ercot.lmp_electrical_bus")
    def test_get_lmp_electrical_bus_returns_dataframe(
        self, mock_endpoint, sample_single_page_response
    ):
        """Test that get_lmp_electrical_bus returns a DataFrame."""
        mock_response = MagicMock()
        mock_response.to_dict.return_value = sample_single_page_response

        mock_endpoint.sync.return_value = mock_response

        ercot = ERCOT(retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        result = ercot.get_lmp_electrical_bus(sced_timestamp_from="2024-01-01")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5
        assert "SCED Time Stamp" in result.columns

    @patch("tinygrid.ercot.lf_by_model_weather_zone")
    def test_get_load_forecast_returns_dataframe(
        self, mock_endpoint, sample_single_page_response
    ):
        """Test that get_load_forecast_by_weather_zone returns a DataFrame."""
        mock_response = MagicMock()
        mock_response.to_dict.return_value = sample_single_page_response

        mock_endpoint.sync.return_value = mock_response

        ercot = ERCOT(retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        result = ercot.get_load_forecast_by_weather_zone(
            start_date="2024-01-01",
            end_date="2024-01-07",
        )

        assert isinstance(result, pd.DataFrame)

    @patch("tinygrid.ercot.dam_hourly_lmp")
    def test_get_dam_hourly_lmp_returns_dataframe(
        self, mock_endpoint, sample_single_page_response
    ):
        """Test that get_dam_hourly_lmp returns a DataFrame."""
        mock_response = MagicMock()
        mock_response.to_dict.return_value = sample_single_page_response

        mock_endpoint.sync.return_value = mock_response

        ercot = ERCOT(retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        result = ercot.get_dam_hourly_lmp(
            start_date="2024-01-01",
            end_date="2024-01-07",
        )

        assert isinstance(result, pd.DataFrame)


class TestDataFrameColumnLabels:
    """Test that DataFrame columns have proper labels."""

    @patch("tinygrid.ercot.lmp_electrical_bus")
    def test_columns_use_field_labels(
        self, mock_endpoint, sample_single_page_response
    ):
        """Test that DataFrame columns use field labels, not names."""
        mock_response = MagicMock()
        mock_response.to_dict.return_value = sample_single_page_response

        mock_endpoint.sync.return_value = mock_response

        ercot = ERCOT(retry_min_wait=0.01, retry_max_wait=0.1)
        ercot._client = MagicMock()

        result = ercot.get_lmp_electrical_bus()

        # Should use labels, not names
        assert "SCED Time Stamp" in result.columns
        assert "SCEDTimestamp" not in result.columns
        assert "Repeat Hour Flag" in result.columns
        assert "repeatHourFlag" not in result.columns
