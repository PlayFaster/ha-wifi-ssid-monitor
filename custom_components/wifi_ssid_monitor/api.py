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
        # Set on every successful fetch. False means the response parsed but
        # carried no ``accesspoints`` key at all — a contract change, which is
        # a different fact from "the key was there and the list was empty".
        # The health checks read this; nothing else should.
        self.last_response_had_ap_key: bool = True
        self.last_interface_present: bool | None = True

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
                    self.last_interface_present = True
                    try:
                        res_data = await response.json()
                    except (aiohttp.ContentTypeError, ValueError) as e:
                        _LOGGER.error("Invalid JSON response from API: %s", e)
                        raise WifiScanError(f"Invalid API response: {e}") from e
                else:
                    if status in (400, 404):
                        self.last_interface_present = False
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
        raw_aps = data_block.get("accesspoints")
        if not isinstance(raw_aps, list):
            self.last_response_had_ap_key = False
            _LOGGER.debug(
                "Supervisor response carried no 'accesspoints' list (keys: %s)",
                sorted(data_block)
                if isinstance(data_block, dict)
                else type(data_block),
            )
            return []
        self.last_response_had_ap_key = True
        access_points: list[dict[str, Any]] = raw_aps
        # One-off shape capture for support: the Supervisor's AccessPoint model
        # is not versioned, so the raw key set is the only evidence of drift.
        if access_points:
            _LOGGER.debug("raw AP sample: %s", access_points[0])
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

        # Filter for wireless interfaces. The Supervisor reports "wifi" on
        # generic-x86-64 but "wireless" on a Raspberry Pi 4 — matching only the
        # former made auto-detection return nothing on Pi hardware, forcing
        # every Pi user to type the interface name manually.
        return [
            iface.get("interface", "")
            for iface in interfaces
            if iface.get("type") in ("wifi", "wireless") and iface.get("interface")
        ]
