# Development & Architecture Notes: ZTE Router 5G Monitor

## 1. Project Objective
To develop a high-performance Home Assistant custom component for monitoring and managing ZTE 5G Routers (MC801, MC888, MC7010, MC889 series). The integration leverages the router's internal `goform` API to extract signal metrics (RSRP, RSRQ, SNR), data usage, and SMS management features into the Home Assistant ecosystem.

## 2. Architecture & File Structure
The integration follows the standard Home Assistant Custom Component pattern, optimized for asynchronous performance.

### Core Files (`custom_components/zte_router_5g/`)
- **`api.py`**: Async wrapper for the router's internal `goform` API using `aiohttp`. Handles Z-hashed authentication, hex decoding, and protocol detection (HTTP/HTTPS).
- **`coordinator.py`**: Specialized `DataUpdateCoordinator` implementation. Centralizes polling logic to ensure only one API call is made per refresh interval, distributing data to all entities. Includes retry logic and "Pause Polling" detection.
- **`__init__.py`**: Manages the integration lifecycle (setup/unload). Also handles background initialization to prevent blocking HA startup.
- **`sensor.py`**: Extracts technical metrics and handles transformations (e.g., Bytes to GB, Uptime to ISO Datetime).
- **`binary_sensor.py`**: Maps boolean states (e.g., `best_connection` logic).
- **`switch.py`**: Implements "Pause Polling" to stop API calls without disabling the integration, allowing temporary exclusive access to the router WebUI.
- **`button.py`**: Triggers stateless actions (Reboot, Delete All SMS).
- **`number.py`**: Provides UI control over the `DataUpdateCoordinator` refresh interval with persistent storage in `ConfigEntry` options.
- **`config_flow.py`**: Manages initial setup and reconfiguration via `OptionsFlow`, storing credentials in `entry.options`.

## 3. Historical Architectural Shifts
To reach its current "modern" state, the project underwent two major refactors:

### From Monolithic to Orchestrated (v2.2.4 -> v2.3.1)
- **Initial State**: All data fetching and coordination logic resided within `__init__.py`.
- **Change**: Extracted fetching logic into a dedicated `coordinator.py`.
- **Result**: Improved separation of concerns, where `__init__.py` handles lifecycle and `coordinator.py` handles data. This aligned the project with Home Assistant's professional development standards.

### From Synchronous to Native Async (v2.3.1 -> v3.0.0)
- **Initial State**: Used the `requests` library, which is synchronous and blocking. This required wrapping every API call in `hass.async_add_executor_job` to avoid stalling the HA event loop.
- **Change**: Migrated the entire API layer to `aiohttp`.
- **Result**: Native asynchronous execution. Removed the overhead of thread-switching, simplified the code by removing executor wrappers, and eliminated the need to pin and maintain the `requests` dependency in `manifest.json`.

## 4. Success Patterns
- **`DataUpdateCoordinator`**: Essential for preventing the router from being overwhelmed by simultaneous requests. Using `coordinator.async_request_refresh()` for write actions ensures immediate UI feedback.
- **Protocol Discovery**: The `api.try_set_protocol` method identifies whether a router is on HTTP or HTTPS by attempting short-timeout requests before authentication.
- **Background Safety**: Connection and login are offloaded to a background task in `async_setup_entry` to ensure Home Assistant starts quickly even if the router is slow to respond.
- **Single-Domain Discovery**: Configuring `hacs.json` to be minimal allows HACS to automatically discover the domain and class from the `manifest.json`.

## 5. Technical Pitfalls & Fixes
- **Catching `AbortFlow`**: Using a generic `except Exception:` block in `config_flow.py` can break HA’s "Already Configured" logic.
  - *Fix*: Explicitly allow `AbortFlow` to propagate before catching generic exceptions.
- **NTFS/OneDrive Locking**: Development within OneDrive-synced Windows folders causes intermittent `.git` corruption and `PermissionError` during test runs.
- **MappingProxy TypeError**: In unit tests, `ZTEConfigFlow().context` is a read-only `mappingproxy`.
  - *Fix*: Explicitly set `flow.context = {}` in test setups.
- **HACS Branch Resolution**: HACS validation actions on non-default branches (like `dev`) often fail to find the manifest or brand assets.
  - *Fix*: Explicitly provide the repository context as `repository: ${{ github.repository }}@${{ github.ref_name }}` in the workflow.

## 6. Environment Constraints
- **Native Async API**: The integration uses `aiohttp` for all network communication, aligning with the Home Assistant event loop. This removes the need for `executor_job` threading and eliminates the maintenance burden of pinning external libraries like `requests`.
- **SSL Verification**: Local routers typically use self-signed certificates. The `ZTERouterAPI` uses `ssl=False` in its `aiohttp` calls to maintain connectivity.
- **Shared Session**: The integration uses `async_get_clientsession(hass)` to leverage Home Assistant's optimized, shared connection pool.

## 7. Technical Debt & Future Work
- **Token Persistence**: Currently, the `stok` (Session Token) is stored in memory. A fresh login is required on every integration restart.
- **SMS Page Limits**: The `delete_all` feature is limited to the first 500 messages to avoid API timeouts.
- **Debounce Dependency**: The `ZTEPollingInterval` entity uses an `asyncio.sleep(2)` debounce. This creates a task that must be handled carefully in unit tests to avoid `UnraisableExceptionWarnings`.
