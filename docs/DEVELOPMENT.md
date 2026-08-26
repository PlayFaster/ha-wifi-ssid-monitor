# Development & Architecture Notes: WiFi SSID Monitor

## 1. Project Objective

To develop a native Home Assistant custom component that scans for SSIDs using the local system's WiFi via the Supervisor Network API. This integration replaces basic shell scripts with a robust, polled integration that provides counts and SSID lists.

## 2. Architecture & File Structure

The integration follows the standard Home Assistant Custom Component pattern, optimized for asynchronous performance.

### Core Files (`custom_components/wifi_ssid_monitor/`)

- **`api.py`**: Async wrapper for the Supervisor Network API using `aiohttp`. Sets `last_response_had_ap_key` for the health checks and accepts `type: wifi|wireless` in interface discovery.
- **`parse.py`**: The **payload normalization layer** - the single boundary that turns the raw Supervisor access-point dict into the internal shape (`normalize_access_point`), plus `frequency_to_channel`, `dbm_to_pct`, `normalize_essid`, `hidden_label`, `history_key`. Every downstream reader uses this shape; nothing touches raw keys.
- **`health.py`**: The self-diagnosis check catalog - small pure functions over a `ScanFacts` snapshot, run by `run_checks`. A future contract check is a one-line addition to `CHECKS`.
- **`coordinator.py`**: `DataUpdateCoordinator`. Fetch → normalize → filter → history → health. Holds `health_snapshot` **outside** `self.data`, the force-refresh flag, coalesced store saves, and the composite history key.
- **`entity.py`**: Shared `WifiScanEntity` base + `WifiAboutEntity` mixin + `build_device_info`. All platforms delegate `device_info` here - previously copy-pasted five times.
- **`services.py`**: Domain-global services (`add_ssid`/`remove_ssid`/`set_ssids` with `target`, `scan_now`, `clear_last_seen`, `get_networks`).
- **`__init__.py`**: Lifecycle, the one-time option migration (dBm→% threshold, `scan_bands`→switches), the `_LIVE_OPTION_KEYS` allow-list reload, flush-on-unload, delete-on-remove.
- **`sensor.py` / `binary_sensor.py` / `number.py` / `switch.py` / `button.py`**: Declarative platforms. Band/hidden/pause/threshold/interval are option-backed control entities.
- **`config_flow.py`**: Setup and reconfigure. Keeps identity + the two text lists + TTL; the tuned settings are entities now.
- **`diagnostics.py`**: Two-pass structural sanitizer - learns SSIDs/BSSIDs from the payload, pseudonymizes them everywhere including dict keys, preserves the diagnostic substance.

## 3. Success Patterns (v1.5.0-dev1 additions in this section)

- **High Test Coverage**: 100% line **and 100% branch** coverage across all core modules — **415 tests as of 2026-08-22**, with zero partial branches and zero zero-assertion tests. Mutation testing (`mutmut`, scoped by `.validate/mutmut_modules.txt`) checks that the tests actually detect a fault rather than merely executing the line. Scoped to `parse.py`, `diagnostics.py`, `health.py` and — since 2026-08-22 — `coordinator.py`: **1,307 mutants, 84.3% killed.** Why each module is on or off that list, and what it costs to add one, is recorded in `../.notes/test_pytest_issues/mutation_covered_not_covered.md`.

  **Coverage is necessary but not sufficient**, and this project has the evidence twice over. See §3c on the standards sweeps, which exist because the suite hit 100% while four standards had no working guard at all. And every fault fixed on 2026-08-06 — negative 6 GHz channel numbers, a health sensor silent for two polls, repair issues clobbering each other across entries — was found by deepening the tests against code already at 100% line coverage. None came from the field.

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
- **`entry.runtime_data` Pattern (v1.4.4-dev2)**: The coordinator is stored on `entry.runtime_data` rather than `hass.data[DOMAIN]`. HA manages the lifecycle automatically - `async_unload_entry` needs no manual cleanup beyond unloading platforms. Platform files access it with `coordinator: WifiScanCoordinator = entry.runtime_data`. Update listeners (`async_reload_entry`) also read it directly. Tests set `mock_config_entry.runtime_data = mock_coordinator` before calling `async_forward_entry_setups`.
- **Explicit Coordinator `config_entry` (HA polling option)**: Pass `config_entry=entry` to `DataUpdateCoordinator.__init__`. HA core's `_schedule_refresh()` reads `self.config_entry.pref_disable_polling` - the flag behind the "Enable polling for changes" system option - and skips arming the next timer when it's OFF (the "Scan Now" button and `homeassistant.update_entity` still fetch via `async_refresh` / `async_request_refresh`, which ignore the flag). Passing the entry explicitly is also required going forward: HA deprecated implicit `ContextVar` detection and reports it as an error from **2026.8** (the argument dates from **2024.8**, hence the minimum-HA bump to 2024.8.0). **Corrected 2026-08-03:** this bullet previously said the project has no "Pause Polling" switch, so the system option was the only route to manual-only updates. That was true when written and has not been since v2.0.0 — `switch.stop_polling` ships as a `CONFIG` entity. **The two are not equivalent and both are worth having:**

  |  | Pause Polling switch | "Enable polling for changes" = OFF |
  | :-- | :-- | :-- |
  | Level | This integration | Home Assistant system option |
  | Mechanism | `_async_update_data` returns cached data | The next timer is never armed |
  | Explicit actions | **Still fetch** — the force-refresh flag bypasses the pause | Still fetch (`async_refresh` ignores the flag) |
  | Visible in | The device page, and automatable as an entity | The integration's system options menu |

  The switch is the one to reach for: it is discoverable, scriptable, and honors explicit requests by design. The system option remains the harder stop, and is what `config_entry=entry` above exists to make work. Full write-up: `.shared/info/sys_options_enable_polling.md`.

- **Repair Issues (v1.4.4-dev2)**: Persistent API failures surface in the HA Repairs panel via `ir.async_create_issue(hass, DOMAIN, "conn_error", ...)`. The issue is cleared with `ir.async_delete_issue()` on the next successful scan. Issue title/description strings live under the `"issues"` key in `strings.json` and `translations/en.json`, keyed by the issue id (`conn_error`).
- **Button Platform (v1.5.0-dev1)**: The `button` entity has no state value - it exists solely for its `async_press()` action. The implementation simply calls `await self._coordinator.async_refresh()`. No `CoordinatorEntity` inheritance is needed because buttons don't display coordinator data; they just trigger it. This is the lightest possible HA entity pattern.
- **`fnmatch` Pattern Matching (v1.5.0-dev1)**: Replaced exact-string known SSID comparisons with `fnmatch.fnmatch(ssid, pattern)`. This is backward-compatible - existing strings without wildcards behave as exact matches. Case-sensitive by design (SSIDs are case-sensitive byte strings). The check is a simple `any(fnmatch.fnmatch(ssid, p) for p in known_patterns)` per SSID.
- **Channel-to-Band Helper (v1.5.0-dev1)**: `_channel_to_band(channel)` maps channel integers to band strings (`"2.4 GHz"`, `"5 GHz"`). Channel data comes from the Supervisor API's `channel` field on each access point. Channels 1–14 = 2.4 GHz; 36–177 = 5 GHz. Returns `None` for out-of-range values or missing channel data. Band is stored in `network_map` alongside `rssi` and `channel`.
- **In-Memory Last Seen Tracking (v1.5.0-dev1)**: `self._last_seen: dict[str, datetime]` on the coordinator accumulates the datetime each SSID was last detected. It persists across polls (in-memory only - resets on HA restart). The full dict is included in `coordinator.data["last_seen"]` each refresh cycle. Entities that want "last seen" data read it from `coordinator.data`, not from `self._last_seen` directly. Old SSIDs that disappear from scans are not pruned - they remain in `_last_seen` indefinitely.
- **Domain Service Registration Pattern (v1.5.0-dev4)**: Domain-scoped services (not entity services) are registered in `async_setup`, not `async_setup_entry`. `async_setup` runs once per domain lifetime - no `has_service` guard is needed and no un-registration is required in `async_unload_entry`. The handler dynamically reads `hass.config_entries.async_entries(DOMAIN)` at call time so it always targets live entries. Services registered in `async_setup` persist for the domain's loaded state. Contrast with the initial `async_setup_entry` + guard approach (used up to v1.5.0-dev3), which was replaced because the guard was a workaround for the wrong lifecycle method rather than a real solution.
- **`services.yaml` (v1.5.0-dev1)**: Service descriptions for the HA Tools UI live in `custom_components/wifi_ssid_monitor/services.yaml`. The `selector: config_entry: integration: wifi_ssid_monitor` selector renders a dropdown in the UI scoped to this integration's entries.
- **Button error propagation (v1.5.0-dev3, corrected 2026-08-06)**: `DataUpdateCoordinator.async_refresh()` returns `None` (not `bool`), so `if not await coordinator.async_refresh()` is always `True` and raises unconditionally. That much still holds.

  **The rest of the original pattern is now wrong, and copying it reintroduces a real bug.** It said to call `async_refresh()` and then check `coordinator.last_update_success`. Two things moved underneath it: the button routes through `async_force_refresh()` → `async_request_refresh()` (§1.6 of the cross-project checks), and that path is **debounced with a 10-second cooldown**. Inside the cooldown the call returns without fetching, so `last_update_success` still describes the run before — and a failed scan followed by a quick retry press reports failure again without having retried.

  **The correct pattern is to judge only a run that actually happened:**

  ```python
  before = self.coordinator.last_update_success_time
  await self.coordinator.async_force_refresh()
  if self.coordinator.last_update_success_time == before:
      return  # coalesced by the debouncer — not a failure
  if not self.coordinator.last_update_success:
      raise HomeAssistantError(...)
  ```

  `last_update_success` is still `True` throughout the 3-strike stale-hold window and `False` only when `UpdateFailed` is raised on the 4th consecutive failure. There are **three** outcomes to a press, not two: coalesced (silent), ran and failed (raise), ran and succeeded (silent).

- **`HomeAssistantError` with translation keys (v1.5.0-dev4)**: `HomeAssistantError` accepts `translation_domain`, `translation_key`, and `translation_placeholders` keyword args alongside the positional string message. The positional string is preserved as `str(exception)` - logging and test `match=` assertions continue to work unchanged. The UI picks up the translation key from the `"exceptions"` section of `strings.json` / `translations/en.json`. Pattern: `raise HomeAssistantError("fallback message", translation_domain=DOMAIN, translation_key="my_key", translation_placeholders={"param": value})`.
- **`HomeAssistantError` in service handlers on bad input (v1.5.0-dev3)**: Per the HA `action-exceptions` rule, service handlers must raise `HomeAssistantError` (not `ServiceValidationError`) for conditions that are the system's fault (e.g., unknown `config_entry_id`). For user input errors (e.g., invalid SSID format), `ServiceValidationError` is preferred. In this integration, an unmatched `config_entry_id` is treated as a caller error and raises `HomeAssistantError`.

- **Persistent Store Lifecycle - `async_initialize()` Pattern (v1.6.0-dev1)**: `HA Store` is the correct mechanism for cross-restart persistence of coordinator data (not `RestoreEntity`, which is entity-scoped). Three separate `Store[T]` instances are created in `__init__` with keys like `f"{DOMAIN}.{entry.entry_id}.last_seen"`. Data is loaded by an explicit `async_initialize()` method called from `async_setup_entry` **before** the first background refresh - this is required because `_async_setup()` is never called when the integration uses `coordinator.async_refresh()` rather than `async_config_entry_first_refresh()`. All three Stores are loaded in parallel via `asyncio.gather(return_exceptions=True)` with independent per-Store error handling. All three are saved in parallel via `asyncio.gather()` at the end of each scan. Stores are cleaned up by an `async_remove_entry` hook to prevent orphaned `.storage` files on entry deletion.
- **`asyncio.gather(return_exceptions=True)` - `BaseException` Narrowing (v1.6.0-dev4)**: When `return_exceptions=True`, mypy infers each result as `T | BaseException` (not `T | Exception`). Use `isinstance(x, BaseException)` not `isinstance(x, Exception)` to narrow the union - only `BaseException` allows mypy to correctly infer the `T` branch in the `elif` check that follows.
- **`SupportsResponse.OPTIONAL` - Service Response Data (v1.6.0-dev4)**: Services that optionally return data import `SupportsResponse` from `homeassistant.core` and pass `supports_response=SupportsResponse.OPTIONAL` to `hass.services.async_register`. The handler must return `dict[str, Any]` (not `None`). The `services.yaml` entry does **not** need a `response:` key - the HASSFest schema version used by this project does not support it, and the Python declaration is sufficient for runtime behavior.
- **`_resolve_entries()` Helper - Multi-Entry Service Handlers (v1.6.0-dev4)**: Domain services that accept an optional `config_entry_id` share the same resolution logic: if provided, find the matching entry and raise `HomeAssistantError(translation_key="entry_not_found")` if absent; if omitted, return all entries. Extract this into a `_resolve_entries(hass, target_entry_id)` helper in `__init__.py` to avoid duplication across all service handlers.

## 3a. Architecture Decisions (v1.7.0)

- **Payload normalization as the seam.** The three v1.6 bugs (band always null, signal treated as dBm, Pi interface type) shared one root: code read raw Supervisor keys that had changed. `parse.py` is now the only place that touches raw keys. Its cardinal rule: an unresolved field becomes `None`, and **every downstream filter treats `None` as pass, never drop** - treating "unknown band" as a failed match is exactly what hid every network. `_safe_int`/`_safe_float` coercion (dev_standards §6) lives here rather than in a separate helper.
- **Signal is canonically 0–100%.** The Supervisor sends a percentage; a negative value is converted via `dbm_to_pct` and the unit actually seen is recorded (`signal_unit`) so a future flip is a health finding, not silent corruption. The old `strongest_unknown_rssi` sensor was **removed, not renamed** - reusing the key with a new unit raises HA's statistics unit-change repair on every install, so a fresh `strongest_unknown_signal` key was used and the old entity left to be deleted by the user (its LTS survives).
- **Composite history key** (`parse.history_key`): named networks key on the SSID, cloaked ones on `hidden:<bssid>`. This preserves pre-existing history, keeps dual-band APs single, and makes the new-network event immune to a phone hotspot's rotating MAC (a named SSID never puts the MAC in the key). MAC randomization is a client-probe behavior and never appears in an AP scan, so it is not a flood source - the event rate limit exists only for ordinary hotspot churn.

  **Merging by SSID settles identity; it does not settle whose reading is published.** Several radios can share one label — a dual-band AP, or every node of a mesh — and until 2026-08-06 the surviving `signal`, `channel`, `band` and `bssid` were whichever the Supervisor listed last, so they flipped with nothing changing in the environment. The **strongest signal now wins**: this is a rogue detector, and the question it answers is how strong the strongest thing broadcasting that name is. A `None` signal never displaces a real reading, and a network whose radios all report `None` is still published.

- **Health snapshot lives outside `coordinator.data`** (dev_standards §19). `data` is `None` before first success and frozen at last-good values during an outage, so a verdict held there cannot describe the failure that stopped it updating. It is written on both the success and failure paths, and the sensor overrides `available` to `True` unconditionally so it can report the outage that takes every other entity down. Total-outage flags immediately at cold start, at the Nth strike at runtime, cleared same-cycle on success.
- **§3 identity-ladder exception.** Neither rung of the dev_standards §3 ladder is available: the Supervisor exposes no MAC for the scanning host and there is no IP (it monitors the HA machine itself). The device stays keyed on `(DOMAIN, entry.entry_id)` - deliberately unchanged, since churning it would orphan every existing user's entities. Recorded here so a future review does not re-raise it.
- **Diagnostics: structural, not key-name (dev_standards §20).** The payload is keyed by SSID, and neighbor SSIDs are third-party data `async_redact_data` cannot reach (it rewrites values, not keys). The sanitizer learns identifiers from the payload, allocates stable tokens, and rewrites SSIDs/BSSIDs everywhere including dict keys, while preserving signal/channel/band/counts. `"None Detected"` and `Hidden-<last4>` pass through as themselves.

## 3b. Decisions Recorded 2026-08-03

Settled positions that were previously implicit — held in the code but written down nowhere, so each was re-derived on every review pass. None of these is pending work.

- **`PARALLEL_UPDATES = 0` on all five platforms, deliberately** (dev_standards §22). `0` means unlimited, and §22 requires `1` on any platform that **commands a device**. No platform here does: `switch`, `number` and `button` write to `ConfigEntry.options`, not to hardware. There is also no race to serialize — `hass.config_entries.async_update_entry` is synchronous, so a setter has no await point between reading the options and writing them back, and two concurrent toggles cannot interleave into a lost update. `zte_router_5g` sets `1` because its router permits one session at a time and concurrent writes tear it down; that condition does not exist here. **Revisit if a platform ever writes to the Supervisor**, at which point §22's serialize/assure/confirm requirements apply in full.

- **`scan_now`, not `refresh`, for the Refresh Now control** (dev_standards §13 deviation). §13 names `translation_key="<prefix>_refresh"` and `unique_id` `f"{entry.unique_id}_refresh"`. This project shipped `scan_now` for both, and it stays: Home Assistant never renames an existing `entity_id`, so a correction would break every automation referencing `button.wifi_ssid_monitor_scan_now` while benefiting only new installs. All three §13 controls exist and behave correctly, including force-refresh bypassing pause; only the spelling differs. Recorded in `dev_standards.md` → Project Deviations.

  **Corrected 2026-08-03.** This bullet previously said `async_force_refresh` calling `async_refresh()` instead of §13's `async_request_refresh()` was deliberate, because "a button the user just pressed should fetch now rather than up to ten seconds later". That premise is false: HA builds the coordinator's debouncer with `immediate=True`, so `async_request_refresh()` **also** fetches on the first call — the 10-second cooldown only coalesces the calls behind it. The divergence was not a decision, it was an unexamined line with a rationalization attached afterwards, and it made the repeat case worse (ten presses, ten scans) while making the single-press case no better. Now aligned with §13, `zte_router_5g` and `unifi_network_monitor`. The coalescing it restores is what makes an action a script can call in a loop safe to route through the same path.

- **No `suggested_display_precision` or `suggested_unit_of_measurement`** (dev_standards §5). §5 asks that both be considered for every numeric sensor. Considered and declined: the four numeric sensors are a 0–100 integer percentage and three small counts, all of which render correctly with no hint. There is no native-versus-display split to bridge here — nothing is stored in a unit different from the one shown, which is the problem those fields exist to solve. **Revisit if a sensor is ever added whose storage unit reads badly** (a byte counter, a throughput figure).

- **Entity naming carries no doubled group word.** §12/§3.6 of the cross-project checks warn against repeating a sub-device name in an entity name, since HA prefixes the sub-device. Not applicable: there are no sub-devices (see §3a and `docs/all_sensors.md`), so HA prefixes only the device name and no entity name repeats it. Scanned 2026-08-03, no findings.

## 3d. Supervisor payload — observed on real hardware, 2026-08-21

**Recorded so nobody has to re-derive it.** Three diagnostics downloads, kept at `.notes/local_only/diag_dl/` with an index beside them. This continues the hardware findings already in this file — the frequency/percent-signal/`wireless` corrections of 2026-07-22 and the hidden-network confirmation of 2026-08-03 — rather than starting a second record elsewhere.

**These are not HA-core compatibility facts and do not belong in `docs/ha_compatibility.md`.** That document is for Home Assistant core API versions and deprecations; this is the shape of an upstream payload.

**The sample:**

| Box           | Arch    | HA       | Host OS / Supervisor  | Interface |
| :------------ | :------ | :------- | :-------------------- | :-------- |
| `bt3_x86`     | x86_64  | 2026.8.2 | HAOS 18.2 / 2026.08.0 | `wlan0`   |
| `ha_main_x86` | x86_64  | 2026.7.4 | HAOS 18.2             | `wlp2s0`  |
| `rpi4`        | aarch64 | 2026.8.2 | HAOS 18.2             | `wlan0`   |

**Confirmed, on both architectures:**

- **`signal` is a 0-100 percentage.** `signal_unit` reads `percent` on all three, and `signal == signal_raw` in every record. No capture has ever shown dBm.
- **`frequency` is present and in MHz**, aarch64 included — bands resolved to 2.4 GHz (ch 11) and 5 GHz (ch 48). This was the largest open assumption and it holds.
- **`mode` is `"infrastructure"`.** The mock said `"infra"` until 2026-08-21; the value reaches entity attributes and the `get_networks` response, so the container was showing a string the Supervisor never sends.
- **Interface names vary.** `wlp2s0` — predictable naming — is in the wild alongside `wlan0`.

**Still unconfirmed, and these downloads cannot settle it.** No cloaked network and no zero-width SSID appeared in any capture, so `Hidden-<last4>` and `ssid_anomaly` still rest on the single hand test of 2026-08-03. A capture taken with a hotspot cloaked nearby would close it.

**One live confirmation worth recording.** `rpi4` was running the `2.0.2-dev5` build and reports `severity: "ok"`; the two x86 boxes are on an older build and still report `severity: null`. That is the §19 severity enum working on real hardware, and a reminder those two boxes are behind.

**A hypothesis these captures raise but cannot test.** Real signal values cluster very high — every network in all three captures reads between 82 and 100. **There is not one weak or distant access point anywhere in the sample**, so nothing here says how well the proximity threshold discriminates; the captures hold only one end of the distribution. _If_ street-level networks also read high, `proximity_alert` at its default of 80 would approach being a duplicate of `new_network_alert`, which is simply "any unknown present". Testing that needs a capture from a location with genuinely distant networks in range. **It is not evidence that the default is wrong** — an unknown network at 82% inside the building is exactly what that sensor exists to flag, and the remedy there is the known list.

## 3e. Decisions Recorded 2026-08-21 — mock Supervisor

Four changes to `.devcontainer/mock_supervisor.py`, **decided and implemented the same day.** Prompted by three real diagnostics downloads (`.notes/local_only/diag_dl/`, from two x86_64 HAOS boxes and a Raspberry Pi 4), which showed the mock has drifted from what the Supervisor actually sends.

**(A) Correct the payload to match the real thing.** Two facts, each confirmed on all three systems:

- **`mode` is `"infrastructure"`, not `"infra"`.** The value is passed straight through to entity attributes and the `get_networks` response, so the devcontainer currently shows users a string the Supervisor never sends.
- **Interface names are not always `wlan0`.** One box reports `wlp2s0` (predictable naming). The mock offers only the easy name.

Also fix a pre-existing internal contradiction: `Neighbors_WiFi_5G` is defined with `frequency: 2412`, which is 2.4 GHz.

**(B) A second WiFi adapter — `wlp2s0`, with `"type": "wireless"`.** Three things follow from two lines:

- **The `"wireless"` branch becomes reachable.** `get_interfaces` matches `("wifi", "wireless")` because a Raspberry Pi reports `wireless`, and that mismatch was a shipped bug that made auto-detection return nothing for every Pi user (see the v1.7.0 entry). The mock has only ever sent `"wifi"`, so the devcontainer cannot exercise the branch that exists because of it.
- **Multi-entry behaviour becomes visible.** One entry per interface is this project's supported answer to multiple adapters (`ROADMAP.md` declines aggregation on that basis), and nothing in the devcontainer has ever shown two. Two entries exercise the `wifi_ssid_monitor_{interface}` duplicate guard, `_resolve_entries()` fanning actions across entries, two devices with two entity sets, and a config-flow dropdown with an actual choice in it.
- **Entry-scoped repair ids become observable.** `test_a_repair_id_is_scoped_to_the_entry` exists because a sibling entry could overwrite another's issue — a bug class that only manifests with two entries, and which no one has ever watched not happen.

Give the second adapter its own access-point payload, or the two entries look identical and prove less.

**(C) Variability, on exactly two networks, driven by minute-of-hour.** The payload is static today, so across a whole devcontainer session `new_24h` stays `0`, `visit_counts` never move, `last_seen` never changes, the signal never crosses the proximity threshold and the strike budget never runs.

- **`Neighbors_WiFi_5G`** — signal as a triangle wave between 55 and 95 across the hour, crossing the default threshold of 80 twice. Drives `proximity_alert`, `strongest_unknown_signal`, and gives the hysteresis roadmap item something real to be judged against.
- **`Unknown_WiFi_6G`** — present for minutes 0-29, absent for 30-59. Drives the `new_network` event, `visit_counts`, `new_24h`, `last_seen` movement and a changing `unknown_count`.

**Minute-of-hour rather than a request counter**, because it is stateless — the mock is a bare `HTTPServer` that loses everything on restart — and reproducible: ":05 looks like this" is a statement someone can check.

**Both `My_WiFi_*` entries, the hidden one and the zero-width one stay fixed.** A flapping known set would trip the canary and raise repairs continuously, and the hidden and anomaly labels must stay reproducible.

**`MOCK_STATIC=1` pins the payload, and is not optional.** `Sensor: Verify HA` audits live entity state in the devcontainer, and any bug reproduction wants a fixed payload. Without the escape hatch this trades one problem for a worse one.

**(D) Fault injection, through a `/mock/fault` control endpoint.** The integration builds its own fixed URL, so there is nowhere to put a query parameter — the switch has to be out of band. An endpoint setting module-level state also allows a fault to be **cleared** mid-session, which is the point: auto-recovery and repair deletion are the least eyeballed behaviour in the health system. An environment variable would need a container restart and could not show recovery at all.

| Fault | Mock does | Reaches |
| :-- | :-- | :-- |
| `unknown_interface` | 400 for an interface not in the list | `interface_missing` → health finding, `severity: error` |
| `down` | connection refused / 500 | strike budget → repair `conn_error`, `ConfigEntryNotReady` on cold start |
| `dbm` | signals as negative dBm | `signal_format_changed` → drift on health |
| `no_ap_key` | `200` with `data: {}` | `payload_no_ap_list` → drift → `warning` |
| `empty` | `200` with `accesspoints: []` | `empty_scan`, `no_known_networks` → `degraded` |
| `no_mac` / `no_freq` | drop the field from all or some APs | `payload_field_missing` / `_partial`, `band_unresolved_all` / `_some` |
| `html` | HTML body under a JSON content type | the `ContentTypeError` path |
| `slow` | sleep past `API_TIMEOUT_SECONDS` | the coordinator's `asyncio.timeout` |

That reaches **all eight health checks and all three repair issues**, none of which can currently be seen in the devcontainer UI at all.

**Splitting what is exercised from what is looked at.** Three things are asserted in pytest and need no human: every repair has readable `title` and `description` in `strings.json` **and** every compiled translation; no orphan `issues.*` entry survives a rename; and no check may declare a `repair=` that `all_issue_ids()` omits — that last one matters because `async_remove_entry` deletes exactly that list, so an unregistered repair would outlive the integration itself with no UI path to clear it. Repair create/delete, strike budgets and recovery were already covered.

**What is left is presentation, and it cannot be exercised** — does the card read like a sentence someone can act on, do the right entities hold their values, does the health sensor stay available when everything else has not. That is the `Mock: Fault Drill` task, driving `.devcontainer/fault_drill.sh`. It is attended, standalone, and clears the fault on exit including Ctrl-C: a drill that abandons the mock in a faulted state is worse than one nobody ran, because the next person debugs the fault instead of their own change.

**And a checklist nobody is prompted to run is a file nobody opens**, which is why the drill records its date in `.notes/fault_drill_last.txt` and `Mock: Fault Drill Staleness` sits inside `Validate All`. It compares that date against the last commit touching `health.py`, `coordinator.py`, `const.py`, `strings.json`, `translations/` and `mock_supervisor.py`, and warns — never fails — when the drill predates a change to any of them, or when one has uncommitted edits.

**It prints nothing when the drill is current, and that is the whole design.** A banner on every run is filtered out within a week; one that appears only when something has actually changed still carries information. Relevance-triggered rather than calendar-triggered for the same reason — a fixed cadence cries wolf when nothing has changed and stays silent when you edited `health.py` yesterday.

**One limitation worth knowing:** the check reads `git log`, so an edit only counts once committed. The uncommitted-changes branch covers the gap in the meantime, more loosely.

**Several will not fire on the first poll, and that is correct.** Drift checks wait out `HEALTH_STARTUP_GRACE_SCANS` and `HEALTH_DRIFT_STRIKE_LIMIT`, `signal_format_changed` needs a baseline from a previous scan, and `empty_scan` and the canary need accumulated visit counts. So the endpoint wants an optional auto-clear after N scans, and a short devcontainer scan interval — otherwise the tool is a waiting game. Route `/mock/` **before** the existing 404 fallback.

## 3c. Standards Sweeps — why 100% coverage was not enough

Added 2026-08-03. The suite was at 100% line coverage and 217 passing, and **four standards had no working guard**. Each was proved by breaking the thing deliberately and watching every test still pass:

| Broken deliberately | Result before | Guard added |
| :-- | :-- | :-- |
| Removed a sensor's `min_limit` / `max_limit` | 217/217 passed | `test_every_numeric_sensor_has_a_guard_band` |
| Deleted an entity from `icons.json` | 217/217 passed | `test_every_live_entity_has_an_icon_or_a_device_class` |
| Flipped four `is_drift=True` tags to `False` | 217/217 passed | `test_every_finding_is_classified_exactly_once` |
| (`test_async_remove_entry` asserted nothing) | could not fail | `test_async_remove_entry_deletes_every_live_store` |

**The shape matters more than the assertions.** Each of these sweeps a **set** — `CHECKS`, `SENSOR_TYPES`, the live entity list, the registered action list — rather than checking a known member. A test that asserts a mechanism works passes right up until the mechanism is bypassed; a test that asserts every member of a set is covered fails the moment the set grows. That is why adding a sensor without bounds, an entity without an icon, an action without an icon, or a health check without a classification now fails immediately.

**Two of the sweeps needed a vacuity floor.** `MIN_ENTITIES_SWEPT` was `2` against a real figure of 16, so the guard would have passed while 14 entities went uninspected. A sweep that inspects almost nothing passes for the same reason a correct one does; assert the count as well as the property.

**Guard bands are the exception to "sweep the live entities".** A guard band is never published as a state or an attribute — its only observable effect is a value that never appears — so nothing a running instance can be asked will reveal one. That check reads the descriptions statically. Decide which kind you need before writing the test.

**On the `_unrecorded_attributes` repetition.** Every class that declares its own set must repeat `"about"` from the mixin. Home Assistant does **not** merge this attribute across the class hierarchy — `Entity.__init_subclass__` unions the _component_ set with the class's _own_ attribute and never walks the MRO — so a subclass assignment shadows the mixin's set completely. `dev_standards` §14 claimed the opposite until 2026-08-03; the repetition looks redundant and is not. The sweep above catches an omission, which is the reason it does not have to be remembered.

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
- **Hidden Network Deduplication (resolved in v2.0.0 — kept as history).** Before v2.0.0 every AP without a broadcast SSID collapsed to a single `"[hidden]"` key, so three hidden APs counted as one and `network_map["[hidden]"]` held only the last one's values. **This is no longer the case.** `parse.hidden_label()` now names each cloaked network `Hidden-<last 4 of BSSID>`, and `resolve_hidden_collisions()` extends the suffix when two would collide, so they are counted and tracked individually. The shared `[hidden]` label survives only as the fallback for an AP that reports no BSSID at all.

  **Corrected 2026-08-03.** This entry previously described the old behavior in the present tense and pointed at the roadmap for a fix that had already shipped.

- **VS16 Compound Emoji in README Headings (2026-06-08)**: Using VS16 compound emoji (e.g., `⚙️`, `🏗️`, `⚠️`, `🗑️`) in README headings causes Table of Contents links to silently 404. GitHub's anchor generator strips VS16 bytes (U+FE0F) when computing heading slugs, but Markdown tooling includes them in `href` values. The mismatch is completely invisible in source editors - the heading renders fine and GitHub preview looks correct, but clicking a ToC link jumps nowhere.
  - _Fix_: Replace all VS16 compound emoji in headings and their corresponding ToC `href` values with always-color single-codepoint alternatives (e.g., 🔧 🔩 ❌ ❗ 🔄 💬). See root `CLAUDE.md` → "Shared Markdown Notes" for the full replacement table and detection script.

## 5. Environment Constraints

- **Native Async API**: The integration uses `aiohttp` for all network communication, aligning with the Home Assistant event loop.
- **Supervisor API**: This integration requires Home Assistant to be running in an environment with the Supervisor (HA OS or Supervised). It uses the internal `http://supervisor` endpoint and `SUPERVISOR_TOKEN`.
- **Testing Dependencies**: Robust testing relies on `pytest-homeassistant-custom-component` and `pytest-asyncio`.
- **Supervisor payload shape**: what the real Supervisor sends is recorded in §3d, from three live systems; the dev-container mock reproduces it and its docstring carries the same table. Check both before assuming a field's type or value.
- **Mock switches**: `MOCK_STATIC=1` pins the mock payload for reproducible runs; `GET /mock/fault?mode=<name>` injects a failure and `mode=off` clears it. See §3e.
- **Branding Assets**: Generic branding (WiFi signal + magnifying glass) was generated using Python's `Pillow` library to ensure a clean, modern aesthetic independent of hardware-specific imagery.

---

## Version Control

- **v1.0.1** (2026-04-01) - Created.
- **v1.0.2** (2026-05-06) - Updated with diagnostics and flow management patterns.
- **v1.0.3** (2026-05-13) - Added `entry.runtime_data` pattern, repair issues pattern, and `runtime_data` test pitfall (v1.4.4-dev2).
- **v1.0.4** (2026-06-02) - Added button platform, fnmatch matching, channel-to-band helper, in-memory last seen tracking, and domain service registration patterns (v1.5.0-dev1).
- **v1.0.5** (2026-06-03) - Added button error propagation, service lifecycle cleanup, and HomeAssistantError-in-handler patterns (v1.5.0-dev3).
- **v1.0.6** (2026-06-03) - Updated domain service registration pattern to `async_setup` approach; replaced stale service-lifecycle-cleanup pitfall; added exception-translations pattern (v1.5.0-dev4).
- **[2026-06-08]** - Added VS16 compound emoji in README headings pitfall entry.
- **v1.0.7** (2026-06-11) - Added persistent Store lifecycle pattern, `BaseException` narrowing, `SupportsResponse.OPTIONAL`, and `_resolve_entries()` helper patterns (v1.6.0-dev1/dev4).
- **v1.0.8** (2026-07-02) - Added explicit coordinator `config_entry=entry` pattern (honours the "Enable polling for changes" system option via `pref_disable_polling`; required as HA removes implicit context detection in 2026.8). Minimum HA raised to 2024.8.0 (v1.6.1-dev8).
- **[2026-07-22]** - **v1.7.0 overhaul.** Payload normalization layer (`parse.py`) fixing the three live-verified bugs (frequency→band, percent signal, `wireless` interface type); `strongest_unknown_signal` sensor replacing the removed dBm `rssi` sensor; BSSID-aware composite history keying + `Hidden-<last4>` naming + `ssid_anomaly`; Integration Health self-diagnosis (`health.py` catalog + snapshot outside `data` + always-available sensor + `interface_missing`/`signal_format_changed` repairs); band/hidden/pause/threshold/interval moved to control entities with a force-refresh flag; `get_networks` action, New Networks (24h) sensor, `new_network` bus event; coalesced store writes + flush-on-unload + shared key helpers; structural diagnostics sanitizer. Plan and decision log: `.notes/roadmap/version2_202607/3_wifi_updates_20260722.md`. Breaking changes documented in the README and CHANGELOG.
- **[2026-08-03]** - Added §3b (decisions previously held only in code: `PARALLEL_UPDATES`, `scan_now` naming, display scaling, entity naming) and §3c (the standards sweeps and what each rejects). Corrected two stale entries: the claim that this project has no Pause Polling switch, false since v2.0.0, now a table contrasting it with HA's system option; and the hidden-network deduplication pitfall, which described pre-v2.0.0 `[hidden]` collapse in the present tense and pointed at the roadmap for a fix that had already shipped. Coverage figure 99% → 100%. Hidden-network naming confirmed on hardware 2026-08-03.
- **[2026-08-21]** - Added §3d, the Supervisor payload as observed on three real systems, and §3e, four mock Supervisor changes, implemented the same day after those downloads showed it had drifted from the live payload (`mode`, interface naming). Records the second-adapter reasoning, minute-of-hour variability and out-of-band fault injection, plus the attended drill and the relevance-triggered staleness warning that makes it get run.
- **[2026-08-06]** - **Corrected one pattern that had become false, and refreshed two facts.** The button error-propagation entry (§3, added v1.5.0-dev3) told a reader to call `async_refresh()` and then check `last_update_success`. Both halves had drifted: the button routes through `async_force_refresh()` → `async_request_refresh()` since 2026-08-03, and that path is debounced — inside the 10-second cooldown `last_update_success` describes the _previous_ run, so a failed scan followed by a quick retry press reported failure again without having retried. The entry now carries the timestamp-comparison pattern and names all three outcomes of a press. **This is the second stale claim found in this file in four days**, and the first that would have propagated a live bug into a sibling project, since §3 exists to be copied. Coverage figure updated to 363 tests at 100% line _and_ branch, with a note that every fault fixed on 2026-08-06 was found by deepening tests against code already at 100% line coverage. Composite history key entry extended to state which radio's measurement survives when several share one SSID — arbitrary until 2026-08-06, now the strongest.
- **[2026-08-22]** - **Refreshed two facts §3 had outlived.** The test count read "363 tests as of 2026-08-06" and is now 415; the mutation sentence predated `coordinator.py` joining the scoped list and now carries the measured result — 1,307 mutants, 84.3% killed — plus a pointer to `.notes/test_pytest_issues/mutation_covered_not_covered.md`, which records why each module is on or off that list and what adding one costs. No pattern in §3 became false; these were stale numbers, which age quietly and are the reason this section is worth re-reading rather than appending to.


## Which conditions earn a Repair

Only one: `conn_error`, raised after the fetch strike budget is spent. The Repairs panel is for conditions that have stopped resolving themselves **and** that the user can act on; anything else is reported on the Integration Health sensor, where it can be automated on without asking for an action the panel cannot deliver.

`interface_missing` and `signal_format_changed` raised cards until 2026-08-26. They remain health findings — the first at `severity: error` in `degraded_capabilities`, the second as drift at `warning` — and their `Finding.repair` is simply `None`. Because repairs were derived from findings, retiring them removed the card and nothing else.

**`RETIRED_REPAIR_KEYS` is not dead code.** `ir.async_delete_issue` looks up by id, so a card still showing under a retired key has no code left that can clear it and no UI path out; every repair here is `is_fixable=False`. The keys are swept at setup and on removal, which is what makes retiring one safe.

**`_sync_repairs` was removed with them.** No finding carries a repair any more, so its raise loop could never execute — `conn_error` is raised and cleared on the fetch path, in one place, as on the sibling projects.
