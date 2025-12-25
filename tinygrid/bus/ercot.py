"""ERCOT Electrical Buses and Hub Mappings"""

import csv
from pathlib import Path

# Path to the CSV file
_CSV_PATH = Path(__file__).parent / "ercot_electrical_bus_to_hub_map.csv"


def _load_bus_mapping_data() -> dict:
    """Load bus mapping data from CSV file."""
    data = {
        "electrical_buses": [],
        "hub_bus_names": [],
        "hubs": [],
        "electrical_bus_to_hub_bus": {},
        "electrical_bus_to_hub": {},
        "hub_bus_to_electrical_buses": {},
        "hub_to_electrical_buses": {},
        "hub_to_hub_bus_names": {},
        "hub_bus_to_hub": {},
    }

    if not _CSV_PATH.exists():
        return data

    with open(_CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=",")
        for row in reader:
            electrical_bus = row["ELECTRICAL_BUS"].strip()
            hub_bus_name = row["HUB_BUS_NAME"].strip()
            hub = row["HUB"].strip()

            if not electrical_bus:  # Skip empty rows
                continue

            # Add to lists (will deduplicate later)
            data["electrical_buses"].append(electrical_bus)
            data["hub_bus_names"].append(hub_bus_name)
            data["hubs"].append(hub)

            # Create mappings
            data["electrical_bus_to_hub_bus"][electrical_bus] = hub_bus_name
            data["electrical_bus_to_hub"][electrical_bus] = hub
            data["hub_bus_to_hub"][hub_bus_name] = hub

            # Reverse mappings (many-to-one)
            if hub_bus_name not in data["hub_bus_to_electrical_buses"]:
                data["hub_bus_to_electrical_buses"][hub_bus_name] = []
            data["hub_bus_to_electrical_buses"][hub_bus_name].append(electrical_bus)

            if hub not in data["hub_to_electrical_buses"]:
                data["hub_to_electrical_buses"][hub] = []
            data["hub_to_electrical_buses"][hub].append(electrical_bus)

            if hub not in data["hub_to_hub_bus_names"]:
                data["hub_to_hub_bus_names"][hub] = set()
            data["hub_to_hub_bus_names"][hub].add(hub_bus_name)

    # Convert lists to sorted unique lists
    data["electrical_buses"] = sorted(set(data["electrical_buses"]))
    data["hub_bus_names"] = sorted(set(data["hub_bus_names"]))
    data["hubs"] = sorted(set(data["hubs"]))

    # Convert sets to sorted lists in hub_to_hub_bus_names
    data["hub_to_hub_bus_names"] = {
        hub: sorted(hub_bus_names) for hub, hub_bus_names in data["hub_to_hub_bus_names"].items()
    }

    return data


# Load data at module level
_BUS_MAPPING_DATA = _load_bus_mapping_data()


# Public API: Lists
ELECTRICAL_BUSES: list[str] = _BUS_MAPPING_DATA["electrical_buses"]
"""List of all electrical bus names (e.g., 'ADICKS_345B', 'CBY_5025').
Useful for functions that require electrical_bus parameter."""

HUB_BUS_NAMES: list[str] = _BUS_MAPPING_DATA["hub_bus_names"]
"""List of all hub bus names (e.g., 'ADK', 'CBY', 'BI').
Useful for functions that require hub_bus_name parameter."""

HUBS: list[str] = _BUS_MAPPING_DATA["hubs"]
"""List of all hub names (e.g., 'HB_HOUSTON', 'HB_NORTH', 'HB_SOUTH').
Useful for functions that require hub or settlement_point parameter."""

# Public API: Mappings
ELECTRICAL_BUS_TO_HUB_BUS: dict[str, str] = _BUS_MAPPING_DATA["electrical_bus_to_hub_bus"]
"""Map electrical bus name -> hub bus name.
Example: 'ADICKS_345B' -> 'ADK'"""

ELECTRICAL_BUS_TO_HUB: dict[str, str] = _BUS_MAPPING_DATA["electrical_bus_to_hub"]
"""Map electrical bus name -> hub name.
Example: 'ADICKS_345B' -> 'HB_HOUSTON'"""

HUB_BUS_TO_ELECTRICAL_BUSES: dict[str, list[str]] = _BUS_MAPPING_DATA["hub_bus_to_electrical_buses"]
"""Map hub bus name -> list of electrical bus names.
Example: 'ADK' -> ['ADICKS_345B', 'ADICKS__345D']"""

HUB_TO_ELECTRICAL_BUSES: dict[str, list[str]] = _BUS_MAPPING_DATA["hub_to_electrical_buses"]
"""Map hub name -> list of electrical bus names.
Example: 'HB_HOUSTON' -> ['ADICKS_345B', 'ADICKS__345D', ...]"""

HUB_TO_HUB_BUS_NAMES: dict[str, list[str]] = _BUS_MAPPING_DATA["hub_to_hub_bus_names"]
"""Map hub name -> list of hub bus names.
Example: 'HB_HOUSTON' -> ['ADK', 'BI', 'CBY', ...]"""

HUB_BUS_TO_HUB: dict[str, str] = _BUS_MAPPING_DATA["hub_bus_to_hub"]
"""Map hub bus name -> hub name.
Example: 'ADK' -> 'HB_HOUSTON'"""


# Convenience functions
def get_electrical_buses_for_hub(hub: str) -> list[str]:
    """Get all electrical bus names for a given hub.

    Args:
        hub: Hub name (e.g., 'HB_HOUSTON')

    Returns:
        List of electrical bus names

    Example:
        >>> buses = get_electrical_buses_for_hub('HB_HOUSTON')
        >>> 'ADICKS_345B' in buses
        True
    """
    return HUB_TO_ELECTRICAL_BUSES.get(hub, [])


def get_hub_bus_names_for_hub(hub: str) -> list[str]:
    """Get all hub bus names for a given hub.

    Args:
        hub: Hub name (e.g., 'HB_HOUSTON')

    Returns:
        List of hub bus names

    Example:
        >>> hub_buses = get_hub_bus_names_for_hub('HB_HOUSTON')
        >>> 'ADK' in hub_buses
        True
    """
    return HUB_TO_HUB_BUS_NAMES.get(hub, [])


def get_hub_for_electrical_bus(electrical_bus: str) -> str:
    """Get the hub name for a given electrical bus.

    Args:
        electrical_bus: Electrical bus name (e.g., 'ADICKS_345B')

    Returns:
        Hub name (e.g., 'HB_HOUSTON')

    Example:
        >>> hub = get_hub_for_electrical_bus('ADICKS_345B')
        >>> hub == 'HB_HOUSTON'
        True
    """
    return ELECTRICAL_BUS_TO_HUB.get(electrical_bus, "")


def get_hub_bus_for_electrical_bus(electrical_bus: str) -> str:
    """Get the hub bus name for a given electrical bus.

    Args:
        electrical_bus: Electrical bus name (e.g., 'ADICKS_345B')

    Returns:
        Hub bus name (e.g., 'ADK')

    Example:
        >>> hub_bus = get_hub_bus_for_electrical_bus('ADICKS_345B')
        >>> hub_bus == 'ADK'
        True
    """
    return ELECTRICAL_BUS_TO_HUB_BUS.get(electrical_bus, "")


def get_electrical_buses_for_hub_bus(hub_bus_name: str) -> list[str]:
    """Get all electrical bus names for a given hub bus name.

    Args:
        hub_bus_name: Hub bus name (e.g., 'ADK')

    Returns:
        List of electrical bus names

    Example:
        >>> buses = get_electrical_buses_for_hub_bus('ADK')
        >>> 'ADICKS_345B' in buses
        True
    """
    return HUB_BUS_TO_ELECTRICAL_BUSES.get(hub_bus_name, [])
