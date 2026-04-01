from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.wifi_scan_ssid.const import DOMAIN


@pytest.mark.asyncio
async def test_sensors(hass: HomeAssistant, mock_config_entry, mock_coordinator):
    """Test sensor states and attributes."""
    mock_config_entry.add_to_hass(hass)

    with patch.dict(
        hass.data, {DOMAIN: {mock_config_entry.entry_id: mock_coordinator}}
    ):
        assert await hass.config_entries.async_forward_entry_setups(
            mock_config_entry, ["sensor"]
        )
        await hass.async_block_till_done()

    # Total Count Sensor
    state = hass.states.get("sensor.wifi_scan_wlan0_total_count")
    assert state
    assert state.state == "2"
    assert state.attributes["ssids"] == ["MyNetwork1", "UnknownNet"]
    assert state.attributes["icon"] == "mdi:wifi"

    # Unknown Count Sensor
    state = hass.states.get("sensor.wifi_scan_wlan0_unknown_count")
    assert state
    assert state.state == "1"
    assert state.attributes["ssids"] == ["UnknownNet"]
    assert state.attributes["icon"] == "mdi:wifi-off"


@pytest.mark.asyncio
async def test_sensors_no_data(
    hass: HomeAssistant, mock_config_entry, mock_coordinator
):
    """Test sensors when coordinator has no data."""
    mock_config_entry.add_to_hass(hass)
    mock_coordinator.data = None

    with patch.dict(
        hass.data, {DOMAIN: {mock_config_entry.entry_id: mock_coordinator}}
    ):
        assert await hass.config_entries.async_forward_entry_setups(
            mock_config_entry, ["sensor"]
        )
        await hass.async_block_till_done()

    state = hass.states.get("sensor.wifi_scan_wlan0_total_count")
    assert state
    assert state.state == "unknown"
    assert "ssids" not in state.attributes

    state = hass.states.get("sensor.wifi_scan_wlan0_unknown_count")
    assert state
    assert state.state == "unknown"
    assert "ssids" not in state.attributes
