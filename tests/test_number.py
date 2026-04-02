"""Tests for WiFi SSID Monitor number platform."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState

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

    # CONF_SCAN_INTERVAL is 60 in conftest, so initial_value should be 1
    number = WifiScanIntervalNumber(mock_coordinator, SCAN_INTERVAL_DESCRIPTION)
    number.hass = hass
    number.async_write_ha_state = MagicMock()

    # Mock async_update_entry to update the mock_config_entry directly
    # since it's a mock object and not a real config entry.
    def mock_update_entry(entry, **kwargs):
        if "options" in kwargs:
            # Bypass AttributeError: options cannot be changed directly
            object.__setattr__(entry, "options", kwargs["options"])
        return True

    with (
        patch.object(
            hass.config_entries, "async_update_entry", side_effect=mock_update_entry
        ),
        patch("asyncio.sleep", AsyncMock()),
    ):
        # Test setting a new value via direct call to simulate service
        await number.async_set_native_value(15)
        # We MUST await the background task created by the entity
        if number._refresh_task:
            await number._refresh_task

    # Verify persistence in options.
    assert mock_config_entry.options[CONF_SCAN_INTERVAL] == 900  # 15 * 60


@pytest.mark.asyncio
async def test_number_debounce_cancellation(hass, mock_config_entry, mock_coordinator):
    """Test that rapid changes cancel previous update tasks."""
    number = WifiScanIntervalNumber(mock_coordinator, SCAN_INTERVAL_DESCRIPTION)
    number.hass = hass
    number.async_write_ha_state = MagicMock()

    def mock_update_entry(entry, **kwargs):
        if "options" in kwargs:
            # Bypass AttributeError: options cannot be changed directly
            object.__setattr__(entry, "options", kwargs["options"])
        return True

    with (
        patch.object(
            hass.config_entries, "async_update_entry", side_effect=mock_update_entry
        ),
        patch("asyncio.sleep", AsyncMock()),
    ):
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

    # Verify that only the final value was persisted
    assert mock_config_entry.options[CONF_SCAN_INTERVAL] == 1800  # 30 * 60


@pytest.mark.asyncio
async def test_number_apply_error(hass, mock_config_entry, mock_coordinator):
    """Test error handling during interval application."""
    number = WifiScanIntervalNumber(mock_coordinator, SCAN_INTERVAL_DESCRIPTION)
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
    number = WifiScanIntervalNumber(mock_coordinator, SCAN_INTERVAL_DESCRIPTION)
    info = number.device_info
    assert info["identifiers"] == {(DOMAIN, mock_config_entry.entry_id)}
    assert info["manufacturer"] == "PlayFaster"
