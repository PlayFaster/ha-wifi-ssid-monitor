"""Tests for WiFi SSID Monitor binary sensor."""

from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.wifi_ssid_monitor.binary_sensor import (
    HEALTH_DESCRIPTION,
    NEW_NETWORK_DESCRIPTION,
    PROXIMITY_ALERT_DESCRIPTION,
    WifiHealthBinarySensor,
    WifiProximityBinarySensor,
    WifiScanBinarySensor,
)
from custom_components.wifi_ssid_monitor.const import (
    CONF_PROXIMITY_SIGNAL_THRESHOLD,
    DOMAIN,
)


@pytest.fixture
def binary_data() -> dict:
    """Return coordinator data in the current shape."""
    return {
        "count": 2,
        "ssids": ["MyNetwork1", "UnknownNet"],
        "unknown_ssids": ["UnknownNet"],
        "unknown_count": 1,
        "interface": "wlan0",
        "networks": {
            "UnknownNet": {
                "bssid": "AA:BB:CC:00:00:02",
                "signal": 55,
                "channel": 48,
                "band": "5 GHz",
                "hidden": False,
                "key": "UnknownNet",
            },
        },
        "last_seen": {},
        "first_seen": {},
        "visit_counts": {},
        "new_24h": 0,
        "strongest_unknown_signal": 55,
        "strongest_unknown_ssid": "UnknownNet",
        "signal_unit": "percent",
    }


@pytest.mark.asyncio
async def test_binary_sensor_setup(hass: HomeAssistant, mock_config_entry, binary_data):
    """Platform setup and initial states, including the health sensor."""
    mock_config_entry.add_to_hass(hass)
    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    coordinator = mock_config_entry.runtime_data
    coordinator.data = binary_data
    coordinator.last_update_success = True
    coordinator.async_update_listeners()
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.wifi_ssid_monitor_new_network_alert")
    assert state.state == "on"

    # Signal 55 is below the default 80% threshold.
    state = hass.states.get("binary_sensor.wifi_ssid_monitor_proximity_alert")
    assert state.state == "off"

    state = hass.states.get("binary_sensor.wifi_ssid_monitor_integration_health")
    assert state is not None

    await coordinator.async_shutdown()


def test_new_network_is_on_with_unknown(mock_config_entry, mock_coordinator):
    """New-network sensor is on when unknown networks are present."""
    mock_coordinator.data["unknown_count"] = 3
    sensor = WifiScanBinarySensor(
        mock_coordinator, mock_config_entry, NEW_NETWORK_DESCRIPTION
    )
    assert sensor.is_on is True


def test_new_network_off_all_known(mock_config_entry, mock_coordinator):
    """New-network sensor is off when all networks are known."""
    mock_coordinator.data["unknown_count"] = 0
    sensor = WifiScanBinarySensor(
        mock_coordinator, mock_config_entry, NEW_NETWORK_DESCRIPTION
    )
    assert sensor.is_on is False


def test_new_network_off_no_data(mock_config_entry, mock_coordinator):
    """New-network sensor is off with no data."""
    mock_coordinator.data = None
    sensor = WifiScanBinarySensor(
        mock_coordinator, mock_config_entry, NEW_NETWORK_DESCRIPTION
    )
    assert sensor.is_on is False


def test_new_network_unique_id(mock_config_entry, mock_coordinator):
    """New-network unique id is formed from the entry unique id."""
    sensor = WifiScanBinarySensor(
        mock_coordinator, mock_config_entry, NEW_NETWORK_DESCRIPTION
    )
    assert sensor.unique_id == f"{mock_config_entry.unique_id}_new_network"


# --- Proximity (percent scale, higher = closer) ---


def _proximity(entry, coordinator, threshold=None):
    if threshold is not None:
        object.__setattr__(
            entry,
            "options",
            {**entry.options, CONF_PROXIMITY_SIGNAL_THRESHOLD: threshold},
        )
    return WifiProximityBinarySensor(coordinator, entry, PROXIMITY_ALERT_DESCRIPTION)


def test_proximity_off_no_data(mock_config_entry, mock_coordinator):
    """Proximity is off with no data."""
    mock_coordinator.data = None
    assert _proximity(mock_config_entry, mock_coordinator).is_on is False


def test_proximity_off_no_signal(mock_config_entry, mock_coordinator):
    """Proximity is off when no unknown signal is present."""
    mock_coordinator.data["strongest_unknown_signal"] = None
    assert _proximity(mock_config_entry, mock_coordinator).is_on is False


def test_proximity_off_below_threshold(mock_config_entry, mock_coordinator):
    """Proximity is off when the signal is below the default 80%."""
    mock_coordinator.data["strongest_unknown_signal"] = 55
    assert _proximity(mock_config_entry, mock_coordinator).is_on is False


def test_proximity_on_above_threshold(mock_config_entry, mock_coordinator):
    """Proximity is on when the signal exceeds the default 80%."""
    mock_coordinator.data["strongest_unknown_signal"] = 90
    assert _proximity(mock_config_entry, mock_coordinator).is_on is True


def test_proximity_boundary_equal_is_on(mock_config_entry, mock_coordinator):
    """Proximity fires when the signal equals the threshold."""
    mock_coordinator.data["strongest_unknown_signal"] = 70
    assert _proximity(mock_config_entry, mock_coordinator, threshold=70).is_on is True


def test_proximity_boundary_below_is_off(mock_config_entry, mock_coordinator):
    """Proximity does not fire one below the threshold."""
    mock_coordinator.data["strongest_unknown_signal"] = 69
    assert _proximity(mock_config_entry, mock_coordinator, threshold=70).is_on is False


def test_proximity_extra_state_attributes(mock_config_entry, mock_coordinator):
    """Proximity exposes the signal and threshold."""
    mock_coordinator.data["strongest_unknown_signal"] = 55
    sensor = _proximity(mock_config_entry, mock_coordinator, threshold=60)
    attrs = sensor.extra_state_attributes
    assert attrs["strongest_unknown_signal"] == 55
    assert attrs["threshold"] == 60

    mock_coordinator.data = None
    attrs = sensor.extra_state_attributes
    assert attrs["strongest_unknown_signal"] is None
    assert attrs["threshold"] == 60


def test_proximity_unique_id(mock_config_entry, mock_coordinator):
    """Proximity unique id is formed from the entry unique id."""
    sensor = _proximity(mock_config_entry, mock_coordinator)
    assert sensor.unique_id == f"{mock_config_entry.unique_id}_proximity_alert"


# --- Integration Health ---


def test_health_always_available(mock_config_entry, mock_coordinator):
    """The health sensor is available even when the coordinator has failed."""
    mock_coordinator.last_update_success = False
    sensor = WifiHealthBinarySensor(
        mock_coordinator, mock_config_entry, HEALTH_DESCRIPTION
    )
    assert sensor.available is True


def test_health_reflects_snapshot(mock_config_entry, mock_coordinator):
    """The health sensor reads problem/issues from the snapshot."""
    mock_coordinator.health_snapshot = {
        "problem": True,
        "severity": "serious",
        "issues": ["Cannot reach the Supervisor API"],
        "checks_failed": ["supervisor_unreachable"],
        "signal_unit": "percent",
        "last_good_scan": None,
    }
    sensor = WifiHealthBinarySensor(
        mock_coordinator, mock_config_entry, HEALTH_DESCRIPTION
    )
    assert sensor.is_on is True
    attrs = sensor.extra_state_attributes
    assert attrs["severity"] == "serious"
    assert "Cannot reach the Supervisor API" in attrs["issues"]


def test_health_off_when_healthy(mock_config_entry, mock_coordinator):
    """The health sensor is off when the snapshot reports no problem."""
    mock_coordinator.health_snapshot = {"problem": False, "issues": []}
    sensor = WifiHealthBinarySensor(
        mock_coordinator, mock_config_entry, HEALTH_DESCRIPTION
    )
    assert sensor.is_on is False


def test_device_info(mock_config_entry, mock_coordinator):
    """Binary sensors report the shared device info."""
    sensor = WifiScanBinarySensor(
        mock_coordinator, mock_config_entry, NEW_NETWORK_DESCRIPTION
    )
    info = sensor.device_info
    assert info["identifiers"] == {(DOMAIN, mock_config_entry.entry_id)}
    assert info["manufacturer"] == "PlayFaster"
    assert "wlan0" in info["model"]
