"""Tests for WiFi SSID Monitor binary sensor."""

from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.wifi_ssid_monitor.binary_sensor import (
    NEW_NETWORK_DESCRIPTION,
    WifiScanBinarySensor,
)
from custom_components.wifi_ssid_monitor.const import DOMAIN


@pytest.mark.asyncio
async def test_binary_sensor_setup(
    hass: HomeAssistant, mock_config_entry, mock_coordinator
):
    """Test binary sensor platform setup and initial state."""
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.mock_state(hass, ConfigEntryState.LOADED)

    with patch.dict(
        hass.data, {DOMAIN: {mock_config_entry.entry_id: mock_coordinator}}
    ):
        await hass.config_entries.async_forward_entry_setups(
            mock_config_entry, ["binary_sensor"]
        )
        await hass.async_block_till_done()

    # Fixture has unknown_count=1, so sensor should be on
    state = hass.states.get("binary_sensor.wifi_ssid_monitor_new_network_alert")
    assert state
    assert state.state == "on"

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
