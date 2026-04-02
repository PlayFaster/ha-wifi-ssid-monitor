from unittest.mock import MagicMock, patch

import pytest

from custom_components.zte_router_5g.api import (
    ZTEAuthError,
    ZTERouterAPI,
)

from .conftest import MockResponse


def test_api_hash():
    api = ZTERouterAPI(MagicMock(), "192.168.0.1", "admin", "password")
    assert (
        api._hash("test")
        == "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
    )


def test_api_hash_none():
    """Test _hash with None input."""
    api = ZTERouterAPI(MagicMock(), "192.168.0.1", "admin", "password")
    with pytest.raises(ValueError, match="Input to hash function cannot be None"):
        api._hash(None)


def test_api_hex_decode():
    api = ZTERouterAPI(MagicMock(), "192.168.0.1", "admin", "password")
    assert api._hex_decode("00480065006c006c006f") == "Hello"
    assert api._hex_decode("") == ""
    assert api._hex_decode("invalid") == "[Decoding Error]"


def test_api_parse_date():
    api = ZTERouterAPI(MagicMock(), "192.168.0.1", "admin", "password")
    assert api._parse_date("23,10,10,10,0,0,+1") == "2023-10-10T10:00:00"
    assert api._parse_date("") is None
    assert api._parse_date("invalid") == "invalid"


def test_api_parse_date_error():
    """Test date parsing with a string that splits but fails int conversion."""
    api = ZTERouterAPI(MagicMock(), "192.168.0.1", "admin", "password")
    assert api._parse_date("23,fail,10,10,00,00") == "23,fail,10,10,00,00"


@pytest.mark.asyncio
async def test_api_try_set_protocol(mock_aiohttp_client):
    api = ZTERouterAPI(mock_aiohttp_client, "192.168.0.1", "admin", "password")

    # Success on first attempt (http)
    mock_aiohttp_client.get.side_effect = [MockResponse(status=200)]

    await api.try_set_protocol()
    assert api.protocol == "http"
    assert api.referer == "http://192.168.0.1/"


@pytest.mark.asyncio
async def test_api_try_set_protocol_error(mock_aiohttp_client):
    """Test protocol detection with connection errors."""
    api = ZTERouterAPI(mock_aiohttp_client, "192.168.0.1", "admin", "password")
    # Fail both http and https
    mock_aiohttp_client.get.side_effect = Exception("Connect Fail")
    await api.try_set_protocol()
    assert api.protocol == "http"


@pytest.mark.asyncio
async def test_api_get_version(mock_aiohttp_client):
    api = ZTERouterAPI(mock_aiohttp_client, "192.168.0.1", "admin", "password")
    mock_aiohttp_client.get.return_value = MockResponse(
        json_data={"wa_inner_version": "test_v"}
    )
    assert await api.get_version() == "test_v"


@pytest.mark.asyncio
async def test_api_get_version_error(mock_aiohttp_client):
    """Test version fetching error."""
    api = ZTERouterAPI(mock_aiohttp_client, "192.168.0.1", "admin", "password")
    mock_aiohttp_client.get.side_effect = Exception("Fail")
    assert await api.get_version() == ""


@pytest.mark.asyncio
async def test_api_login_success(mock_aiohttp_client):
    api = ZTERouterAPI(mock_aiohttp_client, "192.168.0.1", "admin", "password")

    # LD, Version, then Post for Login
    mock_aiohttp_client.get.side_effect = [
        MockResponse(json_data={"LD": "test_ld"}),
        MockResponse(json_data={"wa_inner_version": "test_v"}),
    ]

    mock_stok_cookie = MagicMock()
    mock_stok_cookie.value = "test_stok"
    mock_aiohttp_client.post.return_value = MockResponse(
        cookies={"stok": mock_stok_cookie}
    )

    stok = await api.login()
    assert stok == "stok=test_stok"
    assert api.stok == "stok=test_stok"


@pytest.mark.asyncio
async def test_api_login_no_password(mock_aiohttp_client):
    """Test login failure when no password provided."""
    api = ZTERouterAPI(mock_aiohttp_client, "192.168.0.1", "admin", "")
    with (
        patch.object(api, "get_LD", return_value="LD"),
        patch.object(api, "get_version", return_value="VER"),
        pytest.raises(Exception, match="No password provided"),
    ):
        await api.login()


@pytest.mark.asyncio
async def test_api_login_failure_no_stok(mock_aiohttp_client):
    """Test login failure when response missing stok."""
    api = ZTERouterAPI(mock_aiohttp_client, "192.168.0.1", "admin", "pass")

    mock_aiohttp_client.get.side_effect = [
        MockResponse(json_data={"LD": "LD"}),
        MockResponse(json_data={"wa_inner_version": "VER"}),
    ]
    mock_aiohttp_client.post.return_value = MockResponse(cookies={})

    with pytest.raises(ZTEAuthError, match="Login failed"):
        await api.login()


@pytest.mark.asyncio
async def test_api_get_all_data_expired_session(mock_aiohttp_client):
    api = ZTERouterAPI(mock_aiohttp_client, "192.168.0.1", "admin", "password")
    api.stok = "stok=old_stok"

    # 1. Expired response (empty network_type/signalbar)
    # 2. Success response after re-login
    mock_aiohttp_client.get.side_effect = [
        MockResponse(json_data={"network_type": "", "signalbar": ""}),
        MockResponse(json_data={"network_type": "LTE", "signalbar": "4"}),
    ]

    with patch.object(api, "login") as mock_login:
        data = await api.get_all_data()
        assert data["network_type"] == "LTE"
        assert mock_login.called


@pytest.mark.asyncio
async def test_api_get_all_data_error(mock_aiohttp_client):
    """Test technical data fetch error."""
    api = ZTERouterAPI(mock_aiohttp_client, "192.168.0.1", "admin", "password")
    api.stok = "stok=test"
    mock_aiohttp_client.get.side_effect = Exception("Network Error")
    with pytest.raises(Exception, match="Network Error"):
        await api.get_all_data()
    assert api.stok is None


@pytest.mark.asyncio
async def test_api_get_sms_capacity(mock_aiohttp_client):
    """Test SMS capacity fetch."""
    api = ZTERouterAPI(mock_aiohttp_client, "192.168.0.1", "admin", "password")
    api.stok = "stok=test"
    mock_aiohttp_client.get.return_value = MockResponse(json_data={"cap": 100})
    assert await api.get_sms_capacity() == {"cap": 100}


@pytest.mark.asyncio
async def test_api_get_sms_capacity_error(mock_aiohttp_client):
    """Test SMS capacity fetch error."""
    api = ZTERouterAPI(mock_aiohttp_client, "192.168.0.1", "admin", "password")
    api.stok = "stok=test"
    mock_aiohttp_client.get.side_effect = Exception("Fail")
    assert await api.get_sms_capacity() == {}


@pytest.mark.asyncio
async def test_api_get_last_sms_content(mock_aiohttp_client):
    """Test last SMS fetching and decoding."""
    api = ZTERouterAPI(mock_aiohttp_client, "192.168.0.1", "admin", "password")
    api.stok = "stok=test"
    mock_aiohttp_client.post.return_value = MockResponse(
        json_data={
            "messages": [
                {
                    "id": "1",
                    "content": "00480065006c006c006f",  # "Hello"
                    "number": "003100320033",  # "123"
                    "date": "23,10,10,10,0,0,+1",
                }
            ]
        }
    )

    msg = await api.get_last_sms_content()
    assert msg["content_decoded"] == "Hello"
    assert msg["number_decoded"] == "123"
    assert msg["date_decoded"] == "2023-10-10T10:00:00"


@pytest.mark.asyncio
async def test_api_get_last_sms_content_empty(mock_aiohttp_client):
    """Test last SMS fetching when mailbox is empty."""
    api = ZTERouterAPI(mock_aiohttp_client, "192.168.0.1", "admin", "password")
    api.stok = "stok=test"
    mock_aiohttp_client.post.return_value = MockResponse(json_data={"messages": []})
    assert await api.get_last_sms_content() == {}


@pytest.mark.asyncio
async def test_api_reboot_success(mock_aiohttp_client):
    """Test reboot command success."""
    api = ZTERouterAPI(mock_aiohttp_client, "192.168.0.1", "admin", "password")
    api.stok = "stok=test"
    with (
        patch.object(api, "login"),
        patch.object(api, "get_AD", return_value="test_ad"),
    ):
        mock_aiohttp_client.post.return_value = MockResponse(status=200)
        assert await api.reboot() == 200


@pytest.mark.asyncio
async def test_api_reboot_error(mock_aiohttp_client):
    """Test reboot command failure."""
    api = ZTERouterAPI(mock_aiohttp_client, "192.168.0.1", "admin", "password")
    api.stok = "stok=test"
    with (
        patch.object(api, "login"),
        patch.object(api, "get_AD", return_value="test_ad"),
        pytest.raises(RuntimeError, match="Fail"),
    ):
        mock_aiohttp_client.post.side_effect = RuntimeError("Fail")
        await api.reboot()
    assert api.stok is None


@pytest.mark.asyncio
async def test_api_delete_sms(mock_aiohttp_client):
    """Test single SMS deletion."""
    api = ZTERouterAPI(mock_aiohttp_client, "192.168.0.1", "admin", "password")
    api.stok = "stok=test"
    with patch.object(api, "get_AD", return_value="test_ad"):
        mock_aiohttp_client.post.return_value = MockResponse(status=200)
        assert await api.delete_sms("1") == 200


@pytest.mark.asyncio
async def test_api_delete_all_success(mock_aiohttp_client):
    """Test bulk SMS deletion logic."""
    api = ZTERouterAPI(mock_aiohttp_client, "192.168.0.1", "admin", "password")
    api.stok = "stok=test"

    mock_aiohttp_client.post.side_effect = [
        MockResponse(json_data={"messages": [{"id": "1"}, {"id": "2"}]}),
        MockResponse(status=200),
    ]

    with patch.object(api, "login"), patch.object(api, "get_AD", return_value="ad"):
        assert await api.delete_all() == 200


@pytest.mark.asyncio
async def test_api_delete_all_empty(mock_aiohttp_client):
    """Test bulk SMS deletion when no messages exist."""
    api = ZTERouterAPI(mock_aiohttp_client, "192.168.0.1", "admin", "password")
    api.stok = "stok=test"
    mock_aiohttp_client.post.return_value = MockResponse(json_data={"messages": []})
    with patch.object(api, "login"):
        assert await api.delete_all() == 200


@pytest.mark.asyncio
async def test_api_get_AD_new_gen(mock_aiohttp_client):
    """Test AD hash generation for new generation models (MC888/MC889)."""
    api = ZTERouterAPI(mock_aiohttp_client, "192.168.0.1", "admin", "password")
    with (
        patch.object(api, "get_version", return_value="MC888_VER"),
        patch.object(api, "get_RD", return_value="test_rd"),
    ):
        ad = await api.get_AD()
        assert len(ad) == 64


@pytest.mark.asyncio
async def test_api_get_RD_error(mock_aiohttp_client):
    """Test RD fetch error."""
    api = ZTERouterAPI(mock_aiohttp_client, "192.168.0.1", "admin", "password")
    mock_aiohttp_client.get.side_effect = Exception("Fail")
    assert await api.get_RD() == ""
