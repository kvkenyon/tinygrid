
import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from tinygrid.ercot.api import ERCOTAPIMixin
from tinygrid.constants.ercot import Market, LocationType
from tinygrid.errors import GridError

class TestERCOTAPIMixin(ERCOTAPIMixin):
    def __init__(self):
        self._archive_mock = MagicMock()
        self._needs_historical_mock = MagicMock(return_value=False)
        
    def _get_archive(self):
        return self._archive_mock
        
    def _needs_historical(self, date, data_type="real_time"):
        return self._needs_historical_mock(date, data_type)
        
    # Mock endpoint methods
    get_spp_node_zone_hub = MagicMock(return_value=pd.DataFrame())
    get_dam_settlement_point_prices = MagicMock(return_value=pd.DataFrame())
    get_lmp_electrical_bus = MagicMock(return_value=pd.DataFrame())
    get_lmp_node_zone_hub = MagicMock(return_value=pd.DataFrame())
    get_dam_hourly_lmp = MagicMock(return_value=pd.DataFrame())
    get_dam_clear_price_for_cap = MagicMock(return_value=pd.DataFrame())
    get_dam_as_plan = MagicMock(return_value=pd.DataFrame())
    get_dam_shadow_prices = MagicMock(return_value=pd.DataFrame())
    get_shadow_prices_bound_transmission_constraint = MagicMock(return_value=pd.DataFrame())
    get_actual_system_load_by_forecast_zone = MagicMock(return_value=pd.DataFrame())
    get_actual_system_load_by_weather_zone = MagicMock(return_value=pd.DataFrame())
    get_wpp_hourly_actual_forecast_geo = MagicMock(return_value=pd.DataFrame())
    get_wpp_hourly_average_actual_forecast = MagicMock(return_value=pd.DataFrame())
    get_spp_hourly_actual_forecast_geo = MagicMock(return_value=pd.DataFrame())
    get_spp_hourly_average_actual_forecast = MagicMock(return_value=pd.DataFrame())

class TestAPICoverage:
    
    def test_get_spp_historical(self):
        mixin = TestERCOTAPIMixin()
        mixin._needs_historical_mock.return_value = True
        mixin._archive_mock.fetch_historical.return_value = pd.DataFrame({"Date": ["2020-01-01"]})
        
        # Test Real Time Historical
        df = mixin.get_spp(start="2020-01-01", market=Market.REAL_TIME_15_MIN)
        assert mixin._archive_mock.fetch_historical.called
        assert mixin._archive_mock.fetch_historical.call_args[1]["endpoint"] == "/np6-905-cd/spp_node_zone_hub"
        
        # Test Day Ahead Historical
        mixin.get_spp(start="2020-01-01", market=Market.DAY_AHEAD_HOURLY)
        assert mixin._archive_mock.fetch_historical.call_args[1]["endpoint"] == "/np4-190-cd/dam_stlmnt_pnt_prices"
        
    def test_get_spp_invalid_market(self):
        mixin = TestERCOTAPIMixin()
        with pytest.raises(ValueError, match="Unsupported market"):
            mixin.get_spp(market=Market.REAL_TIME_SCED) # SCED not supported for SPP

    def test_get_lmp_historical(self):
        mixin = TestERCOTAPIMixin()
        mixin._needs_historical_mock.return_value = True
        mixin._archive_mock.fetch_historical.return_value = pd.DataFrame()
        
        # RT SCED - Electrical Bus
        mixin.get_lmp(market=Market.REAL_TIME_SCED, location_type=LocationType.ELECTRICAL_BUS)
        assert mixin._archive_mock.fetch_historical.call_args[1]["endpoint"] == "/np6-787-cd/lmp_electrical_bus"
        
        # RT SCED - Node/Zone/Hub
        mixin.get_lmp(market=Market.REAL_TIME_SCED, location_type=LocationType.RESOURCE_NODE)
        assert mixin._archive_mock.fetch_historical.call_args[1]["endpoint"] == "/np6-788-cd/lmp_node_zone_hub"
        
        # DAM
        mixin.get_lmp(market=Market.DAY_AHEAD_HOURLY)
        assert mixin._archive_mock.fetch_historical.call_args[1]["endpoint"] == "/np4-183-cd/dam_hourly_lmp"

    def test_get_lmp_invalid_market(self):
        mixin = TestERCOTAPIMixin()
        with pytest.raises(ValueError, match="Unsupported market"):
            mixin.get_lmp(market=Market.REAL_TIME_15_MIN)

    def test_get_as_prices_historical(self):
        mixin = TestERCOTAPIMixin()
        mixin._needs_historical_mock.return_value = True
        mixin._archive_mock.fetch_historical.return_value = pd.DataFrame()
        
        mixin.get_as_prices(start="2020-01-01")
        assert mixin._archive_mock.fetch_historical.called

    def test_get_as_plan_historical(self):
        mixin = TestERCOTAPIMixin()
        mixin._needs_historical_mock.return_value = True
        mixin._archive_mock.fetch_historical.return_value = pd.DataFrame()
        
        mixin.get_as_plan(start="2020-01-01")
        assert mixin._archive_mock.fetch_historical.called

    def test_get_shadow_prices_historical(self):
        mixin = TestERCOTAPIMixin()
        mixin._needs_historical_mock.return_value = True
        mixin._archive_mock.fetch_historical.return_value = pd.DataFrame()
        
        # DAM
        mixin.get_shadow_prices(market=Market.DAY_AHEAD_HOURLY)
        assert mixin._archive_mock.fetch_historical.call_args[1]["endpoint"] == "/np4-191-cd/dam_shadow_prices"
        
        # RT
        mixin.get_shadow_prices(market=Market.REAL_TIME_SCED)
        assert mixin._archive_mock.fetch_historical.call_args[1]["endpoint"] == "/np6-86-cd/shdw_prices_bnd_trns_const"

    def test_get_load_historical(self):
        mixin = TestERCOTAPIMixin()
        mixin._needs_historical_mock.return_value = True
        mixin._archive_mock.fetch_historical.return_value = pd.DataFrame()
        
        # Forecast Zone
        mixin.get_load(by="forecast_zone")
        assert mixin._archive_mock.fetch_historical.call_args[1]["endpoint"] == "/np6-346-cd/act_sys_load_by_fzn"
        
        # Weather Zone
        mixin.get_load(by="weather_zone")
        assert mixin._archive_mock.fetch_historical.call_args[1]["endpoint"] == "/np6-345-cd/act_sys_load_by_wzn"

    def test_get_wind_forecast_historical(self):
        mixin = TestERCOTAPIMixin()
        mixin._needs_historical_mock.return_value = True
        mixin._archive_mock.fetch_historical.return_value = pd.DataFrame()
        
        # By Region
        mixin.get_wind_forecast(by_region=True)
        assert mixin._archive_mock.fetch_historical.call_args[1]["endpoint"] == "/np4-742-cd/wpp_hrly_actual_fcast_geo"
        
        # System
        mixin.get_wind_forecast(by_region=False)
        assert mixin._archive_mock.fetch_historical.call_args[1]["endpoint"] == "/np4-732-cd/wpp_hrly_avrg_actl_fcast"

    def test_get_solar_forecast_historical(self):
        mixin = TestERCOTAPIMixin()
        mixin._needs_historical_mock.return_value = True
        mixin._archive_mock.fetch_historical.return_value = pd.DataFrame()
        
        # By Region
        mixin.get_solar_forecast(by_region=True)
        assert mixin._archive_mock.fetch_historical.call_args[1]["endpoint"] == "/np4-745-cd/spp_hrly_actual_fcast_geo"
        
        # System
        mixin.get_solar_forecast(by_region=False)
        assert mixin._archive_mock.fetch_historical.call_args[1]["endpoint"] == "/np4-737-cd/spp_hrly_avrg_actl_fcast"
