"""Services for WiFi SSID Monitor.

All services are domain-global and registered once in ``async_setup``. Each
resolves its target entry from the call, defaulting to every configured entry.
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import (
    BAND_5,
    BAND_6,
    BAND_24,
    DOMAIN,
    SERVICE_ADD_SSID,
    SERVICE_CLEAR_LAST_SEEN,
    SERVICE_GET_NETWORKS,
    SERVICE_REMOVE_SSID,
    SERVICE_SCAN_NOW,
    SERVICE_SET_SSIDS,
    TARGET_DENYLIST,
    TARGET_KNOWN,
    TARGET_OPTION_KEYS,
)
from .coordinator import WifiScanCoordinator

_LOGGER = logging.getLogger(__name__)

_TARGETS = vol.In([TARGET_KNOWN, TARGET_DENYLIST])
_BANDS = vol.In(["2.4", "5", "6", "all"])
_SCOPES = vol.In(["known", "unknown", "all"])

_BAND_LABELS = {"2.4": BAND_24, "5": BAND_5, "6": BAND_6}

DEFAULT_QUANTITY = 50
MAX_QUANTITY = 500

SCHEMA_ADD_SSID = vol.Schema(
    {
        vol.Required("ssid"): cv.string,
        vol.Required("target", default=TARGET_KNOWN): _TARGETS,
        vol.Optional("config_entry_id"): cv.string,
    }
)

SCHEMA_REMOVE_SSID = vol.Schema(
    {
        vol.Required("ssid"): cv.string,
        vol.Required("target", default=TARGET_KNOWN): _TARGETS,
        vol.Optional("config_entry_id"): cv.string,
    }
)

SCHEMA_SET_SSIDS = vol.Schema(
    {
        vol.Required("values"): cv.string,
        vol.Required("target", default=TARGET_KNOWN): _TARGETS,
        vol.Optional("config_entry_id"): cv.string,
    }
)

SCHEMA_ENTRY_ONLY = vol.Schema({vol.Optional("config_entry_id"): cv.string})

SCHEMA_GET_NETWORKS = vol.Schema(
    {
        vol.Optional("config_entry_id"): cv.string,
        vol.Optional("scope", default="unknown"): _SCOPES,
        vol.Optional("band", default="all"): _BANDS,
        vol.Optional("min_signal"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
        vol.Optional("quantity", default=DEFAULT_QUANTITY): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=MAX_QUANTITY)
        ),
        vol.Optional("keyword"): cv.string,
        vol.Optional("exclude"): cv.string,
    }
)


def _resolve_entries(
    hass: HomeAssistant, target_entry_id: str | None
) -> list[ConfigEntry]:
    """Return target entries, raising if a named ID is missing/unloaded."""
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
        entry = entries[0]
        if (
            entry.state != ConfigEntryState.LOADED
            or getattr(entry, "runtime_data", None) is None
        ):
            raise HomeAssistantError(
                f"{DOMAIN} entry '{target_entry_id}' is not loaded",
                translation_domain=DOMAIN,
                translation_key="entry_not_loaded",
                translation_placeholders={"entry_id": target_entry_id},
            )
        return entries
    return [
        e
        for e in entries
        if e.state == ConfigEntryState.LOADED
        and getattr(e, "runtime_data", None) is not None
    ]


def _split_terms(raw: str | None) -> list[str]:
    """Split a comma-separated filter into lower-cased terms."""
    if not raw:
        return []
    return [term.strip().lower() for term in raw.split(",") if term.strip()]


def _matches(haystack: str, terms: list[str]) -> bool:
    """Return whether any term appears in the haystack."""
    return any(term in haystack for term in terms)


def _list_from_options(entry: ConfigEntry, option_key: str) -> list[str]:
    raw = entry.options.get(option_key, "")
    return [item.strip() for item in raw.split(",") if item.strip()]


async def _async_write_list(
    hass: HomeAssistant, entry: ConfigEntry, option_key: str, values: list[str]
) -> None:
    """Persist a pattern list back to the entry options."""
    new_options = {**entry.options, option_key: ", ".join(values)}
    hass.config_entries.async_update_entry(entry, options=new_options)


def async_register_services(hass: HomeAssistant) -> None:
    """Register every domain-global service.

    Registered once per Home Assistant session and deliberately never removed
    on unload — removing them per-entry would break them for any remaining
    entry.
    """

    async def _handle_add_ssid(call: ServiceCall) -> None:
        ssid = call.data["ssid"].strip()
        option_key = TARGET_OPTION_KEYS[call.data["target"]]
        for entry in _resolve_entries(hass, call.data.get("config_entry_id")):
            existing = _list_from_options(entry, option_key)
            if ssid in existing:
                continue
            existing.append(ssid)
            await _async_write_list(hass, entry, option_key, existing)

    async def _handle_remove_ssid(call: ServiceCall) -> None:
        ssid = call.data["ssid"].strip()
        option_key = TARGET_OPTION_KEYS[call.data["target"]]
        for entry in _resolve_entries(hass, call.data.get("config_entry_id")):
            existing = _list_from_options(entry, option_key)
            remaining = [item for item in existing if item != ssid]
            if remaining == existing:
                continue  # Not present — a silent success, not an error.
            await _async_write_list(hass, entry, option_key, remaining)

    async def _handle_set_ssids(call: ServiceCall) -> dict[str, Any]:
        new_value = call.data["values"].strip()
        option_key = TARGET_OPTION_KEYS[call.data["target"]]
        old_entries: dict[str, str] = {}
        new_entries: dict[str, str] = {}
        for entry in _resolve_entries(hass, call.data.get("config_entry_id")):
            old_entries[entry.entry_id] = entry.options.get(option_key, "")
            new_options = {**entry.options, option_key: new_value}
            hass.config_entries.async_update_entry(entry, options=new_options)
            new_entries[entry.entry_id] = new_value
        # old/new returned so an automation can undo its own change.
        return {
            "target": call.data["target"],
            "new_entries": new_entries,
            "old_entries": old_entries,
        }

    async def _handle_scan_now(call: ServiceCall) -> None:
        for entry in _resolve_entries(hass, call.data.get("config_entry_id")):
            coordinator: WifiScanCoordinator = entry.runtime_data
            # Explicit request: bypass Pause Polling.
            await coordinator.async_force_refresh()

    async def _handle_clear_last_seen(call: ServiceCall) -> None:
        for entry in _resolve_entries(hass, call.data.get("config_entry_id")):
            coordinator: WifiScanCoordinator = entry.runtime_data
            await coordinator.async_clear_history()

    async def _handle_get_networks(call: ServiceCall) -> dict[str, Any]:
        """Return the current networks with their history annotations.

        Reads the coordinator's own state rather than a sensor's attributes, so
        it keeps working when the passive entities are unavailable, filtered or
        capped.
        """
        entries = _resolve_entries(hass, call.data.get("config_entry_id"))
        scope = call.data["scope"]
        band = call.data["band"]
        min_signal = call.data.get("min_signal")
        quantity = call.data["quantity"]
        keyword = _split_terms(call.data.get("keyword"))
        exclude = _split_terms(call.data.get("exclude"))

        results: list[dict[str, Any]] = []
        for entry in entries:
            coordinator: WifiScanCoordinator = entry.runtime_data
            data = coordinator.data or {}
            networks: dict[str, Any] = data.get("networks", {})
            unknown = set(data.get("unknown_ssids") or [])

            for label, net in networks.items():
                is_unknown = label in unknown
                if scope == "unknown" and not is_unknown:
                    continue
                if scope == "known" and is_unknown:
                    continue
                if band != "all" and net.get("band") != _BAND_LABELS.get(band):
                    continue
                signal = net.get("signal")
                if min_signal is not None and (signal is None or signal < min_signal):
                    continue

                haystack = " ".join(
                    str(part).lower()
                    for part in (label, net.get("bssid"), net.get("band"))
                    if part
                )
                if keyword and not _matches(haystack, keyword):
                    continue
                if exclude and _matches(haystack, exclude):
                    continue

                key = net.get("key")
                results.append(
                    {
                        "entry_id": entry.entry_id,
                        "ssid": label,
                        "bssid": net.get("bssid"),
                        "signal": signal,
                        "channel": net.get("channel"),
                        "band": net.get("band"),
                        "hidden": net.get("hidden"),
                        "ssid_anomaly": net.get("ssid_anomaly"),
                        "mode": net.get("mode"),
                        "known": not is_unknown,
                        "first_seen": _iso(coordinator.first_seen.get(key)),
                        "last_seen": _iso(coordinator.last_seen.get(key)),
                        "visit_count": coordinator.visit_counts.get(key),
                    }
                )

        results.sort(key=lambda n: (n["signal"] is None, -(n["signal"] or 0)))
        total_matched = len(results)
        return {
            "networks": results[:quantity],
            "count": min(quantity, total_matched),
            "total_matched": total_matched,
        }

    hass.services.async_register(
        DOMAIN, SERVICE_ADD_SSID, _handle_add_ssid, schema=SCHEMA_ADD_SSID
    )
    hass.services.async_register(
        DOMAIN, SERVICE_REMOVE_SSID, _handle_remove_ssid, schema=SCHEMA_REMOVE_SSID
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SSIDS,
        _handle_set_ssids,
        schema=SCHEMA_SET_SSIDS,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SCAN_NOW, _handle_scan_now, schema=SCHEMA_ENTRY_ONLY
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CLEAR_LAST_SEEN,
        _handle_clear_last_seen,
        schema=SCHEMA_ENTRY_ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_NETWORKS,
        _handle_get_networks,
        schema=SCHEMA_GET_NETWORKS,
        supports_response=SupportsResponse.ONLY,
    )


def _iso(value: Any) -> str | None:
    """Render a stored datetime as ISO text, tolerating a missing value."""
    return value.isoformat() if hasattr(value, "isoformat") else None
