# Changelog: WiFi SSID Monitor

All notable changes to this project will be documented in this file.

---

## [2.0.0] - 2026-07-23

> **This release has breaking changes — see the Breaking section.**

### Summary

A major update, with significant capability improvements and fixes BUT also some **breaking changes** unfortunately. The integration was originally developed with SSID signal as RSSI in dBm [-100 to -30], but most HA installs report Signal Quality in % [0 to 100]. This meant that the proximity threshold checking was not working on most systems.

**THE FIX**: SSID Signal is now as a **0–100% quality figure** (not dBm), and Proximity Signal Threshold is also % to match.

**NEW**: Hidden networks are now identified individually, BSSID is captured and matchable, an **Integration Health** sensor catches silent errors, and several frequently-tuned settings became control entities. A new `get_networks` action allows current SSID status to be captured and used in automations and scripts.

### Breaking

> **Upgrading from 1.6.x to 2.0.0 or above — breaking changes.** This release corrects long-standing signal-unit and band-filter bugs, which required renaming several things. There are also some moves. This was not done lightly, but the previous set-up was incorrect for most systems.
>
> 1. **`sensor.wifi_ssid_monitor_strongest_unknown_rssi` is removed**, replaced by `sensor.wifi_ssid_monitor_strongest_unknown_signal` (0–100%, not dBm). The old entity becomes unavailable — delete it when convenient; its long-term statistics are kept (delete in Developer Tools > Statistics). Update any dashboard or automation referencing it.
> 2. **Signal is now a 0–100% quality figure** everywhere. Higher means closer. The Proximity Alert now compares on this scale, and its threshold moved to the **Proximity Signal Threshold** number entity (default 80%). A stored dBm threshold is migrated automatically.
> 3. **The list-management services were renamed and merged.** `add_known_ssid` → `add_ssid`, `remove_known_ssid` → `remove_ssid`, `set_known_ssids` → `set_ssids`, each now taking a required `target: known | denylist` (and `set_known_ssids`'s `known_ssids` field is now `values`). **There are no aliases** — automations calling the old names will fail. Update them, including any copied from the guest-network example below.
> 4. **Four settings moved out of the Configure dialog** and are now entities on the device page: **Scan Interval**, **Include Hidden Networks**, and the band filter (now three **Show 2.4/5/6 GHz** switches). The old `scan_bands` option is migrated.

### Added

- **Integration Health binary sensor** — a `problem` sensor that stays available even during an outage, reporting an unreachable Supervisor, a changed payload shape or unit, an unresolved band, or all known networks vanishing at once. Backed by `interface_missing`, `signal_format_changed`, and `supervisor_unavailable` repair issues.
- **`about` notes**: All sensor entities now have an "about:" attribute (visible in details) that explains the sensor. This information is set as `unrecorded` which prevents it being written to the Home Assistant database and taking up unnecessary space.
- **Pause Polling switch** — halt scheduled scanning; explicit actions still fetch while paused.
- **6 GHz support** and per-band **Show 2.4 / 5 / 6 GHz** switches replacing the single-choice band filter. Obviously this only has an impact if your Home Assistant system WiFi is 6GHz capable.
- **Individual hidden-network naming** — cloaked networks are identified as `Hidden-<last 4 of BSSID>` instead of collapsing into one `[hidden]` entry.
- **`get_networks` action** — a response action returning the current networks filtered by scope, band, signal and keyword; reads live scan data, so it works when the sensors are unavailable or their attribute list is capped.
- **New Networks (24h) sensor** and the **`wifi_ssid_monitor_new_network` bus event** — fires once per genuinely-new network, survives restarts, baselined on first scan and rate-limited.
- **BSSID exposure and matching** — `bssid` on the per-network detail, the action response and the event payload; `known_wifi_ids` and `denylist_ssids` now match against the BSSID as well as the name, so exact MACs and MAC wildcards (`AA:BB:CC:*`) are valid in both lists.
- **`ssid_anomaly` flag** — set when a name is hidden or contains control, zero-width, or right-to-left characters (the toolkit for spoofing a network name).
- **Operating mode (`mode`)** on the per-network detail, action response, and event payload.
- **Denylist management from automations** via the `target` argument on the list actions.
- **Refreshed icons and branding.**

### Changed

- **Signal is a 0–100% quality figure throughout** — sensors, the proximity threshold, and the action filters all use the same scale.
- **Channel / Band Correct**: The channel and band detail (Strongest Unknown SSID - Networks attribute) was being misreported on many systems (conflating frequency and channel).
- **Per-network detail relocated** onto **Strongest Unknown SSID** as a `networks` list capped at the 25 strongest (with a `networks_truncated` flag), and excluded from the recorder along with the other high-churn attributes.
- **Strongest Unknown SSID reads `None Detected`** when nothing unknown is in range, instead of `unknown`.
- **History writes are coalesced** rather than written on every scan, with a hard entry cap bounding growth in SSID-heavy locations.
- **First-run setup failures raise `ConfigEntryNotReady`**, so Home Assistant shows its native retry behavior instead of marking the entry set up. The 3-strike hold still applies once running.
- **Documentation overhauled** — the README gained a detection deep-dive, an entity/action reference, architecture and self-diagnosis sections, and a restructured FAQ.
- **All Attributes `unrecorded`**: All attributes of sensor entities are now written as `unrecorded`, which prevents them being written to the Home Assistant database and taking up unnecessary space.

### Fixed

- **The band filter no longer hides every network** — band is derived from `frequency`, and an unresolved band passes rather than being dropped.
- **The Proximity Alert no longer fires permanently** — it previously compared a 0–100 value against a negative dBm threshold, so it was on whenever any unknown network was visible.
- **Interface auto-detection works on Raspberry Pi** — the Supervisor reports `wireless` there rather than `wifi`.
- **Diagnostics redacts neighboring SSIDs** — a structural sanitizer pseudonymizes SSIDs and BSSIDs, including where they are used as dictionary keys, while preserving signal, channel, band and counts.
- **Action calls targeting an unloaded entry** return a clear, translated error instead of an internal failure.

### Removed

- **`sensor.…_strongest_unknown_rssi`** — superseded by `…_strongest_unknown_signal` (see Breaking).

---

## [1.6.1] - 2026-07-04 - Release

### Summary

- **Mostly Behind the Scenes**: Most of the changes in v1.6.1 are behind-the-scenes or under-the-hood: a lot of improvements in the CI Validation and Testing system; some documentation updates. No new features , but some improvements for more predictable performance.

### Changed

- **Polling Toggle Future Ready**: Turning off "Enable polling for changes" in the entry's system options now reliably stops scheduled polling and will satisfy the upcoming HA requirement (implicit `ContextVar` detection is being removed in HA 2026.8).
- **Minimum Home Assistant Version**: Documented minimum raised to 2024.8.0.

### Fixed

- **Reconfigure Screen Now Shows All Settings**: The ⋮ Reconfigure screen previously offered only Name, Known SSIDs, and Interface, while the gear → Configure screen exposed everything. Reconfigure now shows the full settings set — Scan Interval, Include Hidden Networks, Proximity Alert Threshold, Band Filter, Always-Unknown (denylist), and Last Seen History — so both paths behave identically.

---

## [1.6.0] - 2026-06-12

### Summary

Version 1.6.0 is a major feature release focusing on security monitoring, scanning control, and robust history tracking. Key highlights include a **Proximity Alert** sensor and threshold controls to detect nearby unknown networks, dedicated sensors for the **Strongest Unknown SSID & RSSI**, and **Persistent History** (surviving restarts, tracking first-seen and visit counts). Scanning can now be filtered by **frequency band** and **hidden networks**, and an **SSID Denylist** is introduced to force specific networks to remain permanently flagged. Five new service actions and a **Scan Now** dashboard button enable dynamic whitelisting and on-demand polling. Finally, known network matching is upgraded to support **wildcard patterns** (e.g., `Guest_*`).

### Added

- **Proximity Alert Binary Sensor**: New binary sensor that fires when the strongest unknown network's signal strength meets or exceeds a configurable threshold (default −60 dBm).
- **Scan Now Button**: New button entity for triggering an immediate WiFi scan from the HA dashboard without waiting for the next scheduled interval.
- **Strongest Unknown SSID Sensor**: New sensor showing the SSID name of the unknown network with the strongest signal.
- **Strongest Unknown RSSI Sensor**: New sensor showing the signal strength (dBm) of the closest unknown network, with native long-term statistics support.
- **Persistent History**: Unknown SSID last-seen timestamps now survive HA restarts. Each SSID also records a first-seen timestamp and a visit count (number of scan cycles the SSID was detected).
- **History TTL**: New option to automatically expire stale history entries after a configurable number of days (default 90; set to 0 to keep forever).
- **Band Filter**: New option to restrict scanning to 2.4 GHz or 5 GHz networks only. APs with an undetermined band are excluded when a filter is active.
- **SSID Denylist**: New option accepting comma-separated `fnmatch` patterns. Matching SSIDs are always treated as unknown, regardless of the known list.
- **Include Hidden Networks Toggle**: New option to exclude hidden (non-broadcasting) APs from all counts and attributes (default: include).
- **Proximity Alert Threshold**: New option controlling the RSSI level at which the Proximity Alert sensor fires (range −100 to −30 dBm, default −60 dBm).
- **`add_known_ssid` Service**: Add an SSID or pattern to the known list with an immediate re-scan.
- **`remove_known_ssid` Service**: Remove a single SSID or pattern from the known list. Silent success if not present; triggers a re-scan when the list changes.
- **`scan_now` Service**: Trigger an immediate scan for one or all configured entries.
- **`clear_last_seen` Service**: Clear all persistent history (last seen, first seen, and visit counts) for one or all entries.
- **`set_known_ssids` Service**: Replace the entire known SSID list in a single call. Returns the previous list per entry as service response data.
- **Repair Issues**: HA now creates a repair issue after 4 consecutive scan failures and clears it automatically on recovery.

### Changed

- **Known SSID Matching**: Now uses `fnmatch` wildcard patterns (e.g., `Guest_*`, `IoT_?`) in addition to exact string matching. Existing lists work unchanged.
- **Signal Strength and Band Attributes**: `signal_strengths` (RSSI per SSID) and `bands` (frequency band per SSID) are now exposed as attributes on both count sensors.
- **Options Dialog**: Added contextual hints to all configuration and options flow fields.
- **Error Messages**: Integration errors (e.g., invalid service parameters, failed scans) now display translated messages in the HA UI.

### Fixed

- **Scan Button Error Reporting**: The scan button now correctly propagates scan failure to automations (previously always reported success).
- **`add_known_ssid` Silent No-Op**: Supplying an invalid `config_entry_id` now raises a UI-visible error instead of silently doing nothing.

---

## [1.4.3] - 2026-05-10

### Changed

- **Readme**: Overhaul of the readme file, additional example automations, re-ordered for readability.
- **Under the Hood**: Several internal code changes to improve maintainability and alignment with Home Assistant development standards (no functional breaking changes).
- **Validations**: Improved local and automated remote testing to ensure code remains secure and follows best practices.

## [1.4.2] - 2026-05-02

### Fixed

- **Scan Interval Minimum**: Aligned the minimum scan interval to 60 seconds across both the Options dialog and the number entity slider. Previously the options dialog accepted 30 seconds, which would silently round to 1 minute in the slider UI.

### Changed

- **Options Dialog**: Scan interval field label updated to "Scan Interval (seconds, minimum 60)" to clarify the expected unit and enforced minimum.

### Documentation

- **Known Limitations**: Added a Known Limitations section to the README documenting that multiple hidden (non-broadcasting) WiFi networks are reported as a single `[hidden]` entry in SSID counts. This is expected behavior — hidden networks cannot be individually identified without SSID data.

## [1.4.1] - 2026-04-18

### Added

- **Last Updated Sensor**: New diagnostic sensor showing the timestamp of the last successful WiFi scan.
- **Guard Bands**: Added validation for network count sensors, to ensure reasonable numbers.

### Changed

- **Custom User Naming**: Users can now define a custom prefix (e.g., "GuestScanner") for all devices and entities during setup or via the Options flow.
- **Startup Safe**: Changed to try to ensure that integration startup will not block Home Assistant, e.g. if WiFi is unavailable etc.
- **Enhanced Resilience**: The integration now holds last known values for up to 3 failures, preventing sensors from showing as "Unavailable" during brief network or Supervisor API hiccups.

## [1.4.0] - 2026-04-05

### Added

- **WiFi Interface Auto-Discovery**: The setup and options flows now automatically detect and list available WiFi interfaces from the Supervisor, providing a user-friendly dropdown selection.

### Fixed

- **Unavailable after Scan Change**: Fixed an issue where the sensors could become unavailable after a scan interval change (until the next scan).
- **Code Quality**: Multiple improvements to address potential errors and problems identified in a code review.
- **Hidden Networks**: Improved detection and logging of hidden WiFi networks (APs without a broadcasted SSID).

### Changed

- **Entity Naming**: Changed the default entity names to not have the WiFi interface name embedded, resulting in slightly shorter, more predictable names (good for example automations, etc.). If a second instance was to be added, it would include the WiFi interface in the entity names.
- **Logging**: Improved exception logging so that if there is a problem, it should appear in the Home Assistant log.

## [1.3.1] - 2026-04-02

### Changed

- **Architecture**: Refactored the internal data model to use a structured mapping for networks. This change is non-breaking but provides the necessary foundation for future features like per-network signal strength (RSSI) and channel tracking without requiring further structural rewrites.

## [1.3.0] - 2026-04-02

### Changed

- **Project Rename**: Formally renamed the integration from "WiFi Scan SSID" to **WiFi SSID Monitor** to better distinguish it from device tracking integrations and highlight its monitoring purpose.
- **Domain Update**: Changed the internal domain from `wifi_scan_ssid` to `wifi_ssid_monitor` for consistency.

## [1.2.0] - 2026-04-02

### Added

- **Scan Interval Slider**: Implemented a new `number` entity allowing users to adjust the scan frequency (1-180 minutes) directly from the Home Assistant GUI.

### Changed

- **Tests**: Expanded the test suite to include full coverage for the new number platform and debouncing logic.

## [1.1.0] - 2026-04-02

### Added

- **New Network Alert**: Added a binary sensor that triggers when unknown SSIDs are detected, making it easier to set up automations.
- **Interface Sensor**: Added a diagnostic sensor to show the active WiFi adapter being scanned.
- **Setup Validation**: Enhanced the configuration flow to validate connectivity and the presence of the Supervisor token before setup completes.

## [1.0.2] - 2026-04-02

### Added

- **Branding**: Created new, generic WiFi scanning icons and logos.

## [1.0.1] - 2026-04-02

### Changed

- **Tests and Coverage**: Significantly expanded test suite to achieve 99% coverage, including new coordinator tests and improved error path validation.

### Fixed

- **Code Quality**: Fixed file formatting and line length issues to comply with Ruff standards.
- **Documentation**: Added missing docstrings across modules and tests.

## [1.0.0] - 2026-04-01

### Added

- **Initial Release**: Basic SSID scanning and unknown SSID identification.
- **Supervisor API Integration**: Native async support for fetching access points.
- **Configurable Interface**: Support for choosing the WiFi interface.
- **Known SSID List**: Manage known networks via the UI.
- **Sensors**: Total SSID count and Unknown SSID count sensors with attributes.

---

### Format

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
