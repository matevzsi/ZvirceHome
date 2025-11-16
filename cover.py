"""Platform for cover integration."""
from __future__ import annotations

import logging

from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    CoverEntity,
    CoverDeviceClass,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_COVERS, DOMAIN
from .entity import IntegrationPoLEDEntity


_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PoLED covers from a config entry."""
    _LOGGER.info("Cover async_setup_entry")

    # Get data from hass.data
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    client = data["client"]

    # Get covers configuration from options
    covers_config = entry.options.get(CONF_COVERS, {})

    _LOGGER.info("Adding cover entities...")
    entities = []

    # Add enabled covers from configuration
    for blind_id in range(12):
        blind = client._pli.blinds.get(blind_id)
        if blind:
            cover_id = str(blind_id)
            cover_cfg = covers_config.get(cover_id, {})

            # Only add if enabled (default to True if not specified)
            if cover_cfg.get("enabled", True):
                # Add main cover entity
                entities.append(PoLEDBlindChannel(coordinator, blind, entry, False))
                # Add tilt-only entity
                entities.append(PoLEDBlindChannel(coordinator, blind, entry, True))

    async_add_entities(entities)


class PoLEDBlindChannel(IntegrationPoLEDEntity, CoverEntity):
    """Representation of an PoLED blind."""

    def __init__(self, coordinator, config_entry, entry: ConfigEntry, only_tilt: bool = False):
        """Initialize the cover."""
        super().__init__(coordinator, config_entry)
        self._entry = entry
        self.onlyTilt = only_tilt

        if only_tilt:
            self.entity_name = "blind_angle_." + self.ref.name
        else:
            self.entity_name = "blind." + self.ref.name

    @property
    def name(self) -> str:
        """Return the display name of this blind."""
        # Try to get custom name from options
        covers_config = self._entry.options.get(CONF_COVERS, {})
        cover_id = str(self.ref.ID)
        cover_cfg = covers_config.get(cover_id, {})
        custom_name = cover_cfg.get("name")

        if custom_name:
            if self.onlyTilt:
                return f"Naklon {custom_name}"
            return custom_name

        if self.onlyTilt:
            return f"Naklon {self.ref.name}"
        return self.ref.name

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
        return CoverDeviceClass.BLIND

    @property
    def supported_features(self) -> int:
        if self.onlyTilt:
            return CoverEntityFeature.OPEN_TILT | CoverEntityFeature.CLOSE_TILT | CoverEntityFeature.SET_TILT_POSITION | CoverEntityFeature.STOP_TILT
        else:
            return CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.SET_POSITION | CoverEntityFeature.STOP | CoverEntityFeature.OPEN_TILT | CoverEntityFeature.CLOSE_TILT | CoverEntityFeature.SET_TILT_POSITION | CoverEntityFeature.STOP_TILT


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
