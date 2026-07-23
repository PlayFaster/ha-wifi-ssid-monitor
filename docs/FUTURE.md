# Future Roadmap: WiFi SSID Monitor

This document tracks what was planned, what has been delivered, and what new directions are available.

---

## ✅ Delivered with v2.0.0

The v2.0.0 correctness-and-capability release closed three long-standing roadmap items outright, and delivered a fourth in a different (better) form than originally framed.

| Roadmap item | Where it landed |
| :-- | :-- |
| **BSSID (MAC Address) Support** _(was blocked on API uncertainty)_ | **Unblocked and delivered.** The Supervisor `/accesspoints` payload does return `mac`, verified on both Intel and Raspberry Pi hardware. BSSID is now captured in the normalized shape, exposed as `bssid` on the per-network detail and in the `get_networks` response and `new_network` event, and used as the identity for cloaked networks (`Hidden-<last 4 of BSSID>`). `known_wifi_ids` and `denylist_ssids` matching evaluates against **both** the network key and the BSSID, so exact MACs or MAC wildcards (`AA:BB:CC:*`) are valid in either list — the "more reliable known list" the item asked for. |
| **"First Seen" Events** | **Delivered as `wifi_ssid_monitor_new_network`.** Fires once per genuinely-new network, keyed on the persisted history so it **survives restarts**, with the existing set recorded silently as a baseline on first scan (no backlog replay) and a per-cycle rate limit. Payload carries `entry_id`, `key`, `ssid`, `bssid`, `band`, `channel`, `signal`, `hidden`, `ssid_anomaly`, `mode`, and `first_seen`. This supersedes the "First Detected Events" future option, and — because BSSID is now available — it satisfies the original hardware-level framing as well as the SSID-level one. |
| **Hardware Health Monitoring** | **Delivered as the Integration Health self-diagnosis sensor.** A `problem` binary sensor that stays available even when everything else has gone `unavailable`, backed by a check catalogue and three repair issues: `interface_missing` (the adapter/interface is no longer reported — the "adapter stalled" case the item described), `signal_format_changed`, and `supervisor_unavailable`. It also catches the _silent_ failure the original item did not anticipate — a scan that succeeds while the payload shape or units have drifted. Delivered as integration-level health rather than raw adapter telemetry, which the Supervisor API does not expose. |
| **"First Detected" Events** _(future option)_ | Superseded by `wifi_ssid_monitor_new_network` above — the persisted-history keying makes it restart-safe, which the originally-sketched `hass.bus.async_fire`-on-missing-`first_seen` approach would not have been. |

---

**Also delivered in v2.0.0, beyond the roadmap** — these were not on any list but shaped the release: the `parse.py` payload normalization boundary (and the three root-cause bug fixes it enabled: percent signal, frequency→band, `wireless` interface type); per-band **Show 2.4 / 5 / 6 GHz** switches replacing the old single-choice enum; the **Pause Polling** switch with force-refresh; the **`get_networks`** response action; the **New Networks (24h)** LTS sensor; the `ssid_anomaly` flag for control/zero-width/RTL characters in SSIDs; a structural diagnostics sanitizer; coalesced storage writes with a hard entry cap; and `_unrecorded_attributes` across the high-churn attributes.

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

## 💡 New Opportunities — Future Options

With the `parse.py` normalization boundary, BSSID identity, persisted history, the bus event, and the full action suite all in place, the following remain open.

---

### Per-SSID Signal Quality Sensors

**Difficulty:** Hard **Benefit:** High — let the user nominate specific networks (known **or** unknown) and get a dedicated numeric sensor per network, e.g. **"My Home Network Signal Quality"**, so an individual SSID's signal can be graphed and trended over time in its own right rather than being visible only as one row inside the `networks` attribute or a `get_networks` response.

**Why it does not exist today:** the current signal sensors are deliberately _aggregate_ — **Strongest Unknown Signal** tracks whichever unknown network happens to be strongest at that moment, so its history is a composite of different networks over time and cannot answer "how has _this_ network's signal behaved this month?". Per-network signal is present in the attributes, but attributes are unrecorded and are not LTS candidates, so there is no trend series.

**What it needs:**

- **A tracked-SSID list option** — which networks get their own sensor. Should accept the same identity forms the known/denylist already support (SSID, `fnmatch` pattern, or BSSID), so a user can pin a specific radio rather than a name that could be spoofed.
- **Add / remove actions** — `add_tracked_ssid` / `remove_tracked_ssid` / `set_tracked_ssids`, mirroring the existing `add_ssid` / `remove_ssid` / `set_ssids` `target:` pattern, so the list is automatable and not Configure-only.
- **Dynamic entity creation and teardown** — one `sensor` per tracked network, created when added and removed when dropped. This is the same hard problem as _Per-SSID Presence Binary Sensors_ below, and the two should almost certainly be built together on one dynamic-entity mechanism.
- **A defined "no longer present" state** — a tracked network that stops broadcasting must be distinguishable from one that is present but weak. `unknown` (value absent, source healthy) is the correct state per the existing `unknown` vs `unavailable` convention, **not** `0`, which would corrupt the trend with a false floor. A companion `last_seen` attribute and/or a per-network presence binary sensor would make "gone" legible.
- **Stale-entry identification and cleanup** — a way to surface tracked SSIDs that have not been seen for some period (they may have been renamed, or the hardware retired), plus a supported way to prune them. The existing history TTL and the Integration Health check catalogue are the natural places to hang this; a "tracked network not seen for N days" health finding would fit the established pattern.

**Watch out for:** a pattern or wildcard in the tracked list could match many networks at once and spawn an unbounded number of entities — the list should either resolve to a capped set or be restricted to exact identities. And a tracked network whose SSID is spoofed by a second AP would need a rule for which radio the sensor follows (strongest, or the pinned BSSID).

---

### Per-SSID Presence Binary Sensors

**Difficulty:** Hard **Benefit:** High (for the right users) — auto-create a binary sensor for each SSID in the known list, showing whether it is currently visible. Enables direct "is my work laptop nearby?" automations without template sensors. Requires dynamic entity creation and teardown when the known list changes, which is significantly more complex than the current static entity model.

**Note:** this shares its entire hard part — dynamic per-network entity creation, teardown, and a defined "no longer present" state — with _Per-SSID Signal Quality Sensors_ above. If either is built, build the mechanism once and let both ride on it: one tracked-network list producing a presence binary sensor and a signal-quality sensor per entry.

---

### Visit Count Threshold Filter

**Difficulty:** Easy **Benefit:** Medium-high — add a configurable options-flow setting (e.g., `min_visit_count`, default 0 = disabled) that excludes networks from the `unknown_count` and all attributes unless they have been seen at least N times. Filters out drive-by hotspots and one-off scan artifacts without requiring the user to write template automation conditions. The `visit_counts` history that would drive it is already persisted.

---

### SSID Appearance / Disappearance Events

**Difficulty:** Medium **Benefit:** Medium-high — **the "first ever seen" half of this is now delivered** as `wifi_ssid_monitor_new_network`. What remains is the _recurring_ diff: fire events when a previously-known network **re-appears** after an absence, and when a currently-visible one **disappears**. Especially useful for presence-detection use cases (e.g., "notify me when the IoT device hotspot disappears — it may have been stolen").

**Implementation:** compare the current scan's key set against the previous one in the coordinator and fire on the diffs. The previous set is derivable from `coordinator.data` at the start of `_async_update_data`, and the persisted `last_seen` history gives the "how long was it gone?" context the `new_network` event does not need. Should reuse the existing baseline-and-rate-limit machinery so a busy location cannot flood automations.

---

### Proximity Alert Hysteresis

**Difficulty:** Medium **Benefit:** Medium — if a mobile device sits right at the threshold (e.g., 79/81% alternating against an 80% threshold), the proximity sensor will flap on every scan. A configurable hysteresis band (e.g., "must drop 5 percentage points below the threshold to turn off") prevents this. Requires tracking the previous `is_on` state and applying upper/lower bounds separately.

---

### Case-Insensitive Known SSID Matching

**Difficulty:** Unknown **Benefit:** Medium — currently, known SSID matching (including `fnmatch` patterns) is case-sensitive, matching the behavior of real SSID identifiers. Some routers and devices broadcast the same network name with inconsistent capitalization (e.g., `MyWiFi` vs `mywifi`), which can cause a network to appear as unknown even when it is in the known list. A configurable option to enable case-insensitive matching (e.g., lowercasing both the scanned SSID and all known patterns before comparison) could reduce false positives in these environments. Implementation complexity is unclear — the main uncertainty is whether `fnmatch` pattern semantics remain correct after lowercasing, particularly for patterns with mixed-case characters.

---

## 🔜 Remaining Original Roadmap Items

These items were on the original list but have not yet been implemented.

### Channel Crowding Map

**Original idea:** Identify which WiFi channels are most congested to help optimize home router settings.

**Assessment (updated for v2.0.0):** The input data is now materially better — channel is derived reliably from the Supervisor's `frequency` field rather than a `channel` key that never existed, and per-network `channel` and `band` are exposed on the detail attributes and in the `get_networks` response. A histogram is therefore a straightforward coordinator computation. The blocker is unchanged and is presentational: there is no clean HA entity type for a `{channel: count}` map, so it would surface as a sensor attribute or a user-built template sensor. Low demand relative to effort; defer unless requested.

---

### Multi-Interface Support

**Original idea:** Aggregate results from multiple WiFi cards simultaneously in a single integration instance.

**Assessment:** The integration already supports multiple independent config entries, one per interface. A user with two WiFi adapters can install the integration twice and get separate entity sets for each. True aggregation into a single entity set would require significant rework of the coordinator and entity model. Document the "multiple entries" workaround clearly in the README instead.

---

### System Role Attribute

**Original idea:** Re-integrate "System Role" logic from the original script.

**Assessment:** The original script context is no longer available and the value to HA users is unclear. Removed from active consideration unless a concrete use case is identified.

---

## Version Control

- **v1.0.1** (2026-04-01) - Created.
- **v1.1.0** (2026-06-02) - Major rewrite. Marked v1.5.0 delivered items. Reassessed remaining original items. Added new opportunity section based on v1.5.0 capabilities.
- **v1.2.0** (2026-06-11) - Marked v1.6.0 delivered items. Updated "First Seen Events" assessment. Added new opportunity section based on v1.6.0 capabilities.
- **v1.3.0** (2026-06-11) - Marked v1.7.0 delivered items. Updated "First Seen Events" assessment to reflect first_seen Store is now live. Replaced v1.6.0 opportunity section with v1.7.0 opportunities.
- **v1.4.0** (2026-06-11) - Re-bundled: v1.5.0/v1.6.0/v1.7.0 features all ship together as v1.6.0. Renamed delivered sections to Part 1/2/3. Renamed opportunity section to "Future Options".
- **v1.5.0** (2026-06-12) - Added "Case-Insensitive Known SSID Matching" to Future Options.
- **v1.6.0** (2026-07-23) - Added "✅ Delivered with v2.0.0". Marked **BSSID (MAC Address) Support** (API uncertainty resolved — `mac` is present), **"First Seen" Events** (delivered as the restart-surviving `wifi_ssid_monitor_new_network` bus event), and **Hardware Health Monitoring** (delivered as the Integration Health self-diagnosis sensor + repairs) as delivered, and removed them from the remaining list. Retired the "First Detected Events" future option as superseded. Updated the **Channel Crowding Map** assessment (channel now derived from `frequency`), the **SSID Appearance / Disappearance Events** scope (first-seen half delivered; re-appear/disappear remains), and **Proximity Alert Hysteresis** to the 0–100% scale. Added **Per-SSID Signal Quality Sensors** to Future Options and cross-linked it with Per-SSID Presence Binary Sensors.
