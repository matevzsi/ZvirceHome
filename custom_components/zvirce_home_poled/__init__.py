"""
PoLED integration for Home Assistant.
"""
from datetime import timedelta
import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.typing import ConfigType

from .api import PoLEDApiClient

from .const import (
    CONF_HOST,
    CONF_USER_ID,
    DOMAIN,
    PLATFORMS,
)

SCAN_INTERVAL = timedelta(seconds=2)

_LOGGER: logging.Logger = logging.getLogger(__package__)

# Config schema - integration only supports config entries
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the PoLED component from YAML (deprecated)."""
    # This is kept for backwards compatibility but does nothing
    # All setup is now done via config flow
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PoLED from a config entry."""
    _LOGGER.info("PoLED setup entry")

    # Get configuration from config entry
    host = entry.data[CONF_HOST]
    user_id = entry.data[CONF_USER_ID]

    _LOGGER.info(f"Creating API object for {host}...")

    # Create API client
    try:
        client = await hass.async_add_executor_job(
            PoLEDApiClient, host, user_id
        )

        if client._user is None:
            raise ConfigEntryNotReady("Failed to connect to PoLED gateway")
    except Exception as err:
        _LOGGER.error(f"Failed to connect to PoLED gateway: {err}")
        raise ConfigEntryNotReady from err

    _LOGGER.info("Creating update coordinator")
    coordinator = PoLEDDataUpdateCoordinator(hass, client=client)

    # Perform initial data fetch
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator and client
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        'coordinator': coordinator,
        'client': client,
        'entry': entry,
    }

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("PoLED unload entry")

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class PoLEDDataUpdateCoordinator(DataUpdateCoordinator):    
    def __init__(
        self, hass: HomeAssistant, client: PoLEDApiClient) -> None:
        """Initialize."""
        self.api = client
        self.platforms = []
        self.hass = hass

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    async def _async_update_data(self):
        """Update data via library."""
        try:            
            data = await self.hass.async_add_executor_job(self.api.sync_get_data)
        except Exception as exception:
            raise UpdateFailed() from exception

