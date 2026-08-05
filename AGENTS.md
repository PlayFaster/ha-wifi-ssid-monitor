# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

> [!CAUTION]
> **Never run `git checkout`, `git restore`, `git reset`, `git stash` or `git clean`. Ask first, every time — no exceptions, whoever's changes you think they are.** Reading git (`status`, `diff`, `log`, `show`) is always fine. Full rule and the incident behind it: [`agent_conventions.md`](.shared/dev_std/agent_conventions.md).


> **Read the shared conventions first:** [`.shared/dev_std/agent_conventions.md`](.shared/dev_std/agent_conventions.md) — commands (tests, lint, mypy, validation), the Windows-host `docker exec` workflow, devcontainer access, HAB/MCP for interrogating the running HA instance, the post-modification SCOPE table, code conventions, and the markdown/Python rules. That file is the single source of truth for everything shared across the integration projects; this file covers only what is specific to **ha-wifi-ssid-monitor**.

## What This Integration Does

A Home Assistant custom component (HACS integration) that polls the Home Assistant Supervisor Network API (`/network/interface/{interface}/accesspoints`) on a configurable schedule to scan for WiFi SSIDs. It compares detected networks against a user-defined allow-list and surfaces the results as HA entities for use in automations (e.g., rogue AP detection, smart device pairing detection, home network uptime monitoring).

Requires a Home Assistant Supervised or HAOS installation with WiFi hardware — the Supervisor API is not available on plain container/core installs.

## Commands

Standard for all integration projects — see [shared conventions §2](.shared/dev_std/agent_conventions.md). Nothing about this project's commands differs.

## Architecture

The integration follows the standard HA `DataUpdateCoordinator` pattern, on a **single** device.

> **Entity and service inventory lives in [`docs/all_sensors.md`](docs/all_sensors.md)** — it is authoritative and kept current against live HA by `sensor_review.md`. This block describes the code layout only; it deliberately carries no entity counts or service descriptions.

```text
__init__.py         Entry point: sets up coordinator, calls async_initialize(), forwards to
                    platforms, registers reload listener; async_setup delegates to
                    services.async_register_services(); async_remove_entry cleans up all 3 Stores
api.py              WifiScanAPI — async aiohttp wrapper for two Supervisor endpoints:
                      GET /network/interface/{iface}/accesspoints  → SSID scan
                      GET /network/info                            → interface discovery
parse.py            Single parsing boundary: normalizes raw payloads to 0–100% signal, MHz →
                    channel/band, Hidden-<last4> labels for cloaked SSIDs, zero-width
                    ssid_anomaly flags
coordinator.py      WifiScanCoordinator — polls API, computes known/unknown SSID sets,
                    implements 3-strike resilience (holds stale data for ≤3 failures,
                    raises UpdateFailed + HA Repair issue on 4th); applies band switches and
                    denylist; tracks last_seen / first_seen / visit_counts via 3 Stores;
                    computes strongest_unknown_signal / strongest_unknown_ssid / new_24h
health.py           Integration Health fact-gathering and severity computation
entity.py           build_device_info() (single device, keyed on entry_id) + the WifiAboutEntity
                    mixin (unrecorded `about` attribute). Every platform delegates here
sensor.py           Sensor platform — WifiSensorEntityDescription dataclass with value_fn lambdas
binary_sensor.py    Binary sensor platform. Note the semantics:
                      new_network_alert   — ON when unknown_ssid_count > 0
                      proximity_alert     — ON when strongest_unknown_signal ≥ threshold (percent,
                                            not dBm)
                      integration_health  — PROBLEM class; available unconditionally
button.py           Button platform
number.py           Number platform — interval changes debounce 2 s before persisting to options
switch.py           Switch platform — polling pause, hidden-network and per-band visibility
services.py         Registers the domain services + _resolve_entries()
config_flow.py      user + reauth / reauth_confirm + reconfigure + options (async_step_init)
services.yaml       Service descriptions
diagnostics.py      HA diagnostics. Structural sanitizer, not key-name redaction: the payload is
                    keyed by SSID and neighbouring SSIDs are third-party data, so it learns every
                    SSID/BSSID from the payload, allocates a stable token per identity and
                    rewrites them everywhere including dict keys. Signal/channel/band/counts are
                    preserved deliberately — a gutted file is as useless as a leaky one
const.py            Constants; reads VERSION from manifest.json at import time
```

**Single device, not sub-devices.** `entity.py:build_device_info` returns one `DeviceInfo` identified by `(DOMAIN, entry.entry_id)`. The Supervisor exposes no MAC and there is no IP — the integration monitors the HA machine itself — so neither rung of the dev_standards §3 identity ladder is available; the entry id is the only thing to key on. `docs/all_sensors.md` described a **System** / **Monitor** sub-device split until 2026-08-03; that architecture was never built and the document has been corrected. If you see it referenced anywhere, it is stale.

**Data flow:** `coordinator.data` is a dict with keys: `count`, `ssids`, `unknown_ssids`, `unknown_count`, `interface`, `networks` (map of key → `{bssid, signal, signal_raw, channel, band, hidden, ssid_anomaly, mode, key}`), `last_seen` / `first_seen` (map of key → datetime), `visit_counts` (map of key → int), `new_24h` (int), `strongest_unknown_signal` (int | None, percent), `strongest_unknown_ssid` (str | None — sentinel `"None Detected"` when none visible), `signal_unit`. All entity platforms read exclusively from this dict via `entry.runtime_data` (the coordinator).

**Config storage:** All user settings are stored in `entry.options` (not `entry.data`). On startup, `__init__.py` migrates any old `entry.data` entries to `entry.options`. The unique ID is `wifi_ssid_monitor_{interface}`, preventing duplicate entries for the same interface. Options: `name`, `wifi_interface`, `known_wifi_ids`, `scan_interval` (seconds, default `600`), `include_hidden` (bool, default `True`), `proximity_signal_threshold` (int percent, default `80`), `show_24ghz` / `show_5ghz` / `show_6ghz` (bool, each default `True`), `denylist_ssids` (str, comma-separated fnmatch patterns, default `""`), `last_seen_ttl_days` (int 0–366, default `90`, 0 = keep forever), `stop_polling` (bool, default `False`).

**Legacy option aliases** — `const.py` keeps `CONF_PROXIMITY_RSSI_THRESHOLD` (superseded by the percentage `proximity_signal_threshold`) and `CONF_SCAN_BANDS` (the old `"all"`/`"2.4"`/`"5"` string, superseded by the three per-band switches) pointing at their legacy keys. Don't reintroduce them as live settings; they exist for migration.

**Scan interval handling:** The number entity stores minutes in the UI; the coordinator and options store seconds. Changing the interval via the number entity debounces for 2 s, then writes seconds to `entry.options`, which fires the update listener in `__init__.py`. An immediate re-scan is triggered by any change to the known list, the denylist, `include_hidden`, the proximity threshold, or the three band switches (`REFRESH_ON_CHANGE_KEYS` in `__init__.py`). An interval-only change or a pause toggle does not force a fetch.

**Pattern matching:** Known-SSID and denylist patterns are matched with `fnmatch` against **both** the network key (SSID or hidden label) **and** the hardware BSSID — so a MAC pattern is a valid list entry. Exact matches and wildcards (e.g. `Guest_*`) are both supported. Case-sensitive (SSIDs are case-sensitive).

**Hidden networks:** When `include_hidden=True` (default), a cloaked AP gets a **per-BSSID** label — `Hidden-<last4 hex of BSSID>` (extended to six hex digits when two labels collide, see `parse.py`) — rather than one shared bucket, so two cloaked networks stay distinguishable. `HIDDEN_FALLBACK_LABEL` (`"[hidden]"`) remains only as the fallback when no BSSID is available. When `include_hidden=False` they are filtered out before processing and appear in no count or attribute.

**Service registration pattern** — services are registered by `services.async_register_services(hass)` called from `async_setup` (domain lifecycle, **not** `async_setup_entry`), so they exist once for the domain regardless of entry count. The list-mutating actions take a `target: known|denylist` selector rather than having separate per-list services, and the two response actions use `SupportsResponse.OPTIONAL` (`set_ssids`, returning the previous list) and `SupportsResponse.ONLY` (`get_networks`). All multi-entry services accept an optional `config_entry_id`, resolved by `_resolve_entries(hass, target_entry_id)` in `services.py`.

For the service names, parameters, and descriptions see [`docs/all_sensors.md`](docs/all_sensors.md) and `services.yaml`.

## Key Patterns & Conventions

Shared conventions (ruff/mypy strictness, `PARALLEL_UPDATES`, `translation_key`, icons, exception tuple syntax, markdown emoji rules) are in [shared conventions §4–5](.shared/dev_std/agent_conventions.md). Project-specific additions:

- `type: ignore` comments are used in several places to suppress mypy errors on HA base classes that lack complete stubs — this is expected.
- The `.comp/` directory contains unrelated scratch/reference files; ignore it.
- `quality_scale.yaml` tracks compliance with HA Integration Quality Scale (currently Platinum level).

### Tests that will stop you, and why they exist

Several standards here are enforced by sweeps over a **set**, not by spot checks, so they fail when the set grows rather than only when a known member breaks. Each was verified by deliberately breaking the thing it guards. If one of these fails, it has found something — do not reach for the allow-list first.

| Add or change this | This fails | Do this |
| :-- | :-- | :-- |
| A sensor with a unit or `state_class` | `test_every_numeric_sensor_has_a_guard_band` | Declare `min_limit` / `max_limit`, or add the key to `UNGUARDED_ALLOWLIST` **with a reason**. Also update `docs/value_min_max.md` — §6 requires it to match the code both ways. |
| Any entity | `test_every_live_entity_has_an_icon_or_a_device_class` | Add an `icons.json` entry **under that entity's own platform**, unless it has a `device_class`. |
| Any action | `test_every_registered_action_has_an_icon` | Add a `services` entry in the nested `{"service": "mdi:..."}` form. The flat string form is legacy and the test rejects it. |
| An entity attribute | `test_no_entity_publishes_a_recorded_attribute` | Add the key to that class's `_unrecorded_attributes`. **Repeat `"about"` if the class declares its own set** — HA does not merge this attribute across the class hierarchy, so a subclass assignment shadows the mixin's entirely. |
| A health check in `CHECKS` | `test_every_check_has_a_firing_fixture`, `test_every_finding_is_classified_exactly_once` | Add a fixture that makes it fire, and classify it in `_EXPECTED_DRIFT` or `_EXPECTED_CAPABILITY`. `is_drift` defaults to `False`, so a new check is a capability unless it opts in. |
| A fourth `Store` | `test_async_remove_entry_deletes_every_live_store` | Add the key to `all_storage_keys()` in `const.py`, which both the coordinator and `async_remove_entry` build from. |
| A condition only ever exercised one way | `Pytest: Check Test Coverage` reports a partial branch (`123->126` in the `Missing` column) | **Write the test.** All twelve found here were missing tests; none was dead code. Delete the guard only where the type system or the immediate caller already prevents the case — never in code consuming held or stored state, where the "impossible" shape arrives exactly when something upstream has already failed. |
| A test that runs code without checking it | `Tests: Assertion Audit` | Assert the **observable outcome**. Where "this must not raise" is the real contract, assert what that implies — nothing cancelled, no task created, exactly one event on the bus — so the test fails on a behaviour change and not only on a crash. Adding a trivial assertion to clear the count is a defect, not a fix. Last resort: `tests/zero_assertion_allowlist.txt`, with a reason. |

- **Mutation testing is scoped by `.validate/mutmut_modules.txt`** — currently `parse.py`, `diagnostics.py`, `health.py`. Those three were chosen because their tests exercise real code; `config_flow.py` and `__init__.py` were tried and rejected because their tests mock the thing being mutated, so every mutation of a call into that mock survives and none of them is a findable defect. Run it with the **Tests: Mutation Check** task, or on one function via `devcon_coverage` STEP 3c. Not part of `Validate All` — survivors need judging, not counting. Background: [`.shared/info/test_better_docs/mutation_testing_setup.md`](.shared/info/test_better_docs/mutation_testing_setup.md).

- **`SLF001` and `RET504` are exempted for `tests/**`only.** This comes from the **synced**`pyproject.toml`— do not edit that file, see [shared conventions → Synced Files](.shared/dev_std/agent_conventions.md). Tests must reach private state (asserting on`\_unrecorded_attributes`, driving `coordinator.\_async_update_data()`), so forbidding it would forbid the tests the standards require. Production code is not exempt: a genuine need there gets a `# ruff: noqa` at the site.

## Development Environment

Shared devcontainer, MCP, and post-modification details are in [shared conventions §3](.shared/dev_std/agent_conventions.md). Specific to this project:

- The devcontainer runs a **mock Supervisor sidecar** that simulates the WiFi scan API — see `.devcontainer/mock_supervisor.py`. The `SUPERVISOR_TOKEN` env var is set to `mock_dev_token` in the compose file.

`AGENTS.md` revision history: `.notes/agents_md_version_log.md`.
