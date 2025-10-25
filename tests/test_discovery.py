"""Unit tests for discovery functions."""

import pytest
from datetime import datetime

from homeassistant.core import HomeAssistant

from custom_components.import_statistics.discovery import (
    store_discovered_tracker,
    get_discovered_tracker,
    get_all_discovered_trackers,
    remove_discovered_tracker,
    create_device_info,
    _DISCOVERED_TRACKERS,
)


@pytest.fixture(autouse=True)
def clear_discovered_trackers():
    """Clear discovered trackers before each test."""
    _DISCOVERED_TRACKERS.clear()


def test_store_and_get_discovered_tracker(hass: HomeAssistant) -> None:
    """Test storing and retrieving a discovered tracker."""
    component_name = "test_tracker"
    vendor = "Test Vendor"
    device_info = {
        "model": "TT-1000",
        "manufacturer": "Test Corp",
        "sw_version": "1.0.0",
        "hw_version": "2.0",
    }
    entities = [
        {
            "name": "steps",
            "friendly_name": "Steps",
            "state_class": "total_increasing",
        },
        {
            "name": "heart_rate",
            "friendly_name": "Heart Rate",
            "state_class": "measurement",
        },
    ]
    
    # Store the tracker
    store_discovered_tracker(hass, component_name, vendor, device_info, entities)
    
    # Retrieve the tracker
    tracker = get_discovered_tracker(component_name)
    assert tracker is not None
    assert tracker["component_name"] == component_name
    assert tracker["vendor"] == vendor
    assert tracker["device_info"] == device_info
    assert tracker["entities"] == entities
    assert "discovered_at" in tracker
    
    # Check that the discovery state is set
    state = hass.states.get(f"import_statistics.{component_name}_discovered")
    assert state is not None
    assert state.state == "True"
    assert state.attributes["component_name"] == component_name
    assert state.attributes["vendor"] == vendor
    assert state.attributes["entity_count"] == len(entities)


def test_get_nonexistent_discovered_tracker() -> None:
    """Test getting a tracker that doesn't exist."""
    tracker = get_discovered_tracker("nonexistent_tracker")
    assert tracker is None


def test_get_all_discovered_trackers(hass: HomeAssistant) -> None:
    """Test getting all discovered trackers."""
    # Initially should be empty
    all_trackers = get_all_discovered_trackers()
    assert len(all_trackers) == 0
    
    # Store first tracker
    store_discovered_tracker(
        hass,
        "tracker1",
        "Vendor 1",
        {"model": "T1"},
        [{"name": "steps", "friendly_name": "Steps"}],
    )
    
    # Store second tracker
    store_discovered_tracker(
        hass,
        "tracker2",
        "Vendor 2",
        {"model": "T2"},
        [{"name": "heart_rate", "friendly_name": "Heart Rate"}],
    )
    
    # Get all trackers
    all_trackers = get_all_discovered_trackers()
    assert len(all_trackers) == 2
    assert "tracker1" in all_trackers
    assert "tracker2" in all_trackers
    assert all_trackers["tracker1"]["vendor"] == "Vendor 1"
    assert all_trackers["tracker2"]["vendor"] == "Vendor 2"


def test_remove_discovered_tracker(hass: HomeAssistant) -> None:
    """Test removing a discovered tracker."""
    component_name = "test_tracker"
    
    # Store a tracker first
    store_discovered_tracker(
        hass,
        component_name,
        "Test Vendor",
        {"model": "TT-1000"},
        [{"name": "steps", "friendly_name": "Steps"}],
    )
    
    # Verify it exists
    tracker = get_discovered_tracker(component_name)
    assert tracker is not None
    
    # Remove the tracker
    result = remove_discovered_tracker(component_name)
    assert result is True
    
    # Verify it's gone
    tracker = get_discovered_tracker(component_name)
    assert tracker is None
    
    # Try removing again
    result = remove_discovered_tracker(component_name)
    assert result is False


def test_create_device_info() -> None:
    """Test creating device info."""
    component_name = "test_tracker"
    vendor = "Test Vendor"
    device_info = {
        "model": "TT-1000",
        "manufacturer": "Test Corp",
        "sw_version": "1.0.0",
        "hw_version": "2.0",
    }
    
    device_info_obj = create_device_info(component_name, vendor, device_info)
    
    assert device_info_obj["name"] == vendor
    assert ("import_statistics", component_name) in device_info_obj["identifiers"]
    assert device_info_obj["manufacturer"] == "Test Corp"
    assert device_info_obj["model"] == "TT-1000"
    assert device_info_obj["sw_version"] == "1.0.0"
    assert device_info_obj["hw_version"] == "2.0"


def test_create_device_info_minimal() -> None:
    """Test creating device info with minimal data."""
    component_name = "minimal_tracker"
    vendor = "Minimal Vendor"
    device_info = {}
    
    device_info_obj = create_device_info(component_name, vendor, device_info)
    
    assert device_info_obj["name"] == vendor
    assert ("import_statistics", component_name) in device_info_obj["identifiers"]
    assert device_info_obj["manufacturer"] == vendor
    assert device_info_obj["model"] is None
    assert device_info_obj["sw_version"] is None
    assert device_info_obj["hw_version"] is None


def test_store_discovered_tracker_overwrites(hass: HomeAssistant) -> None:
    """Test that storing a tracker with the same name overwrites the previous one."""
    component_name = "test_tracker"
    
    # Store first version
    store_discovered_tracker(
        hass,
        component_name,
        "Vendor 1",
        {"model": "T1"},
        [{"name": "steps", "friendly_name": "Steps"}],
    )
    
    # Store second version with same name
    store_discovered_tracker(
        hass,
        component_name,
        "Vendor 2",
        {"model": "T2"},
        [{"name": "heart_rate", "friendly_name": "Heart Rate"}],
    )
    
    # Verify only the second version exists
    tracker = get_discovered_tracker(component_name)
    assert tracker is not None
    assert tracker["vendor"] == "Vendor 2"
    assert tracker["device_info"]["model"] == "T2"
    assert len(tracker["entities"]) == 1
    assert tracker["entities"][0]["name"] == "heart_rate"
    
    # Verify only one tracker exists in total
    all_trackers = get_all_discovered_trackers()
    assert len(all_trackers) == 1