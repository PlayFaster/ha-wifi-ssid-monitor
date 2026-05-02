"""DataUpdateCoordinator for WiFi SSID Monitor integration."""

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import WifiScanAPI
from .const import CONF_KNOWN_SSIDS, CONF_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class WifiScanCoordinator(DataUpdateCoordinator):
    """Class to manage fetching WiFi SSID Monitor data."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, api: WifiScanAPI, version: str
    ):
        """Initialize the coordinator."""
        self.api = api
        self.entry = entry
        self.version = version
        self.last_known_ssids = entry.options.get(CONF_KNOWN_SSIDS, "")
        self.last_update_success_time = None
        self._failure_count = 0

        scan_interval = entry.options.get(CONF_SCAN_INTERVAL, 600)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{entry.title} Data",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self):
        """Fetch data from API with resilience and timeout."""
        try:
            # Use standard timeout wrapper (HA Best Practice)
            async with asyncio.timeout(30):
                access_points = await self.api.get_access_points()

                # Success: reset failure count
                self._failure_count = 0
                self.last_update_success_time = dt_util.now()

                # Defensive: ensure access_points is iterable
                if access_points is None:
                    access_points = []

                # Handle hidden networks (missing SSID)
                hidden_count = sum(1 for ap in access_points if "ssid" not in ap)
                if hidden_count > 0:
                    _LOGGER.debug("Found %d hidden WiFi networks", hidden_count)

                all_ssids = sorted(
                    list({ap.get("ssid", "[hidden]") for ap in access_points})
                )

                # Build a structured map for future-proofing (RSSI, Channel, etc.)
                network_map = {
                    ap.get("ssid", "[hidden]"): {
                        "rssi": ap.get("signal"),
                        "channel": ap.get("channel"),
                    }
                    for ap in access_points
                }

                known_networks_str = self.entry.options.get(CONF_KNOWN_SSIDS, "")
                self.last_known_ssids = known_networks_str
                known_networks = [
                    x.strip() for x in known_networks_str.split(",") if x.strip()
                ]
                unknown_ssids = sorted(
                    [ssid for ssid in all_ssids if ssid not in known_networks]
                )

                return {
                    "count": len(all_ssids),
                    "ssids": all_ssids,
                    "unknown_ssids": unknown_ssids,
                    "unknown_count": len(unknown_ssids),
                    "interface": self.api.interface,
                    "networks": network_map,
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
                return self.data

            _LOGGER.error("Failed to fetch WiFi networks: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
