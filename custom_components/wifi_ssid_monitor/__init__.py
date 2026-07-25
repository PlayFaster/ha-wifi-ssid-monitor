"""The WiFi SSID Monitor integration."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType

from .api import WifiScanAPI
from .const import (
    CONF_DENYLIST_SSIDS,
    CONF_INCLUDE_HIDDEN,
    CONF_INTERFACE,
    CONF_KNOWN_SSIDS,
    CONF_PROXIMITY_SIGNAL_THRESHOLD,
    CONF_SCAN_INTERVAL,
    CONF_SHOW_5GHZ,
    CONF_SHOW_6GHZ,
    CONF_SHOW_24GHZ,
    DEFAULT_NAME,
    DEFAULT_PROXIMITY_SIGNAL_THRESHOLD,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    LEGACY_CONF_PROXIMITY_RSSI_THRESHOLD,
    LEGACY_CONF_SCAN_BANDS,
    LIVE_OPTION_KEYS,
    STORAGE_VERSION,
    VERSION,
    all_storage_keys,
)
from .coordinator import WifiScanCoordinator
from .parse import dbm_to_pct
from .services import async_register_services

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS: list[str] = ["sensor", "binary_sensor", "number", "button", "switch"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the WiFi SSID Monitor domain."""
    async_register_services(hass)
    return True


def _migrate_options(options: dict[str, Any]) -> dict[str, Any]:
    """Bring an entry's options onto the current schema, once.

    Two settings changed meaning in this release and are migrated here so the
    control entities and the coordinator only ever see the new keys:

    * The proximity threshold moved from a negative dBm value to a 0-100
      percentage. A stored negative value is converted; the old key is dropped.
    * The single ``scan_bands`` enum became three per-band switches.
    """
    migrated = dict(options)

    # Proximity threshold: dBm -> percent.
    if LEGACY_CONF_PROXIMITY_RSSI_THRESHOLD in migrated:
        legacy = migrated.pop(LEGACY_CONF_PROXIMITY_RSSI_THRESHOLD)
        if CONF_PROXIMITY_SIGNAL_THRESHOLD not in migrated:
            try:
                value = float(legacy)
            except (TypeError, ValueError):
                value = None
            if value is not None and value < 0:
                migrated[CONF_PROXIMITY_SIGNAL_THRESHOLD] = dbm_to_pct(value)
            elif value is not None:
                migrated[CONF_PROXIMITY_SIGNAL_THRESHOLD] = int(max(0, min(100, value)))
            else:
                migrated[CONF_PROXIMITY_SIGNAL_THRESHOLD] = (
                    DEFAULT_PROXIMITY_SIGNAL_THRESHOLD
                )

    # Band enum -> three switches.
    if LEGACY_CONF_SCAN_BANDS in migrated:
        bands = migrated.pop(LEGACY_CONF_SCAN_BANDS)
        if CONF_SHOW_24GHZ not in migrated:
            migrated[CONF_SHOW_24GHZ] = bands in ("all", "2.4")
            migrated[CONF_SHOW_5GHZ] = bands in ("all", "5")
            # No 6 GHz existed under the old enum; default it on to match "all".
            migrated[CONF_SHOW_6GHZ] = bands == "all"

    return migrated


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WiFi SSID Monitor from a config entry."""
    # Migrate data -> options (legacy installs) then run the option migration.
    options = dict(entry.options)
    if entry.data:
        _LOGGER.debug("Migrating configuration from data to options")
        options = {**entry.data, **options}
        if CONF_SCAN_INTERVAL not in options:
            options[CONF_SCAN_INTERVAL] = DEFAULT_SCAN_INTERVAL

    migrated = _migrate_options(options)
    if migrated != dict(entry.options) or entry.data:
        hass.config_entries.async_update_entry(entry, data={}, options=migrated)

    interface = entry.options.get(CONF_INTERFACE, "wlan0")

    # Migrate the single-entry legacy title.
    entries = hass.config_entries.async_entries(DOMAIN)
    if len(entries) == 1 and entry.title == f"{DEFAULT_NAME} ({interface})":
        _LOGGER.debug("Migrating config entry title to %s", DEFAULT_NAME)
        hass.config_entries.async_update_entry(entry, title=DEFAULT_NAME)

    session = async_get_clientsession(hass)
    api = WifiScanAPI(session, interface)

    coordinator = WifiScanCoordinator(hass, entry, api, VERSION)
    await coordinator.async_initialize()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # First fetch runs in the background so setup returns instantly. Platforms
    # are already forwarded, so entities exist (unavailable) if it fails, and
    # the Integration Health sensor reports the reason — no probe needed.
    entry.async_create_background_task(
        hass, coordinator.async_refresh(), "wifi-ssid-monitor-setup"
    )

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and release resources."""
    coordinator: WifiScanCoordinator = entry.runtime_data
    # A reload fires no HOMEASSISTANT_STOP, so a pending coalesced save would be
    # lost. Flush (not delete) before teardown; removal is a separate event.
    await coordinator.async_flush_stores()
    return bool(await hass.config_entries.async_unload_platforms(entry, PLATFORMS))


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove all stored data when the config entry is deleted.

    Keys come from the shared helpers so the delete side cannot drift from the
    write side in the coordinator.
    """
    await asyncio.gather(
        *(
            Store(hass, version=STORAGE_VERSION, key=key).async_remove()
            for key in all_storage_keys(entry.entry_id)
        )
    )


REFRESH_ON_CHANGE_KEYS: frozenset[str] = frozenset(
    {
        CONF_KNOWN_SSIDS,
        CONF_DENYLIST_SSIDS,
        CONF_INCLUDE_HIDDEN,
        CONF_PROXIMITY_SIGNAL_THRESHOLD,
        CONF_SHOW_24GHZ,
        CONF_SHOW_5GHZ,
        CONF_SHOW_6GHZ,
    }
)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Apply option changes, reloading only when a structural option changed.

    Live options — the ones read fresh each poll or applied by a control — are
    handled without a reload. Everything else reloads, so a future structural
    option cannot silently default to live and desync the entity set.
    """
    coordinator: WifiScanCoordinator = entry.runtime_data

    changed = _changed_option_keys(coordinator, entry)

    if changed - LIVE_OPTION_KEYS:
        # A structural option changed (interface, name, or anything new).
        await hass.config_entries.async_reload(entry.entry_id)
        return

    # Live-only change: apply in place.
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    new_delta = timedelta(seconds=scan_interval)
    if coordinator.update_interval != new_delta:
        _LOGGER.debug("Updating scan interval to %s seconds", scan_interval)
        coordinator.update_interval = new_delta

    coordinator.last_reload_options = dict(entry.options)

    # Re-scan on any filter, list, or threshold change so the effect is immediate;
    # bare interval changes and pause-polling toggles do not force a fetch.
    if changed & REFRESH_ON_CHANGE_KEYS:
        await coordinator.async_force_refresh()


def _changed_option_keys(
    coordinator: WifiScanCoordinator, entry: ConfigEntry
) -> set[str]:
    """Return the option keys whose value changed since the last reload."""
    previous = coordinator.last_reload_options
    current = dict(entry.options)
    coordinator.last_reload_options = current
    keys = set(previous) | set(current)
    return {k for k in keys if previous.get(k) != current.get(k)}
