"""Tests for WiFi SSID Monitor number platform."""

import asyncio
from contextlib import suppress
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.wifi_ssid_monitor.const import (
    CONF_PROXIMITY_SIGNAL_THRESHOLD,
    CONF_SCAN_INTERVAL,
    DOMAIN,
)
from custom_components.wifi_ssid_monitor.number import NUMBER_TYPES, WifiOptionNumber


def _number(coordinator, entry, key):
    """Build a WifiOptionNumber for the given description key."""
    description = next(d for d in NUMBER_TYPES if d.key == key)
    number = WifiOptionNumber(coordinator, entry, description)
    return number


def test_scan_interval_reads_option_in_minutes(mock_config_entry, mock_coordinator):
    """The interval entity shows the stored seconds as minutes (60 -> 1)."""
    number = _number(mock_coordinator, mock_config_entry, "scan_interval")
    # conftest stores 60 seconds.
    assert number.native_value == 1


def test_threshold_reads_option_directly(mock_config_entry, mock_coordinator):
    """The threshold entity shows the stored percentage as-is."""
    object.__setattr__(
        mock_config_entry,
        "options",
        {**mock_config_entry.options, CONF_PROXIMITY_SIGNAL_THRESHOLD: 70},
    )
    number = _number(mock_coordinator, mock_config_entry, "proximity_signal_threshold")
    assert number.native_value == 70


@pytest.mark.asyncio
async def test_scan_interval_persists_seconds(
    hass, mock_config_entry, mock_coordinator
):
    """Setting 15 minutes persists 900 seconds and does not force a refresh."""
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.runtime_data = mock_coordinator
    mock_coordinator.async_force_refresh = AsyncMock()

    number = _number(mock_coordinator, mock_config_entry, "scan_interval")
    number.hass = hass
    number.async_write_ha_state = MagicMock()

    with patch("asyncio.sleep", AsyncMock()):
        await number.async_set_native_value(15)
        await number._pending
        await hass.async_block_till_done()

    assert mock_config_entry.options[CONF_SCAN_INTERVAL] == 900
    # A scan-interval change is applied by the listener, not a forced fetch.
    mock_coordinator.async_force_refresh.assert_not_called()


@pytest.mark.asyncio
async def test_threshold_forces_refresh(hass, mock_config_entry, mock_coordinator):
    """Changing the threshold persists the percent value and forces a fetch."""
    from custom_components.wifi_ssid_monitor import async_reload_entry

    mock_config_entry.add_to_hass(hass)
    mock_config_entry.runtime_data = mock_coordinator
    mock_config_entry.async_on_unload(
        mock_config_entry.add_update_listener(async_reload_entry)
    )
    mock_coordinator.async_force_refresh = AsyncMock()

    number = _number(mock_coordinator, mock_config_entry, "proximity_signal_threshold")
    number.hass = hass
    number.async_write_ha_state = MagicMock()

    with patch("asyncio.sleep", AsyncMock()):
        await number.async_set_native_value(65)
        await number._pending
        await hass.async_block_till_done()

    assert mock_config_entry.options[CONF_PROXIMITY_SIGNAL_THRESHOLD] == 65
    mock_coordinator.async_force_refresh.assert_awaited()


@pytest.mark.asyncio
async def test_debounce_cancellation(hass, mock_config_entry, mock_coordinator):
    """A rapid second change cancels the first pending write."""
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.runtime_data = mock_coordinator
    mock_coordinator.async_force_refresh = AsyncMock()

    number = _number(mock_coordinator, mock_config_entry, "scan_interval")
    number.hass = hass
    number.async_write_ha_state = MagicMock()

    with patch("asyncio.sleep", AsyncMock()):
        await number.async_set_native_value(20)
        task1 = number._pending
        await number.async_set_native_value(30)
        task2 = number._pending
        assert task1 is not task2
        await task2
        await hass.async_block_till_done()

    assert mock_config_entry.options[CONF_SCAN_INTERVAL] == 1800  # 30 * 60


@pytest.mark.asyncio
async def test_apply_error_logs(hass, mock_config_entry, mock_coordinator):
    """A failure to persist is logged and the optimistic value is cleared."""
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.runtime_data = mock_coordinator

    number = _number(mock_coordinator, mock_config_entry, "scan_interval")
    number.hass = hass
    number.async_write_ha_state = MagicMock()

    with (
        patch("asyncio.sleep", AsyncMock()),
        patch.object(
            hass.config_entries,
            "async_update_entry",
            side_effect=Exception("Save error"),
        ),
        patch(
            "custom_components.wifi_ssid_monitor.number._LOGGER.exception"
        ) as mock_log,
    ):
        await number.async_set_native_value(15)
        await number._pending

    mock_log.assert_called_once()


def test_device_info(mock_config_entry, mock_coordinator):
    """The number reports the shared device info."""
    number = _number(mock_coordinator, mock_config_entry, "scan_interval")
    info = number.device_info
    assert info["identifiers"] == {(DOMAIN, mock_config_entry.entry_id)}
    assert info["manufacturer"] == "PlayFaster"


@pytest.mark.asyncio
async def test_debounce_cancelled_is_graceful(
    hass, mock_config_entry, mock_coordinator
):
    """A CancelledError during the debounce sleep is swallowed."""
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.runtime_data = mock_coordinator

    number = _number(mock_coordinator, mock_config_entry, "scan_interval")
    number.hass = hass
    number.async_write_ha_state = MagicMock()

    with (
        patch("asyncio.sleep", side_effect=asyncio.CancelledError()),
        patch(
            "custom_components.wifi_ssid_monitor.number._LOGGER.debug"
        ) as mock_log_debug,
    ):
        await number.async_set_native_value(30)
        with suppress(asyncio.CancelledError):
            await number._pending

    mock_log_debug.assert_called_once()


def test_optimistic_value_returned(mock_config_entry, mock_coordinator):
    """When an optimistic value is set, native_value returns it."""
    number = _number(mock_coordinator, mock_config_entry, "scan_interval")
    number._optimistic = 42.0
    assert number.native_value == 42.0


def test_scale_division(mock_config_entry, mock_coordinator):
    """Values with scale > 1 are divided by the scale factor."""
    object.__setattr__(
        mock_config_entry,
        "options",
        {**mock_config_entry.options, "scan_interval": 3600},
    )
    number = _number(mock_coordinator, mock_config_entry, "scan_interval")
    assert number.native_value == 60  # 3600 / 60


@pytest.mark.asyncio
async def test_will_remove_cancels_task(hass, mock_config_entry, mock_coordinator):
    """Removal cancels an in-flight debounce task."""
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.runtime_data = mock_coordinator

    number = _number(mock_coordinator, mock_config_entry, "scan_interval")
    number.hass = hass
    number.async_write_ha_state = MagicMock()

    await number.async_set_native_value(15)
    assert number._pending is not None

    await number.async_will_remove_from_hass()
    with suppress(asyncio.CancelledError):
        await number._pending

    assert number._pending.done()
