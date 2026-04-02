from unittest.mock import MagicMock

import pytest

from custom_components.zte_router_5g.const import CONF_STOP_POLLING, DOMAIN
from custom_components.zte_router_5g.switch import (
    PAUSE_POLLING_DESCRIPTION,
    ZTEPausePollingSwitch,
    async_setup_entry,
)


@pytest.mark.asyncio
async def test_pause_polling_switch(mock_coordinator, mock_config_entry):
    """Test turning the pause switch on and off."""
    # Start with False (not paused)
    mock_config_entry.options[CONF_STOP_POLLING] = False

    switch = ZTEPausePollingSwitch(
        mock_coordinator, mock_config_entry, PAUSE_POLLING_DESCRIPTION, False
    )
    switch.hass = MagicMock()
    # Mock hass.data structure
    switch.hass.data = {DOMAIN: {mock_config_entry.entry_id: mock_coordinator}}
    switch.async_write_ha_state = MagicMock()

    # 1. Turn ON (Pause)
    await switch.async_turn_on()
    switch.hass.config_entries.async_update_entry.assert_called()
    _args, kwargs = switch.hass.config_entries.async_update_entry.call_args
    assert kwargs["options"][CONF_STOP_POLLING] is True

    # 2. Turn OFF (Resume)
    await switch.async_turn_off()
    _args, kwargs = switch.hass.config_entries.async_update_entry.call_args
    assert kwargs["options"][CONF_STOP_POLLING] is False
    mock_coordinator.async_request_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_switch_setup_entry():
    """Test platform setup."""
    hass = MagicMock()
    entry = MagicMock()
    entry.entry_id = "test"
    entry.options = {CONF_STOP_POLLING: False}
    coordinator = MagicMock()
    hass.data = {DOMAIN: {"test": coordinator}}

    async_add_entities = MagicMock()
    await async_setup_entry(hass, entry, async_add_entities)
    async_add_entities.assert_called_once()
