# WiFi SSID Monitor Integration - Entity Manifest

A complete list of the entities and actions this integration creates. It is a maintenance reference: the definitive source for what exists, what it is keyed on, and where its value comes from.

This file is automatically extracted and reconciled directly from entity description code via `.workbench/check_sensor_manifest.py`.

## Device model — one flat device

**This integration creates a single device per config entry.** There are no sub-devices, no `via_device` chain and no group routing: `build_device_info` in `entity.py` returns one `DeviceInfo` keyed on `(DOMAIN, entry.entry_id)`, and every entity delegates to it.

Earlier revisions of this document described a **System** and a **Monitor** sub-device, with a `_Group:_` key on each. **That architecture was never built.** It is recorded here because a reader who saw it would go looking for routing code that does not exist. Sub-device grouping is not on the roadmap either — `dev_standards` §7 is assessed `N/A` for this project, since one host with one adapter and 18 entities does not need it.

The **Key** column below is the `key` field on the entity description. That is not the entity id: Home Assistant derives the entity id from the entity name via `translation_key`, so `key="count"` becomes `sensor.wifi_ssid_monitor_total_ssid_count`. Earlier revisions listed entity-id suffixes in this column, which matched nothing in the source.

For entity `about` attribute notes, see [`about_attribute_list.md`](about_attribute_list.md).

<!-- GENERATED:start -->

| Name | Key | Type | Unit | Category | Notes |
| :-- | :-- | :-- | :-- | :-- | :-- |
| Integration Health | `integration_health` | Binary Sensor | - | Diagnostic | - |
| New Network Alert | `new_network` | Binary Sensor | - | - | - |
| Proximity Alert | `proximity_alert` | Binary Sensor | - | - | - |
| Scan Now | `scan_now` | Button | - | - | - |
| Proximity Signal Threshold | `proximity_signal_threshold` | Number | % | Config | - |
| Scan Interval | `scan_interval` | Number | min | Config | - |
| Total SSID Count | `count` | Sensor | - | - | LTS: `measurement` |
| Interface | `interface` | Sensor | - | Diagnostic | - |
| Last Updated | `last_updated` | Sensor | - | Diagnostic | - |
| New Networks (24h) | `new_24h` | Sensor | - | - | LTS: `measurement` |
| Strongest Unknown Signal | `strongest_unknown_signal` | Sensor | % | - | LTS: `measurement` |
| Strongest Unknown SSID | `strongest_unknown_ssid` | Sensor | - | - | - |
| Unknown SSID Count | `unknown_count` | Sensor | - | - | LTS: `measurement` |
| Include Hidden Networks | `include_hidden` | Switch | - | Config | - |
| Show 2.4 GHz | `show_24ghz` | Switch | - | Config | - |
| Show 5 GHz | `show_5ghz` | Switch | - | Config | - |
| Show 6 GHz | `show_6ghz` | Switch | - | Config | - |
| Pause Polling | `stop_polling` | Switch | - | Config | - |

<!-- GENERATED:end -->

---

## Debugging & Maintenance Reference

### Identity Strategy

- **Base Unique ID**: The unique ID generated during config flow (typically `wifi_ssid_monitor_{interface}`).
- **Entity Unique ID**: `{{base_id}}_{{key}}`.
- **Device Identifiers**: `(DOMAIN, entry_id)` — one device per entry, no sub-devices.

### Entity Attributes

The following entities expose additional data in their extra state attributes:

- **Strongest Unknown SSID (`strongest_unknown_ssid`)**:
  - `networks`: List of up to 25 network detail objects (`ssid`, `bssid`, `signal`, `channel`, `band`, `hidden`, `ssid_anomaly`, `mode`, `first_seen`, `last_seen`, `visit_count`).
  - `networks_truncated`: `True` if more than 25 networks were visible.
  - Excluded from recorder database history via `_unrecorded_attributes`.

- **Integration Health (`integration_health`)**:
  - `issues`: List of active health issues (`conn_error`, `interface_missing`, `signal_format_changed`).
  - `severity`: `minor` or `serious`, or `None` when healthy.
  - `degraded_capabilities`: capabilities currently failing, by key.
  - `drift`: contract/semantic drift findings — a payload that parsed but changed shape.
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
- **v2.0.0** (2026-08-03) - **Corrected the device model.** The document described a System and a Monitor sub-device, each with a `_Group:_` key; no such architecture exists or ever did — `build_device_info` returns one flat `DeviceInfo` and there is no `via_device` or group routing anywhere in the component. Replaced with an explicit statement of the flat model and a note that §7 is `N/A` here, so a reader stops looking for routing code. **The Key column was also wrong throughout**, listing entity-id suffixes (`total_ssid_count`, `unknown_ssid_count`, `new_network_alert`) rather than the description keys (`count`, `unknown_count`, `new_network`); an explanation of how HA derives the entity id from the name is now inline. Regrouped by platform rather than by the fictitious sub-devices, added guard bands and device classes, added the `drift` and `degraded_capabilities` health attributes missing since `[2.0.1-dev7]`, and recorded the single deliberate `about` omission as §14 requires.
- **v1.0.6** (2026-07-23) - Updated manifest to v2.0 overhaul: 18 entities (added Integration Health, Pause Polling, New Networks 24h, Strongest Unknown Signal, Proximity Signal Threshold, Include Hidden, Show 2.4/5/6 GHz switches); updated service actions (add_ssid, remove_ssid, set_ssids, get_networks).
