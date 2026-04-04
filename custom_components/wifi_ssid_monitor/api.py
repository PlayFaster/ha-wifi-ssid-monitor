"""API for WiFi SSID Monitor."""

import logging
import os

import aiohttp

_LOGGER = logging.getLogger(__name__)


class WifiScanError(Exception):
    """Raised when the WiFi SSID Monitor fails."""


class WifiScanAPI:
    """Async wrapper for the Supervisor Network API."""

    def __init__(self, session: aiohttp.ClientSession, interface: str):
        """Initialize the API."""
        self.session = session
        self.interface = interface
        self.token = os.environ.get("SUPERVISOR_TOKEN")

    async def validate(self):
        """Validate the API connection."""
        if not self.token:
            raise WifiScanError("SUPERVISOR_TOKEN not found")
        await self.get_access_points()
        return True

    async def get_access_points(self):
        """Fetch access points from the Supervisor API."""
        if not self.token:
            _LOGGER.error("SUPERVISOR_TOKEN not found in environment")
            raise WifiScanError("SUPERVISOR_TOKEN not found")

        url = f"http://supervisor/network/interface/{self.interface}/accesspoints"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        try:
            async with self.session.get(url, headers=headers, timeout=30) as response:
                if response.status != 200:
                    text = await response.text()
                    _LOGGER.error(
                        "Failed to fetch access points: %s - %s", response.status, text
                    )
                    raise WifiScanError(f"API returned status {response.status}")

                try:
                    res_data = await response.json()
                except (aiohttp.ContentTypeError, ValueError) as e:
                    _LOGGER.error("Invalid JSON response from API: %s", e)
                    raise WifiScanError(f"Invalid API response: {e}") from e

                data_block = res_data.get("data") or {}
                return data_block.get("accesspoints", [])
        except aiohttp.ClientError as e:
            _LOGGER.error("Connection error fetching access points: %s", e)
            raise WifiScanError(f"Connection error: {e}") from e
        except Exception as e:
            _LOGGER.error("Unexpected error fetching access points: %s", e)
            raise WifiScanError(f"Unexpected error: {e}") from e
