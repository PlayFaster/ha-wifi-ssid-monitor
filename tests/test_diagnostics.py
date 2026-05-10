"""Tests for the diagnostics platform."""

from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant

from custom_components.wifi_ssid_monitor.const import (
    CONF_INTERFACE,
    CONF_KNOWN_SSIDS,
    DOMAIN,
)
from custom_components.wifi_ssid_monitor.diagnostics import (
    async_get_config_entry_diagnostics,
)
from tests.conftest import MockConfigEntry


async def test_diagnostics(hass: HomeAssistant, mock_config_entry: MockConfigEntry):
    """Test diagnostics output."""
    mock_config_entry.add_to_hass(hass)

    # Setup coordinator mock
    mock_coordinator = MagicMock()
    mock_coordinator.api.interface = "wlan0"
    mock_coordinator.last_update_success = True
    mock_coordinator.last_update_success_time = "2026-05-06T12:00:00"
    mock_coordinator.version = "1.4.3-dev3"
    mock_coordinator.data = {
        "count": 5,
        "unknown_count": 2,
        "ssids": ["Home", "Guest", "Hidden1", "Hidden2", "Rogue"],
        "unknown_ssids": ["Hidden1", "Hidden2"],
    }

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator

    diagnostics = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert diagnostics["entry"]["title"] == "WiFi SSID Monitor"
    assert diagnostics["entry"]["options"][CONF_INTERFACE] == "wlan0"
    # Ensure known SSIDs are redacted
    assert diagnostics["entry"]["options"][CONF_KNOWN_SSIDS] == "**REDACTED**"

    assert diagnostics["coordinator"]["interface"] == "wlan0"
    assert diagnostics["coordinator"]["data"]["count"] == 5
    assert diagnostics["coordinator"]["data"]["unknown_ssids"] == ["Hidden1", "Hidden2"]
