"""Unit tests for config flow."""

import pytest
from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.data_entry_flow import FlowResultType

from custom_components.import_statistics.config_flow import ImportStatisticsConfigFlow
from custom_components.import_statistics.discovery import (
    store_discovered_tracker,
    _DISCOVERED_TRACKERS,
)


@pytest.fixture(autouse=True)
def clear_discovered_trackers():
    """Clear discovered trackers before each test."""
    _DISCOVERED_TRACKERS.clear()


@pytest.mark.asyncio
async def test_config_flow_user_step(hass: HomeAssistant) -> None:
    """Test user step of config flow."""
    flow = ImportStatisticsConfigFlow()
    flow.hass = hass
    flow.context = {}
    
    # Test initial step
    result = await flow.async_step_user()
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    
    # Test completing flow
    result = await flow.async_step_user({})
    
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Import Statistics"
    assert result["data"] == {}


@pytest.mark.asyncio
async def test_config_flow_discovery_no_trackers(hass: HomeAssistant) -> None:
    """Test discovery step when no trackers are available."""
    flow = ImportStatisticsConfigFlow()
    flow.hass = hass
    flow.context = {}
    
    result = await flow.async_step_discovery()
    
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "no_discovered_trackers"


@pytest.mark.asyncio
async def test_config_flow_discovery_with_trackers(hass: HomeAssistant) -> None:
    """Test discovery step when trackers are available."""
    # Store a discovered tracker
    store_discovered_tracker(
        hass,
        "test_tracker",
        "Test Vendor",
        {"model": "TT-1000"},
        [{"name": "steps", "friendly_name": "Steps"}],
    )
    
    flow = ImportStatisticsConfigFlow()
    flow.hass = hass
    flow.context = {}
    
    result = await flow.async_step_discovery()
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "discovery"
    # Check that schema has component_name field
    assert "component_name" in result["data_schema"].schema


@pytest.mark.asyncio
async def test_config_flow_discovery_select_tracker(hass: HomeAssistant) -> None:
    """Test selecting a tracker in discovery step."""
    # Store a discovered tracker
    store_discovered_tracker(
        hass,
        "test_tracker",
        "Test Vendor",
        {"model": "TT-1000"},
        [{"name": "steps", "friendly_name": "Steps"}],
    )
    
    flow = ImportStatisticsConfigFlow()
    flow.hass = hass
    flow.context = {}
    
    # Select tracker
    result = await flow.async_step_discovery({"component_name": "test_tracker"})
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "confirm"
    assert flow._selected_tracker is not None
    assert flow._selected_tracker["component_name"] == "test_tracker"


@pytest.mark.asyncio
async def test_config_flow_discovery_select_nonexistent_tracker(hass: HomeAssistant) -> None:
    """Test selecting a tracker that doesn't exist."""
    # Store a discovered tracker
    store_discovered_tracker(
        hass,
        "test_tracker",
        "Test Vendor",
        {"model": "TT-1000"},
        [{"name": "steps", "friendly_name": "Steps"}],
    )
    
    flow = ImportStatisticsConfigFlow()
    flow.hass = hass
    flow.context = {}
    
    # Select a non-existent tracker
    result = await flow.async_step_discovery({"component_name": "nonexistent_tracker"})
    
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "tracker_not_found"


@pytest.mark.asyncio
async def test_config_flow_confirm_success(hass: HomeAssistant) -> None:
    """Test confirming the addition of a fitness tracker."""
    # Store a discovered tracker
    store_discovered_tracker(
        hass,
        "test_tracker",
        "Test Vendor",
        {"model": "TT-1000"},
        [{"name": "steps", "friendly_name": "Steps"}],
    )
    
    flow = ImportStatisticsConfigFlow()
    flow.hass = hass
    flow.context = {}
    
    # Select tracker first
    await flow.async_step_discovery({"component_name": "test_tracker"})
    
    # Confirm the addition
    result = await flow.async_step_confirm({"confirm": True})
    
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Fitness Tracker: Test Vendor"
    assert result["data"]["component_name"] == "test_tracker"
    assert result["data"]["vendor"] == "Test Vendor"
    assert len(result["data"]["entities"]) == 1


@pytest.mark.asyncio
async def test_config_flow_confirm_cancelled(hass: HomeAssistant) -> None:
    """Test cancelling the addition of a fitness tracker."""
    # Store a discovered tracker
    store_discovered_tracker(
        hass,
        "test_tracker",
        "Test Vendor",
        {"model": "TT-1000"},
        [{"name": "steps", "friendly_name": "Steps"}],
    )
    
    flow = ImportStatisticsConfigFlow()
    flow.hass = hass
    flow.context = {}
    
    # Select tracker first
    await flow.async_step_discovery({"component_name": "test_tracker"})
    
    # Cancel the addition
    result = await flow.async_step_confirm({"confirm": False})
    
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "not_confirmed"


@pytest.mark.asyncio
async def test_config_flow_import_step(hass: HomeAssistant) -> None:
    """Test import step of the config flow."""
    flow = ImportStatisticsConfigFlow()
    flow.hass = hass
    flow.context = {}
    
    import_data = {"some": "data"}
    result = await flow.async_step_import(import_data)
    
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Import Statistics"
    # The import step doesn't pass through data, it just creates an empty entry
    assert result["data"] == {}


@pytest.mark.asyncio
async def test_config_flow_unique_id_prevents_duplicates(hass: HomeAssistant) -> None:
    """Test that unique ID prevents duplicate config entries."""
    # Store a discovered tracker
    store_discovered_tracker(
        hass,
        "test_tracker",
        "Test Vendor",
        {"model": "TT-1000"},
        [{"name": "steps", "friendly_name": "Steps"}],
    )
    
    # Mock config entry to simulate an existing entry
    with patch.object(
        hass.config_entries,
        "async_get_entry",
        return_value={"entry_id": "test"},
    ):
        flow = ImportStatisticsConfigFlow()
        flow.hass = hass
        flow.context = {}
        
        # Try to select the tracker (this will set the unique ID and check for existing entries)
        result = await flow.async_step_discovery({"component_name": "test_tracker"})
        
        # Should abort because the entry already exists
        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "already_configured"