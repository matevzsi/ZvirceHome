"""PoLEDEntity class"""
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import logging
from .const import DOMAIN, NAME, VERSION, ATTRIBUTION

_LOGGER: logging.Logger = logging.getLogger(__package__)


class IntegrationPoLEDEntity(CoordinatorEntity):
    def __init__(self, coordinator, config_entry):

        #_LOGGER.info(f"New entity: config={config_entry}")

        super().__init__(coordinator)
        self.ref = config_entry
        self.entity_name = "poled." + self.ref.name

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return self.entity_name

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": NAME,
            "model": VERSION,
            "manufacturer": NAME,
        }

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            "attribution": ATTRIBUTION,
            #"id": str(self.coordinator.data.get("id")),
            "integration": DOMAIN,
        }
