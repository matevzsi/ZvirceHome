"""Platform for cover integration."""
#from __future__ import annotations

import logging
import math


from homeassistant.components.cover import *
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
import homeassistant.util.color as color_util

from .const import DEFAULT_NAME, DOMAIN, ICON, COVER
from .entity import IntegrationPoLEDEntity


_LOGGER: logging.Logger = logging.getLogger(__package__)

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info) -> None:
    
    _LOGGER.info("Blinds setup platform")

    # We only want this platform to be set up via discovery.
    if discovery_info is None:
        _LOGGER.info("Not in discovery mode")
        return

    coordinator = hass.data[DOMAIN]["coordinator"]
    client = hass.data[DOMAIN]["client"]
    
    _LOGGER.info("Adding blinds entities...")
    devList = [PoLEDBlindChannel(coordinator, client._pli.blinds[i])  for i in range(12)]
    add_entities(devList)

    # Add the blinds again, this time indicate only tilt support
    devList2 = [PoLEDBlindChannel(coordinator, client._pli.blinds[i])  for i in range(12)]
    for b in devList2:
        b.limit_to_tilting()

    add_entities(devList2)


class PoLEDBlindChannel(IntegrationPoLEDEntity, CoverEntity):
    """Representation of an PoLED blind."""  

    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry)
        self.onlyTilt = False
        self.entity_name = "blind." + self.ref.name
        self.blind_name = self.ref.name

    def limit_to_tilting(self):
        self.onlyTilt = True
        self.entity_name = "blind_angle_." + self.ref.name
        self.blind_name = "Naklon " + self.ref.name

    @property
    def name(self) -> str:
        """Return the display name of this blind."""
        return self.blind_name

    @property
    def current_cover_position(self) -> int:
        # The current position of cover where 0 means closed and 100 is fully open. Required with SUPPORT_SET_POSITION.
        return self.ref.pos

    @property
    def current_cover_tilt_position(self) -> int:
        # The current tilt position of the cover where 0 means closed/no tilt and 100 means open/maximum tilt. Required with SUPPORT_SET_TILT_POSITION
        return self.ref.angle

    @property
    def is_opening(self) -> bool:
        # If the cover is opening or not. Used to determine state.
        return self.ref.pos < self.ref.refPos

    @property
    def is_closing(self) -> bool:
        # If the cover is closing or not. Used to determine state.
        return self.ref.pos > self.ref.refPos

    @property
    def is_closed(self) -> bool:
        # If the cover is closed or not. if the state is unknown, return None. Used to determine state.
        return self.ref.pos == 0

    @property
    def device_class(self) -> str:
        return DEVICE_CLASS_BLIND

    @property
    def supported_features(self) -> int:
        if self.onlyTilt:
            return SUPPORT_OPEN_TILT | SUPPORT_CLOSE_TILT | SUPPORT_SET_TILT_POSITION | SUPPORT_STOP_TILT
        else:
            return SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_SET_POSITION | SUPPORT_STOP | SUPPORT_OPEN_TILT | SUPPORT_CLOSE_TILT | SUPPORT_SET_TILT_POSITION | SUPPORT_STOP_TILT


    def open_cover(self, **kwargs):
        """Open the cover."""
        self.ref.refPos = 100
        self.coordinator.api.set_blind_position(self.ref)

    def close_cover(self, **kwargs):
        """Close cover."""
        self.ref.refPos = 0
        self.coordinator.api.set_blind_position(self.ref)
            
    def set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        self.ref.refPos = kwargs[ATTR_POSITION]
        self.coordinator.api.set_blind_position(self.ref)

    def stop_cover(self, **kwargs):
        """Stop the cover."""
        self.coordinator.api.stop_blind(self.ref)

    def open_cover_tilt(self, **kwargs):
        """Open the cover tilt."""
        self.ref.refAngle = 100
        self.coordinator.api.set_blind_position(self.ref)

    def close_cover_tilt(self, **kwargs):
        """Close the cover tilt."""
        self.ref.refAngle = 0
        self.coordinator.api.set_blind_position(self.ref)

    def set_cover_tilt_position(self, **kwargs):
        """Move the cover tilt to a specific position."""
        self.ref.refAngle = kwargs[ATTR_TILT_POSITION ]
        self.coordinator.api.set_blind_position(self.ref)
    
    def stop_cover_tilt(self, **kwargs):
        """Stop the cover."""
        self.coordinator.api.stop_blind(self.ref)
