"""Platform for light integration."""
from __future__ import annotations

import logging

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_RGBW_COLOR,
    LightEntity,
    ColorMode,
)
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
    """Set up PoLED lights from a config entry."""
    _LOGGER.info("Light async_setup_entry")

    # Get data from hass.data
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    client = data["client"]

    # Get lights configuration from options
    lights_config = entry.options.get(CONF_LIGHTS, {})

    _LOGGER.info("Adding light entities...")
    entities = []

    # Add enabled lights from configuration
    for group_id, group in client._user.groups.items():
        light_id = str(group_id)
        light_cfg = lights_config.get(light_id, {})

        # Only add if enabled (default to True if not specified)
        if light_cfg.get("enabled", True):
            entities.append(PoLEDLightChannel(coordinator, group, entry))

    async_add_entities(entities)


class PoLEDLightChannel(IntegrationPoLEDEntity, LightEntity):
    """Representation of an PoLED Light."""

    def __init__(self, coordinator, config_entry, entry: ConfigEntry):
        """Initialize the light."""
        super().__init__(coordinator, config_entry)
        self._entry = entry

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        # Try to get custom name from options
        lights_config = self._entry.options.get(CONF_LIGHTS, {})
        light_id = str(self.ref.ID)
        light_cfg = lights_config.get(light_id, {})
        custom_name = light_cfg.get("name")

        if custom_name:
            return custom_name
        return self.ref.name


    @property
    def brightness(self):
        """Return the brightness of the light."""

        # RGBW - return the maximum level between whites and rgb average
        if (self.ref.type & 4) == 4:
            return max([self.ref.white_warm, self.ref.white_cold, (self.ref.rgb[0]+self.ref.rgb[1]+self.ref.rgb[2])/3])

        # Otherwise return maximum of whites
        return max([self.ref.white_warm, self.ref.white_cold])

    @property
    def color_temp(self):
        #total = self.ref.white_warm + self.ref.white_cold
        #if total > 0:
        #    return self.min_mireds + (self.max_mireds - self.min_mireds) * self.ref.white_warm / total
        #return self.min_mireds

        b = self.brightness

        if b == 0:
            return self.min_mireds

        if self.ref.white_warm > self.ref.white_cold:
            r = float(self.ref.white_cold) / self.ref.white_warm / 2.0
        else:
            r = 1 - float(self.ref.white_warm) / self.ref.white_cold / 2.0

        color_K = 2700 + 1300 * r
        return 1e6 / color_K
            

    @property
    def supported_color_modes(self):
        if (self.ref.type & 3) == 3:
            # White with temperature selection
            return [ColorMode.COLOR_TEMP]
        elif (self.ref.type & 4) == 4:
            return [ColorMode.RGBW]
        elif (self.ref.type & 3) == 1 or (self.ref.type & 3) == 2:
            return [ColorMode.BRIGHTNESS]
        else:
            return [ColorMode.ONOFF]

    @property
    def color_mode(self):
        # Only one mode supported
        return self.supported_color_modes[0]

    @property
    def rgbw_color(self):
        if (self.ref.type & 3) == 0:
            return (self.ref.rgb[0], self.ref.rgb[1], self.ref.rgb[2], self.ref.white_warm)
        else:
            return (self.ref.rgb[0], self.ref.rgb[1], self.ref.rgb[2], self.ref.white_cold)

    @property
    def min_mireds(self):
        return 1e6/4000.0

    @property
    def max_mireds(self):
        return 1e6/2700.0


    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return (self.ref.white_warm > 0 or 
                self.ref.white_cold > 0 or 
                self.ref.rgb[0] > 0 or 
                self.ref.rgb[1] > 0 or 
                self.ref.rgb[2] > 0)

   
    def turn_on(self, **kwargs) -> None:
        """Instruct the light to turn on."""
        if (self.ref.type & 3) == 3:
            # WW+NW
            if ATTR_COLOR_TEMP in kwargs:
                temp_K = 1e6 / kwargs[ATTR_COLOR_TEMP]
                power = self.brightness
            else:
                temp_K = 1e6 / self.color_temp                

            temp = (temp_K - 2700) / 1300
            if temp < 0:
                temp = 0
            elif temp > 1:
                temp = 1

            if ATTR_BRIGHTNESS in kwargs:
                power = kwargs[ATTR_BRIGHTNESS]
                if self.brightness == 0:
                    temp = 0.5

            if not (ATTR_BRIGHTNESS in kwargs or ATTR_COLOR_TEMP in kwargs):
                # None of them are in arguments -> ON command to default value
                power = 220

            if temp < 0.5:
                self.ref.white_warm = int(power)
                self.ref.white_cold = int(power * 2 * temp)
            else:
                self.ref.white_warm = int((1 - temp) * 2 * power)
                self.ref.white_cold = int(power)

            self.ref.rgb = [0, 0, 0]

        elif (self.ref.type & 4) == 4:
            # RGBW
            if ATTR_RGBW_COLOR in kwargs:
                # RGBW in arguments
                rgbw = list(kwargs[ATTR_RGBW_COLOR])
                self.ref.rgb = rgbw[0:3]
                self.ref.white_warm = rgbw[3]
                self.ref.white_cold = rgbw[3]

            elif ATTR_BRIGHTNESS in kwargs:
                power = kwargs[ATTR_BRIGHTNESS]
                self.ref.rgb = [power, power, power]
                self.ref.white_warm = power
                self.ref.white_cold = power

            else:
                self.ref.rgb = [0, 0, 0]
                self.ref.white_warm = 220
                self.ref.white_cold = 220

        elif (self.ref.type & 3) > 0:
            # Only brightness control
            power = kwargs.get(ATTR_BRIGHTNESS, 220)

            self.ref.white_warm = power
            self.ref.white_cold = power          

        else:
            # On/off
            power = kwargs.get(ATTR_BRIGHTNESS, 220)
            self.ref.white_warm = power
            self.ref.white_cold = power          

        #_LOGGER.info(f"Setting {self.ref.name} to P={power}/T={temp} => {self.ref.white_warm}/{self.ref.white_cold}")
        #_LOGGER.info(f"Resulting in P={self.brightness}/T={self.color_temp}")
        
        self.ref.override = 1
        self.coordinator.api.set_status(self.ref)

    def turn_off(self, **kwargs) -> None:
        """Instruct the light to turn off."""
        self.ref.white_warm = 0
        self.ref.white_cold = 0
        self.ref.rgb = [0, 0, 0]
        self.ref.override = 1
        self.coordinator.api.set_status(self.ref)
