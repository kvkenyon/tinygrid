"""ERCOT-specific constants, enums, and mappings."""

import sys
from enum import Enum

# StrEnum is only available in Python 3.11+
if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    # Backport for Python 3.10
    class StrEnum(str, Enum):
        """String enum for Python 3.10 compatibility."""

        def __new__(cls, value):
            if not isinstance(value, str):
                raise TypeError(f"{value!r} is not a string")
            obj = str.__new__(cls, value)
            obj._value_ = value
            return obj

        def __str__(self):
            return self._value_


# Timezone constants
ERCOT_TIMEZONE = "US/Central"

# Historical data threshold - use archive API for data older than this
HISTORICAL_THRESHOLD_DAYS = 90

# API endpoints
PUBLIC_API_BASE_URL = "https://api.ercot.com/api/public-reports"
ESR_API_BASE_URL = "https://api.ercot.com/api/public-data"


class Market(StrEnum):
    """ERCOT market types for price data."""

    REAL_TIME_SCED = "REAL_TIME_SCED"
    REAL_TIME_15_MIN = "REAL_TIME_15_MIN"
    DAY_AHEAD_HOURLY = "DAY_AHEAD_HOURLY"


class LocationType(StrEnum):
    """Types of settlement point locations in ERCOT."""

    LOAD_ZONE = "Load Zone"
    TRADING_HUB = "Trading Hub"
    RESOURCE_NODE = "Resource Node"
    ELECTRICAL_BUS = "Electrical Bus"


class SettlementPointType(StrEnum):
    """Settlement point type prefixes."""

    LZ = "LZ"  # Load Zone (LZ_HOUSTON, LZ_NORTH, etc.)
    HB = "HB"  # Trading Hub (HB_HOUSTON, HB_NORTH, etc.)
    RN = "RN"  # Resource Node


# ERCOT Load Zones
LOAD_ZONES = [
    "LZ_HOUSTON",
    "LZ_NORTH",
    "LZ_SOUTH",
    "LZ_WEST",
    "LZ_AEN",
    "LZ_CPS",
    "LZ_LCRA",
    "LZ_RAYBN",
]

# ERCOT Trading Hubs
TRADING_HUBS = [
    "HB_HOUSTON",
    "HB_NORTH",
    "HB_SOUTH",
    "HB_WEST",
    "HB_BUSAVG",
    "HB_HUBAVG",
    "HB_PAN",
]

# Endpoint mappings for unified methods
ENDPOINT_MAPPINGS = {
    # Settlement Point Prices
    "spp": {
        Market.REAL_TIME_15_MIN: "/np6-905-cd/spp_node_zone_hub",
        Market.DAY_AHEAD_HOURLY: "/np4-190-cd/dam_stlmnt_pnt_prices",
    },
    # Locational Marginal Prices
    "lmp": {
        Market.REAL_TIME_SCED: {
            LocationType.RESOURCE_NODE: "/np6-788-cd/lmp_node_zone_hub",
            LocationType.ELECTRICAL_BUS: "/np6-787-cd/lmp_electrical_bus",
        },
        Market.DAY_AHEAD_HOURLY: "/np4-183-cd/dam_hourly_lmp",
    },
    # Ancillary Services
    "as_prices": "/np4-188-cd/dam_clear_price_for_cap",
    "as_plan": "/np4-33-cd/dam_as_plan",
    # Shadow Prices
    "shadow_prices": {
        Market.DAY_AHEAD_HOURLY: "/np4-191-cd/dam_shadow_prices",
        Market.REAL_TIME_SCED: "/np6-86-cd/shdw_prices_bnd_trns_const",
    },
    # Wind/Solar
    "wind_forecast": "/np4-732-cd/wpp_hrly_avrg_actl_fcast",
    "wind_forecast_geo": "/np4-742-cd/wpp_hrly_actual_fcast_geo",
    "solar_forecast": "/np4-737-cd/spp_hrly_avrg_actl_fcast",
    "solar_forecast_geo": "/np4-745-cd/spp_hrly_actual_fcast_geo",
    # Indicative LMP
    "indicative_lmp": "/np6-970-cd/rtd_lmp_node_zone_hub",
    # Resource Outage
    "resource_outage": "/np3-233-cd/hourly_res_outage_cap",
}

# Days of data available on live API (before needing historical archive)
LIVE_API_RETENTION = {
    "real_time": 1,  # Real-time endpoints: today only
    "day_ahead": 2,  # DAM endpoints: ~2 days (today + tomorrow)
    "forecast": 3,  # Forecasts: ~3 days
    "load": 3,  # Load data: ~3 days
    "default": 1,  # Default: assume 1 day
}

# EMIL IDs for historical data archive
# Maps endpoint prefixes to their archive EMIL IDs
EMIL_IDS = {
    # Disclosure reports
    "as_reports_dam": "np3-911-er",
    "as_reports_sced": "np3-906-ex",
    "dam_disclosure": "np3-966-er",
    "sced_disclosure": "np3-965-er",
    # Real-time SPP/LMP
    "np6-905-cd": "np6-905-cd",  # Real-time SPP node/zone/hub
    "np6-788-cd": "np6-788-cd",  # Real-time LMP node/zone/hub
    "np6-787-cd": "np6-787-cd",  # Real-time LMP electrical bus
    "np6-970-cd": "np6-970-cd",  # RTD LMP node/zone/hub
    "np6-86-cd": "np6-86-cd",  # SCED shadow prices
    # DAM endpoints
    "np4-190-cd": "np4-190-cd",  # DAM SPP
    "np4-183-cd": "np4-183-cd",  # DAM LMP
    "np4-191-cd": "np4-191-cd",  # DAM shadow prices
    "np4-188-cd": "np4-188-cd",  # DAM AS MCPC prices
    "np4-33-cd": "np4-33-cd",  # DAM AS plan
    # Forecasts
    "np4-732-cd": "np4-732-cd",  # Wind forecast
    "np4-742-cd": "np4-742-cd",  # Wind forecast geo
    "np4-737-cd": "np4-737-cd",  # Solar forecast
    "np4-745-cd": "np4-745-cd",  # Solar forecast geo
    # Load
    "np6-345-cd": "np6-345-cd",  # Load by weather zone
    "np6-346-cd": "np6-346-cd",  # Load by forecast zone
}

# Column name mappings for standardization (raw API name -> user-friendly name)
COLUMN_MAPPINGS = {
    # Location columns
    "ElectricalBus": "Location",
    "SettlementPoint": "Location",
    "SettlementPointName": "Location",
    "Settlement Point": "Location",
    "Settlement Point Name": "Location",
    "SettlementPointType": "Location Type",
    "Settlement Point Type": "Location Type",
    # Price columns
    "SettlementPointPrice": "Price",
    "Settlement Point Price": "Price",
    "LMP": "Price",
    "ShadowPrice": "Shadow Price",
    "MaxShadowPrice": "Max Shadow Price",
    "SystemLambda": "System Lambda",
    # Time columns
    "SCEDTimestamp": "Timestamp",
    "SCED Timestamp": "Timestamp",
    "DeliveryDate": "Date",
    "Delivery Date": "Date",
    "DeliveryHour": "Hour",
    "Delivery Hour": "Hour",
    "DeliveryInterval": "Interval",
    "Delivery Interval": "Interval",
    "HourEnding": "Hour Ending",
    "Hour Ending": "Hour Ending",
    "PostedDatetime": "Posted Time",
    "Posted Datetime": "Posted Time",
    # Flag columns
    "DSTFlag": "DST",
    "DST Flag": "DST",
    "RepeatedHourFlag": "Repeated Hour",
    "Repeated Hour Flag": "Repeated Hour",
    # Constraint columns
    "ConstraintId": "Constraint ID",
    "ConstraintID": "Constraint ID",
    "ConstraintName": "Constraint Name",
    "ConstraintLimit": "Constraint Limit",
    "ConstraintValue": "Constraint Value",
    "ContingencyName": "Contingency Name",
    "ViolatedMW": "Violated MW",
    "ViolationAmount": "Violation Amount",
    "FromStation": "From Station",
    "FromStationkV": "From Station kV",
    "ToStation": "To Station",
    "ToStationkV": "To Station kV",
    "CCTStatus": "CCT Status",
    # Load columns
    "SystemTotal": "System Total",
    "Coast": "Coast",
    "East": "East",
    "FarWest": "Far West",
    "North": "North",
    "NorthCentral": "North Central",
    "SouthCentral": "South Central",
    "Southern": "Southern",
    "West": "West",
    # Forecast columns
    "HourEndingSystemWide": "System Wide",
    "HourEndingCOPHSL": "COP HSL",
    "HourEndingSTWPF": "STWPF",
    "HourEndingWGRPP": "WGRPP",
    "HourEndingSolar": "Solar",
    "GeoMagLatitude": "Latitude",
    "GeoMagLongitude": "Longitude",
}
