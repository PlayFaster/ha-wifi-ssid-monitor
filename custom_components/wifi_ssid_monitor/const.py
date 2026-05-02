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
