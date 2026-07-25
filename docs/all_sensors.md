# WiFi SSID Monitor Integration - Entity Manifest

This document provides a comprehensive list of all entities currently implemented in the WiFi SSID Monitor integration. It serves as a master reference for debugging, maintenance, and future development.

## Summary

| Sub-Device | Entity Count | Description |
| :-- | :-- | :-- |
| **System** | 6 | Core interface info, health binary sensor, and poll controls. |
| **Monitor** | 12 | WiFi network counters, alerts, threshold controls, and band switches. |
| **Total** | **18** |  |

---

## 1. System Sub-Device (6 Entities, 6 Services)

_Group: `system`_

| Name | Key | Type | Unit | Category | Notes |
| :-- | :-- | :-- | :-- | :-- | :-- | --- |
| Interface | `interface` | Sensor | - | Diagnostic | The network interface being monitored (e.g., `wlan0`). |
| Last Updated | `last_updated` | Sensor | Timestamp | Diagnostic | Timestamp of the last successful scan. |
| Integration Health | `integration_health` | Binary Sensor | - | Diagnostic | **OFF** when operating normally; **ON** if a Supervisor API outage or interface loss occurs. `available = True` unconditionally. |
| Scan Interval | `scan_interval` | Number | min | Config | Range: 1 min – 180 min. Debounced (2 s) before applying. |
| Scan Now | `scan_now` | Button | - | - | Triggers an immediate on-demand scan (`coordinator.async_force_refresh()`). |
| Pause Polling | `stop_polling` | Switch | - | Config | Pauses scheduled polling scans while allowing explicit actions and buttons to fetch. |
| Add SSID | `add_ssid` | Service | — | — | Adds an SSID or pattern to the known or denylist (`target: known | denylist`). Triggers an immediate re-scan. |
| Remove SSID | `remove_ssid` | Service | — | — | Removes an SSID or pattern from the known or denylist (`target: known | denylist`). |
| Set SSIDs | `set_ssids` | Service | — | — | Replaces the entire known or denylist in a single call (`target: known | denylist`). |
| Scan Now | `scan_now` | Service | — | — | Triggers an immediate WiFi scan for one or all integration entries, even while polling is paused. |
| Clear Last Seen | `clear_last_seen` | Service | — | — | Clears all persisted last-seen, first-seen, and visit-count history. Repopulates on the next scan. |
| Get Networks | `get_networks` | Service | — | — | Response action (`SupportsResponse.ONLY`) returning visible networks filtered and sorted by signal strength. |

---

## 2. Monitor Sub-Device (12 Entities)

_Group: `monitor`_

| Name | Key | Type | Unit | Category | Notes |
| :-- | :-- | :-- | :-- | :-- | :-- |
| Total SSID Count | `total_ssid_count` | Sensor | - | - | Total number of access points visible to the interface. |
| Unknown SSID Count | `unknown_ssid_count` | Sensor | - | - | Number of detected networks not in the "Known SSIDs" list. |
| New Networks (24h) | `new_24h` | Sensor | - | Diagnostic | Number of distinct new networks discovered in the last 24 hours. |
| New Network Alert | `new_network_alert` | Binary Sensor | - | - | **ON** if `unknown_ssid_count > 0`. Triggers `mdi:wifi-alert`. |
| Proximity Alert | `proximity_alert` | Binary Sensor | - | - | **ON** if the strongest unknown SSID signal ≥ configured percentage threshold. |
| Strongest Unknown SSID | `strongest_unknown_ssid` | Sensor | - | - | SSID name of the unknown network with the strongest signal. State is `"None Detected"` when no unknown networks are visible. |
| Strongest Unknown Signal | `strongest_unknown_signal` | Sensor | % | - | Signal strength percentage (0–100%) of the closest unknown network. Replaces legacy `strongest_unknown_rssi`. |
| Proximity Signal Threshold | `proximity_signal_threshold` | Number | % | Config | Range: 0–100%. Triggers Proximity Alert when strongest unknown signal meets or exceeds this percentage. |
| Include Hidden Networks | `include_hidden` | Switch | - | Config | Toggle inclusion of non-broadcasting (hidden) WiFi networks (`Hidden-<last4>`). |
| Show 2.4 GHz | `show_24ghz` | Switch | - | Config | Toggle display/counting of 2.4 GHz WiFi networks. |
| Show 5 GHz | `show_5ghz` | Switch | - | Config | Toggle display/counting of 5 GHz WiFi networks. |
| Show 6 GHz | `show_6ghz` | Switch | - | Config | Toggle display/counting of 6 GHz WiFi networks. |

---

## Debugging & Maintenance Reference

### Identity Strategy

- **Base Unique ID**: The unique ID generated during config flow (typically `wifi_ssid_monitor_{interface}`).
- **Entity Unique ID**: `{{base_id}}_{{key}}`.
- **Device Identifiers**: `{{DOMAIN}}_{{entry_id}}`.

### Entity Attributes

The following entities expose additional data in their extra state attributes:

- **Strongest Unknown SSID (`strongest_unknown_ssid`)**:
  - `networks`: List of up to 25 network detail objects (`ssid`, `bssid`, `signal`, `channel`, `band`, `hidden`, `ssid_anomaly`, `mode`, `first_seen`, `last_seen`, `visit_count`).
  - `networks_truncated`: `True` if more than 25 networks were visible.
  - Excluded from recorder database history via `_unrecorded_attributes`.

- **Integration Health (`integration_health`)**:
  - `issues`: List of active health issues (`supervisor_unavailable`, `interface_missing`, `signal_format_changed`).
  - `severity`: Health severity status (`healthy`, `minor`, `serious`).
  - `last_good_update`: Timestamp of last successful API fetch.

### Scan Logic

- **Supervisor API**: The integration queries the Home Assistant Supervisor Network API (`/network/interface/{interface}/accesspoints`).
- **Single-Boundary Parsing**: `parse.py` normalizes raw payloads to 0–100% signal, MHz frequency to channel/band, hidden AP labels (`Hidden-<last4>`), and zero-width SSID anomaly flags.
- **Pattern Matching**: Known SSIDs and denylist patterns match both network keys (SSID/hidden label) and hardware BSSID MAC addresses using `fnmatch`.
- **Debounce**: Interval changes in the UI are held for 2 seconds to allow for multi-step adjustments before being persisted and applied.

### Services

- **`wifi_ssid_monitor.add_ssid`**: Adds an SSID or BSSID pattern to the known or denylist (`target: known|denylist`) and triggers an immediate re-scan.
- **`wifi_ssid_monitor.remove_ssid`**: Removes an SSID or BSSID pattern from the known or denylist (`target: known|denylist`).
- **`wifi_ssid_monitor.set_ssids`**: Replaces the entire known or denylist (`target: known|denylist`) in one call.
- **`wifi_ssid_monitor.scan_now`**: Triggers an immediate scan bypassing pause polling.
- **`wifi_ssid_monitor.clear_last_seen`**: Clears all persisted history.
- **`wifi_ssid_monitor.get_networks`**: Response action returning filtered and sorted network details.

---

## Version Control

- **v1.0.2** (2026-05-05) - Updated.
- **v1.0.3** (2026-06-02) - Added button and proximity alert entities; updated attributes, band detection, and service reference (v1.5.0-dev1).
- **v1.0.4** (2026-06-11) - Added `strongest_unknown_ssid` and `strongest_unknown_rssi` sensors; updated `unknown_count` attributes to include `first_seen` and `visit_counts`; updated scan logic with band filter and denylist; expanded services list (v1.6.0-dev1/dev4).
- **v1.0.5** (2026-06-12) - Updated entity names/keys to match HA runtime (renamed total/unknown counters and new network alert); added service descriptions to System device manifest; removed stale guard bands from value_min_max.md.
- **v1.0.6** (2026-07-23) - Updated manifest to v2.0 overhaul: 18 entities (added Integration Health, Pause Polling, New Networks 24h, Strongest Unknown Signal, Proximity Signal Threshold, Include Hidden, Show 2.4/5/6 GHz switches); updated service actions (add_ssid, remove_ssid, set_ssids, get_networks).
