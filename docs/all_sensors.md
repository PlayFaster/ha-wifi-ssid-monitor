# WiFi SSID Monitor Integration - Entity Manifest

This document provides a comprehensive list of all entities currently implemented in the WiFi SSID Monitor integration. It serves as a master reference for debugging, maintenance, and future development.

## Summary

| Sub-Device  | Entity Count | Description                                          |
| :---------- | :----------- | :--------------------------------------------------- |
| **System**  | 3            | Core interface info and global integration settings. |
| **Monitor** | 3            | WiFi network counters and unknown network detection. |
| **Total**   | **6**        |                                                      |

---

## 1. System Sub-Device (3 Entities)

_Group: `system`_

| Name | Key | Type | Unit | Category | Notes |
| :-- | :-- | :-- | :-- | :-- | :-- |
| Interface | `interface` | Sensor | - | Diagnostic | The network interface being monitored (e.g., `wlan0`). |
| Last Updated | `last_updated` | Sensor | Timestamp | Diagnostic | Timestamp of the last successful scan. |
| Scan Interval | `scan_interval` | Number | min | Config | Range: 1min - 180min. Debounced (2s) before applying. |

---

## 2. Monitor Sub-Device (3 Entities)

_Group: `monitor`_

| Name | Key | Type | Unit | Category | Notes |
| :-- | :-- | :-- | :-- | :-- | :-- |
| Total WiFi Networks | `count` | Sensor | - | - | Total number of access points visible to the interface. |
| Unknown WiFi Networks | `unknown_count` | Sensor | - | - | Number of detected networks not in the "Known SSIDs" list. |
| New WiFi Network Detected | `new_network` | Binary | - | - | **ON** if `unknown_count > 0`. Triggers `mdi:wifi-alert`. |

---

## Debugging & Maintenance Reference

### Identity Strategy

- **Base Unique ID**: The unique ID generated during config flow (typically `wifi_ssid_monitor_{interface}`).
- **Entity Unique ID**: `{{base_id}}_{{key}}`.
- **Device Identifiers**: `{{DOMAIN}}_{{entry_id}}`.

### Entity Attributes

The following sensors contain list data in their extra state attributes:

- **Total WiFi Networks (`count`)**:
  - `ssids`: List of all SSIDs detected in the last scan.
- **Unknown WiFi Networks (`unknown_count`)**:
  - `ssids`: List of specific SSIDs flagged as unknown.

### Scan Logic

- **Supervisor API**: The integration queries the Home Assistant Supervisor Network API (`/network/interface/{interface}/accesspoints`).
- **Debounce**: Interval changes in the UI are held for 2 seconds to allow for multi-step adjustments before being persisted and applied.

---

## Version Control

- **v1.0.2** (2026-05-05) - Updated.
