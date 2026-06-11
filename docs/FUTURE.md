# Future Roadmap: WiFi SSID Monitor

This document tracks what was planned, what has been delivered, and what new directions are available now that v1.6.0 is in place.

---

## ✅ Delivered in v1.5.0

All of the following items were on the original roadmap and have been implemented.

| Feature | Where it landed |
| :-- | :-- |
| **Signal Strength (RSSI) Tracking** | `signal_strengths` dict attribute on `count` and `unknown_count` sensors; per-SSID dBm values sourced from the Supervisor API. |
| **Frequency & Band Identification** | `bands` dict attribute on both count sensors; computed from channel number via `_channel_to_band()` (1–14 → 2.4 GHz, 36–177 → 5 GHz). |
| **Pattern Matching (Wildcards)** | Known SSID matching uses `fnmatch` — `Guest_*`, `IoT_?`, etc. are all valid. Backward-compatible with exact-match lists. |
| **Hidden Network Management** | `include_hidden` toggle in the options flow. When disabled, APs without a broadcasted SSID are filtered before any counting occurs. |
| **"Add to Known" Service** | `wifi_ssid_monitor.add_known_ssid` — appends to the known list and triggers an immediate re-scan via the update listener. Documented in `services.yaml`. |
| **Manual Scan Button** | `button.scan_now` — calls `coordinator.async_refresh()` on press. No interval constraint. |
| **"Last Seen" Tracking** | In-memory `last_seen` dict (SSID → datetime) exposed as ISO timestamps in `unknown_count` attributes. Populated each scan cycle. |
| **Proximity Alerts** | `binary_sensor.proximity_alert` — fires when `strongest_unknown_rssi` meets or exceeds a configurable threshold (default −60 dBm). Threshold and RSSI both exposed as attributes. |

---

## ✅ Delivered in v1.6.0

All of the following items were on the v1.5.0 new-opportunities list and have been implemented.

| Feature | Where it landed |
| :-- | :-- |
| **"Remove from Known" Service** | `wifi_ssid_monitor.remove_known_ssid` — removes an exact SSID or pattern from the known list. Silent success if not found. Triggers an immediate re-scan when the list changes. |
| **Strongest Unknown SSID Name Sensor** | `sensor.strongest_unknown_ssid` — state is the SSID name of the unknown network with the strongest signal. Companion to the existing `proximity_alert` binary sensor. State is `unknown` when no unknown networks are visible. |
| **Persistent "Last Seen" Storage** | `_last_seen` dict is now backed by HA's `Store` (`.storage/wifi_ssid_monitor.<entry_id>.last_seen`). Timestamps survive HA restarts. Store is cleaned up when the integration entry is deleted. |
| **Auto-Expire Stale "Last Seen" Entries** | Configurable TTL in the options flow (0–366 days; 0 = keep forever; default 90 days). Applied on each successful scan before saving to the Store. |
| **Band Filter Option** | `scan_bands` option (`all` / `2.4` / `5`) in the options flow. Filters all scan results — counts, attributes, and known-network matching — not just band display. APs with an undetermined band are excluded when a filter is active (strict mode). |
| **SSID Denylist** | `denylist_ssids` option in the options flow. Comma-separated list of SSIDs or `fnmatch` patterns that are always counted as unknown even if they match the known list. The denylist overrides the known list. |

---

## 🔜 Remaining Original Roadmap Items

These items were on the original list but have not yet been implemented.

### Channel Crowding Map

**Original idea:** Identify which WiFi channels are most congested to help optimise home router settings.

**Assessment:** The data is available (channel per AP in `network_map`), so a channel-frequency histogram could be computed in the coordinator. The harder problem is the entity model — there is no clean HA entity type for a map of `{channel: count}`. This would surface best as a sensor attribute (easy) or as a template sensor the user builds themselves. Low user demand relative to effort; defer unless requested.

---

### BSSID (MAC Address) Support

**Original idea:** Track unique BSSIDs to prevent SSID spoofing and enable a more reliable "known list."

**Assessment:** Still blocked on API uncertainty — it is unclear whether the Supervisor `/accesspoints` endpoint returns BSSID data. Needs investigation against a real HAOS device. If the field is available, the implementation path is straightforward: extend `network_map`, add BSSID to the known-list matching logic, and update the config flow. Worth re-examining in a future session with a live device.

---

### "First Seen" Events

**Original idea:** Fire a specific HA event the very first time a new hardware BSSID is detected.

**Assessment (updated for v1.6.0):** The original framing required BSSID tracking (still unresolved). However, now that persistent `Store` storage is in place, the simpler SSID-level variant — "fire an event the first time this SSID name has ever been seen across all restarts" — is directly feasible without BSSID. See "First Seen Timestamps" in the v1.6.0 opportunities section below, which is a prerequisite. The BSSID-level variant (detecting the same physical device under a renamed SSID) remains blocked on the API question.

---

### Multi-Interface Support

**Original idea:** Aggregate results from multiple WiFi cards simultaneously in a single integration instance.

**Assessment:** The integration already supports multiple independent config entries, one per interface. A user with two WiFi adapters can install the integration twice and get separate entity sets for each. True aggregation into a single entity set would require significant rework of the coordinator and entity model. Document the "multiple entries" workaround clearly in the README instead.

---

### Hardware Health Monitoring

**Original idea:** Diagnostic sensor for WiFi adapter health; alert if the adapter stalls.

**Assessment:** Requires the Supervisor API to expose adapter health status, which it may not. If the adapter stalls, the existing 3-strike resilience will surface the problem via the Repairs panel after 4 consecutive failures. Additional health monitoring on top of this is low priority.

---

### System Role Attribute

**Original idea:** Re-integrate "System Role" logic from the original script.

**Assessment:** The original script context is no longer available and the value to HA users is unclear. Removed from active consideration unless a concrete use case is identified.

---

## 💡 New Opportunities Unlocked by v1.5.0

These items were identified after v1.5.0 and have not yet been implemented.

---

### SSID Appearance / Disappearance Events

**Difficulty:** Medium
**Benefit:** High — fire `wifi_ssid_monitor.ssid_appeared` and `wifi_ssid_monitor.ssid_disappeared` HA events by diffing the current scan against the previous one. Users can automate on these directly without needing a binary sensor. Especially useful for presence-detection use cases (e.g., "notify me when the IoT device hotspot disappears — it may have been stolen").

**Implementation:** Compare `set(current_ssids)` with `set(previous_ssids)` in the coordinator after each scan; fire events for diffs via `hass.bus.async_fire`. The previous scan set can be derived from `coordinator.data` at the start of each `_async_update_data` call before the new data is returned.

---

### Proximity Alert Hysteresis

**Difficulty:** Medium
**Benefit:** Medium — if a mobile device sits right at the threshold (e.g., −61/−59 dBm alternating), the proximity sensor will flap on every scan. A configurable hysteresis band (e.g., "must drop 5 dBm below threshold to turn off") prevents this. Requires tracking the previous `is_on` state and applying upper/lower bounds separately.

---

### Per-SSID Presence Binary Sensors

**Difficulty:** Hard
**Benefit:** High (for the right users) — auto-create a binary sensor for each SSID in the known list, showing whether it is currently visible. Enables direct "is my work laptop nearby?" automations without template sensors. Requires dynamic entity creation and teardown when the known list changes, which is significantly more complex than the current static entity model.

---

## 💡 New Opportunities Unlocked by v1.6.0

Now that persistent storage, band filtering, the denylist, and the remove service are all in place, another tier of useful features has become feasible.

---

### "First Seen" Persistent Timestamps

**Difficulty:** Easy
**Benefit:** High — track the date each SSID was _first ever_ detected across all restarts. Stored in the same `Store` as `last_seen` (as a second dict or a combined record per SSID). Exposed as a `first_seen` attribute on `unknown_count` alongside the existing `last_seen` attribute.

**Why it matters:** "Last seen 2 minutes ago" tells you something is nearby now. "First seen 3 weeks ago" tells you it has been parked in range for weeks — a very different threat profile. Together, `first_seen` and `last_seen` give the user a full timeline without requiring BSSID support.

**Note:** This directly enables the SSID-level variant of the "First Seen Events" original roadmap item (see above). If `first_seen` is stored, firing `wifi_ssid_monitor.ssid_first_detected` when an SSID has no prior `first_seen` record is a trivial addition.

---

### Unknown SSID Visit Count

**Difficulty:** Easy
**Benefit:** Medium-high — track how many scan cycles each SSID has been observed (total, not consecutive). Stored persistently alongside `last_seen`. Exposed as a `visit_counts` attribute on `unknown_count`.

**Why it matters:** Signal strength tells you proximity; visit count tells you persistence. A network at −70 dBm seen 200 times is more significant than one at −50 dBm seen once. This lets users write automations like "alert only if an unknown network has been seen more than 5 times" — filtering out drive-by hotspots without requiring a complex time-window calculation.

**Implementation:** Increment `_visit_counts[ssid]` for each SSID present in a successful scan. Persist in the same Store as `last_seen`, or in a second Store key.

---

### Dedicated Strongest Unknown RSSI Sensor

**Difficulty:** Easy
**Benefit:** Medium — `strongest_unknown_rssi` is currently exposed only as an attribute of `binary_sensor.proximity_alert`. A dedicated `sensor.strongest_unknown_rssi` with `SensorDeviceClass.SIGNAL_STRENGTH` and `unit_of_measurement=dBm` would allow users to plot the value on HA history graphs natively and use it in numeric conditions in automations without attribute extraction.

**Implementation:** Add a new `WifiSensorEntityDescription` entry with `key="strongest_unknown_rssi"`, `device_class=SensorDeviceClass.SIGNAL_STRENGTH`, `native_unit_of_measurement="dBm"`, and `value_fn=lambda data: data.get("strongest_unknown_rssi")`.

---

### `scan_now` Service — `wifi_ssid_monitor.scan_now`

**Difficulty:** Easy
**Benefit:** Medium — the existing `button.scan_now` triggers an immediate scan but buttons are UI-first. Calling a button from an automation requires `homeassistant.press` on a specific entity ID. A dedicated `wifi_ssid_monitor.scan_now` service with an optional `config_entry_id` field makes automation-triggered scans cleaner and consistent with the other services in this integration.

**Implementation:** Register in `async_setup` alongside the other services. Handler calls `coordinator.async_refresh()` for the target entry or all entries.

---

### Clear Last Seen History Service — `wifi_ssid_monitor.clear_last_seen`

**Difficulty:** Easy
**Benefit:** Medium — clears `_last_seen` (and, if implemented, `first_seen` and `visit_counts`) for one or all entries and saves the empty state to the Store. Useful when relocating, after a significant network change, or for a deliberate monitoring reset without removing and re-adding the integration entry. Optional `config_entry_id` target.

---

### Set Known SSIDs Service — `wifi_ssid_monitor.set_known_ssids`

**Difficulty:** Easy
**Benefit:** Medium — replaces the entire known list for an entry in a single call, rather than building it up through individual `add_known_ssid` calls. Enables backup/restore patterns (store the list in an input_text helper, restore it via automation) and bulk management from scripts. Should return the previous list as service response data to enable round-trip backup.

---

## Version Control

- **v1.0.1** (2026-04-01) - Created.
- **v1.1.0** (2026-06-02) - Major rewrite. Marked v1.5.0 delivered items. Reassessed remaining original items. Added new opportunity section based on v1.5.0 capabilities.
- **v1.2.0** (2026-06-11) - Marked v1.6.0 delivered items. Updated "First Seen Events" assessment to reflect that SSID-level first_seen is now feasible with persistent storage. Added new opportunity section based on v1.6.0 capabilities.
