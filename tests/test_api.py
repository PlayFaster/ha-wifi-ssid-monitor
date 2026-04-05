"""Tests for WiFi SSID Monitor API."""

import os
from unittest.mock import patch

import pytest

from custom_components.wifi_ssid_monitor.api import WifiScanAPI, WifiScanError

from .conftest import MockResponse


@pytest.mark.asyncio
async def test_get_access_points_success(mock_aiohttp_client):
    """Test successful access point retrieval."""
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = WifiScanAPI(mock_aiohttp_client, "wlan0")

        mock_response_data = {
            "result": "ok",
            "data": {
                "accesspoints": [
                    {"ssid": "Network1", "signal": -50},
                    {"ssid": "Network2", "signal": -60},
                ]
            },
        }
        mock_aiohttp_client.get.return_value = MockResponse(
            json_data=mock_response_data
        )

        aps = await api.get_access_points()

        assert len(aps) == 2
        assert aps[0]["ssid"] == "Network1"
        assert aps[1]["ssid"] == "Network2"

        mock_aiohttp_client.get.assert_called_once_with(
            "http://supervisor/network/interface/wlan0/accesspoints",
            headers={
                "Authorization": "Bearer test_token",
                "Content-Type": "application/json",
            },
            timeout=30,
        )


@pytest.mark.asyncio
async def test_get_access_points_no_token(mock_aiohttp_client):
    """Test error when SUPERVISOR_TOKEN is missing."""
    with patch.dict(os.environ, {}, clear=True):
        api = WifiScanAPI(mock_aiohttp_client, "wlan0")
        with pytest.raises(WifiScanError, match="SUPERVISOR_TOKEN not found"):
            await api.get_access_points()


@pytest.mark.asyncio
async def test_get_access_points_api_error(mock_aiohttp_client):
    """Test error when API returns non-200 status."""
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = WifiScanAPI(mock_aiohttp_client, "wlan0")
        mock_aiohttp_client.get.return_value = MockResponse(
            status=404, text_data="Not Found"
        )

        with pytest.raises(WifiScanError, match="API returned status 404"):
            await api.get_access_points()


@pytest.mark.asyncio
async def test_get_access_points_connection_error(mock_aiohttp_client):
    """Test error when connection fails."""
    import aiohttp

    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = WifiScanAPI(mock_aiohttp_client, "wlan0")
        mock_aiohttp_client.get.side_effect = aiohttp.ClientError("Connection failed")

        with pytest.raises(WifiScanError, match="Connection error"):
            await api.get_access_points()


@pytest.mark.asyncio
async def test_get_access_points_generic_error(mock_aiohttp_client):
    """Test error when a generic exception occurs."""
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = WifiScanAPI(mock_aiohttp_client, "wlan0")
        mock_aiohttp_client.get.side_effect = Exception("Generic error")

        with pytest.raises(WifiScanError, match="Unexpected error"):
            await api.get_access_points()


@pytest.mark.asyncio
async def test_get_interfaces_success(mock_aiohttp_client):
    """Test successful interface retrieval."""
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = WifiScanAPI(mock_aiohttp_client, "wlan0")

        mock_response_data = {
            "result": "ok",
            "data": {
                "interfaces": [
                    {"interface": "eth0", "type": "ethernet"},
                    {"interface": "wlan0", "type": "wifi"},
                    {"interface": "wlan1", "type": "wifi"},
                ]
            },
        }
        mock_aiohttp_client.get.return_value = MockResponse(
            json_data=mock_response_data
        )

        ifaces = await api.get_interfaces()

        assert len(ifaces) == 2
        assert "wlan0" in ifaces
        assert "wlan1" in ifaces

        mock_aiohttp_client.get.assert_called_once_with(
            "http://supervisor/network/info",
            headers={
                "Authorization": "Bearer test_token",
                "Content-Type": "application/json",
            },
            timeout=30,
        )


@pytest.mark.asyncio
async def test_get_interfaces_api_error(mock_aiohttp_client):
    """Test error when get_interfaces API returns non-200 status."""
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = WifiScanAPI(mock_aiohttp_client, "wlan0")
        mock_aiohttp_client.get.return_value = MockResponse(
            status=500, text_data="Internal Server Error"
        )

        with pytest.raises(WifiScanError, match="API returned status 500"):
            await api.get_interfaces()


@pytest.mark.asyncio
async def test_validate_success(mock_aiohttp_client):
    """Test successful API validation."""
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = WifiScanAPI(mock_aiohttp_client, "wlan0")
        with patch.object(api, "get_access_points", return_value=[]):
            assert await api.validate() is True
