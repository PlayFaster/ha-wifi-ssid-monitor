"""Config flow for WiFi SSID Monitor integration."""

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import AbortFlow
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import WifiScanAPI, WifiScanError
from .const import (
    CONF_INTERFACE,
    CONF_KNOWN_SSIDS,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    DEFAULT_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def _validate_input(hass, user_input):
    """Validate user input."""
    session = async_get_clientsession(hass)
    api = WifiScanAPI(session, user_input[CONF_INTERFACE])
    await api.validate()


async def _get_wifi_interfaces(hass):
    """Fetch available WiFi interfaces.

    Returns a list of interface names, or empty list if fetch fails.
    """
    try:
        session = async_get_clientsession(hass)
        # Use a dummy interface name since get_interfaces doesn't depend on it
        api = WifiScanAPI(session, "")
        return await api.get_interfaces()
    except WifiScanError as e:
        _LOGGER.debug("Could not fetch available WiFi interfaces: %s", e)
        return []


class WifiScanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WiFi SSID Monitor."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        interfaces = await _get_wifi_interfaces(self.hass)

        if user_input is not None:
            try:
                await _validate_input(self.hass, user_input)
                await self.async_set_unique_id(
                    f"wifi_ssid_monitor_{user_input[CONF_INTERFACE]}"
                )
                self._abort_if_unique_id_configured()

                name = user_input.get(CONF_NAME, DEFAULT_NAME)

                return self.async_create_entry(
                    title=name,
                    data={},
                    options={
                        CONF_NAME: name,
                        CONF_INTERFACE: user_input[CONF_INTERFACE],
                        CONF_KNOWN_SSIDS: user_input[CONF_KNOWN_SSIDS],
                        CONF_SCAN_INTERVAL: 600,
                    },
                )
            except WifiScanError:
                errors["base"] = "cannot_connect"
            except AbortFlow:
                raise
            except Exception:
                _LOGGER.exception("Unexpected error")
                errors["base"] = "unknown"

        data_schema = {
            vol.Required(CONF_NAME, default=DEFAULT_NAME): cv.string,
            vol.Optional(CONF_KNOWN_SSIDS, default=""): cv.string,
        }

        if interfaces:
            data_schema[vol.Required(CONF_INTERFACE, default=interfaces[0])] = vol.In(
                interfaces
            )
        else:
            data_schema[vol.Required(CONF_INTERFACE, default="wlan0")] = cv.string

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return WifiScanOptionsFlowHandler(config_entry)


class WifiScanOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for WiFi SSID Monitor."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        errors = {}
        interfaces = await _get_wifi_interfaces(self.hass)

        if user_input is not None:
            try:
                # Only validate if interface changed
                if user_input[CONF_INTERFACE] != self._config_entry.options.get(
                    CONF_INTERFACE
                ):
                    await _validate_input(self.hass, user_input)

                # Update entry title if name changed
                if user_input.get(CONF_NAME) != self._config_entry.options.get(
                    CONF_NAME
                ):
                    self.hass.config_entries.async_update_entry(
                        self._config_entry, title=user_input[CONF_NAME]
                    )

                return self.async_create_entry(title="", data=user_input)
            except WifiScanError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error validating options")
                errors["base"] = "unknown"

        current_interface = self._config_entry.options.get(
            CONF_INTERFACE, self._config_entry.data.get(CONF_INTERFACE, "wlan0")
        )

        # Ensure current interface is in the list even if it's not detected as wifi
        available_interfaces = list(interfaces) if interfaces else []
        if current_interface not in available_interfaces:
            available_interfaces.append(current_interface)

        data_schema = {
            vol.Required(
                CONF_NAME,
                default=self._config_entry.options.get(CONF_NAME, DEFAULT_NAME),
            ): cv.string,
            vol.Optional(
                CONF_KNOWN_SSIDS,
                default=self._config_entry.options.get(
                    CONF_KNOWN_SSIDS,
                    self._config_entry.data.get(CONF_KNOWN_SSIDS, ""),
                ),
            ): cv.string,
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=self._config_entry.options.get(CONF_SCAN_INTERVAL, 600),
            ): vol.All(vol.Coerce(int), vol.Range(min=60)),
        }

        if available_interfaces:
            data_schema[vol.Required(CONF_INTERFACE, default=current_interface)] = (
                vol.In(available_interfaces)
            )
        else:
            data_schema[vol.Required(CONF_INTERFACE, default=current_interface)] = (
                cv.string
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(data_schema),
            errors=errors,
        )
