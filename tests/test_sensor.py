"""Tests for WiFi SSID Monitor sensors."""

from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.wifi_ssid_monitor.const import DOMAIN
from custom_components.wifi_ssid_monitor.sensor import SENSOR_TYPES, WifiScanSensor


@pytest.mark.asyncio
async def test_sensors(hass: HomeAssistant, mock_config_entry, mock_coordinator):
    """Test sensor states and attributes."""
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.mock_state(hass, ConfigEntryState.LOADED)

    with patch.dict(
        hass.data, {DOMAIN: {mock_config_entry.entry_id: mock_coordinator}}
    ):
        await hass.config_entries.async_forward_entry_setups(
            mock_config_entry, ["sensor"]
        )
        await hass.async_block_till_done()

    # Total Count Sensor
    state = hass.states.get("sensor.wifi_ssid_monitor_wlan0_total_ssid_count")
    assert state
    assert state.state == "2"
    assert state.attributes["ssids"] == ["MyNetwork1", "UnknownNet"]
    assert state.attributes["icon"] == "mdi:wifi"

    # Unknown Count Sensor
    state = hass.states.get("sensor.wifi_ssid_monitor_wlan0_unknown_ssid_count")
    assert state
    assert state.state == "1"
    assert state.attributes["ssids"] == ["UnknownNet"]
    assert state.attributes["icon"] == "mdi:wifi-off"

    # Interface Sensor
    state = hass.states.get("sensor.wifi_ssid_monitor_wlan0_interface")
    assert state
    assert state.state == "wlan0"
    assert state.attributes["icon"] == "mdi:lan"

    # Test Device Info
    sensor = WifiScanSensor(mock_coordinator, mock_config_entry, SENSOR_TYPES[0])
    device_info = sensor.device_info
    assert device_info["identifiers"] == {(DOMAIN, mock_config_entry.entry_id)}
    assert device_info["name"] == "WiFi SSID Monitor wlan0"
    assert device_info["manufacturer"] == "PlayFaster"


@pytest.mark.asyncio
async def test_sensors_no_data(
    hass: HomeAssistant, mock_config_entry, mock_coordinator
):
    """Test sensors when coordinator has no data."""
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.mock_state(hass, ConfigEntryState.LOADED)
    mock_coordinator.data = None

    with patch.dict(
        hass.data, {DOMAIN: {mock_config_entry.entry_id: mock_coordinator}}
    ):
        await hass.config_entries.async_forward_entry_setups(
            mock_config_entry, ["sensor"]
        )
        await hass.async_block_till_done()

    state = hass.states.get("sensor.wifi_ssid_monitor_wlan0_total_ssid_count")
    assert state
    assert state.state == "unknown"
    assert "ssids" not in state.attributes

    state = hass.states.get("sensor.wifi_ssid_monitor_wlan0_unknown_ssid_count")
    assert state
    assert state.state == "unknown"
    assert "ssids" not in state.attributes
