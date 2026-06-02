"""Tests for WiFi SSID Monitor sensors."""

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
    mock_config_entry.runtime_data = mock_coordinator

    await hass.config_entries.async_forward_entry_setups(mock_config_entry, ["sensor"])
    await hass.async_block_till_done()

    # Total Count Sensor
    state = hass.states.get("sensor.wifi_ssid_monitor_total_ssid_count")
    assert state
    assert state.state == "2"
    assert state.attributes["ssids"] == ["MyNetwork1", "UnknownNet"]

    # Covers finding ASSERT.2 from recommendations_20260602.md
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

    # Covers finding ASSERT.2 from recommendations_20260602.md
    assert state.attributes["signal_strengths"] == {"UnknownNet": -70}
    assert state.attributes["bands"] == {"UnknownNet": "5 GHz"}

    # Interface Sensor
    state = hass.states.get("sensor.wifi_ssid_monitor_interface")
    assert state
    assert state.state == "wlan0"

    # Test Device Info
    sensor = WifiScanSensor(mock_coordinator, mock_config_entry, SENSOR_TYPES[0])
    device_info = sensor.device_info
    assert device_info["identifiers"] == {(DOMAIN, mock_config_entry.entry_id)}
    assert device_info["name"] == "WiFi SSID Monitor"
    assert device_info["manufacturer"] == "PlayFaster"

    await mock_coordinator.async_shutdown()


@pytest.mark.asyncio
async def test_sensors_no_data(
    hass: HomeAssistant, mock_config_entry, mock_coordinator
):
    """Test sensors when coordinator has no data."""
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.mock_state(hass, ConfigEntryState.LOADED)
    mock_coordinator.data = None
    mock_config_entry.runtime_data = mock_coordinator

    await hass.config_entries.async_forward_entry_setups(mock_config_entry, ["sensor"])
    await hass.async_block_till_done()

    state = hass.states.get("sensor.wifi_ssid_monitor_total_ssid_count")
    assert state
    assert state.state == "unknown"
    assert "ssids" not in state.attributes

    state = hass.states.get("sensor.wifi_ssid_monitor_unknown_ssid_count")
    assert state
    assert state.state == "unknown"
    assert "ssids" not in state.attributes

    await mock_coordinator.async_shutdown()


@pytest.mark.asyncio
async def test_sensors_edge_cases(
    hass: HomeAssistant, mock_config_entry, mock_coordinator
):
    """Test sensor edge cases for native_value."""
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.mock_state(hass, ConfigEntryState.LOADED)
    mock_config_entry.runtime_data = mock_coordinator

    await hass.config_entries.async_forward_entry_setups(mock_config_entry, ["sensor"])
    await hass.async_block_till_done()

    # Test KeyError/AttributeError in value_fn
    # Using an empty dict for count that doesn't have the expected keys
    # Instead of calling async_set_updated_data,
    # we directly update the data to avoid TypeError
    mock_coordinator.data = {"wrong_key": "data"}
    mock_coordinator.async_update_listeners()
    state = hass.states.get("sensor.wifi_ssid_monitor_total_ssid_count")
    assert state.state == "unknown"

    # Test value is None
    mock_coordinator.data = {"count": None}
    mock_coordinator.async_update_listeners()
    state = hass.states.get("sensor.wifi_ssid_monitor_total_ssid_count")
    assert state.state == "unknown"
    state = hass.states.get("sensor.wifi_ssid_monitor_total_ssid_count")
    assert state.state == "unknown"

    # Test min_limit guard band (min_limit=0)
    mock_coordinator.data = {"count": -1}
    mock_coordinator.async_update_listeners()
    state = hass.states.get("sensor.wifi_ssid_monitor_total_ssid_count")
    assert state.state == "unknown"

    # Test max_limit guard band (max_limit=256)
    mock_coordinator.data = {"count": 1000}
    mock_coordinator.async_update_listeners()
    state = hass.states.get("sensor.wifi_ssid_monitor_total_ssid_count")
    assert state.state == "unknown"

    # Test min_limit at exact boundary (count=0) — BVA.3
    mock_coordinator.data = {"count": 0}
    mock_coordinator.async_update_listeners()
    state = hass.states.get("sensor.wifi_ssid_monitor_total_ssid_count")
    assert state.state == "0"

    # Test max_limit at and above boundary (256/257) — BVA.4
    mock_coordinator.data = {"count": 256}
    mock_coordinator.async_update_listeners()
    state = hass.states.get("sensor.wifi_ssid_monitor_total_ssid_count")
    assert state.state == "256"

    mock_coordinator.data = {"count": 257}
    mock_coordinator.async_update_listeners()
    state = hass.states.get("sensor.wifi_ssid_monitor_total_ssid_count")
    assert state.state == "unknown"

    # Test Last Updated
    from homeassistant.util import dt as dt_util

    mock_coordinator.last_update_success_time = dt_util.now()
    mock_coordinator.async_update_listeners()
    state = hass.states.get("sensor.wifi_ssid_monitor_last_updated")
    assert state.state != "unknown"

    await mock_coordinator.async_shutdown()


@pytest.mark.asyncio
async def test_sensors_non_numeric_handling(
    hass: HomeAssistant, mock_config_entry, mock_coordinator
):
    """Test that non-numeric values pass through the guard band logic correctly."""
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.mock_state(hass, ConfigEntryState.LOADED)

    # Use a sensor that returns a string, e.g., 'interface'
    # The guard band logic 'isinstance(value, int | float)' should be False
    mock_config_entry.runtime_data = mock_coordinator
    await hass.config_entries.async_forward_entry_setups(mock_config_entry, ["sensor"])
    await hass.async_block_till_done()

    state = hass.states.get("sensor.wifi_ssid_monitor_interface")
    assert state is not None
    assert state.state == "wlan0"  # Confirms it passed through the guard logic

    await mock_coordinator.async_shutdown()


@pytest.mark.asyncio
async def test_sensor_last_seen_attributes(
    hass: HomeAssistant, mock_config_entry, mock_coordinator
):
    """Test unknown_count sensor includes last_seen in extra_state_attributes."""
    from homeassistant.util import dt as dt_util

    mock_config_entry.add_to_hass(hass)
    mock_config_entry.mock_state(hass, ConfigEntryState.LOADED)

    now = dt_util.now()
    mock_coordinator.data["last_seen"] = {"UnknownNet": now}
    mock_config_entry.runtime_data = mock_coordinator

    await hass.config_entries.async_forward_entry_setups(mock_config_entry, ["sensor"])
    await hass.async_block_till_done()

    state = hass.states.get("sensor.wifi_ssid_monitor_unknown_ssid_count")
    assert state is not None
    assert state.state == "1"
    assert "last_seen" in state.attributes
    assert isinstance(state.attributes["last_seen"], dict)
    assert "UnknownNet" in state.attributes["last_seen"]

    await mock_coordinator.async_shutdown()
