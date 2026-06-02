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

## 3. Success Patterns (v1.5.0-dev1 additions in this section)

- **High Test Coverage**: The project maintains 99% test coverage across all core modules and the test suite itself.
- **Coordinator Logic**: Centralizing SSID deduplication and filtering in the `DataUpdateCoordinator` ensures that all entities share a consistent and optimized data set.
- **Retry Resilience**: The coordinator holds last known values for up to 3 consecutive fetch failures before marking entities unavailable. This handles transient Supervisor API restarts or brief network outages without entities toggling to "Unavailable". On the 4th consecutive failure, `UpdateFailed` is raised and HA marks entities unavailable as normal.
- **DevContainer Mocking**: Integrated a `mock_supervisor.py` service within the `docker-compose.yml` to simulate the Supervisor API. This allows developers on Windows to test the integration's logic despite virtualization limits on physical WiFi access.
- **Structured Data Model (v1.3.1)**: Refactored the coordinator's internal data model to use a dictionary mapping instead of simple lists. This architectural update allows for adding metadata like RSSI or channel info in the future without breaking changes.
- **Clean Entity Naming (v1.4.0)**: Implemented logic to omit the interface ID from entity names and the integration title for single-instance installations, while automatically appending it for multi-interface setups. This provides a cleaner UI experience for the majority of users.
- **Automated Migrations**: Added robust migration logic in `__init__.py` to seamlessly move configuration from legacy `entry.data` to `entry.options` and to update the integration title for existing single-instance users during upgrades.
- **Robust Debouncing**: Refined the scan interval adjustment in `number.py` to use a task-canceling debounce pattern, preventing race conditions and ensuring only the final user input is persisted to the configuration.
- **Enhanced API Resilience**: Improved error handling in `api.py` and `coordinator.py` by explicitly catching JSON decode errors and utilizing `from err` to preserve exception chains, providing much clearer diagnostic logs.
- **Non-Blocking Startup**: Removed the initial blocking data fetch during `async_setup_entry`. The integration now forwards platforms immediately and performs the first WiFi scan in a background task using `entry.async_create_background_task`. This ensures 0ms impact on Home Assistant boot times.
- **Declarative Patterns**: Migrated to a centralized `SENSOR_TYPES` definition using a custom `WifiSensorEntityDescription`. This pattern uses a callback-driven `value_fn` to isolate data extraction logic from the entity class, making the platform easier to extend and maintain.
- **Data Integrity (Guard Bands)**: Implemented validation for all network count sensors. Values are automatically checked against `min_limit` and `max_limit` (e.g., 0-256 for SSIDs) before being committed to the state machine, preventing dashboard corruption from transient API artifacts.
- **Resilient Holding**: Enhanced the coordinator to hold last known values for up to 3 consecutive fetch failures. This prevents entities from toggling to "Unavailable" during brief Supervisor API restarts or high-load events.
- **Custom User Naming**: Implemented global name prefixing. Users can define a custom string (e.g., "Guest WiFi") that is prepended to every device and entity, allowing for multiple instances to be clearly distinguished in the UI without technical entity ID conflicts.
- **Diagnostics Platform (v1.4.3-dev3)**: Implemented `diagnostics.py` to allow users to download a sanitized state dump. This is essential for troubleshooting and is a core requirement for the HA Gold tier.
- **Reauthentication & Reconfiguration (v1.4.3-dev3)**: Added UI-driven flows for token recovery and setting updates, significantly improving UX and reducing the need for integration re-installs.
- **`entry.runtime_data` Pattern (v1.4.4-dev2)**: The coordinator is stored on `entry.runtime_data` rather than `hass.data[DOMAIN]`. HA manages the lifecycle automatically — `async_unload_entry` needs no manual cleanup beyond unloading platforms. Platform files access it with `coordinator: WifiScanCoordinator = entry.runtime_data`. Update listeners (`async_reload_entry`) also read it directly. Tests set `mock_config_entry.runtime_data = mock_coordinator` before calling `async_forward_entry_setups`.
- **Repair Issues (v1.4.4-dev2)**: Persistent API failures surface in the HA Repairs panel via `ir.async_create_issue(hass, DOMAIN, "supervisor_unavailable", ...)`. The issue is cleared with `ir.async_delete_issue()` on the next successful scan. Issue title/description strings live under the `"issues"` key in `strings.json` and `translations/en.json`, keyed by the issue id (`supervisor_unavailable`).
- **Button Platform (v1.5.0-dev1)**: The `button` entity has no state value — it exists solely for its `async_press()` action. The implementation simply calls `await self._coordinator.async_refresh()`. No `CoordinatorEntity` inheritance is needed because buttons don't display coordinator data; they just trigger it. This is the lightest possible HA entity pattern.
- **`fnmatch` Pattern Matching (v1.5.0-dev1)**: Replaced exact-string known SSID comparisons with `fnmatch.fnmatch(ssid, pattern)`. This is backward-compatible — existing strings without wildcards behave as exact matches. Case-sensitive by design (SSIDs are case-sensitive byte strings). The check is a simple `any(fnmatch.fnmatch(ssid, p) for p in known_patterns)` per SSID.
- **Channel-to-Band Helper (v1.5.0-dev1)**: `_channel_to_band(channel)` maps channel integers to band strings (`"2.4 GHz"`, `"5 GHz"`). Channel data comes from the Supervisor API's `channel` field on each access point. Channels 1–14 = 2.4 GHz; 36–177 = 5 GHz. Returns `None` for out-of-range values or missing channel data. Band is stored in `network_map` alongside `rssi` and `channel`.
- **In-Memory Last Seen Tracking (v1.5.0-dev1)**: `self._last_seen: dict[str, datetime]` on the coordinator accumulates the datetime each SSID was last detected. It persists across polls (in-memory only — resets on HA restart). The full dict is included in `coordinator.data["last_seen"]` each refresh cycle. Entities that want "last seen" data read it from `coordinator.data`, not from `self._last_seen` directly. Old SSIDs that disappear from scans are not pruned — they remain in `_last_seen` indefinitely.
- **Domain Service Registration Pattern (v1.5.0-dev1)**: Domain-scoped services (not entity services) are registered in `async_setup_entry` using a `hass.services.has_service(DOMAIN, name)` guard so that multiple config entries don't duplicate the registration. The handler dynamically reads `hass.config_entries.async_entries(DOMAIN)` at call time, so it always targets live entries. No unregistration is performed on entry unload — the service gracefully no-ops when no entries exist. This avoids complex reference-counting at the cost of a stale service registration if all entries are removed (harmless and cleaned up on HA restart).
- **`services.yaml` (v1.5.0-dev1)**: Service descriptions for the HA Developer Tools UI live in `custom_components/wifi_ssid_monitor/services.yaml`. The `selector: config_entry: integration: wifi_ssid_monitor` selector renders a dropdown in the UI scoped to this integration's entries.

## 4. Technical Pitfalls & Fixes

- **Line-Ending Sensitivity**: Alpine Linux shell scripts in the devcontainer are highly sensitive to Windows-style carriage returns (`\r\n`). The `setup.sh` script has been hardened to avoid `if/fi` syntax (which breaks on corrupted line endings) and uses a series of `&&` commands with clean path resolution via `tr -d '\r'`.
- **Testing Custom Components**: Standard `pytest` runs fail to load custom components unless the `enable_custom_integrations` fixture is active in `conftest.py`.
- **ConfigEntry State**: Forwarding setups in unit tests requires the `ConfigEntry` to be in the `LOADED` state. Using `mock_config_entry.mock_state(hass, ConfigEntryState.LOADED)` is essential.
- **Return Values**: `async_forward_entry_setups` returns `None`. Asserting its result in tests will cause failures.
- **Options Management**: Configuration options must be updated via `hass.config_entries.async_update_entry()` rather than direct assignment to the `options` attribute.
- **Title Updates**: Similar to options, `ConfigEntry.title` is protected and cannot be assigned to directly. It must be updated using `async_update_entry(entry, title="New Title")`.
- **Options Flow Validation**: Initial versions lacked validation in the reconfiguration step. The `OptionsFlow` now verifies interface changes against the Supervisor API before saving to prevent invalid runtime states.
- **`runtime_data` in Platform Tests**: When tests call `async_forward_entry_setups` directly (bypassing `hass.config_entries.async_setup`), `entry.runtime_data` is not populated automatically. Set `mock_config_entry.runtime_data = mock_coordinator` before calling `async_forward_entry_setups`. The old pattern of `patch.dict(hass.data, {DOMAIN: {entry_id: coordinator}})` is obsolete after the runtime-data migration and will cause `AttributeError: 'MockConfigEntry' object has no attribute 'runtime_data'`.
- **Windows WiFi Access**: Containers on Windows (via Docker Desktop/WSL2) cannot directly access physical WiFi hardware for scanning. The `mock_supervisor` service provides a reliable alternative for UI and logic validation.
- **Hidden Network Deduplication**: All APs without a broadcasted SSID are normalised to the key `"[hidden]"` in both `all_ssids` (set deduplication) and `network_map`. If three hidden APs are visible, the total count shows 1 and `network_map["[hidden]"]` stores only the last AP's RSSI/channel (overwritten each pass). This is intentional — hidden networks are indistinguishable by name — but means the count will not match tools like `nmcli` that report each hidden AP separately. BSSID-based tracking (see `FUTURE.md`) would resolve this.

## 5. Environment Constraints

- **Native Async API**: The integration uses `aiohttp` for all network communication, aligning with the Home Assistant event loop.
- **Supervisor API**: This integration requires Home Assistant to be running in an environment with the Supervisor (HA OS or Supervised). It uses the internal `http://supervisor` endpoint and `SUPERVISOR_TOKEN`.
- **Testing Dependencies**: Robust testing relies on `pytest-homeassistant-custom-component` and `pytest-asyncio`.
- **Branding Assets**: Generic branding (WiFi signal + magnifying glass) was generated using Python's `Pillow` library to ensure a clean, modern aesthetic independent of hardware-specific imagery.

---

## Version Control

- **v1.0.1** (2026-04-01) - Created.
- **v1.0.2** (2026-05-06) - Updated with diagnostics and flow management patterns.
- **v1.0.3** (2026-05-13) - Added `entry.runtime_data` pattern, repair issues pattern, and `runtime_data` test pitfall (v1.4.4-dev2).
- **v1.0.4** (2026-06-02) - Added button platform, fnmatch matching, channel-to-band helper, in-memory last seen tracking, and domain service registration patterns (v1.5.0-dev1).
