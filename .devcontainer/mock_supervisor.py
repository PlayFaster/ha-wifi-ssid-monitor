"""Mock Supervisor Network API for development.

**Every literal in here is a claim about what the real Supervisor sends.** Three
diagnostics downloads taken on 2026-08-21 — two x86_64 HAOS boxes and a
Raspberry Pi 4, all HAOS 18.2 / Supervisor 2026.08.0 — are the evidence, and are
summarised in `docs/DEVELOPMENT.md`. Before changing a field here, check it
against those rather than against memory: this file drifted to ``mode: "infra"``
and a single ``wlan0`` interface, and neither was ever what the Supervisor said.

Observed on real hardware, and reproduced below:

===================  ==========================================================
``signal``           0-100 **percentage**, on x86_64 and aarch64 alike. Never
                     dBm in any capture. Real values cluster high, 82-100 for
                     networks in the same building.
``frequency``        Present, in **MHz**, on both architectures.
``mode``             ``"infrastructure"``. Not ``"infra"``.
interface names      ``wlan0`` **and** ``wlp2s0`` — predictable naming is in
                     the wild, so the mock must not offer only the easy name.
interface ``type``   ``"wifi"`` and ``"wireless"``. The Pi reports the latter,
                     which is why ``get_interfaces`` matches both; sending only
                     ``"wifi"`` left that branch unreachable in the container.
===================  ==========================================================

**Not yet confirmed against hardware:** no cloaked network and no zero-width
SSID appeared in any capture, so the ``Hidden-<last4>`` and ``ssid_anomaly``
entries below rest on the single hand test of 2026-08-03. They are kept
deliberately, and kept **static** (see `_variable_signal`), so those labels stay
reproducible.

Two switches, both off by default:

``MOCK_STATIC=1``
    Pins the payload. Set it for `Sensor: Verify HA`, and for any bug
    reproduction that needs the same bytes twice.

``GET /mock/fault?mode=<name>[&scans=N]``
    Injects a failure. ``mode=off`` clears it, no arguments reports the current
    state. Out of band because the integration builds its own fixed URL, and
    stateful so a fault can be **cleared** mid-session — auto-recovery and
    repair deletion are the least observed behaviour in the health system.
"""
# ruff: noqa: S104, INP001
# INP001: a standalone dev-container script, run directly by docker-compose and
# never imported, so it is deliberately not a package. Suppressed here rather
# than in pyproject.toml — that file is synced from dev-workbench and a local
# per-file-ignores entry would be erased on the next sync.

import json
import logging
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

_LOGGER = logging.getLogger(__name__)

# Longer than the integration's API_TIMEOUT_SECONDS (30) so `fault=slow`
# actually reaches the coordinator's asyncio.timeout rather than merely
# being sluggish.
_SLOW_SECONDS = 40

_FAULTS = (
    "unknown_interface",
    "down",
    "dbm",
    "no_ap_key",
    "empty",
    "no_mac",
    "no_mac_partial",
    "no_freq",
    "no_freq_partial",
    "html",
    "slow",
)

# Module-level, because the switch has to outlive one request. HTTPServer is
# single-threaded here, so no lock is needed.
_state: dict[str, object] = {"fault": None, "scans": None}


# --------------------------------------------------------------------------
# Interfaces
# --------------------------------------------------------------------------
#
# Two WiFi adapters, deliberately. One entry per interface is this project's
# supported answer to multiple adapters, and until 2026-08-21 nothing in the
# container had ever shown two at once — leaving the per-interface unique_id
# guard, `_resolve_entries()` fanning actions across entries, and the
# entry-scoped repair ids all unobserved outside pytest.
#
# `wlp2s0` carries `type: "wireless"` so both spellings `get_interfaces`
# accepts are exercised. Sending only "wifi" is how the Pi bug reached users.
_INTERFACES = [
    {"interface": "wlan0", "type": "wifi", "enabled": True},
    {"interface": "wlp2s0", "type": "wireless", "enabled": True},
    {"interface": "eth0", "type": "ethernet", "enabled": True},
]

_WIFI_INTERFACES = {i["interface"] for i in _INTERFACES if i["type"] != "ethernet"}


# --------------------------------------------------------------------------
# Access points, per interface
# --------------------------------------------------------------------------
#
# Distinct payloads per adapter on purpose: two entries showing identical data
# prove nothing about entry separation.
#
# `frequency` drives the band; the name is only a label. `Neighbors_WiFi_5G`
# was defined at 2412 MHz — 2.4 GHz — until 2026-08-21, so its name and its
# band disagreed.
_WLAN0_APS = [
    {
        "mac": "AA:BB:CC:DD:EE:01",
        "ssid": "My_WiFi_24G",
        "signal": 94,
        "frequency": 2412,
        "mode": "infrastructure",
    },
    {
        "mac": "AA:BB:CC:DD:EE:06",
        "ssid": "My_WiFi_5G",
        "signal": 88,
        "frequency": 5180,
        "mode": "infrastructure",
    },
    {
        "mac": "AA:BB:CC:DD:EE:02",
        "ssid": "Neighbors_WiFi_5G",
        "signal": 65,
        "frequency": 5240,
        "mode": "infrastructure",
    },
    {
        "mac": "AA:BB:CC:DD:EE:03",
        "ssid": "Unknown_WiFi_6G",
        "signal": 45,
        "frequency": 6105,
        "mode": "infrastructure",
    },
    {
        "mac": "AA:BB:CC:DD:EE:04",
        "ssid": "",
        "signal": 55,
        "frequency": 2437,
        "mode": "infrastructure",
    },
    {
        "mac": "AA:BB:CC:DD:EE:05",
        "ssid": "Evil\u200bTwin",
        "signal": 84,
        "frequency": 2462,
        "mode": "infrastructure",
    },
]

# The second adapter sees a smaller, overlapping set — the shape a second radio
# in the same building actually produces. `My_WiFi_24G` appears on both with a
# different BSSID, which is what makes per-interface history keys worth having.
_WLP2S0_APS = [
    {
        "mac": "AA:BB:CC:DD:FF:01",
        "ssid": "My_WiFi_24G",
        "signal": 71,
        "frequency": 2437,
        "mode": "infrastructure",
    },
    {
        "mac": "AA:BB:CC:DD:FF:02",
        "ssid": "Cafe_Guest",
        "signal": 38,
        "frequency": 2462,
        "mode": "infrastructure",
    },
]

_APS_BY_INTERFACE = {"wlan0": _WLAN0_APS, "wlp2s0": _WLP2S0_APS}


# --------------------------------------------------------------------------
# Variability
# --------------------------------------------------------------------------
#
# Driven by minute-of-hour rather than a request counter, for two reasons: this
# server is a bare HTTPServer that loses all state on restart, and ":05 looks
# like this" is a claim someone can go and check.
#
# Exactly two networks move. Both `My_WiFi_*` stay fixed — a flapping known set
# trips the canary check and raises repairs continuously — and so do the hidden
# and zero-width entries, whose labels must stay reproducible.

_VARIABLE_SIGNAL_SSID = "Neighbors_WiFi_5G"
_VARIABLE_PRESENCE_SSID = "Unknown_WiFi_6G"

_SIGNAL_LOW = 55
_SIGNAL_HIGH = 95


def _static() -> bool:
    """Return True when the payload must not move."""
    return os.environ.get("MOCK_STATIC", "") not in ("", "0", "false", "False")


def _variable_signal(minute: int) -> int:
    """Triangle wave between the low and high bounds, once per hour.

    Crosses the default proximity threshold of 80 twice an hour in each
    direction, so `proximity_alert` and `strongest_unknown_signal` both move
    within a single session — and so a hysteresis implementation would have
    something real to be judged against.
    """
    # 0 -> 30 -> 0 across the hour, then scaled onto the bounds.
    distance = minute if minute <= 30 else 60 - minute
    span = _SIGNAL_HIGH - _SIGNAL_LOW
    return _SIGNAL_LOW + round(span * distance / 30)


def _access_points(interface: str) -> list[dict]:
    """Return this interface's access points, with variability applied."""
    base = [dict(ap) for ap in _APS_BY_INTERFACE.get(interface, [])]
    if _static():
        return base

    minute = time.localtime().tm_min
    out = []
    for ap in base:
        if ap["ssid"] == _VARIABLE_PRESENCE_SSID and minute >= 30:
            # Absent for the second half of every hour: drives the new_network
            # event, visit_counts, new_24h, last_seen and unknown_count.
            continue
        if ap["ssid"] == _VARIABLE_SIGNAL_SSID:
            ap["signal"] = _variable_signal(minute)
        out.append(ap)
    return out


# --------------------------------------------------------------------------
# Fault injection
# --------------------------------------------------------------------------


def _current_fault() -> str | None:
    """Return the active fault, counting down and clearing an expiring one."""
    fault = _state["fault"]
    if fault is None:
        return None
    scans = _state["scans"]
    if isinstance(scans, int):
        if scans <= 0:
            _LOGGER.info("Fault %s expired; clearing", fault)
            _state["fault"] = None
            _state["scans"] = None
            return None
        _state["scans"] = scans - 1
    return str(fault)


def _apply_fault(aps: list[dict], fault: str) -> list[dict]:
    """Rewrite the access-point list for the payload-shaped faults."""
    if fault == "empty":
        return []
    if fault == "dbm":
        # The Supervisor has never done this in any capture. It is here because
        # `check_signal_unit_flip` exists for the day it does, and because a
        # flip silently inverts the meaning of the proximity threshold.
        return [{**ap, "signal": -(100 - int(ap["signal"]) // 2)} for ap in aps]
    if fault == "no_mac":
        return [{k: v for k, v in ap.items() if k != "mac"} for ap in aps]
    if fault == "no_freq":
        return [{k: v for k, v in ap.items() if k != "frequency"} for ap in aps]
    if fault == "no_mac_partial":
        return [
            {k: v for k, v in ap.items() if k != "mac"} if i == 0 else ap
            for i, ap in enumerate(aps)
        ]
    if fault == "no_freq_partial":
        return [
            {k: v for k, v in ap.items() if k != "frequency"} if i == 0 else ap
            for i, ap in enumerate(aps)
        ]
    return aps


class MockSupervisorHandler(BaseHTTPRequestHandler):
    """Handles mock requests for the Supervisor Network API."""

    def _send_json(self, payload: dict, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    # -- control -----------------------------------------------------------

    def _handle_fault_control(self, query: dict[str, list[str]]) -> None:
        """Set, clear or report the injected fault."""
        mode = (query.get("mode") or [None])[0]

        if mode is None:
            self._send_json(
                {
                    "fault": _state["fault"],
                    "scans_remaining": _state["scans"],
                    "available": list(_FAULTS),
                    "static": _static(),
                }
            )
            return

        if mode in ("off", "none", "clear"):
            _state["fault"] = None
            _state["scans"] = None
            _LOGGER.info("Fault cleared")
            self._send_json({"fault": None})
            return

        if mode not in _FAULTS:
            self._send_json(
                {"error": f"unknown fault {mode!r}", "available": list(_FAULTS)},
                status=400,
            )
            return

        scans_raw = (query.get("scans") or [None])[0]
        scans = int(scans_raw) if scans_raw and scans_raw.isdigit() else None
        _state["fault"] = mode
        _state["scans"] = scans
        _LOGGER.info("Fault %s armed (scans=%s)", mode, scans)
        self._send_json({"fault": mode, "scans_remaining": scans})

    # -- API ---------------------------------------------------------------

    def _handle_access_points(self, path: str) -> None:
        """Serve /network/interface/{iface}/accesspoints."""
        parts = [p for p in path.split("/") if p]
        interface = parts[2] if len(parts) > 2 else ""
        fault = _current_fault()

        # An unrecognised interface 400s whether or not a fault is armed: that
        # is what the real Supervisor does, and until 2026-08-21 this mock
        # returned 200 for any path containing "accesspoints", so a wrong
        # interface name could never fail in the container.
        if fault == "unknown_interface" or interface not in _WIFI_INTERFACES:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"unknown interface")
            return

        if fault == "down":
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"supervisor unavailable")
            return

        if fault == "slow":
            time.sleep(_SLOW_SECONDS)

        if fault == "html":
            # What the Supervisor answers with when it serves an error page:
            # a JSON content type over a body that is not JSON.
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b"<html><body>Gateway Error</body></html>")
            return

        if fault == "no_ap_key":
            # Parses cleanly, carries no `accesspoints` key at all — a contract
            # change, which is a different fact from an empty list.
            self._send_json({"result": "ok", "data": {}})
            return

        aps = _access_points(interface)
        if fault:
            aps = _apply_fault(aps, fault)
        self._send_json({"result": "ok", "data": {"accesspoints": aps}})

    def do_GET(self):
        """Respond to GET requests with fake WiFi data."""
        parsed = urlparse(self.path)
        path = parsed.path

        # Routed before the 404 fallback, and before the API paths, so a
        # control call is never mistaken for a scan.
        if path.startswith("/mock/fault"):
            self._handle_fault_control(parse_qs(parsed.query))
            return

        if "accesspoints" in path:
            self._handle_access_points(path)
            return

        if "network/info" in path:
            self._send_json({"result": "ok", "data": {"interfaces": _INTERFACES}})
            return

        self.send_response(404)
        self.end_headers()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    _LOGGER.info(
        "Starting Mock Supervisor on port 80 (static=%s, interfaces=%s)",
        _static(),
        sorted(_WIFI_INTERFACES),
    )
    httpd = HTTPServer(("0.0.0.0", 80), MockSupervisorHandler)
    httpd.serve_forever()
