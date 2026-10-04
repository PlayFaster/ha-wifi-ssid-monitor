# Test Guards: WiFi SSID Monitor

Rationale for the guard tests listed under _Tests that will stop you_ in [`AGENTS.md`](../AGENTS.md). `AGENTS.md` states what fails and what to do; this file records why each guard exists. When a guard test is added, its row goes in `AGENTS.md` and its rationale here.

---

## Guards Moved From `AGENTS.md` (2026-09-23)

Each entry is the rationale column of the former `AGENTS.md` table, copied verbatim.

### A sensor with a unit or `state_class`

**Tests:** `test_every_numeric_sensor_has_a_guard_band`

Declare `min_limit` / `max_limit`, or add the key to `UNGUARDED_ALLOWLIST` **with a reason**. Also update `docs/value_min_max.md` — §6 requires it to match the code both ways.

### Any entity

**Tests:** `test_every_live_entity_has_an_icon_or_a_device_class`

Add an `icons.json` entry **under that entity's own platform**, unless it has a `device_class`.

### Any action

**Tests:** `test_every_registered_action_has_an_icon`

Add a `services` entry in the nested `{"service": "mdi:..."}` form. The flat string form is legacy and the test rejects it.

### An entity attribute

**Tests:** `test_no_entity_publishes_a_recorded_attribute`

Add the key to that class's `_unrecorded_attributes`. **Repeat `"about"` if the class declares its own set** — HA does not merge this attribute across the class hierarchy, so a subclass assignment shadows the mixin's entirely.

### A new `severity` value, or a check whose value disagrees with its `is_drift` flag

**Tests:** `test_every_check_reports_a_value_the_standard_allows`, `test_every_published_severity_is_in_the_section_19_vocabulary`, `test_every_finding_is_classified_exactly_once`

Use one of `dev_standards` §19's five words — drift is `warning`, a lost capability is `degraded`, and `None` is never permitted. A sixth value is a contract change and belongs in the standard first, because user templates compare against these strings.

### A `_LOGGER` call that passes a payload or a network key

**Tests:** `test_the_ap_sample_log_carries_keys_and_never_values`, `test_discarded_timestamps_are_counted_not_named`

Log the **shape** — field names and counts. §20: a log file has no redaction layer and users paste them into public issues, and an SSID is data about someone who never installed this.

### A repair issue, or a renamed one

**Tests:** `test_every_repair_issue_has_title_and_rendered_text`, `test_no_orphan_issue_translations`, `test_every_repair_the_code_raises_is_registered_for_removal`

Add `issues.<key>.title` and `.description` to `strings.json` **and** every `translations/*.json`, and add the key to `all_issue_ids()` in `const.py`. That list is what `async_remove_entry` deletes — a repair missing from it outlives the integration with no UI path to clear it.

### A health check in `CHECKS`

**Tests:** `test_every_check_has_a_firing_fixture`, `test_every_finding_is_classified_exactly_once`

Add a fixture that makes it fire, and classify it in `_EXPECTED_DRIFT` or `_EXPECTED_CAPABILITY`. `is_drift` defaults to `False`, so a new check is a capability unless it opts in.

### A fourth `Store`

**Tests:** `test_async_remove_entry_deletes_every_live_store`

Add the key to `all_storage_keys()` in `const.py`, which both the coordinator and `async_remove_entry` build from.

### A condition only ever exercised one way

**Tests:** `Pytest: Check Test Coverage` reports a partial branch (`123->126` in the `Missing` column)

**Write the test.** All twelve found here were missing tests; none was dead code. Delete the guard only where the type system or the immediate caller already prevents the case — never in code consuming held or stored state, where the "impossible" shape arrives exactly when something upstream has already failed.

### A `# type: ignore`, `# noqa` or `# pragma: no cover` anywhere in `custom_components/` or `tests/`

**Tests:** `test_every_suppression_is_on_the_reviewed_allow_list`

Add it to `ALLOWED_SUPPRESSIONS` in `tests/test_entity_hygiene.py` **with a reason**. Ask what the tool would have said and whether that thing is _true_ — a suppression the linters accept can still be hiding a real defect, which is why `RUF100` and `warn_unused_ignores` do not cover this. Removing a suppression alone is not a fix. Removing the code it covered will fail `test_allowed_suppressions_has_no_dead_entries` instead; delete the entry too.

### A control that writes an option and then publishes

**Tests:** `test_switch_publishes_the_post_write_state`, `test_number_publishes_the_post_write_value`

Publish **after** the write. These capture what the entity reads at the moment `async_write_ha_state` fires, so a publish carrying the pre-write value fails here and nowhere else — the three older switch tests pass against exactly that defect. Background: `.shared/issues/x_project/stubbed_publish_tests.md`.

### A test that runs code without checking it

**Tests:** `Tests: Assertion Audit`

Assert the **observable outcome**. Where "this must not raise" is the real contract, assert what that implies — nothing cancelled, no task created, exactly one event on the bus — so the test fails on a behavior change and not only on a crash. Adding a trivial assertion to clear the count is a defect, not a fix. Last resort: `tests/zero_assertion_allowlist.txt`, with a reason.

---

## Guards Added to the Table (2026-09-23)

Tests that fire on an ordinary change and were not previously listed. Each rationale is the test's docstring.

### `test_health_detail_is_unrecorded`

Regression guard for the specific miss found on 2026-07-27. `severity` and `networks_scanned` were published by the health sensor but absent from `_unrecorded_attributes`, which had fallen behind `extra_state_attributes` as the attribute set grew.

### `test_every_allowed_suppression_states_a_reason`

The reason is the entire value of the allow-list. An entry with an empty or token justification is indistinguishable from one added to make a check pass, which is the thing being guarded against.
