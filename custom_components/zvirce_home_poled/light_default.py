from homeassistant.components.number import NumberEntity

class DefaultBrightnessNumber(NumberEntity):
    def __init__(self, hass, entry, light_id, mode_name, initial):
        self.hass = hass
        self.entry = entry
        self._light_id = light_id
        self._mode = mode_name  # "day", "night", ...
        self._attr_min_value = 1
        self._attr_max_value = 255
        self._attr_step = 1
        self._attr_native_value = initial
        self._attr_unique_id = f"{light_id}_{mode_name}_default_brightness"
        self._attr_name = f"{light_id} {mode_name.capitalize()} default brightness"

    @property
    def native_value(self):
        return self._attr_native_value

    async def async_set_native_value(self, value: float):
        self._attr_native_value = int(value)
        await self._store_to_entry_options()
        self.async_write_ha_state()

    async def _store_to_entry_options(self):
        # Load options
        options = dict(self.entry.options)
        lights = dict(options.get("lights", {}))
        light_cfg = dict(lights.get(self._light_id, {}))

        key = f"{self._mode}_brightness"
        light_cfg[key] = self._attr_native_value
        lights[self._light_id] = light_cfg
        options["lights"] = lights

        # Save back
        self.hass.config_entries.async_update_entry(self.entry, options=options)
