"""Tests for service utility functions."""

from custom_components.wifi_ssid_monitor.services import _iso, _matches, _split_terms


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
    from homeassistant.exceptions import HomeAssistantError

    from custom_components.wifi_ssid_monitor.services import _resolve_entries

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
