"""Diagnostics support for WiFi SSID Monitor.

A diagnostics download must be safe to attach to a public issue without hand
editing. Key-name redaction is not enough here: the payload is keyed by SSID,
and neighbouring SSIDs are third-party data — personal information about other
people, correlatable to the user's location. ``async_redact_data`` rewrites
values, never keys, so it cannot reach any of it.

This sanitizer learns every SSID and BSSID from the payload itself, allocates a
stable pseudonym for each, and rewrites them everywhere — including dictionary
keys. Signal, channel, band, counts and timestamps are preserved, because a
gutted file is as useless as a leaky one.
"""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_DENYLIST_SSIDS,
    CONF_KNOWN_SSIDS,
    HIDDEN_FALLBACK_LABEL,
    HIDDEN_KEY_PREFIX,
    NO_NETWORKS_SENTINEL,
)
from .coordinator import WifiScanCoordinator

# The known and denylist SSIDs are the user's own network names — redacted from
# the config block. The neighbour data is handled structurally below.
REDACT_CONFIG = {CONF_KNOWN_SSIDS, CONF_DENYLIST_SSIDS}

_MAC_RE = re.compile(r"^(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$")

# Values that carry no identity and must pass through untouched, or the file
# loses the very information a maintainer reads first.
_PRESERVE = {HIDDEN_FALLBACK_LABEL, NO_NETWORKS_SENTINEL}


class _Pseudonymizer:
    """Allocates and reuses stable tokens for the identifiers it is shown."""

    def __init__(self) -> None:
        self._ssid_tokens: dict[str, str] = {}
        self._bssid_tokens: dict[str, str] = {}

    def ssid(self, value: str) -> str:
        """Return a stable token for an SSID label."""
        if value in _PRESERVE:
            return value
        # A hidden label already reveals only the last hex of a BSSID; tokenize
        # it as a network so it still cross-references, but never leak the hex.
        token = self._ssid_tokens.get(value)
        if token is None:
            token = f"ssid-{len(self._ssid_tokens) + 1}"
            self._ssid_tokens[value] = token
        return token

    def bssid(self, value: str) -> str:
        """Return a stable token for a BSSID."""
        token = self._bssid_tokens.get(value)
        if token is None:
            token = f"bssid-{len(self._bssid_tokens) + 1}"
            self._bssid_tokens[value] = token
        return token

    def history_key(self, key: str) -> str:
        """Rewrite a history key, which is an SSID or ``hidden:<bssid>``."""
        if key.startswith(HIDDEN_KEY_PREFIX):
            return f"{HIDDEN_KEY_PREFIX}{self.bssid(key[len(HIDDEN_KEY_PREFIX) :])}"
        return self.ssid(key)


def _sanitize_networks(
    networks: dict[str, Any], pseudo: _Pseudonymizer
) -> dict[str, Any]:
    """Rewrite the SSID-keyed network map, keys and values alike."""
    result: dict[str, Any] = {}
    for label, net in networks.items():
        clean = dict(net)
        if clean.get("bssid"):
            clean["bssid"] = pseudo.bssid(clean["bssid"])
        if clean.get("key"):
            clean["key"] = pseudo.history_key(clean["key"])
        result[pseudo.ssid(label)] = clean
    return result


def _sanitize_history(
    history: dict[str, Any], pseudo: _Pseudonymizer
) -> dict[str, Any]:
    """Rewrite a history map keyed by network identity."""
    return {pseudo.history_key(key): value for key, value in history.items()}


def _sanitize_list(values: Any, pseudo: _Pseudonymizer) -> Any:
    """Rewrite a list of SSID labels."""
    if not isinstance(values, list):
        return values
    return [pseudo.ssid(v) if isinstance(v, str) else v for v in values]


def _sanitize_data(data: dict[str, Any]) -> dict[str, Any]:
    """Sanitize a coordinator data payload in place on a copy."""
    pseudo = _Pseudonymizer()
    clean = deepcopy(data)

    if isinstance(clean.get("networks"), dict):
        clean["networks"] = _sanitize_networks(clean["networks"], pseudo)

    for list_key in ("ssids", "unknown_ssids"):
        if list_key in clean:
            clean[list_key] = _sanitize_list(clean[list_key], pseudo)

    for hist_key in ("last_seen", "first_seen", "visit_counts"):
        if isinstance(clean.get(hist_key), dict):
            clean[hist_key] = _sanitize_history(clean[hist_key], pseudo)

    if isinstance(clean.get("strongest_unknown_ssid"), str):
        clean["strongest_unknown_ssid"] = pseudo.ssid(clean["strongest_unknown_ssid"])

    return clean


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: WifiScanCoordinator = entry.runtime_data

    data = coordinator.data
    sanitized_data = _sanitize_data(data) if isinstance(data, dict) else data

    return {
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
            "health_snapshot": coordinator.health_snapshot,
            "data": sanitized_data,
        },
    }
