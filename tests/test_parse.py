"""Unit tests for the payload normalization layer.

These are pure functions with no Home Assistant dependency, so they document
the exact contract the rest of the integration relies on.
"""

import pytest

from custom_components.wifi_ssid_monitor.parse import (
    dbm_to_pct,
    frequency_to_channel,
    hidden_label,
    history_key,
    normalize_access_point,
    normalize_essid,
    normalize_mac,
    normalize_signal,
    resolve_hidden_collisions,
)


@pytest.mark.parametrize(
    ("dbm", "expected"),
    [(-100, 0), (-75, 50), (-60, 80), (-50, 100), (-30, 100), (-110, 0)],
)
def test_dbm_to_pct(dbm, expected):
    """DBm converts to the NetworkManager percentage and clamps to 0-100."""
    assert dbm_to_pct(dbm) == expected


@pytest.mark.parametrize(
    ("mhz", "channel", "band"),
    [
        (2412, 1, "2.4 GHz"),
        (2462, 11, "2.4 GHz"),
        (2472, 13, "2.4 GHz"),
        (2484, 14, "2.4 GHz"),
        (5180, 36, "5 GHz"),
        (5240, 48, "5 GHz"),
        (5955, 1, "6 GHz"),
        (6175, 45, "6 GHz"),
        (9999, None, None),
        (None, None, None),
        ("not-a-number", None, None),
    ],
)
def test_frequency_to_channel(mhz, channel, band):
    """Frequencies map to the right channel and band; junk degrades to None."""
    assert frequency_to_channel(mhz) == (channel, band)


def test_normalize_signal_percent():
    """A 0-100 value is taken as a percentage as-is."""
    assert normalize_signal(80) == (80, 80, "percent")


def test_normalize_signal_dbm():
    """A negative value is treated as dBm and converted."""
    pct, raw, unit = normalize_signal(-60)
    assert (pct, raw, unit) == (80, -60, "dBm")


def test_normalize_signal_missing():
    """A missing signal is None, not zero."""
    assert normalize_signal(None) == (None, None, None)


def test_normalize_essid_plain():
    """A normal SSID passes through and is not flagged."""
    assert normalize_essid("HomeWiFi") == ("HomeWiFi", False)


def test_normalize_essid_blank_is_hidden():
    """A blank or whitespace SSID is treated as hidden."""
    assert normalize_essid("   ") == (None, False)
    assert normalize_essid(None) == (None, False)


def test_normalize_essid_anomaly():
    """A zero-width character is flagged and replaced with a visible marker."""
    sanitized, anomalous = normalize_essid("Home\u200bWiFi")
    assert anomalous is True
    assert "\u200b" not in sanitized
    assert "·" in sanitized


def test_normalize_mac():
    """MACs canonicalize to upper-case colon form; blanks become None."""
    assert normalize_mac("aa-bb-cc-dd-ee-ff") == "AA:BB:CC:DD:EE:FF"
    assert normalize_mac("") is None
    assert normalize_mac(None) is None


def test_hidden_label():
    """The hidden label is the last four hex of the BSSID; blank falls back."""
    assert hidden_label("AA:BB:CC:DD:EE:FF") == "Hidden-EEFF"
    assert hidden_label(None) == "[hidden]"


def test_resolve_hidden_collisions():
    """Two hidden APs sharing their last four hex extend to six."""
    nets = [
        {"hidden": True, "mac": "AA:BB:CC:11:EE:FF", "label": "Hidden-EEFF"},
        {"hidden": True, "mac": "AA:BB:CC:22:EE:FF", "label": "Hidden-EEFF"},
        {"hidden": True, "mac": "AA:BB:CC:33:00:11", "label": "Hidden-0011"},
    ]
    resolve_hidden_collisions(nets)
    assert nets[0]["label"] == "Hidden-11EEFF"
    assert nets[1]["label"] == "Hidden-22EEFF"
    # The non-colliding one is untouched.
    assert nets[2]["label"] == "Hidden-0011"


def test_history_key_named_uses_ssid():
    """A named network keys on its SSID, immune to a rotating MAC."""
    net = {"hidden": False, "ssid": "PhoneHotspot", "mac": "AA:BB:CC:00:00:99"}
    assert history_key(net) == "PhoneHotspot"


def test_history_key_hidden_uses_bssid():
    """A cloaked network keys on its BSSID so it stays distinct."""
    net = {"hidden": True, "ssid": None, "mac": "AA:BB:CC:00:00:01"}
    assert history_key(net) == "hidden:AA:BB:CC:00:00:01"


def test_history_key_fallback():
    """A network with no SSID and no MAC falls back to the sentinel label."""
    net = {"hidden": True, "ssid": None, "mac": None}
    assert history_key(net) == "[hidden]"


def test_normalize_mac_empty_string():
    """An empty string returns None."""
    assert normalize_mac("") is None
    assert normalize_mac("   ") is None


def test_hidden_label_empty_mac():
    """An empty MAC falls back to the default hidden label."""
    assert hidden_label("") == "[hidden]"
    assert hidden_label("::") == "[hidden]"


def test_safe_float_bad_types():
    """Bad types return None."""
    from custom_components.wifi_ssid_monitor.parse import normalize_signal

    assert normalize_signal("not-a-number") == (None, "not-a-number", None)
    assert normalize_signal([1, 2, 3]) == (None, [1, 2, 3], None)


def test_normalize_access_point_full():
    """A whole AP normalizes to the documented shape."""
    result = normalize_access_point(
        {"mac": "aa:bb:cc:00:00:01", "ssid": "Net", "signal": 72, "frequency": 5240}
    )
    assert result["mac"] == "AA:BB:CC:00:00:01"
    assert result["ssid"] == "Net"
    assert result["hidden"] is False
    assert result["band"] == "5 GHz"
    assert result["channel"] == 48
    assert result["signal_pct"] == 72
    assert result["signal_unit"] == "percent"


def test_normalize_access_point_hidden():
    """A hidden AP gets a Hidden-<last4> label and the anomaly flag."""
    result = normalize_access_point(
        {"mac": "aa:bb:cc:00:00:02", "ssid": "", "signal": 40, "frequency": 2412}
    )
    assert result["hidden"] is True
    assert result["label"] == "Hidden-0002"
    assert result["ssid_anomaly"] is True
