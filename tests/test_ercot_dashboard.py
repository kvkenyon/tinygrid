"""Tests for tinygrid.ercot.dashboard module."""

from __future__ import annotations

import pandas as pd
import pytest

from tinygrid.ercot.dashboard import (
    ERCOTDashboardMixin,
    GridCondition,
    GridStatus,
)


class TestGridCondition:
    """Tests for GridCondition enum."""

    def test_normal_condition(self):
        """Test normal condition value."""
        assert GridCondition.NORMAL.value == "normal"

    def test_conservation_condition(self):
        """Test conservation condition value."""
        assert GridCondition.CONSERVATION.value == "conservation"

    def test_watch_condition(self):
        """Test watch condition value."""
        assert GridCondition.WATCH.value == "watch"

    def test_emergency_condition(self):
        """Test emergency condition value."""
        assert GridCondition.EMERGENCY.value == "emergency"

    def test_unknown_condition(self):
        """Test unknown condition value."""
        assert GridCondition.UNKNOWN.value == "unknown"


class TestGridStatus:
    """Tests for GridStatus dataclass."""

    def test_create_grid_status(self):
        """Test creating GridStatus instance."""
        ts = pd.Timestamp.now(tz="US/Central")
        status = GridStatus(
            condition=GridCondition.NORMAL,
            current_frequency=60.0,
            current_load=50000.0,
            capacity=70000.0,
            reserves=20000.0,
            timestamp=ts,
        )
        assert status.condition == GridCondition.NORMAL
        assert status.current_frequency == 60.0
        assert status.current_load == 50000.0

    def test_grid_status_with_message(self):
        """Test GridStatus with message."""
        status = GridStatus(
            condition=GridCondition.WATCH,
            current_frequency=59.95,
            current_load=60000.0,
            capacity=65000.0,
            reserves=5000.0,
            timestamp=pd.Timestamp.now(tz="US/Central"),
            message="Conservation appeal in effect",
        )
        assert status.message == "Conservation appeal in effect"

    def test_unavailable_factory(self):
        """Test unavailable class method."""
        status = GridStatus.unavailable()
        assert status.condition == GridCondition.UNKNOWN
        assert status.current_frequency == 0.0
        assert status.current_load == 0.0
        assert "not available" in status.message


class TestERCOTDashboardMixin:
    """Tests for ERCOTDashboardMixin class."""

    @pytest.fixture
    def mixin_instance(self):
        """Create a test instance with the mixin."""

        class TestClass(ERCOTDashboardMixin):
            pass

        return TestClass()

    def test_get_status_returns_unavailable(self, mixin_instance):
        """Test get_status returns unavailable GridStatus."""
        status = mixin_instance.get_status()
        assert isinstance(status, GridStatus)
        assert status.condition == GridCondition.UNKNOWN
        assert "not available" in status.message

    def test_get_fuel_mix_returns_empty(self, mixin_instance):
        """Test get_fuel_mix returns empty DataFrame."""
        df = mixin_instance.get_fuel_mix()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_get_fuel_mix_with_date_param(self, mixin_instance):
        """Test get_fuel_mix accepts date parameter."""
        df = mixin_instance.get_fuel_mix(date="yesterday")
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_get_energy_storage_resources_returns_empty(self, mixin_instance):
        """Test get_energy_storage_resources returns empty DataFrame."""
        df = mixin_instance.get_energy_storage_resources()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_get_system_wide_demand_returns_empty(self, mixin_instance):
        """Test get_system_wide_demand returns empty DataFrame."""
        df = mixin_instance.get_system_wide_demand()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_get_renewable_generation_returns_empty(self, mixin_instance):
        """Test get_renewable_generation returns empty DataFrame."""
        df = mixin_instance.get_renewable_generation()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_get_capacity_committed_returns_empty(self, mixin_instance):
        """Test get_capacity_committed returns empty DataFrame."""
        df = mixin_instance.get_capacity_committed()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_get_capacity_forecast_returns_empty(self, mixin_instance):
        """Test get_capacity_forecast returns empty DataFrame."""
        df = mixin_instance.get_capacity_forecast()
        assert isinstance(df, pd.DataFrame)
        assert df.empty
