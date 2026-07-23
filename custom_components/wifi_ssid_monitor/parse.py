"""Supervisor payload normalization for WiFi SSID Monitor.

This module is the single boundary between whatever the Supervisor's
``/network/interface/{iface}/accesspoints`` endpoint returns and the shape the
rest of the integration reads. Nothing downstream touches raw keys.

Three rules hold throughout:

1. A missing or unparsable field becomes ``None``. Downstream filters must
   treat ``None`` as *pass*, never *drop* — treating it as drop is what made the
   band filter hide every network once ``channel`` stopped being present.
2. Signal is canonically a **percentage, 0-100**. The Supervisor sends a
   percentage today; a dBm value is converted rather than trusted as-is, and
   the unit actually seen is reported so the health checks can spot a flip.
3. Identity is the BSSID where available. The SSID is a label and may be
   absent, duplicated across radios, or deliberately spoofed.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from .const import (
    BAND_5,
    BAND_6,
    BAND_24,
    HIDDEN_FALLBACK_LABEL,
    HIDDEN_KEY_PREFIX,
)

SIGNAL_UNIT_PERCENT = "percent"
SIGNAL_UNIT_DBM = "dBm"

# Characters that have no business in an SSID: C0/C1 controls, zero-width
# joiners and spaces, and the bidirectional overrides used to disguise a name.
# Written as escapes deliberately — these are invisible in an editor, so a
# literal here would be unreviewable and unmaintainable.
_ANOMALOUS_CHARS = re.compile(
    "["
    "\x00-\x1f"  # C0 controls
    "\x7f-\x9f"  # DEL + C1 controls
    "\u200b-\u200f"  # zero-width space/non-joiner/joiner, LRM, RLM
    "\u202a-\u202e"  # bidirectional embedding and override
    "\u2066-\u2069"  # bidirectional isolates
    "\ufeff"  # zero-width no-break space
    "]"
)
_ANOMALY_REPLACEMENT = "·"


def _safe_int(value: Any, default: int | None = None) -> int | None:
    """Coerce to int, tolerating None, empty strings and bad types."""
    if value is None or value == "":
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float | None = None) -> float | None:
    """Coerce to float rounded to 3 dp, tolerating None and bad types."""
    if value is None or value == "":
        return default
    try:
        return round(float(value), 3)
    except (TypeError, ValueError):
        return default


def dbm_to_pct(dbm: float) -> int:
    """Convert a dBm signal level to NetworkManager's 0-100 percentage.

    Matches the formula NetworkManager itself uses, so a converted value is
    comparable with one the Supervisor reports directly.
    """
    return max(0, min(100, round(2 * (dbm + 100))))


def frequency_to_channel(mhz: Any) -> tuple[int | None, str | None]:
    """Map a frequency in MHz to a (channel, band) pair.

    Returns ``(None, None)`` for anything unrecognised — including ``None`` —
    so an unfamiliar radio degrades to "band unknown" rather than being dropped.
    """
    freq = _safe_int(mhz)
    if freq is None:
        return None, None

    # 2.4 GHz: channels 1-13 are 5 MHz apart from 2412; channel 14 is an outlier.
    if 2412 <= freq <= 2472:
        return (freq - 2407) // 5, BAND_24
    if freq == 2484:
        return 14, BAND_24

    # 5 GHz.
    if 5150 <= freq <= 5895:
        return (freq - 5000) // 5, BAND_5

    # 6 GHz (Wi-Fi 6E / 7).
    if 5925 <= freq <= 7125:
        return (freq - 5950) // 5, BAND_6

    return None, None


def normalize_essid(raw_ssid: Any) -> tuple[str | None, bool]:
    """Return a display-safe SSID and whether it looks anomalous.

    Anomalous means the name carries control, zero-width or bidirectional
    characters — the toolkit for making one network's name render identically
    to another's. Those characters are replaced with a visible marker rather
    than stripped, so the difference is apparent instead of invisible.
    """
    if raw_ssid is None:
        return None, False
    text = str(raw_ssid)
    if not text.strip():
        return None, False

    sanitized = _ANOMALOUS_CHARS.sub(_ANOMALY_REPLACEMENT, text)
    anomalous = sanitized != text

    # A right-to-left mark is caught above; a mixed-direction name without one
    # is legitimate, so only formatting categories count as an anomaly here.
    if not anomalous:
        anomalous = any(unicodedata.category(ch) == "Cf" for ch in text)

    return sanitized, anomalous


def hidden_label(mac: str | None, length: int = 4) -> str:
    """Build the display name for a cloaked network.

    ``Hidden-A2D3`` rather than a shared ``[hidden]`` bucket, so two cloaked
    networks in range are distinguishable. Falls back to the shared label only
    when there is no BSSID to derive from.
    """
    if not mac:
        return HIDDEN_FALLBACK_LABEL
    hexonly = mac.replace(":", "").replace("-", "").upper()
    if not hexonly:
        return HIDDEN_FALLBACK_LABEL
    return f"Hidden-{hexonly[-length:]}"


def normalize_mac(mac: Any) -> str | None:
    """Canonicalize a BSSID to upper-case colon-delimited form."""
    if not mac:
        return None
    text = str(mac).strip().replace("-", ":").upper()
    if not text:
        return None
    return text


def normalize_signal(raw: Any) -> tuple[int | None, Any, str | None]:
    """Return ``(percentage, raw_value, unit_seen)`` for a signal reading.

    The Supervisor reports a 0-100 percentage. A negative value means some
    upstream switched to dBm, which is converted rather than rejected — and the
    unit actually seen is returned so a flip becomes a health finding instead
    of silently wrong data.
    """
    value = _safe_float(raw)
    if value is None:
        return None, raw, None

    if value < 0:
        return dbm_to_pct(value), raw, SIGNAL_UNIT_DBM

    return max(0, min(100, round(value))), raw, SIGNAL_UNIT_PERCENT


def normalize_access_point(raw: dict[str, Any]) -> dict[str, Any]:
    """Turn one raw Supervisor access point into the internal shape.

    Every field is optional in the output. Callers must handle ``None``.
    """
    mac = normalize_mac(raw.get("mac"))
    ssid, anomalous = normalize_essid(raw.get("ssid"))
    hidden = ssid is None

    # Prefer an explicit channel if a future Supervisor ever supplies one;
    # otherwise derive it. Band always comes from the frequency, which is what
    # the Supervisor actually sends.
    channel, band = frequency_to_channel(raw.get("frequency"))
    if channel is None:
        channel = _safe_int(raw.get("channel"))

    signal_pct, signal_raw, signal_unit = normalize_signal(raw.get("signal"))

    return {
        "mac": mac,
        "ssid": ssid,
        "hidden": hidden,
        "label": hidden_label(mac) if hidden else ssid,
        "ssid_anomaly": anomalous or hidden,
        "channel": channel,
        "band": band,
        "signal_pct": signal_pct,
        "signal_raw": signal_raw,
        "signal_unit": signal_unit,
        "mode": raw.get("mode"),
    }


def resolve_hidden_collisions(networks: list[dict[str, Any]]) -> None:
    """Extend colliding ``Hidden-XXXX`` labels to six hex digits, in place.

    Two cloaked APs whose BSSIDs share their last four hex digits would
    otherwise present as one network. Extending only the colliding pair keeps
    the common case short and readable.
    """
    by_label: dict[str, list[dict[str, Any]]] = {}
    for net in networks:
        if net.get("hidden") and net.get("mac"):
            by_label.setdefault(net["label"], []).append(net)

    for entries in by_label.values():
        if len(entries) < 2:
            continue
        for net in entries:
            net["label"] = hidden_label(net["mac"], length=6)


def history_key(network: dict[str, Any]) -> str:
    """Return the persistent identity for a network.

    Named networks key on the SSID: a phone hotspot rotating its MAC keeps one
    identity, a dual-band AP is one network rather than two, and history
    written before BSSIDs were captured still resolves.

    Cloaked networks have no usable name, so they key on the BSSID — which is
    also what makes two hidden APs in range distinguishable.
    """
    if not network.get("hidden") and network.get("ssid"):
        return str(network["ssid"])
    mac = network.get("mac")
    if mac:
        return f"{HIDDEN_KEY_PREFIX}{mac}"
    return HIDDEN_FALLBACK_LABEL
