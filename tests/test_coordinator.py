"""Tests for WiFi SSID Monitor coordinator."""

from unittest.mock import patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.wifi_ssid_monitor.api import WifiScanError
from custom_components.wifi_ssid_monitor.coordinator import WifiScanCoordinator


@pytest.mark.asyncio
async def test_coordinator_update_data_success(hass, mock_config_entry, mock_wifi_api):
    """Test successful data update in coordinator."""
    coordinator = WifiScanCoordinator(hass, mock_config_entry, mock_wifi_api, "1.4.0")

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
    coordinator = WifiScanCoordinator(hass, mock_config_entry, mock_wifi_api, "1.4.0")

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
async def test_coordinator_update_data_timeout(hass, mock_config_entry, mock_wifi_api):
    """Test data update with a timeout."""
    coordinator = WifiScanCoordinator(hass, mock_config_entry, mock_wifi_api, "1.4.0")

    mock_wifi_api.get_access_points.side_effect = TimeoutError

    with pytest.raises(UpdateFailed, match="API request timed out"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_update_data_failure(hass, mock_config_entry, mock_wifi_api):
    """Test data update failure."""
    coordinator = WifiScanCoordinator(hass, mock_config_entry, mock_wifi_api, "1.4.0")

    mock_wifi_api.get_access_points.side_effect = WifiScanError("Persistent failure")

    with pytest.raises(
        UpdateFailed,
        match="Communication error: Persistent failure",
    ):
        await coordinator._async_update_data()

    assert mock_wifi_api.get_access_points.call_count == 1


@pytest.mark.asyncio
async def test_coordinator_update_data_no_ssids(hass, mock_config_entry, mock_wifi_api):
    """Test data update when no SSIDs are found."""
    coordinator = WifiScanCoordinator(hass, mock_config_entry, mock_wifi_api, "1.4.0")

    mock_wifi_api.get_access_points.return_value = [{"signal": -50}]  # Missing ssid key

    data = await coordinator._async_update_data()

    assert data["count"] == 1
    assert data["ssids"] == ["[hidden]"]
    assert data["unknown_count"] == 1
    assert data["unknown_ssids"] == ["[hidden]"]


@pytest.mark.asyncio
async def test_coordinator_update_data_hidden_networks(
    hass, mock_config_entry, mock_wifi_api
):
    """Test data update with hidden networks (missing SSID)."""
    coordinator = WifiScanCoordinator(hass, mock_config_entry, mock_wifi_api, "1.4.0")

    mock_wifi_api.get_access_points.return_value = [
        {"ssid": "VisibleNet", "signal": -50, "channel": 1},
        {"signal": -70, "channel": 6},  # Hidden
        {"signal": -80, "channel": 11},  # Hidden
    ]

    data = await coordinator._async_update_data()

    assert data["count"] == 2  # VisibleNet and [hidden]
    assert "[hidden]" in data["ssids"]
    assert data["networks"]["[hidden]"]["rssi"] == -80  # Overwritten by last one
    assert data["networks"]["VisibleNet"]["channel"] == 1


@pytest.mark.asyncio
async def test_coordinator_update_data_api_none(hass, mock_config_entry, mock_wifi_api):
    """Test data update when API returns None (defensive check)."""
    coordinator = WifiScanCoordinator(hass, mock_config_entry, mock_wifi_api, "1.4.0")

    mock_wifi_api.get_access_points.return_value = None

    data = await coordinator._async_update_data()

    assert data["count"] == 0
    assert data["ssids"] == []
