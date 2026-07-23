"""Tests for WiFi SSID Monitor switch platform."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.wifi_ssid_monitor.const import (
    CONF_STOP_POLLING,
    DOMAIN,
)
from custom_components.wifi_ssid_monitor.switch import SWITCH_TYPES, WifiOptionSwitch


def _switch(coordinator, entry, key):
    """Build a WifiOptionSwitch for the given description key."""
    description = next(d for d in SWITCH_TYPES if d.key == key)
    sw = WifiOptionSwitch(coordinator, entry, description)
    return sw


def test_switch_is_on_reads_option(mock_config_entry, mock_coordinator):
    """The switch reflects the stored option value."""
    sw = _switch(mock_coordinator, mock_config_entry, "stop_polling")
    assert sw.is_on is False

    object.__setattr__(
        mock_config_entry,
        "options",
        {**mock_config_entry.options, CONF_STOP_POLLING: True},
    )
    assert sw.is_on is True


@pytest.mark.asyncio
async def test_switch_turn_on(hass, mock_config_entry, mock_coordinator):
    """Turning on the switch persists True and triggers a refresh."""
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.runtime_data = mock_coordinator
    mock_coordinator.async_force_refresh = AsyncMock()

    sw = _switch(mock_coordinator, mock_config_entry, "stop_polling")
    sw.hass = hass
    sw.async_write_ha_state = MagicMock()

    await sw.async_turn_on()

    assert mock_config_entry.options[CONF_STOP_POLLING] is True


@pytest.mark.asyncio
async def test_switch_turn_off(hass, mock_config_entry, mock_coordinator):
    """Turning off the switch persists False and triggers a refresh."""
    object.__setattr__(
        mock_config_entry,
        "options",
        {**mock_config_entry.options, CONF_STOP_POLLING: True},
    )
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.runtime_data = mock_coordinator
    mock_coordinator.async_force_refresh = AsyncMock()

    sw = _switch(mock_coordinator, mock_config_entry, "stop_polling")
    sw.hass = hass
    sw.async_write_ha_state = MagicMock()

    await sw.async_turn_off()

    assert mock_config_entry.options[CONF_STOP_POLLING] is False


@pytest.mark.asyncio
async def test_switch_stop_polling_on_does_not_refresh(
    hass, mock_config_entry, mock_coordinator
):
    """Turning on stop_polling does not trigger a fetch."""
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.runtime_data = mock_coordinator
    mock_coordinator.async_force_refresh = AsyncMock()

    sw = _switch(mock_coordinator, mock_config_entry, "stop_polling")
    sw.hass = hass
    sw.async_write_ha_state = MagicMock()

    await sw.async_turn_on()

    mock_coordinator.async_force_refresh.assert_not_called()


def test_available_always_true(mock_config_entry, mock_coordinator):
    """Switch remains available even if coordinator is down."""
    sw = _switch(mock_coordinator, mock_config_entry, "stop_polling")
    assert sw.available is True


def test_device_info(mock_config_entry, mock_coordinator):
    """The switch reports the shared device info."""
    sw = _switch(mock_coordinator, mock_config_entry, "stop_polling")
    info = sw.device_info
    assert info["identifiers"] == {(DOMAIN, mock_config_entry.entry_id)}
    assert info["manufacturer"] == "PlayFaster"
