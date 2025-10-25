"""Sensor platform for fitness tracker entities."""

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .discovery import create_device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up fitness tracker sensor entities from a config entry."""
    component_name = entry.data.get("component_name")
    vendor = entry.data.get("vendor")
    device_info_data = entry.data.get("device_info", {})
    entities_config = entry.data.get("entities", [])
    
    _LOGGER.info(f"Setting up {len(entities_config)} sensor entities for {component_name}")
    
    # Create device info
    device_info = create_device_info(component_name, vendor, device_info_data)
    
    # Create sensor entities
    entities = []
    for entity_config in entities_config:
        entity = FitnessTrackerSensor(
            component_name=component_name,
            entity_config=entity_config,
            device_info=device_info,
        )
        entities.append(entity)
    
    async_add_entities(entities, True)
    _LOGGER.info(f"Added {len(entities)} sensor entities for {component_name}")


class FitnessTrackerSensor(SensorEntity):
    """Representation of a fitness tracker sensor."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        component_name: str,
        entity_config: dict[str, Any],
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the sensor."""
        self._component_name = component_name
        self._entity_config = entity_config
        self._attr_device_info = device_info
        
        # Set entity attributes from config
        entity_name = entity_config["name"]
        self._attr_unique_id = f"{component_name}_{entity_name}"
        self._attr_name = entity_config.get("friendly_name", entity_name)
        self._attr_native_unit_of_measurement = entity_config.get("unit_of_measurement")
        self._attr_device_class = entity_config.get("device_class")
        self._attr_state_class = entity_config.get("state_class")
        self._attr_icon = entity_config.get("icon")
        
        # Initialize state as unavailable until data is imported
        self._attr_native_value = None
        self._attr_available = False
        
        _LOGGER.debug(f"Initialized sensor: {self.unique_id}")

    @property
    def entity_id(self) -> str:
        """Return the entity ID."""
        return f"sensor.{self._component_name}_{self._entity_config['name']}"

    async def async_added_to_hass(self) -> None:
        """Handle entity added to hass."""
        _LOGGER.info(f"Sensor {self.entity_id} added to Home Assistant")

    async def async_will_remove_from_hass(self) -> None:
        """Handle entity removal."""
        _LOGGER.info(f"Sensor {self.entity_id} removed from Home Assistant")