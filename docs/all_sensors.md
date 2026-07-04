# WiFi SSID Monitor Integration - Entity Manifest

This document provides a comprehensive list of all entities currently implemented in the WiFi SSID Monitor integration. It serves as a master reference for debugging, maintenance, and future development.

## Summary

| Sub-Device  | Entity Count | Description                                           |
| :---------- | :----------- | :---------------------------------------------------- |
| **System**  | 4            | Core interface info and global integration settings.  |
| **Monitor** | 6            | WiFi network counters, alerts, and on-demand control. |
| **Total**   | **10**       |                                                       |

---

## 1. System Sub-Device (4 Entities, 5 Services)

_Group: `system`_

| Name | Key | Type | Unit | Category | Notes |
| :-- | :-- | :-- | :-- | :-- | :-- |
| Interface | `interface` | Sensor | - | Diagnostic | The network interface being monitored (e.g., `wlan0`). |
| Last Updated | `last_updated` | Sensor | Timestamp | Diagnostic | Timestamp of the last successful scan. |
| Scan Interval | `scan_interval` | Number | min | Config | Range: 1 min – 180 min. Debounced (2 s) before applying. |
| Scan Now | `scan_now` | Button | - | - | Triggers an immediate on-demand scan (`coordinator.async_refresh()`). |
| Add Known Ssid | `add_known_ssid` | Service | — | — | Adds an SSID to the known networks list for one or all integration entries. Triggers an immediate re-scan after the list is updated. |
| Remove Known Ssid | `remove_known_ssid` | Service | — | — | Removes an SSID or pattern from the known networks list for one or all integration entries. |
| Scan Now | `scan_now` | Service | — | — | Triggers an immediate WiFi scan for one or all integration entries. |
| Clear Last Seen | `clear_last_seen` | Service | — | — | Clears all persisted last-seen, first-seen, and visit-count history for one or all integration entries. |
| Set Known Ssids | `set_known_ssids` | Service | — | — | Replaces the entire known networks list for one or all integration entries in a single call. |

---

## 2. Monitor Sub-Device (6 Entities)

_Group: `monitor`_

| Name | Key | Type | Unit | Category | Notes |
| :-- | :-- | :-- | :-- | :-- | :-- |
| Total SSID Count | `total_ssid_count` | Sensor | - | - | Total number of access points visible to the interface. |
| Unknown SSID Count | `unknown_ssid_count` | Sensor | - | - | Number of detected networks not in the "Known SSIDs" list. |
| New Network Alert | `new_network_alert` | Binary Sensor | - | - | **ON** if `unknown_ssid_count > 0`. Triggers `mdi:wifi-alert`. |
| Proximity Alert | `proximity_alert` | Binary Sensor | - | - | **ON** if the strongest unknown SSID signal ≥ configured RSSI threshold. |
| Strongest Unknown SSID | `strongest_unknown_ssid` | Sensor | - | - | SSID name of the unknown network with the strongest signal. State is `unknown` when no unknown networks are visible. |
| Strongest Unknown RSSI | `strongest_unknown_rssi` | Sensor | dBm | - | Signal strength of the strongest unknown network. `SensorDeviceClass.SIGNAL_STRENGTH`. Guard band: −100 to 0 dBm. |

---

## Debugging & Maintenance Reference

### Identity Strategy

- **Base Unique ID**: The unique ID generated during config flow (typically `wifi_ssid_monitor_{interface}`).
- **Entity Unique ID**: `{{base_id}}_{{key}}`.
- **Device Identifiers**: `{{DOMAIN}}_{{entry_id}}`.

### Entity Attributes

The following entities expose additional data in their extra state attributes:

- **Total WiFi Networks (`count`)**:
  - `ssids`: List of all SSIDs detected in the last scan.
  - `signal_strengths`: Dict of SSID → RSSI (dBm) for networks where signal data is available.
  - `bands`: Dict of SSID → band string (`"2.4 GHz"` or `"5 GHz"`) where channel data is available.

- **Unknown WiFi Networks (`unknown_count`)**:
  - `ssids`: List of specific SSIDs flagged as unknown.
  - `signal_strengths`: Dict of SSID → RSSI (dBm) for unknown networks where signal data is available.
  - `bands`: Dict of SSID → band string for unknown networks where channel data is available.
  - `last_seen`: Dict of SSID → ISO 8601 timestamp of when each unknown network was last detected. Persists across HA restarts via `Store`.
  - `first_seen`: Dict of SSID → ISO 8601 timestamp of when each unknown network was first ever detected. Written once; never overwritten. Persists across HA restarts via `Store`.
  - `visit_counts`: Dict of SSID → integer count of how many scan cycles the SSID has been observed. Persists across HA restarts via `Store`.

- **Proximity Alert (`proximity_alert`)**:
  - `strongest_unknown_rssi`: RSSI (dBm) of the closest unknown network, or `null` if no unknown networks are present.
  - `threshold`: The currently configured RSSI threshold (dBm).

### Scan Logic

- **Supervisor API**: The integration queries the Home Assistant Supervisor Network API (`/network/interface/{interface}/accesspoints`).
- **Pattern Matching**: Known SSIDs are matched using `fnmatch` — exact matches and wildcards (e.g., `Guest_*`) are both supported. Case-sensitive.
- **Band Detection**: Channel numbers are mapped to bands: channels 1–14 → `2.4 GHz`, channels 36–177 → `5 GHz`.
- **Band Filter**: The `scan_bands` option (`all` / `2.4` / `5`) restricts scan results globally — counts, attributes, and known-network matching. APs with an undetermined band are excluded when a band filter is active.
- **SSID Denylist**: The `denylist_ssids` option accepts comma-separated `fnmatch` patterns. Matching SSIDs are always treated as unknown, even if they appear in the known list. Denylist takes priority.
- **Debounce**: Interval changes in the UI are held for 2 seconds to allow for multi-step adjustments before being persisted and applied.

### Services

- **`wifi_ssid_monitor.add_known_ssid`**: Adds an SSID to the known list and triggers an immediate re-scan. Accepts `ssid` (required) and optional `config_entry_id`.
- **`wifi_ssid_monitor.remove_known_ssid`**: Removes an exact SSID or pattern from the known list. Silent success if not found. Triggers a re-scan when the list changes. Accepts `ssid` (required) and optional `config_entry_id`.
- **`wifi_ssid_monitor.scan_now`**: Triggers an immediate scan. Accepts optional `config_entry_id`.
- **`wifi_ssid_monitor.clear_last_seen`**: Clears all persisted `last_seen`, `first_seen`, and `visit_count` history. Accepts optional `config_entry_id`.
- **`wifi_ssid_monitor.set_known_ssids`**: Replaces the entire known list in one call. Returns the previous list as service response data. Accepts `known_ssids` (required) and optional `config_entry_id`.

---

## Version Control

- **v1.0.2** (2026-05-05) - Updated.
- **v1.0.3** (2026-06-02) - Added button and proximity alert entities; updated attributes, band detection, and service reference (v1.5.0-dev1).
- **v1.0.4** (2026-06-11) - Added `strongest_unknown_ssid` and `strongest_unknown_rssi` sensors; updated `unknown_count` attributes to include `first_seen` and `visit_counts`; updated scan logic with band filter and denylist; expanded services list (v1.6.0-dev1/dev4).
- **v1.0.5** (2026-06-12) - Updated entity names/keys to match HA runtime (renamed total/unknown counters and new network alert); added service descriptions to System device manifest; removed stale guard bands from value_min_max.md.
