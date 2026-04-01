# Development & Architecture Notes: Wifi Scan SSID

## 1. Project Objective
To develop a native Home Assistant custom component that scans for SSIDs using the local system's WiFi via the Supervisor Network API. This integration replaces basic shell scripts with a robust, polled integration that provides counts and SSID lists.

## 2. Architecture & File Structure
The integration follows the standard Home Assistant Custom Component pattern, optimized for asynchronous performance.

### Core Files (`custom_components/wifi_scan_ssid/`)
- **`api.py`**: Async wrapper for the Supervisor Network API using `aiohttp`.
- **`coordinator.py`**: `DataUpdateCoordinator` implementation. Centralizes polling logic and handles the comparison against known SSIDs.
- **`__init__.py`**: Manages the integration lifecycle (setup/unload).
- **`sensor.py`**: Defines sensors for total count and unknown count.
- **`config_flow.py`**: Manages initial setup and reconfiguration via `OptionsFlow`.

## 3. Environment Constraints
- **Native Async API**: The integration uses `aiohttp` for all network communication, aligning with the Home Assistant event loop.
- **Supervisor API**: This integration requires Home Assistant to be running in an environment with the Supervisor (HA OS or Supervised). It uses the internal `http://supervisor` endpoint and `SUPERVISOR_TOKEN`.
