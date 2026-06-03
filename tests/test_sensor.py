"""Tests for WiFi SSID Monitor sensors."""

from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.wifi_ssid_monitor.const import DOMAIN
from custom_components.wifi_ssid_monitor.sensor import SENSOR_TYPES, WifiScanSensor


@pytest.fixture
def data_initial() -> dict:
    """Return data dict for sensor tests."""
    return {
        "count": 2,
        "ssids": ["MyNetwork1", "UnknownNet"],
        "unknown_ssids": ["UnknownNet"],
        "unknown_count": 1,
        "interface": "wlan0",
        "networks": {
            "MyNetwork1": {"rssi": -50, "channel": 6, "band": "2.4 GHz"},
            "UnknownNet": {"rssi": -70, "channel": 36, "band": "5 GHz"},
        },
        "last_seen": {},
        "strongest_unknown_rssi": -70,
    }


@pytest.mark.asyncio
async def test_sensors(hass: HomeAssistant, mock_config_entry, data_initial):
    """Test sensor states and attributes."""
    mock_config_entry.add_to_hass(hass)
    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    coordinator = mock_config_entry.runtime_data
    coordinator.data = data_initial
    coordinator.last_update_success = True
    coordinator.async_update_listeners()
    await hass.async_block_till_done()

    # Total Count Sensor
    state = hass.states.get("sensor.wifi_ssid_monitor_total_ssid_count")
    assert state
    assert state.state == "2"
    assert state.attributes["ssids"] == ["MyNetwork1", "UnknownNet"]

    assert state.attributes["signal_strengths"] == {
        "MyNetwork1": -50,
        "UnknownNet": -70,
    }
    assert state.attributes["bands"] == {
        "MyNetwork1": "2.4 GHz",
        "UnknownNet": "5 GHz",
    }

    # Unknown Count Sensor
    state = hass.states.get("sensor.wifi_ssid_monitor_unknown_ssid_count")
    assert state
    assert state.state == "1"
    assert state.attributes["ssids"] == ["UnknownNet"]

    assert state.attributes["signal_strengths"] == {"UnknownNet": -70}
    assert state.attributes["bands"] == {"UnknownNet": "5 GHz"}

    # Interface Sensor
    state = hass.states.get("sensor.wifi_ssid_monitor_interface")
    assert state
    assert state.state == "wlan0"

    # Test Device Info
    sensor = WifiScanSensor(coordinator, mock_config_entry, SENSOR_TYPES[0])
    device_info = sensor.device_info
    assert device_info["identifiers"] == {(DOMAIN, mock_config_entry.entry_id)}
    assert device_info["name"] == "WiFi SSID Monitor"
    assert device_info["manufacturer"] == "PlayFaster"

    await coordinator.async_shutdown()


@pytest.mark.asyncio
async def test_sensors_no_data(hass: HomeAssistant, mock_config_entry):
    """Test sensors when coordinator has no data."""
    mock_config_entry.add_to_hass(hass)
    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    coordinator = mock_config_entry.runtime_data
    coordinator.data = None
    coordinator.async_update_listeners()
    await hass.async_block_till_done()

    state = hass.states.get("sensor.wifi_ssid_monitor_total_ssid_count")
    assert state
    assert state.state == "unknown"
    assert "ssids" not in state.attributes

    state = hass.states.get("sensor.wifi_ssid_monitor_unknown_ssid_count")
    assert state
    assert state.state == "unknown"
    assert "ssids" not in state.attributes

    await coordinator.async_shutdown()


@pytest.mark.asyncio
async def test_sensors_edge_cases(hass: HomeAssistant, mock_config_entry, data_initial):
    """Test sensor edge cases for native_value."""
    mock_config_entry.add_to_hass(hass)
    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    coordinator = mock_config_entry.runtime_data
    coordinator.data = data_initial
    coordinator.last_update_success = True
    coordinator.async_update_listeners()
    await hass.async_block_till_done()

    coordinator.data = {"wrong_key": "data"}
    coordinator.async_update_listeners()
    state = hass.states.get("sensor.wifi_ssid_monitor_total_ssid_count")
    assert state.state == "unknown"

    coordinator.data = {"count": None}
    coordinator.async_update_listeners()
    state = hass.states.get("sensor.wifi_ssid_monitor_total_ssid_count")
    assert state.state == "unknown"

    coordinator.data = {"count": -1}
    coordinator.async_update_listeners()
    state = hass.states.get("sensor.wifi_ssid_monitor_total_ssid_count")
    assert state.state == "unknown"

    coordinator.data = {"count": 1000}
    coordinator.async_update_listeners()
    state = hass.states.get("sensor.wifi_ssid_monitor_total_ssid_count")
    assert state.state == "unknown"

    coordinator.data = {"count": 0}
    coordinator.async_update_listeners()
    state = hass.states.get("sensor.wifi_ssid_monitor_total_ssid_count")
    assert state.state == "0"

    coordinator.data = {"count": 256}
    coordinator.async_update_listeners()
    state = hass.states.get("sensor.wifi_ssid_monitor_total_ssid_count")
    assert state.state == "256"

    coordinator.data = {"count": 257}
    coordinator.async_update_listeners()
    state = hass.states.get("sensor.wifi_ssid_monitor_total_ssid_count")
    assert state.state == "unknown"

    from homeassistant.util import dt as dt_util

    coordinator.last_update_success_time = dt_util.now()
    coordinator.async_update_listeners()
    state = hass.states.get("sensor.wifi_ssid_monitor_last_updated")
    assert state.state != "unknown"

    await coordinator.async_shutdown()


@pytest.mark.asyncio
async def test_sensors_non_numeric_handling(
    hass: HomeAssistant, mock_config_entry, data_initial
):
    """Test that non-numeric values pass through guard band logic."""
    mock_config_entry.add_to_hass(hass)
    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    coordinator = mock_config_entry.runtime_data
    coordinator.data = data_initial
    coordinator.last_update_success = True
    coordinator.async_update_listeners()
    await hass.async_block_till_done()

    state = hass.states.get("sensor.wifi_ssid_monitor_interface")
    assert state is not None
    assert state.state == "wlan0"

    await coordinator.async_shutdown()


@pytest.mark.asyncio
async def test_sensor_last_seen_attributes(
    hass: HomeAssistant, mock_config_entry, data_initial
):
    """Test unknown_count sensor includes last_seen in extra_state_attributes."""
    from homeassistant.util import dt as dt_util

    mock_config_entry.add_to_hass(hass)
    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    coordinator = mock_config_entry.runtime_data
    now = dt_util.now()
    data_initial["last_seen"] = {"UnknownNet": now}
    coordinator.data = data_initial
    coordinator.last_update_success = True
    coordinator.async_update_listeners()
    await hass.async_block_till_done()

    state = hass.states.get("sensor.wifi_ssid_monitor_unknown_ssid_count")
    assert state is not None
    assert state.state == "1"
    assert "last_seen" in state.attributes
    assert isinstance(state.attributes["last_seen"], dict)
    assert "UnknownNet" in state.attributes["last_seen"]

    await coordinator.async_shutdown()
