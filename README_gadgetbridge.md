# Fitness Tracker Discovery Service for Home Assistant Statistics Integration

## Overview

This document describes the updated fitness tracker discovery service for the Home Assistant Statistics integration. Instead of directly creating components and entities, the service now discovers fitness trackers and makes them available for configuration through the integration's config flow. This approach provides better user control and follows Home Assistant's recommended patterns for device integration.

## Service Name

`create_fitness_component`

## Purpose

To discover a fitness tracker device and store its metadata for later configuration through the integration setup flow. The service does not directly create entities but instead makes the tracker available for user approval and configuration.

## Key Features

1. **Discovery-Based Approach**: Fitness trackers are discovered first, then configured by the user
2. **User Control**: Users can review and approve discovered trackers before adding them
3. **Volatile Storage**: Discovery data is stored in memory only (not persisted)
4. **Config Flow Integration**: Discovered trackers appear in the integration's configuration flow
5. **Generic Vendor Support**: Works with any fitness tracker vendor or custom setup

## Service Interface

The service is called with the following parameters:

```yaml
service: import_statistics.create_fitness_component
data:
  component_name: "my_fitness_tracker"
  vendor: "Generic Fitness Tracker"
  device_info:
    model: "FT-1000"
    manufacturer: "Fitness Corp"
    sw_version: "1.0.0"
    hw_version: "2.0"
  entities:
    - name: "daily_steps"
      friendly_name: "Daily Steps"
      state_class: "total_increasing"
      icon: "mdi:foot-print"
    - name: "heart_rate"
      friendly_name: "Heart Rate"
      state_class: "measurement"
      icon: "mdi:heart-pulse"
    - name: "sleep_duration"
      friendly_name: "Sleep Duration"
      unit_of_measurement: "h"
      device_class: "duration"
      state_class: "total"
      icon: "mdi:sleep"
    - name: "blood_oxygen"
      friendly_name: "Blood Oxygen"
      state_class: "measurement"
      icon: "mdi:heart-pulse"
```

## Implementation Details

### 1. Service Registration

The service is registered in `__init__.py` as an async service:

```python
async def handle_create_fitness_component(call: ServiceCall) -> None:
    """Handle the fitness component discovery service call."""
    _LOGGER.info("Service handle_create_fitness_component called")
    await fitness_component.discover_fitness_component(hass, call)
    
    component_name = call.data.get(ATTR_COMPONENT_NAME)
    vendor = call.data.get("vendor", "Fitness Tracker")
    device_info = call.data.get("device_info", {})
    
    # Create a more descriptive title for discovery
    model = device_info.get("model", "")
    title = f"{vendor} {model}".strip() if model else vendor
    
    # Trigger discovery flow notification with proper discovery_info
    await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "discovery", "title_placeholders": {"name": title}},
        data={"component_name": component_name, "vendor": vendor},
    )

hass.services.async_register(DOMAIN, SERVICE_CREATE_FITNESS_COMPONENT, handle_create_fitness_component)
```

### 2. Discovery Storage

A new module `discovery.py` handles the in-memory storage of discovered trackers:

```python
async def store_discovered_tracker(
    hass: HomeAssistant,
    component_name: str,
    vendor: str,
    device_info: Dict[str, Any],
    entities: List[Dict[str, Any]],
) -> None:
    """Store a discovered fitness tracker in memory."""
    # Store tracker data in volatile memory
    _DISCOVERED_TRACKERS[component_name] = tracker_data
    
    # Set discovery state for notification
    hass.states.async_set(
        f"import_statistics.{component_name}_discovered",
        "discovered",
        attributes={...},
    )
```

The module provides functions for managing discovered trackers:
- `store_discovered_tracker()` - Store a newly discovered tracker
- `get_discovered_tracker()` - Retrieve a specific tracker
- `get_all_discovered_trackers()` - Get all discovered trackers
- `remove_discovered_tracker()` - Remove a tracker from discovery
- `create_device_info()` - Create DeviceInfo object for registration

### 3. Config Flow Integration

The config flow in `config_flow.py` is enhanced to handle discovered trackers:

```python
async def async_step_discovery(self, discovery_info: dict[str, Any] | None = None) -> ConfigFlowResult:
    """Handle the discovery step for fitness trackers."""
    # Get all discovered trackers
    self._discovered_trackers = get_all_discovered_trackers()
    
    if discovery_info and "component_name" in discovery_info:
        # Pre-select the discovered tracker
        component_name = discovery_info["component_name"]
        self._selected_tracker = get_discovered_tracker(component_name)
        
        # Set unique ID to prevent duplicates
        unique_id = f"{DOMAIN}_{component_name}"
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()
        
        # Move to confirmation step
        return await self.async_step_confirm()
```

The confirmation step shows detailed tracker information:

```python
async def async_step_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
    """Handle the confirmation step for adding a fitness tracker."""
    if user_input is not None:
        # Remove from discovered trackers
        remove_discovered_tracker(self._selected_tracker["component_name"])
        
        # Create config entry with tracker data
        return self.async_create_entry(
            title=f"{self._selected_tracker['vendor']} - {self._selected_tracker['component_name']}",
            data={...},
        )
    
    # Build and show confirmation dialog with full tracker details
```

### 4. Entity Platform Implementation

A new `sensor.py` module implements proper entity platform support:

```python
class FitnessTrackerSensor(SensorEntity):
    """Representation of a fitness tracker sensor."""
    
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, component_name, entity_config, device_info):
        """Initialize the sensor with config."""
        self._attr_unique_id = f"{component_name}_{entity_name}"
        self._attr_name = entity_config.get("friendly_name", entity_name)
        self._attr_native_unit_of_measurement = entity_config.get("unit_of_measurement")
        self._attr_device_class = entity_config.get("device_class")
        self._attr_state_class = entity_config.get("state_class")
        self._attr_icon = entity_config.get("icon")
```

The platform setup creates all sensor entities:

```python
async def async_setup_entry(hass, entry, async_add_entities):
    """Set up fitness tracker sensor entities from a config entry."""
    # Create sensor entities for each configured entity
    entities = [
        FitnessTrackerSensor(component_name, entity_config, device_info)
        for entity_config in entities_config
    ]
    async_add_entities(entities, True)
```

### 5. Config Entry Setup

The `async_setup_entry()` in `__init__.py` forwards setup to the sensor platform:

```python
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the device based on a config entry."""
    # Forward the setup to the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True
```

And proper cleanup on unload:

```python
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload the sensor platform
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    return unload_ok
```

### 4. Data Flow

1. External app calls `create_fitness_component` service with tracker configuration
2. Service validates and stores tracker data in volatile memory (not persisted)
3. Service triggers discovery flow, which shows discovered device notification
4. User clicks "Configure" on the discovered device notification
5. Config flow automatically pre-selects the discovered tracker
6. User reviews detailed tracker information (vendor, model, entities) in confirmation dialog
7. User clicks "Submit" to confirm addition
8. Integration creates:
   - Device entry in device registry
   - Config entry with tracker configuration
   - Sensor entities via proper entity platform
9. Entities are created in "unavailable" state, ready to receive data
10. User can then use the existing `import_from_json` service to import historical data

### 5. Integration with Existing Services

The discovery service works with the existing `import_from_json` service:

```yaml
# First, discover the tracker
service: import_statistics.create_fitness_component
data:
  component_name: "my_fitness_tracker"
  vendor: "Generic Fitness Tracker"
  entities:
    - name: "daily_steps"
      friendly_name: "Daily Steps"
      unit_of_measurement: "steps"
      device_class: "step"
      state_class: "total_increasing"

# Then, configure through the UI and import data using the existing service
service: import_statistics.import_from_json
data:
  timezone_identifier: Europe/Vienna
  entities:
    - id: "sensor.my_fitness_tracker_daily_steps"
      unit: "steps"
      values:
        - state: 8500
          sum: 8500
          datetime: "2024-09-13 00:00"
```

## Benefits

1. **User Control**: Users can review and approve devices before adding them
2. **Better UX**: Follows Home Assistant's standard device discovery pattern with notifications
3. **Clean Integration**: Properly integrates with Home Assistant's device and entity registries
4. **Proper Entity Platform**: Uses standard sensor platform for easy management and deletion
5. **Flexible**: Still supports any vendor or custom fitness tracker setup
6. **Non-Intrusive**: Discovery is volatile - no permanent changes until user approval
7. **Multiple Devices**: Supports multiple fitness trackers simultaneously
8. **Detailed Confirmation**: Shows complete device and entity information before adding

## Technical Considerations

1. **Volatile Storage**: Discovery data is stored in memory only and lost on restart
2. **User Notification**: Discovery flow automatically triggers notification showing device name
3. **Config Flow**: Enhanced config flow with discovery and confirmation steps
4. **Unique IDs**: Properly generated and checked to prevent duplicate config entries
5. **Error Handling**: Comprehensive validation and error messages for invalid configurations
6. **Entity Platform**: Uses proper sensor platform for lifecycle management
7. **Async Operations**: All operations are async for better performance
8. **Clean Removal**: Entities and devices can be properly deleted through UI
9. **Device Registry**: Devices are properly registered with manufacturer, model, and version info
10. **Entity Registry**: Entities have proper attributes including state_class, device_class, and icons

## Files Created/Modified

1. `custom_components/import_statistics/__init__.py` - Updated service handler and config entry setup
2. `custom_components/import_statistics/fitness_component.py` - Discovery validation logic
3. `custom_components/import_statistics/discovery.py` - New async module for discovery storage
4. `custom_components/import_statistics/config_flow.py` - Enhanced with discovery and confirmation steps
5. `custom_components/import_statistics/sensor.py` - **New** proper sensor platform implementation
6. `custom_components/import_statistics/services.yaml` - Updated service description
7. `custom_components/import_statistics/strings.json` - Added discovery flow translations
8. `custom_components/import_statistics/translations/en.json` - Added English translations
9. `custom_components/import_statistics/manifest.json` - Changed to support multiple config entries
10. Tests for the new discovery functionality

## Example Use Cases

1. **Gadgetbridge Integration**: Discover a Gadgetbridge-synced fitness tracker
2. **Custom Fitness App**: Discover devices from a custom fitness application
3. **Multiple Devices**: Discover and configure multiple fitness trackers separately
4. **Specialized Metrics**: Discover trackers with specialized fitness metrics

## User Experience

1. **Discovery**: External app calls the service to discover a fitness tracker
2. **Notification**: Home Assistant shows a notification with the device name (e.g., "Gadgetbridge Band 5")
3. **Configuration**: User clicks "Configure" on the notification
4. **Review**: User sees detailed information including:
   - Vendor and model name
   - Component name
   - List of all entities with friendly names
5. **Approval**: User clicks "Submit" to confirm adding the tracker
6. **Confirmation**: Success message shows device and entities were created
7. **Usage**: Entities appear in Home Assistant, ready to receive data via `import_from_json` service
8. **Management**: Devices and entities can be easily removed through the UI if needed

## Conclusion

This discovery-based approach provides a better user experience while maintaining the flexibility of the original design. By separating discovery from configuration, users have more control over which devices are added to their Home Assistant instance, following Home Assistant's recommended patterns for device integration.