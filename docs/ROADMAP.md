# Roadmap: WiFi SSID Monitor

Forward view for `ha-wifi-ssid-monitor`, and the record of what has been decided against. The integration counts visible networks, separates known from unknown, and records signal, band and history for them. What remains is mostly one large item — per-network entities, in three phases — plus a few small filters over history that is already persisted.

Format document `roadmap_format.md` v1.2.0 used, with one deliberate carry-over: **nothing that was in the predecessor `FUTURE.md` has been dropped.** Where the format would have excluded something — the off-roadmap v2.0.0 deliveries, and one future option retired without ever being built — it is kept under **Done** in a clearly separated subsection rather than discarded, so this first conversion loses no record.

**Reviewed 2026-08-03** against the v2.0.0 source and the current entity set.

---

## To Be Done

### Per-network entities

#### **Value ⭐⭐⭐⭐ · Effort High overall — see the per-phase Effort below**

Three things that were previously listed as separate items — a my-WiFi online count, per-network presence entities, and per-network signal sensors — are one item in three phases. They were split because they arrived at different times, not because they are separable: all three read from the same list of networks the user cares about, and building them independently would produce three lists, two presence paths and a signal sensor with no defined "gone" state.

**Recorded as one item so the end state is designed once.** Phase 1 is worth building on its own and does not depend on the later phases, but it must not be built in a way that has to be undone by phase 2.

**Shared foundation, needed by all three phases:**

- **A "my WiFi" list** — the networks the user owns. Separate from the known list, which exists to suppress noise: a whitelisted neighbour belongs in the known list and not here. Accepts the same identity forms as the known and deny lists (SSID, `fnmatch` pattern, or BSSID). BSSID is the strongest form because it pins one radio and a spoofed name cannot satisfy it.
- **Add / remove / set actions** for that list, mirroring the existing `add_known_ssid` / `remove_known_ssid` / `set_known_ssids` `target:` pattern, so it is not Configure-only.
- **Absence debounce** — a network counts as gone only after N consecutive missed scans (configurable), so one bad scan does not register as an outage. This is the `for:` duration the README automation currently carries, moved into the integration.
- **Deference to Integration Health** — a scan that fails wholesale (interface gone, Supervisor unreachable) makes every network look absent at once. Nothing in any phase may report absence while Integration Health says the scan itself failed.

---

#### Phase 1 — my-WiFi count and offline sensors · **Effort Medium**

Two fixed entities, regardless of how many networks are in the list:

- **`My WiFi Online`** — a count of how many entries in the my-WiFi list are currently visible, with the matched and missing names as attributes. An integer, so it graphs and reaches long-term statistics.
- **`My WiFi Offline`** — a `problem` binary sensor, `on` when one or more entries are not visible, with the missing names as an attribute.

**What this replaces.** The **Home WiFi Offline Alert** automation in `README.md` infers "a network went down" by subtracting the unknown count from the total and watching that base drop below a hand-set number. Three concrete failures follow from that:

- The base falling from 3 to 2 says a network is missing but not which one, and if a previously-unknown neighbour joins the known list at the same moment two of the user's own networks drop, the base does not move at all.
- The `< 3` threshold is specific to one location and must be re-set whenever the user adds a network, disables a band, or moves.
- If an AP dies as a new unknown one appears, the total and the base are both unchanged and nothing fires.

Naming the expected networks removes all three, and needs no threshold.

**No dynamic entity creation**, which is what keeps this phase at Medium and lets it ship first.

#### Phase 2 — per-network presence entities · **Effort High**

One entity per network showing whether it is currently visible. This is the phase that carries the hard mechanism; phases 1 and 3 are cheap on either side of it.

- **Entity type is undecided** — a `binary_sensor` or a `device_tracker`. `device_tracker` is the closer fit if the network being visible is treated as a location signal (a phone hotspot arriving home), `binary_sensor` if it is treated as equipment being up. This should be settled before any code, because it is not a cheap change afterwards.
- **Scope option** — which networks get an entity, because "all of them" in a dense location is hundreds. The choices are: off (default), my-WiFi only, known only, unknown only, or an explicit list. Off by default matters: a user upgrading should not silently acquire a hundred entities.
- **Created on sighting, not on configuration.** An entity appears the first time a network matching the scope is seen, so the list does not have to be written by hand in advance.
- **Cleanup by age** — an action and a button that remove entities for networks not seen for N days (configurable, default 90, matching the existing history TTL). Creation on sighting means entities accumulate, so an explicit prune is part of the mechanism and not an afterthought.
- **A defined "gone" state** — `unknown` when the network is not visible but the scan is healthy, `unavailable` only when the scan itself failed. This is the existing convention and phase 3 depends on it.

**Watch out for:** a wildcard in an explicit scope list matching far more networks than intended. The resolved set needs a cap, with the overflow reported rather than silently truncated.

**Relationship to phase 1.** Once this exists, `My WiFi Online` is a rollup of the my-WiFi subset of these entities. It must be reimplemented as that rollup rather than left running as a second, parallel presence calculation.

#### Phase 3 — per-network signal sensors · **Effort Low once phase 2 exists**

A numeric signal sensor alongside each phase 2 entity, so one network's signal can be trended over time.

**Why the current sensors cannot do this.** They are aggregate by design: **Strongest Unknown Signal** follows whichever unknown network is strongest at that moment, so its history is a composite of different networks and cannot answer how one network behaved over a month. Per-network signal exists in the attributes, but attributes are unrecorded and are not long-term statistics candidates, so no trend series exists.

The value here is entirely in the mechanism phase 2 builds — same list, same lifecycle, same cleanup. The only addition is the sensor itself and one rule: when the network is not visible the state is `unknown`, never `0`, which would put a false floor in the trend.

**Where a spoofed SSID matters.** If two APs broadcast the same name, the sensor needs a stated rule for which radio it follows — strongest, or the pinned BSSID if the list entry was a BSSID.

### Visit-count threshold

#### **Value ⭐⭐⭐ · Effort Low**

A **Number** control (`min_visit_count`, default `0` = disabled) excluding networks from `unknown_count` and its attributes until they have been seen at least N times. Filters drive-by hotspots and one-off scan artifacts without the user writing template conditions.

A control rather than a Configure option because it is a value the user will want to tune against what they are actually seeing, and adjusting it from a dashboard slider — or from an automation — beats reopening the options flow each time. It follows the existing convention for disabled-by-default controls that change what other entities report.

The `visit_counts` history that drives it is already persisted, so this is a filter over existing state rather than new state, which is what keeps the effort low.

### Appearance / disappearance events

#### **Value ⭐⭐⭐ · Effort Medium**

The first-ever-seen case ships as `wifi_ssid_monitor_new_network`. What remains is the recurring diff: an event when a previously-seen network **re-appears** after an absence, and one when a currently-visible network **disappears**.

**What this gives an automation.** The events fire for every network, carrying the same payload fields as `new_network` (`key`, `ssid`, `bssid`, `band`, `signal`, and for the recurring cases, how long it was absent or present). Selecting a specific network is the automation's job, in an event-trigger condition — a template `condition` on `trigger.event.data.ssid`, with whatever wildcard or regex the user wants, or a match on `bssid` to pin one radio. **The integration does not take a per-network event filter**, because the automation can express one better than a config option could, and adding one would mean a fourth list to keep in step with the other three.

**Glitch guarding — this is the part that decides whether the events are usable.** A scan that misses a network for one cycle would otherwise fire a disappearance and then an appearance, and a location with passing traffic would fire constantly. Three guards, all reusing machinery that exists:

- **Appearance guarded by visit count.** An appearance event fires only once the network has been seen at least N times, reusing the same `visit_counts` history as the **Visit-count threshold** item above and, if set, its threshold. A network seen once and never again never fires.
- **Disappearance guarded by consecutive misses.** A disappearance fires only after the network has been absent for N consecutive scans, the same debounce the phase 1 my-WiFi work needs. Both should be one implementation.
- **Health deference and rate limiting.** No event fires while Integration Health reports the scan itself failed, and the existing per-cycle rate limit and first-scan baseline apply, so a first scan after a restart does not replay the whole neighbourhood.

**Implementation.** Compare the current scan's key set against the previous one in the coordinator and fire on the diffs. The previous set is derivable from `coordinator.data` at the start of `_async_update_data`, and the persisted `last_seen` history supplies the absence duration.

**Sequencing.** The two guards are shared with other items — the visit-count history with the threshold control, the miss debounce with the per-network entities. Whichever is built first should build them to be reused.

---

## Maybe

### Proximity alert hysteresis

#### **Value ⭐⭐ · Effort Medium**

A device sitting at the threshold — 79/81% against an 80% threshold — makes the proximity sensor flap on every scan. A configurable hysteresis band ("must drop 5 percentage points below the threshold to turn off") stops it. Requires tracking the previous `is_on` state and applying the upper and lower bounds separately.

**Would be justified by:** observing the flap. It is a predicted failure rather than a reported one, and a user whose threshold is nowhere near a real network's signal will never see it. The **Appearance / disappearance events** item builds debounce machinery that may cover this case more generally, so it is worth checking whether this is still a separate problem afterwards.

### Case-insensitive known-SSID matching

#### **Value ⭐⭐ · Effort Medium**

Known-SSID matching, `fnmatch` patterns included, is case-sensitive, matching how real SSID identifiers behave. Some routers and devices broadcast the same network name with inconsistent capitalization (`MyWiFi` vs `mywifi`), which can leave a network counted as unknown despite being in the known list. An option to lowercase both sides before comparison would remove that class of false positive.

The effort is uncertain rather than large: the open question is whether `fnmatch` pattern semantics stay correct after lowercasing, particularly for patterns carrying mixed-case characters, and that has not been established.

**Would be justified by:** an actual observed mismatch — a network appearing as unknown when its name is in the known list differing only in case. Adding the option speculatively adds a config surface for a problem that may not occur on any hardware here.

---

## Revisit

### Channel crowding map

Not doing it. A histogram of which channels are congested is easy to compute and has nowhere good to go — Home Assistant has no entity type for a `{channel: count}` map, so it would land as a sensor attribute or a template sensor the user has to build themselves.

**Reopens if:** anyone asks for it, or a presentation that suits a map appears.

**Detail.** The input data is materially better than when this was first considered: channel is derived reliably from the Supervisor's `frequency` field rather than a `channel` key that never existed, and per-network `channel` and `band` are exposed on the detail attributes and in the `get_networks` response. The computation is a straightforward coordinator step. The blocker is unchanged and purely presentational, and demand is low relative to the effort of designing around it.

---

## Declined

### Multi-interface aggregation

Not doing it. A user with two WiFi adapters can already install the integration twice and get a separate entity set for each; folding them into one set would be a rework of the coordinator and entity model for a presentation preference.

**Detail.** The integration supports multiple independent config entries, one per interface, and that is the supported answer. True aggregation raises questions the current model never has to answer — how a network visible on both adapters is counted, which adapter's signal wins, what the persisted history keys on — none with an obviously right answer. `README.md` should document the multiple-entries approach clearly instead.

### System Role attribute

Not doing it. This was carried over from an earlier script whose context no longer exists, and no use for it in Home Assistant has ever been stated.

**Detail.** The original script is unavailable, so what "System Role" meant cannot now be recovered — which means the item cannot be specified, let alone built. The condition that would revive it, recovering the original context, cannot be met. If someone describes a concrete use from scratch, that is a new item rather than this one.

---

## Summary

Forward work only. Declined and Revisit items are recorded above and are not work in progress.

Phases of the per-network entities item are listed separately because their Effort differs; they are one item and are not independently orderable.

| Item                                 | Group      | Value    | Effort            |
| :----------------------------------- | :--------- | :------- | :---------------- |
| Per-network entities                 | To Be Done | ⭐⭐⭐⭐ | High overall      |
| — phase 1, my-WiFi count and offline | To Be Done | ⭐⭐⭐⭐ | Medium            |
| — phase 2, presence entities         | To Be Done | ⭐⭐⭐   | High              |
| — phase 3, signal sensors            | To Be Done | ⭐⭐⭐   | Low after phase 2 |
| Visit-count threshold                | To Be Done | ⭐⭐⭐   | Low               |
| Appearance / disappearance events    | To Be Done | ⭐⭐⭐   | Medium            |
| Proximity alert hysteresis           | Maybe      | ⭐⭐     | Medium            |
| Case-insensitive known-SSID matching | Maybe      | ⭐⭐     | Medium            |

---

## Done

Items that were on this roadmap and have since been built. Detail is in `CHANGELOG.md` and `docs/changelog_local.md`; this records only that the roadmap item was met.

| Item | Origin | Where it landed |
| :-- | :-- | :-- |
| **BSSID (MAC address) support** | Original item | Unblocked and delivered in v2.0.0. The Supervisor `/accesspoints` payload does return `mac`, verified on Intel and Raspberry Pi hardware. BSSID is captured in the normalized shape, exposed as `bssid` on the per-network detail, the `get_networks` response and the `new_network` event, and used as the identity for cloaked networks (`Hidden-<last 4 of BSSID>`). `known_wifi_ids` and `denylist_ssids` match against both the network key and the BSSID, so exact MACs and MAC wildcards (`AA:BB:CC:*`) are valid in either list. |
| **"First seen" events** | Original item | `wifi_ssid_monitor_new_network` in v2.0.0. Fires once per genuinely-new network, keyed on the persisted history so it survives restarts, with the existing set recorded silently as a baseline on first scan and a per-cycle rate limit. Payload carries `entry_id`, `key`, `ssid`, `bssid`, `band`, `channel`, `signal`, `hidden`, `ssid_anomaly`, `mode` and `first_seen`. Supersedes the separate "first detected events" item, whose sketched `hass.bus.async_fire`-on-missing-`first_seen` approach would not have been restart-safe. |
| **Hardware health monitoring** | Original item | Delivered in v2.0.0 as the Integration Health self-diagnosis sensor, not as raw adapter telemetry — the Supervisor API does not expose that. A `problem` binary sensor that stays available when everything else has gone `unavailable`, backed by a check catalogue and three repair issues: `interface_missing` (the "adapter stalled" case the item described), `signal_format_changed` and `supervisor_unavailable`. It also catches the silent failure the item did not anticipate: a scan that succeeds while the payload shape or units have drifted. |
| **Signal strength (RSSI) tracking** | Original item | `signal_strengths` dict attribute on the `count` and `unknown_count` sensors, per SSID, sourced from the Supervisor API. |
| **Dedicated strongest-unknown RSSI sensor** | Original item | `sensor.strongest_unknown_rssi`, `SensorDeviceClass.SIGNAL_STRENGTH` in dBm, so history graphing and numeric automation conditions work without attribute extraction. |
| **Strongest unknown SSID name sensor** | Original item | `sensor.strongest_unknown_ssid`; `unknown` when no unknown networks are visible. Companion to the `proximity_alert` binary sensor. |
| **Proximity alerts** | Original item | `binary_sensor.proximity_alert`, firing when the strongest unknown signal meets or exceeds a configurable threshold (originally −60 dBm; now on the 0–100% scale). Threshold and signal both exposed as attributes. |
| **Frequency and band identification** | Original item | `bands` dict attribute on both count sensors. Originally computed from channel number via `_channel_to_band()` (1–14 → 2.4 GHz, 36–177 → 5 GHz); since v2.0.0 derived from the Supervisor's `frequency` field through the `parse.py` normalization boundary. |
| **Band filter option** | Original item | `scan_bands` (`all` / `2.4` / `5`), filtering counts, attributes and known-network matching rather than only band display, with undetermined-band APs excluded while a filter is active (strict mode). Since v2.0.0 the single-choice enum is replaced by per-band **Show 2.4 / 5 / 6 GHz** switches. |
| **Pattern matching (wildcards)** | Original item | Known-SSID matching uses `fnmatch` — `Guest_*`, `IoT_?` and so on — backward-compatible with exact-match lists. |
| **SSID denylist** | Original item | `denylist_ssids`: SSIDs or `fnmatch` patterns always counted as unknown even when they match the known list. The denylist overrides the known list. |
| **Hidden network management** | Original item | `include_hidden` toggle; when disabled, APs with no broadcast SSID are filtered before any counting occurs. |
| **"Last seen" tracking, persisted** | Original item | Started as an in-memory `last_seen` dict populated each scan cycle; now backed by HA's `Store` (`.storage/wifi_ssid_monitor.<entry_id>.last_seen`) so timestamps survive restarts, exposed as ISO timestamps on `unknown_count`. The Store is cleaned up when the entry is deleted. |
| **"First seen" persistent timestamps** | Original item | `_first_seen` backed by `Store` (`.storage/wifi_ssid_monitor.<entry_id>.first_seen`), written once on first detection and never overwritten, exposed as the `first_seen` attribute on `unknown_count`. |
| **Unknown SSID visit count** | Original item | `_visit_counts` backed by `Store` (`.storage/wifi_ssid_monitor.<entry_id>.visit_counts`), incremented each scan cycle the network is present, exposed as `visit_counts` on `unknown_count`. |
| **Auto-expire stale history** | Original item | Configurable TTL in the options flow (0–366 days; `0` keeps forever, default 90), applied on each successful scan before saving and pruning `first_seen` alongside `last_seen`. |
| **Manual scan** | Original item | `button.scan_now` calls `coordinator.async_refresh()` on press with no interval constraint, and the `scan_now` action does the same for one or all entries — cleaner than pressing the button from an automation and consistent with the other actions. |
| **Known-list management actions** | Original item | `add_known_ssid` appends, `remove_known_ssid` removes an exact SSID or pattern (silent success if not found), and `set_known_ssids` replaces the whole list in one call and returns the previous list per entry as `SupportsResponse.OPTIONAL` response data, enabling backup/restore patterns. All trigger an immediate re-scan via the update listener when the list changes. Documented in `services.yaml`. |
| **Clear history action** | Original item | `clear_last_seen` clears `_last_seen`, `_first_seen` and `_visit_counts` and saves empty state to all three Stores; the next scan repopulates from scratch. |

### Retired without being built

| Item | Origin | Outcome |
| :-- | :-- | :-- |
| **"First detected" events** | Future option | Superseded by `wifi_ssid_monitor_new_network` above, and never built in its own right. The sketched approach — `hass.bus.async_fire` whenever a network had no `first_seen` value — would have re-fired for every network after a restart. The delivered event keys on the persisted history instead, so it is restart-safe. |

### Off-roadmap deliveries

**Not roadmap items.** None of the following was on any list; they are recorded here only because they shaped v2.0.0 and because the roadmap items above are stated in their terms. Format §2 excludes them from **Done** proper — provenance, not significance, is what qualifies an item — and `CHANGELOG.md` remains the authority on them.

- **The `parse.py` payload normalization boundary**, and the three root-cause bug fixes it enabled: percent signal, frequency→band, and the `wireless` interface type. Every band, channel and signal figure quoted in the items above comes through it.
- **Per-band Show 2.4 / 5 / 6 GHz switches**, replacing the old single-choice `scan_bands` enum.
- **The Pause Polling switch**, with force-refresh.
- **The `get_networks` response action**, returning the full per-network detail to a script rather than through attributes.
- **The New Networks (24h) LTS sensor.**
- **The `ssid_anomaly` flag** for control, zero-width and RTL characters in SSIDs.
- **A structural diagnostics sanitizer.**
- **Coalesced storage writes** with a hard entry cap, and `_unrecorded_attributes` across the high-churn attributes.

---

## Version Control

- **v2.1.0** (2026-08-03) — **Three items merged into one.** "Track your own WiFi online", "Per-SSID presence binary sensors" and "Per-SSID signal quality sensors" were one feature listed three times: all three read the same list, and building them separately would have produced three lists, two parallel presence calculations, and a signal sensor with no defined "gone" state. Now **Per-network entities**, with a shared foundation (the my-WiFi list, its actions, absence debounce, Integration Health deference) and three phases — my-WiFi count and offline sensors, per-network presence entities, per-network signal sensors — so the end state is designed once and phase 1 is not built in a way phase 2 has to undo. Phase 2 is stated as `binary_sensor` **or** `device_tracker`, undecided, with created-on-sighting lifecycle, a scope option defaulting to off, and cleanup by age. The old presence entry's "is my work laptop nearby?" framing is removed: a laptop does not broadcast an SSID, so the example described something the feature cannot do. **Visit-count threshold** is a Number control, not an options-flow field. **Appearance / disappearance events** now states what an automation actually gets — events for every network, with selection done in the automation's own condition, and no per-network filter in the integration — and the three glitch guards that make them usable: visit-count on appearance, consecutive-miss debounce on disappearance, health deference and rate limiting on both, each shared with another item. **Proximity alert hysteresis** moved To Be Done → Maybe with a trigger; it is a predicted flap, not an observed one. Prose edited throughout against `roadmap_format.md` §4.
- **v2.0.0** (2026-08-03) — Restructured to `roadmap_format.md` v1.1.0 and renamed from `docs/FUTURE.md`. Six groups replace the previous per-release "delivered" tables plus a mixed opportunities section. **Done is now membership by provenance**, so the "beyond the roadmap" v2.0.0 paragraph — `parse.py` normalization, the pause-polling switch, the `get_networks` response action, the LTS new-networks sensor, `ssid_anomaly`, the diagnostics sanitizer, coalesced storage writes — no longer qualifies as a roadmap item. **It is kept anyway**, in an explicitly labelled **Off-roadmap deliveries** subsection, along with the retired-unbuilt "first detected events" option: this is the first conversion of this document, and losing content in the move would be indistinguishable from losing it by accident. Both subsections state why they are not Done proper. A later revision may prune them once `CHANGELOG.md` is confirmed to carry everything. Forward items carry Value and Effort; **Track your own WiFi online** is the highest-value forward item and the only one of the three "named network" items needing no dynamic entity creation, so it is To Be Done while the two per-SSID items are Maybe with stated triggers. **Channel crowding map** moved to Revisit with an explicit reopening trigger; **multi-interface aggregation** and **System Role** to Declined, each opening with the decision in one plain sentence. Framing that treated earlier revisions as milestones — "delivered since the original roadmap", "remaining original roadmap items" — removed.
- **v1.6.0** (2026-07-23) — Added "Delivered with v2.0.0". Marked BSSID support (API uncertainty resolved — `mac` is present), "First Seen" events (delivered as the restart-surviving `wifi_ssid_monitor_new_network` bus event) and hardware health monitoring (delivered as the Integration Health sensor plus repairs) as delivered. Retired "First Detected Events" as superseded. Updated the channel crowding map assessment (channel now derived from `frequency`), the appearance/disappearance scope (first-seen half delivered) and proximity hysteresis to the 0–100% scale. Added per-SSID signal quality sensors, cross-linked with per-SSID presence.
- **v1.5.0** (2026-06-12) — Added case-insensitive known-SSID matching to Future Options.
- **v1.4.0** (2026-06-11) — Re-bundled: the v1.5.0/v1.6.0/v1.7.0 features all ship together as v1.6.0. Renamed the delivered sections to Part 1/2/3 and the opportunity section to "Future Options".
- **v1.3.0** (2026-06-11) — Marked v1.7.0 delivered items; updated the "First Seen" assessment now that the `first_seen` Store is live.
- **v1.2.0** (2026-06-11) — Marked v1.6.0 delivered items; added an opportunity section based on v1.6.0 capabilities.
- **v1.1.0** (2026-06-02) — Major rewrite. Marked v1.5.0 delivered items, reassessed the remaining original items, added an opportunity section.
- **v1.0.1** (2026-04-01) — Created.
