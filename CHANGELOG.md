# Changelog

All notable changes to this project will be documented in this file.

## [1.4.0] - 2026-04-05

### Added

- **WiFi Interface Auto-Discovery**: The setup and options flows now automatically detect and list available WiFi interfaces from the Supervisor, providing a user-friendly dropdown selection.
- **Enhanced Device Info**: Standardized the Device Info card to show the configuration entry title, manufacturer, version, and active interface.

### Fixed

- **Stability**: Resolved a critical race condition in the scan interval debounce logic that could lead to data loss or UI inconsistency.
- **API Error Handling**: Resolved exception double-wrapping in the API and ensured interface discovery raises proper errors instead of failing silently.
- **Config Flow Robustness**: Eliminated sentinel values during setup and improved validation of user-selected interfaces in the options flow.
- **Coordinator Stability**: Added defensive null checks and improved accuracy of hidden network reporting and signal tracking.
- **Hidden Networks**: Improved detection and logging of hidden WiFi networks (APs without a broadcasted SSID).
- **Migration**: Added automated migration of configuration settings for users upgrading from older versions.
- **Test Suite**: Fixed critical `TypeError` across the test suite and resolved schema validation failures in config flow tests.
- **Code Quality**: Resolved multiple Ruff linting errors including line length violations and missing docstrings.

### Changed

- **Dependency Reduction**: Removed `AwesomeVersion` to simplify version handling and reduce external dependencies.
- **Scan Interval Precision**: Improved the accuracy of scan interval updates by using rounded division when converting between units.
- **UX**: Improved the reconfiguration experience by adding immediate validation for the selected network interface.
- **Logging**: Refined log levels to reduce noise during expected recovery paths (e.g., retries).
- **Tests**: Expanded the test suite to achieve 92% coverage, including new paths for API validation and hidden network logic.

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
