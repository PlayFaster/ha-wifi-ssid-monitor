"""The WiFi SSID Monitor integration."""

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import WifiScanAPI
from .const import CONF_INTERFACE, CONF_KNOWN_SSIDS, CONF_SCAN_INTERVAL, DOMAIN
from .coordinator import WifiScanCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor", "binary_sensor", "number"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WiFi SSID Monitor from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    interface = entry.options.get(
        CONF_INTERFACE, entry.data.get(CONF_INTERFACE, "wlan0")
    )
    session = async_get_clientsession(hass)
    api = WifiScanAPI(session, interface)

    coordinator = WifiScanCoordinator(hass, entry, api)

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options are updated."""
    coordinator: WifiScanCoordinator = hass.data[DOMAIN][entry.entry_id]

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
