"""Tests for WiFi SSID Monitor coordinator."""

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.wifi_ssid_monitor.api import WifiScanError
from custom_components.wifi_ssid_monitor.const import CONF_INCLUDE_HIDDEN
from custom_components.wifi_ssid_monitor.coordinator import (
    WifiScanCoordinator,
    _channel_to_band,
)


def test_channel_to_band_boundaries():
    """Test _channel_to_band at all boundary values including None, edges, and out-of-range."""  # noqa: E501
    assert _channel_to_band(None) is None
    assert _channel_to_band(0) is None
    assert _channel_to_band(1) == "2.4 GHz"
    assert _channel_to_band(14) == "2.4 GHz"
    assert _channel_to_band(15) is None
    assert _channel_to_band(35) is None
    assert _channel_to_band(36) == "5 GHz"
    assert _channel_to_band(177) == "5 GHz"
    assert _channel_to_band(178) is None


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

    # Covers finding RETVAL.1 from recommendations_20260602.md
    assert "networks" in data
    assert data["networks"]["Net1"]["rssi"] == -55
    assert data["networks"]["Net2"]["rssi"] == -60
    assert data["networks"]["MyNetwork1"]["rssi"] == -40

    assert set(data["last_seen"].keys()) == {"MyNetwork1", "Net1", "Net2"}

    assert data["strongest_unknown_rssi"] == -55

    assert coordinator._failure_count == 0
    assert coordinator.last_update_success_time is not None


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

    with pytest.raises(UpdateFailed, match="Error communicating with API: "):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_update_data_failure(hass, mock_config_entry, mock_wifi_api):
    """Test data update failure."""
    coordinator = WifiScanCoordinator(hass, mock_config_entry, mock_wifi_api, "1.4.0")

    mock_wifi_api.get_access_points.side_effect = WifiScanError("Persistent failure")

    with pytest.raises(
        UpdateFailed,
        match="Error communicating with API: Persistent failure",
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

    # Covers finding RETVAL.2 from recommendations_20260602.md
    assert data["networks"]["VisibleNet"]["band"] == "2.4 GHz"
    assert data["networks"]["[hidden]"]["band"] == "2.4 GHz"

    assert data["strongest_unknown_rssi"] == -50

    assert "VisibleNet" in data["last_seen"]
    assert "[hidden]" in data["last_seen"]


@pytest.mark.asyncio
async def test_coordinator_include_hidden_false(hass, mock_config_entry, mock_wifi_api):
    """Test hidden APs are filtered out when include_hidden is False."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, CONF_INCLUDE_HIDDEN: False},
    )
    coordinator = WifiScanCoordinator(hass, mock_config_entry, mock_wifi_api, "1.4.0")

    mock_wifi_api.get_access_points.return_value = [
        {"ssid": "VisibleA", "signal": -50},
        {"ssid": "VisibleB", "signal": -60},
        {"signal": -70},  # Hidden
        {"signal": -80},  # Hidden
    ]

    data = await coordinator._async_update_data()

    assert data["count"] == 2
    assert "[hidden]" not in data["ssids"]
    assert "[hidden]" not in data["networks"]
    assert data["ssids"] == ["VisibleA", "VisibleB"]


@pytest.mark.asyncio
async def test_coordinator_include_hidden_true(hass, mock_config_entry, mock_wifi_api):
    """Test hidden APs are collected into [hidden] when include_hidden is True."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, CONF_INCLUDE_HIDDEN: True},
    )
    coordinator = WifiScanCoordinator(hass, mock_config_entry, mock_wifi_api, "1.4.0")

    mock_wifi_api.get_access_points.return_value = [
        {"ssid": "VisibleA", "signal": -50},
        {"ssid": "VisibleB", "signal": -60},
        {"signal": -70},  # Hidden
    ]

    data = await coordinator._async_update_data()

    assert "[hidden]" in data["ssids"]
    assert data["count"] == 3


@pytest.mark.asyncio
async def test_coordinator_wildcard_known_ssid(hass, mock_config_entry, mock_wifi_api):
    """Test fnmatch wildcard patterns in known_wifi_ids (Guest_*, IoT_?) matching case-sensitively."""  # noqa: E501
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, "known_wifi_ids": "Guest_*,IoT_?"},
    )
    coordinator = WifiScanCoordinator(hass, mock_config_entry, mock_wifi_api, "1.4.0")

    mock_wifi_api.get_access_points.return_value = [
        {"ssid": "Guest_Home", "signal": -50},
        {"ssid": "Guest_Back", "signal": -55},
        {"ssid": "IoT_1", "signal": -60},
        {"ssid": "guest_home", "signal": -65},
        {"ssid": "Rogue", "signal": -70},
    ]

    data = await coordinator._async_update_data()

    assert data["unknown_ssids"] == ["Rogue", "guest_home"]
    assert data["unknown_count"] == 2
    assert data["count"] == 5


@pytest.mark.asyncio
async def test_coordinator_update_data_api_none(hass, mock_config_entry, mock_wifi_api):
    """Test data update when API returns None (fails rather than swallowing)."""
    coordinator = WifiScanCoordinator(hass, mock_config_entry, mock_wifi_api, "1.4.0")

    mock_wifi_api.get_access_points.return_value = None

    with pytest.raises(
        UpdateFailed,
        match="Error communicating with API: API returned no data",
    ):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_resilience_holds_for_three_failures(
    hass, mock_config_entry, mock_wifi_api
):
    """Test coordinator holds last known values for up to 3 consecutive failures."""
    coordinator = WifiScanCoordinator(hass, mock_config_entry, mock_wifi_api, "1.4.0")

    initial_data = {
        "count": 2,
        "ssids": ["Net1", "Net2"],
        "unknown_ssids": ["Net2"],
        "unknown_count": 1,
        "interface": "wlan0",
        "networks": {},
    }
    coordinator.data = initial_data
    mock_wifi_api.get_access_points.side_effect = WifiScanError("API down")

    # Failures 1, 2, 3 — stale data returned, no exception
    for expected_count in range(1, 4):
        result = await coordinator._async_update_data()
        assert result == initial_data
        assert coordinator._failure_count == expected_count

    # Failure 4 — raises UpdateFailed
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_resilience_resets_on_success(
    hass, mock_config_entry, mock_wifi_api
):
    """Test failure count resets to zero after a successful fetch."""
    coordinator = WifiScanCoordinator(hass, mock_config_entry, mock_wifi_api, "1.4.0")
    coordinator.data = {
        "count": 1,
        "ssids": ["Net1"],
        "unknown_ssids": [],
        "unknown_count": 0,
        "interface": "wlan0",
        "networks": {},
    }

    # Accumulate 2 failures
    mock_wifi_api.get_access_points.side_effect = WifiScanError("fail")
    await coordinator._async_update_data()
    await coordinator._async_update_data()
    assert coordinator._failure_count == 2

    # Successful fetch resets the count
    mock_wifi_api.get_access_points.side_effect = None
    mock_wifi_api.get_access_points.return_value = [{"ssid": "Net1", "signal": -50}]
    await coordinator._async_update_data()
    assert coordinator._failure_count == 0


@pytest.mark.asyncio
async def test_coordinator_async_initialize_with_stored_data(
    hass, mock_config_entry, mock_wifi_api
):
    """Test async_initialize loads persisted last_seen data."""
    coordinator = WifiScanCoordinator(hass, mock_config_entry, mock_wifi_api, "1.4.0")

    # Pre-populate the store with data
    from homeassistant.util import dt as dt_util

    now = dt_util.now()
    await coordinator.store.async_save(
        {"Net1": now.isoformat(), "Net2": now.isoformat()}
    )

    await coordinator.async_initialize()

    assert "Net1" in coordinator._last_seen
    assert isinstance(coordinator._last_seen["Net1"], type(now))


@pytest.mark.asyncio
async def test_coordinator_async_initialize_with_corrupt_data(
    hass, mock_config_entry, mock_wifi_api
):
    """Test async_initialize gracefully handles corrupt stored data."""
    coordinator = WifiScanCoordinator(hass, mock_config_entry, mock_wifi_api, "1.4.0")

    # Save invalid ISO format data
    await coordinator.store.async_save({"Net1": "not-a-valid-date"})

    # Should not raise - warning logged and empty history used
    await coordinator.async_initialize()

    assert coordinator._last_seen == {}


@pytest.mark.asyncio
async def test_coordinator_band_filtering_2ghz(hass, mock_config_entry, mock_wifi_api):
    """Test band filtering restricts to 2.4 GHz only."""
    from custom_components.wifi_ssid_monitor.const import CONF_SCAN_BANDS

    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, CONF_SCAN_BANDS: "2.4"},
    )
    coordinator = WifiScanCoordinator(hass, mock_config_entry, mock_wifi_api, "1.4.0")

    mock_wifi_api.get_access_points.return_value = [
        {"ssid": "Net2G", "channel": 6},  # 2.4 GHz
        {"ssid": "Net5G", "channel": 36},  # 5 GHz
        {"ssid": "NetUnknown", "channel": 99},  # Unknown band
    ]

    data = await coordinator._async_update_data()

    assert data["ssids"] == ["Net2G"]
    assert data["count"] == 1


@pytest.mark.asyncio
async def test_coordinator_band_filtering_5ghz(hass, mock_config_entry, mock_wifi_api):
    """Test band filtering restricts to 5 GHz only."""
    from custom_components.wifi_ssid_monitor.const import CONF_SCAN_BANDS

    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, CONF_SCAN_BANDS: "5"},
    )
    coordinator = WifiScanCoordinator(hass, mock_config_entry, mock_wifi_api, "1.4.0")

    mock_wifi_api.get_access_points.return_value = [
        {"ssid": "Net2G", "channel": 6},  # 2.4 GHz
        {"ssid": "Net5G", "channel": 36},  # 5 GHz
    ]

    data = await coordinator._async_update_data()

    assert data["ssids"] == ["Net5G"]
    assert data["count"] == 1
