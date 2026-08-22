"""Recorder hygiene — dev_standards Section 14.

The failure this guards is silent. When an attribute is added to an entity and
not added to ``_unrecorded_attributes``, nothing errors and nothing looks
wrong; the value is simply written to the recorder database on every state
change, forever. This project had exactly that: ``severity`` and
``networks_scanned`` were published but never excluded, the second of them
changing on every scan.

Section 14 (Standard Version 1.12.0) makes the default total: every key an
entity can publish must be unrecorded, and a recorded attribute is an exception
needing a written justification. Attributes exist to carry detail about
something that does not merit its own entity — they are not a history
mechanism. A value whose history is genuinely wanted should be promoted to an
entity, or templated into one by the user.

The sweep runs against live entities rather than reading source because
description-driven entities build their attributes from a function on the
entity description, and no static check can see through that.
"""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.wifi_ssid_monitor.const import DOMAIN

# Attributes deliberately left recorded, with the justification Section 14
# requires. Empty by design — adding an entry here is a visible, reviewable
# act, whereas forgetting to extend `_unrecorded_attributes` is not. That
# asymmetry is the entire point of the allow-list.
ALLOWED_RECORDED: frozenset[str] = frozenset()

# Below this, the sweep is not meaningfully exercising the integration and a
# pass would be vacuous — a fixture that stops producing attributes would let
# a real regression through silently.
#
# Measured 2026-08-03: 16 of the integration's 18 entities publish attributes;
# the other two publish none and are skipped, which is correct. Set to the
# real figure rather than a token floor — at 2 the guard passed while 14
# entities went uninspected, which is the failure it exists to prevent.
MIN_ENTITIES_SWEPT = 16

_ACCESS_POINTS = [
    {
        "mac": "AA:BB:CC:00:00:01",
        "ssid": "MyNetwork1",
        "signal": 80,
        "frequency": 2462,
        "mode": "infrastructure",
    },
    {
        "mac": "AA:BB:CC:00:00:02",
        "ssid": "UnknownNet",
        "signal": 55,
        "frequency": 5240,
        "mode": "infrastructure",
    },
]


@pytest.mark.asyncio
async def test_no_entity_publishes_a_recorded_attribute(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """Section 14: `_unrecorded_attributes` must cover every published key."""
    mock_config_entry.add_to_hass(hass)

    with (
        # Force disabled-by-default entities to be added. Without this the
        # sweep silently skips them — they are never instantiated, so their
        # attributes are never inspected. Verified in `zte_router_5g` by
        # mutation: removing a key from a disabled-by-default sensor's
        # `_unrecorded_attributes` did not fail the sweep until this patch was
        # added, and adding it immediately surfaced a real offender.
        patch(
            "homeassistant.helpers.entity.Entity.entity_registry_enabled_default",
            property(lambda self: True),
        ),
        patch(
            "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
            new=AsyncMock(return_value=list(_ACCESS_POINTS)),
        ),
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        checked = 0
        offenders: list[str] = []
        for component in hass.data["entity_components"].values():
            for entity in component.entities:
                platform = getattr(entity, "platform", None)
                if platform is None or platform.platform_name != DOMAIN:
                    continue
                published = set(entity.extra_state_attributes or {})
                if not published:
                    continue
                checked += 1
                leaked = published - entity._unrecorded_attributes - ALLOWED_RECORDED
                if leaked:
                    offenders.append(f"{entity.entity_id}: {sorted(leaked)}")

    assert not offenders, "attributes published but recorded:\n" + "\n".join(offenders)
    assert checked >= MIN_ENTITIES_SWEPT, (
        f"sweep inspected only {checked} entities — the fixture has gone stale "
        f"and this test is passing vacuously"
    )


def test_health_detail_is_unrecorded() -> None:
    """Regression guard for the specific miss found on 2026-07-27.

    `severity` and `networks_scanned` were published by the health sensor but
    absent from `_unrecorded_attributes`, which had fallen behind
    `extra_state_attributes` as the attribute set grew.
    """
    from custom_components.wifi_ssid_monitor.binary_sensor import (
        WifiHealthBinarySensor,
    )

    unrecorded = WifiHealthBinarySensor._unrecorded_attributes
    for name in (
        "issues",
        "severity",
        "degraded_capabilities",
        "drift",
        "signal_unit",
        "last_good_update",
        "networks_scanned",
    ):
        assert name in unrecorded, f"Section 14 requires '{name}' to be unrecorded"


# ---------------------------------------------------------------------------
# Section 12 (b) and (c): icon coverage.
#
# Two properties, deliberately not merged, and neither comparing one artefact
# against another:
#
#  (b) Entities — swept LIVE, not from a description list. Descriptions here
#      live in a mix of module-level tuples (`SENSOR_TYPES`) and standalone
#      singletons (`HEALTH_DESCRIPTION`), so any static enumeration drifts the
#      moment a platform is added. And the check is PER-PLATFORM: flattening
#      `icons.json` into one key set lets an entry filed under the wrong
#      platform satisfy it while the entity still renders a default icon.
#
#  (c) Actions — every registered action carries an icon, and every icon names
#      a real action. Action icons appear in the automation and script editors
#      and in Tools -> Actions; they never appear on the device page
#      or on an entity, so an integration missing them looks entirely normal
#      until someone opens the action picker. That invisibility is why this
#      went unnoticed across the project family until 2026-08-03.
#
# Required by dev_standards Section 12 (Standard Version 1.21.0), which
# extended the section from entity icons to action icons.
# ---------------------------------------------------------------------------

import json  # noqa: E402
import pathlib  # noqa: E402

_ICONS = json.loads(
    (
        pathlib.Path(__file__).parent.parent
        / "custom_components"
        / "wifi_ssid_monitor"
        / "icons.json"
    ).read_text(encoding="utf-8")
)


@pytest.mark.asyncio
async def test_every_live_entity_has_an_icon_or_a_device_class(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """Section 12(b): every entity resolves an icon, checked per platform."""
    mock_config_entry.add_to_hass(hass)

    entity_icons: dict[str, dict] = _ICONS.get("entity", {})

    with (
        patch(
            "homeassistant.helpers.entity.Entity.entity_registry_enabled_default",
            property(lambda self: True),
        ),
        patch(
            "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
            new=AsyncMock(return_value=list(_ACCESS_POINTS)),
        ),
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        checked = 0
        offenders: list[str] = []
        seen_keys: set[tuple[str, str]] = set()

        for component in hass.data["entity_components"].values():
            for entity in component.entities:
                platform = getattr(entity, "platform", None)
                if platform is None or platform.platform_name != DOMAIN:
                    continue
                checked += 1

                key = entity.translation_key
                domain = entity.entity_id.split(".", 1)[0]

                # Recorded before the device_class skip below. An entity with a
                # device class may still carry an explicit icon entry — that is
                # a deliberate override, not a dead entry — so it must count as
                # "seen" or the dead-entry check below reports a false positive.
                seen_keys.add((domain, key))

                # A device class supplies a sensible default icon on its own.
                if getattr(entity, "device_class", None) is not None:
                    continue

                # Per-platform lookup on purpose: an entry filed under the
                # wrong platform must not satisfy this.
                if key not in entity_icons.get(domain, {}):
                    offenders.append(
                        f"{entity.entity_id} (icons.entity.{domain}.{key})"
                    )

    assert not offenders, (
        "entities with no device_class and no icons.json entry under their own "
        "platform:\n" + "\n".join(offenders)
    )
    assert checked >= MIN_ENTITIES_SWEPT, (
        f"icon sweep inspected only {checked} entities — the fixture has gone "
        f"stale and this test is passing vacuously"
    )

    # Dead entries mask genuine gaps and inflate any count-based assessment.
    declared = {(plat, key) for plat, keys in entity_icons.items() for key in keys}
    dead = sorted(declared - seen_keys)
    assert not dead, f"icons.json entity entries matching no live entity: {dead}"


@pytest.mark.asyncio
async def test_every_registered_action_has_an_icon(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """Section 12(c): the services block matches the registered actions, both ways."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        new=AsyncMock(return_value=list(_ACCESS_POINTS)),
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Truth comes from what HA has actually registered, never from the
        # icon file being tested.
        registered = set(hass.services.async_services().get(DOMAIN, {}))

    assert registered, "no actions registered — this test would pass vacuously"

    declared = _ICONS.get("services", {})

    missing = sorted(registered - set(declared))
    assert not missing, (
        f"registered actions with no icons.json entry: {missing}. These render "
        f"with the generic default in the automation editor and the Actions picker."
    )

    dead = sorted(set(declared) - registered)
    assert not dead, f"icons.json service entries matching no registered action: {dead}"

    # The nested `{"service": "mdi:..."}` form, not the legacy bare string:
    # only the object form can carry per-section icons.
    flat = sorted(k for k, v in declared.items() if not isinstance(v, dict))
    assert not flat, (
        f"action icons declared in the legacy flat form: {flat}. Use "
        f'{{"service": "mdi:..."}} so a `sections` icon can be added later.'
    )


# ---------------------------------------------------------------------------
# Suppressed static-analysis directives — every one is a reviewed decision
# ---------------------------------------------------------------------------
#
# `masked_errors_check` Class D, and x_project chore C-004. Ported from
# `ha-huawei-router-5g-monitor`, where an audit on 2026-08-14 found five
# suppressions of which **three were wrong and two were hiding live defects**:
# two calls behind a `type: ignore` were to library methods that did not
# exist, so the controls had never worked.
#
# A prompt run is a point-in-time audit. This is the mechanism that keeps it
# true afterwards: the set cannot grow without someone editing the table below
# and writing a reason.
#
# **Why ruff and mypy do not already cover this.** `RUF100` and mypy's
# `warn_unused_ignores` report a suppression that is *unnecessary* — one where
# no error would have fired. They are silent on the dangerous case: a
# suppression that IS doing work, because the error is real. Huawei was clean
# under both while two calls to non-existent methods sat behind `type: ignore`.
#
# Keyed on (file, code) rather than line number, so ordinary edits do not
# churn it.
ALLOWED_SUPPRESSIONS: dict[tuple[str, str], str] = {
    ("coordinator.py", "noqa: BLE001"): (
        "Guards `run_checks` on the fetch-failure path. This whole method runs "
        "inside the coordinator's error handler, so anything raised out of the "
        "health computation would replace the Supervisor error that actually "
        "caused the failure — the user would be shown the wrong cause. The "
        "checks are pure functions over a ScanFacts snapshot and have no "
        "expected exception to name, which is what makes the except broad. "
        "Verified 2026-08-21: findings default to [] and the Supervisor error "
        "propagates unchanged."
    ),
    ("test_entity_hygiene.py", "noqa: E402"): (
        "`json` and `pathlib` are imported mid-module, below the long comment "
        "block explaining why the icon sweep reads the shipped icons.json "
        "rather than a copy. Moving them to the top would separate the imports "
        "from the `_ICONS` load they exist for, which is the only thing in "
        "this file that uses them. Placement only — no rule about the code "
        "itself is being suppressed."
    ),
}


def _shipped_root():
    """Return the project root of the **shipped** tree, not a working copy.

    `mutmut` runs the suite from a `mutants/` directory holding a rewritten
    copy of `custom_components/` and `tests/` — and **nothing else**. The
    suppression sweep is about the shipped tree rather than about behavior,
    and reading the mutant copy breaks it: every mutated copy of a function
    carries its comments again, turning two reviewed suppressions into
    several hundred unreviewed ones.

    Resolving from the first ancestor that actually carries a `docs/`
    directory steps out of the mutant tree and reads what ships. It never
    falls back to a copy and never skips: a genuinely missing tree still
    raises.
    """
    import pathlib

    import custom_components.wifi_ssid_monitor as component

    start = pathlib.Path(component.__path__[0]).parent.parent
    for base in (start, *start.parents):
        if (base / "docs").is_dir():
            return base
    raise FileNotFoundError(f"no docs/ directory found above {start}")


def _real_comments() -> list[tuple[str, int, str]]:
    """Return every genuine comment in the component and tests.

    Uses `tokenize` rather than a regex over raw text: docstrings and comments
    in these projects quote directives while explaining why a past one was
    wrong, and a text search cannot tell those apart from a live suppression.
    On Huawei the raw count was 14 against 2 real ones.
    """
    import tokenize

    root = _shipped_root()
    roots = [root / "custom_components" / "wifi_ssid_monitor", root / "tests"]

    found: list[tuple[str, int, str]] = []
    for base in roots:
        for path in sorted(base.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            with path.open("rb") as handle:
                found.extend(
                    (path.name, token.start[0], token.string)
                    for token in tokenize.tokenize(handle.readline)
                    if token.type == tokenize.COMMENT
                )
    return found


def _live_suppressions() -> dict[tuple[str, str], list[int]]:
    """Map (file, directive) to the lines carrying it."""
    import re

    # The optional `ruff: ` prefix is the **file-level** form and must be
    # caught: that directive at the top of a module suppresses its rule for
    # every line in the file, which is broader than any per-line directive.
    #
    # The literal form is deliberately not written out in this comment: ruff
    # scans comments for it and would read the example as a real directive.
    #
    # The prefix is kept in the captured code rather than normalized away, so
    # a file-level suppression can never be reviewed as if it were one line.
    pattern = re.compile(
        r"#\s*((?:ruff:\s*)?(?:type:\s*ignore(?:\[[^\]]*\])?"
        r"|noqa(?::\s*[A-Z0-9, ]+)?|pragma:\s*no cover))"
    )

    live: dict[tuple[str, str], list[int]] = {}
    for filename, line, comment in _real_comments():
        for raw in pattern.findall(comment):
            code = " ".join(raw.split())
            live.setdefault((filename, code), []).append(line)
    return live


def test_every_suppression_is_on_the_reviewed_allow_list() -> None:
    """No `type: ignore`, `noqa` or `pragma: no cover` without a written reason.

    **If this fails, the new suppression needs a reason, not an entry.** Ask
    what the tool would have said and whether that thing is actually true —
    an `attr-defined` ignore on a library call is a *claim about that library*.
    """
    unlisted = sorted(
        f"{filename}:{','.join(str(n) for n in lines)}  {code}"
        for (filename, code), lines in _live_suppressions().items()
        if (filename, code) not in ALLOWED_SUPPRESSIONS
    )

    assert not unlisted, (
        "suppressions with no reviewed justification:\n"
        + "\n".join(unlisted)
        + "\n\nAdd to ALLOWED_SUPPRESSIONS with a reason, or fix the underlying "
        "problem. Removing the suppression alone is not a fix."
    )


def test_allowed_suppressions_has_no_dead_entries() -> None:
    """An allow-list entry must not outlive the suppression it covers.

    A dead entry silently pre-approves the next occurrence of the same
    directive in the same file, which is how a reviewed exception becomes an
    unreviewed habit.
    """
    live = set(_live_suppressions())
    stale = sorted(f"{f}  {c}" for (f, c) in ALLOWED_SUPPRESSIONS if (f, c) not in live)

    assert not stale, (
        "ALLOWED_SUPPRESSIONS entries that no longer match anything:\n"
        + "\n".join(stale)
    )


def test_every_allowed_suppression_states_a_reason() -> None:
    """The reason is the entire value of the allow-list.

    An entry with an empty or token justification is indistinguishable from
    one added to make a check pass, which is the thing being guarded against.
    """
    thin = sorted(
        f"{f}  {c}"
        for (f, c), reason in ALLOWED_SUPPRESSIONS.items()
        if len(reason.strip()) < 40
    )
    assert not thin, "allow-list entries with no real justification:\n" + "\n".join(
        thin
    )


# ---------------------------------------------------------------------------
# Repair issues — every one must have text a user can read
# ---------------------------------------------------------------------------
#
# dev_standards §19: "each repair `translation_key` needs a matching `issues.*`
# entry in `strings.json` **and** the compiled `translations/*.json`, or the
# Repairs card shows the raw key."
#
# Nothing caught that until 2026-08-21. A repair added without its text passes
# every other test in this suite — the key is asserted, never the string behind
# it — and the defect is visible only to a user who has already hit the fault
# the repair exists to explain. That is the worst possible moment to show them
# `supervisor_unavailable_01KND...` instead of a sentence.
#
# Driven off `all_issue_ids()`, which is the same list `async_remove_entry`
# uses, so the text side cannot drift from the raise side or the delete side.

_ISSUE_SENTINEL = "sentinel_entry"


def _issue_keys() -> set[str]:
    """Return the bare repair keys, unscoped from their entry id."""
    from custom_components.wifi_ssid_monitor.const import all_issue_ids

    suffix = f"_{_ISSUE_SENTINEL}"
    ids = all_issue_ids(_ISSUE_SENTINEL)
    assert ids, "all_issue_ids() is empty — this sweep would pass vacuously"
    for scoped in ids:
        assert scoped.endswith(suffix), (
            f"{scoped!r} is not entry-scoped; issue_id() has changed shape and "
            f"this helper no longer knows how to unscope it"
        )
    return {scoped[: -len(suffix)] for scoped in ids}


def _translation_files() -> list:
    """Return `strings.json` plus every compiled translation."""
    component = _shipped_root() / "custom_components" / "wifi_ssid_monitor"
    return [
        component / "strings.json",
        *sorted((component / "translations").glob("*.json")),
    ]


def test_every_repair_issue_has_title_and_description() -> None:
    """A raised repair must render a sentence, not its translation key.

    Sweeps every translation file, not just `strings.json`: the compiled
    `translations/en.json` is the one Home Assistant actually reads, and the
    two drifting apart is invisible until the card is on screen.
    """
    import json

    keys = _issue_keys()
    missing: list[str] = []

    for path in _translation_files():
        issues = json.loads(path.read_text(encoding="utf-8")).get("issues", {})
        for key in sorted(keys):
            entry = issues.get(key)
            if not isinstance(entry, dict):
                missing.append(f"{path.name}: issues.{key} absent")
                continue
            missing.extend(
                f"{path.name}: issues.{key}.{field} empty or absent"
                for field in ("title", "description")
                if not str(entry.get(field, "")).strip()
            )

    assert not missing, (
        "repair issues with no readable text:\n"
        + "\n".join(missing)
        + "\n\nAdd the entry to strings.json AND every translations/*.json, or "
        "the Repairs card shows the raw key at exactly the moment the user "
        "most needs a sentence."
    )


def test_no_orphan_issue_translations() -> None:
    """An `issues.*` entry that matches no real repair is dead text.

    It reads as coverage on inspection and can never appear, which is how a
    renamed repair leaves its old text behind and its new key with none.
    """
    import json

    keys = _issue_keys()
    orphans: list[str] = []
    for path in _translation_files():
        issues = json.loads(path.read_text(encoding="utf-8")).get("issues", {})
        orphans.extend(
            f"{path.name}: issues.{key}" for key in sorted(set(issues) - keys)
        )

    assert not orphans, (
        "translation entries matching no repair this integration can raise:\n"
        + "\n".join(orphans)
    )
