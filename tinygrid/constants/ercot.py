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

# Developer resources
DEVELOPER_PORTAL_URL = "https://developer.ercot.com"
API_EXPLORER_URL = "https://apiexplorer.ercot.com"
OPENAPI_SPECS_URL = "https://github.com/ercot/api-specs"

# ============================================================================
# API Data Availability - Important Limitations
# ============================================================================
#
# The ERCOT Public API has the following key limitations that users should
# be aware of when building applications:
#
# 1. API DATA START DATE: December 11, 2023
#    - The REST API only contains data from this date forward
#    - For earlier data, use MIS document downloads or the archive API
#    - Historical archives extend 7+ years back
#
# 2. DATA DELAY: Approximately 1 hour
#    - Real-time data is NOT truly real-time
#    - There is approximately a 1-hour delay from actual grid operations
#      to data availability in the API
#
# 3. GEOGRAPHIC RESTRICTION: US IP addresses only
#    - The API blocks requests from non-US IP addresses
#    - Users outside the US will need a VPN or US-based proxy
#
# 4. RATE LIMIT: 30 requests per minute
#    - Exceeding this limit results in HTTP 429 errors
#    - Use the built-in rate limiter (enabled by default)
#
# 5. FILE LIMIT: 1,000 documents per bulk download
#    - When using archive bulk downloads, max 1,000 files per request

# Date when ERCOT's Public API became available
API_LAUNCH_DATE = "2023-12-11"

# Approximate delay (in minutes) from real-time to API availability
API_DATA_DELAY_MINUTES = 60

# Maximum documents per bulk archive download
MAX_BULK_DOWNLOAD_FILES = 1000

# Rate limit (requests per minute)
API_RATE_LIMIT = 30

# ============================================================================
# RTC+B (Real-Time Co-optimization + Batteries) Changes
# ============================================================================
#
# RTC+B went live in December 2024 and includes:
#
# 1. ESR (Energy Storage Resource) Integration
#    - Batteries can now participate in energy and AS markets
#    - New resource type: ESR
#    - Bidirectional dispatch (charge/discharge)
#    - State of Charge (SOC) constraints
#
# 2. Real-Time AS Co-optimization
#    - AS is now procured in real-time alongside energy
#    - New price signals: RT SCED Price Adders, RT 15-min Price Adders
#    - Replaced legacy ORDC-based price adders
#
# 3. New Data Fields
#    - ESR-specific capacity and award columns in disclosure reports
#    - New HDL/LDL fields for ESR base point adjustments
#    - New MCPC fields for RT AS clearing prices
#
# Legacy Endpoint Support:
# - All existing REST API endpoints continue to work
# - Data returned may include new ESR-related columns
# - SASM (Supplemental AS Market) fields deprecated in EWS
#
# For more information:
# - ERCOT Technical Reference: https://www.ercot.com/mktrules/guides
# - API Specs: https://github.com/ercot/api-specs

# Date when RTC+B went live
RTC_B_LAUNCH_DATE = "2024-12-04"

# Date when ESR integration was enabled
ESR_INTEGRATION_DATE = "2024-06-01"


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


class ResourceType(StrEnum):
    """ERCOT resource types.

    RTC+B (Real-Time Co-optimization + Batteries) introduced ESR as a new
    resource type in December 2024. ESRs can provide both energy and
    ancillary services with bidirectional dispatch (charge/discharge).
    """

    # Generation Resources
    GEN = "GEN"  # Generation Resource
    WGR = "WGR"  # Wind Generation Resource
    PVGR = "PVGR"  # Photovoltaic (Solar) Generation Resource
    SMNE = "SMNE"  # Small Non-Exempt Generation Resource

    # Load Resources
    CLR = "CLR"  # Controllable Load Resource
    LR = "LR"  # Load Resource
    DSR = "DSR"  # Demand Side Response Resource

    # Energy Storage Resources (RTC+B)
    ESR = "ESR"  # Energy Storage Resource (batteries, added in RTC+B)
    DESR = "DESR"  # Distributed Energy Storage Resource
    DGR = "DGR"  # Distributed Generation Resource


class AncillaryServiceType(StrEnum):
    """ERCOT Ancillary Service types.

    RTC+B modified how these services are procured in real-time with
    co-optimization of energy and AS. ESRs can now provide most AS types.
    """

    # Regulation Services
    REGUP = "REGUP"  # Regulation Up
    REGDN = "REGDN"  # Regulation Down

    # Responsive Reserve Services (RRS)
    RRSPFR = "RRSPFR"  # Responsive Reserve - Primary Frequency Response
    RRSFFR = "RRSFFR"  # Responsive Reserve - Fast Frequency Response
    RRSUFR = "RRSUFR"  # Responsive Reserve - Ultra-Fast Frequency Response

    # Non-Spinning Reserve
    NSPIN = "NSPIN"  # Non-Spinning Reserve (Online)
    NSPNM = "NSPNM"  # Non-Spinning Reserve (Non-Market)
    ONNS = "ONNS"  # Online Non-Spinning Reserve
    OFFNS = "OFFNS"  # Offline Non-Spinning Reserve

    # Emergency Contingency Reserve Service (ECRS)
    ECRSM = "ECRSM"  # ECRS - Slow (10-minute)
    ECRSS = "ECRSS"  # ECRS - Super Slow (30-minute)


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
    "np4-732-cd": "np4-732-cd",  # Wind forecast hourly
    "np4-733-cd": "np4-733-cd",  # Wind 5-minute averaged
    "np4-742-cd": "np4-742-cd",  # Wind forecast geo hourly
    "np4-743-cd": "np4-743-cd",  # Wind 5-minute geo
    "np4-737-cd": "np4-737-cd",  # Solar forecast hourly
    "np4-738-cd": "np4-738-cd",  # Solar 5-minute averaged
    "np4-745-cd": "np4-745-cd",  # Solar forecast geo hourly
    "np4-746-cd": "np4-746-cd",  # Solar 5-minute geo
    # Load
    "np6-345-cd": "np6-345-cd",  # Load by weather zone
    "np6-346-cd": "np6-346-cd",  # Load by forecast zone
    # System-wide / Transmission
    "np6-625-cd": "np6-625-cd",  # Total ERCOT generation
    "np6-626-cd": "np6-626-cd",  # DC tie flows
    "np6-235-cd": "np6-235-cd",  # System-wide actuals
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
