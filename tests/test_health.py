"""Unit tests for the self-diagnosis check catalogue.

Pure functions over a ScanFacts snapshot — each check is asserted at its
severity, and the checks that fire only on a whole-payload change are shown
not to fire on a per-AP quirk.
"""

from custom_components.wifi_ssid_monitor.health import (
    SEVERITY_MINOR,
    SEVERITY_SERIOUS,
    ScanFacts,
    check_band_unresolved,
    check_field_absent_everywhere,
    check_field_absent_minority,
    check_interface_missing,
    check_known_network_canary,
    check_signal_unit_flip,
    run_checks,
)


def _ap(**over):
    base = {"mac": "AA:BB:CC:00:00:01", "signal_pct": 80, "band": "5 GHz"}
    base.update(over)
    return base


def test_interface_missing_serious():
    """A missing interface is a serious, repairable finding."""
    finding = check_interface_missing(
        ScanFacts(interface="wlan0", interface_present=False)
    )
    assert finding is not None
    assert finding.severity == SEVERITY_SERIOUS
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
    """A field absent from every AP is serious."""
    facts = ScanFacts(normalized=[_ap(mac=None), _ap(mac=None)], total_aps=2)
    finding = check_field_absent_everywhere(facts)
    assert finding is not None
    assert finding.severity == SEVERITY_SERIOUS


def test_field_present_somewhere_no_finding():
    """A field present on some APs does not fire."""
    facts = ScanFacts(normalized=[_ap(mac=None), _ap()], total_aps=2)
    assert check_field_absent_everywhere(facts) is None


def test_band_unresolved_all_serious():
    """No AP resolving to a band is serious."""
    facts = ScanFacts(normalized=[_ap(band=None), _ap(band=None)], total_aps=2)
    finding = check_band_unresolved(facts)
    assert finding is not None
    assert finding.severity == SEVERITY_SERIOUS


def test_band_unresolved_minority_minor():
    """A minority of unresolved bands is minor."""
    facts = ScanFacts(
        normalized=[_ap(band=None)] + [_ap() for _ in range(9)], total_aps=10
    )
    finding = check_band_unresolved(facts)
    assert finding is not None
    assert finding.severity == SEVERITY_MINOR


def test_canary_fires_when_all_known_vanish():
    """All established known networks vanishing is serious."""
    facts = ScanFacts(established_known={"Home", "Office"}, seen_keys={"Neighbour"})
    finding = check_known_network_canary(facts)
    assert finding is not None
    assert finding.severity == SEVERITY_SERIOUS


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
    assert finding.severity == SEVERITY_SERIOUS


def test_field_absent_minority_fires_when_partial():
    """When a field is missing on some but not most APs, a minor finding is returned."""
    facts = ScanFacts(
        normalized=[_ap(mac=None)] + [_ap() for _ in range(9)],
        total_aps=10,
    )
    finding = check_field_absent_minority(facts)
    assert finding is not None
    assert finding.key == "payload_field_partial"
    assert finding.severity == SEVERITY_MINOR


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
    assert finding.severity == SEVERITY_MINOR


def test_empty_scan_silent_when_no_known():
    """An empty scan without established known networks is silent."""
    from custom_components.wifi_ssid_monitor.health import check_empty_scan

    assert check_empty_scan(ScanFacts(total_aps=0, established_known=set())) is None


def test_fraction_missing_empty_returns_zero():
    """_fraction_missing returns 0.0 when the normalized list is empty."""
    from custom_components.wifi_ssid_monitor.health import _fraction_missing

    assert _fraction_missing(ScanFacts(normalized=[]), "mac") == 0.0
