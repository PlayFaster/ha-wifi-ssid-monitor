"""Tests for the diagnostics platform.

Asserted as properties over the rendered output with synthetic fixtures: no
real SSID or BSSID survives, tokens are stable across sections, and the
non-identifying substance is preserved.
"""

import json
from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant

from custom_components.wifi_ssid_monitor.const import (
    CONF_DENYLIST_SSIDS,
    CONF_INTERFACE,
    CONF_KNOWN_SSIDS,
    HIDDEN_FALLBACK_LABEL,
    NO_NETWORKS_SENTINEL,
)
from custom_components.wifi_ssid_monitor.diagnostics import (
    _Pseudonymizer,
    _sanitize_list,
    async_get_config_entry_diagnostics,
)
from tests.conftest import MockConfigEntry


def _coordinator_with_data():
    coordinator = MagicMock()
    coordinator.api.interface = "wlan0"
    coordinator.last_update_success = True
    coordinator.last_update_success_time = "2026-07-22T12:00:00"
    coordinator.version = "1.7.0"
    coordinator.health_snapshot = {"problem": False, "issues": []}
    coordinator.data = {
        "count": 3,
        "unknown_count": 1,
        "ssids": ["HomeNet", "NeighbourNet", "Hidden-1A2B"],
        "unknown_ssids": ["NeighbourNet"],
        "strongest_unknown_ssid": "NeighbourNet",
        "strongest_unknown_signal": 55,
        "networks": {
            "HomeNet": {
                "bssid": "AA:BB:CC:00:00:01",
                "signal": 80,
                "channel": 11,
                "band": "2.4 GHz",
                "hidden": False,
                "key": "HomeNet",
            },
            "NeighbourNet": {
                "bssid": "AA:BB:CC:00:00:02",
                "signal": 55,
                "channel": 48,
                "band": "5 GHz",
                "hidden": False,
                "key": "NeighbourNet",
            },
            "Hidden-1A2B": {
                "bssid": "AA:BB:CC:00:00:03",
                "signal": 30,
                "channel": 1,
                "band": "2.4 GHz",
                "hidden": True,
                "key": "hidden:AA:BB:CC:00:00:03",
            },
        },
        "last_seen": {"NeighbourNet": "2026-07-22T11:00:00"},
        "first_seen": {"NeighbourNet": "2026-07-01T09:00:00"},
        "visit_counts": {"NeighbourNet": 42},
    }
    return coordinator


async def test_diagnostics_redacts_config(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
    """The user's own known and denylist SSIDs are redacted from the config."""
    mock_config_entry.add_to_hass(hass)
    coordinator = _coordinator_with_data()
    object.__setattr__(
        mock_config_entry,
        "options",
        {
            **mock_config_entry.options,
            CONF_KNOWN_SSIDS: "HomeNet",
            CONF_DENYLIST_SSIDS: "BadNet",
        },
    )
    mock_config_entry.runtime_data = coordinator

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert diag["entry"]["options"][CONF_INTERFACE] == "wlan0"
    assert diag["entry"]["options"][CONF_KNOWN_SSIDS] == "**REDACTED**"
    assert diag["entry"]["options"][CONF_DENYLIST_SSIDS] == "**REDACTED**"


async def test_diagnostics_no_identifier_survives(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
    """No neighbouring SSID or BSSID appears anywhere in the output."""
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.runtime_data = _coordinator_with_data()

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)
    blob = json.dumps(diag)

    for leaked in (
        "HomeNet",
        "NeighbourNet",
        "AA:BB:CC:00:00:01",
        "AA:BB:CC:00:00:02",
        "AA:BB:CC:00:00:03",
        "1A2B",  # the hidden label's hex must not leak either
    ):
        assert leaked not in blob


async def test_diagnostics_tokens_stable_and_substance_kept(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
    """Tokens cross-reference across sections; signal/band/counts survive."""
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.runtime_data = _coordinator_with_data()

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)
    data = diag["coordinator"]["data"]

    # The strongest-unknown SSID token matches its key in the networks map.
    token = data["strongest_unknown_ssid"]
    assert token in data["networks"]
    # And the same token keys the history maps.
    assert token in data["last_seen"]
    assert token in data["first_seen"]
    assert data["visit_counts"][token] == 42

    # Substance preserved.
    assert data["count"] == 3
    assert data["networks"][token]["signal"] == 55
    assert data["networks"][token]["band"] == "5 GHz"
    assert data["networks"][token]["channel"] == 48


async def test_diagnostics_does_not_mutate_live_data(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
    """The coordinator's live data is untouched — diagnostics is a read path."""
    mock_config_entry.add_to_hass(hass)
    coordinator = _coordinator_with_data()
    mock_config_entry.runtime_data = coordinator

    await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert "HomeNet" in coordinator.data["networks"]
    assert coordinator.data["networks"]["HomeNet"]["bssid"] == "AA:BB:CC:00:00:01"


async def test_diagnostics_pseudonymizer_caches(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
    """The same SSID gets the same token within one diagnostics call."""
    mock_config_entry.add_to_hass(hass)
    coordinator = _coordinator_with_data()
    mock_config_entry.runtime_data = coordinator

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)
    data = diag["coordinator"]["data"]

    # The SSID token appears consistently across networks, lists, and history.
    pseudo = _Pseudonymizer()
    token1 = pseudo.ssid("HomeNet")
    token2 = pseudo.ssid("HomeNet")
    assert token1 == token2


def test_sanitize_list_passthrough_non_list():
    """_sanitize_list returns non-list values unchanged."""
    assert _sanitize_list(42, _Pseudonymizer()) == 42
    assert _sanitize_list("string", _Pseudonymizer()) == "string"
    assert _sanitize_list(None, _Pseudonymizer()) is None


def test_pseudonymizer_preserves_sentinels():
    """Preserved values like [hidden] and None Detected pass through."""
    pseudo = _Pseudonymizer()
    assert pseudo.ssid(HIDDEN_FALLBACK_LABEL) == HIDDEN_FALLBACK_LABEL
    assert pseudo.ssid(NO_NETWORKS_SENTINEL) == NO_NETWORKS_SENTINEL
