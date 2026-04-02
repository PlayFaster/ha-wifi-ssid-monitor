# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - Now

### Added

- **Added**: Added.
  
### Changed

- **README**: Improve screenshot visibility.
- **Tests and Coverage**: Added Testing and Coverage to GitHub Validation (previously only local).
- **Changed**: Changed.
  
### Fixed

- **Fixed**: Fixed.
  
### Removed

- **Removed**: Removed.
  
### Deprecated

- **Deprecated**: Deprecated.
  
### Security

- **Security**: Security
  
## [3.0.0] - 2026-04-01

### Added

- **Native Async Architecture**: Migrated the entire API and polling layer to `aiohttp` for native asynchronous execution.
- **Improved Performance**: Removed thread-based `executor_job` wrappers, aligning the integration with the Home Assistant event loop.
- **Dependency Simplification**: Removed `requests` as a required dependency, eliminating maintenance of version pinning.

### Changed

- **Version Bump**: Major version update to reflect the complete architectural shift.

## [2.3.1] - 2026-04-01

### Added

- **Development Documentation**: Added `DEVELOPMENT.md` containing architectural notes and project history.
- **Screenshots**: Added images to `README.md`.
- **Icon and Logo**: Added required assets for HACS and Home Assistant branding.
- **Automated Validation**: Integrated specialized GitHub Actions for Hassfest, HACS, and Python quality.

### Changed

- **Architecture Refactor**: Introduced `coordinator.py` to centralize and optimize data fetching logic.
  
### Fixed

- **Unavailable Bug**: Fixed an issue where sensors would never go unavailable due to misconfigured grace period.

## [2.2.4] - 2026-03-30

### Added

- **Coverage**: Added basic test coverage.

### Changed

- **Clean Code**: Code clean-up and formatting/linting rules.
- **Testing**: Improved scope of testing.
- **Strings**: Added strings.json in addition to en.json.
  
## [2.2.3] - 2026-03-30

### Added

- **Testing Infrastructure**: Added python tests.

### Fixed

- **Manifest**: Fixed manifest.json for GitHub tests.
  
## [2.1.1] - 2026-03-29

### Added

- **Error Logging**: Significantly improved home assistant (logger) error logging.
  
## [2.0.1] - 2026-03-29

### Added

- **Options Flow**: Allow reconfiguration of integration in-situ rather than delete and re-add.
  
## [1.9.4] - 2026-03-29

### Added

- **Model Number**: Pulls model number from device.
  
### Changed

- **Exception Handling**: Improved exception handling.
  
### Fixed

- **Strings and Translate**: Fixed strings en.json structure and moved all elements to this.
- **Sessions Handling**: Explicit closing of sessions.
  
## [1.8.1] - 2026-03-29

### Added

- **Strings and Translate**: Added translation folder structure, just en for now.
  
## [1.7.3] - 2026-03-29

### Fixed

- **Entity Naming**: Fixed entity sensor naming approach.
  
## [1.6.3] - 2026-03-28

### Changed

- **Reduced Startup Risk**: Moved to async for startup to avoid any potential for slowness/hangs/locks if router is unavailable at HA start.
  
## [1.5.7] - 2026-03-28

### Added

- **Integration Icon**: Added ZTE icons.
  
### Fixed

- **Sub Device Sensors**: Properly align sub device (data, sms) sensor naming.
  
## [1.5.1] - 2026-03-28

### Changed

- **Aligned Integration Naming**: All naming now ZTE Router 5G Monitor.
  
## [1.4.5] - 2026-03-28

### Added

- **Changelog**: Added Changelog (this) as CHANGELOG.md.
  
### Changed

- **Standard Names**: Changed specific sensor names (with ID tag) to standard names.

## [1.4.4] - 2026-03-28

### Added

- **All Relevant Attributes**: Added all relevant signal and status attributes available from the router as sensors.

## [1.4.3] - 2026-03-28

### Added

- **Pause Polling Switch**: New entity to manually halt API traffic to the router.
- **Polling Interval Slider**: Number entity to adjust the refresh rate (30s to 3600s) directly from the UI.
- **Persistence**: Integration now saves Polling State and Interval to `ConfigEntry` options, ensuring settings survive a Home Assistant restart.

### Fixed

- **Startup Deadlock**: Implemented "Initial Bypass" logic to ensure entities load correctly on restart even if polling was previously paused.
- **Boot Resilience**: Added a fail-safe to prevent the integration from becoming "Unavailable" if the router is unreachable during the initial Home Assistant startup sequence.

## [1.4.2] - 2026-03-27

### Added

- **SMS Monitoring**: Added sensors for SMS capacity (total/used) and a sensor to display the content of the latest received message.
- **Hybrid Resilience**: Implemented a "one-cycle grace period" where sensors hold their last known value during a single failed poll before marking as unavailable.
- **GitHub**: Initial release to GitHub repository.

## [1.4.1] - 2026-03-27

### Changed

- Refactored `DataUpdateCoordinator` to handle centralized data fetching for all platforms.
- Improved API login reliability with automatic protocol detection (HTTP/HTTPS).

## [1.4.0] - 2026-03-26

### Added

- Core sensors: Signal Strength (RSRP/RSRQ/SINR), Network Type, and Data Usage.
- Connection status binary sensor.
  
## [1.3.6] - 2026-03-25

### Added

- Initial release for ZTE MC7010 5G Router.
- Moved from one sensor with all data as sensor attributes to separate sensors.
- Added config flow.
- Added single device, then sub-devices (router, data, sms).
  
***
  
### Format
  
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
