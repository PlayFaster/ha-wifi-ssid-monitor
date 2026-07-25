"""Config flow for WiFi SSID Monitor integration."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import AbortFlow
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import WifiScanAPI, WifiScanError
from .const import (
    CONF_DENYLIST_SSIDS,
    CONF_INTERFACE,
    CONF_KNOWN_SSIDS,
    CONF_LAST_SEEN_TTL_DAYS,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    DEFAULT_LAST_SEEN_TTL_DAYS,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def _validate_input(hass: HomeAssistant, interface: str) -> None:
    """Validate the API connection for an interface."""
    api = WifiScanAPI(async_get_clientsession(hass), interface)
    await api.validate()


async def _get_wifi_interfaces(hass: HomeAssistant) -> list[str]:
    """Fetch available WiFi interfaces, or an empty list if the fetch fails."""
    try:
        api = WifiScanAPI(async_get_clientsession(hass), "")
        return await api.get_interfaces()
    except WifiScanError as err:
        _LOGGER.debug("Could not fetch available WiFi interfaces: %s", err)
        return []


def _build_settings_schema(
    options: Mapping[str, Any],
    available_interfaces: list[str],
    current_interface: str,
    name_fallback: str,
) -> vol.Schema:
    """Build the reconfigure/options schema.

    The frequently-tuned settings — scan interval, band filter, hidden
    networks, proximity threshold — are Home Assistant entities now, not fields
    here, so they are deliberately absent. This flow keeps identity (name,
    interface) and the two things that are genuinely lists (known / denylist)
    plus the history retention window.
    """
    return vol.Schema(
        {
            vol.Required(
                CONF_NAME, default=options.get(CONF_NAME, name_fallback)
            ): cv.string,
            vol.Optional(
                CONF_KNOWN_SSIDS, default=options.get(CONF_KNOWN_SSIDS, "")
            ): cv.string,
            vol.Optional(
                CONF_DENYLIST_SSIDS,
                default=options.get(CONF_DENYLIST_SSIDS, ""),
            ): cv.string,
            vol.Optional(
                CONF_LAST_SEEN_TTL_DAYS,
                default=options.get(
                    CONF_LAST_SEEN_TTL_DAYS, DEFAULT_LAST_SEEN_TTL_DAYS
                ),
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=366)),
            vol.Required(CONF_INTERFACE, default=current_interface): vol.In(
                available_interfaces
            ),
        }
    )


class WifiScanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WiFi SSID Monitor."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        interfaces = await _get_wifi_interfaces(self.hass)

        if user_input is not None:
            try:
                await _validate_input(self.hass, user_input[CONF_INTERFACE])
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
                        CONF_KNOWN_SSIDS: user_input.get(CONF_KNOWN_SSIDS, ""),
                        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                    },
                )
            except WifiScanError:
                errors["base"] = "cannot_connect"
            except AbortFlow:
                raise
            except Exception:
                _LOGGER.exception("Unexpected error")
                errors["base"] = "unknown"

        data_schema: dict[Any, Any] = {
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
            step_id="user", data_schema=vol.Schema(data_schema), errors=errors
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Handle reauthentication."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Confirm reauthentication."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                interface = self._get_reauth_entry().options.get(
                    CONF_INTERFACE, "wlan0"
                )
                await _validate_input(self.hass, interface)
                return self.async_update_reload_and_abort(self._get_reauth_entry())
            except WifiScanError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during reauth")
                errors["base"] = "unknown"

        return self.async_show_form(step_id="reauth_confirm", errors=errors)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle reconfiguration."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()
        interfaces = await _get_wifi_interfaces(self.hass)

        if user_input is not None:
            try:
                await _validate_input(self.hass, user_input[CONF_INTERFACE])

                new_interface = user_input[CONF_INTERFACE]
                if new_interface != entry.options.get(CONF_INTERFACE):
                    await self.async_set_unique_id(f"wifi_ssid_monitor_{new_interface}")
                    self._abort_if_unique_id_configured()

                name = user_input.get(CONF_NAME, entry.title)
                return self.async_update_reload_and_abort(
                    entry,
                    title=name,
                    options={**entry.options, **user_input},
                )
            except WifiScanError:
                errors["base"] = "cannot_connect"
            except AbortFlow:
                raise
            except Exception:
                _LOGGER.exception("Unexpected error during reconfigure")
                errors["base"] = "unknown"

        current_interface = entry.options.get(CONF_INTERFACE, "wlan0")
        available = list(interfaces) if interfaces else []
        if current_interface not in available:
            available.append(current_interface)

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_build_settings_schema(
                entry.options, available, current_interface, entry.title
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> WifiScanOptionsFlowHandler:
        """Get the options flow for this handler."""
        return WifiScanOptionsFlowHandler(config_entry)


class WifiScanOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for WiFi SSID Monitor."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}
        interfaces = await _get_wifi_interfaces(self.hass)

        if user_input is not None:
            try:
                if user_input[CONF_INTERFACE] != self._config_entry.options.get(
                    CONF_INTERFACE
                ):
                    await _validate_input(self.hass, user_input[CONF_INTERFACE])

                if user_input.get(CONF_NAME) != self._config_entry.options.get(
                    CONF_NAME
                ):
                    self.hass.config_entries.async_update_entry(
                        self._config_entry, title=user_input[CONF_NAME]
                    )

                return self.async_create_entry(
                    title="", data={**self._config_entry.options, **user_input}
                )
            except WifiScanError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error validating options")
                errors["base"] = "unknown"

        current_interface = self._config_entry.options.get(CONF_INTERFACE, "wlan0")
        available = list(interfaces) if interfaces else []
        if current_interface not in available:
            available.append(current_interface)

        return self.async_show_form(
            step_id="init",
            data_schema=_build_settings_schema(
                self._config_entry.options, available, current_interface, DEFAULT_NAME
            ),
            errors=errors,
        )
