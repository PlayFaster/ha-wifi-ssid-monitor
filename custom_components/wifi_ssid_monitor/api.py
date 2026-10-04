"""API for WiFi SSID Monitor."""

from collections.abc import Mapping
import logging
import os
import re
from typing import Any

import aiohttp
from aiohttp import ClientTimeout

from homeassistant.util import dt as dt_util

from .const import API_TIMEOUT_SECONDS

_LOGGER = logging.getLogger(__name__)

_SUPERVISOR_BASE_URL = "http://supervisor"

# Rejection record limits. A non-200 body is capped, and a payload key name is
# listed only where it looks like a field name: under payload drift a payload
# keyed by SSID would otherwise put SSIDs in the record.
_REJECTION_TEXT_CAP = 500
_FIELD_NAME_RE = re.compile(r"[a-z0-9_]{1,32}")
_MAC_REDACTION = "[REDACTED_MAC]"

# A MAC inside free text, in colon, dash or dotted form. Anchored on hex
# boundaries so a UUID, a hash or a timestamp is not altered.
_MAC_IN_TEXT_RE = re.compile(
    r"(?<![0-9A-Fa-f])"
    r"(?:(?:[0-9A-Fa-f]{2}([:-]))(?:[0-9A-Fa-f]{2}\1){4}[0-9A-Fa-f]{2}"
    r"|(?:[0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4})"
    r"(?![0-9A-Fa-f])"
)


def _scrub_macs(text: str) -> str:
    """Replace every MAC-shaped substring of free text."""
    return _MAC_IN_TEXT_RE.sub(_MAC_REDACTION, text)


def _content_type(response: Any) -> str | None:
    """Read the content type from a response, tolerating a response without one."""
    headers = getattr(response, "headers", None)
    if not isinstance(headers, Mapping):
        return None
    value = headers.get("Content-Type")
    return value if isinstance(value, str) else None


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
        # The most recent rejected scan response, for the diagnostics download:
        # structure only, never access-point data. Cleared by the next response
        # that carries an access-point list.
        self.last_rejection: dict[str, Any] | None = None

    def _record_rejection(
        self,
        status: int,
        failure_class: str,
        content_type: str | None,
        text: str | None = None,
        data_block: Any = None,
    ) -> None:
        """Retain the structure of a rejected response.

        ``text`` is passed only where the body was read, and ``data_block`` only
        where a JSON object parsed.
        """
        record: dict[str, Any] = {
            "http_status": status,
            "failure_class": failure_class,
            "recorded_at": dt_util.utcnow().isoformat(),
            "content_type": content_type,
        }
        if text is not None:
            record["text_length"] = len(text)
            record["text"] = _scrub_macs(text)[:_REJECTION_TEXT_CAP]
        if isinstance(data_block, dict) and data_block:
            names = sorted(k for k in data_block if isinstance(k, str))
            listed = [name for name in names if _FIELD_NAME_RE.fullmatch(name)]
            record["key_names"] = listed
            record["other_key_count"] = len(data_block) - len(listed)
        self.last_rejection = record

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
        content_type: str | None = None
        try:
            async with self.session.get(
                url, headers=headers, timeout=ClientTimeout(total=API_TIMEOUT_SECONDS)
            ) as response:
                status = response.status
                content_type = _content_type(response)
                if status == 200:
                    self.last_interface_present = True
                    try:
                        res_data = await response.json()
                    except (aiohttp.ContentTypeError, ValueError) as e:
                        _LOGGER.error("Invalid JSON response from API: %s", e)
                        self._record_rejection(status, "invalid_json", content_type)
                        raise WifiScanError(f"Invalid API response: {e}") from e
                else:
                    if status in (400, 404):
                        self.last_interface_present = False
                    text = await response.text()
                    _LOGGER.error(
                        "Failed to fetch access points: %s - %s", status, text
                    )
                    self._record_rejection(status, "http_error", content_type, text)
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

        # A JSON array or scalar with HTTP 200 would make `.get` raise an
        # AttributeError here, outside the try above, bypassing the
        # WifiScanError wrapping every other failure mode goes through. Treat
        # it as the payload-drift it is: no AP list, which the health check
        # turns into a finding.
        data_block = res_data.get("data") if isinstance(res_data, dict) else None
        if not isinstance(data_block, dict):
            data_block = {}
        raw_aps = data_block.get("accesspoints")
        if not isinstance(raw_aps, list):
            self.last_response_had_ap_key = False
            self._record_rejection(
                status, "missing_ap_key", content_type, data_block=data_block
            )
            _LOGGER.debug(
                "Supervisor response carried no 'accesspoints' list (keys: %s)",
                sorted(data_block),
            )
            return []
        self.last_response_had_ap_key = True
        self.last_rejection = None
        access_points: list[dict[str, Any]] = raw_aps
        # One-off shape capture for support: the Supervisor's AccessPoint model
        # is not versioned, so the raw key set is the only evidence of drift.
        #
        # The key set, never the values. dev_standards Section 20: a log file
        # has no redaction layer and users are routinely asked to paste one
        # into a public issue, so a verbatim access point would publish a
        # neighbour's SSID and BSSID. The keys are what a drift question
        # actually needs; the values never answered it.
        if access_points:
            _LOGGER.debug("raw AP sample keys: %s", sorted(access_points[0]))
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
                url, headers=headers, timeout=ClientTimeout(total=API_TIMEOUT_SECONDS)
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
