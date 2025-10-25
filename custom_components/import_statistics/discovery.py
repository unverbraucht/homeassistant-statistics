"""Discovery mechanism for fitness tracker devices."""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_NAME
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from custom_components.import_statistics.const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# In-memory storage for discovered fitness trackers
_DISCOVERED_TRACKERS: Dict[str, Dict[str, Any]] = {}


async def store_discovered_tracker(
    hass: HomeAssistant,
    component_name: str,
    vendor: str,
    device_info: Dict[str, Any],
    entities: List[Dict[str, Any]],
) -> None:
    """
    Store a discovered fitness tracker in memory.
    
    Args:
    ----
        hass: Home Assistant instance
        component_name: Unique identifier for the tracker
        vendor: Vendor name of the tracker
        device_info: Device information dictionary
        entities: List of entity configurations
    """
    tracker_data = {
        "component_name": component_name,
        "vendor": vendor,
        "device_info": device_info,
        "entities": entities,
        "discovered_at": datetime.now().isoformat(),
    }
    
    _DISCOVERED_TRACKERS[component_name] = tracker_data
    _LOGGER.info(f"Stored discovered fitness tracker: {component_name}")
    
    # Set a state to indicate discovery
    hass.states.async_set(
        f"import_statistics.{component_name}_discovered",
        "discovered",
        attributes={
            "component_name": component_name,
            "vendor": vendor,
            "entity_count": len(entities),
            "discovered_at": tracker_data["discovered_at"],
        },
    )


def get_discovered_tracker(component_name: str) -> Optional[Dict[str, Any]]:
    """
    Get a discovered fitness tracker by component name.
    
    Args:
    ----
        component_name: Unique identifier for the tracker
        
    Returns:
    -------
        Dictionary with tracker data or None if not found
    """
    return _DISCOVERED_TRACKERS.get(component_name)


def get_all_discovered_trackers() -> Dict[str, Dict[str, Any]]:
    """
    Get all discovered fitness trackers.
    
    Returns:
    -------
        Dictionary with all discovered trackers
    """
    return _DISCOVERED_TRACKERS.copy()


def remove_discovered_tracker(component_name: str) -> bool:
    """
    Remove a discovered fitness tracker.
    
    Args:
    ----
        component_name: Unique identifier for the tracker
        
    Returns:
    -------
        True if tracker was removed, False if not found
    """
    if component_name in _DISCOVERED_TRACKERS:
        del _DISCOVERED_TRACKERS[component_name]
        _LOGGER.info(f"Removed discovered fitness tracker: {component_name}")
        return True
    return False


def create_device_info(
    component_name: str,
    vendor: str,
    device_info: Dict[str, Any],
) -> DeviceInfo:
    """
    Create DeviceInfo for a fitness tracker.
    
    Args:
    ----
        component_name: Unique identifier for the tracker
        vendor: Vendor name of the tracker
        device_info: Device information dictionary
        
    Returns:
    -------
        DeviceInfo object
    """
    return DeviceInfo(
        name=vendor,
        identifiers={(DOMAIN, component_name)},
        manufacturer=device_info.get("manufacturer", vendor),
        model=device_info.get("model"),
        sw_version=device_info.get("sw_version"),
        hw_version=device_info.get("hw_version"),
        entry_type=DeviceEntryType.SERVICE,
    )