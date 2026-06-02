"""Tests for WiFi SSID Monitor binary sensor."""

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.wifi_ssid_monitor.binary_sensor import (
    NEW_NETWORK_DESCRIPTION,
    PROXIMITY_ALERT_DESCRIPTION,
    WifiProximityBinarySensor,
    WifiScanBinarySensor,
)
from custom_components.wifi_ssid_monitor.const import (
    CONF_PROXIMITY_RSSI_THRESHOLD,
    DOMAIN,
)


@pytest.mark.asyncio
async def test_binary_sensor_setup(
    hass: HomeAssistant, mock_config_entry, mock_coordinator
):
    """Test binary sensor platform setup and initial state."""
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.mock_state(hass, ConfigEntryState.LOADED)
    mock_config_entry.runtime_data = mock_coordinator

    await hass.config_entries.async_forward_entry_setups(
        mock_config_entry, ["binary_sensor"]
    )
    await hass.async_block_till_done()

    # Fixture has unknown_count=1, so sensor should be on
    state = hass.states.get("binary_sensor.wifi_ssid_monitor_new_network_alert")
    assert state
    assert state.state == "on"

    # Covers finding ASSERT.1 from recommendations_20260602.md
    state = hass.states.get("binary_sensor.wifi_ssid_monitor_proximity_alert")
    assert state is not None
    assert state.state == "off"  # strongest_unknown_rssi=-70 < threshold=-60

    await mock_coordinator.async_shutdown()


def test_binary_sensor_is_on_with_unknown_networks(mock_config_entry, mock_coordinator):
    """Test binary sensor is on when unknown networks are detected."""
    mock_coordinator.data["unknown_count"] = 3
    sensor = WifiScanBinarySensor(
        mock_coordinator, mock_config_entry, NEW_NETWORK_DESCRIPTION
    )
    assert sensor.is_on is True


def test_binary_sensor_is_off_all_known(mock_config_entry, mock_coordinator):
    """Test binary sensor is off when all detected networks are known."""
    mock_coordinator.data["unknown_count"] = 0
    sensor = WifiScanBinarySensor(
        mock_coordinator, mock_config_entry, NEW_NETWORK_DESCRIPTION
    )
    assert sensor.is_on is False


def test_binary_sensor_is_off_no_data(mock_config_entry, mock_coordinator):
    """Test binary sensor is off when coordinator has no data yet."""
    mock_coordinator.data = None
    sensor = WifiScanBinarySensor(
        mock_coordinator, mock_config_entry, NEW_NETWORK_DESCRIPTION
    )
    assert sensor.is_on is False


def test_binary_sensor_device_info(mock_config_entry, mock_coordinator):
    """Test binary sensor device information."""
    sensor = WifiScanBinarySensor(
        mock_coordinator, mock_config_entry, NEW_NETWORK_DESCRIPTION
    )
    info = sensor.device_info
    assert info["identifiers"] == {(DOMAIN, mock_config_entry.entry_id)}
    assert info["name"] == "WiFi SSID Monitor"
    assert info["manufacturer"] == "PlayFaster"
    assert "wlan0" in info["model"]


def test_binary_sensor_unique_id(mock_config_entry, mock_coordinator):
    """Test binary sensor unique ID is correctly formed."""
    sensor = WifiScanBinarySensor(
        mock_coordinator, mock_config_entry, NEW_NETWORK_DESCRIPTION
    )
    assert sensor.unique_id == f"{mock_config_entry.unique_id}_new_network"


# --- Proximity binary sensor tests (COMBO.3) ---


def test_proximity_sensor_is_off_no_data(mock_config_entry, mock_coordinator):
    """Test proximity sensor is off when coordinator data is None."""
    mock_coordinator.data = None
    sensor = WifiProximityBinarySensor(
        mock_coordinator, mock_config_entry, PROXIMITY_ALERT_DESCRIPTION
    )
    assert sensor.is_on is False


def test_proximity_sensor_is_off_no_rssi(mock_config_entry, mock_coordinator):
    """Test proximity sensor is off when strongest_unknown_rssi is None."""
    mock_coordinator.data["strongest_unknown_rssi"] = None
    sensor = WifiProximityBinarySensor(
        mock_coordinator, mock_config_entry, PROXIMITY_ALERT_DESCRIPTION
    )
    assert sensor.is_on is False


def test_proximity_sensor_is_off_below_threshold(mock_config_entry, mock_coordinator):
    """Test proximity sensor is off when RSSI is below default threshold."""
    mock_coordinator.data["strongest_unknown_rssi"] = -70
    sensor = WifiProximityBinarySensor(
        mock_coordinator, mock_config_entry, PROXIMITY_ALERT_DESCRIPTION
    )
    assert sensor.is_on is False


def test_proximity_sensor_is_on_above_threshold(mock_config_entry, mock_coordinator):
    """Test proximity sensor is on when RSSI exceeds default threshold."""
    mock_coordinator.data["strongest_unknown_rssi"] = -50
    sensor = WifiProximityBinarySensor(
        mock_coordinator, mock_config_entry, PROXIMITY_ALERT_DESCRIPTION
    )
    assert sensor.is_on is True


@pytest.mark.asyncio
async def test_proximity_sensor_custom_threshold(
    hass, mock_config_entry, mock_coordinator
):
    """Test proximity sensor with custom RSSI threshold at boundary equality."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, CONF_PROXIMITY_RSSI_THRESHOLD: -40},
    )
    mock_coordinator.data["strongest_unknown_rssi"] = -45
    sensor = WifiProximityBinarySensor(
        mock_coordinator, mock_config_entry, PROXIMITY_ALERT_DESCRIPTION
    )
    assert sensor.is_on is False

    mock_coordinator.data["strongest_unknown_rssi"] = -40
    assert sensor.is_on is True


@pytest.mark.asyncio
async def test_proximity_sensor_extra_state_attributes(
    hass, mock_config_entry, mock_coordinator
):
    """Test proximity sensor extra state attributes with and without data."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, CONF_PROXIMITY_RSSI_THRESHOLD: -60},
    )
    mock_coordinator.data["strongest_unknown_rssi"] = -55
    sensor = WifiProximityBinarySensor(
        mock_coordinator, mock_config_entry, PROXIMITY_ALERT_DESCRIPTION
    )
    assert sensor.extra_state_attributes == {
        "strongest_unknown_rssi": -55,
        "threshold": -60,
    }

    mock_coordinator.data = None
    assert sensor.extra_state_attributes == {
        "strongest_unknown_rssi": None,
        "threshold": -60,
    }


def test_proximity_sensor_device_info(mock_config_entry, mock_coordinator):
    """Test proximity sensor device_info contains identifiers, manufacturer, and model."""  # noqa: E501
    sensor = WifiProximityBinarySensor(
        mock_coordinator, mock_config_entry, PROXIMITY_ALERT_DESCRIPTION
    )
    info = sensor.device_info
    assert info["identifiers"] == {(DOMAIN, mock_config_entry.entry_id)}
    assert "PlayFaster" in info["manufacturer"]
    assert "wlan0" in info["model"]  # model includes interface


def test_proximity_sensor_unique_id(mock_config_entry, mock_coordinator):
    """Test proximity sensor unique ID is correctly formed."""
    sensor = WifiProximityBinarySensor(
        mock_coordinator, mock_config_entry, PROXIMITY_ALERT_DESCRIPTION
    )
    assert sensor.unique_id == f"{mock_config_entry.unique_id}_proximity_alert"


# --- Proximity boundary value tests (BVA.2) ---


@pytest.mark.asyncio
async def test_proximity_sensor_is_on_at_boundary_equal(
    hass, mock_config_entry, mock_coordinator
):
    """Test proximity sensor is on when RSSI equals threshold exactly."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, CONF_PROXIMITY_RSSI_THRESHOLD: -60},
    )
    mock_coordinator.data["strongest_unknown_rssi"] = -60
    sensor = WifiProximityBinarySensor(
        mock_coordinator, mock_config_entry, PROXIMITY_ALERT_DESCRIPTION
    )
    assert sensor.is_on is True


@pytest.mark.asyncio
async def test_proximity_sensor_is_off_one_below_boundary(
    hass, mock_config_entry, mock_coordinator
):
    """Test proximity sensor is off when RSSI is one below threshold."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, CONF_PROXIMITY_RSSI_THRESHOLD: -60},
    )
    mock_coordinator.data["strongest_unknown_rssi"] = -61
    sensor = WifiProximityBinarySensor(
        mock_coordinator, mock_config_entry, PROXIMITY_ALERT_DESCRIPTION
    )
    assert sensor.is_on is False


@pytest.mark.asyncio
async def test_proximity_sensor_is_on_one_above_boundary(
    hass, mock_config_entry, mock_coordinator
):
    """Test proximity sensor is on when RSSI is one above threshold."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, CONF_PROXIMITY_RSSI_THRESHOLD: -60},
    )
    mock_coordinator.data["strongest_unknown_rssi"] = -59
    sensor = WifiProximityBinarySensor(
        mock_coordinator, mock_config_entry, PROXIMITY_ALERT_DESCRIPTION
    )
    assert sensor.is_on is True
