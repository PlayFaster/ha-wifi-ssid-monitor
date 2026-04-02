"""DataUpdateCoordinator for WiFi SSID Monitor integration."""

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import WifiScanAPI, WifiScanError
from .const import CONF_KNOWN_SSIDS, CONF_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class WifiScanCoordinator(DataUpdateCoordinator):
    """Class to manage fetching WiFi SSID Monitor data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: WifiScanAPI):
        """Initialize the coordinator."""
        self.api = api
        self.entry = entry

        scan_interval = entry.options.get(CONF_SCAN_INTERVAL, 600)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{entry.title} Data",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self):
        """Fetch data from API."""
        last_error = None
        for attempt in range(2):
            try:
                access_points = await self.api.get_access_points()

                all_ssids = sorted(
                    list({ap["ssid"] for ap in access_points if "ssid" in ap})
                )
                
                # Build a structured map for future-proofing (RSSI, Channel, etc.)
                network_map = {
                    ap["ssid"]: {
                        "rssi": ap.get("signal"),
                        "channel": ap.get("channel"),
                    }
                    for ap in access_points if "ssid" in ap
                }

                known_networks_str = self.entry.options.get(CONF_KNOWN_SSIDS, "")
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

            except WifiScanError as err:
                last_error = err
                if attempt == 0:
                    _LOGGER.warning(
                        "Fetch failed: %s. Retrying in 10 seconds...",
                        err,
                    )
                    await asyncio.sleep(10)
                else:
                    _LOGGER.error("Second fetch attempt failed: %s", err)

        raise UpdateFailed(f"Communication error: {last_error}")
