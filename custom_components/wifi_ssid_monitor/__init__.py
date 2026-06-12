"""The WiFi SSID Monitor integration."""

import asyncio
import logging
from datetime import timedelta
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType

from .api import WifiScanAPI
from .const import (
    CONF_INTERFACE,
    CONF_KNOWN_SSIDS,
    CONF_SCAN_INTERVAL,
    DEFAULT_NAME,
    DOMAIN,
    VERSION,
)
from .coordinator import WifiScanCoordinator

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS: list[str] = ["sensor", "binary_sensor", "number", "button"]

SERVICE_ADD_KNOWN_SSID = "add_known_ssid"
SERVICE_SCHEMA_ADD_KNOWN_SSID = vol.Schema(
    {
        vol.Required("ssid"): cv.string,
        vol.Optional("config_entry_id"): cv.string,
    }
)

SERVICE_REMOVE_KNOWN_SSID = "remove_known_ssid"
SERVICE_SCHEMA_REMOVE_KNOWN_SSID = vol.Schema(
    {
        vol.Required("ssid"): cv.string,
        vol.Optional("config_entry_id"): cv.string,
    }
)

SERVICE_SCAN_NOW = "scan_now"
SERVICE_SCHEMA_SCAN_NOW = vol.Schema({vol.Optional("config_entry_id"): cv.string})

SERVICE_CLEAR_LAST_SEEN = "clear_last_seen"
SERVICE_SCHEMA_CLEAR_LAST_SEEN = vol.Schema(
    {vol.Optional("config_entry_id"): cv.string}
)

SERVICE_SET_KNOWN_SSIDS = "set_known_ssids"
SERVICE_SCHEMA_SET_KNOWN_SSIDS = vol.Schema(
    {
        vol.Required("known_ssids"): cv.string,
        vol.Optional("config_entry_id"): cv.string,
    }
)


def _resolve_entries(
    hass: HomeAssistant, target_entry_id: str | None
) -> list[ConfigEntry]:
    """Return the target entries, raising HomeAssistantError if ID not found."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if target_entry_id:
        entries = [e for e in entries if e.entry_id == target_entry_id]
        if not entries:
            raise HomeAssistantError(
                f"No {DOMAIN} entry found with ID '{target_entry_id}'",
                translation_domain=DOMAIN,
                translation_key="entry_not_found",
                translation_placeholders={"entry_id": target_entry_id},
            )
    return entries


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the WiFi SSID Monitor domain."""

    async def _handle_add_known_ssid(call: ServiceCall) -> None:
        ssid = call.data["ssid"].strip()
        for target_entry in _resolve_entries(hass, call.data.get("config_entry_id")):
            current = target_entry.options.get(CONF_KNOWN_SSIDS, "")
            existing = [x.strip() for x in current.split(",") if x.strip()]
            if ssid in existing:
                continue
            existing.append(ssid)
            new_options = dict(target_entry.options)
            new_options[CONF_KNOWN_SSIDS] = ", ".join(existing)
            hass.config_entries.async_update_entry(target_entry, options=new_options)

    async def _handle_remove_known_ssid(call: ServiceCall) -> None:
        ssid = call.data["ssid"].strip()
        for target_entry in _resolve_entries(hass, call.data.get("config_entry_id")):
            current = target_entry.options.get(CONF_KNOWN_SSIDS, "")
            existing = [x.strip() for x in current.split(",") if x.strip()]
            new_list = [x for x in existing if x != ssid]
            if new_list == existing:
                continue  # SSID not present in this entry — silent success
            new_options = dict(target_entry.options)
            new_options[CONF_KNOWN_SSIDS] = ", ".join(new_list)
            hass.config_entries.async_update_entry(target_entry, options=new_options)

    async def _handle_scan_now(call: ServiceCall) -> None:
        for target_entry in _resolve_entries(hass, call.data.get("config_entry_id")):
            coordinator: WifiScanCoordinator = target_entry.runtime_data
            await coordinator.async_refresh()

    async def _handle_clear_last_seen(call: ServiceCall) -> None:
        for target_entry in _resolve_entries(hass, call.data.get("config_entry_id")):
            coordinator: WifiScanCoordinator = target_entry.runtime_data
            await coordinator.async_clear_history()

    async def _handle_set_known_ssids(call: ServiceCall) -> dict[str, Any]:
        new_ssids_str = call.data["known_ssids"].strip()
        old_entries: dict[str, str] = {}
        new_entries: dict[str, str] = {}
        for target_entry in _resolve_entries(hass, call.data.get("config_entry_id")):
            old_entries[target_entry.entry_id] = target_entry.options.get(
                CONF_KNOWN_SSIDS, ""
            )
            new_options = dict(target_entry.options)
            new_options[CONF_KNOWN_SSIDS] = new_ssids_str
            hass.config_entries.async_update_entry(target_entry, options=new_options)
            new_entries[target_entry.entry_id] = new_ssids_str
        return {"new_entries": new_entries, "old_entries": old_entries}

    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_KNOWN_SSID,
        _handle_add_known_ssid,
        schema=SERVICE_SCHEMA_ADD_KNOWN_SSID,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_KNOWN_SSID,
        _handle_remove_known_ssid,
        schema=SERVICE_SCHEMA_REMOVE_KNOWN_SSID,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SCAN_NOW,
        _handle_scan_now,
        schema=SERVICE_SCHEMA_SCAN_NOW,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CLEAR_LAST_SEEN,
        _handle_clear_last_seen,
        schema=SERVICE_SCHEMA_CLEAR_LAST_SEEN,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_KNOWN_SSIDS,
        _handle_set_known_ssids,
        schema=SERVICE_SCHEMA_SET_KNOWN_SSIDS,
        supports_response=SupportsResponse.OPTIONAL,
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WiFi SSID Monitor from a config entry."""
    # Migrate from entry.data to entry.options if needed
    if entry.data and not entry.options:
        _LOGGER.debug("Migrating configuration from data to options")
        hass.config_entries.async_update_entry(
            entry,
            data={},
            options={
                CONF_INTERFACE: entry.data.get(CONF_INTERFACE, "wlan0"),
                CONF_KNOWN_SSIDS: entry.data.get(CONF_KNOWN_SSIDS, ""),
                CONF_SCAN_INTERVAL: 600,
            },
        )

    # Migrate title if it's the only entry and has the old format
    entries = hass.config_entries.async_entries(DOMAIN)
    interface = entry.options.get(CONF_INTERFACE, "wlan0")
    if len(entries) == 1 and entry.title == f"{DEFAULT_NAME} ({interface})":
        _LOGGER.debug("Migrating config entry title to %s", DEFAULT_NAME)
        hass.config_entries.async_update_entry(entry, title=DEFAULT_NAME)

    session = async_get_clientsession(hass)
    api = WifiScanAPI(session, interface)

    coordinator = WifiScanCoordinator(hass, entry, api, VERSION)

    # Load persisted history before the first scan
    await coordinator.async_initialize()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Trigger the first refresh in the background to avoid blocking HA startup
    entry.async_create_background_task(
        hass, coordinator.async_refresh(), "wifi-ssid-monitor-setup"
    )

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and release resources."""
    return bool(await hass.config_entries.async_unload_platforms(entry, PLATFORMS))


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove all stored data when the config entry is deleted."""
    await asyncio.gather(
        Store(
            hass, version=1, key=f"{DOMAIN}.{entry.entry_id}.last_seen"
        ).async_remove(),
        Store(
            hass, version=1, key=f"{DOMAIN}.{entry.entry_id}.first_seen"
        ).async_remove(),
        Store(
            hass, version=1, key=f"{DOMAIN}.{entry.entry_id}.visit_counts"
        ).async_remove(),
    )


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options are updated."""
    coordinator: WifiScanCoordinator = entry.runtime_data

    new_interface = entry.options.get(CONF_INTERFACE)

    if coordinator.api.interface != new_interface:
        _LOGGER.debug(
            "Interface changed from %s to %s, reloading",
            coordinator.api.interface,
            new_interface,
        )
        await hass.config_entries.async_reload(entry.entry_id)
        return

    # Update coordinator interval if it changed
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, 600)
    new_delta = timedelta(seconds=scan_interval)
    if coordinator.update_interval != new_delta:
        _LOGGER.debug("Updating scan interval to %s seconds", scan_interval)
        coordinator.update_interval = new_delta

    # Refresh the coordinator ONLY if known_wifi_ids changed.
    # Changing ONLY the scan interval will NOT trigger an immediate re-scan.
    new_known_ssids = entry.options.get(CONF_KNOWN_SSIDS, "")
    if coordinator.last_known_ssids != new_known_ssids:
        _LOGGER.debug("Known SSIDs changed, refreshing data")
        await coordinator.async_refresh()
