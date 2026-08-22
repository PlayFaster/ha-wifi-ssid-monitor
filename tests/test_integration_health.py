"""Unit tests for the self-diagnosis check catalogue.

Pure functions over a ScanFacts snapshot — each check is asserted at its
severity, and the checks that fire only on a whole-payload change are shown
not to fire on a per-AP quirk.
"""

from custom_components.wifi_ssid_monitor import health
from custom_components.wifi_ssid_monitor.health import (
    SEVERITY_DEGRADED,
    SEVERITY_ERROR,
    SEVERITY_OK,
    SEVERITY_WARNING,
    Finding,
    ScanFacts,
    check_band_unresolved,
    check_empty_scan,
    check_field_absent_everywhere,
    check_field_absent_minority,
    check_interface_missing,
    check_known_network_canary,
    check_signal_unit_flip,
    run_checks,
    worst_severity,
)


def _ap(**over):
    base = {"mac": "AA:BB:CC:00:00:01", "signal_pct": 80, "band": "5 GHz"}
    base.update(over)
    return base


def test_interface_missing_is_an_error():
    """A missing interface is a total outage, and repairable.

    Section 19 reserves `error` for the device being unreachable. There is no
    core still working here to call `degraded`: the interface being monitored
    is the whole job.
    """
    finding = check_interface_missing(
        ScanFacts(interface="wlan0", interface_present=False)
    )
    assert finding is not None
    assert finding.severity == SEVERITY_ERROR
    assert finding.repair == "interface_missing"


def test_interface_present_no_finding():
    """A present interface produces no finding."""
    assert check_interface_missing(ScanFacts(interface_present=True)) is None


def test_signal_unit_flip():
    """A unit flip raises the signal-format repair."""
    finding = check_signal_unit_flip(
        ScanFacts(signal_unit="dBm", baseline_signal_unit="percent")
    )
    assert finding is not None
    assert finding.repair == "signal_format_changed"


def test_signal_unit_flip_needs_baseline():
    """Without a baseline there is no flip to report."""
    # No baseline yet — cannot be a flip.
    assert check_signal_unit_flip(ScanFacts(signal_unit="percent")) is None


def test_field_absent_everywhere():
    """A field absent from every AP is drift, so it reports `warning`."""
    facts = ScanFacts(normalized=[_ap(mac=None), _ap(mac=None)], total_aps=2)
    finding = check_field_absent_everywhere(facts)
    assert finding is not None
    assert finding.severity == SEVERITY_WARNING


def test_field_present_somewhere_no_finding():
    """A field present on some APs does not fire."""
    facts = ScanFacts(normalized=[_ap(mac=None), _ap()], total_aps=2)
    assert check_field_absent_everywhere(facts) is None


def test_band_unresolved_all_warns():
    """No AP resolving to a band is drift, so it reports `warning`."""
    facts = ScanFacts(normalized=[_ap(band=None), _ap(band=None)], total_aps=2)
    finding = check_band_unresolved(facts)
    assert finding is not None
    assert finding.severity == SEVERITY_WARNING


def test_band_unresolved_minority_warns():
    """A minority of unresolved bands is still drift, so still `warning`.

    Magnitude is not what picks the value: both the majority and the minority
    case describe data that arrived and may be wrong.
    """
    facts = ScanFacts(
        normalized=[_ap(band=None)] + [_ap() for _ in range(9)], total_aps=10
    )
    finding = check_band_unresolved(facts)
    assert finding is not None
    assert finding.severity == SEVERITY_WARNING


def test_canary_fires_when_all_known_vanish():
    """All known networks vanishing is a lost capability, so `degraded`.

    The scan itself is still working — it is returning networks, just not the
    expected ones — which is exactly what separates `degraded` from `error`.
    """
    facts = ScanFacts(established_known={"Home", "Office"}, seen_keys={"Neighbour"})
    finding = check_known_network_canary(facts)
    assert finding is not None
    assert finding.severity == SEVERITY_DEGRADED


def test_canary_silent_when_one_known_present():
    """One known network present keeps the canary silent."""
    facts = ScanFacts(established_known={"Home", "Office"}, seen_keys={"Home"})
    assert check_known_network_canary(facts) is None


def test_canary_silent_without_baseline():
    """No established networks means no canary."""
    # A fresh install with no established networks must not trip.
    assert check_known_network_canary(ScanFacts(seen_keys=set())) is None


def test_run_checks_survives_a_broken_check(monkeypatch):
    """A check that raises does not stop the others."""
    # A check raising must not propagate — a broken diagnosis cannot break a scan.
    from custom_components.wifi_ssid_monitor import health

    def boom(_facts):
        raise RuntimeError("boom")

    monkeypatch.setattr(health, "CHECKS", (boom, check_interface_missing))
    findings = run_checks(ScanFacts(interface_present=False))
    # The good check still ran.
    assert any(f.repair == "interface_missing" for f in findings)


def test_empty_normalized_fraction_missing_returns_zero():
    """When normalized list is empty, _fraction_missing returns 0.0."""
    from custom_components.wifi_ssid_monitor.health import check_field_absent_everywhere

    facts = ScanFacts(normalized=[], total_aps=0)
    assert check_field_absent_everywhere(facts) is None


def test_response_shape_no_ap_key():
    """When response_had_ap_key is False, a serious finding is returned."""
    from custom_components.wifi_ssid_monitor.health import check_response_shape

    finding = check_response_shape(ScanFacts(response_had_ap_key=False))
    assert finding is not None
    assert finding.key == "payload_no_ap_list"
    assert finding.severity == SEVERITY_WARNING


def test_field_absent_minority_fires_when_partial():
    """When a field is missing on some but not most APs, a minor finding is returned."""
    facts = ScanFacts(
        normalized=[_ap(mac=None)] + [_ap() for _ in range(9)],
        total_aps=10,
    )
    finding = check_field_absent_minority(facts)
    assert finding is not None
    assert finding.key == "payload_field_partial"
    assert finding.severity == SEVERITY_WARNING


def test_field_absent_minority_no_partial():
    """When no field is partially missing, no finding is returned."""
    from custom_components.wifi_ssid_monitor.health import check_field_absent_minority

    facts = ScanFacts(normalized=[_ap(), _ap()], total_aps=2)
    assert check_field_absent_minority(facts) is None


def test_empty_scan_triggers_on_established_known():
    """An empty scan with established known networks is a minor finding."""
    from custom_components.wifi_ssid_monitor.health import check_empty_scan

    facts = ScanFacts(
        total_aps=0,
        established_known={"HomeNet"},
        normalized=[],
    )
    finding = check_empty_scan(facts)
    assert finding is not None
    assert finding.key == "empty_scan"
    assert finding.severity == SEVERITY_DEGRADED


def test_empty_scan_silent_when_no_known():
    """An empty scan without established known networks is silent."""
    from custom_components.wifi_ssid_monitor.health import check_empty_scan

    assert check_empty_scan(ScanFacts(total_aps=0, established_known=set())) is None


def test_fraction_missing_empty_returns_zero():
    """_fraction_missing returns 0.0 when the normalized list is empty."""
    from custom_components.wifi_ssid_monitor.health import _fraction_missing

    assert _fraction_missing(ScanFacts(normalized=[]), "mac") == 0.0


# ---------------------------------------------------------------------------
# Section 19: the drift / capability split
#
# `degraded_capabilities` and `drift` are a published contract — users write
# templates against them — and the classification is one `is_drift` flag per
# check, defaulting to False. Nothing else asserts it: re-tagging a check
# changes what a user's automation sees and breaks no other test.
#
# These are coverage tests, not sample tests. The set they sweep is CHECKS
# itself, so adding a check without classifying it fails here.
# ---------------------------------------------------------------------------

# One ScanFacts per check, chosen to make that check fire. Keyed by the check
# function's name so a renamed or added check shows up as a missing key rather
# than as a silently smaller sweep.
_FIRING_FACTS: dict[str, ScanFacts] = {
    "check_interface_missing": ScanFacts(interface="wlan0", interface_present=False),
    "check_signal_unit_flip": ScanFacts(
        signal_unit="dBm", baseline_signal_unit="percent"
    ),
    "check_response_shape": ScanFacts(response_had_ap_key=False),
    "check_field_absent_everywhere": ScanFacts(
        normalized=[_ap(mac=None), _ap(mac=None)], total_aps=2
    ),
    "check_band_unresolved": ScanFacts(
        normalized=[_ap(band=None), _ap(band=None)], total_aps=2
    ),
    "check_field_absent_minority": ScanFacts(
        normalized=[_ap(mac=None)] + [_ap() for _ in range(9)], total_aps=10
    ),
    "check_known_network_canary": ScanFacts(
        established_known={"HomeNet"}, seen_keys={"Someone else"}
    ),
    "check_empty_scan": ScanFacts(total_aps=0, established_known={"HomeNet"}),
}

# Which published attribute each finding must land in. Every key a check can
# produce appears exactly once across the two sets.
_EXPECTED_DRIFT = {
    "signal_format_changed",
    "payload_no_ap_list",
    "payload_field_missing",
    "payload_field_partial",
    "band_unresolved_all",
    "band_unresolved_some",
}
_EXPECTED_CAPABILITY = {
    "interface_missing",
    "no_known_networks",
    "empty_scan",
    "supervisor_unreachable",  # set directly on the failure path, not by a check
}


def test_every_check_has_a_firing_fixture():
    """Every check in CHECKS is exercised by the classification tests below.

    This is the coverage guard: a new check added to CHECKS with no fixture
    here makes this fail, rather than quietly shrinking the sweep that the
    classification tests perform.
    """
    from custom_components.wifi_ssid_monitor.health import CHECKS

    missing = [c.__name__ for c in CHECKS if c.__name__ not in _FIRING_FACTS]
    assert not missing, f"CHECKS entries with no firing fixture: {missing}"

    unused = set(_FIRING_FACTS) - {c.__name__ for c in CHECKS}
    assert not unused, f"fixtures for checks that no longer exist: {sorted(unused)}"

    for check in CHECKS:
        assert check(_FIRING_FACTS[check.__name__]) is not None, (
            f"{check.__name__} did not fire under its fixture — the fixture has "
            f"gone stale and this check is no longer being classified"
        )


def test_every_finding_sets_a_valid_severity():
    """No check may publish a severity outside the Section 19 vocabulary.

    Written because a mutation setting `severity=None` on `check_signal_unit_flip`
    **survived** the 2026-08-06 run: every test asserted the severity of the check
    it was written for, so nothing noticed when one check stopped setting one.
    Severity is what the health sensor publishes and what user automations
    compare against, and `worst_severity` looks the value up in `_SEVERITY_RANK`
    — a `None` reaching it is a `KeyError` inside a poll, not a wrong string.

    Sweeps `CHECKS` rather than a list, so a check added later is covered without
    anyone remembering. `unknown` is deliberately excluded: it is the
    never-reported state, not something a firing check may claim.
    """
    from custom_components.wifi_ssid_monitor.health import CHECKS

    # The **published strings**, not the constants. Asserting
    # `{SEVERITY_OK, ...}` compares the code against itself: renaming a constant
    # renames both sides and the sweep still passes, while every user automation
    # matching on `severity` breaks. Section 19 fixes this vocabulary, so it is
    # spelled out here.
    allowed = {"ok", "degraded", "warning", "error"}
    assert {
        SEVERITY_OK,
        SEVERITY_DEGRADED,
        SEVERITY_WARNING,
        SEVERITY_ERROR,
    } == allowed, "a severity constant no longer carries its published string"

    for check in CHECKS:
        finding = check(_FIRING_FACTS[check.__name__])
        assert finding is not None
        assert finding.severity in allowed, (
            f"{check.__name__} published severity {finding.severity!r}, which is "
            f"not one of {sorted(allowed)}. Section 19 fixes this vocabulary and "
            f"user automations compare against it."
        )


def test_every_finding_is_classified_exactly_once():
    """Each key a check can produce is either drift or a capability, never both.

    Sweeps CHECKS rather than a hand-listed sample, so a new check with the
    default `is_drift=False` fails here until it is deliberately classified.
    """
    from custom_components.wifi_ssid_monitor.health import CHECKS

    seen: dict[str, bool] = {}
    for check in CHECKS:
        finding = check(_FIRING_FACTS[check.__name__])
        assert finding is not None
        seen[finding.key] = finding.is_drift

    for key, is_drift in seen.items():
        in_drift = key in _EXPECTED_DRIFT
        in_capability = key in _EXPECTED_CAPABILITY
        assert in_drift != in_capability, (
            f"'{key}' is in neither or both classification sets — every finding "
            f"must land in exactly one published attribute"
        )
        assert is_drift == in_drift, (
            f"'{key}' has is_drift={is_drift} but is classified as "
            f"{'drift' if in_drift else 'a capability'}. Changing this changes "
            f"which attribute users' automations read."
        )


def test_band_unresolved_minority_is_also_drift():
    """The second key `check_band_unresolved` can produce is classified too.

    One check, two keys — the sweep above only reaches whichever fires under
    its fixture, so the other is asserted here rather than left unclassified.
    """
    finding = check_band_unresolved(
        ScanFacts(normalized=[_ap(band=None)] + [_ap() for _ in range(9)], total_aps=10)
    )
    assert finding is not None
    assert finding.key == "band_unresolved_some"
    assert finding.is_drift is True


def test_drift_default_is_false():
    """A Finding built without an explicit classification is a capability.

    `health.py` advertises that adding a check is a one-line addition, so the
    default must fail safe: under-claiming drift is recoverable, over-claiming
    it raises a payload-changed alarm for an environmental condition.
    """
    from custom_components.wifi_ssid_monitor.health import Finding

    assert Finding(key="x", severity=SEVERITY_DEGRADED, message="m").is_drift is False


# ---------------------------------------------------------------------------
# Thresholds — the exact point each check changes its mind
# ---------------------------------------------------------------------------
#
# Mutation testing found every comparison in this module movable without a
# test noticing. The tests above assert the obvious side of each threshold
# (all missing, none missing), which is where an off-by-one is invisible.
#
# _MAJORITY is 0.9, so with ten access points the boundary falls exactly
# between nine missing and ten.


def test_band_unresolved_is_serious_at_exactly_the_majority():
    """9 of 10 missing is 0.9 — `>=` means this is already the serious case.

    Moving the comparison to `>` downgrades it to the minor finding, so the
    payload-shape change this check exists to catch would be reported as a
    percentage note instead of a serious drift finding.
    """
    facts = ScanFacts(
        normalized=[_ap(band=None)] * 9 + [_ap()],
        total_aps=10,
    )
    finding = check_band_unresolved(facts)
    assert finding is not None
    assert finding.key == "band_unresolved_all"
    assert finding.severity == SEVERITY_WARNING


def test_band_unresolved_is_minor_just_below_the_majority():
    """8 of 10 is 0.8 — below the threshold, so the minor finding fires."""
    facts = ScanFacts(
        normalized=[_ap(band=None)] * 8 + [_ap(), _ap()],
        total_aps=10,
    )
    finding = check_band_unresolved(facts)
    assert finding is not None
    assert finding.key == "band_unresolved_some"
    assert finding.severity == SEVERITY_WARNING


def test_field_absent_minority_stops_at_the_majority():
    """9 of 10 missing belongs to the *everywhere* check, not this one.

    The bound is `< _MAJORITY`. Widening it to `<=` makes both checks fire on
    the same payload, so a serious finding arrives paired with a minor one
    contradicting it.
    """
    facts = ScanFacts(normalized=[_ap(mac=None)] * 9 + [_ap()], total_aps=10)
    assert check_field_absent_minority(facts) is None


def test_field_absent_minority_fires_just_below_the_majority():
    """8 of 10 is this check's territory."""
    facts = ScanFacts(normalized=[_ap(mac=None)] * 8 + [_ap(), _ap()], total_aps=10)
    finding = check_field_absent_minority(facts)
    assert finding is not None
    assert finding.key == "payload_field_partial"


def test_field_absent_minority_watches_signal_pct_as_well_as_mac():
    """Both field names are checked, and both are named in the message.

    The names are a literal tuple. Mutating either one leaves a check that
    quietly stops looking at that field — the tests pass, and the signal
    column can go missing on half the network map with nothing said.
    """
    facts = ScanFacts(normalized=[_ap(signal_pct=None), _ap()], total_aps=2)
    finding = check_field_absent_minority(facts)
    assert finding is not None
    assert "signal_pct" in finding.message


def test_empty_scan_fires_only_when_nothing_at_all_was_found():
    """Zero access points is empty; one is not.

    The gate is `total_aps > 0`. Moving it to `> 1` reports a location that
    found a single network as having found nothing, which is a false alarm in
    exactly the marginal-reception case the check is supposed to help with.
    """
    known = {"Home"}
    assert check_empty_scan(ScanFacts(total_aps=0, established_known=known)) is not None
    assert check_empty_scan(ScanFacts(total_aps=1, established_known=known)) is None


def test_empty_scan_stays_silent_without_established_known_networks():
    """A genuinely quiet location must not trip this."""
    assert check_empty_scan(ScanFacts(total_aps=0, established_known=set())) is None


# ---------------------------------------------------------------------------
# run_checks — the dispatch loop's own contract
# ---------------------------------------------------------------------------


def test_a_raising_check_does_not_stop_the_checks_after_it(monkeypatch):
    """The isolation this function's docstring promises, asserted.

    `run_checks` is called from the middle of a poll and catches per-check
    exceptions so a bug in one check cannot fail the update. Nothing proved
    the loop *continues* — swapping `continue` for `break` passed every test,
    and would silently disable every check after the first broken one.
    """

    def boom(_facts):
        raise ValueError("this check is broken")

    def always_fires(_facts):
        return Finding(key="sentinel", severity=SEVERITY_DEGRADED, message="fired")

    monkeypatch.setattr(health, "CHECKS", (boom, always_fires))

    findings = run_checks(ScanFacts())

    assert [f.key for f in findings] == ["sentinel"]


def test_run_checks_collects_findings_and_discards_the_quiet_checks(monkeypatch):
    """Only checks returning a Finding contribute, and `None` never lands.

    Inverting the `is not None` test, or appending `result` unconditionally,
    both put `None` into the findings list — which the health sensor then
    reads attributes from.
    """

    def quiet(_facts):
        return None

    def loud(_facts):
        return Finding(key="loud", severity=SEVERITY_WARNING, message="x")

    monkeypatch.setattr(health, "CHECKS", (quiet, loud, quiet))

    findings = run_checks(ScanFacts())

    assert len(findings) == 1
    assert findings[0].key == "loud"
    assert None not in findings


def test_run_checks_returns_an_empty_list_when_nothing_fires(monkeypatch):
    """The healthy case is an empty list, not None."""
    monkeypatch.setattr(health, "CHECKS", (lambda _f: None,))
    assert run_checks(ScanFacts()) == []


def test_field_absent_everywhere_is_serious_at_exactly_the_majority():
    """9 of 10 missing is 0.9, and `>=` means this check owns it.

    The same threshold as `check_band_unresolved`, in a different function.
    Moving it to `>` leaves the payload silently unreported: this check stops
    firing and `check_field_absent_minority`, bounded by `< _MAJORITY`, never
    starts. A field missing on 90% of networks would produce no finding at all.
    """
    facts = ScanFacts(normalized=[_ap(mac=None)] * 9 + [_ap()], total_aps=10)
    finding = check_field_absent_everywhere(facts)
    assert finding is not None
    assert finding.severity == SEVERITY_WARNING


def test_band_unresolved_says_nothing_when_every_band_resolved():
    """Zero missing must produce no finding.

    The minor branch is gated on `fraction > 0`. Relaxing it to `>= 0` makes
    it fire on a completely healthy scan, reporting "0% of networks reported a
    frequency outside the known ranges" every poll.
    """
    facts = ScanFacts(normalized=[_ap(), _ap(), _ap()], total_aps=3)
    assert check_band_unresolved(facts) is None


# ---------------------------------------------------------------------------
# Section 19 aggregation ladder — x_project C-014
# ---------------------------------------------------------------------------


def test_no_findings_aggregates_to_ok():
    """An empty set is a positive verdict, not an absent one.

    This is the whole point of banning `None`: healthy has to say something.
    """
    assert worst_severity([]) == SEVERITY_OK


def test_error_beats_everything():
    """A total outage is not softened by whatever else fired alongside it."""
    assert worst_severity([SEVERITY_DEGRADED, SEVERITY_ERROR]) == SEVERITY_ERROR
    assert worst_severity([SEVERITY_WARNING, SEVERITY_ERROR]) == SEVERITY_ERROR


def test_drift_outranks_a_lost_capability():
    """`warning` wins over `degraded`, matching Section 19's own order.

    `zte_router_5g` resolves the same collision the same way. It is not an
    arbitrary tie-break: data you cannot trust is the harder problem to notice,
    because unlike a lost capability nothing else about the integration looks
    wrong.
    """
    assert worst_severity([SEVERITY_DEGRADED, SEVERITY_WARNING]) == SEVERITY_WARNING
    assert worst_severity([SEVERITY_WARNING, SEVERITY_DEGRADED]) == SEVERITY_WARNING


def test_every_check_reports_a_value_the_standard_allows():
    """Sweep, not spot checks — and the value must follow the classification.

    Two things are asserted together because they are one rule: Section 19
    forbids inventing a sixth word, and it defines which of the five each kind
    of finding gets. Drift means the data that arrived may be wrong, so it is
    `warning`; a failed capability means something stopped working, so it is
    `degraded`. `interface_missing` is the single exception and is named here
    rather than excused — the interface being monitored is the whole job, so
    there is no core left working to call degraded.

    Reuses `_FIRING_FACTS` rather than rolling its own fixtures, so a check
    added without one fails in `test_every_check_has_a_firing_fixture` instead
    of shrinking this sweep silently.
    """
    from custom_components.wifi_ssid_monitor.health import _SEVERITY_RANK, CHECKS

    error_by_design = {"interface_missing"}

    for check in CHECKS:
        finding = check(_FIRING_FACTS[check.__name__])
        assert finding is not None
        assert finding.severity in _SEVERITY_RANK, (
            f"{finding.key} reports {finding.severity!r}, which is not one of "
            f"the five Section 19 values"
        )

        if finding.key in error_by_design:
            expected = SEVERITY_ERROR
        elif finding.is_drift:
            expected = SEVERITY_WARNING
        else:
            expected = SEVERITY_DEGRADED

        assert finding.severity == expected, (
            f"{finding.key} is classified is_drift={finding.is_drift} but "
            f"reports {finding.severity!r}; expected {expected!r}"
        )


# ---------------------------------------------------------------------------
# Repairs a check can raise must be registered for removal
# ---------------------------------------------------------------------------
#
# The text side of this contract — that each repair renders a sentence rather
# than its raw key — is swept in `test_entity_hygiene.py`. This is the other
# half, and it lives here because it is a property of `CHECKS`.


def _registered_issue_keys() -> set[str]:
    """Return the bare repair keys `async_remove_entry` will delete."""
    from custom_components.wifi_ssid_monitor.const import all_issue_ids

    sentinel = "sentinel_entry"
    suffix = f"_{sentinel}"
    ids = all_issue_ids(sentinel)
    assert ids, "all_issue_ids() is empty — this sweep would pass vacuously"
    return {scoped[: -len(suffix)] for scoped in ids}


def test_every_check_repair_is_registered_for_removal() -> None:
    """A check may not declare a repair `all_issue_ids()` does not know about.

    This is the sharp one. `async_remove_entry` deletes exactly the ids
    `all_issue_ids()` returns, so a repair raised from a check but missing from
    that list is **never cleaned up**: uninstalling the integration leaves a
    permanent Repairs card with no UI path to clear it.

    Reuses `_FIRING_FACTS` so a check added without a fixture fails in
    `test_every_check_has_a_firing_fixture` rather than shrinking this sweep.
    """
    from custom_components.wifi_ssid_monitor.health import CHECKS

    declared = set()
    for check in CHECKS:
        finding = check(_FIRING_FACTS[check.__name__])
        assert finding is not None
        if finding.repair:
            declared.add(finding.repair)

    unregistered = sorted(declared - _registered_issue_keys())
    assert not unregistered, (
        f"checks declare repair(s) {unregistered} that all_issue_ids() does not "
        f"list. async_remove_entry would leave them raised for ever — add them "
        f"to all_issue_ids() in const.py."
    )
