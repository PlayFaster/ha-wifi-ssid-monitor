# Changelog: WiFi SSID Monitor

All notable changes to this project will be documented in this file.

## [1.4.3-dev1] - Now - Unreleased

### Changed

- **Badge Links**: Added links to readme badges.

## [1.4.2] - 2026-05-02

### Fixed

- **Scan Interval Minimum**: Aligned the minimum scan interval to 60 seconds across both the Options dialog and the number entity slider. Previously the options dialog accepted 30 seconds, which would silently round to 1 minute in the slider UI.

### Changed

- **Options Dialog**: Scan interval field label updated to "Scan Interval (seconds, minimum 60)" to clarify the expected unit and enforced minimum.

### Documentation

- **Known Limitations**: Added a Known Limitations section to the README documenting that multiple hidden (non-broadcasting) WiFi networks are reported as a single `[hidden]` entry in SSID counts. This is expected behaviour — hidden networks cannot be individually identified without SSID data.

## [1.4.2-dev3] - 2026-05-01 - Unreleased

### Fixed

- **Readme**: Typo in Readme.
- **Scan Interval Minimum Mismatch** (B2): Aligned minimum scan interval to 60 seconds in `config_flow.py` — changed `vol.Range(min=30)` to `vol.Range(min=60)`. The number entity already enforced 60s (1 min); the options flow now matches, preventing silent round-up of 30–59s values.
- **Scan Interval Label** (D2): Updated `strings.json` and `translations/en.json` scan interval label from `"Scan Interval (seconds)"` to `"Scan Interval (seconds, minimum 60)"` to reflect the enforced minimum and clarify units.

### Changed

- **Exception Syntax** (B1): `except KeyError, AttributeError:` → `except (KeyError, AttributeError):` in `sensor.py:118` — idiomatic Python 3 tuple-style; no runtime change.
- **Exception Handling** (Q1): Removed redundant `TimeoutError` and `WifiScanError` from `except (TimeoutError, WifiScanError, Exception)` in `coordinator.py` — `Exception` already subsumes both, keeping the catch and removing the noise.
- **Task Management** (Q2): Replaced `asyncio.create_task()` with `self.hass.async_create_task()` in `number.py` for proper HA lifecycle management. With `asyncio.create_task`, debounce tasks were not tracked by HA and could run against stale entities after removal.
- **Translation Key** (Q3): Changed `name="Last Updated"` to `translation_key="last_updated"` in `sensor.py` `SENSOR_TYPES` — consistent with all other sensor descriptions; translation already existed in `strings.json`.
- **Type Hints** (B/Q4): Added full type annotations to `async_setup_entry` and `WifiScanBinarySensor.__init__` in `binary_sensor.py`. Added `CoordinatorEntity[WifiScanCoordinator]` type parameter to the class.
- **Config Entry Data** (Q5 / A2): Changed `data=user_input` to `data={}` in `config_flow.py` `async_step_user`. All configuration lives in `options`; `data` is reserved for immutable/auth values per HA best practice. Resolves the stale `data` dict that persisted on all new installs.
- **VERSION Constant** (Q6): Added `VERSION` constant to `const.py`, read from `manifest.json` at module import time via `json.loads`. Removed `async_get_integration(hass, DOMAIN)` call from `async_setup_entry` in `__init__.py` — it was called solely to read the version string, adding an unnecessary async I/O step on every setup.

### Added

- **Binary Sensor Tests** (T1): Created `tests/test_binary_sensor.py` with 6 tests: platform setup and initial state, `is_on` with unknown networks, `is_on` with all-known, `is_on` with no data, `device_info` structure, and unique ID format.
- **Coordinator Resilience Tests** (T3): Added `test_coordinator_resilience_holds_for_three_failures` and `test_coordinator_resilience_resets_on_success` to `tests/test_coordinator.py`, covering the 3-failure stale-hold behaviour and failure count reset on success.

### Changed (Tests)

- **Test Fixture** (T4): Updated `conftest.py` `mock_config_entry`: title changed to `"WiFi SSID Monitor"`, `CONF_NAME: "WiFi SSID Monitor"` added to options, `data` set to `{}` — aligns fixture with post-Q5 config flow behaviour and v1.4.0 clean naming.
- **Sensor Test Entity IDs** (T4): Updated entity ID assertions in `tests/test_sensor.py` from `sensor.wifi_ssid_monitor_wlan0_*` to `sensor.wifi_ssid_monitor_*` to match v1.4.0 single-instance clean naming.
- **Config Flow Test**: Updated `test_user_flow` in `tests/test_config_flow.py` — `result["data"]` assertion changed from `{user_input contents}` to `{}` to reflect Q5 fix.
- **Number Debounce Test**: Replaced `task1.cancelling() > 0 or task1.cancelled()` state check in `test_number_debounce_cancellation` with `task1 is not task2` — the old check broke when `hass.async_create_task` with eager start ran the mocked-sleep task to completion immediately.
- **Setup Failure Test**: Updated `test_setup_entry_failure` in `tests/test_init.py` to mock `WifiScanCoordinator` instead of the now-removed `async_get_integration`.

### Removed

- **Placeholder Test File** (T2): Deleted empty `tests/test_temp.py`.

### Documentation

- **DEVELOPMENT.md** (D1): Updated "Retry Resilience" bullet to accurately describe the 3-failure hold strategy, replacing stale reference to a "two-stage fetch attempt with a 10-second delay" (that logic no longer exists).
- **DEVELOPMENT.md** (A1): Added pitfall note on hidden network deduplication — multiple hidden APs collapse to a single `[hidden]` entry in `all_ssids` (set dedup) and `network_map` (last-write-wins). Count will differ from tools like `nmcli` that report per-AP.
- **README.md** (A1): Added "Known Limitations" section documenting the hidden network grouping behaviour for end users.

### Dev Tooling

- **VS Code Tasks**: Updated "Pytest: Run All Tests" and "Pytest: Check Test Coverage" tasks to strip ANSI escape codes from `.reports/pytest_results.txt` and `.reports/pytest_coverage.txt` while preserving colour in the terminal. Uses bash process substitution: `tee >(sed 's/\x1b\[[0-9;]*[a-zA-Z]//g' > file.txt)`. Same fix applied to `ha-tplink-router-5g-monitor` and `ha-zte-router-5g-monitor`.

## [1.4.1] - 2026-04-18

### Added

- **Last Updated Sensor**: New diagnostic sensor showing the timestamp of the last successful WiFi scan.
- **Diagnostic Monitoring**: Added a "Last Updated" timestamp sensor to track the most recent successful data fetch from the Supervisor API.
- **Guard Bands**: Added validation for network count sensors, to ensure reasonable numbers.
- **Guard Bands**: Implemented data integrity validation (Standard 4) for network count sensors, limiting reported values to a realistic range (0-256) to filter out transient hardware spikes.

### Changed

- **Custom User Naming**: Users can now define a custom prefix (e.g., "GuestScanner") for all devices and entities during setup or via the Options flow.
- **Custom User Naming**: Added support for `CONF_NAME`, allowing users to define a custom prefix for all devices and entities during initial setup or reconfiguration via the Options flow.
- **Improved Setup**: Rewrote the devcontainer configuration to ensure faster and more reliable environment setup on Windows and Linux hosts.
- **Enhanced Resilience**: The integration now holds last known values for up to 3 failures, preventing sensors from showing as "Unavailable" during brief network or Supervisor API hiccups.
- **Standardized Resilience**: Aligned the Data Update Coordinator with the architectural standards. Implemented `asyncio.timeout(30)` and enhanced the coordinator to hold last known values for up to 3 consecutive failures before reporting "Unavailable".
- **Declarative Entities**: Refactored the sensor platform to use the standardized `TPLinkSensorEntityDescription` pattern with callback-driven `value_fn` logic.
- **DevContainer Hardening**: Synchronized and "hardened" the `setup.sh` script to be resilient against Windows-style carriage returns. Removed sensitive shell syntax (`if/fi`) in favor of robust `&&` chaining and added detailed logging to `.reports/devcontainer/post_setup.log`.
- **Startup Safe**: Changed to try to ensure that integration startup will not block Home Assistant, e.g. if WiFi is unavailable etc.
- **Modern Background Tasks**: Formally migrated the non-blocking startup sequence to the `entry.async_create_background_task` API for better lifecycle tracking.

### Fixed

- **Domain Cleanup**: Implemented standardized unloading logic to ensure the `DOMAIN` key is scrubbed from Home Assistant's internal memory when no integration instances remain.

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
- **Tests & Coverage**: Added tests and improved coverage for the most recent code changes.

## [1.3.1] - 2026-04-02

### Changed

- **Architecture**: Refactored the internal data model to use a structured mapping for networks. This change is non-breaking but provides the necessary foundation for future features like per-network signal strength (RSSI) and channel tracking without requiring further structural rewrites.

## [1.3.0] - 2026-04-02

### Changed

- **Project Rename**: Formally renamed the integration from "WiFi Scan SSID" to **WiFi SSID Monitor** to better distinguish it from device tracking integrations and highlight its monitoring purpose.
- **Domain Update**: Changed the internal domain from `wifi_scan_ssid` to `wifi_ssid_monitor` for full architectural consistency.
- **Folder Structure**: Migrated all components to the `wifi_ssid_monitor` directory.

## [1.2.0] - 2026-04-02

### Added

- **Scan Interval Slider**: Implemented a new `number` entity allowing users to adjust the scan frequency (1-180 minutes) directly from the Home Assistant GUI.
- **Enhanced Diagnostics**: Updated the interface sensor with a standard `mdi:lan` icon for better visibility and added internal tracking for the active scanning interface.

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
- **Mock Supervisor**: Implemented service in the DevContainer to allow for integration testing on systems where physical WiFi access is restricted within containers.

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
