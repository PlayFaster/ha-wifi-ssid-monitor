"""Tests for WiFi SSID Monitor API."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
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
            timeout=aiohttp.ClientTimeout(total=30),
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
            timeout=aiohttp.ClientTimeout(total=30),
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


@pytest.mark.asyncio
async def test_validate_no_token(mock_aiohttp_client):
    """Test validation fails when SUPERVISOR_TOKEN is missing."""
    with patch.dict(os.environ, {}, clear=True):
        api = WifiScanAPI(mock_aiohttp_client, "wlan0")
        with pytest.raises(WifiScanError, match="SUPERVISOR_TOKEN not found"):
            await api.validate()


@pytest.mark.asyncio
async def test_get_access_points_json_error(mock_aiohttp_client):
    """Test error when API returns invalid JSON."""
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = WifiScanAPI(mock_aiohttp_client, "wlan0")
        mock_aiohttp_client.get.return_value = MockResponse(json_error=True)

        with pytest.raises(WifiScanError, match="Invalid API response"):
            await api.get_access_points()


@pytest.mark.asyncio
async def test_get_interfaces_no_token(mock_aiohttp_client):
    """Test get_interfaces fails when SUPERVISOR_TOKEN is missing."""
    with patch.dict(os.environ, {}, clear=True):
        api = WifiScanAPI(mock_aiohttp_client, "wlan0")
        with pytest.raises(WifiScanError, match="SUPERVISOR_TOKEN not found"):
            await api.get_interfaces()


@pytest.mark.asyncio
async def test_get_interfaces_json_error(mock_aiohttp_client):
    """Test error when get_interfaces API returns invalid JSON."""
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = WifiScanAPI(mock_aiohttp_client, "wlan0")
        mock_aiohttp_client.get.return_value = MockResponse(json_error=True)

        with pytest.raises(WifiScanError, match="Invalid API response"):
            await api.get_interfaces()


@pytest.mark.asyncio
async def test_get_interfaces_connection_error(mock_aiohttp_client):
    """Test error when connection fails during get_interfaces."""
    import aiohttp

    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = WifiScanAPI(mock_aiohttp_client, "wlan0")
        mock_aiohttp_client.get.side_effect = aiohttp.ClientError("Connection failed")

        with pytest.raises(WifiScanError, match="Connection error"):
            await api.get_interfaces()


@pytest.mark.asyncio
async def test_get_interfaces_generic_error(mock_aiohttp_client):
    """Test error when a generic exception occurs during get_interfaces."""
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = WifiScanAPI(mock_aiohttp_client, "wlan0")
        mock_aiohttp_client.get.side_effect = Exception("Generic error")

        with pytest.raises(WifiScanError, match="Unexpected error"):
            await api.get_interfaces()


@pytest.mark.asyncio
async def test_get_access_points_json_value_error(mock_aiohttp_client):
    """Test ValueError from json() is caught and wrapped in WifiScanError."""
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = WifiScanAPI(mock_aiohttp_client, "wlan0")

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            side_effect=ValueError("No JSON object could be decoded")
        )

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_cm.__aexit__ = AsyncMock(return_value=None)
        mock_aiohttp_client.get.return_value = mock_cm

        with pytest.raises(WifiScanError, match="Invalid API response"):
            await api.get_access_points()


@pytest.mark.asyncio
async def test_get_interfaces_json_value_error(mock_aiohttp_client):
    """Test ValueError from json() on get_interfaces is caught and wrapped."""
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = WifiScanAPI(mock_aiohttp_client, "wlan0")

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            side_effect=ValueError("No JSON object could be decoded")
        )

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_cm.__aexit__ = AsyncMock(return_value=None)
        mock_aiohttp_client.get.return_value = mock_cm

        with pytest.raises(WifiScanError, match="Invalid API response"):
            await api.get_interfaces()


@pytest.mark.asyncio
async def test_get_access_points_no_accesspoints_key(mock_aiohttp_client):
    """When the response has no 'accesspoints' key, returns [] and sets flag."""
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = WifiScanAPI(mock_aiohttp_client, "wlan0")

        mock_response_data = {
            "result": "ok",
            "data": {"interfaces": []},
        }
        mock_aiohttp_client.get.return_value = MockResponse(
            json_data=mock_response_data
        )

        aps = await api.get_access_points()

        assert aps == []
        assert api.last_response_had_ap_key is False


@pytest.mark.asyncio
async def test_get_access_points_empty_list_is_not_a_missing_key(mock_aiohttp_client):
    """An empty scan and a missing 'accesspoints' key are different states.

    Both return ``[]``, so only ``last_response_had_ap_key`` separates "the
    radio saw nothing" from "the Supervisor did not answer the question" — and
    the health checks read that flag to decide whether to report drift.
    """
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = WifiScanAPI(mock_aiohttp_client, "wlan0")

        mock_aiohttp_client.get.return_value = MockResponse(
            json_data={"result": "ok", "data": {"accesspoints": []}}
        )

        aps = await api.get_access_points()

        assert aps == []
        assert api.last_response_had_ap_key is True


@pytest.mark.asyncio
async def test_get_access_points_server_error_does_not_blame_the_interface(
    mock_aiohttp_client,
):
    """A 500 must not be read as the interface having gone away.

    Only 400 and 404 mean "no such interface". Clearing the flag on any
    non-200 would raise a missing-hardware repair issue every time the
    Supervisor had a bad minute.
    """
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = WifiScanAPI(mock_aiohttp_client, "wlan0")

        mock_aiohttp_client.get.return_value = MockResponse(
            status=500, text_data="Internal Server Error"
        )

        with pytest.raises(WifiScanError, match="API returned status 500"):
            await api.get_access_points()

        assert api.last_interface_present is True


# ---------------------------------------------------------------------------
# testing_deeper_lev1_review — recommendations_20260806.md
# ---------------------------------------------------------------------------


def _request_info():
    """Build a usable RequestInfo for ContentTypeError.

    `str(ContentTypeError)` reads `request_info.real_url`, so passing None
    raises inside the logger and the error is misattributed to the catch-all
    handler rather than the clause under test.
    """
    info = MagicMock()
    info.real_url = "http://supervisor/network/interface/wlan0/accesspoints"
    return info


@pytest.mark.asyncio
async def test_get_access_points_content_type_error(mock_aiohttp_client):
    """`ContentTypeError` is the one that actually happens in production.

    Covers finding ERR.2 from recommendations_20260806.md.

    Both `json()` call sites catch `(aiohttp.ContentTypeError, ValueError)`
    and only `ValueError` was exercised. `ContentTypeError` is what the
    Supervisor raises when it answers with an HTML error page instead of
    JSON, and a test using `ValueError` does not prove it is caught.
    """
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = WifiScanAPI(mock_aiohttp_client, "wlan0")

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            side_effect=aiohttp.ContentTypeError(
                request_info=_request_info(), history=()
            )
        )

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_cm.__aexit__ = AsyncMock(return_value=None)
        mock_aiohttp_client.get.return_value = mock_cm

        with pytest.raises(WifiScanError, match="Invalid API response"):
            await api.get_access_points()


@pytest.mark.asyncio
async def test_get_interfaces_content_type_error(mock_aiohttp_client):
    """The same clause in `get_interfaces`, exercised independently.

    Covers finding ERR.2 from recommendations_20260806.md.
    """
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = WifiScanAPI(mock_aiohttp_client, "wlan0")

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            side_effect=aiohttp.ContentTypeError(
                request_info=_request_info(), history=()
            )
        )

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_cm.__aexit__ = AsyncMock(return_value=None)
        mock_aiohttp_client.get.return_value = mock_cm

        with pytest.raises(WifiScanError, match="Invalid API response"):
            await api.get_interfaces()


@pytest.mark.asyncio
async def test_an_unforeseen_error_is_wrapped_and_keeps_its_cause(
    mock_aiohttp_client,
):
    """The catch-all wraps, and the original exception is not lost.

    Covers finding ERR.3 from recommendations_20260806.md.

    The bare `except Exception` exists so an unforeseen library error reaches
    the coordinator as a `WifiScanError` it knows how to hold data through,
    rather than propagating raw and being counted as a different class of
    failure. Asserting `__cause__` is what proves the traceback survives —
    without `from e` the original error is invisible in the log.
    """
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = WifiScanAPI(mock_aiohttp_client, "wlan0")
        original = RuntimeError("socket exploded")
        mock_aiohttp_client.get.side_effect = original

        with pytest.raises(WifiScanError, match="Unexpected error") as excinfo:
            await api.get_access_points()

        assert "socket exploded" in str(excinfo.value)
        assert excinfo.value.__cause__ is original
