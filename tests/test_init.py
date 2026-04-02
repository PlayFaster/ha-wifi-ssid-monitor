"""Tests for WiFi SSID Monitor setup and unload."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.wifi_ssid_monitor.const import DOMAIN


@pytest.mark.asyncio
async def test_setup_unload_entry(hass: HomeAssistant, mock_config_entry):
    """Test setting up and unloading the integration."""
    mock_config_entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.wifi_ssid_monitor.coordinator.WifiScanCoordinator.async_config_entry_first_refresh",
            return_value=None,
        ),
        patch(
            "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
            return_value=[],
        ),
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert DOMAIN in hass.data
    assert mock_config_entry.entry_id in hass.data[DOMAIN]

    # Unload
    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.entry_id not in hass.data.get(DOMAIN, {})


@pytest.mark.asyncio
async def test_async_reload_entry(hass: HomeAssistant, mock_config_entry):
    """Test reloading the entry."""
    mock_config_entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.wifi_ssid_monitor.coordinator.WifiScanCoordinator.async_config_entry_first_refresh",
            return_value=None,
        ),
        patch(
            "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
            return_value=[],
        ),
        patch("homeassistant.config_entries.ConfigEntries.async_reload") as mock_reload,
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Test case 1: Only scan interval changed (No reload, just refresh)
        coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]
        with patch.object(coordinator, "async_request_refresh") as mock_refresh:
            hass.config_entries.async_update_entry(
                mock_config_entry,
                options={**mock_config_entry.options, "scan_interval": 120},
            )
            await hass.async_block_till_done()
            assert mock_reload.call_count == 0
            assert mock_refresh.call_count == 1
            assert coordinator.update_interval == timedelta(seconds=120)

        # Test case 2: Interface changed (Triggers full reload)
        hass.config_entries.async_update_entry(
            mock_config_entry,
            options={
                **mock_config_entry.options,
                "wifi_interface": "wlan1",
            },
        )
        await hass.async_block_till_done()
        mock_reload.assert_called_once_with(mock_config_entry.entry_id)


@pytest.mark.asyncio
async def test_sensor_option_update_no_reload(hass: HomeAssistant, mock_config_entry):
    """Test that sensors correctly reflect updated options without a full reload."""
    mock_config_entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.wifi_ssid_monitor.coordinator.WifiScanCoordinator.async_config_entry_first_refresh",
            return_value=None,
        ),
        patch(
            "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
            return_value=[],
        ),
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Initial scan interval should be 60 (from conftest)
        coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]
        assert coordinator.update_interval == timedelta(seconds=60)

        # Change scan interval via options
        hass.config_entries.async_update_entry(
            mock_config_entry,
            options={**mock_config_entry.options, "scan_interval": 300},
        )
        await hass.async_block_till_done()

        # Verify coordinator updated without full reload
        assert coordinator.update_interval == timedelta(seconds=300)

        # Verify number entity (Scan Interval) correctly reads the new value
        state = hass.states.get("number.wifi_ssid_monitor_wlan0_scan_interval")
        assert state
        assert state.state == "5"  # 300 / 60


@pytest.mark.asyncio
async def test_setup_entry_failure(hass: HomeAssistant, mock_config_entry):
    """Test setup entry failure."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.coordinator.WifiScanCoordinator.async_config_entry_first_refresh",
        side_effect=Exception("Failed to refresh"),
    ):
        assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.entry_id not in hass.data.get(DOMAIN, {})
