# Future Roadmap: WiFi SSID Monitor

This document tracks what was planned, what has been delivered, and what new directions are available.

---

## ✅ Delivered with v1.6.0, Part 1 (was v1.5.0)

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

## ✅ Delivered with v1.6.0, Part 2 (was v1.6.0)

| Feature | Where it landed |
| :-- | :-- |
| **"Remove from Known" Service** | `wifi_ssid_monitor.remove_known_ssid` — removes an exact SSID or pattern from the known list. Silent success if not found. Triggers an immediate re-scan when the list changes. |
| **Strongest Unknown SSID Name Sensor** | `sensor.strongest_unknown_ssid` — state is the SSID name of the unknown network with the strongest signal. Companion to the existing `proximity_alert` binary sensor. State is `unknown` when no unknown networks are visible. |
| **Persistent "Last Seen" Storage** | `_last_seen` dict is now backed by HA's `Store` (`.storage/wifi_ssid_monitor.<entry_id>.last_seen`). Timestamps survive HA restarts. Store is cleaned up when the integration entry is deleted. |
| **Auto-Expire Stale "Last Seen" Entries** | Configurable TTL in the options flow (0–366 days; 0 = keep forever; default 90 days). Applied on each successful scan before saving to the Store. |
| **Band Filter Option** | `scan_bands` option (`all` / `2.4` / `5`) in the options flow. Filters all scan results — counts, attributes, and known-network matching — not just band display. APs with an undetermined band are excluded when a filter is active (strict mode). |
| **SSID Denylist** | `denylist_ssids` option in the options flow. Comma-separated list of SSIDs or `fnmatch` patterns that are always counted as unknown even if they match the known list. The denylist overrides the known list. |

---

## ✅ Delivered with v1.5.0, Part 3 (was v1.7.0)

| Feature | Where it landed |
| :-- | :-- |
| **"First Seen" Persistent Timestamps** | `_first_seen` dict backed by `Store` (`.storage/wifi_ssid_monitor.<entry_id>.first_seen`). Written once on first detection; never overwritten. Exposed as `first_seen` ISO-timestamp attribute on `unknown_count`. TTL expiry prunes `first_seen` alongside `last_seen`. |
| **Unknown SSID Visit Count** | `_visit_counts` dict backed by `Store` (`.storage/wifi_ssid_monitor.<entry_id>.visit_counts`). Incremented each scan cycle the SSID is present. Exposed as `visit_counts` attribute on `unknown_count`. |
| **Dedicated Strongest Unknown RSSI Sensor** | `sensor.strongest_unknown_rssi` — `SensorDeviceClass.SIGNAL_STRENGTH`, `native_unit_of_measurement="dBm"`. Allows native HA history graphing and numeric automation conditions without attribute extraction. |
| **`scan_now` Service** | `wifi_ssid_monitor.scan_now` — triggers `coordinator.async_refresh()` for one or all entries. Cleaner than pressing `button.scan_now` from an automation; consistent with the other services. |
| **Clear Last Seen History Service** | `wifi_ssid_monitor.clear_last_seen` — silently clears `_last_seen`, `_first_seen`, and `_visit_counts` and saves empty state to all three Stores. Next scheduled scan repopulates from scratch. |
| **Set Known SSIDs Service** | `wifi_ssid_monitor.set_known_ssids` — replaces the entire known list in a single call and returns the previous list per entry as `SupportsResponse.OPTIONAL` service response data. Enables backup/restore automation patterns. |

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

**Assessment (updated for v1.5.0):** The original BSSID-level framing remains blocked on API uncertainty. However, the simpler SSID-level variant is now trivially feasible: `first_seen` timestamps are persistently stored, so the coordinator can fire `wifi_ssid_monitor.ssid_first_detected` whenever it encounters an SSID with no existing `first_seen` record. The only work required is the `hass.bus.async_fire` call at scan time. See "First Detected Events" in the future options section below.

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

## 💡 New Opportunities — Future Options

Now that `first_seen`, `visit_counts`, and the full service suite are in place, a new tier of features is feasible.

---

### "First Detected" Events — `wifi_ssid_monitor.ssid_first_detected`

**Difficulty:** Easy **Benefit:** High — fire an HA event when an SSID is encountered for the first time across all restarts. The `first_seen` Store is already in place; the only addition is a `hass.bus.async_fire` call when the coordinator detects an SSID with no prior `first_seen` record. Users can automate directly on this event (e.g., send a notification, log to a spreadsheet, turn on a warning light). This completes the SSID-level variant of the "First Seen Events" original roadmap item.

---

### Visit Count Threshold Filter

**Difficulty:** Easy **Benefit:** Medium-high — add a configurable options-flow setting (e.g., `min_visit_count`, default 0 = disabled) that excludes SSIDs from the `unknown_count` and all attributes unless they have been seen at least N times. Filters out drive-by hotspots and one-off scan artefacts without requiring the user to write template automation conditions.

---

### SSID Appearance / Disappearance Events

**Difficulty:** Medium **Benefit:** High — fire `wifi_ssid_monitor.ssid_appeared` and `wifi_ssid_monitor.ssid_disappeared` HA events by diffing the current scan against the previous one. Users can automate on these directly without needing a binary sensor. Especially useful for presence-detection use cases (e.g., "notify me when the IoT device hotspot disappears — it may have been stolen").

**Implementation:** Compare `set(current_ssids)` with `set(previous_ssids)` in the coordinator after each scan; fire events for diffs via `hass.bus.async_fire`. The previous scan set can be derived from `coordinator.data` at the start of each `_async_update_data` call before the new data is returned.

---

### Proximity Alert Hysteresis

**Difficulty:** Medium **Benefit:** Medium — if a mobile device sits right at the threshold (e.g., −61/−59 dBm alternating), the proximity sensor will flap on every scan. A configurable hysteresis band (e.g., "must drop 5 dBm below threshold to turn off") prevents this. Requires tracking the previous `is_on` state and applying upper/lower bounds separately.

---

### Case-Insensitive Known SSID Matching

**Difficulty:** Unknown **Benefit:** Medium — currently, known SSID matching (including `fnmatch` patterns) is case-sensitive, matching the behavior of real SSID identifiers. Some routers and devices broadcast the same network name with inconsistent capitalisation (e.g., `MyWiFi` vs `mywifi`), which can cause a network to appear as unknown even when it is in the known list. A configurable option to enable case-insensitive matching (e.g., lowercasing both the scanned SSID and all known patterns before comparison) could reduce false positives in these environments. Implementation complexity is unclear — the main uncertainty is whether `fnmatch` pattern semantics remain correct after lowercasing, particularly for patterns with mixed-case characters.

---

### Per-SSID Presence Binary Sensors

**Difficulty:** Hard **Benefit:** High (for the right users) — auto-create a binary sensor for each SSID in the known list, showing whether it is currently visible. Enables direct "is my work laptop nearby?" automations without template sensors. Requires dynamic entity creation and teardown when the known list changes, which is significantly more complex than the current static entity model.

---

## Version Control

- **v1.0.1** (2026-04-01) - Created.
- **v1.1.0** (2026-06-02) - Major rewrite. Marked v1.5.0 delivered items. Reassessed remaining original items. Added new opportunity section based on v1.5.0 capabilities.
- **v1.2.0** (2026-06-11) - Marked v1.6.0 delivered items. Updated "First Seen Events" assessment. Added new opportunity section based on v1.6.0 capabilities.
- **v1.3.0** (2026-06-11) - Marked v1.7.0 delivered items. Updated "First Seen Events" assessment to reflect first_seen Store is now live. Replaced v1.6.0 opportunity section with v1.7.0 opportunities.
- **v1.4.0** (2026-06-11) - Rebundled: v1.5.0/v1.6.0/v1.7.0 features all ship together as v1.6.0. Renamed delivered sections to Part 1/2/3. Renamed opportunity section to "Future Options".
- **v1.5.0** (2026-06-12) - Added "Case-Insensitive Known SSID Matching" to Future Options.
