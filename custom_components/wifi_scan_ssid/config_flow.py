import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

from .const import CONF_INTERFACE, CONF_KNOWN_SSIDS, CONF_SCAN_INTERVAL, DOMAIN


class WifiScanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Wifi Scan SSID."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(f"wifi_scan_{user_input[CONF_INTERFACE]}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"Wifi Scan ({user_input[CONF_INTERFACE]})",
                data=user_input,
                options={
                    CONF_INTERFACE: user_input[CONF_INTERFACE],
                    CONF_KNOWN_SSIDS: user_input[CONF_KNOWN_SSIDS],
                    CONF_SCAN_INTERVAL: 180,
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_INTERFACE, default="wlan0"): cv.string,
                    vol.Optional(CONF_KNOWN_SSIDS, default=""): cv.string,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return WifiScanOptionsFlowHandler(config_entry)


class WifiScanOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Wifi Scan SSID."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_INTERFACE,
                        default=self.config_entry.options.get(
                            CONF_INTERFACE,
                            self.config_entry.data.get(CONF_INTERFACE, "wlan0"),
                        ),
                    ): cv.string,
                    vol.Optional(
                        CONF_KNOWN_SSIDS,
                        default=self.config_entry.options.get(
                            CONF_KNOWN_SSIDS,
                            self.config_entry.data.get(CONF_KNOWN_SSIDS, ""),
                        ),
                    ): cv.string,
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(CONF_SCAN_INTERVAL, 180),
                    ): vol.All(vol.Coerce(int), vol.Range(min=30)),
                }
            ),
        )
