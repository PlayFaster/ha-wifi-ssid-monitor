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
CONF_DENYLIST_SSIDS = "denylist_ssids"
CONF_LAST_SEEN_TTL_DAYS = "last_seen_ttl_days"
CONF_STOP_POLLING = "stop_polling"

# Signal threshold — percentage (0-100). Replaces CONF_PROXIMITY_RSSI_THRESHOLD,
# which stored a negative dBm value. Migrated once in async_setup_entry.
CONF_PROXIMITY_SIGNAL_THRESHOLD = "proximity_signal_threshold"
LEGACY_CONF_PROXIMITY_RSSI_THRESHOLD = "proximity_rssi_threshold"
CONF_PROXIMITY_RSSI_THRESHOLD = LEGACY_CONF_PROXIMITY_RSSI_THRESHOLD

# Band show/hide switches. Replace the CONF_SCAN_BANDS enum ("all"/"2.4"/"5"),
# which is migrated once in async_setup_entry.
CONF_SHOW_24GHZ = "show_24ghz"
CONF_SHOW_5GHZ = "show_5ghz"
CONF_SHOW_6GHZ = "show_6ghz"
LEGACY_CONF_SCAN_BANDS = "scan_bands"
CONF_SCAN_BANDS = LEGACY_CONF_SCAN_BANDS

DEFAULT_INCLUDE_HIDDEN = True
DEFAULT_PROXIMITY_SIGNAL_THRESHOLD = 80
DEFAULT_PROXIMITY_RSSI_THRESHOLD = -60
DEFAULT_SCAN_BANDS = "all"
DEFAULT_LAST_SEEN_TTL_DAYS = 90
DEFAULT_SCAN_INTERVAL = 600
DEFAULT_SHOW_BAND = True
DEFAULT_STOP_POLLING = False

# Band labels. Kept as display strings because they are surfaced in attributes.
BAND_24 = "2.4 GHz"
BAND_5 = "5 GHz"
BAND_6 = "6 GHz"

HIDDEN_FALLBACK_LABEL = "[hidden]"
HIDDEN_KEY_PREFIX = "hidden:"
NO_NETWORKS_SENTINEL = "None Detected"

# Options that are read fresh on every poll (or applied directly by a control
# entity) and therefore must NOT trigger a config-entry reload. Anything outside
# this set reloads, so a future structural option cannot silently default to
# live. See dev_standards section 9.
LIVE_OPTION_KEYS: frozenset[str] = frozenset(
    {
        CONF_SCAN_INTERVAL,
        CONF_KNOWN_SSIDS,
        CONF_DENYLIST_SSIDS,
        CONF_INCLUDE_HIDDEN,
        CONF_LAST_SEEN_TTL_DAYS,
        CONF_PROXIMITY_SIGNAL_THRESHOLD,
        CONF_SHOW_24GHZ,
        CONF_SHOW_5GHZ,
        CONF_SHOW_6GHZ,
        CONF_STOP_POLLING,
    }
)

# Resilience.
FETCH_STRIKE_LIMIT = 3
HEALTH_DRIFT_STRIKE_LIMIT = 3
HEALTH_STARTUP_GRACE_SCANS = 2

# A known network counts as "established" (and so is eligible for the
# known-network canary check) once it has been seen in this many scans. Derived
# from the existing visit-count history rather than a dedicated baseline store.
CANARY_MIN_VISITS = 5

# Bounds on history growth, on top of the user-facing TTL.
HISTORY_MAX_ENTRIES = 2000

# Cap on the network list carried as an entity attribute. Beyond this, use the
# get_networks action.
NETWORK_ATTR_MAX = 25

# Cap on new-network bus events emitted in a single poll cycle. Excess is
# counted and logged, never silently dropped.
NEW_NETWORK_EVENT_MAX_PER_CYCLE = 10

EVENT_NEW_NETWORK = f"{DOMAIN}_new_network"

# Store schema version, shared by all three stores.
STORAGE_VERSION = 1

# Service names.
SERVICE_ADD_SSID = "add_ssid"
SERVICE_REMOVE_SSID = "remove_ssid"
SERVICE_SET_SSIDS = "set_ssids"
SERVICE_SCAN_NOW = "scan_now"
SERVICE_CLEAR_LAST_SEEN = "clear_last_seen"
SERVICE_GET_NETWORKS = "get_networks"

# Targets for the list-management services.
TARGET_KNOWN = "known"
TARGET_DENYLIST = "denylist"
TARGET_OPTION_KEYS = {
    TARGET_KNOWN: CONF_KNOWN_SSIDS,
    TARGET_DENYLIST: CONF_DENYLIST_SSIDS,
}

# Repair issue keys.
ISSUE_SUPERVISOR_UNAVAILABLE = "supervisor_unavailable"
ISSUE_INTERFACE_MISSING = "interface_missing"
ISSUE_SIGNAL_FORMAT_CHANGED = "signal_format_changed"


def last_seen_storage_key(entry_id: str) -> str:
    """Build the ``.storage`` key for an entry's last-seen history."""
    return f"{DOMAIN}.{entry_id}.last_seen"


def first_seen_storage_key(entry_id: str) -> str:
    """Build the ``.storage`` key for an entry's first-seen history."""
    return f"{DOMAIN}.{entry_id}.first_seen"


def visit_counts_storage_key(entry_id: str) -> str:
    """Build the ``.storage`` key for an entry's visit-count history."""
    return f"{DOMAIN}.{entry_id}.visit_counts"


def all_storage_keys(entry_id: str) -> tuple[str, ...]:
    """Return every ``.storage`` key this integration writes for an entry.

    Used by ``async_remove_entry`` so the delete side cannot drift from the
    write side — both build keys from the helpers above.
    """
    return (
        last_seen_storage_key(entry_id),
        first_seen_storage_key(entry_id),
        visit_counts_storage_key(entry_id),
    )
