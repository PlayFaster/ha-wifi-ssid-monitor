"""Tests for WiFi SSID Monitor coordinator."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.wifi_ssid_monitor.api import WifiScanError
from custom_components.wifi_ssid_monitor.coordinator import WifiScanCoordinator


@pytest.mark.asyncio
async def test_coordinator_update_data_success(hass, mock_config_entry, mock_wifi_api):
    """Test successful data update in coordinator."""
    coordinator = WifiScanCoordinator(hass, mock_config_entry, mock_wifi_api)

    mock_wifi_api.get_access_points.return_value = [
        {"ssid": "Net1", "signal": -50},
        {"ssid": "Net2", "signal": -60},
        {"ssid": "Net1", "signal": -55},  # Duplicate SSID
        {"ssid": "MyNetwork1", "signal": -40},  # Known SSID from conftest
    ]

    data = await coordinator._async_update_data()

    assert data["count"] == 3
    assert data["ssids"] == ["MyNetwork1", "Net1", "Net2"]
    assert data["unknown_ssids"] == ["Net1", "Net2"]
    assert data["unknown_count"] == 2
    assert data["interface"] == "wlan0"


@pytest.mark.asyncio
async def test_coordinator_update_data_known_networks_parsing(
    hass, mock_config_entry, mock_wifi_api
):
    """Test parsing of known networks string with various formats."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={
            "known_wifi_ids": " Net1 , Net2, ,Net3",  # Extra spaces, empty entries
        },
    )
    coordinator = WifiScanCoordinator(hass, mock_config_entry, mock_wifi_api)

    mock_wifi_api.get_access_points.return_value = [
        {"ssid": "Net1"},
        {"ssid": "Net2"},
        {"ssid": "Net3"},
        {"ssid": "Net4"},
    ]

    data = await coordinator._async_update_data()

    assert data["count"] == 4
    assert data["unknown_count"] == 1
    assert data["unknown_ssids"] == ["Net4"]


@pytest.mark.asyncio
async def test_coordinator_update_data_retry_success(
    hass, mock_config_entry, mock_wifi_api
):
    """Test data update with a retry success."""
    coordinator = WifiScanCoordinator(hass, mock_config_entry, mock_wifi_api)

    mock_wifi_api.get_access_points.side_effect = [
        WifiScanError("Temporary failure"),
        [{"ssid": "Net1", "signal": -50}],
    ]

    with patch("asyncio.sleep", AsyncMock()) as mock_sleep:
        data = await coordinator._async_update_data()

    assert data["count"] == 1
    assert data["ssids"] == ["Net1"]
    mock_sleep.assert_called_once_with(10)
    assert mock_wifi_api.get_access_points.call_count == 2


@pytest.mark.asyncio
async def test_coordinator_update_data_failure(hass, mock_config_entry, mock_wifi_api):
    """Test data update failure after retries."""
    coordinator = WifiScanCoordinator(hass, mock_config_entry, mock_wifi_api)

    mock_wifi_api.get_access_points.side_effect = WifiScanError("Persistent failure")

    with (
        patch("asyncio.sleep", AsyncMock()),
        pytest.raises(UpdateFailed, match="Communication error: Persistent failure"),
    ):
        await coordinator._async_update_data()

    assert mock_wifi_api.get_access_points.call_count == 2


@pytest.mark.asyncio
async def test_coordinator_update_data_no_ssids(hass, mock_config_entry, mock_wifi_api):
    """Test data update when no SSIDs are found."""
    coordinator = WifiScanCoordinator(hass, mock_config_entry, mock_wifi_api)

    mock_wifi_api.get_access_points.return_value = [{"signal": -50}]  # Missing ssid key

    data = await coordinator._async_update_data()

    assert data["count"] == 0
    assert data["ssids"] == []
    assert data["unknown_count"] == 0
    assert data["unknown_ssids"] == []
