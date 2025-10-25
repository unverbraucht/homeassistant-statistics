"""Unit tests for fitness component discovery functions."""

import pytest
from homeassistant.core import ServiceCall
from homeassistant.exceptions import HomeAssistantError

from custom_components.import_statistics import fitness_component
from custom_components.import_statistics.discovery import (
    get_discovered_tracker,
    get_all_discovered_trackers,
    _DISCOVERED_TRACKERS,
)


@pytest.fixture(autouse=True)
def clear_discovered_trackers():
    """Clear discovered trackers before each test."""
    _DISCOVERED_TRACKERS.clear()


@pytest.mark.asyncio
async def test_discover_fitness_component_success(hass) -> None:
    """Test successful discovery of fitness component."""
    test_data = {
        "component_name": "my_fitness_tracker",
        "vendor": "Generic Fitness Tracker",
        "device_info": {
            "model": "FT-1000",
            "manufacturer": "Fitness Corp",
            "sw_version": "1.0.0",
            "hw_version": "2.0",
        },
        "entities": [
            {
                "name": "daily_steps",
                "friendly_name": "Daily Steps",
                "state_class": "total_increasing",
                "icon": "mdi:foot-print",
            },
            {
                "name": "heart_rate",
                "friendly_name": "Heart Rate",
                "state_class": "measurement",
                "icon": "mdi:heart-pulse",
            },
        ],
    }
    
    call = ServiceCall("import_statistics", "create_fitness_component", test_data, test_data)
    
    # This should not raise an exception
    await fitness_component.discover_fitness_component(hass, call)
    
    # Check that the discovery state is set
    state = hass.states.get("import_statistics.my_fitness_tracker_discovered")
    assert state is not None
    assert state.state == "True"
    assert state.attributes["component_name"] == "my_fitness_tracker"
    assert state.attributes["vendor"] == "Generic Fitness Tracker"
    assert state.attributes["entity_count"] == 2
    assert "discovered_at" in state.attributes
    
    # Check that the tracker is stored in discovery
    tracker = get_discovered_tracker("my_fitness_tracker")
    assert tracker is not None
    assert tracker["component_name"] == "my_fitness_tracker"
    assert tracker["vendor"] == "Generic Fitness Tracker"
    assert len(tracker["entities"]) == 2


@pytest.mark.asyncio
async def test_discover_fitness_component_missing_component_name(hass) -> None:
    """Test error when component_name is missing."""
    test_data = {
        "vendor": "Generic Fitness Tracker",
        "entities": [
            {
                "name": "daily_steps",
                "friendly_name": "Daily Steps",
            },
        ],
    }
    
    call = ServiceCall("import_statistics", "create_fitness_component", test_data, test_data)
    
    with pytest.raises(HomeAssistantError, match="component_name is required"):
        await fitness_component.discover_fitness_component(hass, call)


@pytest.mark.asyncio
async def test_discover_fitness_component_missing_vendor(hass) -> None:
    """Test error when vendor is missing."""
    test_data = {
        "component_name": "my_fitness_tracker",
        "entities": [
            {
                "name": "daily_steps",
                "friendly_name": "Daily Steps",
            },
        ],
    }
    
    call = ServiceCall("import_statistics", "create_fitness_component", test_data, test_data)
    
    with pytest.raises(HomeAssistantError, match="vendor is required"):
        await fitness_component.discover_fitness_component(hass, call)


@pytest.mark.asyncio
async def test_discover_fitness_component_missing_entities(hass) -> None:
    """Test error when entities list is empty."""
    test_data = {
        "component_name": "my_fitness_tracker",
        "vendor": "Generic Fitness Tracker",
        "entities": [],
    }
    
    call = ServiceCall("import_statistics", "create_fitness_component", test_data, test_data)
    
    with pytest.raises(HomeAssistantError, match="at least one entity must be specified"):
        await fitness_component.discover_fitness_component(hass, call)


@pytest.mark.asyncio
async def test_discover_fitness_component_invalid_component_name(hass) -> None:
    """Test error when component_name contains invalid characters."""
    test_data = {
        "component_name": "my-fitness-tracker",  # Contains hyphen which is invalid
        "vendor": "Generic Fitness Tracker",
        "entities": [
            {
                "name": "daily_steps",
                "friendly_name": "Daily Steps",
            },
        ],
    }
    
    call = ServiceCall("import_statistics", "create_fitness_component", test_data, test_data)
    
    with pytest.raises(HomeAssistantError, match="Invalid component_name"):
        await fitness_component.discover_fitness_component(hass, call)


@pytest.mark.asyncio
async def test_discover_fitness_component_missing_entity_name(hass) -> None:
    """Test error when entity name is missing."""
    test_data = {
        "component_name": "my_fitness_tracker",
        "vendor": "Generic Fitness Tracker",
        "entities": [
            {
                "friendly_name": "Daily Steps",
            },
        ],
    }
    
    call = ServiceCall("import_statistics", "create_fitness_component", test_data, test_data)
    
    with pytest.raises(HomeAssistantError, match="entity name is required"):
        await fitness_component.discover_fitness_component(hass, call)


@pytest.mark.asyncio
async def test_discover_fitness_component_missing_entity_friendly_name(hass) -> None:
    """Test error when entity friendly_name is missing."""
    test_data = {
        "component_name": "my_fitness_tracker",
        "vendor": "Generic Fitness Tracker",
        "entities": [
            {
                "name": "daily_steps",
            },
        ],
    }
    
    call = ServiceCall("import_statistics", "create_fitness_component", test_data, test_data)
    
    with pytest.raises(HomeAssistantError, match="entity friendly_name is required"):
        await fitness_component.discover_fitness_component(hass, call)


@pytest.mark.asyncio
async def test_discover_fitness_component_invalid_entity_name(hass) -> None:
    """Test error when entity name contains invalid characters."""
    test_data = {
        "component_name": "my_fitness_tracker",
        "vendor": "Generic Fitness Tracker",
        "entities": [
            {
                "name": "daily-steps",  # Contains hyphen which is invalid
                "friendly_name": "Daily Steps",
            },
        ],
    }
    
    call = ServiceCall("import_statistics", "create_fitness_component", test_data, test_data)
    
    with pytest.raises(HomeAssistantError, match="Invalid entity name"):
        await fitness_component.discover_fitness_component(hass, call)


@pytest.mark.asyncio
async def test_discover_fitness_component_minimal_config(hass) -> None:
    """Test discovery with minimal configuration."""
    test_data = {
        "component_name": "minimal_tracker",
        "vendor": "Minimal Tracker",
        "entities": [
            {
                "name": "steps",
                "friendly_name": "Steps",
            },
        ],
    }
    
    call = ServiceCall("import_statistics", "create_fitness_component", test_data, test_data)
    
    # This should not raise an exception
    await fitness_component.discover_fitness_component(hass, call)
    
    # Check that the discovery state is set
    state = hass.states.get("import_statistics.minimal_tracker_discovered")
    assert state is not None
    assert state.state == "True"
    assert state.attributes["component_name"] == "minimal_tracker"
    assert state.attributes["vendor"] == "Minimal Tracker"
    assert state.attributes["entity_count"] == 1
    
    # Check that the tracker is stored in discovery
    tracker = get_discovered_tracker("minimal_tracker")
    assert tracker is not None
    assert tracker["component_name"] == "minimal_tracker"
    assert tracker["vendor"] == "Minimal Tracker"
    assert len(tracker["entities"]) == 1


@pytest.mark.asyncio
async def test_discover_fitness_component_with_device_info(hass) -> None:
    """Test discovery with device info."""
    test_data = {
        "component_name": "device_tracker",
        "vendor": "Device Vendor",
        "device_info": {
            "model": "DT-2000",
            "manufacturer": "Device Corp",
            "sw_version": "2.1.0",
            "hw_version": "3.0",
        },
        "entities": [
            {
                "name": "battery",
                "friendly_name": "Battery Level",
                "unit_of_measurement": "%",
                "device_class": "battery",
                "state_class": "measurement",
                "icon": "mdi:battery",
            },
        ],
    }
    
    call = ServiceCall("import_statistics", "create_fitness_component", test_data, test_data)
    
    # This should not raise an exception
    await fitness_component.discover_fitness_component(hass, call)
    
    # Check that the discovery state is set
    state = hass.states.get("import_statistics.device_tracker_discovered")
    assert state is not None
    assert state.state == "True"
    assert state.attributes["component_name"] == "device_tracker"
    assert state.attributes["vendor"] == "Device Vendor"
    assert state.attributes["entity_count"] == 1
    
    # Check that the tracker is stored in discovery
    tracker = get_discovered_tracker("device_tracker")
    assert tracker is not None
    assert tracker["component_name"] == "device_tracker"
    assert tracker["vendor"] == "Device Vendor"
    assert len(tracker["entities"]) == 1
    assert tracker["device_info"]["model"] == "DT-2000"


@pytest.mark.asyncio
async def test_discover_multiple_fitness_components(hass) -> None:
    """Test discovering multiple fitness components."""
    # Discover first tracker
    test_data1 = {
        "component_name": "tracker1",
        "vendor": "Vendor 1",
        "entities": [
            {
                "name": "steps",
                "friendly_name": "Steps",
            },
        ],
    }
    
    call1 = ServiceCall("import_statistics", "create_fitness_component", test_data1, test_data1)
    await fitness_component.discover_fitness_component(hass, call1)
    
    # Discover second tracker
    test_data2 = {
        "component_name": "tracker2",
        "vendor": "Vendor 2",
        "entities": [
            {
                "name": "heart_rate",
                "friendly_name": "Heart Rate",
            },
        ],
    }
    
    call2 = ServiceCall("import_statistics", "create_fitness_component", test_data2, test_data2)
    await fitness_component.discover_fitness_component(hass, call2)
    
    # Check both trackers are discovered
    all_trackers = get_all_discovered_trackers()
    assert len(all_trackers) == 2
    assert "tracker1" in all_trackers
    assert "tracker2" in all_trackers
    
    # Check discovery states
    state1 = hass.states.get("import_statistics.tracker1_discovered")
    assert state1 is not None
    assert state1.attributes["vendor"] == "Vendor 1"
    
    state2 = hass.states.get("import_statistics.tracker2_discovered")
    assert state2 is not None
    assert state2.attributes["vendor"] == "Vendor 2"