# Internal Detailed Changelog: WiFi SSID Monitor

All notable changes to this project will be documented in this file.

---

## [1.6.0-dev6] - 2026-06-11 - Unreleased

### Changed

- **Test Coverage**: `__init__.py` coverage increased from 88% to 100% (overall 96% → 100%) with new tests for `scan_now`, `clear_last_seen`, and `set_known_ssids` service paths.

### Fixed

- **`test_coordinator_async_initialize_with_corrupt_data`**: Updated test to use store mock exception instead of invalid date string, which no longer exercises the error path under the new `asyncio.gather(return_exceptions=True)` loading pattern.

---

## [1.6.0-dev4] - 2026-06-11 - Unreleased

### Added

- **"First Seen" Persistent Timestamps**: `_first_seen` dict backed by a dedicated `Store` (`.storage/wifi_ssid_monitor.<entry_id>.first_seen`). Written once per SSID on first detection — never overwritten. Exposed as `first_seen` ISO-timestamp dict attribute on `unknown_count`. TTL expiry prunes `first_seen` entries simultaneously with `last_seen` and `visit_counts`.
- **Unknown SSID Visit Count**: `_visit_counts` dict backed by a dedicated `Store` (`.storage/wifi_ssid_monitor.<entry_id>.visit_counts`). Incremented each scan cycle the SSID is present. Exposed as `visit_counts` int dict attribute on `unknown_count`.
- **Dedicated Strongest Unknown RSSI Sensor** (`sensor.strongest_unknown_rssi`): `SensorDeviceClass.SIGNAL_STRENGTH`, `native_unit_of_measurement="dBm"`, guard band −100–0 dBm. Allows native HA history graphing and numeric automation conditions without attribute extraction.
- **`scan_now` Service** (`wifi_ssid_monitor.scan_now`): Triggers `coordinator.async_refresh()` for one or all entries. Optional `config_entry_id` field. Registered in `async_setup` alongside other domain services.
- **`clear_last_seen` Service** (`wifi_ssid_monitor.clear_last_seen`): Silently clears `_last_seen`, `_first_seen`, and `_visit_counts` and saves empty state to all three Stores. The next scheduled scan repopulates from scratch. No re-scan triggered. Optional `config_entry_id` field.
- **`set_known_ssids` Service** (`wifi_ssid_monitor.set_known_ssids`): Replaces the entire known networks list in a single call. Returns the previous list per entry as service response data (`SupportsResponse.OPTIONAL`). Triggers an immediate re-scan. Optional `config_entry_id` field.
- **`_resolve_entries()` Helper**: Internal helper in `__init__.py` deduplicates entry-resolution logic across all multi-entry service handlers. Raises `HomeAssistantError` (with `translation_key="entry_not_found"`) when a supplied `config_entry_id` matches no loaded entry.
- **`async_remove_entry` Hook**: Removes all three Stores when an integration entry is deleted, preventing orphaned `.storage` files.

### Changed

- **`coordinator.py` — Three Stores**: `async_initialize()` now loads all three Stores in parallel via `asyncio.gather(return_exceptions=True)` with independent error handling per Store. All three are saved in parallel via `asyncio.gather()` after each scan cycle. TTL expiry prunes `last_seen`, `first_seen`, and `visit_counts` simultaneously using a shared `expired` set.

### Fixed

- **mypy strict errors** in `coordinator.py:async_initialize`: Changed `isinstance(x, Exception)` to `isinstance(x, BaseException)` for Store load results from `asyncio.gather(return_exceptions=True)`. mypy infers the exception union as `T | BaseException` (not `T | Exception`), so only `BaseException` correctly narrows the union in the `elif` data branches.
- **HASSFest `services.yaml` validation errors**: Removed unsupported `response` and `target` keys from the `set_known_ssids` service definition. The HASSFest schema version used by this project does not accept these keys. `SupportsResponse.OPTIONAL` in the Python handler controls runtime response behaviour; the services.yaml entry is UI documentation only.

---

## [1.6.0-dev1] - 2026-06-11 - Unreleased

### Added

- **`remove_known_ssid` Service** (`wifi_ssid_monitor.remove_known_ssid`): Removes an exact SSID or `fnmatch` pattern from the known list. Silent success if the SSID is not present. Triggers an immediate re-scan when the list changes. Optional `config_entry_id` field.
- **Strongest Unknown SSID Name Sensor** (`sensor.strongest_unknown_ssid`): State is the SSID name of the unknown network with the strongest signal. State is `unknown` when no unknown networks are visible.
- **Persistent "Last Seen" Storage**: `_last_seen` dict is now backed by HA's `Store` (`.storage/wifi_ssid_monitor.<entry_id>.last_seen`). Timestamps survive HA restarts. `async_initialize()` (called from `async_setup_entry` before the first background scan) loads persisted data. Store is removed via `async_remove_entry` when the entry is deleted.
- **Auto-Expire Stale "Last Seen" Entries** (`last_seen_ttl_days`): Configurable TTL in the options flow (range 0–366 days; 0 = keep forever; default 90 days). Applied on each successful scan immediately before saving to the Store. Entries not seen within the TTL window are pruned.
- **Band Filter Option** (`scan_bands`): Options flow dropdown (`all` / `2.4` / `5`). Filters all scan results — network counts, sensor attributes, and known-network matching — not just band display. APs with an undetermined band are excluded (strict exclusion) when any filter other than `all` is active.
- **SSID Denylist** (`denylist_ssids`): Options flow field accepting comma-separated `fnmatch` patterns. SSIDs matching any denylist pattern are always counted as unknown regardless of the known list. Denylist takes priority over the known list for SSIDs that match both.

### Changed

- **`coordinator.py` — `async_initialize()`**: New explicit method replaces the abandoned `_async_setup()` hook (which is never invoked when the integration uses `coordinator.async_refresh()` rather than `async_config_entry_first_refresh()`). Called directly from `async_setup_entry` before the first background refresh.
- **Options flow**: Added `scan_bands`, `denylist_ssids`, and `last_seen_ttl_days` fields to `WifiScanOptionsFlowHandler.async_step_init`. `strings.json` and `translations/en.json` updated with descriptions and warnings for each new field.

---

## [1.5.0-dev6] - 2026-06-11 - Unreleased

### Changed

- **Validation Sync**: Moved to a better system and process to keep validation (lint/format/test) tools in sync, across PlayFaster projects and between the projects and what Home Assistant uses.
  - .validate/version_matrix.json added as the definitive source of tool version use.
  - Several Env: entries added to .vscode/tasks.json for tool sync and checking.
  - .validate/requirements_test.txt pulled as generic, with all tools pinned to versions, and requirements_custom.txt used to add project specific items.
  - As part of the sync, docker-compose.yml and devcontainer.json are now generic, with a .env file holding project specific info and a docker-compose.override.yml holding additional, project specific steps.
  - HA Manifest and HACS schema files updated.
  - Ruff updated from 0.15.12 to 0.15.15

## [1.5.0-dev5] - 2026-06-07 - Unreleased

### Changed

- **README Emoji Consistency**: Replaced all VS16 compound emoji in headings and ToC links with always-colour single-codepoint alternatives (`⚙️`→`🔧`, `🗑️`→`❌`, `⚠️`→`❗`, `⏱️`→`🔁`, `✉️`→`💬`, `⏯️`→`🔁`, `🛠️`→`🔩`, `🎛️`→`🔘`); moved License badge out of heading; standardised Use Cases icon to `🎯`.

- **`pyproject.toml` — mypy Configuration Realigned with HA's Internal `mypy.ini`**: The project's `[tool.mypy]` section has been restructured to closely match HA's auto-generated `mypy.ini` (produced by `script/hassfest -p mypy_config`). This ensures the pre-commit mypy hook, and the project's basic `mypy custom_components/` check, run under materially the same conditions as HA's own integration quality checks. The goal is for any type errors caught here to be errors HA itself would also catch — and vice versa.

## [1.5.0-dev4] - 2026-06-03 - Unreleased

### Changed

- **`action-setup` fix**: `add_known_ssid` service registration moved from `async_setup_entry` (with `has_service` guard) to `async_setup`. Service is now domain-lifecycle-managed — active for the domain's loaded state, no per-entry guard or cleanup needed. `async_unload_entry` simplified accordingly (service cleanup logic removed).
- **Config flow dead code removal**: Removed two unreachable `else: cv.string` branches from `async_step_reconfigure` and `WifiScanOptionsFlowHandler.async_step_init` in `config_flow.py`. The `current_interface` fallback guard that runs immediately before the conditional guarantees `available_interfaces` is always non-empty, making the `else` branches dead code. `config_flow.py` coverage is now 100%.
- **Exception translations**: `HomeAssistantError` raises in `button.py` (`async_press`) and `__init__.py` (service handler) now include `translation_domain`, `translation_key`, and `translation_placeholders` for UI-translatable error messages. `exceptions` section added to `strings.json` and `translations/en.json` (`scan_failed`, `entry_not_found` keys).

---

## [1.5.0-dev3] - 2026-06-03 - Unreleased

### Fixed

- **`button.async_press` error propagation**: `async_press` now checks `coordinator.last_update_success` after calling `async_refresh()` and raises `HomeAssistantError` when False. Previously the button always reported success to the caller, making it impossible for automations to detect a failed scan. The fix correctly uses `last_update_success` rather than the return value of `async_refresh()` (which always returns `None`, not a bool — the proposed fix in the code review document was incorrect on this point; see `.notes/code_review/code_review_20260602.md`).
- **`add_known_ssid` service silent no-op on bad `config_entry_id`**: Service handler now raises `HomeAssistantError(f"No {DOMAIN} entry found with ID '{target_entry_id}'")` when a `config_entry_id` is provided but does not match any loaded entry. Previously a mistyped or stale entry ID silently did nothing.
- **`async_unload_entry` service lifecycle cleanup**: `async_unload_entry` now removes the `add_known_ssid` domain service when the last config entry is unloaded. The remaining-entries check explicitly filters out the entry currently being unloaded (which is still present in `async_entries(DOMAIN)` during the unload call) — the proposed fix in the code review document contained a bug that would have prevented removal; see `.notes/code_review/code_review_20260602.md`.

### Changed

- **Supervisor URL constant**: Extracted `_SUPERVISOR_BASE_URL = "http://supervisor"` as a named module-level constant in `api.py`. Both endpoint URL constructions now use this constant. No behavioural change.

---

## [1.5.0-dev2] - 2026-06-02 - Unreleased

### Added

- **Level 1 Deeper Testing**: Implemented all 14 findings from recommendations_20260602.md — 22 new tests across 5 files. Coverage: BVA boundary-value tests for `_channel_to_band`, `WifiProximityBinarySensor.is_on`, and sensor guard bands; combinatorial tests for `include_hidden`, `fnmatch` wildcard matching, and proximity sensor unit tests; error-path tests for `ValueError` in JSON decode (`get_access_points` and `get_interfaces`); assertion gap tests for `proximity_alert` check, `signal_strengths`/`bands` attributes, `networks`/`last_seen`/`strongest_unknown_rssi` return validation, hidden network band/strongest_rssi assertions, and `add_known_ssid` runtime deduplication.

### Changed

- **Coverage**: `__init__.py` coverage increased from 76% to 100% (overall 95% → 98%) with 4 new tests for data-to-options migration and `add_known_ssid` service paths.
- **Docstrings**: Fixed 18 D103 missing-docstring violations across `test_coordinator.py`, `test_binary_sensor.py`, `test_api.py`, and `test_init.py`.

---

## [1.5.0-dev1] - 2026-06-02 - Unreleased

### Added

- **Manual Scan Button**: New `button` platform with a `scan_now` entity. Pressing it calls `coordinator.async_refresh()` for an immediate on-demand scan without waiting for the next scheduled interval.
- **Proximity Alert Binary Sensor**: New `binary_sensor.proximity_alert` entity — fires when the strongest unknown SSID signal meets or exceeds a configurable RSSI threshold (default −60 dBm). Exposes `strongest_unknown_rssi` and `threshold` as state attributes.
- **`add_known_ssid` Service**: New `wifi_ssid_monitor.add_known_ssid` HA service. Appends an SSID to the known list and triggers an immediate re-scan via the existing update listener. Accepts optional `config_entry_id` to target a specific entry; if omitted, updates all entries. Documented in `services.yaml`.
- **Include Hidden Networks Toggle** (`CONF_INCLUDE_HIDDEN`): New boolean option in the options flow (default: `True`). When disabled, APs without a broadcasted SSID are filtered out entirely before processing — they no longer appear in counts or attributes.
- **Proximity Alert Threshold** (`CONF_PROXIMITY_RSSI_THRESHOLD`): New integer option in the options flow (range: −100 to −30 dBm, default: −60 dBm). Controls the signal strength at which the Proximity Alert sensor fires.

### Changed

- **Pattern Matching for Known SSIDs**: Replaced exact-string comparison with `fnmatch.fnmatch()` for known SSID matching. Existing comma-separated exact-match lists continue to work unchanged; wildcards (`Guest_*`, `IoT_?`) are now also supported.
- **Band Identification**: `coordinator.py` now computes the WiFi band for each network via `_channel_to_band()` helper (channels 1–14 → `"2.4 GHz"`, 36–177 → `"5 GHz"`). Band is stored in `network_map` and exposed in sensor attributes.
- **Signal Strength Attributes**: `signal_strengths` (RSSI per SSID) and `bands` (band per SSID) dicts added to `count` and `unknown_count` sensor `extra_state_attributes`.
- **Last Seen Timestamps**: In-memory `_last_seen` dict tracks the datetime each SSID was last detected. ISO-format timestamps are exposed in the `unknown_count` sensor's `last_seen` attribute. Resets on HA restart (no cross-restart persistence by design).
- **Coordinator Data Keys**: `coordinator.data` now includes `band` per network entry, `last_seen` (dict of SSID → datetime), and `strongest_unknown_rssi` (int | None).
- **`__init__.py`**: Added `"button"` to PLATFORMS; registered `add_known_ssid` service with `has_service` guard to avoid duplicate registration on multi-entry setups.
- **Version**: Bumped to `1.5.0-dev1` (minor version increment; reflects significant feature additions).

---

## [1.4.4-dev3] - 2026-06-02 - Unreleased

### Changed

- **Entity Category Imports**: Standardized `EntityCategory` imports to use `homeassistant.const` instead of `homeassistant.helpers.entity` in sensor and number platforms.
- **README Alignment**: Aligned the `README.md` layout and structure with the premium ZTE project template (adding compatibility grid, config parameter tables, and side-by-side screenshots).
- **Automation YAML Formatting**: Rewrote example automations to use standard block scalar `|` formatting and updated legacy time platform triggers to `trigger: time` syntax.

### Fixed

- **Mypy Strict Errors**: Resolved all 10 type errors logged in strict mode (correcting exception tuple syntax, wrapping forward type references in quotes in config flow, and removing unused type ignore comments).
- **Incorrect Entity IDs in Docs**: Updated all sensor entity ID references in `README.md` from `total_count` and `unknown_count` to `total_ssid_count` and `unknown_ssid_count` to match runtime IDs.

---

## [1.4.4-dev2] - 2026-05-13 - Unreleased

### Added

- Full IQS Review carried out , all open items implemented. IQS compliance is currently taken as far as it can go in this project.

### Changed

- **runtime-data** (IQS Bronze): Migrated coordinator storage from `hass.data[DOMAIN]` to `entry.runtime_data` in `__init__.py`, `sensor.py`, `binary_sensor.py`, `number.py`, `diagnostics.py`; `async_unload_entry` simplified — HA handles `runtime_data` cleanup automatically, no manual teardown needed.
- **parallel-updates** (IQS Silver): Added `PARALLEL_UPDATES = 0` to `sensor.py`, `binary_sensor.py`, `number.py`, signaling to HA that the coordinator handles all update coordination.
- **config-flow** (IQS Bronze): Added `data_description` contextual hints to all config and options flow steps in `strings.json` and `translations/en.json`.
- **docs-data-update** (IQS Gold): Added Data Updates section to `README.md` documenting polling endpoint, interval, 3-strike resilience, and immediate-refresh behaviour.
- **repair-issues** (IQS Gold): Implemented `ir.async_create_issue` / `ir.async_delete_issue` in `coordinator.py`; added `supervisor_unavailable` repair issue strings to `strings.json` and `translations/en.json`. Issue is raised on 4th consecutive failure and cleared on next successful scan.
- **quality_scale.yaml**: Rewrote to canonical 52-rule format; all 47 trackable rules now `done`.

### Fixed

- **Tests**: Updated `test_sensor.py`, `test_binary_sensor.py`, `test_number.py` to use `mock_config_entry.runtime_data = mock_coordinator` instead of `patch.dict(hass.data, {DOMAIN: ...})` injection — aligns test setup with runtime-data migration.

## [1.4.4-dev1] - 2026-05-13 - Unreleased

### Changed

- **icons.json**: Implemented icons.json standard, where all icons are defined in an icons.json file, not individual .py files.
- **mypy --strict**: Addressed all mypy type issues.

## [1.4.3] - 2026-05-10

### Changed

- **Readme**: Overhaul of the readme file, additional example automations, re-ordered for readability.
- **Under the Hood**: Several internal code changes to improve maintainability and alignment with Home Assistant development standards (no functional breaking changes).
- **Validations**: Improved local and automated remote testing to ensure code remains secure and follows best practices.

## [1.4.3-rc1] - 2026-05-10 - Unreleased

### Changed

- **Readme**: Updated Readme with additional information. Re-ordered some sections. Added more emoji icons to headings.
- **pyproject.toml**: pyproject.toml is now fully project agnostic. It does not contain the name of the specific project, instead just references the general custom_components folder for pytest coverage.
- **tasks.json**: tasks.json is also not fully project agnostic. It does require a settings.json file, but this now only requires one change per project.

## [1.4.3-dev20] - 2026-05-09 - Unreleased

### Dev Tooling

- **Shared Reusable CI Workflow**: Created `PlayFaster/.github` organisation repo containing a parameterised reusable workflow (`validate.yaml`, named "Validate (Shared)"). All 8 validation jobs (`hassfest`, `hacs_val`, `py_val`, `test_val`, `file_val`, `codespell`, `zizmor`, `mypy_val`) now live in the shared repo and are called by each integration via a thin caller. Changes to validation logic propagate to all 4 projects on the next CI run without per-project edits.
- **Thin Caller Workflow**: Replaced the 270-line inline `.github/workflows/validate.yaml` with a ~30-line caller that delegates to the shared workflow via `uses: PlayFaster/.github/.github/workflows/validate.yaml@main`. Permissions correctly scoped: `contents: read` at workflow level, `contents: write` and `pull-requests: write` at job level (required by `test_val` for coverage badge and PR comments).
- **Shared Workflow Concurrency**: Reusable workflow uses `${{ github.workflow }}-${{ github.ref }}-${{ github.repository }}` as its concurrency group, preventing cross-repo cancellation when multiple integrations trigger simultaneously.
- **Shared Workflow Dependabot**: Added `dependabot.yml` to `PlayFaster/.github` tracking the `github-actions` ecosystem weekly, keeping SHA pins in the shared workflow current.
- **Pre-commit: Suppress Inapplicable Hooks**: Added `stages: [manual]` to the `no-commit-to-branch` hook — direct commits to `main`/`dev` are the working pattern for this project, so the hook is retained for explicit use but removed from the default commit flow. Added `exclude: \.yamllint$` to the `yamllint` hook to prevent it from linting its own config file (which lacks `---` and uses CRLF).
- **VS Code Tasks**: Added `Zizmor: Fix (Safe Auto-Fix)` task (`zizmor --fix .github/`) for applying zizmor's safe auto-fixes on demand. Added `Pre-commit: Autoupdate Hooks` task (`pre-commit autoupdate`) for updating all hook `rev:` pins to their latest releases. Neither task is wired into `Fix All` or `Validate All`.

## [1.4.3-dev11] - 2026-05-09 - Unreleased

### Changed

- **mypy errors**: Addressed all type issues flagged by mypy tool (in HA mode, not --strict mode). Added type annotations to all functions, params, and return types.

## [1.4.3-dev4] - 2026-05-06 - Unreleased

### Added

- **Quality Scale**: Added quality_scale.yaml into project folder to track compliance to Home Assistant Integration Quality Scale (IQS). As a custom component full compliance is not possible but this is a good mechanism to ensure alignment with Home Assistant best practice.

### Changed

- **Coverage**: Test coverage improvements to sensor.py.

## [1.4.3-dev3] - 2026-05-06 - Unreleased

### Added

- **Diagnostics**: Implemented a diagnostics platform (`diagnostics.py`) to provide sanitized integration state for troubleshooting.
- **Reauthentication**: Added a reauthentication flow to handle invalid or expired Supervisor API tokens.
- **Reconfiguration**: Added a reconfiguration flow allowing users to update the interface and settings without re-installing.

### Changed

- **Translations**: Updated localized strings for reauth and reconfigure flows; verified entity translation keys.
- **Quality Standards**: Updated IQS compliance matrix in `ha_quality_standard.md` to reflect Silver/Gold progress.

### Fixed

- **Integration Stability**: Verified clean startup and error-free operation of the diagnostics component.

## [1.4.3-dev2] - 2026-05-06 - Unreleased

### Added

- **Documentation**: Created `docs/all_sensors.md` (Entity Manifest) and `docs/value_min_max.md` (Guard Bands) to provide clear reference for users and developers.

### Changed

- **Test Coverage**: Achieved 100% unit test coverage for `api.py` by adding exhaustive tests for error paths, including JSON decoding failures and connection issues.
- **Test Infrastructure**: Enhanced `MockResponse` in `conftest.py` to support simulated JSON content-type errors.

### Fixed

- **API Robustness**: Verified and fixed handling of malformed JSON responses in `api.py` (discovered during coverage testing).

## [1.4.3-dev1] - 2026-05-02 - Unreleased

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
