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


# ---------------------------------------------------------------------------
# Section 20 — a log line is not a diagnostics download
# ---------------------------------------------------------------------------
#
# A diagnostics file has a redaction layer; a log file
# has none, and users are routinely asked to paste one into a public issue. So
# the shape of a payload may be logged and the payload itself may not — a
# neighbouring network's SSID and BSSID are personal data about someone who
# never installed this integration.
#
# This asserts the property rather than the wording, so a future rewrite of the
# message cannot quietly reintroduce the values.


@pytest.mark.asyncio
async def test_the_ap_sample_log_carries_keys_and_never_values(
    mock_aiohttp_client, caplog
):
    """The drift log names the fields, not what is in them."""
    import logging

    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = WifiScanAPI(mock_aiohttp_client, "wlan0")
        mock_aiohttp_client.get.return_value = MockResponse(
            json_data={
                "data": {
                    "accesspoints": [
                        {
                            "ssid": "TheNeighbours",
                            "mac": "AA:BB:CC:DD:EE:FF",
                            "signal": 70,
                        }
                    ]
                }
            }
        )

        with caplog.at_level(logging.DEBUG):
            await api.get_access_points()

    assert "ssid" in caplog.text, "the key set is the point of the line"
    assert "TheNeighbours" not in caplog.text
    assert "AA:BB:CC:DD:EE:FF" not in caplog.text


# ---------------------------------------------------------------------------
# Rejected-response record (`last_rejection`), published by the diagnostics
# download. Structure only, never access-point data.
# ---------------------------------------------------------------------------


def _api(mock_aiohttp_client, response):
    mock_aiohttp_client.get.return_value = response
    return WifiScanAPI(mock_aiohttp_client, "wlan0")


@pytest.mark.asyncio
async def test_a_non_200_response_is_retained_with_its_status_and_text(
    mock_aiohttp_client,
):
    """A non-200 keeps status, class, content type, length and the body text."""
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = _api(
            mock_aiohttp_client,
            MockResponse(
                status=500,
                text_data="Internal Server Error",
                headers={"Content-Type": "text/plain"},
            ),
        )
        with pytest.raises(WifiScanError):
            await api.get_access_points()

    record = api.last_rejection
    assert record is not None
    assert record["http_status"] == 500
    assert record["failure_class"] == "http_error"
    assert record["content_type"] == "text/plain"
    assert record["text_length"] == len("Internal Server Error")
    assert record["text"] == "Internal Server Error"
    assert record["recorded_at"].endswith("+00:00")
    assert "key_names" not in record


@pytest.mark.asyncio
async def test_a_mac_in_an_error_body_is_scrubbed_in_every_form(mock_aiohttp_client):
    """Colon, dash and dotted MACs in an error body never reach the record."""
    body = "bad aa:bb:cc:dd:ee:ff then AA-BB-CC-DD-EE-FF then aabb.ccdd.eeff end"
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = _api(mock_aiohttp_client, MockResponse(status=500, text_data=body))
        with pytest.raises(WifiScanError):
            await api.get_access_points()

    assert api.last_rejection is not None
    assert (
        api.last_rejection["text"]
        == "bad [REDACTED_MAC] then [REDACTED_MAC] then [REDACTED_MAC] end"
    )


@pytest.mark.asyncio
async def test_a_uuid_hash_or_timestamp_in_an_error_body_is_not_altered(
    mock_aiohttp_client,
):
    """Only MAC-shaped text is replaced; other hex-looking text is kept."""
    body = (
        "id 123e4567-e89b-12d3-a456-426614174000 "
        "sha 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08 "
        "at 2026-10-02T12:34:56+00:00 ip 10.0.0.1"
    )
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = _api(mock_aiohttp_client, MockResponse(status=500, text_data=body))
        with pytest.raises(WifiScanError):
            await api.get_access_points()

    assert api.last_rejection is not None
    assert api.last_rejection["text"] == body


@pytest.mark.asyncio
async def test_error_text_is_scrubbed_before_it_is_capped(mock_aiohttp_client):
    """A MAC straddling the cap is replaced whole, not cut into a fragment."""
    body = "x" * 495 + "aa:bb:cc:dd:ee:ff" + "y" * 50
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = _api(mock_aiohttp_client, MockResponse(status=500, text_data=body))
        with pytest.raises(WifiScanError):
            await api.get_access_points()

    assert api.last_rejection is not None
    text = api.last_rejection["text"]
    assert len(text) == 500
    assert "aa:bb" not in text
    assert text.endswith("[REDA")
    assert api.last_rejection["text_length"] == len(body)


@pytest.mark.asyncio
async def test_a_200_that_fails_json_parsing_keeps_no_body(mock_aiohttp_client):
    """An unparsable 200 records status and class, with no text and no keys."""
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = _api(
            mock_aiohttp_client,
            MockResponse(
                json_error=True,
                text_data="<html>aa:bb:cc:dd:ee:ff</html>",
                headers={"Content-Type": "text/html"},
            ),
        )
        with pytest.raises(WifiScanError, match="Invalid API response"):
            await api.get_access_points()

    record = api.last_rejection
    assert record is not None
    assert record["http_status"] == 200
    assert record["failure_class"] == "invalid_json"
    assert record["content_type"] == "text/html"
    assert "text" not in record
    assert "text_length" not in record
    assert "key_names" not in record


@pytest.mark.asyncio
async def test_a_200_with_no_access_point_list_keeps_the_record(mock_aiohttp_client):
    """A 200 with no `accesspoints` list is a rejection and keeps its record."""
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = _api(
            mock_aiohttp_client,
            MockResponse(json_data={"result": "ok", "data": {"interfaces": []}}),
        )
        assert await api.get_access_points() == []

    record = api.last_rejection
    assert record is not None
    assert record["http_status"] == 200
    assert record["failure_class"] == "missing_ap_key"
    assert record["content_type"] == "application/json"
    assert record["key_names"] == ["interfaces"]
    assert record["other_key_count"] == 0
    assert "text" not in record


@pytest.mark.asyncio
async def test_only_a_later_successful_scan_clears_the_record(mock_aiohttp_client):
    """The record survives another rejection and a connection error, not a success."""
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = _api(mock_aiohttp_client, MockResponse(json_data={"data": {}}))
        await api.get_access_points()
        assert api.last_rejection is not None

        mock_aiohttp_client.get.side_effect = aiohttp.ClientError("down")
        with pytest.raises(WifiScanError):
            await api.get_access_points()
        assert api.last_rejection is not None
        assert api.last_rejection["failure_class"] == "missing_ap_key"

        mock_aiohttp_client.get.side_effect = None
        mock_aiohttp_client.get.return_value = MockResponse(
            json_data={"data": {"accesspoints": []}}
        )
        await api.get_access_points()
        assert api.last_rejection is None


@pytest.mark.asyncio
async def test_key_names_are_listed_only_where_they_look_like_field_names(
    mock_aiohttp_client,
):
    """Under payload drift an SSID-shaped key is counted, never named."""
    data = {
        "interfaces": [],
        "scan_state": 1,
        "HomeNet": 2,
        "Cafe Guest": 3,
        "a" * 33: 4,
    }
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = _api(mock_aiohttp_client, MockResponse(json_data={"data": data}))
        await api.get_access_points()

    assert api.last_rejection is not None
    assert api.last_rejection["key_names"] == ["interfaces", "scan_state"]
    assert api.last_rejection["other_key_count"] == 3


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"data": ["x"]},
        {"data": "text"},
        {"data": 5},
        {"data": None},
        {"data": {}},
        {"result": "ok"},
        ["not", "an", "object"],
        "scalar",
    ],
)
async def test_a_payload_with_no_object_data_records_no_key_names(
    mock_aiohttp_client, payload
):
    """Non-object or empty `data` is a missing list, with no key names recorded."""
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = _api(mock_aiohttp_client, MockResponse(json_data=payload))
        assert await api.get_access_points() == []

    assert api.last_response_had_ap_key is False
    assert api.last_rejection is not None
    assert api.last_rejection["failure_class"] == "missing_ap_key"
    assert "key_names" not in api.last_rejection


@pytest.mark.asyncio
async def test_a_non_string_content_type_is_not_retained(mock_aiohttp_client):
    """A header value that is not text is recorded as None."""
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = _api(
            mock_aiohttp_client,
            MockResponse(json_data={"data": {}}, headers={"Content-Type": 5}),
        )
        await api.get_access_points()

    assert api.last_rejection is not None
    assert api.last_rejection["content_type"] is None


@pytest.mark.asyncio
async def test_a_response_with_no_headers_mapping_records_no_content_type(
    mock_aiohttp_client,
):
    """A response object without a headers mapping does not break the capture."""
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        response = MockResponse(json_data={"data": {}})
        response.headers = None
        api = _api(mock_aiohttp_client, response)
        await api.get_access_points()

    assert api.last_rejection is not None
    assert api.last_rejection["content_type"] is None


@pytest.mark.asyncio
async def test_a_hex_run_that_only_contains_a_mac_shape_is_not_altered(
    mock_aiohttp_client,
):
    """The MAC scrub is bounded on both sides by non-hex characters.

    ``0aa:bb:cc:dd:ee:ff`` and ``aa:bb:cc:dd:ee:fff`` are longer hex runs, not
    MACs, so neither is altered, which is what keeps a hash or an identifier
    in an error body from being cut up.
    """
    body = "run 0aa:bb:cc:dd:ee:ff and aa:bb:cc:dd:ee:fff end"
    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = _api(mock_aiohttp_client, MockResponse(status=500, text_data=body))
        with pytest.raises(WifiScanError):
            await api.get_access_points()

    assert api.last_rejection is not None
    assert api.last_rejection["text"] == body
