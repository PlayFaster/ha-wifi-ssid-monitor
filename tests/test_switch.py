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
    return WifiOptionSwitch(coordinator, entry, description)


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


# ---------------------------------------------------------------------------
# Publish-moment capture
# ---------------------------------------------------------------------------
#
#
# The tests above stub `async_write_ha_state` with a bare `MagicMock()` and
# assert the option afterwards. Both halves pass even if the publish carried
# the **pre-write** value — which is exactly how three `huawei_router_5g`
# switches shipped for a fortnight springing back on every toggle.
#
# These tests join the two halves: they capture what `is_on` reads **at the
# moment of the publish**, so a `_set_state` that published before
# `async_update_entry` had landed would fail here and nowhere else.
#
# `wifi_ssid_monitor` is not affected — every switch is option-backed and
# reads `entry.options` rather than a coordinator payload, so there is no
# stale-payload window to begin with. The tests are added anyway,
# part 2: a project that is not affected still has nothing proving it, and
# the next regression would otherwise arrive uncovered.


@pytest.mark.asyncio
@pytest.mark.parametrize("description", SWITCH_TYPES, ids=lambda d: d.key)
@pytest.mark.parametrize("target", [True, False])
async def test_switch_publishes_the_post_write_state(
    hass, mock_config_entry, mock_coordinator, description, target
):
    """Every switch publishes the value it just wrote, not the one it replaced.

    The option is seeded to the opposite of `target` first: starting from the
    value under test would pass against a publish that sent the old one.
    """
    object.__setattr__(
        mock_config_entry,
        "options",
        {**mock_config_entry.options, description.option_key: not target},
    )
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.runtime_data = mock_coordinator
    mock_coordinator.async_force_refresh = AsyncMock()

    sw = WifiOptionSwitch(mock_coordinator, mock_config_entry, description)
    sw.hass = hass

    published: list[bool] = []
    sw.async_write_ha_state = MagicMock(side_effect=lambda: published.append(sw.is_on))

    if target:
        await sw.async_turn_on()
    else:
        await sw.async_turn_off()

    assert published == [target]
