# Future Roadmap: WiFi SSID Monitor

This document tracks what was planned, what has been delivered, and what new directions
are available now that v1.5.0 is in place.

---

## ✅ Delivered in v1.5.0

All of the following items were on the original roadmap and have been implemented.

| Feature | Where it landed |
| :--- | :--- |
| **Signal Strength (RSSI) Tracking** | `signal_strengths` dict attribute on `count` and `unknown_count` sensors; per-SSID dBm values sourced from the Supervisor API. |
| **Frequency & Band Identification** | `bands` dict attribute on both count sensors; computed from channel number via `_channel_to_band()` (1–14 → 2.4 GHz, 36–177 → 5 GHz). |
| **Pattern Matching (Wildcards)** | Known SSID matching uses `fnmatch` — `Guest_*`, `IoT_?`, etc. are all valid. Backward-compatible with exact-match lists. |
| **Hidden Network Management** | `include_hidden` toggle in the options flow. When disabled, APs without a broadcasted SSID are filtered before any counting occurs. |
| **"Add to Known" Service** | `wifi_ssid_monitor.add_known_ssid` — appends to the known list and triggers an immediate re-scan via the update listener. Documented in `services.yaml`. |
| **Manual Scan Button** | `button.scan_now` — calls `coordinator.async_refresh()` on press. No interval constraint. |
| **"Last Seen" Tracking** | In-memory `last_seen` dict (SSID → datetime) exposed as ISO timestamps in `unknown_count` attributes. Populated each scan cycle. |
| **Proximity Alerts** | `binary_sensor.proximity_alert` — fires when `strongest_unknown_rssi` meets or exceeds a configurable threshold (default −60 dBm). Threshold and RSSI both exposed as attributes. |

---

## 🔜 Remaining Original Roadmap Items

These items were on the original list but were not implemented in v1.5.0. Reasons and
reassessments are given for each.

### Channel Crowding Map

**Original idea:** Identify which WiFi channels are most congested to help optimise
home router settings.

**Assessment:** The data is available (channel per AP in `network_map`), so a
channel-frequency histogram could be computed in the coordinator. The harder problem is
the entity model — there is no clean HA entity type for a map of `{channel: count}`.
This would surface best as a sensor attribute (easy) or as a template sensor the user
builds themselves. Low user demand relative to effort; defer unless requested.

---

### BSSID (MAC Address) Support

**Original idea:** Track unique BSSIDs to prevent SSID spoofing and enable a more
reliable "known list."

**Assessment:** Still blocked on API uncertainty — it is unclear whether the Supervisor
`/accesspoints` endpoint returns BSSID data. Needs investigation against a real HAOS
device. If the field is available, the implementation path is straightforward: extend
`network_map`, add BSSID to the known-list matching logic, and update the config flow.
Worth re-examining in a future session with a live device.

---

### "First Seen" Events

**Original idea:** Fire a specific HA event the very first time a new hardware BSSID is
detected.

**Assessment:** Depends on BSSID support (above). Even with BSSIDs available, this
requires cross-restart persistent storage so that "first seen ever" is meaningful after
an HA reboot. Complexity is high for a relatively narrow use case. Deprioritised until
BSSID tracking is implemented first.

---

### Multi-Interface Support

**Original idea:** Aggregate results from multiple WiFi cards simultaneously in a single
integration instance.

**Assessment:** The integration already supports multiple independent config entries, one
per interface. A user with two WiFi adapters can install the integration twice and get
separate entity sets for each. True aggregation into a single entity set would require
significant rework of the coordinator and entity model. Document the "multiple entries"
workaround clearly in the README instead.

---

### Hardware Health Monitoring

**Original idea:** Diagnostic sensor for WiFi adapter health; alert if the adapter
stalls.

**Assessment:** Requires the Supervisor API to expose adapter health status, which it may
not. If the adapter stalls, the existing 3-strike resilience will surface the problem
via the Repairs panel after 4 consecutive failures. Additional health monitoring on top
of this is low priority.

---

### System Role Attribute

**Original idea:** Re-integrate "System Role" logic from the original script.

**Assessment:** The original script context is no longer available and the value to HA
users is unclear. Removed from active consideration unless a concrete use case is
identified.

---

## 💡 New Opportunities Unlocked by v1.5.0

Now that RSSI, band, last-seen, pattern matching, proximity alerting, and the add-to-known
service are in place, a second tier of useful features has become more feasible.

---

### "Remove from Known" Service — `wifi_ssid_monitor.remove_known_ssid`

**Difficulty:** Easy  
**Benefit:** High — logical complement to `add_known_ssid`. Users can remove a network
from the known list via automation or Developer Tools without opening the options flow.
Implementation mirrors the existing service: parse the list, filter out the target, write
back to options.

---

### Strongest Unknown SSID Name Sensor

**Difficulty:** Easy  
**Benefit:** Medium-high — the Proximity Alert fires, but the name of the nearest unknown
network is buried in the `unknown_count` sensor's `signal_strengths` attribute. A
dedicated sensor whose state is the SSID name of the strongest unknown signal would make
dashboard cards and notification templates trivial to write.

**Implementation:** Coordinator already has `strongest_unknown_rssi`; add a parallel
`strongest_unknown_ssid: str | None` key alongside it.

---

### Persistent "Last Seen" Storage

**Difficulty:** Medium  
**Benefit:** High — the current `last_seen` timestamps reset on every HA restart, making
them useful only within a session. Using HA's `Store` (JSON file via
`homeassistant.helpers.storage`) or `RestoreExtraData` would persist timestamps across
restarts and dramatically improve usefulness for security dashboards and long-term
monitoring.

**Consideration:** Storage size grows unboundedly if old SSIDs are never pruned — pair
with an auto-expiry option (see below).

---

### Auto-Expire Stale "Last Seen" Entries

**Difficulty:** Easy  
**Benefit:** Medium — the in-memory `_last_seen` dict currently accumulates entries for
SSIDs that have disappeared and never prunes them. A configurable TTL (e.g., "remove
entries not seen in 30 days") would keep the attribute clean and make persistent storage
practical.

**Implementation:** On each successful scan, walk `_last_seen` and remove entries where
`now - last_seen[ssid] > timedelta(days=ttl)`.

---

### SSID Appearance / Disappearance Events

**Difficulty:** Medium  
**Benefit:** High — fire `wifi_ssid_monitor.ssid_appeared` and
`wifi_ssid_monitor.ssid_disappeared` HA events by diffing the current scan against the
previous one. Users can automate on these directly without needing a binary sensor.
Especially useful for presence-detection use cases (e.g., "notify me when the IoT device
hotspot disappears — it may have been stolen").

**Implementation:** Compare `set(current_ssids)` with `set(previous_ssids)` in the
coordinator after each scan; fire events for diffs via `hass.bus.async_fire`.

---

### Band Filter Option

**Difficulty:** Easy  
**Benefit:** Medium — in urban environments 5 GHz networks are extremely dense and
ephemeral (neighbours, passing devices). A `scan_bands` option (`"all"` / `"2.4 GHz
only"` / `"5 GHz only"`) would let users focus on the band most relevant to their
threat model. The band is now computed per AP, so filtering is a one-line addition to
the coordinator.

---

### Proximity Alert Hysteresis

**Difficulty:** Medium  
**Benefit:** Medium — if a mobile device sits right at the threshold (e.g., −61/−59 dBm
alternating), the proximity sensor will flap on every scan. A configurable hysteresis
band (e.g., "must drop 5 dBm below threshold to turn off") prevents this. Requires
tracking the previous `is_on` state and applying upper/lower bounds separately.

---

### SSID Denylist

**Difficulty:** Easy  
**Benefit:** Low-Medium — a second list of SSIDs that are *always* flagged as unknown
even if they match a pattern in the known list. Useful for intentionally watching a
specific network that would otherwise be suppressed by a wildcard (e.g., `Guest_*`
catches most guest networks, but `Guest_Rogue` should always alert). Implementation is
a pre-check before the known-pattern match.

---

### Per-SSID Presence Binary Sensors

**Difficulty:** Hard  
**Benefit:** High (for the right users) — auto-create a binary sensor for each SSID in
the known list, showing whether it is currently visible. Enables direct "is my work
laptop nearby?" automations without template sensors. Requires dynamic entity creation
and teardown when the known list changes, which is significantly more complex than the
current static entity model.

---

## Version Control

- **v1.0.1** (2026-04-01) - Created.
- **v1.1.0** (2026-06-02) - Major rewrite. Marked v1.5.0 delivered items. Reassessed
  remaining original items. Added new opportunity section based on v1.5.0 capabilities.
