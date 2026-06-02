# WiFi SSID Monitor Integration - Entity Manifest

This document provides a comprehensive list of all entities currently implemented in the WiFi SSID Monitor integration. It serves as a master reference for debugging, maintenance, and future development.

## Summary

| Sub-Device  | Entity Count | Description                                           |
| :---------- | :----------- | :---------------------------------------------------- |
| **System**  | 4            | Core interface info and global integration settings.  |
| **Monitor** | 5            | WiFi network counters, alerts, and on-demand control. |
| **Total**   | **9**        |                                                       |

---

## 1. System Sub-Device (4 Entities)

_Group: `system`_

| Name | Key | Type | Unit | Category | Notes |
| :-- | :-- | :-- | :-- | :-- | :-- |
| Interface | `interface` | Sensor | - | Diagnostic | The network interface being monitored (e.g., `wlan0`). |
| Last Updated | `last_updated` | Sensor | Timestamp | Diagnostic | Timestamp of the last successful scan. |
| Scan Interval | `scan_interval` | Number | min | Config | Range: 1 min – 180 min. Debounced (2 s) before applying. |
| Scan Now | `scan_now` | Button | - | - | Triggers an immediate on-demand scan (`coordinator.async_refresh()`). |

---

## 2. Monitor Sub-Device (5 Entities)

_Group: `monitor`_

| Name | Key | Type | Unit | Category | Notes |
| :-- | :-- | :-- | :-- | :-- | :-- |
| Total WiFi Networks | `count` | Sensor | - | - | Total number of access points visible to the interface. |
| Unknown WiFi Networks | `unknown_count` | Sensor | - | - | Number of detected networks not in the "Known SSIDs" list. |
| New WiFi Network Detected | `new_network` | Binary Sensor | - | - | **ON** if `unknown_count > 0`. Triggers `mdi:wifi-alert`. |
| Proximity Alert | `proximity_alert` | Binary Sensor | - | - | **ON** if the strongest unknown SSID signal ≥ configured RSSI threshold. |

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
  - `last_seen`: Dict of SSID → ISO 8601 timestamp of when each unknown network was last detected. Resets on HA restart.

- **Proximity Alert (`proximity_alert`)**:
  - `strongest_unknown_rssi`: RSSI (dBm) of the closest unknown network, or `null` if no unknown networks are present.
  - `threshold`: The currently configured RSSI threshold (dBm).

### Scan Logic

- **Supervisor API**: The integration queries the Home Assistant Supervisor Network API (`/network/interface/{interface}/accesspoints`).
- **Pattern Matching**: Known SSIDs are matched using `fnmatch` — exact matches and wildcards (e.g., `Guest_*`) are both supported.
- **Band Detection**: Channel numbers are mapped to bands: channels 1–14 → `2.4 GHz`, channels 36–177 → `5 GHz`.
- **Debounce**: Interval changes in the UI are held for 2 seconds to allow for multi-step adjustments before being persisted and applied.

### Service

- **`wifi_ssid_monitor.add_known_ssid`**: Adds an SSID to the known list and triggers an immediate re-scan. Accepts `ssid` (required) and optional `config_entry_id` to target a specific integration entry.

---

## Version Control

- **v1.0.2** (2026-05-05) - Updated.
- **v1.0.3** (2026-06-02) - Added button and proximity alert entities; updated attributes, band detection, and service reference (v1.5.0-dev1).
