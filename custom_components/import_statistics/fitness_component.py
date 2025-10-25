"""Fitness component discovery for the import_statistics integration."""

import logging
from typing import Any, Dict, List

from homeassistant.core import HomeAssistant, ServiceCall

from custom_components.import_statistics.const import DOMAIN
from custom_components.import_statistics.discovery import store_discovered_tracker
from custom_components.import_statistics.helpers import _LOGGER, handle_error

_LOGGER = logging.getLogger(__name__)


async def discover_fitness_component(hass: HomeAssistant, call: ServiceCall) -> None:
    """
    Discover a fitness component with its entities.

    Args:
    ----
        hass: Home Assistant instance
        call: Service call containing the component configuration

    Raises:
    ------
        HomeAssistantError: If component discovery fails

    """
    _LOGGER.info("Discovering fitness component")
    
    component_name = call.data.get("component_name")
    vendor = call.data.get("vendor")
    device_info = call.data.get("device_info", {})
    entities = call.data.get("entities", [])

    # Validate required parameters
    if not component_name:
        handle_error("component_name is required")
    if not vendor:
        handle_error("vendor is required")
    if not entities:
        handle_error("at least one entity must be specified")

    # Validate component name
    if not component_name.replace("_", "").isalnum():
        handle_error(f"Invalid component_name: {component_name}. Only alphanumeric characters and underscores are allowed")

    # Validate entities
    for entity in entities:
        if "name" not in entity:
            handle_error("entity name is required")
        if "friendly_name" not in entity:
            handle_error("entity friendly_name is required")
        if not entity["name"].replace("_", "").isalnum():
            handle_error(f"Invalid entity name: {entity['name']}. Only alphanumeric characters and underscores are allowed")

    # Store the discovered tracker data
    await store_discovered_tracker(hass, component_name, vendor, device_info, entities)
    
    _LOGGER.info(f"Successfully discovered fitness component: {component_name} with {len(entities)} entities")