"""Diagnostics support for WiFi SSID Monitor."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_KNOWN_SSIDS, DOMAIN
from .coordinator import WifiScanCoordinator

REDACT_CONFIG = {CONF_KNOWN_SSIDS}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: WifiScanCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Redact known SSIDs as they might be sensitive to some users
    diag_data = {
        "entry": {
            "title": entry.title,
            "version": entry.version,
            "data": async_redact_data(entry.data, REDACT_CONFIG),
            "options": async_redact_data(entry.options, REDACT_CONFIG),
            "unique_id": entry.unique_id,
        },
        "coordinator": {
            "interface": coordinator.api.interface,
            "last_update_success": coordinator.last_update_success,
            "last_update_success_time": coordinator.last_update_success_time,
            "version": coordinator.version,
            "data": coordinator.data,
        },
    }

    return diag_data
