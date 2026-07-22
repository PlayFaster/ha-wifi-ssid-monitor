# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

## What This Integration Does

A Home Assistant custom component (HACS integration) that polls the Home Assistant Supervisor Network API (`/network/interface/{interface}/accesspoints`) on a configurable schedule to scan for WiFi SSIDs. It compares detected networks against a user-defined allow-list and surfaces the results as HA entities for use in automations (e.g., rogue AP detection, smart device pairing detection, home network uptime monitoring).

Requires a Home Assistant Supervised or HAOS installation with WiFi hardware — the Supervisor API is not available on plain container/core installs.

## Commands

### Tests

```bash
# Run all tests
pytest

# Run a single test file
pytest tests/test_coordinator.py

# Run a single test by name
pytest tests/test_coordinator.py::test_coordinator_resilience_holds_for_three_failures

# Run with coverage
pytest --cov=custom_components --cov-report=term-missing
```

### Linting & Formatting

```bash
# Lint
ruff check .

# Lint and auto-fix
ruff check --fix .

# Format
ruff format .

# Type check
mypy custom_components/wifi_ssid_monitor

# Spell check
codespell
```

### Running tools from a Windows host

These commands only work **inside** the devcontainer — HA imports `fcntl`, so `pytest` (and the other tools) cannot run on a Windows host directly. From Windows, run everything through `docker exec` against the running container. See [`.shared/prompts/devcon_run_gen.md`](.shared/prompts/devcon_run_gen.md) for the full mini-skill. Quick reference:

```bash
# Confirm the container is up first
docker ps --filter "name=<CONTAINER_NAME>" --format "{{.Names}}"

# Run a tool inside the container (-w sets the in-container working dir)
docker exec -w /workspaces/<PROJECT_DIR> <CONTAINER_NAME> bash -c "PYTHONPATH=. pytest tests/"
docker exec -w /workspaces/<PROJECT_DIR> <CONTAINER_NAME> bash -c "ruff check ."
```

Do not install or run these tools on the host as a workaround.

## Architecture

The integration follows the standard HA `DataUpdateCoordinator` pattern:

```text
__init__.py         Entry point: sets up coordinator, calls async_initialize(), forwards to
                    platforms, registers reload listener; async_setup registers 5 domain
                    services (add_known_ssid, remove_known_ssid, scan_now, clear_last_seen,
                    set_known_ssids); async_remove_entry cleans up all 3 Stores
api.py              WifiScanAPI — async aiohttp wrapper for two Supervisor endpoints:
                      GET /network/interface/{iface}/accesspoints  → SSID scan
                      GET /network/info                            → interface discovery
coordinator.py      WifiScanCoordinator — polls API, computes known/unknown SSID sets,
                    implements 3-strike resilience (holds stale data for ≤3 failures,
                    raises UpdateFailed + HA Repair issue on 4th); applies band filter and
                    denylist; tracks last_seen / first_seen / visit_counts via 3 Stores;
                    computes strongest_unknown_rssi and strongest_unknown_ssid
sensor.py           6 sensor entities (total count, unknown count, interface, last updated,
                    strongest_unknown_ssid, strongest_unknown_rssi) defined via
                    WifiSensorEntityDescription dataclass with value_fn lambdas
binary_sensor.py    2 binary sensors:
                      new_network_alert — True when unknown_count > 0
                      proximity_alert   — True when strongest_unknown_rssi ≥ threshold
button.py           1 button entity (scan_now) — async_press() calls coordinator.async_refresh()
number.py           1 number entity (scan_interval, 1–180 min) — debounced 2 s before
                    persisting to entry options, which triggers async_reload_entry
config_flow.py      Initial setup + options flow + reconfigure + reauth flows
services.yaml       HA service descriptions for all 5 domain services
diagnostics.py      HA diagnostics support; redacts known_wifi_ids
const.py            Constants; reads VERSION from manifest.json at import time
```

**Data flow:** `coordinator.data` is a dict with keys: `count`, `ssids`, `unknown_ssids`, `unknown_count`, `interface`, `networks` (map of ssid → `{rssi, channel, band}`), `last_seen` (map of ssid → datetime), `first_seen` (map of ssid → datetime), `visit_counts` (map of ssid → int), `strongest_unknown_rssi` (int | None), `strongest_unknown_ssid` (str | None). All entity platforms read exclusively from this dict via `entry.runtime_data` (the coordinator).

**Config storage:** All user settings are stored in `entry.options` (not `entry.data`). On startup, `__init__.py` migrates any old `entry.data` entries to `entry.options`. The unique ID is `wifi_ssid_monitor_{interface}`, preventing duplicate entries for the same interface. Options include: `name`, `wifi_interface`, `known_wifi_ids`, `scan_interval`, `include_hidden` (bool, default `True`), `proximity_rssi_threshold` (int dBm, default `−60`), `scan_bands` (str `"all"`/`"2.4"`/`"5"`, default `"all"`), `denylist_ssids` (str, comma-separated fnmatch patterns, default `""`), `last_seen_ttl_days` (int 0–366, default `90`, 0 = keep forever).

**Scan interval handling:** The number entity stores minutes in the UI; the coordinator and options store seconds. Changing the interval via the number entity debounces for 2 s, then writes seconds to `entry.options`, which fires the update listener in `__init__.py`. Only a known-SSID change triggers an immediate re-scan; an interval-only change does not.

**Known SSID matching:** Uses `fnmatch.fnmatch(ssid, pattern)` — exact matches and wildcard patterns (e.g., `Guest_*`) are both supported. Case-sensitive (SSIDs are case-sensitive).

**Hidden networks:** When `include_hidden=True` (default), APs without an `ssid` key are grouped as a single `[hidden]` entry. When `include_hidden=False`, they are filtered out before processing and do not appear in any count or attribute.

**Services** — all registered in `async_setup` (domain lifecycle), persisting for the domain's loaded state. Described in `services.yaml`:

- **`add_known_ssid`**: Appends an SSID to `CONF_KNOWN_SSIDS` for one or all entries; triggers a re-scan.
- **`remove_known_ssid`**: Removes an SSID or pattern from `CONF_KNOWN_SSIDS`; silent success if not found; triggers a re-scan when the list changes.
- **`scan_now`**: Triggers `coordinator.async_refresh()` for one or all entries immediately.
- **`clear_last_seen`**: Silently clears all three persistent Stores (`last_seen`, `first_seen`, `visit_counts`); no re-scan.
- **`set_known_ssids`**: Replaces the entire known list in one call; returns previous list per entry as `SupportsResponse.OPTIONAL` response data; triggers a re-scan.

All multi-entry services accept an optional `config_entry_id` field. Resolution is handled by `_resolve_entries(hass, target_entry_id)` in `__init__.py`.

## Key Patterns & Conventions

- `PARALLEL_UPDATES = 0` is set on all platforms (coordinator-driven, no per-entity polling).
- All entities use `_attr_has_entity_name = True` and `translation_key` for localization; display strings live in `strings.json` and `translations/`.
- `type: ignore` comments are used in several places to suppress mypy errors on HA base classes that lack complete stubs — this is expected.
- The `.comp/` directory contains unrelated scratch/reference files; ignore it.
- `quality_scale.yaml` tracks compliance with HA Integration Quality Scale (currently Platinum level).

### Exception Tuple Syntax — Settled Decision

Always use `except (A, B):` with explicit parentheses for multi-exception catches. Never use the bare-tuple form `except A, B:`.

- **Do not flag or change this** — it has been researched and decided.
- `except A, B:` silently catches only `A` on Python 3.12–3.13 (what HA runs on in production), making it a correctness issue, not just style.
- `except (A, B):` is correct and unambiguous across Python 2.6 through 3.14+.
- Full background: `shared/SharedNotes/info/py_exception_tuple_syntax/issue_summary.md`

## Development Environment

The project uses a VS Code devcontainer (`.devcontainer/`, image `ha-dev-base:latest`) running a real Home Assistant instance plus a mock Supervisor sidecar that simulates the WiFi scan API (see `.devcontainer/mock_supervisor.py`). The `SUPERVISOR_TOKEN` env var is set to `mock_dev_token` in the compose file.

### MCP Access (ha-mcp-dev)

When the devcontainer is running, the `ha-mcp-dev` MCP server automatically connects to the HA instance inside it (`http://localhost:8123`). Use it to verify integration changes without leaving the editor.

**After any modification, follow the post-modification process** — see [`.shared/prompts/post_mod_process.md`](.shared/prompts/post_mod_process.md). Specify a `SCOPE` when invoking it:

| SCOPE      | What runs                                                 |
| :--------- | :-------------------------------------------------------- |
| `None`     | Changes only — no validation                              |
| `Basic`    | HA restart + error check + lint/format fixes              |
| `Full`     | Basic + mypy (standard) + pytest (fix failing tests only) |
| `Complete` | Full + pre-commit --all-files + mypy --strict             |

Additional tools useful during development:

- `ha_get_state` / `ha_search_entities` — verify entity states and attributes after a reload
- `ha_call_service` — trigger service calls (e.g. `homeassistant.update_entity`) to exercise platform callbacks directly

HA core source is mounted read-only at `/ha_core`; mypy resolves HA types against it. Tests use `pytest-homeassistant-custom-component` and must be run inside the devcontainer where the HA test helpers are available.

Validation reports are written to the `.reports/` directory (gitignored outputs from lint/test runs).

### Skill Prompts

Three reusable prompts are available via `.shared/prompts/` for working within this devcontainer:

| Prompt | Purpose |
| :-- | :-- |
| `devcon_run_gen.md` | Run any single command inside the container |
| `devcon_run_and_fix.md` | Full test + lint cycle: pytest, ruff, prettier, validate — with auto-fix |
| `devcon_coverage.md` | Coverage report, target file selection, and new test writing |

Container identity values (`CONTAINER_NAME`, `PROJECT_DIR`) are in `.devcontainer/.env`.

---

## Version Control

- **v1.0.1** (2026-05-13) - Current version at time of first recording.
- **v1.0.2** (2026-06-02) - Updated architecture block, coordinator data keys, config options, service, and hidden/known-SSID matching docs (v1.5.0-dev1).
- **v1.0.3** (2026-06-03) - Updated `__init__.py` architecture line and service description to reflect `async_setup` registration pattern (v1.5.0-dev4).
- **v1.0.4** (2026-06-11) - Updated architecture block (6 sensors, 3 Stores, 5 services), data flow keys (first_seen, visit_counts, strongest_unknown_ssid), config options (scan_bands, denylist_ssids, last_seen_ttl_days), and services section (v1.6.0-dev1/dev4).

## Emoji in Headings — Single Codepoint Only

**Two-codepoint ("complex") emoji are banned from Markdown headings.** An emoji such as `⚙️` is a glyph plus an invisible `U+FE0F` variation selector; `📘` is a single codepoint.

Heading anchors are generated by stripping the emoji, and our two validators strip **different amounts** — GitHub / `markdown-link-check` remove both codepoints, while `markdownlint` **MD051** keeps the `U+FE0F` (it is Unicode category *Mark*). No link fragment satisfies both, so a linked heading is **unfixable in the link** — only changing the emoji resolves it. The ban is absolute (not just linked headings), because adding a link later is a normal edit that would silently break.

- Safe: `📅 📦 💻 🧩 📶 📈 🔐 📘 🧰 📖 🚀 🔍 🧹`
- Banned: `⏱️ ⚙️ ✂️ 🎛️ 🖥️ 🛡️ ♻️ ▶️ ⚖️ 🗂️ 🛠️ ✔️ ❤️`

Detect mechanically — `U+FE0F` is invisible in every editor, so never review for it by eye:

```bash
grep -n "^#" README.md | cat -A | grep "M-oM-8M-^O"
```

Body text, tables and link labels are unaffected — the ban applies to headings only.

Full background: `.shared/` → `SharedNotes/info/markdown_anchor_emoji/anchor_emoji_conflict.md`
