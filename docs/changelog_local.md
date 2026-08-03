# Internal Detailed Changelog: WiFi SSID Monitor

All changes to this project will be documented in this file. This is the detailed changelog, to include non user facing changes and intra-release changes.

---

- [Internal Detailed Changelog: WiFi SSID Monitor](#internal-detailed-changelog-wifi-ssid-monitor)
  - [\[2.0.1-dev13\] - 2026-08-03 - Standards Test Coverage: §6, §12, §19 and §21 Guards; Action Icons](#201-dev13---2026-08-03---standards-test-coverage-6-12-19-and-21-guards-action-icons)
  - [\[2.0.1-dev12\] - 2026-08-03 - Validation Pass; ROADMAP Conversion; dev\_std\_review and IQS SCAN=Full](#201-dev12---2026-08-03---validation-pass-roadmap-conversion-dev_std_review-and-iqs-scanfull)
  - [\[2.0.1-dev11\] - 2026-08-03 - Hardware-Check Task; Changelog ToC Added, Bumps](#201-dev11---2026-08-03---hardware-check-task-changelog-toc-added-bumps)
  - [\[2.0.1-dev10\] - 2026-07-28 - Automation Example Glitch Guards \& has\_value Checks in README](#201-dev10---2026-07-28---automation-example-glitch-guards--has_value-checks-in-readme)
  - [\[2.0.1-dev9\] - 2026-07-27 - Standards Test Coverage Recorded](#201-dev9---2026-07-27---standards-test-coverage-recorded)
  - [\[2.0.1-dev8\] - 2026-07-27 - §14 Enforcement Test](#201-dev8---2026-07-27---14-enforcement-test)
  - [\[2.0.1-dev7\] - 2026-07-27 - §19 `drift` Attribute](#201-dev7---2026-07-27---19-drift-attribute)
  - [\[2.0.1-dev6\] - 2026-07-27 - Cross-Project Alignment](#201-dev6---2026-07-27---cross-project-alignment)
  - [\[2.0.1-dev5\] - 2026-07-26 - README Section Names and Links](#201-dev5---2026-07-26---readme-section-names-and-links)
  - [\[2.0.1-dev4\] - 2026-07-26 - Ruff Bump 0.15.21 → 0.15.22](#201-dev4---2026-07-26---ruff-bump-01521--01522)
  - [\[2.0.1-dev3\] - 2026-07-26 - Shared CI Bump v2.0.5 → v2.0.6](#201-dev3---2026-07-26---shared-ci-bump-v205--v206)
  - [\[2.0.1-dev2\] - 2026-07-26 - README Tweaks; AGENTS.md Restructured](#201-dev2---2026-07-26---readme-tweaks-agentsmd-restructured)
  - [\[2.0.1-dev1\] - 2026-07-26 - PHACC Bump 0.13.347 → 0.13.348](#201-dev1---2026-07-26---phacc-bump-013347--013348)
  - [\[2.0.0\] - 2026-07-25 - Signal as a Percentage; Health Sensor; Breaking Renames](#200---2026-07-25---signal-as-a-percentage-health-sensor-breaking-renames)
  - [\[2.0.0-dev9\] - 2026-07-25 - Docs and Formats](#200-dev9---2026-07-25---docs-and-formats)
  - [\[2.0.0-dev8\] - 2026-07-24 - Readme Automations and Edits](#200-dev8---2026-07-24---readme-automations-and-edits)
  - [\[2.0.0-dev7\] - 2026-07-24 - Readme Screenshots and Automations](#200-dev7---2026-07-24---readme-screenshots-and-automations)
  - [\[2.0.0-dev6\] - 2026-07-24 - Signal to dBm Comparisons](#200-dev6---2026-07-24---signal-to-dbm-comparisons)
  - [\[2.0.0-dev5\] - 2026-07-23 - Icons and Branding Refreshed](#200-dev5---2026-07-23---icons-and-branding-refreshed)
  - [\[2.0.0-dev4\] - 2026-07-23 - Exception Translation; UniFi-Aligned README Overhaul](#200-dev4---2026-07-23---exception-translation-unifi-aligned-readme-overhaul)
  - [\[2.0.0-dev3\] - 2026-07-22 - 100% Test Coverage; Document Reconciliation](#200-dev3---2026-07-22---100-test-coverage-document-reconciliation)
  - [\[2.0.0-dev2\] - 2026-07-22 - BSSID Pattern Matching; Operating Mode Exposed](#200-dev2---2026-07-22---bssid-pattern-matching-operating-mode-exposed)
  - [\[2.0.0-dev1\] - 2026-07-22 - Signal Rescaled to Percent; Health Sensor; Services Renamed](#200-dev1---2026-07-22---signal-rescaled-to-percent-health-sensor-services-renamed)
  - [\[1.6.2-dev8\] - 2026-07-22 - Bumped Ruff and PHACC](#162-dev8---2026-07-22---bumped-ruff-and-phacc)
  - [\[1.6.2-dev7\] - 2026-07-12 - Docs Formats and Spelling](#162-dev7---2026-07-12---docs-formats-and-spelling)
  - [\[1.6.2-dev6\] - 2026-07-12 - Bumped pytest-homeassistant-custom-component from 0.13.345 to 0.13.346](#162-dev6---2026-07-12---bumped-pytest-homeassistant-custom-component-from-013345-to-013346)
  - [\[1.6.2-dev5\] - 2026-07-06 - Shared CI Bump v2.0.5 → v2.0.6](#162-dev5---2026-07-06---shared-ci-bump-v205--v206)
  - [\[1.6.2-dev4\] - 2026-07-05 - PyTest Coverage to 100%](#162-dev4---2026-07-05---pytest-coverage-to-100)
  - [\[1.6.2-dev3\] - 2026-07-05 - mypy Unreachable-Statement Fix](#162-dev3---2026-07-05---mypy-unreachable-statement-fix)
  - [\[1.6.2-dev2\] - 2026-07-05 - `test-before-setup` via `ConfigEntryNotReady`](#162-dev2---2026-07-05---test-before-setup-via-configentrynotready)
  - [\[1.6.2-dev1\] - 2026-07-05 - Ruff Checks Extended to Match Home Assistant](#162-dev1---2026-07-05---ruff-checks-extended-to-match-home-assistant)
  - [\[1.6.1\] - 2026-07-04 - Release - Reconfigure Shows All Settings; Polling Toggle](#161---2026-07-04---release---reconfigure-shows-all-settings-polling-toggle)
  - [\[1.6.1-dev11\] - 2026-07-04 - Reconfigure Screen Shows the Full Settings Set](#161-dev11---2026-07-04---reconfigure-screen-shows-the-full-settings-set)
  - [\[1.6.1-dev10\] - 2026-07-04 - Check-Drift Script Fixed; README Aligned](#161-dev10---2026-07-04---check-drift-script-fixed-readme-aligned)
  - [\[1.6.1-dev9\] - 2026-07-03 - Ruff Bump 0.15.19 → 0.15.20](#161-dev9---2026-07-03---ruff-bump-01519--01520)
  - [\[1.6.1-dev8\] - 2026-07-02 - Explicit `config_entry` on the Coordinator](#161-dev8---2026-07-02---explicit-config_entry-on-the-coordinator)
  - [\[1.6.1-dev7\] - 2026-06-27 - README Screenshots; YAML Lint Aligned](#161-dev7---2026-06-27---readme-screenshots-yaml-lint-aligned)
  - [\[1.6.1-dev6\] - 2026-06-26 - Shared CI, Ruff and PHACC Bumps](#161-dev6---2026-06-26---shared-ci-ruff-and-phacc-bumps)
  - [\[1.6.1-dev5\] - 2026-06-18 - CI Validation Overhaul](#161-dev5---2026-06-18---ci-validation-overhaul)
  - [\[1.6.0\] - 2026-06-12 - Proximity Alert, Persistent History and Denylist](#160---2026-06-12---proximity-alert-persistent-history-and-denylist)
  - [\[1.6.0-dev7\] - 2026-06-11 - Documentation Refresh](#160-dev7---2026-06-11---documentation-refresh)
  - [\[1.6.0-dev6\] - 2026-06-11 - `__init__.py` Coverage to 100%](#160-dev6---2026-06-11---__init__py-coverage-to-100)
  - [\[1.6.0-dev4\] - 2026-06-11 - First Seen and Visit Count Stores; Three Services Added](#160-dev4---2026-06-11---first-seen-and-visit-count-stores-three-services-added)
  - [\[1.6.0-dev1\] - 2026-06-11 - Persistent Last Seen; Band Filter and Denylist](#160-dev1---2026-06-11---persistent-last-seen-band-filter-and-denylist)
  - [\[1.5.0-dev6\] - 2026-06-11 - Validation Tooling Sync System](#150-dev6---2026-06-11---validation-tooling-sync-system)
  - [\[1.5.0-dev5\] - 2026-06-07 - README Emoji Consistency; mypy Realigned With HA](#150-dev5---2026-06-07---readme-emoji-consistency-mypy-realigned-with-ha)
  - [\[1.5.0-dev4\] - 2026-06-03 - Service Registration Moved to `async_setup`; Exception Translations](#150-dev4---2026-06-03---service-registration-moved-to-async_setup-exception-translations)
  - [\[1.5.0-dev3\] - 2026-06-03 - Scan Button Error Propagation; Service Lifecycle Cleanup](#150-dev3---2026-06-03---scan-button-error-propagation-service-lifecycle-cleanup)
  - [\[1.5.0-dev2\] - 2026-06-02 - Level 1 Deeper Testing: 22 New Tests](#150-dev2---2026-06-02---level-1-deeper-testing-22-new-tests)
  - [\[1.5.0-dev1\] - 2026-06-02 - Scan Now Button, Proximity Alert and Pattern Matching](#150-dev1---2026-06-02---scan-now-button-proximity-alert-and-pattern-matching)
  - [\[1.4.4-dev3\] - 2026-06-02 - README Aligned With ZTE; mypy Strict Errors Fixed](#144-dev3---2026-06-02---readme-aligned-with-zte-mypy-strict-errors-fixed)
  - [\[1.4.4-dev2\] - 2026-05-13 - Full IQS Review; runtime-data and Repair Issues](#144-dev2---2026-05-13---full-iqs-review-runtime-data-and-repair-issues)
  - [\[1.4.4-dev1\] - 2026-05-13 - `icons.json` Adopted; mypy Strict Clean](#144-dev1---2026-05-13---iconsjson-adopted-mypy-strict-clean)
  - [\[1.4.3\] - 2026-05-10 - README Overhaul and Internal Alignment](#143---2026-05-10---readme-overhaul-and-internal-alignment)
  - [\[1.4.3-rc1\] - 2026-05-10 - README Expanded; Project-Agnostic `pyproject` and `tasks`](#143-rc1---2026-05-10---readme-expanded-project-agnostic-pyproject-and-tasks)
  - [\[1.4.3-dev20\] - 2026-05-09 - Shared Reusable CI Workflow Created](#143-dev20---2026-05-09---shared-reusable-ci-workflow-created)
  - [\[1.4.3-dev11\] - 2026-05-09 - mypy Type Annotations Added](#143-dev11---2026-05-09---mypy-type-annotations-added)
  - [\[1.4.3-dev4\] - 2026-05-06 - `quality_scale.yaml` Added; Sensor Coverage](#143-dev4---2026-05-06---quality_scaleyaml-added-sensor-coverage)
  - [\[1.4.3-dev3\] - 2026-05-06 - Diagnostics, Reauth and Reconfigure Flows](#143-dev3---2026-05-06---diagnostics-reauth-and-reconfigure-flows)
  - [\[1.4.3-dev2\] - 2026-05-06 - Entity Manifest and Guard-Band Docs; `api.py` to 100%](#143-dev2---2026-05-06---entity-manifest-and-guard-band-docs-apipy-to-100)
  - [\[1.4.3-dev1\] - 2026-05-02 - README Badge Links](#143-dev1---2026-05-02---readme-badge-links)
  - [\[1.4.2\] - 2026-05-02 - Scan Interval Minimum Aligned to 60 Seconds](#142---2026-05-02---scan-interval-minimum-aligned-to-60-seconds)
  - [\[1.4.2-dev3\] - 2026-05-01 - Code-Review Fixes; Binary Sensor and Resilience Tests](#142-dev3---2026-05-01---code-review-fixes-binary-sensor-and-resilience-tests)
  - [\[1.4.1\] - 2026-04-18 - Last Updated Sensor; Custom Naming; Guard Bands](#141---2026-04-18---last-updated-sensor-custom-naming-guard-bands)
  - [\[1.4.0\] - 2026-04-05 - WiFi Interface Auto-Discovery](#140---2026-04-05---wifi-interface-auto-discovery)
  - [\[1.3.1\] - 2026-04-02 - Structured Network Data Model](#131---2026-04-02---structured-network-data-model)
  - [\[1.3.0\] - 2026-04-02 - Renamed to WiFi SSID Monitor](#130---2026-04-02---renamed-to-wifi-ssid-monitor)
  - [\[1.2.0\] - 2026-04-02 - Scan Interval Slider](#120---2026-04-02---scan-interval-slider)
  - [\[1.1.0\] - 2026-04-02 - New Network Alert and Interface Sensor](#110---2026-04-02---new-network-alert-and-interface-sensor)
  - [\[1.0.2\] - 2026-04-02 - Branding and Mock Supervisor](#102---2026-04-02---branding-and-mock-supervisor)
  - [\[1.0.1\] - 2026-04-02 - Test Coverage to 99%](#101---2026-04-02---test-coverage-to-99)
  - [\[1.0.0\] - 2026-04-01 - Initial Release](#100---2026-04-01---initial-release)

---

## [2.0.1-dev13] - 2026-08-03 - Standards Test Coverage: §6, §12, §19 and §21 Guards; Action Icons

Implements Priority 1 of `.notes/issues/changes_20260803/wifi_changes_20260803.md` — the four standards `[2.0.1-dev12]` mutation-proved to have no working guard, plus the §21 test that could not fail. **217 → 232 tests, 100% coverage held**, `mypy --strict` and `ruff` clean.

**Every test was verified by mutation** — written, then the guarded thing deliberately broken to confirm it goes red, then restored. Ten mutations across `health.py`, `sensor.py`, `parse.py`, `icons.json` and `__init__.py`; all reverted, `git status --short` confirmed clean for `custom_components/` after each, full suite green afterwards. "A test exists" was not the bar; "a test that fails on this regression exists" was.

**One behavior-affecting change**, and it is additive: six action icons. No integration logic changed.

### Added

- **§19 — the `drift` / `degraded_capabilities` split is now guarded.** The `[2.0.1-dev7]` classification was unasserted: `is_drift` appeared nowhere in `tests/`, and flipping four tags left all 217 tests passing. §19's attribute set is a **published contract** users write templates against, so a re-tagged check silently changes what an automation reads.
  - `tests/test_integration_health.py` — `test_every_check_has_a_firing_fixture` (a check added to `CHECKS` with no fixture fails here rather than quietly shrinking the sweep), `test_every_finding_is_classified_exactly_once` (every key is drift **or** a capability, never neither or both), plus guards for `band_unresolved_some` — the second key one check can produce — and for `is_drift` defaulting to `False`.
  - `tests/test_coordinator.py` — two published-attribute tests proving the classification actually reaches the attribute a template reads: a payload-shape finding lands in `drift` with `degraded_capabilities` empty, and a failed capability the reverse.
  - Mutation-verified three ways, including the reverse direction (`interface_missing` → `is_drift=True`).

- **§6 — guard-band coverage and the `TOTAL` ban** (`tests/test_sensor.py`). `test_guard_bands` proved the mechanism on one sensor and said nothing about how many sensors reach it. **The bands themselves were already correct** — all four sensors carrying a unit or `state_class` declare bounds — but nothing held them there.
  - `test_every_numeric_sensor_has_a_guard_band` — static sweep over `SENSOR_TYPES` with an empty, named `UNGUARDED_ALLOWLIST` and a `>= 4` vacuity floor. Static, not runtime, per §6: a guard band is never published, so no live query can observe one.
  - `test_unguarded_allowlist_has_no_dead_entries` — an exemption cannot outlive the sensor, the bounds it was granted for, or the sensor's numeric-ness.
  - `test_no_sensor_uses_the_total_state_class` — empty `ALLOWED_TOTAL_STATE_CLASS`. Zero `TOTAL` today, so it costs nothing; it exists because ZTE's six monthly byte counters shipped as `TOTAL` and walked long-term statistics backwards on every rollover.

- **§6 — rounding at parse time** (`tests/test_parse.py`). `_safe_float` rounds to 3 dp and nothing asserted it. The new test uses `_safe_float("99.930600002408") == 99.931` — the only shape that can fail when `round()` is deleted; the `approx(37.2)` form the standard warns about passes either way. Tolerance contracts for both `_safe_float` and `_safe_int` added alongside.

- **§12 — icon coverage, entities and actions** (`tests/test_entity_hygiene.py`). No icon test existed in any form.
  - `test_every_live_entity_has_an_icon_or_a_device_class` — sweeps the **live** entity list, not a description list (descriptions here live in a mix of tuples and module-level singletons), and looks up **per platform**, so an entry filed under the wrong platform cannot satisfy it. Also fails on dead entries.
  - `test_every_registered_action_has_an_icon` — bidirectional against `hass.services.async_services()`, never against the icon file being tested, and rejects the legacy flat declaration form.
  - Mutation-verified four ways, including the subtle one: moving an icon to the wrong platform.

- **§21 — a removal test that can fail** (`tests/test_init.py`). `test_async_remove_entry` set an entry up, removed it and asserted nothing; it passed, counted toward coverage, and could not fail. Replaced with `test_async_remove_entry_deletes_every_live_store`, which spies on `Store.async_remove` and asserts the coordinator's three **live** `store.key` values against the **observed removal calls** — not against the shared helper, since `store.key == helper(entry_id)` proves only that the write side uses the helper. Plus `test_storage_keys_are_entry_scoped`. Mutation-verified by making removal build its own keys and delete 1 of 3.

- **Action icons** (`icons.json`). Six actions — `add_ssid`, `clear_last_seen`, `get_networks`, `remove_ssid`, `scan_now`, `set_ssids` — in the nested `{"service": "mdi:..."}` form required by `dev_standards` 1.21.0. These render in the automation and script editors and in Developer Tools → Actions; until now all six showed the generic default. Closed here rather than in Priority 2 because the new action test failed on the real gap, and shipping a knowingly-red test is not an option.

### Changed

- **`MIN_ENTITIES_SWEPT` 2 → 16** in `tests/test_entity_hygiene.py`. Measured: 16 of 18 entities publish attributes; the other two publish none and are correctly skipped. At `2` the staleness guard passed while 14 entities could go uninspected — the failure it exists to prevent.

### Notes

- **A defect was found in the new tests themselves.** The first icon sweep reported three dead entries that were not dead: `seen_keys` was recorded _after_ the `device_class` skip, so an entity carrying a device class **and** a deliberate icon override looked orphaned. Fixed, with a comment at the site, because it would be easy to reintroduce.

- **Coverage-shaped, not sample-shaped.** Each new test sweeps a set — `CHECKS`, `SENSOR_TYPES`, the live entity list, the registered action set — rather than asserting a known member. Per §11: a test asserting a mechanism passes right up until the mechanism is bypassed, while one asserting every member of a set is covered fails the moment the set grows. Adding a health check without classifying it, a sensor without bounds, an entity without an icon or an action without one now fails.

- **Two Priority 4 items folded in**, both one-file, one-shape changes in files already being edited: `MIN_ENTITIES_SWEPT` (4.1) and the `TOTAL` ban (4.4, which the plan explicitly directed be folded into the §6 work).

### Fixed — Priority 2

- **UK spellings removed from shipped user-facing text.** `doc_style.md` mandates US spelling and `codespell` does not flag UK forms, so nothing would have caught these. The one that mattered is `button.py`'s `about` note — a string users read in the More Info dialog — which said an explicit request is always _honoured_. Eleven substitutions across five files: `honoured` (button.py, README), `neighbouring` / `neighbour` / `neighbours` / `neighbourhood` (diagnostics.py, README, ROADMAP.md), `catalogue` (ROADMAP.md, DEVELOPMENT.md) and `labelled` (ROADMAP.md). The sweep was widened past the four words the review listed and found three more.

- **`sensor.interface` gained an `about` note.** The `dev_std_review` recorded both un-annotated sensors as correct §14 omissions. That was half wrong: `wlan0` is self-explanatory only to a reader who already knows what an interface is, which is the opposite of what the note is for. The new note names the adapter and states the consequence — a different adapter, or one moved elsewhere in the building, sees a different set of networks. `last_updated` stays omitted and is now the single recorded omission; a timestamp named "Last Updated" does explain itself, and §14 warns that annotating everything trains users to ignore notes.

- **`docs/all_sensors.md` → v2.0.0: the device model it described was never built.** The file specified a **System** sub-device (6 entities) and a **Monitor** sub-device (12), each with a `_Group:_` key. There is one flat `DeviceInfo`, and `via_device`, `async_get_or_create` and any `group` field are absent from the whole component — a maintainer following this document would have gone looking for routing code that does not exist. The flat model is now stated explicitly, along with the fact that the sub-devices were never built and that §7 is `N/A` here, so the question is closed rather than reopened.

  The **Key** column was also wrong throughout, listing entity-id suffixes (`total_ssid_count`) where the descriptions use `count`; how Home Assistant derives the entity id from the name is now explained inline. Regrouped by platform, guard bands and device classes added, the `drift` and `degraded_capabilities` health attributes added (missing since `[2.0.1-dev7]`), and the deliberate `about` omission recorded as §14 requires. All 18 keys were reconciled against source programmatically rather than by eye.

- **`docs/value_min_max.md` → v2.0.0: reconciled against the code in both directions**, which §6 requires and which had never been done. Four corrections. **Two bands existed and were undocumented** — `new_24h` (0–4096) and the `proximity_signal_threshold` control range (0–100). **One was understated**: Strongest Unknown Signal was described as clamped in the parse boundary only, when the description also declares `min_limit=0, max_limit=100`. The **Key column was wrong** and the worked example used a `name=` field that is the §12 anti-pattern and appears nowhere in the code. And the **"Future Extensions" section that v1.0.2 records as removed was still present**.

  Added the three sensors that correctly have no bounds, so their absence reads as deliberate; added control-range and state-class sections; and pointed at the three tests from this release that now enforce coverage, exemption hygiene and the `TOTAL` ban — none of which existed when the document was last touched.

## [2.0.1-dev12] - 2026-08-03 - Validation Pass; ROADMAP Conversion; dev_std_review and IQS SCAN=Full

**The devcontainer is running.** Everything flagged unvalidated in `[2.0.1-dev6]` through `[2.0.1-dev9]` is now backed by a real run: `pytest` **217 passed at 100% coverage**, `mypy --strict` clean, `ruff`, hassfest and the remaining validations passing.

**One source change in this entry** (`quality_scale.yaml`); everything else is documents, records and findings. No behavior changed.

### Changed

- **`docs/FUTURE.md` → `docs/ROADMAP.md`**, refactored to `roadmap_format.md`. Closes `x_proj_checks_20260802.md` §3.3, which listed WiFi as needing "a rename plus a refactor". Six groups replace the previous per-release delivered tables and mixed opportunities section. **Done is now membership by provenance**, so the off-roadmap v2.0.0 deliveries no longer qualify — they are kept in an explicitly labelled subsection rather than dropped, because this is the first conversion and losing content in the move would be indistinguishable from losing it by accident.

  Three items merged into one **Per-network entities** item with a shared foundation and three phases (my-WiFi count and offline sensors → per-network device trackers → per-network signal sensors). They were one feature listed three times: all three read the same list, and building them separately would have produced three lists, two parallel presence calculations and a signal sensor with no defined "gone" state.

  Phase 2's entity type is **decided: `device_tracker` on `BaseScannerEntity`**, with a dated prior-art subsection so it is not re-searched. An access point is a physical device, so `home` states the useful fact — it is in or near this house — which holds for a network the user owns and equally for one they are watching, and the transition to `not_home` is the event worth having. `ScannerEntity` is recorded as the wrong class and the one that would be actual misuse: it is for devices that connect to the IP network and are identified by MAC, which an observed AP does not do.

  The old presence item's "is my work laptop nearby?" framing is removed — a laptop does not broadcast an SSID, so the example described something the feature cannot do.

- **`.shared/dev_std/roadmap_format.md` → v1.2.0.** New **§4 Tone and language** with a test — _does the opening sentence say what would be built?_ — after the conversion produced an item promising something that "cannot be fooled and needs no per-install tuning" without ever saying it was two entities. States explicitly that uncertainty is in scope and length is not the target, so it is not read as an instruction to be terse. Sections renumbered from 4 onward.

- **`.shared/dev_std/dev_standards.md` → 1.21.0: §12 extended from entity icons to action icons.** A gap in the standard, not in this project. The `**Test:**` tag had carried check (c) for services since 1.13.0 while the section's **Standard** line and `Icons (standard)` bullet described entities only — so the tag mandated a test for a requirement the section never stated, and every project read §12's body and correctly concluded action icons were not required. Found here: `icons.json` carries **no `services` block** while six actions are registered, and the finding had nowhere to attach.

  The Standard line now names action coverage; a new **Action icons (standard)** bullet gives the required nested `{"service": "mdi:…"}` form, records the flat string form as legacy-but-working, and states **where these icons appear** — the automation and script editors and Developer Tools → Actions, and nowhere on the device page or an entity, which is why an integration missing them looks entirely normal. Check (c) renamed Services → Actions and made bidirectional. Tag header corrected from "Two checks" to three. Also recorded that **no IQS rule reaches action icons**, so this half of §12 is PlayFaster-only.

  All four projects' `icons.json` were enumerated: **ZTE** 4 actions nested (the reference), **UniFi** 7 actions flat/legacy, **WiFi** and **Huawei** no block at all. Cross-project status and UniFi's format conversion tracked in `x_proj_checks_20260802.md` **§3.7** (that document bumped to v1.1.0). §12's `DONE` cells for ZTE and UniFi are now assessed against superseded wording and were **deliberately not changed** — they belong to those projects' own review passes.

- **`custom_components/wifi_ssid_monitor/quality_scale.yaml`: `reauthentication-flow` `done` → `exempt`**, with a comment. Not a shortfall — `async_step_reauth` and `async_step_reauth_confirm` exist and re-validate the interface — but this integration stores **no credential**: the Supervisor token is read from `SUPERVISOR_TOKEN` at call time and never enters the config entry or a schema, so nothing can fail authentication and `ConfigEntryAuthFailed` is never raised. `done` read as an authentication surface that does not exist. The comment records that the steps are **retained**, so they are not later removed as dead code. Matrix cell in `ha_quality_standard.md` moved to `N/A` to match; that document is now **v1.15.2**.

### Notes

- **Four standards were mutation-proved to have no working guard.** Each mutation was reverted and the revert confirmed by `git status --short` on `custom_components/` and `tests/`; the full suite was re-run green afterwards.

  | Mutation | Result |
  | :-- | :-- |
  | Removed `min_limit`/`max_limit` from `strongest_unknown_signal` | **217/217 pass** — §6 guard-band coverage unguarded |
  | Deleted `entity.sensor.interface` from `icons.json` | **217/217 pass** — §12 icons unguarded |
  | Flipped four `is_drift=True` → `False` in `health.py` | **217/217 pass** — the `[2.0.1-dev7]` attribute split unguarded |
  | (`test_async_remove_entry` already asserts nothing) | cannot fail — §21 unguarded |

  The `drift` one is the most valuable missing test in the project: §19's attribute set is a **published contract** users write templates against, `is_drift` appears nowhere in `tests/`, and re-tagging a check today would break nothing.

- **The §14 sweep is effective — and its `entity_registry_enabled_default` patch is inert here.** Removing `severity` from the health sensor's `_unrecorded_attributes` failed both the runtime sweep and the static guard, so `[2.0.1-dev8]`'s test is not in the state `zte_router_5g`'s was. But **no entity in this project is disabled by default**, so the class of failure that patch was added for cannot occur; keep it, but do not read its presence as evidence the sweep was validated against that case. `MIN_ENTITIES_SWEPT` is still `2` against a **measured 16** — the sweep counts only entities publishing attributes, so 16 of 18 is correct, and at `2` the staleness guard is nearly vacuous.

- **§21 corrected: the drift bug is not live here.** `[2.0.1-dev9]` claimed it was. A probe confirmed all three store keys reach `Store.async_remove` and both sides build them from the same three helpers in `const.py`. The gap is a missing guard, not a defect — which lowers its urgency without changing its status.

- **§9 is `N/A`, not `PENDING`.** The integration stores no secret to pre-fill. Like §10, a real answer rather than an unassessed one.

- **§12 translations reconcile clean**, verified by the code-to-artefact check rather than by comparing the two JSON files: 18 of 18 entity keys across all five present platforms resolve in both `strings.json` and `translations/en.json`, with no orphan in either direction. The standard is met; what is missing is the test that keeps it met.

- **Guard bands are already in place — only the test is outstanding.** Worth stating plainly, because the §6 finding is easy to misread as "add bounds". All four sensors that §6 asks about declare them: `count` and `unknown_count` 0–256, `new_24h` 0–4096, `strongest_unknown_signal` 0–100. The other three carry neither a unit nor a `state_class` and correctly need none — `interface` and `strongest_unknown_ssid` are text, `last_updated` is a `TIMESTAMP` device class. Both `number` entities are bounded by `native_min_value` / `native_max_value`.

- **The `about` omission assessment was revised.** The review recorded both un-annotated sensors — `interface` and `last_updated` — as correct omissions under §14. Half wrong: `wlan0` is self-explanatory only to someone who already knows what an interface is, which is the opposite of what an `about` note is for. `interface` gains a note; `last_updated` stays omitted, since a timestamp named "Last Updated" does explain itself and §14 warns that annotating everything trains users to ignore notes. The recorded omission set is therefore **one entity, not two**.

### Reviews

Two full passes were run. Both reports are in `.notes/dev_std/`; the consolidated work list is `.notes/issues/changes_20260803/wifi_changes_20260803.md`.

- **`dev_std_review` — `.notes/dev_std/dev_std_review_20260803_1438.md`.** First on this project. All 22 sections: **9 DONE, 9 PARTIAL, 0 PENDING, 4 N/A**, 20 findings. Gaps are almost entirely coverage rather than correctness. Two are not: `docs/all_sensors.md` documents a **two sub-device architecture that does not exist** — one flat `DeviceInfo`, no `via_device`, no `async_get_or_create`, no `group` field anywhere — and `about` notes shipped to users carry UK spellings against `doc_style.md`, which `codespell` does not flag. §19 and §20 were assessed as the strongest work in the family.

- **`iqs_next_steps` at `SCAN=Full` — `.notes/dev_std/next_steps_20260803_1451.md`.** All 48 `done` cells re-validated against source rather than accepted. **All 48 hold; no gap at any tier.** The three 1e verification checks all ran with real coverage and were clean: cross-table verdict diff 54 compared with no mismatches, code-to-artefact reconciliation clean on all five platforms, YAML-vs-matrix 54 compared with zero conflicts.

  **One finding was raised and withdrawn before it was recorded.** `icon-translations` was drafted as a downgrade to PARTIAL because `icons.json` carries no `services` block while six actions are registered. That was wrong: the Gold rule is _"Entities implement entity icon translations"_ and is **entity-scoped**. Service icons are real — they render in the automation and script editors and the Developer Tools Actions picker — but they belong to `dev_standards` §12 check (c), not to any IQS rule. The cell stands at `done` and the item is tracked in the changes document.

  **`test-coverage` carries no quality requirement, verified.** The rule text is _"Above 95% test coverage for all integration modules"_, with `config-flow-test-coverage` requiring 100% of `config_flow.py` at Bronze. Neither says anything about assertions, meaningfulness or test quality. An earlier draft of the report editorialised that the 100% figure was "true and incomplete"; that extended the rule past what it claims and was removed. The four unguarded standards above are `dev_standards` findings and are recorded there.

### Records

- **`dev_standards.md` → Section Conformance**, 10 cells in the `wifi_ssid_monitor` column: §2 → `N/A`; §3, §5, §6, §11, §12, §13, §14, §16, §21 → `PARTIAL`.
- **`dev_standards.md` → Standards Test Coverage**, 2 cells: §9 `PENDING` → **`N/A`**, §14 `UNVERIFIED` → **`DONE`** — the first cell in that table to clear the §11 mutation bar in this project. Known-gaps bullets rewritten to match.
- **`dev_standards.md` → Project Deviations**, 2 entries: **§3** (no root registered before forwarding; root keyed on `entry_id`, which is not on the identity ladder — there is no MAC, no IP, and the monitored host is the HA machine itself) and **§13** (Refresh Now ships as `scan_now`, deliberately not renamed because HA never renames an existing `entity_id`). §5 display scaling was **not** recorded as a deviation: it is an unmet bullet awaiting a decision, not a decision already taken.
- No version entry appended to `dev_standards.md` — this pass changed matrix cells and their bullets, not the standard's own text.

### Fixed

- **`docs/DEVELOPMENT.md`** — the live cross-reference to `FUTURE.md` updated to `ROADMAP.md`. The dated `changelog_local` mention at `[1.6.0]` is left as-is: it records what was true at the time, per `roadmap_format.md` §1.

## [2.0.1-dev11] - 2026-08-03 - Hardware-Check Task; Changelog ToC Added, Bumps

### Changed

- **`tasks.json`**: Added a new hardware checks section to tasks.json, for local hardware validation. This is for ZTE only, for now and uses `scripts/hardware_check.py` within that project, to run actual hardware checks.
- **`changelog_local` ToC**: Added table of contents to `changelog_local` (top-of-file) and to the end of `CHANGELOG` and updated release headers in `changelog_local` for readability.

### Bumps

- **Shared CI**: Bump `.github` Shared CI Validation via SHA from v2.0.7 to v2.0.9
- **Validate Bump**: Update `zizmor` from 1.25.2 to 1.28.0
- **Validate Bump**: Update `ruff` from 0.15.22 to 0.16.0
- **Validate Bump**: Bumped PHACC `pytest-homeassistant-custom-component` from 0.13.348 to 0.13.351

## [2.0.1-dev10] - 2026-07-28 - Automation Example Glitch Guards & has_value Checks in README

Reinforced example automations in `README.md` to prevent false triggers during scanner entity unavailability, network glitches, or system restarts.

### Changed

- **`README.md` Example Automations Glitch Protection**:
  - **`Alert if Home WiFi Offline`**: Added `has_value()` guards to the template trigger expression so missing or `unavailable` scanner entity states do not convert `| int(0)` into `0 - 0 = 0 < 3` and trigger false offline alerts.
  - **`Alert if Device in AP Mode` & `Integration Health Problem`**: Added `not_from: ["unknown", "unavailable"]` state trigger filters.
  - **`Manage Guest Network Whitelist`**: Added `not_from` and `not_to` filters (`unknown` / `unavailable`) so router reconnects do not trigger redundant whitelist actions.

---

## [2.0.1-dev9] - 2026-07-27 - Standards Test Coverage Recorded

**No code changed in this project.** `dev_standards` **1.13.0 / 1.14.0** introduce the `**Test:**` tag and a **Standards Test Coverage** matrix; this entry records what that matrix now says about `wifi_ssid_monitor`.

### Notes

Six sections now carry a `**Test:**` tag — tagged only where breaking the standard is **silent** and the check is **exact**. This project's cells:

| §   | What the test must assert                                    | Status      |
| :-- | :----------------------------------------------------------- | :---------- |
| 6   | rounding applied at parse time                               | **PENDING** |
| 9   | stored secrets never pre-filled into a schema                | **N/A**     |
| 10  | session-terminating call awaited on unload                   | **N/A**     |
| 12  | translations + icons reconciled against code / live entities | **PENDING** |
| 14  | runtime sweep: every published attribute unrecorded          | **DONE**    |
| 21  | live `store.key` among the keys removal actually deletes     | **PENDING** |

Detail:

- **§10 is `N/A`, and that is a real answer rather than an unassessed one.** The Supervisor API holds no session to terminate, so there is nothing for an unload test to assert. The two router integrations both need this test; this one does not.
- **§6** — `_safe_float` (`parse.py:63`) rounds to 3 dp correctly, but no test asserts it: `test_safe_float_bad_types` covers bad input only, and in fact exercises `normalize_signal` rather than the helper directly.
- **§21 is the most concrete gap in this table.** `tests/test_init.py::test_async_remove_entry` sets an entry up, removes it, and **asserts nothing at all**. It is named for the standard, counts toward coverage, and cannot fail — the exact shape of problem the new §11 mutation bar exists to reject. `unifi_network_monitor` has a real version to model on.

  **Corrected 2026-08-03:** this entry previously claimed the §21 drift bug "is live here". It is not. `async_remove_entry` builds its key list from `all_storage_keys()`, and the coordinator builds its three `Store` keys from the same three helpers, so the two sides cannot diverge by construction. A probe confirmed it: all three keys are passed to `Store.async_remove`, none missed. The gap is a **missing test**, not a live defect — which lowers its urgency but not its status, since nothing currently stops a fourth store being added without a matching helper.

- **§9 is `N/A`, established 2026-08-03.** The integration stores no secret to pre-fill. The Supervisor token is read from `SUPERVISOR_TOKEN` in the environment at call time (`api.py:26`) and never enters the config entry or any schema; `config_flow.py` collects only name, interface, and the SSID lists. Like §10, this is a real answer rather than an unassessed one.
- **§12** — `tests/test_services.py::test_exception_translations` checks one exception key. That satisfies the IQS `exception-translations` rule, **not** this tag, which requires reconciling every entity `translation_key` and every icon against the code.

  **Reconciled by hand 2026-08-03 and clean:** `strings.json` and `icons.json` carry the same 16 entity keys, with no orphan in either direction, and every one resolves to a key in the code. So the standard is **met**; what is missing is the test that keeps it met. Note that service names and descriptions live inline in `services.yaml` rather than in a `services` block in `strings.json` — the older supported style, not a defect, but outside what an entity-key reconciliation test would cover.

- **§14** — the sweep was ported on 2026-07-27 and executed for the first time on 2026-08-03. It passes and found nothing leaked, so `DONE`. See the caveats in `[2.0.1-dev8]`: it has not been mutation-checked in this project, and `MIN_ENTITIES_SWEPT` is still at its placeholder value.

> [!NOTE] **Updated 2026-08-03.** The devcontainer is running, and `[2.0.1-dev7]`, `[2.0.1-dev8]` and this entry are backed by a real run: `pytest` 100% pass at 100% coverage, `mypy --strict` clean, other validations passing. §14 moves to `DONE` on that basis.
>
> **The four `PENDING` cells are unaffected by a green run, and that is the point.** They are missing tests, not unverified ones — a suite that passes says nothing about an assertion nobody wrote. §21 is the sharp case: `test_async_remove_entry` still sets an entry up, removes it and asserts nothing, so it passes, counts toward the coverage figure, and cannot fail. A 100% pass rate is precisely the condition under which that defect is invisible.

## [2.0.1-dev8] - 2026-07-27 - §14 Enforcement Test

Implements the enforcement half of `dev_standards` §14 as revised at **Standard Version 1.12.0**. The attribute fixes themselves landed in `[2.0.1-dev7]`; this entry adds the test that stops them recurring.

> [!NOTE] **Validated 2026-08-03.** The devcontainer is running and the sweep has now been executed: it passes, as does the rest of the suite at 100% coverage with `mypy --strict` clean. It found no leaked attribute, so the static fixes in `[2.0.1-dev7]` were complete.
>
> **Mutation-checked 2026-08-03 and effective.** Removing `severity` from the health sensor's `_unrecorded_attributes` failed both the runtime sweep and the static guard, so the sweep is doing real work here — it is not in the state `zte_router_5g`'s was, where the test passed with a key deliberately removed.
>
> Two notes from that run. The `entity_registry_enabled_default` patch is **inert in this project**: no entity here sets `entity_registry_enabled_default = False`, so the failure mode it was added for cannot occur. Keep it — it costs nothing and the moment a disabled-by-default entity is added it starts mattering — but do not read its presence as evidence the sweep was validated against that case, because there is no such case to validate against.
>
> And `MIN_ENTITIES_SWEPT` is still `2` against a measured **16**. The sweep counts only entities that publish attributes, so 16 of the 18 in `docs/all_sensors.md` is correct and the two skipped ones publish none. Raise the floor to 16 so a setup regression that sweeps almost nothing is caught; at `2` the guard is nearly vacuous.

### Added

- **`tests/test_entity_hygiene.py`** — ported from `zte_router_5g`. A runtime sweep sets up the integration against a real `hass`, iterates every live entity, and asserts each published attribute key appears in that entity's `_unrecorded_attributes`. `ALLOWED_RECORDED` is an explicit empty allow-list, so granting an exception is a visible act and forgetting one is not.

  It patches `Entity.entity_registry_enabled_default` to `True` so disabled-by-default entities are swept. In `zte_router_5g` the sweep was **verified by mutation to be ineffective without that patch** — it passed with a key deliberately removed — and adding it immediately surfaced a real defect in a description-driven, disabled-by-default entity that neither a static scan nor the existing suite had found.

  Plus a static regression guard naming all seven health-sensor attributes, including the `severity` and `networks_scanned` that were found recorded in `[2.0.1-dev7]`.

### Notes

- **This is the change that would have prevented `[2.0.1-dev7]`'s fix from being needed.** `_unrecorded_attributes` had fallen behind `extra_state_attributes` here as the attribute set grew, and nothing failed. `zte_router_5g` had a test for this and caught its own equivalent gap on the first run; this project did not, which is the whole reason §14 1.12.0 now mandates the test rather than leaving it to review.
- **Worth running early once the container is up.** A brand-new sweep across an integration that has never been checked this way is the most likely of this session's changes to find something — that is precisely what happened in `zte_router_5g`.

## [2.0.1-dev7] - 2026-07-27 - §19 `drift` Attribute

> [!NOTE] **Validated 2026-08-03.** The devcontainer is running. `pytest` passes at 100% with 100% coverage, `mypy --strict` is clean, and the remaining validations pass. The code below is no longer resting on the `ruff`-only checks originally done by copying files into a sibling container.
>
> [!WARNING] **The `drift` split itself is unguarded, found 2026-08-03.** Flipping four `is_drift=True` tags in `health.py` to `False` — reversing most of this entry's behaviour change — leaves the whole suite passing, 217 tests. No test asserts that a drift-tagged check lands in `drift` rather than `degraded_capabilities`; `is_drift` appears nowhere in `tests/`, and `drift` only in the static hygiene guard, which asserts the attribute is unrecorded and says nothing about its contents. 100% coverage means those lines executed, not that the classification was checked. This is the most valuable test missing from the project: it guards a documented attribute contract that users template against, and re-tagging a check today would break nothing.

### Added

- **The health sensor now publishes a `drift` attribute** (`dev_standards` §19, normative attribute table added at Standard Version 1.11.0). That table makes `drift` conditional — omit it only where no drift check exists — and this integration is built around one: the module docstring in `health.py` names the incident it exists for, the Supervisor payload moving from `channel` to `frequency` while the band filter silently matched nothing.

- **`Finding.is_drift`**, defaulting to `False`. §19 splits the health verdict two ways — a **capability** that has failed versus **contract/semantic drift** — and this integration was folding both into `degraded_capabilities`. Six checks are now tagged as drift: `signal_format_changed`, `payload_no_ap_list`, `payload_field_missing`, `payload_field_partial`, `band_unresolved_all`, `band_unresolved_some`. Four remain capability findings: `interface_missing`, `no_known_networks`, `empty_scan`, and the directly-set `supervisor_unreachable`.

  **The default is `False` deliberately.** `health.py` advertises that adding a check is a one-line addition to `CHECKS`, so the classification must fail safe: a new check is reported as a capability unless it opts in. Under-claiming drift is the recoverable error; over-claiming it raises a firmware-changed alarm for an environmental condition.

### Fixed

- **`severity` and `networks_scanned` were published but not recorder-excluded.** Found while adding `drift` to `_unrecorded_attributes`. §19 requires the health detail to live in _unrecorded_ attributes, and `_unrecorded_attributes` had fallen behind `extra_state_attributes` — so two diagnostic fields, one of them changing on every scan, were being written to the recorder database on every state change. All published attributes are now listed, with a comment stating the list must track the property.

  **This is why the sibling project caught its equivalent and this one did not:** `zte_router_5g` has `test_attributes_are_unrecorded`, which walks the published attributes and asserts each is excluded. It flagged its own missing entry on the first run of this change. No equivalent test existed here at the time — `tests/test_entity_hygiene.py` in `[2.0.1-dev8]` is that test, and it now passes.

- **Pre-existing E501** on the `degraded_capabilities` line in `binary_sensor.py`, wrapped by `ruff format`. It predates this session and indicates this file has not been linted recently.

### Changed

- **`degraded_capabilities` no longer carries drift findings**, which is a behaviour change for anyone templating against it: a payload-shape finding that previously appeared there now appears in `drift`. The health sensor still turns `on` for both, and `issues` still carries every confirmed message, so an automation triggering on the sensor state or reading `issues` is unaffected. Acceptable here because the health sensor shipped this week and the attribute split is what §19 specifies.

## [2.0.1-dev6] - 2026-07-27 - Cross-Project Alignment

Follows a three-way review of `wifi_ssid_monitor`, `unifi_network_monitor` and `zte_router_5g`, checking that the three meet the shared standards the **same way** rather than merely meeting them. The functionality differs by design; the approaches should not.

> [!NOTE]
>
> **Validated 2026-08-03.** The devcontainer is running. `pytest` passes at 100% with 100% coverage, `mypy --strict` is clean, and the remaining validations pass. The attribute renames and the test-file rename are confirmed by a real run; this entry is complete.

### Changed

- **Health-sensor attributes renamed to match dev_standards §19 and the other two projects:**
  - `last_good_scan` → **`last_good_update`**
  - `checks_failed` → **`degraded_capabilities`**

  §19 names these attributes explicitly, and `unifi_network_monitor` already used both full names. Three projects had drifted to three vocabularies for the same two concepts, so an automation written against one did not transfer to another — and the divergence had already produced a live defect in UniFi's README, which referenced this project's `checks_failed` in its own example. All three now publish the identical core contract: `problem`, `issues`, `severity`, `degraded_capabilities`, `last_good_update`, plus per-project extras.

  Updated across `coordinator.py`, `binary_sensor.py`, `tests/test_binary_sensor.py` and `README.md` — 13 references in total.

- **`tests/test_health.py` renamed to `tests/test_integration_health.py`.** New convention across all three projects: name the test file after the **standard** it covers, not the platform or the symptom.

### Added

- **`quality_scale.yaml`: `docs-conditions` and `docs-triggers` added as `exempt`.** Both were **missing entirely** — the file carried 52 of the canonical 54 rules, so the two were neither assessed nor visible as gaps, and any future compliance pass would have re-flagged them. The integration has no `condition.py`, `trigger.py`, `conditions.yaml` or `triggers.yaml`, and no corresponding `strings.json` blocks, so `exempt` is correct. The `docs-triggers` comment notes that the `wifi_ssid_monitor_new_network` bus event is an **event**, not a trigger platform, and points at the analysis in `.notes/issues/custom_trigger_condition/wifi_trigger_options.md`. The file now matches the canonical rule set exactly, in canonical order. Compliance matrix cells updated to match.

### Notes

- **This project is the strongest candidate in the family for a custom trigger platform**, should HA's trigger API stabilise and document itself. The `new_network` event already computes in its payload exactly the filters users want (band, signal, hidden/anomalous), so a trigger would be a thin wrapper rather than new logic. Blocked on the same product decision as the others — the API is a 2026.x construct against a declared floor of HA 2024.8.0, and there is no developer documentation. See the note above for the full analysis.
- No behaviour changed in this entry beyond attribute naming.

## [2.0.1-dev5] - 2026-07-26 - README Section Names and Links

### Changed

- **README**: Tweak to Readme - section names and links.

## [2.0.1-dev4] - 2026-07-26 - Ruff Bump 0.15.21 → 0.15.22

### Bumps

- **Validate Bump**: Update `ruff`from 0.15.21 to 0.15.22

## [2.0.1-dev3] - 2026-07-26 - Shared CI Bump v2.0.5 → v2.0.6

### Bumps

- **Shared .github CI Validation**: Bump .github Shared CI Validation via SHA from v2.0.5 to v2.0.6

## [2.0.1-dev2] - 2026-07-26 - README Tweaks; AGENTS.md Restructured

### Changed

- **README**: Tweak to Readme
- **AGENTS**: Rewrite of AGENTS.md to move content shared across projects to a shared file, and to move sensor entity counts to using `docs/all_sensors.md`as the definitive source.

## [2.0.1-dev1] - 2026-07-26 - PHACC Bump 0.13.347 → 0.13.348

### Bumps

- **Validate Bump**: Bumped PHACC `pytest-homeassistant-custom-component` from 0.13.347 to 0.13.348

---

## [2.0.0] - 2026-07-25 - Signal as a Percentage; Health Sensor; Breaking Renames

> **This release has breaking changes - see the Breaking section.**

### Summary

A major update, with significant capability improvements and fixes BUT also some **breaking changes** unfortunately. The integration was originally developed taking SSID signal as RSSI in dBm [-100 to -30], but this number is actually Signal Quality in % [0 to 100]. This meant that the proximity threshold checking was not working as expected.

**THE FIX**: SSID Signal is now as a **0–100% quality figure** (not dBm), and Proximity Signal Threshold is also % to match.

**NEW**: Hidden networks are now identified individually, BSSID is captured and matchable, an **Integration Health** sensor catches silent errors, and several set-up controls move to became control entities. A new `get_networks` action allows current SSID status to be captured and used in automations and scripts.

- Hidden Network Labelled - Hidden networks now get a name label, using the hidden BSSID, so you can distinguish between always on, repeat and new hidden networks

- Sharper identification - hardware addresses (BSSIDs) usable in your known and blocked lists, spoofed-looking names flagged, and a New Networks (24h) sensor for what's appeared recently.

- Integration Health sensor - stays visible even when everything else goes unavailable, and tells you when a WiFi adapter has disappeared, a Home Assistant update changed the data underneath, or all your known networks vanished at once. Raises a Repair notification where there's something you can act on.

- Controls on the device page - scan interval, per-band 2.4/5/6 GHz switches, hidden-network handling, proximity threshold and a new Pause Polling switch, all usable from a dashboard or an automation instead of the settings dialog.

- Get Networks action and New Network event - ask for exactly the networks you want (by band, signal, keyword, known or unknown) and get data automations can use; the event fires once per genuinely new arrival and remembers across restarts.

### Breaking

> **Upgrading from 1.6.x to 2.0.0 or above - breaking changes.** This release corrects long-standing signal-unit and band-filter bugs, which required renaming several things. There are also some moves. This was not done lightly, but the previous set-up was incorrect.
>
> 1. **`sensor.wifi_ssid_monitor_strongest_unknown_rssi` is removed**, replaced by `sensor.wifi_ssid_monitor_strongest_unknown_signal` (0–100%, not dBm). The old entity becomes unavailable - delete it when convenient; its long-term statistics are kept (delete in Developer Tools > Statistics). Update any dashboard or automation referencing it.
> 2. **Signal is now a 0–100% quality figure** everywhere. Higher means closer. The Proximity Alert now compares on this scale, and its threshold moved to the **Proximity Signal Threshold** number entity (default 80%). A stored dBm threshold is migrated automatically.
> 3. **The list-management services were renamed and merged.** `add_known_ssid` → `add_ssid`, `remove_known_ssid` → `remove_ssid`, `set_known_ssids` → `set_ssids`, each now taking a required `target: known | denylist` (and `set_known_ssids`'s `known_ssids` field is now `values`). **There are no aliases** - automations calling the old names will fail. Update them, including any copied from the guest-network example below.
> 4. **Four settings moved out of the Configure dialog** and are now entities on the device page: **Scan Interval**, **Include Hidden Networks**, and the band filter (now three **Show 2.4/5/6 GHz** switches). The old `scan_bands` option is migrated.

### Added

- **Integration Health binary sensor** - a `problem` sensor that stays available even during an outage, reporting an unreachable Supervisor, a changed payload shape or unit, an unresolved band, or all known networks vanishing at once. Backed by `interface_missing`, `signal_format_changed`, and `supervisor_unavailable` repair issues.
- **`about` notes**: All sensor entities now have an "about:" attribute (visible in details) that explains the sensor. This information is set as `unrecorded` which prevents it being written to the Home Assistant database and taking up unnecessary space.
- **Pause Polling switch** - halt scheduled scanning; explicit actions still fetch while paused.
- **6 GHz support** and per-band **Show 2.4 / 5 / 6 GHz** switches replacing the single-choice band filter. Obviously this only has an impact if your Home Assistant system WiFi is 6GHz capable.
- **Individual hidden-network naming** - cloaked networks are identified as `Hidden-<last 4 of BSSID>` instead of collapsing into one `[hidden]` entry.
- **`get_networks` action** - a response action returning the current networks filtered by scope, band, signal and keyword; reads live scan data, so it works when the sensors are unavailable or their attribute list is capped.
- **New Networks (24h) sensor** and the **`wifi_ssid_monitor_new_network` bus event** - fires once per genuinely-new network, survives restarts, baselined on first scan and rate-limited.
- **BSSID exposure and matching** - `bssid` on the per-network detail, the action response and the event payload; `known_wifi_ids` and `denylist_ssids` now match against the BSSID as well as the name, so exact MACs and MAC wildcards (`AA:BB:CC:*`) are valid in both lists.
- **`ssid_anomaly` flag** - set when a name is hidden or contains control, zero-width, or right-to-left characters (the toolkit for spoofing a network name).
- **Operating mode (`mode`)** on the per-network detail, action response, and event payload.
- **Denylist management from automations** via the `target` argument on the list actions.
- **Refreshed icons and branding.**

### Changed

- **Signal is a 0–100% quality figure throughout** - sensors, the proximity threshold, and the action filters all use the same scale.
- **Channel / Band Correct**: The channel and band detail (Strongest Unknown SSID - Networks attribute) was being misreported on many systems (conflating frequency and channel).
- **Per-network detail relocated** onto **Strongest Unknown SSID** as a `networks` list capped at the 25 strongest (with a `networks_truncated` flag), and excluded from the recorder along with the other high-churn attributes.
- **Strongest Unknown SSID reads `None Detected`** when nothing unknown is in range, instead of `unknown`.
- **History writes are coalesced** rather than written on every scan, with a hard entry cap bounding growth in SSID-heavy locations.
- **First-run setup failures raise `ConfigEntryNotReady`**, so Home Assistant shows its native retry behavior instead of marking the entry set up. The 3-strike hold still applies once running.
- **Documentation overhauled** - the README gained a detection deep-dive, an entity/action reference, architecture and self-diagnosis sections, and a restructured FAQ.
- **All Attributes `unrecorded`**: All attributes of sensor entities are now written as `unrecorded`, which prevents them being written to the Home Assistant database and taking up unnecessary space.

### Fixed

- **The band filter no longer hides every network** - band is derived from `frequency`, and an unresolved band passes rather than being dropped.
- **The Proximity Alert no longer fires permanently** - it previously compared a 0–100 value against a negative dBm threshold, so it was on whenever any unknown network was visible.
- **Interface auto-detection works on Raspberry Pi** - the Supervisor reports `wireless` there rather than `wifi`.
- **Diagnostics redacts neighboring SSIDs** - a structural sanitizer pseudonymizes SSIDs and BSSIDs, including where they are used as dictionary keys, while preserving signal, channel, band and counts.
- **Action calls targeting an unloaded entry** return a clear, translated error instead of an internal failure.

### Removed

- **`sensor.…_strongest_unknown_rssi`** - superseded by `…_strongest_unknown_signal` (see Breaking).

---

## [2.0.0-dev9] - 2026-07-25 - Docs and Formats

### Changed

- **Docs**: Formats, fixes and spellings.

## [2.0.0-dev8] - 2026-07-24 - Readme Automations and Edits

### Changed

- **README**: Further tweaks and enhancements, error fixes and automation improvements. Also, linking of automation examples to relevant parts of file.

## [2.0.0-dev7] - 2026-07-24 - Readme Screenshots and Automations

### Changed

- **Screenshots**: Updated the README screenshots to v2.0.0
- **Automations**: Added additional example automations and included "note:" functionality in all, where useful.

## [2.0.0-dev6] - 2026-07-24 - Signal to dBm Comparisons

### Changed

- **Signal vs dBm**: Added a comparison table and note to the README.md file

## [2.0.0-dev5] - 2026-07-23 - Icons and Branding Refreshed

### Changed

- **Icons & Branding**: Updated the icons and logos for the project.

## [2.0.0-dev4] - 2026-07-23 - Exception Translation; UniFi-Aligned README Overhaul

### Added

- **`entry_not_loaded` Exception Translation**: Added the `entry_not_loaded` exception key to both `strings.json` and `translations/en.json` with a `{entry_id}` placeholder, ensuring Home Assistant displays localized error messages when action calls target an unloaded config entry.
- **Targeted Pytest Iteration Guidelines**: Added the **Targeted Pytest Iteration Rule** to workspace root `AGENTS.md`, enforcing fast, single-file test execution (`pytest tests/test_services.py`) during development to eliminate token and CPU overhead.
- **UniFi-Aligned README Structure**: Overhauled `README.md` layout, section hierarchy, brand banner presentation, entity summary tables, dedicated `## 🧹 Actions (Services)` parameter reference, architecture breakdown, Q&A troubleshooting, and post-deletion retention details to match the UniFi Network Monitor README benchmark.
- **README - Unknown Network Detection deep-dive** (`## 📡 Unknown Network Detection`): a dedicated section consolidating the unknown-detection story - the sensors and Proximity Alert, `Hidden-<last 4 of BSSID>` naming, the `ssid_anomaly` flag, network appearance history, the `wifi_ssid_monitor_new_network` event, the `get_networks` action, and a numbered "How to use it" tuning walkthrough.
- **README - Runtime Controls & Settings (Entities)** subsection under Configuration: lists every control entity (Pause Polling, Scan Interval, Proximity Signal Threshold, Include Hidden, the three band switches, Scan Now) with type and default.
- **README - Under the Hood** additions: a **Self-diagnosis (Integration Health)** subsection documenting the health binary sensor and its `interface_missing` / `signal_format_changed` / `supervisor_unavailable` repair issues, plus an **Actions & Events** subsection; an **Events** reference table in the Actions section; and an **About-attribute TIP** in What You Get documenting the unrecorded `about` notes.
- **README - FAQ Troubleshooting Tips** group with two new entries: **"How do I download diagnostics?"** (explaining the SSID/BSSID pseudonymization and the "logs have no redaction" caveat) and **"I deleted and re-added the integration - why did my settings and history come back?"** (30-day retention table).
- **README - Installation** additions: an **Updating** subsection and the HACS "Open your Home Assistant instance" shortcut badge and release links.

### Changed

- **README - collapsible sections throughout**: wrapped the What You Get entity breakdown, Unknown Network Detection, Under the Hood, Updating, Removal, and every FAQ answer in `<details>` blocks with the standard expand summary, matching the UniFi layout.
- **README - Example Automations restructured**: grouped into Security & Detection / Polling & Scanning / List & History Management, each automation collapsed into its own `<details>`, with entity-ID and notifier preamble notes.
- **README - terminology consistency**: replaced "signal strength" with "signal quality" in the Features section to match the document-wide 0–100% wording; added a storage-clear TIP pointing at the `clear_last_seen` action over hand-editing `.storage`.

### Fixed

- **Option-Change Polling Behavior**: Fixed `_async_update_listener` in `__init__.py` to use an explicit `REFRESH_ON_CHANGE_KEYS` set (`known_wifi_ids`, `denylist_ssids`, `include_hidden`, `proximity_signal_threshold`, `show_24ghz`, `show_5ghz`, `show_6ghz`). Toggling Pause Polling (`stop_polling`) or changing scan intervals no longer forces an immediate fetch, preventing unintended scans when polling is paused.
- **Redundant Control Refreshes**: Removed redundant `async_force_refresh()` calls in `switch.py` and `number.py`, eliminating duplicate back-to-back Supervisor API fetches when changing controls from the UI.
- **Interface Missing Health Repairs**: Connected `last_interface_present` API state directly to `_record_fetch_failure_health` in `coordinator.py`, enabling `check_interface_missing` to detect missing or renamed WiFi interfaces on HTTP 400/404 errors and raise the specific `interface_missing` Repair issue.
- **Service Handler Entry Guarding**: Updated `_resolve_entries` in `services.py` to verify that target entries are in `ConfigEntryState.LOADED` state with active `runtime_data`, raising a clean `HomeAssistantError` instead of a bare `AttributeError`.
- **Import-Time Blocking I/O**: Replaced the import-time synchronous `manifest.json` file read in `const.py` with a static constant `VERSION = "1.7.0-dev1"`, preventing blocking disk I/O during Home Assistant component imports. Added a unit test pinning `VERSION` against `manifest.json`.

---

## [2.0.0-dev3] - 2026-07-22 - 100% Test Coverage; Document Reconciliation

### Added

- **100% Test Suite Coverage**: Achieved 100% test coverage across all 15 source files with 212 unit tests, adding tests for store failure degradation, history overflow pruning, health drift strike lifecycle, repair issue synchronization, signal unit change logging, and event suppression caps.
- **Three-Way Document Reconciliation Prompting**: Updated `sensor_review.md` to v2.5.0 with Category G 3-way document reconciliation (`all_sensors.md` vs `README.md` vs `value_min_max.md`), automated platform entity count comparison tables, and `README.md` write workflows.

### Changed

- **Documentation & Manifest Alignment**: Updated `docs/all_sensors.md` (v1.0.6), `docs/value_min_max.md` (v1.0.4), and `.notes/proj_structure.md` (v1.0.10) to reflect the full 18-entity manifest, 6 service actions, and single-boundary parsing architecture.
- **README - Bus Event documented**: Added a **Bus Events** section documenting the `wifi_ssid_monitor_new_network` event - its per-network, restart-surviving, rate-limited semantics, the full payload table (`entry_id`, `key`, `ssid`, `bssid`, `band`, `channel`, `signal`, `hidden`, `ssid_anomaly`, `mode`, `first_seen`), and a `trigger: event` automation example.
- **README - accuracy fixes**: Corrected the Band Filter feature description to the three Show 2.4/5/6 GHz switches (was the removed `scan_bands` enum); corrected the service count from five to six (adding `get_networks` and the denylist capability); added a **Default** column to the Switch and Number entity tables (Pause Off; Include Hidden and band switches On; Scan Interval 10 min; Proximity Threshold 80%); and fixed a breaking-changes cross-reference that pointed the wrong direction.

---

## [2.0.0-dev2] - 2026-07-22 - BSSID Pattern Matching; Operating Mode Exposed

### Summary

A maintenance and refinement update adding BSSID pattern matching across known and denylist options, exposing network operating mode across sensors and actions, activating the interface missing health check, and fixing legacy option migration and recorder attribute exclusions.

### Added

- **BSSID Pattern Matching**: `known_wifi_ids` and `denylist_ssids` pattern matching now evaluates against both network keys (SSID / hidden label) and BSSID MAC addresses, allowing exact MACs or MAC wildcards (e.g. `AA:BB:CC:*`) in both lists.
- **Operating Mode (`mode`) Attributes**: Exposed network operating mode (`infra`, `adhoc`) in `strongest_unknown_ssid` attributes, `get_networks` action responses, and `wifi_ssid_monitor_new_network` bus event payloads.
- **`first_seen` Timestamp in Bus Events**: `wifi_ssid_monitor_new_network` event payload now carries the network's `first_seen` ISO timestamp.
- **DevContainer Mock Supervisor Enhancements**: Updated `mock_supervisor.py` to support the `/network/info` endpoint for config flow auto-detection testing, with realistic 0–100% signal, MHz frequency, BSSID MACs, hidden APs, and mode test data.

### Fixed

- **Legacy Configuration Migration**: Fixed data-to-options migration in `async_setup_entry` to preserve `CONF_INTERFACE` (`wifi_interface`) when upgrading legacy entries that already have populated options.
- **Recorder Attribute Exclusion**: Fixed `WifiScanSensor._unrecorded_attributes` to inherit from `WifiAboutEntity`, preventing static `about` documentation attributes from being recorded into history database logs.
- **Interface Missing Health Check**: Connected `last_interface_present` API state to `ScanFacts`, enabling `check_interface_missing` in `health.py` to detect interface removal and raise the `interface_missing` Repair issue.

---

## [2.0.0-dev1] - 2026-07-22 - Signal Rescaled to Percent; Health Sensor; Services Renamed

### Breaking

- **`sensor.…_strongest_unknown_rssi` removed**, replaced by `sensor.…_strongest_unknown_signal` (0–100%). The old entity goes unavailable; its LTS is retained. Reusing the key with a new unit would have raised an HA statistics unit-change repair, so a new key was used instead.
- **Proximity threshold rescaled to 0–100%** and moved to the `number.…_proximity_signal_threshold` entity; the `proximity_rssi_threshold` option is migrated (dBm → %) automatically. Higher now means closer.
- **Scan Interval, Include Hidden Networks and the band filter left the Configure dialog** and are now control entities; the `scan_bands` enum is migrated to three **Show 2.4/5/6 GHz** switches.
- **Services renamed and merged:** `add_known_ssid`→`add_ssid`, `remove_known_ssid`→`remove_ssid`, `set_known_ssids`→`set_ssids`, each with a required `target: known|denylist` (and `known_ssids`→`values`). No aliases - update automations.

### Added

- **Payload normalization layer** (`parse.py`) - canonical percent signal, frequency→channel/band, hidden detection, SSID-anomaly flag; the single coercion boundary.
- **Integration Health binary sensor** - a `problem` sensor, always available, that reports an unreachable Supervisor, a changed payload shape/unit, an unresolved band, or all known networks vanishing at once; two repairs (`interface_missing`, `signal_format_changed`).
- **Pause Polling switch** with a force-refresh path so every explicit action still fetches while paused.
- **Individual hidden-network naming** - `Hidden-<last 4 of BSSID>` with collision extension; retires the single `[hidden]` bucket.
- **`get_networks` response action** - filtered, sorted, self-contained; works when the sensors are unavailable or capped.
- **New Networks (24h) sensor**, **`wifi_ssid_monitor_new_network` bus event** (baselined, rate-limited), **6 GHz support**, and denylist management via the `target` argument on the list services.
- **`_unrecorded_attributes`** on the churny map attributes; per-network detail relocated onto Strongest Unknown SSID, capped at 25.

### Fixed

- **Band filter no longer hides every network** - band is derived from `frequency`, and an unknown band passes rather than being dropped.
- **Signal is read as a percentage** - the strongest-unknown sensor and proximity alert previously compared a 0–100 value against a negative dBm threshold, so the alert was permanently on whenever any unknown network was visible.
- **Interface auto-detection works on Raspberry Pi** (accepts `type: wireless`).
- **Diagnostics no longer leak third-party SSIDs** - a structural two-pass sanitizer pseudonymizes SSIDs and BSSIDs, including dictionary keys, while preserving signal/channel/band/counts.
- **Storage writes coalesced** (`async_delay_save` + flush on unload) instead of three disk writes every scan; a hard entry cap bounds history growth.
- **`strongest_unknown_ssid` reads `None Detected`** when nothing is in range, instead of a broken-looking `unknown`.

---

## [1.6.2-dev8] - 2026-07-22 - Bumped Ruff and PHACC

### Changed

- **Emoji Icons**: Updated AGENTS.md to clarify that complex (two character) emoji icons should not be used, to avoid link breakage.

### Bumps

- **Validate Bump**: Bumped PHACC `pytest-homeassistant-custom-component` from 0.13.346 to 0.13.347
- **Validate Bump**: Update `ruff`from 0.15.20 to 0.15.21

## [1.6.2-dev7] - 2026-07-12 - Docs Formats and Spelling

### Changed

- **Docs Formats and Spelling**: Updated document files for formatting and spelling

## [1.6.2-dev6] - 2026-07-12 - Bumped pytest-homeassistant-custom-component from 0.13.345 to 0.13.346

### Bumps

- **Validate Bump**: Bumped pytest-homeassistant-custom-component from 0.13.345 to 0.13.346

## [1.6.2-dev5] - 2026-07-06 - Shared CI Bump v2.0.5 → v2.0.6

### Bumps

- **Shared .github CI Validation**: Bump .github Shared CI Validation via SHA from v2.0.5 to v2.0.6

## [1.6.2-dev4] - 2026-07-05 - PyTest Coverage to 100%

### Changed

- **PyTest Coverage**: Increased PyTest coverage to 100%, addressed 4 uncovered statements.

## [1.6.2-dev3] - 2026-07-05 - mypy Unreachable-Statement Fix

### Summary

- **Mypy Code Quality Fix**: Resolved static type check failure due to an unreachable statement error in the coordinator's defensive None checks.

### Changed

- **Defensive Type Erasure**: Implemented type erasure via `ap_check: Any = access_points` in `coordinator.py` to preserve defensive runtime checks against unexpected null values from API calls while satisfying mypy's static analysis requirements.

---

## [1.6.2-dev2] - 2026-07-05 - `test-before-setup` via `ConfigEntryNotReady`

### Summary

- **IQS test-before-setup Compliance**: Implemented the `test-before-setup` quality scale compliance pattern by raising `ConfigEntryNotReady` in the coordinator during the initial startup refresh. This IQS rule `test-before-setup` had been marked as complete, but the new script, referenced below, highlighted that it was not complete.

### Changed

- **Coordinator Update Failure Handling**: Modified `_async_update_data()` in `coordinator.py` to raise `ConfigEntryNotReady` (imported from `homeassistant.exceptions`) instead of `UpdateFailed` during the first data update (when `self.data is None`), fulfilling the rule requirements statically and dynamically.
  - The normal **3-strike resilience logic** applies, to avoid false flags:
    - During normal operations, if a data fetch fails (due to a temporary Supervisor timeout or network hiccup) and the integration already has existing runtime data (self.data is not None):
      - Failures 1, 2, and 3: The coordinator suppresses raising exceptions. It logs a warning ("Error fetching WiFi data (failure X/3)") and holds onto the last known values, returning them to keep entities functional.
      - Recovery: If the Supervisor API recovers within these 3 attempts, the failure counter is reset to 0 and the integration continues seamlessly.
      - Failure 4: If the outage persists for a 4th consecutive attempt, the coordinator stops holding the last known values, logs an ERROR, creates a persistent repair issue (supervisor_unavailable) in the Home Assistant UI, and raises UpdateFailed, correctly flagging the entities as unavailable.
    - Handling Failures During Initial Startup (Setup)
      - On the first run, the integration has no existing data (self.data is None).
      - In this state, there are no cached values to fall back on, so the 3-strike resilience cannot be applied. The coordinator immediately creates the supervisor_unavailable repair issue and raises ConfigEntryNotReady, indicating that setup cannot complete until the Supervisor API is available.
- **Unit Tests**: Updated `test_coordinator.py` assertions in `test_coordinator_update_data_timeout`, `test_coordinator_update_data_failure`, and `test_coordinator_update_data_api_none` to expect `ConfigEntryNotReady` on startup failures.

---

## [1.6.2-dev1] - 2026-07-05 - Ruff Checks Extended to Match Home Assistant

### Summary

- **Ruff Code Health & Configuration Parity**: Upgraded the project's Ruff checking profile to align with Home Assistant Core (adding Pylint, Tryceratops, Pytest-style, and Bandit rules), resolved extended config path-resolution issues in the devcontainer, and directly refactored all remaining warnings in the component code (achieving 100% clean linter checks).

### Changed

- **Ruff Checks Extended**: As of shared CI Dev-workbench v2.2.1, Ruff checks have been extended to align with Home Assistant. This involves INcluding a wide range of checks and then EXcluding several items because of the wider range.
- **Ruff Configuration Parity**: Adopted the updated root `pyproject.toml` containing `per-file-ignores` for tests, resolving the relative path glob parsing bug in the devcontainer and silencing ~312 false positive `S101` test assert warnings and 47 `PLC0415` test import warnings.
- **Number Entity Exception Handling**: Refactored `number.py` exception logger to use `_LOGGER.exception` without passing the redundant `err` exception object, resolving `TRY401` and rendering the block clean from `BLE001` violations.
- **Documentation**: Updated README.md , re-ordered some sections for logical flow and readability.
- **IQS Validation**: `dev-workbench` script `iqs_static_check.py` added via `tasks.json` now checks for Home Assistant Integration Quality Scale ( IQS ) compliance to 7 basic IQS rules.

### Fixed

- **API raise-within-try (`TRY301`)**: Refactored `get_access_points()` and `get_interfaces()` in `api.py` to handle response checks and exception raises outside of the primary `try-except` block, resolving the raise-within-try alerts.
- **Coordinator updates (`TRY301`)**: Refactored `_async_update_data()` in `coordinator.py` to isolate the `try-except` scope strictly to the API call. Check validations (such as `access_points is None`) are now evaluated outside the block, resolving `TRY301` and allowing the removal of the unused `WifiScanError` import.
- **Mock Supervisor Bind (`S104`)**: Added `# ruff: noqa: S104` to `.devcontainer/mock_supervisor.py` to allow binding the mock service to `0.0.0.0` for local dev container access.

---

## [1.6.1] - 2026-07-04 - Release - Reconfigure Shows All Settings; Polling Toggle

### Summary

- **Mostly Behind the Scenes**: Most of the changes in v1.6.1 are behind-the-scenes or under-the-hood: a lot of improvements in the CI Validation and Testing system; some documentation updates. No new features , but some improvements for more predictable performance.

### Changed

- **Polling Toggle Future Ready**: Turning off "Enable polling for changes" in the entry's system options now reliably stops scheduled polling and will satisfy the upcoming HA requirement (implicit `ContextVar` detection is being removed in HA 2026.8).
- **Minimum Home Assistant Version**: Documented minimum raised to 2024.8.0.

### Fixed

- **Reconfigure Screen Now Shows All Settings**: The ⋮ Reconfigure screen previously offered only Name, Known SSIDs, and Interface, while the gear → Configure screen exposed everything. Reconfigure now shows the full settings set - Scan Interval, Include Hidden Networks, Proximity Alert Threshold, Band Filter, Always-Unknown (denylist), and Last Seen History - so both paths behave identically.

---

## [1.6.1-dev11] - 2026-07-04 - Reconfigure Screen Shows the Full Settings Set

### Changed

- **Reconfigure Shows All Settings**: The ⋮ → **Reconfigure** screen now exposes the same full field set as the gear → **Configure** (options) screen - Scan Interval, Include Hidden Networks, Proximity Alert Threshold, Band Filter, Always-Unknown (denylist), and Last Seen History, in addition to Name, Known SSIDs, and Interface. Previously Reconfigure only offered the three setup essentials, so the two paths gave different results. Both screens are now built from a single shared schema so they can't drift apart. No identity/unique_id behavior changed - entity history is preserved as before. Added `strings.json`/`en.json` labels for the added reconfigure fields and tests asserting the two paths render an identical field set.

## [1.6.1-dev10] - 2026-07-04 - Check-Drift Script Fixed; README Aligned

### Changed

- **Dev-WorkBench**: Updated the Check Drift script to account for the situation where the HA Core version online is ahead of the local version (dev-workbench v2.1.0-dev9).
- **Documentation**: Updated the README file to better align to the style and structure of the ZTE and Huawei README files, while maintaining the project unique content.

## [1.6.1-dev9] - 2026-07-03 - Ruff Bump 0.15.19 → 0.15.20

### Bumps

- **Validate Bump**: Update Ruff from 0.15.19 to 0.15.20

## [1.6.1-dev8] - 2026-07-02 - Explicit `config_entry` on the Coordinator

### Summary

- **Explicit `config_entry` on the Coordinator**: Pass the config entry explicitly to `DataUpdateCoordinator` so Home Assistant reliably honours the "Enable polling for changes" system option and to satisfy the upcoming HA requirement (implicit `ContextVar` detection is being removed in HA 2026.8).

### Changed

- **Coordinator `config_entry`**: `WifiScanCoordinator` now passes `config_entry=entry` to `super().__init__()`. This makes `self.config_entry` explicit, which is what HA core's `_schedule_refresh()` checks (`config_entry.pref_disable_polling`) to stop scheduled polling when the user sets **System options → "Enable polling for changes" = OFF**. Manual updates (`homeassistant.update_entity`, the "Scan Now" button) still fetch. No behavior change on current HA - it removes reliance on implicit context detection, which HA logs as an error from **2026.8**.
- **Minimum HA Version**: Documented minimum raised to **2024.8.0** (the release that added the `config_entry` argument to `DataUpdateCoordinator`).
- **.gitignore**: Added scratch folders

### Tests

- Added a coordinator test asserting `coordinator.config_entry is entry`.

### Bumps

- **Shared .github CI Validation**: Bump .github Shared CI Validation via SHA from v2.0.4 to v2.0.5 (PR #33)
- **Validate Bump**: Updated `ruff` from 0.15.17 to 0.15.19 (PR #34)
- **Validate Bump**: Bumped `pytest-homeassistant-custom-component` from 0.13.340 to 0.13.344
- **Validate Bump**: Bumped `check-jsonschema` from 0.37.2 to 0.37.4

## [1.6.1-dev7] - 2026-06-27 - README Screenshots; YAML Lint Aligned

### Summary

- **Docs and Validation**: Screenshot updates for the README file plus file changes based on YAML List rule change (no "---" needed at top of YAML files).

### Changed

- **Screenshots**: Updated the four screenshots used in the README file to (a) higher resolution and (b) current version. In particular the sensors image now shows all 10 entities versus the 6 shown previously and the setup image is significantly larger, reflecting a lot of set-up based options added in recent versions (scan interval, include hidden, threshold, band filter, deny list, keep days).
- **Docs**: Updated README with a note to clarify that performance depends heavily on the location of the Home Assistant hardware within your home.
- **YAML Lint**: Added "document-start: disable" to .yamllint rule file, to stop warns/fails for "no --- at document start", which brings it in line with Home Assistant.
- **YAML Files**: Updated YAML files to remove any "---" document starts added.
- **Tasks.json**: Updated tasks.json, via hosts-tooling so that YAML-Lint only runs on git tracked files.

## [1.6.1-dev6] - 2026-06-26 - Shared CI, Ruff and PHACC Bumps

### Summary

- **Validation Bumps**: Bumped Shared CI, Ruff, PyTest

### Changed

- **Dependabot Bump**: Updated shared CI Validation call (.github) from v2.0.3 to v2.0.4
- **Dependabot Bump**: Updated ruff from 0.15.16 to 0.15.17
- **Bump**: Updated PyTest Custom from 0.13.326 to 0.13.340
- **Agents.md**: Updated to include reference to run in devcon skills

## [1.6.1-dev5] - 2026-06-18 - CI Validation Overhaul

### Summary

- **CI Validation Overhaul**: Major overhaul of the local (tasks.json) and online (github.com CI) Validation system

### Changed

- **dev-workbench**: Moved CI Validation and Sync to dev-workbench system, with major restructure of files and folders.
- **CI Local Tasks**: Reordered local tasks.json, added color for pass/fail.
- **CI Validation Bump**: Shared CI validation bumped to v2.0.3. No user changes in this release, background/infrastructure only.
- **CI Validation Bump**: Shared CI validation bumped from v2.0.1 to v2.0.2
- **CI Coverage Report**: Removed the pytest coverage report as it required extra permissions and is separate to the coverage badge, which is what is really required.
- **CodeQL**: CodeQL shared config and local caller modified to detail permissions to that Zizmor will pass
- **CodeQL**: Added a shared CodeQL validation config to the shared validation repo, pulled into each project, incl this one.
- **Validation Config**: Fixed use of .prettierrc.json
- **Link Check**: Updated markdown-link-check to ignore .notes/ and .shared/ links in projects as these are excluded.
- **Validation Config**: Changed from .prettierrc.js to .prettierrc.json to allow GitHub.com CodeQL to run without errors
- **DependaBot**: Bumped Ruff from 0.15.12 to 0.15.16
- **.gitignore**: Multiple updates to .gitignore
- **AGENTS.md**: Added AGENTS.md to repo root

## [1.6.0] - 2026-06-12 - Proximity Alert, Persistent History and Denylist

### Summary

Version 1.6.0 is a major feature release focusing on security monitoring, scanning control, and robust history tracking. Key highlights include a **Proximity Alert** sensor and threshold controls to detect nearby unknown networks, dedicated sensors for the **Strongest Unknown SSID & RSSI**, and **Persistent History** (surviving restarts, tracking first-seen and visit counts). Scanning can now be filtered by **frequency band** and **hidden networks**, and an **SSID Denylist** is introduced to force specific networks to remain permanently flagged. Five new service actions and a **Scan Now** dashboard button enable dynamic whitelisting and on-demand polling. Finally, known network matching is upgraded to support **wildcard patterns** (e.g., `Guest_*`).

### Added

- **Proximity Alert Binary Sensor**: New binary sensor that fires when the strongest unknown network's signal strength meets or exceeds a configurable threshold (default −60 dBm).
- **Scan Now Button**: New button entity for triggering an immediate WiFi scan from the HA dashboard without waiting for the next scheduled interval.
- **Strongest Unknown SSID Sensor**: New sensor showing the SSID name of the unknown network with the strongest signal.
- **Strongest Unknown RSSI Sensor**: New sensor showing the signal strength (dBm) of the closest unknown network, with native long-term statistics support.
- **Persistent History**: Unknown SSID last-seen timestamps now survive HA restarts. Each SSID also records a first-seen timestamp and a visit count (number of scan cycles the SSID was detected).
- **History TTL**: New option to automatically expire stale history entries after a configurable number of days (default 90; set to 0 to keep forever).
- **Band Filter**: New option to restrict scanning to 2.4 GHz or 5 GHz networks only. APs with an undetermined band are excluded when a filter is active.
- **SSID Denylist**: New option accepting comma-separated `fnmatch` patterns. Matching SSIDs are always treated as unknown, regardless of the known list.
- **Include Hidden Networks Toggle**: New option to exclude hidden (non-broadcasting) APs from all counts and attributes (default: include).
- **Proximity Alert Threshold**: New option controlling the RSSI level at which the Proximity Alert sensor fires (range −100 to −30 dBm, default −60 dBm).
- **`add_known_ssid` Service**: Add an SSID or pattern to the known list with an immediate re-scan.
- **`remove_known_ssid` Service**: Remove a single SSID or pattern from the known list. Silent success if not present; triggers a re-scan when the list changes.
- **`scan_now` Service**: Trigger an immediate scan for one or all configured entries.
- **`clear_last_seen` Service**: Clear all persistent history (last seen, first seen, and visit counts) for one or all entries.
- **`set_known_ssids` Service**: Replace the entire known SSID list in a single call. Returns the previous list per entry as service response data.
- **Repair Issues**: HA now creates a repair issue after 4 consecutive scan failures and clears it automatically on recovery.

### Changed

- **Known SSID Matching**: Now uses `fnmatch` wildcard patterns (e.g., `Guest_*`, `IoT_?`) in addition to exact string matching. Existing lists work unchanged.
- **Signal Strength and Band Attributes**: `signal_strengths` (RSSI per SSID) and `bands` (frequency band per SSID) are now exposed as attributes on both count sensors.
- **Options Dialog**: Added contextual hints to all configuration and options flow fields.
- **Error Messages**: Integration errors (e.g., invalid service parameters, failed scans) now display translated messages in the HA UI.

### Fixed

- **Scan Button Error Reporting**: The scan button now correctly propagates scan failure to automations (previously always reported success).
- **`add_known_ssid` Silent No-Op**: Supplying an invalid `config_entry_id` now raises a UI-visible error instead of silently doing nothing.

---

## [1.6.0-dev7] - 2026-06-11 - Documentation Refresh

### Changed

- **Documentation**: All relevant documents, README.md, FUTURE.md, DEVELOPMENT.md etc. updated.

## [1.6.0-dev6] - 2026-06-11 - `__init__.py` Coverage to 100%

### Changed

- **Test Coverage**: `__init__.py` coverage increased from 88% to 100% (overall 96% → 100%) with new tests for `scan_now`, `clear_last_seen`, and `set_known_ssids` service paths.

### Fixed

- **`test_coordinator_async_initialize_with_corrupt_data`**: Updated test to use store mock exception instead of invalid date string, which no longer exercises the error path under the new `asyncio.gather(return_exceptions=True)` loading pattern.

---

## [1.6.0-dev4] - 2026-06-11 - First Seen and Visit Count Stores; Three Services Added

### Added

- **"First Seen" Persistent Timestamps**: `_first_seen` dict backed by a dedicated `Store` (`.storage/wifi_ssid_monitor.<entry_id>.first_seen`). Written once per SSID on first detection - never overwritten. Exposed as `first_seen` ISO-timestamp dict attribute on `unknown_count`. TTL expiry prunes `first_seen` entries simultaneously with `last_seen` and `visit_counts`.
- **Unknown SSID Visit Count**: `_visit_counts` dict backed by a dedicated `Store` (`.storage/wifi_ssid_monitor.<entry_id>.visit_counts`). Incremented each scan cycle the SSID is present. Exposed as `visit_counts` int dict attribute on `unknown_count`.
- **Dedicated Strongest Unknown RSSI Sensor** (`sensor.strongest_unknown_rssi`): `SensorDeviceClass.SIGNAL_STRENGTH`, `native_unit_of_measurement="dBm"`, guard band −100–0 dBm. Allows native HA history graphing and numeric automation conditions without attribute extraction.
- **`scan_now` Service** (`wifi_ssid_monitor.scan_now`): Triggers `coordinator.async_refresh()` for one or all entries. Optional `config_entry_id` field. Registered in `async_setup` alongside other domain services.
- **`clear_last_seen` Service** (`wifi_ssid_monitor.clear_last_seen`): Silently clears `_last_seen`, `_first_seen`, and `_visit_counts` and saves empty state to all three Stores. The next scheduled scan repopulates from scratch. No re-scan triggered. Optional `config_entry_id` field.
- **`set_known_ssids` Service** (`wifi_ssid_monitor.set_known_ssids`): Replaces the entire known networks list in a single call. Returns the previous list per entry as service response data (`SupportsResponse.OPTIONAL`). Triggers an immediate re-scan. Optional `config_entry_id` field.
- **`_resolve_entries()` Helper**: Internal helper in `__init__.py` deduplicates entry-resolution logic across all multi-entry service handlers. Raises `HomeAssistantError` (with `translation_key="entry_not_found"`) when a supplied `config_entry_id` matches no loaded entry.
- **`async_remove_entry` Hook**: Removes all three Stores when an integration entry is deleted, preventing orphaned `.storage` files.

### Changed

- **`coordinator.py` - Three Stores**: `async_initialize()` now loads all three Stores in parallel via `asyncio.gather(return_exceptions=True)` with independent error handling per Store. All three are saved in parallel via `asyncio.gather()` after each scan cycle. TTL expiry prunes `last_seen`, `first_seen`, and `visit_counts` simultaneously using a shared `expired` set.

### Fixed

- **mypy strict errors** in `coordinator.py:async_initialize`: Changed `isinstance(x, Exception)` to `isinstance(x, BaseException)` for Store load results from `asyncio.gather(return_exceptions=True)`. mypy infers the exception union as `T | BaseException` (not `T | Exception`), so only `BaseException` correctly narrows the union in the `elif` data branches.
- **HASSFest `services.yaml` validation errors**: Removed unsupported `response` and `target` keys from the `set_known_ssids` service definition. The HASSFest schema version used by this project does not accept these keys. `SupportsResponse.OPTIONAL` in the Python handler controls runtime response behavior; the services.yaml entry is UI documentation only.

---

## [1.6.0-dev1] - 2026-06-11 - Persistent Last Seen; Band Filter and Denylist

### Added

- **`remove_known_ssid` Service** (`wifi_ssid_monitor.remove_known_ssid`): Removes an exact SSID or `fnmatch` pattern from the known list. Silent success if the SSID is not present. Triggers an immediate re-scan when the list changes. Optional `config_entry_id` field.
- **Strongest Unknown SSID Name Sensor** (`sensor.strongest_unknown_ssid`): State is the SSID name of the unknown network with the strongest signal. State is `unknown` when no unknown networks are visible.
- **Persistent "Last Seen" Storage**: `_last_seen` dict is now backed by HA's `Store` (`.storage/wifi_ssid_monitor.<entry_id>.last_seen`). Timestamps survive HA restarts. `async_initialize()` (called from `async_setup_entry` before the first background scan) loads persisted data. Store is removed via `async_remove_entry` when the entry is deleted.
- **Auto-Expire Stale "Last Seen" Entries** (`last_seen_ttl_days`): Configurable TTL in the options flow (range 0–366 days; 0 = keep forever; default 90 days). Applied on each successful scan immediately before saving to the Store. Entries not seen within the TTL window are pruned.
- **Band Filter Option** (`scan_bands`): Options flow dropdown (`all` / `2.4` / `5`). Filters all scan results - network counts, sensor attributes, and known-network matching - not just band display. APs with an undetermined band are excluded (strict exclusion) when any filter other than `all` is active.
- **SSID Denylist** (`denylist_ssids`): Options flow field accepting comma-separated `fnmatch` patterns. SSIDs matching any denylist pattern are always counted as unknown regardless of the known list. Denylist takes priority over the known list for SSIDs that match both.

### Changed

- **`coordinator.py` - `async_initialize()`**: New explicit method replaces the abandoned `_async_setup()` hook (which is never invoked when the integration uses `coordinator.async_refresh()` rather than `async_config_entry_first_refresh()`). Called directly from `async_setup_entry` before the first background refresh.
- **Options flow**: Added `scan_bands`, `denylist_ssids`, and `last_seen_ttl_days` fields to `WifiScanOptionsFlowHandler.async_step_init`. `strings.json` and `translations/en.json` updated with descriptions and warnings for each new field.

---

## [1.5.0-dev6] - 2026-06-11 - Validation Tooling Sync System

### Changed

- **Validation Sync**: Moved to a better system and process to keep validation (lint/format/test) tools in sync, across PlayFaster projects and between the projects and what Home Assistant uses.
  - .validate/version_matrix.json added as the definitive source of tool version use.
  - Several Env: entries added to .vscode/tasks.json for tool sync and checking.
  - .validate/requirements_test.txt pulled as generic, with all tools pinned to versions, and requirements_custom.txt used to add project specific items.
  - As part of the sync, docker-compose.yml and devcontainer.json are now generic, with a .env file holding project specific info and a docker-compose.override.yml holding additional, project specific steps.
  - HA Manifest and HACS schema files updated.
  - Ruff updated from 0.15.12 to 0.15.15

## [1.5.0-dev5] - 2026-06-07 - README Emoji Consistency; mypy Realigned With HA

### Changed

- **README Emoji Consistency**: Replaced all VS16 compound emoji in headings and ToC links with always-color single-codepoint alternatives (`⚙️`→`🔧`, `🗑️`→`❌`, `⚠️`→`❗`, `⏱️`→`🔁`, `✉️`→`💬`, `⏯️`→`🔁`, `🛠️`→`🔩`, `🎛️`→`🔘`); moved License badge out of heading; standardized Use Cases icon to `🎯`.

- **`pyproject.toml` - mypy Configuration Realigned with HA's Internal `mypy.ini`**: The project's `[tool.mypy]` section has been restructured to closely match HA's auto-generated `mypy.ini` (produced by `script/hassfest -p mypy_config`). This ensures the pre-commit mypy hook, and the project's basic `mypy custom_components/` check, run under materially the same conditions as HA's own integration quality checks. The goal is for any type errors caught here to be errors HA itself would also catch - and vice versa.

## [1.5.0-dev4] - 2026-06-03 - Service Registration Moved to `async_setup`; Exception Translations

### Changed

- **`action-setup` fix**: `add_known_ssid` service registration moved from `async_setup_entry` (with `has_service` guard) to `async_setup`. Service is now domain-lifecycle-managed - active for the domain's loaded state, no per-entry guard or cleanup needed. `async_unload_entry` simplified accordingly (service cleanup logic removed).
- **Config flow dead code removal**: Removed two unreachable `else: cv.string` branches from `async_step_reconfigure` and `WifiScanOptionsFlowHandler.async_step_init` in `config_flow.py`. The `current_interface` fallback guard that runs immediately before the conditional guarantees `available_interfaces` is always non-empty, making the `else` branches dead code. `config_flow.py` coverage is now 100%.
- **Exception translations**: `HomeAssistantError` raises in `button.py` (`async_press`) and `__init__.py` (service handler) now include `translation_domain`, `translation_key`, and `translation_placeholders` for UI-translatable error messages. `exceptions` section added to `strings.json` and `translations/en.json` (`scan_failed`, `entry_not_found` keys).

---

## [1.5.0-dev3] - 2026-06-03 - Scan Button Error Propagation; Service Lifecycle Cleanup

### Fixed

- **`button.async_press` error propagation**: `async_press` now checks `coordinator.last_update_success` after calling `async_refresh()` and raises `HomeAssistantError` when False. Previously the button always reported success to the caller, making it impossible for automations to detect a failed scan. The fix correctly uses `last_update_success` rather than the return value of `async_refresh()` (which always returns `None`, not a bool - the proposed fix in the code review document was incorrect on this point; see `.notes/code_review/code_review_20260602.md`).
- **`add_known_ssid` service silent no-op on bad `config_entry_id`**: Service handler now raises `HomeAssistantError(f"No {DOMAIN} entry found with ID '{target_entry_id}'")` when a `config_entry_id` is provided but does not match any loaded entry. Previously a mistyped or stale entry ID silently did nothing.
- **`async_unload_entry` service lifecycle cleanup**: `async_unload_entry` now removes the `add_known_ssid` domain service when the last config entry is unloaded. The remaining-entries check explicitly filters out the entry currently being unloaded (which is still present in `async_entries(DOMAIN)` during the unload call) - the proposed fix in the code review document contained a bug that would have prevented removal; see `.notes/code_review/code_review_20260602.md`.

### Changed

- **Supervisor URL constant**: Extracted `_SUPERVISOR_BASE_URL = "http://supervisor"` as a named module-level constant in `api.py`. Both endpoint URL constructions now use this constant. No behavioral change.

---

## [1.5.0-dev2] - 2026-06-02 - Level 1 Deeper Testing: 22 New Tests

### Added

- **Level 1 Deeper Testing**: Implemented all 14 findings from recommendations_20260602.md - 22 new tests across 5 files. Coverage: BVA boundary-value tests for `_channel_to_band`, `WifiProximityBinarySensor.is_on`, and sensor guard bands; combinatorial tests for `include_hidden`, `fnmatch` wildcard matching, and proximity sensor unit tests; error-path tests for `ValueError` in JSON decode (`get_access_points` and `get_interfaces`); assertion gap tests for `proximity_alert` check, `signal_strengths`/`bands` attributes, `networks`/`last_seen`/`strongest_unknown_rssi` return validation, hidden network band/strongest_rssi assertions, and `add_known_ssid` runtime deduplication.

### Changed

- **Coverage**: `__init__.py` coverage increased from 76% to 100% (overall 95% → 98%) with 4 new tests for data-to-options migration and `add_known_ssid` service paths.
- **Docstrings**: Fixed 18 D103 missing-docstring violations across `test_coordinator.py`, `test_binary_sensor.py`, `test_api.py`, and `test_init.py`.

---

## [1.5.0-dev1] - 2026-06-02 - Scan Now Button, Proximity Alert and Pattern Matching

### Added

- **Manual Scan Button**: New `button` platform with a `scan_now` entity. Pressing it calls `coordinator.async_refresh()` for an immediate on-demand scan without waiting for the next scheduled interval.
- **Proximity Alert Binary Sensor**: New `binary_sensor.proximity_alert` entity - fires when the strongest unknown SSID signal meets or exceeds a configurable RSSI threshold (default −60 dBm). Exposes `strongest_unknown_rssi` and `threshold` as state attributes.
- **`add_known_ssid` Service**: New `wifi_ssid_monitor.add_known_ssid` HA service. Appends an SSID to the known list and triggers an immediate re-scan via the existing update listener. Accepts optional `config_entry_id` to target a specific entry; if omitted, updates all entries. Documented in `services.yaml`.
- **Include Hidden Networks Toggle** (`CONF_INCLUDE_HIDDEN`): New boolean option in the options flow (default: `True`). When disabled, APs without a broadcasted SSID are filtered out entirely before processing - they no longer appear in counts or attributes.
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

## [1.4.4-dev3] - 2026-06-02 - README Aligned With ZTE; mypy Strict Errors Fixed

### Changed

- **Entity Category Imports**: Standardized `EntityCategory` imports to use `homeassistant.const` instead of `homeassistant.helpers.entity` in sensor and number platforms.
- **README Alignment**: Aligned the `README.md` layout and structure with the premium ZTE project template (adding compatibility grid, config parameter tables, and side-by-side screenshots).
- **Automation YAML Formatting**: Rewrote example automations to use standard block scalar `|` formatting and updated legacy time platform triggers to `trigger: time` syntax.

### Fixed

- **Mypy Strict Errors**: Resolved all 10 type errors logged in strict mode (correcting exception tuple syntax, wrapping forward type references in quotes in config flow, and removing unused type ignore comments).
- **Incorrect Entity IDs in Docs**: Updated all sensor entity ID references in `README.md` from `total_count` and `unknown_count` to `total_ssid_count` and `unknown_ssid_count` to match runtime IDs.

---

## [1.4.4-dev2] - 2026-05-13 - Full IQS Review; runtime-data and Repair Issues

### Added

- Full IQS Review carried out , all open items implemented. IQS compliance is currently taken as far as it can go in this project.

### Changed

- **runtime-data** (IQS Bronze): Migrated coordinator storage from `hass.data[DOMAIN]` to `entry.runtime_data` in `__init__.py`, `sensor.py`, `binary_sensor.py`, `number.py`, `diagnostics.py`; `async_unload_entry` simplified - HA handles `runtime_data` cleanup automatically, no manual teardown needed.
- **parallel-updates** (IQS Silver): Added `PARALLEL_UPDATES = 0` to `sensor.py`, `binary_sensor.py`, `number.py`, signaling to HA that the coordinator handles all update coordination.
- **config-flow** (IQS Bronze): Added `data_description` contextual hints to all config and options flow steps in `strings.json` and `translations/en.json`.
- **docs-data-update** (IQS Gold): Added Data Updates section to `README.md` documenting polling endpoint, interval, 3-strike resilience, and immediate-refresh behavior.
- **repair-issues** (IQS Gold): Implemented `ir.async_create_issue` / `ir.async_delete_issue` in `coordinator.py`; added `supervisor_unavailable` repair issue strings to `strings.json` and `translations/en.json`. Issue is raised on 4th consecutive failure and cleared on next successful scan.
- **quality_scale.yaml**: Rewrote to canonical 52-rule format; all 47 trackable rules now `done`.

### Fixed

- **Tests**: Updated `test_sensor.py`, `test_binary_sensor.py`, `test_number.py` to use `mock_config_entry.runtime_data = mock_coordinator` instead of `patch.dict(hass.data, {DOMAIN: ...})` injection - aligns test setup with runtime-data migration.

## [1.4.4-dev1] - 2026-05-13 - `icons.json` Adopted; mypy Strict Clean

### Changed

- **icons.json**: Implemented icons.json standard, where all icons are defined in an icons.json file, not individual .py files.
- **mypy --strict**: Addressed all mypy type issues.

## [1.4.3] - 2026-05-10 - README Overhaul and Internal Alignment

### Changed

- **Readme**: Overhaul of the readme file, additional example automations, re-ordered for readability.
- **Under the Hood**: Several internal code changes to improve maintainability and alignment with Home Assistant development standards (no functional breaking changes).
- **Validations**: Improved local and automated remote testing to ensure code remains secure and follows best practices.

## [1.4.3-rc1] - 2026-05-10 - README Expanded; Project-Agnostic `pyproject` and `tasks`

### Changed

- **Readme**: Updated Readme with additional information. Re-ordered some sections. Added more emoji icons to headings.
- **pyproject.toml**: pyproject.toml is now fully project agnostic. It does not contain the name of the specific project, instead just references the general custom_components folder for pytest coverage.
- **tasks.json**: tasks.json is also not fully project agnostic. It does require a settings.json file, but this now only requires one change per project.

## [1.4.3-dev20] - 2026-05-09 - Shared Reusable CI Workflow Created

### Dev Tooling

- **Shared Reusable CI Workflow**: Created `PlayFaster/.github` organization repo containing a parameterized reusable workflow (`validate.yaml`, named "Validate (Shared)"). All 8 validation jobs (`hassfest`, `hacs_val`, `py_val`, `test_val`, `file_val`, `codespell`, `zizmor`, `mypy_val`) now live in the shared repo and are called by each integration via a thin caller. Changes to validation logic propagate to all 4 projects on the next CI run without per-project edits.
- **Thin Caller Workflow**: Replaced the 270-line inline `.github/workflows/validate.yaml` with a ~30-line caller that delegates to the shared workflow via `uses: PlayFaster/.github/.github/workflows/validate.yaml@main`. Permissions correctly scoped: `contents: read` at workflow level, `contents: write` and `pull-requests: write` at job level (required by `test_val` for coverage badge and PR comments).
- **Shared Workflow Concurrency**: Reusable workflow uses `${{ github.workflow }}-${{ github.ref }}-${{ github.repository }}` as its concurrency group, preventing cross-repo cancellation when multiple integrations trigger simultaneously.
- **Shared Workflow Dependabot**: Added `dependabot.yml` to `PlayFaster/.github` tracking the `github-actions` ecosystem weekly, keeping SHA pins in the shared workflow current.
- **Pre-commit: Suppress Inapplicable Hooks**: Added `stages: [manual]` to the `no-commit-to-branch` hook - direct commits to `main`/`dev` are the working pattern for this project, so the hook is retained for explicit use but removed from the default commit flow. Added `exclude: \.yamllint$` to the `yamllint` hook to prevent it from linting its own config file (which lacks `---` and uses CRLF).
- **VS Code Tasks**: Added `Zizmor: Fix (Safe Auto-Fix)` task (`zizmor --fix .github/`) for applying zizmor's safe auto-fixes on demand. Added `Pre-commit: Autoupdate Hooks` task (`pre-commit autoupdate`) for updating all hook `rev:` pins to their latest releases. Neither task is wired into `Fix All` or `Validate All`.

## [1.4.3-dev11] - 2026-05-09 - mypy Type Annotations Added

### Changed

- **mypy errors**: Addressed all type issues flagged by mypy tool (in HA mode, not --strict mode). Added type annotations to all functions, params, and return types.

## [1.4.3-dev4] - 2026-05-06 - `quality_scale.yaml` Added; Sensor Coverage

### Added

- **Quality Scale**: Added quality_scale.yaml into project folder to track compliance to Home Assistant Integration Quality Scale (IQS). As a custom component full compliance is not possible but this is a good mechanism to ensure alignment with Home Assistant best practice.

### Changed

- **Coverage**: Test coverage improvements to sensor.py.

## [1.4.3-dev3] - 2026-05-06 - Diagnostics, Reauth and Reconfigure Flows

### Added

- **Diagnostics**: Implemented a diagnostics platform (`diagnostics.py`) to provide sanitized integration state for troubleshooting.
- **Reauthentication**: Added a re-authentication flow to handle invalid or expired Supervisor API tokens.
- **Reconfiguration**: Added a reconfiguration flow allowing users to update the interface and settings without re-installing.

### Changed

- **Translations**: Updated localized strings for reauth and reconfigure flows; verified entity translation keys.
- **Quality Standards**: Updated IQS compliance matrix in `ha_quality_standard.md` to reflect Silver/Gold progress.

### Fixed

- **Integration Stability**: Verified clean startup and error-free operation of the diagnostics component.

## [1.4.3-dev2] - 2026-05-06 - Entity Manifest and Guard-Band Docs; `api.py` to 100%

### Added

- **Documentation**: Created `docs/all_sensors.md` (Entity Manifest) and `docs/value_min_max.md` (Guard Bands) to provide clear reference for users and developers.

### Changed

- **Test Coverage**: Achieved 100% unit test coverage for `api.py` by adding exhaustive tests for error paths, including JSON decoding failures and connection issues.
- **Test Infrastructure**: Enhanced `MockResponse` in `conftest.py` to support simulated JSON content-type errors.

### Fixed

- **API Robustness**: Verified and fixed handling of malformed JSON responses in `api.py` (discovered during coverage testing).

## [1.4.3-dev1] - 2026-05-02 - README Badge Links

### Changed

- **Badge Links**: Added links to readme badges.

## [1.4.2] - 2026-05-02 - Scan Interval Minimum Aligned to 60 Seconds

### Fixed

- **Scan Interval Minimum**: Aligned the minimum scan interval to 60 seconds across both the Options dialog and the number entity slider. Previously the options dialog accepted 30 seconds, which would silently round to 1 minute in the slider UI.

### Changed

- **Options Dialog**: Scan interval field label updated to "Scan Interval (seconds, minimum 60)" to clarify the expected unit and enforced minimum.

### Documentation

- **Known Limitations**: Added a Known Limitations section to the README documenting that multiple hidden (non-broadcasting) WiFi networks are reported as a single `[hidden]` entry in SSID counts. This is expected behavior - hidden networks cannot be individually identified without SSID data.

## [1.4.2-dev3] - 2026-05-01 - Code-Review Fixes; Binary Sensor and Resilience Tests

### Fixed

- **Readme**: Typo in Readme.
- **Scan Interval Minimum Mismatch** (B2): Aligned minimum scan interval to 60 seconds in `config_flow.py` - changed `vol.Range(min=30)` to `vol.Range(min=60)`. The number entity already enforced 60s (1 min); the options flow now matches, preventing silent round-up of 30–59s values.
- **Scan Interval Label** (D2): Updated `strings.json` and `translations/en.json` scan interval label from `"Scan Interval (seconds)"` to `"Scan Interval (seconds, minimum 60)"` to reflect the enforced minimum and clarify units.

### Changed

- **Exception Syntax** (B1): `except KeyError, AttributeError:` → `except (KeyError, AttributeError):` in `sensor.py:118` - idiomatic Python 3 tuple-style; no runtime change.
- **Exception Handling** (Q1): Removed redundant `TimeoutError` and `WifiScanError` from `except (TimeoutError, WifiScanError, Exception)` in `coordinator.py` - `Exception` already subsumes both, keeping the catch and removing the noise.
- **Task Management** (Q2): Replaced `asyncio.create_task()` with `self.hass.async_create_task()` in `number.py` for proper HA lifecycle management. With `asyncio.create_task`, debounce tasks were not tracked by HA and could run against stale entities after removal.
- **Translation Key** (Q3): Changed `name="Last Updated"` to `translation_key="last_updated"` in `sensor.py` `SENSOR_TYPES` - consistent with all other sensor descriptions; translation already existed in `strings.json`.
- **Type Hints** (B/Q4): Added full type annotations to `async_setup_entry` and `WifiScanBinarySensor.__init__` in `binary_sensor.py`. Added `CoordinatorEntity[WifiScanCoordinator]` type parameter to the class.
- **Config Entry Data** (Q5 / A2): Changed `data=user_input` to `data={}` in `config_flow.py` `async_step_user`. All configuration lives in `options`; `data` is reserved for immutable/auth values per HA best practice. Resolves the stale `data` dict that persisted on all new installs.
- **VERSION Constant** (Q6): Added `VERSION` constant to `const.py`, read from `manifest.json` at module import time via `json.loads`. Removed `async_get_integration(hass, DOMAIN)` call from `async_setup_entry` in `__init__.py` - it was called solely to read the version string, adding an unnecessary async I/O step on every setup.

### Added

- **Binary Sensor Tests** (T1): Created `tests/test_binary_sensor.py` with 6 tests: platform setup and initial state, `is_on` with unknown networks, `is_on` with all-known, `is_on` with no data, `device_info` structure, and unique ID format.
- **Coordinator Resilience Tests** (T3): Added `test_coordinator_resilience_holds_for_three_failures` and `test_coordinator_resilience_resets_on_success` to `tests/test_coordinator.py`, covering the 3-failure stale-hold behavior and failure count reset on success.

### Changed — tests

- **Test Fixture** (T4): Updated `conftest.py` `mock_config_entry`: title changed to `"WiFi SSID Monitor"`, `CONF_NAME: "WiFi SSID Monitor"` added to options, `data` set to `{}` - aligns fixture with post-Q5 config flow behavior and v1.4.0 clean naming.
- **Sensor Test Entity IDs** (T4): Updated entity ID assertions in `tests/test_sensor.py` from `sensor.wifi_ssid_monitor_wlan0_*` to `sensor.wifi_ssid_monitor_*` to match v1.4.0 single-instance clean naming.
- **Config Flow Test**: Updated `test_user_flow` in `tests/test_config_flow.py` - `result["data"]` assertion changed from `{user_input contents}` to `{}` to reflect Q5 fix.
- **Number Debounce Test**: Replaced `task1.cancelling() > 0 or task1.cancelled()` state check in `test_number_debounce_cancellation` with `task1 is not task2` - the old check broke when `hass.async_create_task` with eager start ran the mocked-sleep task to completion immediately.
- **Setup Failure Test**: Updated `test_setup_entry_failure` in `tests/test_init.py` to mock `WifiScanCoordinator` instead of the now-removed `async_get_integration`.

### Removed

- **Placeholder Test File** (T2): Deleted empty `tests/test_temp.py`.

### Documentation

- **DEVELOPMENT.md** (D1): Updated "Retry Resilience" bullet to accurately describe the 3-failure hold strategy, replacing stale reference to a "two-stage fetch attempt with a 10-second delay" (that logic no longer exists).
- **DEVELOPMENT.md** (A1): Added pitfall note on hidden network deduplication - multiple hidden APs collapse to a single `[hidden]` entry in `all_ssids` (set de-dup) and `network_map` (last-write-wins). Count will differ from tools like `nmcli` that report per-AP.
- **README.md** (A1): Added "Known Limitations" section documenting the hidden network grouping behavior for end users.

### Dev Tooling

- **VS Code Tasks**: Updated "Pytest: Run All Tests" and "Pytest: Check Test Coverage" tasks to strip ANSI escape codes from `.reports/pytest_results.txt` and `.reports/pytest_coverage.txt` while preserving color in the terminal. Uses bash process substitution: `tee >(sed 's/\x1b\[[0-9;]*[a-zA-Z]//g' > file.txt)`. Same fix applied to `ha-tplink-router-5g-monitor` and `ha-zte-router-5g-monitor`.

## [1.4.1] - 2026-04-18 - Last Updated Sensor; Custom Naming; Guard Bands

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

## [1.4.0] - 2026-04-05 - WiFi Interface Auto-Discovery

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

## [1.3.1] - 2026-04-02 - Structured Network Data Model

### Changed

- **Architecture**: Refactored the internal data model to use a structured mapping for networks. This change is non-breaking but provides the necessary foundation for future features like per-network signal strength (RSSI) and channel tracking without requiring further structural rewrites.

## [1.3.0] - 2026-04-02 - Renamed to WiFi SSID Monitor

### Changed

- **Project Rename**: Formally renamed the integration from "WiFi Scan SSID" to **WiFi SSID Monitor** to better distinguish it from device tracking integrations and highlight its monitoring purpose.
- **Domain Update**: Changed the internal domain from `wifi_scan_ssid` to `wifi_ssid_monitor` for full architectural consistency.
- **Folder Structure**: Migrated all components to the `wifi_ssid_monitor` directory.

## [1.2.0] - 2026-04-02 - Scan Interval Slider

### Added

- **Scan Interval Slider**: Implemented a new `number` entity allowing users to adjust the scan frequency (1-180 minutes) directly from the Home Assistant GUI.
- **Enhanced Diagnostics**: Updated the interface sensor with a standard `mdi:lan` icon for better visibility and added internal tracking for the active scanning interface.

### Changed

- **Tests**: Expanded the test suite to include full coverage for the new number platform and debouncing logic.

## [1.1.0] - 2026-04-02 - New Network Alert and Interface Sensor

### Added

- **New Network Alert**: Added a binary sensor that triggers when unknown SSIDs are detected, making it easier to set up automations.
- **Interface Sensor**: Added a diagnostic sensor to show the active WiFi adapter being scanned.
- **Setup Validation**: Enhanced the configuration flow to validate connectivity and the presence of the Supervisor token before setup completes.

## [1.0.2] - 2026-04-02 - Branding and Mock Supervisor

### Added

- **Branding**: Created new, generic WiFi scanning icons and logos.
- **Mock Supervisor**: Implemented service in the DevContainer to allow for integration testing on systems where physical WiFi access is restricted within containers.

## [1.0.1] - 2026-04-02 - Test Coverage to 99%

### Changed

- **Tests and Coverage**: Significantly expanded test suite to achieve 99% coverage, including new coordinator tests and improved error path validation.

### Fixed

- **Code Quality**: Fixed file formatting and line length issues to comply with Ruff standards.
- **Documentation**: Added missing docstrings across modules and tests.

## [1.0.0] - 2026-04-01 - Initial Release

### Added

- **Initial Release**: Basic SSID scanning and unknown SSID identification.
- **Supervisor API Integration**: Native async support for fetching access points.
- **Configurable Interface**: Support for choosing the WiFi interface.
- **Known SSID List**: Manage known networks via the UI.
- **Sensors**: Total SSID count and Unknown SSID count sensors with attributes.

---

### Format

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Entry structure — headers, titles, category headings and the split between this file and its counterpart — follows `.shared/dev_std/changelog_format.md`.
