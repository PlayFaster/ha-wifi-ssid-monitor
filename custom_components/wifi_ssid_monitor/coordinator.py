"""DataUpdateCoordinator for WiFi SSID Monitor integration."""

import asyncio
import fnmatch
import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import WifiScanAPI, WifiScanError
from .const import (
    CONF_INCLUDE_HIDDEN,
    CONF_KNOWN_SSIDS,
    CONF_SCAN_INTERVAL,
    DEFAULT_INCLUDE_HIDDEN,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _channel_to_band(channel: int | None) -> str | None:
    """Return the WiFi band for a given channel number."""
    if channel is None:
        return None
    if 1 <= channel <= 14:
        return "2.4 GHz"
    if 36 <= channel <= 177:
        return "5 GHz"
    return None


class WifiScanCoordinator(DataUpdateCoordinator):
    """Class to manage fetching WiFi SSID Monitor data."""

    _failure_count: int
    last_update_success_time: datetime | None

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, api: WifiScanAPI, version: str
    ) -> None:
        """Initialize the coordinator."""
        self.api = api
        self.entry = entry
        self.version = version
        self.last_known_ssids = entry.options.get(CONF_KNOWN_SSIDS, "")
        self.last_update_success_time = None
        self._failure_count = 0
        self._last_seen: dict[str, datetime] = {}

        scan_interval = entry.options.get(CONF_SCAN_INTERVAL, 600)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{entry.title} Data",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API with resilience and timeout."""
        try:
            # Use standard timeout wrapper (HA Best Practice)
            async with asyncio.timeout(30):
                access_points = await self.api.get_access_points()

            if access_points is None:
                raise WifiScanError("API returned no data")

            # Success: reset failure count and clear any active repair issue
            self._failure_count = 0
            now = dt_util.now()
            self.last_update_success_time = now
            ir.async_delete_issue(self.hass, DOMAIN, "supervisor_unavailable")

            # Optionally filter out hidden networks (APs without an ssid key)
            include_hidden = self.entry.options.get(
                CONF_INCLUDE_HIDDEN, DEFAULT_INCLUDE_HIDDEN
            )
            if not include_hidden:
                access_points = [ap for ap in access_points if "ssid" in ap]
            else:
                hidden_count = sum(1 for ap in access_points if "ssid" not in ap)
                if hidden_count > 0:
                    _LOGGER.debug("Found %d hidden WiFi networks", hidden_count)

            all_ssids = sorted(
                list({ap.get("ssid", "[hidden]") for ap in access_points})
            )

            # Build a structured map with signal, channel, and band
            network_map: dict[str, dict[str, Any]] = {}
            for ap in access_points:
                ssid = ap.get("ssid", "[hidden]")
                channel = ap.get("channel")
                network_map[ssid] = {
                    "rssi": ap.get("signal"),
                    "channel": channel,
                    "band": _channel_to_band(channel),
                }

            # Track last-seen timestamps (in-memory; resets on HA restart)
            for ssid in all_ssids:
                self._last_seen[ssid] = now

            known_networks_str = self.entry.options.get(CONF_KNOWN_SSIDS, "")
            self.last_known_ssids = known_networks_str
            known_patterns = [
                x.strip() for x in known_networks_str.split(",") if x.strip()
            ]
            unknown_ssids = sorted(
                [
                    ssid
                    for ssid in all_ssids
                    if not any(fnmatch.fnmatch(ssid, p) for p in known_patterns)
                ]
            )

            # Strongest RSSI among unknown networks (least-negative = closest)
            unknown_rssi_values = [
                network_map[ssid]["rssi"]
                for ssid in unknown_ssids
                if network_map.get(ssid, {}).get("rssi") is not None
            ]
            strongest_unknown_rssi: int | None = (
                max(unknown_rssi_values) if unknown_rssi_values else None
            )

            return {
                "count": len(all_ssids),
                "ssids": all_ssids,
                "unknown_ssids": unknown_ssids,
                "unknown_count": len(unknown_ssids),
                "interface": self.api.interface,
                "networks": network_map,
                "last_seen": dict(self._last_seen),
                "strongest_unknown_rssi": strongest_unknown_rssi,
            }

        except Exception as err:
            self._failure_count += 1
            # Option D: Hold last known values for up to 3 failures
            if self.data and self._failure_count <= 3:
                _LOGGER.warning(
                    "Error fetching WiFi data (failure %d/3), "
                    "holding last known values: %s",
                    self._failure_count,
                    err,
                )
                result: dict[str, Any] = self.data
                return result

            _LOGGER.error("Failed to fetch WiFi networks: %s", err)
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                "supervisor_unavailable",
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key="supervisor_unavailable",
            )
            raise UpdateFailed(f"Error communicating with API: {err}") from err
