"""Tests for WiFi SSID Monitor number platform."""

import asyncio
from contextlib import suppress
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState

from custom_components.wifi_ssid_monitor import async_reload_entry
from custom_components.wifi_ssid_monitor.const import CONF_SCAN_INTERVAL, DOMAIN
from custom_components.wifi_ssid_monitor.number import (
    SCAN_INTERVAL_DESCRIPTION,
    WifiScanIntervalNumber,
)


@pytest.mark.asyncio
async def test_number_setup_and_update(hass, mock_config_entry, mock_coordinator):
    """Test the scan interval number entity setup and value update."""
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.mock_state(hass, ConfigEntryState.LOADED)

    # Setup environment for the reload listener
    mock_config_entry.runtime_data = mock_coordinator
    mock_config_entry.add_update_listener(async_reload_entry)

    # CONF_SCAN_INTERVAL is 60 in conftest, so initial_value should be 1
    number = WifiScanIntervalNumber(
        mock_coordinator, mock_config_entry, SCAN_INTERVAL_DESCRIPTION, 1
    )
    number.hass = hass
    number.async_write_ha_state = MagicMock()
    mock_coordinator.async_request_refresh = AsyncMock()

    # Test setting a new value via direct call to simulate service
    with patch("asyncio.sleep", AsyncMock()):
        await number.async_set_native_value(15)
        # We MUST await the background task created by the entity
        if number._refresh_task:
            await number._refresh_task
        await hass.async_block_till_done()

    # Verify coordinator update
    assert mock_coordinator.update_interval == timedelta(minutes=15)
    # Note: integration does NOT trigger refresh on interval change ONLY
    mock_coordinator.async_request_refresh.assert_not_called()

    # Verify persistence in options
    assert mock_config_entry.options[CONF_SCAN_INTERVAL] == 900  # 15 * 60


@pytest.mark.asyncio
async def test_number_debounce_cancellation(hass, mock_config_entry, mock_coordinator):
    """Test that rapid changes cancel previous update tasks."""
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.mock_state(hass, ConfigEntryState.LOADED)

    mock_config_entry.runtime_data = mock_coordinator
    mock_config_entry.add_update_listener(async_reload_entry)

    number = WifiScanIntervalNumber(
        mock_coordinator, mock_config_entry, SCAN_INTERVAL_DESCRIPTION, 10
    )
    number.hass = hass
    number.async_write_ha_state = MagicMock()

    with patch("asyncio.sleep", AsyncMock()):
        # First update
        await number.async_set_native_value(20)
        task1 = number._refresh_task

        # Immediate second update should cancel the first
        await number.async_set_native_value(30)
        task2 = number._refresh_task

        # The two calls must produce distinct tasks
        assert task1 is not task2

        # Let task2 finish
        await task2
        await hass.async_block_till_done()

    # Only the final value (30) should be applied — not the first (20)
    assert mock_coordinator.update_interval == timedelta(minutes=30)


@pytest.mark.asyncio
async def test_number_apply_error(hass, mock_config_entry, mock_coordinator):
    """Test error handling during interval application."""
    number = WifiScanIntervalNumber(
        mock_coordinator, mock_config_entry, SCAN_INTERVAL_DESCRIPTION, 10
    )
    number.hass = hass
    number.async_write_ha_state = MagicMock()

    # Mock update_entry to raise an exception
    with (
        patch("asyncio.sleep", AsyncMock()),
        patch.object(
            hass.config_entries,
            "async_update_entry",
            side_effect=Exception("Save error"),
        ),
        patch(
            "custom_components.wifi_ssid_monitor.number._LOGGER.error"
        ) as mock_log_error,
    ):
        await number.async_set_native_value(15)
        await number._refresh_task

        mock_log_error.assert_called_once()
        assert "Failed to apply scan interval change" in mock_log_error.call_args[0][0]


def test_number_device_info(mock_config_entry, mock_coordinator):
    """Test device information for number entity."""
    number = WifiScanIntervalNumber(
        mock_coordinator, mock_config_entry, SCAN_INTERVAL_DESCRIPTION, 10
    )
    info = number.device_info
    assert info["identifiers"] == {(DOMAIN, mock_config_entry.entry_id)}
    assert info["manufacturer"] == "PlayFaster"


@pytest.mark.asyncio
async def test_number_debounce_cancelled(hass, mock_config_entry, mock_coordinator):
    """Test CancelledError during debounce sleep is handled gracefully."""
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.mock_state(hass, ConfigEntryState.LOADED)
    mock_config_entry.runtime_data = mock_coordinator

    number = WifiScanIntervalNumber(
        mock_coordinator, mock_config_entry, SCAN_INTERVAL_DESCRIPTION, 10
    )
    number.hass = hass
    number.async_write_ha_state = MagicMock()

    with (
        patch("asyncio.sleep", side_effect=asyncio.CancelledError()),
        patch(
            "custom_components.wifi_ssid_monitor.number._LOGGER.debug"
        ) as mock_log_debug,
    ):
        await number.async_set_native_value(30)
        if number._refresh_task:
            with suppress(asyncio.CancelledError):
                await number._refresh_task

        mock_log_debug.assert_called_once()
        assert "cancelled" in mock_log_debug.call_args[0][0].lower()

    assert number._attr_native_value == 30


@pytest.mark.asyncio
async def test_number_will_remove_from_hass_cancels_task(
    hass, mock_config_entry, mock_coordinator
):
    """Test that async_will_remove_from_hass cancels an active refresh task."""
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.mock_state(hass, ConfigEntryState.LOADED)
    mock_config_entry.runtime_data = mock_coordinator

    number = WifiScanIntervalNumber(
        mock_coordinator, mock_config_entry, SCAN_INTERVAL_DESCRIPTION, 10
    )
    number.hass = hass
    number.async_write_ha_state = MagicMock()

    await number.async_set_native_value(15)
    assert number._refresh_task is not None
    assert not number._refresh_task.done()

    await number.async_will_remove_from_hass()

    # Task catches CancelledError internally, so it completes normally
    with suppress(asyncio.CancelledError):
        await number._refresh_task

    assert number._refresh_task.done()
