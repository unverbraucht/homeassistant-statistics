"""Handle a config flow initialized from UI."""

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .discovery import get_all_discovered_trackers, get_discovered_tracker, remove_discovered_tracker


class ImportStatisticsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for the Import Statistics integration."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_trackers = {}
        self._selected_tracker = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle a config flow initialized from UI."""
        if user_input is not None:
            return self.async_create_entry(title="Import Statistics", data={})

        return self.async_show_form(step_id="user")

    async def async_step_import(self, import_data: dict[str, Any]) -> ConfigFlowResult:
        """Handle a config flow from configuration.yaml."""
        return await self.async_step_user(import_data)

    async def async_step_discovery(self, discovery_info: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the discovery step for fitness trackers."""
        # Get all discovered trackers
        self._discovered_trackers = get_all_discovered_trackers()
        
        if not self._discovered_trackers:
            return self.async_abort(reason="no_discovered_trackers")

        # If discovery_info is provided, pre-select that tracker
        if discovery_info and "component_name" in discovery_info:
            component_name = discovery_info["component_name"]
            self._selected_tracker = get_discovered_tracker(component_name)
            
            if not self._selected_tracker:
                return self.async_abort(reason="tracker_not_found")
            
            # Set unique ID to prevent duplicate config entries
            unique_id = f"{DOMAIN}_{component_name}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
            
            # Move to confirmation step
            return await self.async_step_confirm()

        # If no pre-selected tracker, show selection form
        options = {
            tracker["component_name"]: f"{tracker['vendor']} ({tracker['component_name']})"
            for tracker in self._discovered_trackers.values()
        }
        
        # Create schema with dropdown options
        schema = {
            vol.Required("component_name"): vol.In(list(self._discovered_trackers.keys())),
        }
        
        return self.async_show_form(
            step_id="discovery",
            data_schema=vol.Schema(schema),
            description_placeholders={"options": "\n".join(f"- {name}: {desc}" for name, desc in options.items())},
        )
    
    async def async_step_discovery_select(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle manual tracker selection from discovery list."""
        if user_input is not None:
            # User selected a tracker
            component_name = user_input["component_name"]
            self._selected_tracker = get_discovered_tracker(component_name)
            
            if not self._selected_tracker:
                return self.async_abort(reason="tracker_not_found")
            
            # Set unique ID to prevent duplicate config entries
            unique_id = f"{DOMAIN}_{component_name}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
            
            # Move to confirmation step
            return await self.async_step_confirm()
        
        # Get all discovered trackers for selection
        self._discovered_trackers = get_all_discovered_trackers()
        
        if not self._discovered_trackers:
            return self.async_abort(reason="no_discovered_trackers")
        
        # Show selection form
        options = {
            tracker["component_name"]: f"{tracker['vendor']} ({tracker['component_name']})"
            for tracker in self._discovered_trackers.values()
        }
        
        # Create schema with dropdown options
        schema = {
            vol.Required("component_name"): vol.In(list(self._discovered_trackers.keys())),
        }
        
        return self.async_show_form(
            step_id="discovery_select",
            data_schema=vol.Schema(schema),
            description_placeholders={"options": "\n".join(f"- {name}: {desc}" for name, desc in options.items())},
        )

    async def async_step_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the confirmation step for adding a fitness tracker."""
        if user_input is not None:
            # Create the config entry with the tracker data (user confirmed by clicking submit)
            # Remove from discovered trackers
            remove_discovered_tracker(self._selected_tracker["component_name"])
            
            return self.async_create_entry(
                title=f"{self._selected_tracker['vendor']} - {self._selected_tracker['component_name']}",
                data={
                    "component_name": self._selected_tracker["component_name"],
                    "vendor": self._selected_tracker["vendor"],
                    "device_info": self._selected_tracker["device_info"],
                    "entities": self._selected_tracker["entities"],
                },
            )

        # Show confirmation form with tracker details
        tracker = self._selected_tracker
        
        # Build entity list
        entities_list = "\n".join(
            f"  • {entity.get('friendly_name', entity['name'])}"
            for entity in tracker["entities"]
        )
        
        # Build device description
        device_info = tracker.get("device_info", {})
        device_name = tracker["vendor"]
        if device_info.get("model"):
            device_name = f"{tracker['vendor']} {device_info['model']}"
        if device_info.get("manufacturer") and device_info.get("manufacturer") != tracker["vendor"]:
            device_name = f"{device_name} by {device_info['manufacturer']}"
        
        # Build full description
        description = (
            f"Add {device_name}?\n\n"
            f"Component name: {tracker['component_name']}\n\n"
            f"This will create {len(tracker['entities'])} entities:\n\n"
            f"{entities_list}"
        )
        
        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({
                vol.Required("add_device", default=True): bool,
            }),
            description_placeholders={"description": description},
        )
