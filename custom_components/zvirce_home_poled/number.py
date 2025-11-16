"""Platform for number integration - Light default values."""
from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_LIGHTS, DOMAIN
from .entity import IntegrationPoLEDEntity


_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PoLED number entities from a config entry."""
    _LOGGER.info("Number async_setup_entry")

    # Get data from hass.data
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    client = data["client"]

    # Get lights configuration from options
    lights_config = entry.options.get(CONF_LIGHTS, {})

    _LOGGER.info("Adding number entities for light default values...")
    entities = []

    # Add number entities for enabled lights
    for group_id, group in client._user.groups.items():
        light_id = str(group_id)
        light_cfg = lights_config.get(light_id, {})

        # Only add if light is enabled (default to True if not specified)
        if light_cfg.get("enabled", True):
            entities.append(PoLEDLightDefaultValue(coordinator, group, entry, entry.entry_id))

    async_add_entities(entities)


class PoLEDLightDefaultValue(IntegrationPoLEDEntity, NumberEntity):
    """Representation of a PoLED Light Default Value control."""

    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0
    _attr_native_max_value = 255
    _attr_native_step = 1

    def __init__(self, coordinator, config_entry, entry: ConfigEntry, entry_id: str):
        """Initialize the number entity."""
        super().__init__(coordinator, config_entry, entry_id)
        self._entry = entry
        self.entity_name = f"poled.{self.ref.name}_default"
        self._attr_entity_category = "config"

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return f"{self._entry_id}_{self.entity_name}"

    @property
    def name(self) -> str:
        """Return the display name of this number entity."""
        # Try to get custom name from options
        lights_config = self._entry.options.get(CONF_LIGHTS, {})
        light_id = str(self.ref.ID)
        light_cfg = lights_config.get(light_id, {})
        custom_name = light_cfg.get("name")

        base_name = custom_name if custom_name else self.ref.name
        return f"{base_name} Default ON Value"

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        return "mdi:lightbulb-on-outline"

    @property
    def native_value(self) -> float:
        """Return the current default value."""
        return self.ref.default_value

    async def async_set_native_value(self, value: float) -> None:
        """Set the default value."""
        int_value = int(value)
        _LOGGER.info(f"Setting default value for {self.ref.name} to {int_value}")
        
        # Call the API to set the default value
        success = await self.hass.async_add_executor_job(
            self.coordinator.api.set_light_default_value,
            self.ref.ID,
            int_value
        )
        
        if success:
            # Update the coordinator to refresh the data
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error(f"Failed to set default value for {self.ref.name}")

