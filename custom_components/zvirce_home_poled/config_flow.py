"""Config flow for PoLED integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_USER_ID,
    CONF_LIGHTS,
    CONF_COVERS,
    DEFAULT_HOST,
    DEFAULT_USER_ID,
)
from .api import PoLEDApiClient

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Required(CONF_USER_ID, default=DEFAULT_USER_ID): int,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # Try to connect to the PoLED gateway
    try:
        client = await hass.async_add_executor_job(
            PoLEDApiClient, data[CONF_HOST], data[CONF_USER_ID]
        )

        if client._user is None:
            raise CannotConnect("Failed to connect to PoLED gateway")

        # Fetch initial data to populate blinds
        await hass.async_add_executor_job(client.sync_get_data)

        # Get available lights and covers
        lights = {}
        for group_id, group in client._user.groups.items():
            lights[str(group_id)] = {
                "name": group.name,
                "enabled": True,
            }

        covers = {}
        for blind_id in range(12):
            blind = client._pli.blinds.get(blind_id)
            if blind:
                covers[str(blind_id)] = {
                    "name": blind.name,
                    "enabled": True,
                }

        return {
            "title": f"PoLED Gateway ({data[CONF_HOST]})",
            "lights": lights,
            "covers": covers,
        }
    except Exception as err:
        _LOGGER.exception("Unexpected exception during validation")
        raise CannotConnect(f"Unexpected error: {err}") from err


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PoLED."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Create unique ID based on host
                await self.async_set_unique_id(user_input[CONF_HOST])
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                    options={
                        CONF_LIGHTS: info["lights"],
                        CONF_COVERS: info["covers"],
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for PoLED."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["lights", "covers"],
        )

    async def async_step_lights(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage light channels."""
        if user_input is not None:
            # Parse the user input and update lights configuration
            lights = dict(self.config_entry.options.get(CONF_LIGHTS, {}))

            for key, value in user_input.items():
                if key.startswith("light_") and key.endswith("_enabled"):
                    light_id = key.replace("light_", "").replace("_enabled", "")
                    if light_id not in lights:
                        lights[light_id] = {}
                    lights[light_id]["enabled"] = value
                elif key.startswith("light_") and key.endswith("_name"):
                    light_id = key.replace("light_", "").replace("_name", "")
                    if light_id not in lights:
                        lights[light_id] = {}
                    lights[light_id]["name"] = value

            # Update options
            new_options = dict(self.config_entry.options)
            new_options[CONF_LIGHTS] = lights

            return self.async_create_entry(title="", data=new_options)

        # Get current lights configuration
        lights = self.config_entry.options.get(CONF_LIGHTS, {})

        # Build schema for light configuration
        schema = {}
        for light_id, light_config in lights.items():
            light_name = light_config.get("name", f"Light {light_id}")
            schema[vol.Optional(
                f"light_{light_id}_enabled",
                default=light_config.get("enabled", True)
            )] = bool
            schema[vol.Optional(
                f"light_{light_id}_name",
                default=light_name
            )] = str

        return self.async_show_form(
            step_id="lights",
            data_schema=vol.Schema(schema),
        )

    async def async_step_covers(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage cover channels."""
        if user_input is not None:
            # Parse the user input and update covers configuration
            covers = dict(self.config_entry.options.get(CONF_COVERS, {}))

            for key, value in user_input.items():
                if key.startswith("cover_") and key.endswith("_enabled"):
                    cover_id = key.replace("cover_", "").replace("_enabled", "")
                    if cover_id not in covers:
                        covers[cover_id] = {}
                    covers[cover_id]["enabled"] = value
                elif key.startswith("cover_") and key.endswith("_name"):
                    cover_id = key.replace("cover_", "").replace("_name", "")
                    if cover_id not in covers:
                        covers[cover_id] = {}
                    covers[cover_id]["name"] = value

            # Update options
            new_options = dict(self.config_entry.options)
            new_options[CONF_COVERS] = covers

            return self.async_create_entry(title="", data=new_options)

        # Get current covers configuration
        covers = self.config_entry.options.get(CONF_COVERS, {})

        # Build schema for cover configuration
        schema = {}
        for cover_id, cover_config in covers.items():
            cover_name = cover_config.get("name", f"Cover {cover_id}")
            schema[vol.Optional(
                f"cover_{cover_id}_enabled",
                default=cover_config.get("enabled", True)
            )] = bool
            schema[vol.Optional(
                f"cover_{cover_id}_name",
                default=cover_name
            )] = str

        return self.async_show_form(
            step_id="covers",
            data_schema=vol.Schema(schema),
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

