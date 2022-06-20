"""
PoLED integration for Home Assistant.
"""
import asyncio
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.typing import ConfigType

from .api import PoLEDApiClient

from .const import (    
    CONF_USERNAME,
    DOMAIN,
    PLATFORMS,
    STARTUP_MESSAGE,
)

SCAN_INTERVAL = timedelta(seconds=2)

_LOGGER: logging.Logger = logging.getLogger(__package__)

async def async_poll_api(hass):
    #poll API here, grab the things I need from it, and set it to data
    client = hass.data[DOMAIN]['client']
    data = await hass.async_add_executor_job(client.sync_get_data)
    return data

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:    
    _LOGGER.info("PoLED setup")

    _LOGGER.info("Creating API object...")    
    client = PoLEDApiClient(0)
    _LOGGER.info("Creating update coordinator")

    '''coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="poled_coordinator",
        update_method=async_poll_api,
        update_interval=timedelta(seconds=5), 
    )'''

    coordinator = PoLEDDataUpdateCoordinator(hass, client=client)
    coordinator.api.sync_get_data()

    hass.data[DOMAIN] = { 'coordinator': coordinator, 'client': client}
    await async_poll_api(hass)


    _LOGGER.info("Initializing platforms")
    for platform in PLATFORMS:
        coordinator.platforms.append(platform)
        hass.helpers.discovery.load_platform(platform, DOMAIN, {}, config)
        
    return True


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

