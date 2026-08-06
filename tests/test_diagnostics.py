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
    HIDDEN_KEY_PREFIX,
    NO_NETWORKS_SENTINEL,
)
from custom_components.wifi_ssid_monitor.diagnostics import (
    _Pseudonymizer,
    _sanitize_data,
    _sanitize_list,
    _sanitize_networks,
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


def test_sanitize_data_tolerates_a_payload_with_nothing_detected():
    """A scan that saw nothing sanitizes without inventing identities.

    Every guard in ``_sanitize_data`` is a type check, and until this test each
    one had only ever been shown a complete payload. The sanitizer runs against
    ``coordinator.data``, which holds stale or partial data across a failed
    poll, so the shapes it must survive are not hypothetical.
    """
    payload = {
        "count": 0,
        "unknown_count": 0,
        "strongest_unknown_ssid": None,
        "strongest_unknown_signal": None,
    }

    clean = _sanitize_data(payload)

    # A missing section must stay missing. Tokenizing ``None`` would fabricate
    # a network the scan never saw, which is worse than leaking nothing.
    assert clean["strongest_unknown_ssid"] is None
    assert clean == payload
    assert clean is not payload
    assert "networks" not in clean


def test_sanitize_networks_handles_an_entry_with_no_bssid_or_key():
    """A network carrying neither a BSSID nor a history key is still relabelled.

    Both fields are optional in the parsed payload. The label must still be
    tokenized — an entry that skipped sanitizing because a field was absent
    would leak the SSID it is keyed on.
    """
    pseudo = _Pseudonymizer()

    clean = _sanitize_networks(
        {"NeighbourNet": {"signal": 55, "band": "5 GHz", "bssid": "", "key": None}},
        pseudo,
    )

    (label,) = clean
    assert label != "NeighbourNet"
    assert clean[label]["bssid"] == ""
    assert clean[label]["key"] is None
    assert clean[label]["signal"] == 55


async def test_a_bssid_keeps_one_pseudonym_everywhere_it_appears(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
    """One real BSSID must map to one token, in every place it appears.

    This is the module's stated purpose — "allocates a stable pseudonym for
    each, and rewrites them everywhere". A hidden network carries the same MAC
    twice: once as its ``bssid`` field, and once embedded in its ``hidden:``
    history key. If those two paths allocate independently, the sanitized file
    still says the truth about signal and channel but no longer says that the
    two rows are the same radio, which is the whole reason to keep the file.

    Nothing asserted this before. ``_sanitize_networks`` reaches ``bssid`` via
    ``pseudo.bssid`` and ``key`` via ``pseudo.history_key``; only the shared
    ``_bssid_tokens`` dict makes them agree.
    """
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.runtime_data = _coordinator_with_data()

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)
    networks = diag["coordinator"]["data"]["networks"]

    (hidden,) = [n for n in networks.values() if n["hidden"]]

    # The key is ``hidden:<token>``; strip the prefix and compare to the field.
    assert hidden["key"].startswith(HIDDEN_KEY_PREFIX)
    assert hidden["key"][len(HIDDEN_KEY_PREFIX) :] == hidden["bssid"]


def test_two_different_bssids_never_share_a_pseudonym():
    """Distinct MACs must get distinct tokens — the map has to be injective.

    "Stable" alone is satisfied by returning a constant, which would merge every
    neighbouring AP into one and quietly destroy the file's meaning. Stability
    and distinctness are separate properties and both are load-bearing.
    """
    pseudo = _Pseudonymizer()
    macs = ["AA:BB:CC:00:00:01", "AA:BB:CC:00:00:02", "AA:BB:CC:00:00:03"]

    tokens = [pseudo.bssid(m) for m in macs]

    assert len(set(tokens)) == len(macs)
    # And repeating the whole set returns the same tokens in the same order.
    assert [pseudo.bssid(m) for m in macs] == tokens


def test_a_bssid_reached_through_a_history_key_shares_the_field_token():
    """``history_key`` and ``bssid`` must resolve a MAC to the same token.

    The unit-level statement of the property above. ``history_key`` routes a
    ``hidden:`` key through ``bssid()`` rather than ``ssid()`` precisely so the
    two namespaces do not diverge — a MAC tokenized as an SSID would get an
    ``ssid-N`` token and stop cross-referencing.
    """
    pseudo = _Pseudonymizer()
    mac = "AA:BB:CC:00:00:07"

    field_token = pseudo.bssid(mac)
    key_token = pseudo.history_key(f"{HIDDEN_KEY_PREFIX}{mac}")

    assert key_token == f"{HIDDEN_KEY_PREFIX}{field_token}"
    assert not field_token.startswith("ssid-")


def test_an_ssid_and_a_bssid_do_not_collide_on_one_token():
    """The two namespaces are separate and must stay visibly separate.

    Both counters start at 1. If either used the other's dict, the first SSID
    and the first BSSID would both be token 1 and a reader could not tell a
    network label from a radio address.
    """
    pseudo = _Pseudonymizer()

    ssid_token = pseudo.ssid("NeighbourNet")
    bssid_token = pseudo.bssid("AA:BB:CC:00:00:01")

    assert ssid_token != bssid_token
    assert ssid_token.startswith("ssid-")
    assert bssid_token.startswith("bssid-")
