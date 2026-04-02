"""Tests for Wifi Scan SSID API."""

import os
from unittest.mock import patch

import pytest

from custom_components.wifi_scan_ssid.api import WifiScanAPI, WifiScanError

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
