"""Tests for WiFi SSID Monitor button platform."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util

from custom_components.wifi_ssid_monitor.button import (
    SCAN_NOW_DESCRIPTION,
    WifiScanButton,
)
from custom_components.wifi_ssid_monitor.const import DOMAIN


@pytest.mark.asyncio
async def test_button_scan_now(
    hass: HomeAssistant, mock_config_entry, mock_coordinator
):
    """Test button press triggers a scan."""
    button = WifiScanButton(mock_coordinator, mock_config_entry, SCAN_NOW_DESCRIPTION)

    with patch.object(mock_coordinator, "async_force_refresh", return_value=None):
        mock_coordinator.last_update_success = True
        await button.async_press()
        # No exception means success

    info = button.device_info
    assert info["identifiers"] == {(DOMAIN, mock_config_entry.entry_id)}
    assert info["manufacturer"] == "PlayFaster"
    assert "wlan0" in info["model"]
    assert button.unique_id == f"{mock_config_entry.unique_id}_scan_now"


@pytest.mark.asyncio
async def test_button_scan_failure_raises_error(
    hass: HomeAssistant, mock_config_entry, mock_coordinator
):
    """Test button press raises HomeAssistantError when scan fails.

    The mock must advance `last_update_success_time`, because a scan that
    genuinely ran is what the handler now distinguishes from a press the
    debouncer coalesced away — see the test below.
    """
    button = WifiScanButton(mock_coordinator, mock_config_entry, SCAN_NOW_DESCRIPTION)
    mock_coordinator.last_update_success_time = dt_util.now()

    async def _ran_and_failed():
        mock_coordinator.last_update_success_time = dt_util.now() + timedelta(seconds=1)

    with patch.object(
        mock_coordinator, "async_force_refresh", side_effect=_ran_and_failed
    ):
        mock_coordinator.last_update_success = False
        with pytest.raises(HomeAssistantError, match="WiFi scan failed"):
            await button.async_press()


@pytest.mark.asyncio
async def test_a_coalesced_press_reports_nothing(
    hass: HomeAssistant, mock_config_entry, mock_coordinator
):
    """A press swallowed by the debouncer is silent, not a failure.

    Covers finding L1 from code_review_20260806_2140.md.

    `async_request_refresh` is debounced with a 10-second cooldown. Inside it
    the call returns without fetching, so `last_update_success` still describes
    the run before — and a failed scan followed by a quick retry reported
    failure again without having retried. A press that did not run is not a
    press that failed.
    """
    button = WifiScanButton(mock_coordinator, mock_config_entry, SCAN_NOW_DESCRIPTION)
    frozen = dt_util.now()
    mock_coordinator.last_update_success_time = frozen
    mock_coordinator.last_update_success = False

    with patch.object(mock_coordinator, "async_force_refresh", return_value=None):
        await button.async_press()

    assert mock_coordinator.last_update_success_time == frozen


@pytest.mark.asyncio
async def test_a_successful_scan_raises_nothing(
    hass: HomeAssistant, mock_config_entry, mock_coordinator
):
    """A scan that ran and succeeded reports nothing at all.

    Covers finding L1 from code_review_20260806_2140.md — the third path.
    The handler now distinguishes three cases: coalesced (silent), ran and
    failed (raises), ran and succeeded (silent). Only the first two were
    covered.
    """
    button = WifiScanButton(mock_coordinator, mock_config_entry, SCAN_NOW_DESCRIPTION)
    mock_coordinator.last_update_success_time = dt_util.now()

    async def _ran_and_succeeded():
        mock_coordinator.last_update_success_time = dt_util.now() + timedelta(seconds=1)
        mock_coordinator.last_update_success = True

    with patch.object(
        mock_coordinator, "async_force_refresh", side_effect=_ran_and_succeeded
    ):
        await button.async_press()

    assert mock_coordinator.last_update_success is True
