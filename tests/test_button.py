"""Tests for WiFi SSID Monitor button platform."""

from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

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
    """Test button press raises HomeAssistantError when scan fails."""
    button = WifiScanButton(mock_coordinator, mock_config_entry, SCAN_NOW_DESCRIPTION)

    with patch.object(mock_coordinator, "async_force_refresh", return_value=None):
        mock_coordinator.last_update_success = False
        with pytest.raises(HomeAssistantError, match="WiFi scan failed"):
            await button.async_press()
