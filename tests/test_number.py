"""Tests for Wifi Scan SSID number platform."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState

from custom_components.wifi_scan_ssid.const import CONF_SCAN_INTERVAL, DOMAIN
from custom_components.wifi_scan_ssid.number import (
    SCAN_INTERVAL_DESCRIPTION,
    WifiScanIntervalNumber,
)


@pytest.mark.asyncio
async def test_number_setup_and_update(hass, mock_config_entry, mock_coordinator):
    """Test the scan interval number entity setup and value update."""
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.mock_state(hass, ConfigEntryState.LOADED)

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

    # Verify coordinator update
    assert mock_coordinator.update_interval == timedelta(minutes=15)
    mock_coordinator.async_request_refresh.assert_called_once()

    # Verify persistence in options
    assert mock_config_entry.options[CONF_SCAN_INTERVAL] == 900  # 15 * 60


@pytest.mark.asyncio
async def test_number_debounce_cancellation(hass, mock_config_entry, mock_coordinator):
    """Test that rapid changes cancel previous update tasks."""
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

        # task.cancel() is requested, check if it's being cancelled
        assert task1.cancelling() > 0 or task1.cancelled()
        assert not task2.cancelled()

        # Let task2 finish
        await task2

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
            "custom_components.wifi_scan_ssid.number._LOGGER.error"
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
