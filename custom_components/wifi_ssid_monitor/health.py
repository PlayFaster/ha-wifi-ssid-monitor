"""Self-diagnosis checks for WiFi SSID Monitor.

The failure this module exists for is not "the Supervisor is unreachable" —
Home Assistant already surfaces that. It is the fetch that *succeeds* while the
data underneath has changed shape or meaning, which is exactly what happened
when the Supervisor payload moved from ``channel`` to ``frequency`` and the
band filter silently began matching nothing.

Every check is a small pure function over a snapshot of the scan, so adding a
future contract check is a one-line addition to ``CHECKS``.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

_LOGGER = logging.getLogger(__name__)

SEVERITY_MINOR = "minor"
SEVERITY_SERIOUS = "serious"

# Fraction of APs that must be missing a field before it counts as a
# whole-payload change rather than a per-AP quirk.
_MAJORITY = 0.9


@dataclass
class ScanFacts:
    """Everything the checks are allowed to look at.

    Deliberately a flat snapshot rather than the coordinator itself — a check
    cannot reach into live state, so it cannot have side effects on the update
    it is diagnosing.
    """

    total_aps: int = 0
    normalized: list[dict[str, Any]] = field(default_factory=list)
    response_had_ap_key: bool = True
    interface: str = ""
    interface_present: bool | None = None
    signal_unit: str | None = None
    baseline_signal_unit: str | None = None
    established_known: set[str] = field(default_factory=set)
    seen_keys: set[str] = field(default_factory=set)
    scans_completed: int = 0


@dataclass
class Finding:
    """One detected problem."""

    key: str
    severity: str
    message: str
    repair: str | None = None


CheckFn = Callable[[ScanFacts], Finding | None]


def _fraction_missing(facts: ScanFacts, field_name: str) -> float:
    if not facts.normalized:
        return 0.0
    missing = sum(1 for n in facts.normalized if n.get(field_name) is None)
    return missing / len(facts.normalized)


def check_interface_missing(facts: ScanFacts) -> Finding | None:
    """Flag when the configured interface is no longer reported."""
    if facts.interface_present is False:
        return Finding(
            key="interface_missing",
            severity=SEVERITY_SERIOUS,
            message=(
                f"The configured interface '{facts.interface}' is no longer "
                "reported by the Supervisor."
            ),
            repair="interface_missing",
        )
    return None


def check_signal_unit_flip(facts: ScanFacts) -> Finding | None:
    """Flag when the signal unit changed from what was previously observed.

    A flip between percentage and dBm silently inverts the meaning of the
    proximity threshold, so it is worth a repair rather than a log line.
    """
    if facts.signal_unit is None or facts.baseline_signal_unit is None:
        return None
    if facts.signal_unit == facts.baseline_signal_unit:
        return None
    return Finding(
        key="signal_format_changed",
        severity=SEVERITY_SERIOUS,
        message=(
            f"Signal values changed from {facts.baseline_signal_unit} to "
            f"{facts.signal_unit}; check the Proximity Threshold."
        ),
        repair="signal_format_changed",
    )


def check_response_shape(facts: ScanFacts) -> Finding | None:
    """Flag when the response parsed but carried no access-point list."""
    if facts.response_had_ap_key:
        return None
    return Finding(
        key="payload_no_ap_list",
        severity=SEVERITY_SERIOUS,
        message=(
            "The Supervisor response contained no 'accesspoints' list. The API "
            "contract may have changed; check for an integration update."
        ),
    )


def check_field_absent_everywhere(facts: ScanFacts) -> Finding | None:
    """Flag when an expected field is missing across every access point."""
    if not facts.normalized:
        return None
    absent = [
        name
        for name in ("mac", "signal_pct")
        if _fraction_missing(facts, name) >= _MAJORITY
    ]
    if not absent:
        return None
    return Finding(
        key="payload_field_missing",
        severity=SEVERITY_SERIOUS,
        message=(
            f"Expected field(s) {', '.join(absent)} absent from all scanned "
            "networks. The component may be degraded; check for an update."
        ),
    )


def check_band_unresolved(facts: ScanFacts) -> Finding | None:
    """Band could not be derived — the signature of the frequency-key change."""
    if not facts.normalized:
        return None
    fraction = _fraction_missing(facts, "band")
    if fraction >= _MAJORITY:
        return Finding(
            key="band_unresolved_all",
            severity=SEVERITY_SERIOUS,
            message=(
                "No scanned network resolved to a band. The frequency field may "
                "have changed shape; band filtering is unreliable."
            ),
        )
    if fraction > 0:
        return Finding(
            key="band_unresolved_some",
            severity=SEVERITY_MINOR,
            message=(
                f"{int(fraction * 100)}% of networks reported a frequency "
                "outside the known 2.4/5/6 GHz ranges."
            ),
        )
    return None


def check_field_absent_minority(facts: ScanFacts) -> Finding | None:
    """Flag when a field is missing on some but not all access points."""
    if not facts.normalized:
        return None
    partial = [
        name
        for name in ("mac", "signal_pct")
        if 0 < _fraction_missing(facts, name) < _MAJORITY
    ]
    if not partial:
        return None
    return Finding(
        key="payload_field_partial",
        severity=SEVERITY_MINOR,
        message=f"Field(s) {', '.join(partial)} missing on some networks.",
    )


def check_known_network_canary(facts: ScanFacts) -> Finding | None:
    """Every established known network vanished at once.

    One known network disappearing is ordinary — someone powered off an AP.
    *All* of them disappearing together is not; it is the signature of the
    interface going away or a filter excluding everything. Requiring the whole
    set is what keeps this from firing on normal churn.
    """
    if not facts.established_known:
        return None
    if facts.established_known & facts.seen_keys:
        return None
    return Finding(
        key="no_known_networks",
        severity=SEVERITY_SERIOUS,
        message=(
            f"None of the {len(facts.established_known)} usually-visible known "
            "networks were detected. Check the WiFi interface, the band "
            "filters, and the hardware's placement."
        ),
    )


def check_empty_scan(facts: ScanFacts) -> Finding | None:
    """Nothing at all was found, where history says something should be.

    A genuinely quiet location must not trip this, so it is gated on having
    established known networks to compare against.
    """
    if facts.total_aps > 0 or not facts.established_known:
        return None
    return Finding(
        key="empty_scan",
        severity=SEVERITY_MINOR,
        message="The scan returned no networks at all.",
    )


CHECKS: tuple[CheckFn, ...] = (
    check_interface_missing,
    check_signal_unit_flip,
    check_response_shape,
    check_field_absent_everywhere,
    check_band_unresolved,
    check_field_absent_minority,
    check_known_network_canary,
    check_empty_scan,
)


def run_checks(facts: ScanFacts) -> list[Finding]:
    """Run every check, returning the findings that fired.

    A check raising is a bug in the check, not a reason to fail the update, so
    each is isolated — this function is called from the middle of a poll.
    """
    findings: list[Finding] = []
    for check in CHECKS:
        try:
            result = check(facts)
        except Exception:  # noqa: BLE001 - a broken check must never break a scan
            _LOGGER.debug(
                "Health check %s raised; skipping", check.__name__, exc_info=True
            )
            continue
        if result is not None:
            findings.append(result)
    return findings
