"""API for WiFi SSID Monitor."""

import logging
import os
from typing import Any

import aiohttp
from aiohttp import ClientTimeout

_LOGGER = logging.getLogger(__name__)

_SUPERVISOR_BASE_URL = "http://supervisor"


class WifiScanError(Exception):
    """Raised when the WiFi SSID Monitor fails."""


class WifiScanAPI:
    """Async wrapper for the Supervisor Network API."""

    def __init__(self, session: aiohttp.ClientSession, interface: str):
        """Initialize the API."""
        self.session = session
        self.interface = interface
        self.token = os.environ.get("SUPERVISOR_TOKEN")

    async def validate(self) -> bool:
        """Validate the API connection."""
        if not self.token:
            raise WifiScanError("SUPERVISOR_TOKEN not found")
        await self.get_access_points()
        return True

    async def get_access_points(self) -> list[dict[str, Any]]:
        """Fetch access points from the Supervisor API."""
        if not self.token:
            _LOGGER.error("SUPERVISOR_TOKEN not found in environment")
            raise WifiScanError("SUPERVISOR_TOKEN not found")

        url = f"{_SUPERVISOR_BASE_URL}/network/interface/{self.interface}/accesspoints"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        status = 200
        res_data = {}
        try:
            async with self.session.get(
                url, headers=headers, timeout=ClientTimeout(total=30)
            ) as response:
                status = response.status
                if status == 200:
                    try:
                        res_data = await response.json()
                    except (aiohttp.ContentTypeError, ValueError) as e:
                        _LOGGER.error("Invalid JSON response from API: %s", e)
                        raise WifiScanError(f"Invalid API response: {e}") from e
                else:
                    text = await response.text()
                    _LOGGER.error(
                        "Failed to fetch access points: %s - %s", status, text
                    )
        except WifiScanError:
            # Re-raise our custom errors without wrapping
            raise
        except aiohttp.ClientError as e:
            _LOGGER.error("Connection error fetching access points: %s", e)
            raise WifiScanError(f"Connection error: {e}") from e
        except Exception as e:
            _LOGGER.error("Unexpected error fetching access points: %s", e)
            raise WifiScanError(f"Unexpected error: {e}") from e

        if status != 200:
            raise WifiScanError(f"API returned status {status}")

        data_block = res_data.get("data") or {}
        access_points: list[dict[str, Any]] = data_block.get("accesspoints", [])
        return access_points

    async def get_interfaces(self) -> list[str]:
        """Fetch all network interfaces and return WiFi ones."""
        if not self.token:
            _LOGGER.error("SUPERVISOR_TOKEN not found in environment")
            raise WifiScanError("SUPERVISOR_TOKEN not found")

        url = f"{_SUPERVISOR_BASE_URL}/network/info"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        status = 200
        res_data = {}
        try:
            async with self.session.get(
                url, headers=headers, timeout=ClientTimeout(total=30)
            ) as response:
                status = response.status
                if status == 200:
                    try:
                        res_data = await response.json()
                    except (aiohttp.ContentTypeError, ValueError) as e:
                        _LOGGER.error("Invalid JSON response from API: %s", e)
                        raise WifiScanError(f"Invalid API response: {e}") from e
                else:
                    _LOGGER.error("Failed to fetch network info: %s", status)
        except WifiScanError:
            # Re-raise our custom errors without wrapping
            raise
        except aiohttp.ClientError as e:
            _LOGGER.error("Connection error fetching interfaces: %s", e)
            raise WifiScanError(f"Connection error: {e}") from e
        except Exception as e:
            _LOGGER.error("Unexpected error fetching interfaces: %s", e)
            raise WifiScanError(f"Unexpected error: {e}") from e

        if status != 200:
            raise WifiScanError(f"API returned status {status}")

        data_block = res_data.get("data") or {}
        interfaces = data_block.get("interfaces", [])

        # Filter for wireless interfaces
        return [
            iface.get("interface", "")
            for iface in interfaces
            if iface.get("type") == "wifi" and iface.get("interface")
        ]
