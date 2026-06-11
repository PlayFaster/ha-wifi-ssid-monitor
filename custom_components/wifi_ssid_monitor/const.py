"""Constants for the WiFi SSID Monitor integration."""

import json
from pathlib import Path

DOMAIN = "wifi_ssid_monitor"

_manifest = json.loads((Path(__file__).parent / "manifest.json").read_text())
VERSION = _manifest["version"]

DEFAULT_NAME = "WiFi SSID Monitor"

CONF_NAME = "name"
CONF_INTERFACE = "wifi_interface"
CONF_KNOWN_SSIDS = "known_wifi_ids"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_INCLUDE_HIDDEN = "include_hidden"
CONF_PROXIMITY_RSSI_THRESHOLD = "proximity_rssi_threshold"
CONF_SCAN_BANDS = "scan_bands"
CONF_DENYLIST_SSIDS = "denylist_ssids"
CONF_LAST_SEEN_TTL_DAYS = "last_seen_ttl_days"

DEFAULT_INCLUDE_HIDDEN = True
DEFAULT_PROXIMITY_RSSI_THRESHOLD = -60
DEFAULT_SCAN_BANDS = "all"
DEFAULT_LAST_SEEN_TTL_DAYS = 90
