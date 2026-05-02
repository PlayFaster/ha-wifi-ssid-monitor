"""Tests for WiFi SSID Monitor setup and unload."""

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
async def test_async_setup_entry_title_migration(
    hass: HomeAssistant, mock_config_entry
):
    """Test that the config entry title is migrated if it's the only one."""
    from custom_components.wifi_ssid_monitor.const import DEFAULT_NAME

    # Set the old title format
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry, title=f"{DEFAULT_NAME} (wlan0)"
    )

    with (
        patch(
            "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
            return_value=[],
        ),
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # Title should have been migrated
    assert mock_config_entry.title == DEFAULT_NAME


@pytest.mark.asyncio
async def test_async_reload_entry(hass: HomeAssistant, mock_config_entry):
    """Test reloading the entry."""
    mock_config_entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
            return_value=[],
        ),
        patch("homeassistant.config_entries.ConfigEntries.async_reload") as mock_reload,
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        from custom_components.wifi_ssid_monitor.const import CONF_INTERFACE

        # Update options to change interface and trigger reload branch
        new_options = {**mock_config_entry.options, CONF_INTERFACE: "wlan1"}
        hass.config_entries.async_update_entry(mock_config_entry, options=new_options)
        await hass.async_block_till_done()

        mock_reload.assert_called_once_with(mock_config_entry.entry_id)


@pytest.mark.asyncio
async def test_async_reload_entry_options(hass: HomeAssistant, mock_config_entry):
    """Test reloading entry options without full reload."""
    mock_config_entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
            return_value=[],
        ),
        patch(
            "custom_components.wifi_ssid_monitor.coordinator.WifiScanCoordinator.async_refresh"
        ) as mock_refresh,
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Refresh is called once during setup now (background task)
        assert mock_refresh.call_count == 1
        mock_refresh.reset_mock()

        from custom_components.wifi_ssid_monitor.const import (
            CONF_KNOWN_SSIDS,
            CONF_SCAN_INTERVAL,
        )

        coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]

        # Update scan interval
        new_options = {**mock_config_entry.options, CONF_SCAN_INTERVAL: 120}
        hass.config_entries.async_update_entry(mock_config_entry, options=new_options)
        await hass.async_block_till_done()

        assert coordinator.update_interval.total_seconds() == 120
        mock_refresh.assert_not_called()

        # Update known SSIDs
        new_options = {**mock_config_entry.options, CONF_KNOWN_SSIDS: "NewNet"}
        hass.config_entries.async_update_entry(mock_config_entry, options=new_options)
        await hass.async_block_till_done()

        mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_setup_entry_failure(hass: HomeAssistant, mock_config_entry):
    """Test setup entry failure when integration cannot be loaded."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.WifiScanCoordinator",
        side_effect=Exception("Coordinator creation failed"),
    ):
        assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.entry_id not in hass.data.get(DOMAIN, {})
