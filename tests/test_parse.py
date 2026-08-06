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


# ---------------------------------------------------------------------------
# Section 6: rounding at parse time.
#
# The trap this must avoid is a "valid input" assertion: `_safe_float("37.2")
# == approx(37.2)` passes unchanged if the rounding is deleted, so it proves
# nothing. The input below has more precision than the helper keeps, which is
# the only shape of test that can fail when `round(...)` is removed.
#
# This matters because it is invisible on a dashboard:
# `suggested_display_precision` hides excess decimals on screen while the
# unrounded value still reaches the recorder and long-term statistics.
# ---------------------------------------------------------------------------


def test_safe_float_rounds_at_parse_time():
    """Excess precision is curtailed where the value is parsed."""
    from custom_components.wifi_ssid_monitor.parse import _safe_float

    # Controllers emit values like this; 3 dp is what reaches the recorder.
    assert _safe_float("99.930600002408") == 99.931
    assert _safe_float(66.6666666666) == 66.667
    assert _safe_float(-42.987654321) == -42.988

    # A value already inside the precision is returned unchanged.
    assert _safe_float("37.25") == 37.25


def test_safe_float_tolerates_absent_and_bad_values():
    """None, empty string and bad types fall back to the default."""
    from custom_components.wifi_ssid_monitor.parse import _safe_float

    assert _safe_float(None) is None
    assert _safe_float("") is None
    assert _safe_float("not-a-number") is None
    assert _safe_float([1, 2, 3]) is None
    assert _safe_float(None, 1.5) == 1.5


def test_safe_int_tolerates_absent_and_bad_values():
    """The integer helper carries the same tolerance contract."""
    from custom_components.wifi_ssid_monitor.parse import _safe_int

    assert _safe_int("48") == 48
    assert _safe_int("48.9") == 48
    assert _safe_int(None) is None
    assert _safe_int("") is None
    assert _safe_int("not-a-number") is None
    assert _safe_int(None, 7) == 7


# ---------------------------------------------------------------------------
# Band edges — every comparison in frequency_to_channel, pinned
# ---------------------------------------------------------------------------
#
# Mutation testing found nine surviving mutants in `frequency_to_channel`
# alone: every `<=` and `>=` bound could move by one, and every offset and
# divisor could change, without a single test noticing. The existing table
# above samples the middle of each band, which is exactly where an off-by-one
# is invisible.
#
# A misplaced edge is not cosmetic. Widening 2.4 GHz by one channel makes a
# 5 GHz radio report as 2.4 GHz, and the band filter then hides a network the
# user asked to see. Narrowing one drops a legitimate AP to "band unknown".


@pytest.mark.parametrize(
    ("mhz", "band"),
    [
        # 2.4 GHz: the contiguous run, then channel 14 as a separate island.
        (2411, None),
        (2412, "2.4 GHz"),
        (2472, "2.4 GHz"),
        (2473, None),
        (2483, None),
        (2484, "2.4 GHz"),
        (2485, None),
        # 5 GHz.
        (5149, None),
        (5150, "5 GHz"),
        (5895, "5 GHz"),
        (5896, None),
        # The gap between the 5 GHz and 6 GHz allocations is real, not an
        # oversight — 5896-5924 belongs to neither and must stay unknown.
        (5924, None),
        # 6 GHz.
        (5925, "6 GHz"),
        (7125, "6 GHz"),
        (7126, None),
    ],
)
def test_every_band_edge_is_exact(mhz, band):
    """Each band boundary is asserted on both sides, one MHz apart.

    Pinning the value inside the band proves it is included; pinning the value
    one MHz outside proves the bound has not been widened. Both are needed —
    either alone leaves the edge free to move in one direction.
    """
    assert frequency_to_channel(mhz)[1] == band


@pytest.mark.parametrize(
    ("mhz", "channel"),
    [
        # (freq - 2407) // 5 across the whole 2.4 GHz run.
        (2412, 1),
        (2437, 6),
        (2472, 13),
        (2484, 14),
        # (freq - 5000) // 5 across the whole 5 GHz run.
        (5150, 30),
        (5180, 36),
        (5895, 179),
        # (freq - 5950) // 5 in the 6 GHz run, from channel 1 upward.
        (5955, 1),
        (6175, 45),
        (7115, 233),
    ],
)
def test_channel_arithmetic_is_pinned_at_both_ends_of_each_band(mhz, channel):
    """The offset and divisor in each band's formula are fixed by two points.

    One sample cannot distinguish a wrong offset from a wrong divisor — both
    produce the right answer somewhere. Two points per band, as far apart as
    the band allows, pin the line.
    """
    assert frequency_to_channel(mhz)[0] == channel


@pytest.mark.parametrize("mhz", [2412, 2484, 5150, 5935, 5955, 7115])
def test_a_recognised_frequency_never_returns_a_half_answer(mhz):
    """Channel and band are decided together and must both be present.

    A frequency that is in a band but yields no channel — or the reverse —
    means the range test and the arithmetic have drifted apart.
    """
    channel, band = frequency_to_channel(mhz)
    assert channel is not None
    assert band is not None


# ---------------------------------------------------------------------------
# normalize_signal — the sign test and the clamp
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected_pct", "expected_unit"),
    [
        # The sign test picks the unit. Zero is a percentage, not dBm: a
        # `<= 0` here would route a legitimate "no signal" reading through the
        # dBm conversion and report it as 100%.
        (0, 0, "percent"),
        (1, 1, "percent"),
        (-1, 100, "dBm"),
        # The clamp holds at both ends and does not clip a valid reading.
        (100, 100, "percent"),
        (101, 100, "percent"),
        (999, 100, "percent"),
    ],
)
def test_normalize_signal_boundaries(raw, expected_pct, expected_unit):
    """The zero crossing and the 0-100 clamp are both exact."""
    pct, _, unit = normalize_signal(raw)
    assert (pct, unit) == (expected_pct, expected_unit)


@pytest.mark.parametrize(
    ("raw", "expected"), [(0.4, 0), (0.5, 0), (0.6, 1), (99.5, 100), (99.4, 99)]
)
def test_normalize_signal_rounds_rather_than_truncates(raw, expected):
    """A fractional percentage rounds; truncation would bias every reading low.

    ``round`` is banker's rounding, so 0.5 goes to 0 and 99.5 to 100. That is
    the behaviour, and pinning it stops a change to ``int()`` passing quietly.
    """
    assert normalize_signal(raw)[0] == expected


# ---------------------------------------------------------------------------
# history_key — which branch decides identity
# ---------------------------------------------------------------------------


def test_history_key_prefers_the_ssid_only_when_not_hidden():
    """A named, visible network keys on its SSID."""
    assert (
        history_key({"hidden": False, "ssid": "HomeNet", "mac": "AA:BB"}) == "HomeNet"
    )


@pytest.mark.parametrize(
    "network",
    [
        {"hidden": True, "ssid": "HomeNet", "mac": "AA:BB"},
        {"hidden": False, "ssid": None, "mac": "AA:BB"},
        {"hidden": False, "ssid": "", "mac": "AA:BB"},
    ],
)
def test_history_key_falls_back_to_the_bssid(network):
    """Hidden, or unnamed, both route to the MAC — the `and` needs both sides.

    Flipping the conjunction to `or`, or dropping either half, still passes a
    test that only checks the happy path. A hidden network keyed on a spoofable
    SSID is how two APs merge into one history entry.
    """
    assert history_key(network) == "hidden:AA:BB"


def test_history_key_with_neither_a_name_nor_a_mac():
    """Nothing to key on falls back to the shared label rather than raising."""
    assert history_key({"hidden": True, "ssid": None, "mac": None}) == "[hidden]"


# ---------------------------------------------------------------------------
# 6 GHz channel numbering — the two places the formula alone is wrong
# ---------------------------------------------------------------------------
#
# IEEE 802.11ax D6.1 27.3.22.2 defines channel 2 at 5935 MHz, BELOW channel 1
# at 5955, as an explicit exception to `(freq - 5950) / 5`. Linux cfg80211
# special-cases the same value in `ieee80211_freq_khz_to_channel`.
#
# And the band opens at 5925 while the lowest channel centre is 5955 and the
# highest is 7115 (channel 233), though the band runs to 7125. So a frequency
# can sit inside the band with no channel of its own, at either end.


def test_6ghz_channel_2_is_the_documented_exception():
    """5935 MHz is channel 2, which the formula cannot produce.

    `(5935 - 5950) // 5` is -3. Channel 2 sits below channel 1 and is defined
    separately in the standard, so it has to be handled as a literal.
    """
    assert frequency_to_channel(5935) == (2, "6 GHz")


@pytest.mark.parametrize("mhz", [5925, 5930, 5940, 5950, 5954, 7120, 7125])
def test_a_6ghz_frequency_with_no_channel_reports_the_band_only(mhz):
    """Inside the band, outside the channel range: band known, channel unknown.

    These are the frequencies the arithmetic gets wrong. Below 5955 it yields
    zero or a negative channel; above 7115 it yields a channel past 233. Both
    are numbers no radio can be on.

    Reporting the band and leaving the channel `None` is what the module's own
    rule 1 requires — a field that cannot be determined becomes `None`, and
    `normalize_access_point` then falls back to any explicit `channel` the
    Supervisor supplied. Inventing a number denies that fallback the chance.
    """
    channel, band = frequency_to_channel(mhz)
    assert band == "6 GHz"
    assert channel is None


@pytest.mark.parametrize(
    ("mhz", "channel"), [(5955, 1), (5975, 5), (6175, 45), (7115, 233)]
)
def test_6ghz_real_channels_still_resolve(mhz, channel):
    """The channels that do exist are unaffected: 1 at 5955 to 233 at 7115."""
    assert frequency_to_channel(mhz) == (channel, "6 GHz")


def test_no_frequency_anywhere_yields_a_channel_below_one():
    """A channel number is 1 or greater, in every band, or it is None.

    The 6 GHz arithmetic produced -5 through 0 for a whole 30 MHz stretch and
    nothing noticed, because no test asked the one question that covers every
    band at once.
    """
    for mhz in range(2400, 7200):
        channel, _ = frequency_to_channel(mhz)
        assert channel is None or channel >= 1, f"{mhz} MHz gave channel {channel}"
