# Development & Architecture Notes: WiFi SSID Monitor

## 1. Project Objective

To develop a native Home Assistant custom component that scans for SSIDs using the local system's WiFi via the Supervisor Network API. This integration replaces basic shell scripts with a robust, polled integration that provides counts and SSID lists.

## 2. Architecture & File Structure

The integration follows the standard Home Assistant Custom Component pattern, optimized for asynchronous performance.

### Core Files (`custom_components/wifi_ssid_monitor/`)

- **`api.py`**: Async wrapper for the Supervisor Network API using `aiohttp`.
- **`coordinator.py`**: `DataUpdateCoordinator` implementation. Centralizes polling logic, handles deduplication, and manages comparison against known SSIDs.
- **`__init__.py`**: Manages the integration lifecycle (setup/unload).
- **`sensor.py`**: Defines sensors for total count and unknown count.
- **`binary_sensor.py`**: Implements the "New Network Alert" logic.
- **`number.py`**: Provides UI control over the scan interval with persistent storage.
- **`config_flow.py`**: Manages initial setup and reconfiguration via `OptionsFlow`.

## 3. Success Patterns
- **High Test Coverage**: The project maintains 99% test coverage across all core modules and the test suite itself.
- **Coordinator Logic**: Centralizing SSID deduplication and filtering in the `DataUpdateCoordinator` ensures that all entities share a consistent and optimized data set.
- **Retry Resilience**: Implemented a two-stage fetch attempt with a 10-second delay to handle transient Supervisor API unavailability.
- **DevContainer Mocking**: Integrated a `mock_supervisor.py` service within the `docker-compose.yml` to simulate the Supervisor API. This allows developers on Windows to test the integration's logic despite virtualization limits on physical WiFi access.
- **Structured Data Model (v1.3.1)**: Refactored the coordinator's internal data model to use a dictionary mapping instead of simple lists. This architectural update allows for adding metadata like RSSI or channel info in the future without breaking changes.


## 4. Technical Pitfalls & Fixes

- **Testing Custom Components**: Standard `pytest` runs fail to load custom components unless the `enable_custom_integrations` fixture is active in `conftest.py`.
- **ConfigEntry State**: Forwarding setups in unit tests requires the `ConfigEntry` to be in the `LOADED` state. Using `mock_config_entry.mock_state(hass, ConfigEntryState.LOADED)` is essential.
- **Return Values**: `async_forward_entry_setups` returns `None`. Asserting its result in tests will cause failures.
- **Options Management**: Configuration options must be updated via `hass.config_entries.async_update_entry()` rather than direct assignment to the `options` attribute.
- **Windows WiFi Access**: Containers on Windows (via Docker Desktop/WSL2) cannot directly access physical WiFi hardware for scanning. The `mock_supervisor` service provides a reliable alternative for UI and logic validation.

## 5. Environment Constraints

- **Native Async API**: The integration uses `aiohttp` for all network communication, aligning with the Home Assistant event loop.
- **Supervisor API**: This integration requires Home Assistant to be running in an environment with the Supervisor (HA OS or Supervised). It uses the internal `http://supervisor` endpoint and `SUPERVISOR_TOKEN`.
- **Testing Dependencies**: Robust testing relies on `pytest-homeassistant-custom-component` and `pytest-asyncio`.
- **Branding Assets**: Generic branding (WiFi signal + magnifying glass) was generated using Python's `Pillow` library to ensure a clean, modern aesthetic independent of hardware-specific imagery.
