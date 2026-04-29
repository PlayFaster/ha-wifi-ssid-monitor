# Changelog: WiFi SSID Monitor

All notable changes to this project will be documented in this file.

## [1.4.2] - Unreleased

### Fixed

- **Readme**: Typo in Readme.

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
