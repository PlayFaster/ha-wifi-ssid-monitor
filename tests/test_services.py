"""Tests for service utility functions."""

import pytest

from custom_components.wifi_ssid_monitor.services import (
    _iso,
    _matches,
    _network_matches_filter,
    _split_terms,
)


def test_split_terms_empty():
    """An empty or None raw string returns an empty list."""
    assert _split_terms(None) == []
    assert _split_terms("") == []


def test_split_terms_normal():
    """A comma-separated string is split and lower-cased."""
    assert _split_terms("Foo, Bar, Baz") == ["foo", "bar", "baz"]


def test_matches_with_terms():
    """_matches returns True when a term is found in the haystack."""
    assert _matches("myhomenetwork", ["home"]) is True
    assert _matches("myhomenetwork", ["office"]) is False


def test_iso_none_for_non_datetime():
    """_iso returns None for values that do not have isoformat."""
    assert _iso(None) is None
    assert _iso(42) is None
    assert _iso("string") is None


def test_resolve_entries_unloaded_entry(hass, mock_config_entry):
    """_resolve_entries raises HomeAssistantError when target entry is not loaded."""
    import pytest

    from custom_components.wifi_ssid_monitor.services import _resolve_entries
    from homeassistant.exceptions import HomeAssistantError

    mock_config_entry.add_to_hass(hass)
    with pytest.raises(HomeAssistantError) as exc_info:
        _resolve_entries(hass, mock_config_entry.entry_id)

    assert exc_info.value.translation_key == "entry_not_loaded"


def test_exception_translations():
    """Verify entry_not_loaded translation key exists in strings.json and en.json."""
    import json
    from pathlib import Path

    base = Path(__file__).parents[1] / "custom_components" / "wifi_ssid_monitor"
    strings = json.loads((base / "strings.json").read_text())
    en = json.loads((base / "translations" / "en.json").read_text())

    assert "entry_not_loaded" in strings["exceptions"]
    assert "entry_not_loaded" in en["exceptions"]


_NET = {"bssid": "AA:BB:CC:00:00:09", "signal": 60, "band": "5 GHz"}


def _matches_filter(label="Cafe", net=None, is_unknown=True, **overrides):
    """Call the predicate with permissive defaults, overriding one filter."""
    args = {
        "scope": "all",
        "band": "all",
        "min_signal": None,
        "keyword": [],
        "exclude": [],
    }
    args.update(overrides)
    return _network_matches_filter(
        label, _NET if net is None else net, is_unknown, **args
    )


@pytest.mark.parametrize(
    ("scope", "is_unknown", "expected"),
    [
        ("unknown", True, True),
        ("unknown", False, False),
        ("known", True, False),
        ("known", False, True),
        ("all", True, True),
        ("all", False, True),
    ],
)
def test_network_matches_filter_scope(scope, is_unknown, expected):
    """Scope keeps unknown, known or every network."""
    assert _matches_filter(scope=scope, is_unknown=is_unknown) is expected


@pytest.mark.parametrize(
    ("band", "expected"),
    [("all", True), ("5", True), ("2.4", False), ("6", False)],
)
def test_network_matches_filter_band(band, expected):
    """A named band keeps only networks reporting that band label."""
    assert _matches_filter(band=band) is expected


@pytest.mark.parametrize(
    ("signal", "min_signal", "expected"),
    [
        (60, None, True),
        (60, 60, True),
        (60, 61, False),
        (None, None, True),
        (None, 0, False),
    ],
)
def test_network_matches_filter_min_signal(signal, min_signal, expected):
    """The minimum is inclusive and a network with no signal never meets one."""
    net = {**_NET, "signal": signal}
    assert _matches_filter(net=net, min_signal=min_signal) is expected


@pytest.mark.parametrize(
    ("keyword", "exclude", "expected"),
    [
        (["cafe"], [], True),
        (["aa:bb:cc:00:00:09"], [], True),
        (["5 ghz"], [], True),
        (["zzz", "cafe"], [], True),
        (["zzz"], [], False),
        ([], ["cafe"], False),
        ([], ["aa:bb:cc"], False),
        ([], ["5 ghz"], False),
        ([], ["zzz"], True),
        (["cafe"], ["5 ghz"], False),
    ],
)
def test_network_matches_filter_keyword_and_exclude(keyword, exclude, expected):
    """Terms match label, BSSID and band, and an exclude beats a keyword."""
    assert _matches_filter(keyword=keyword, exclude=exclude) is expected


def test_network_matches_filter_missing_bssid_adds_no_text():
    """A network with no BSSID contributes nothing to the searched text."""
    net = {"bssid": None, "signal": 60, "band": "5 GHz"}
    assert _matches_filter(net=net, keyword=["none"]) is False
    assert _matches_filter(net=net, keyword=["cafe"]) is True
