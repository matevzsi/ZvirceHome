"""PoLEDEntity class"""
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
import logging
from .const import DOMAIN, VERSION, ATTRIBUTION

_LOGGER: logging.Logger = logging.getLogger(__package__)


class IntegrationPoLEDEntity(CoordinatorEntity):
    def __init__(self, coordinator, config_entry, entry_id):

        #_LOGGER.info(f"New entity: config={config_entry}")

        super().__init__(coordinator)
        self.ref = config_entry
        self._entry_id = entry_id
        self.entity_name = "poled." + self.ref.name

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return f"{self._entry_id}_{self.entity_name}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this PoLED gateway."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=f"PoLED Gateway ({self.coordinator.api.host})",
            manufacturer="Zvirce",
            model="PoLED Gateway",
            sw_version=VERSION,
        )

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            "attribution": ATTRIBUTION,
            #"id": str(self.coordinator.data.get("id")),
            "integration": DOMAIN,
        }
