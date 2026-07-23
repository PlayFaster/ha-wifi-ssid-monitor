"""Tests for WiFi SSID Monitor setup and unload."""

from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.mark.asyncio
async def test_setup_unload_entry(hass: HomeAssistant, mock_config_entry):
    """Test setting up and unloading the integration."""
    mock_config_entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
            return_value=[],
        ),
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.runtime_data is not None

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()


@pytest.mark.asyncio
async def test_async_setup_entry_title_migration(
    hass: HomeAssistant, mock_config_entry
):
    """Test that the config entry title is migrated if it's the only one."""
    from custom_components.wifi_ssid_monitor.const import DEFAULT_NAME

    # Set the old title format
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry, title=f"{DEFAULT_NAME} (wlan0)"
    )

    with (
        patch(
            "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
            return_value=[],
        ),
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # Title should have been migrated
    assert mock_config_entry.title == DEFAULT_NAME


@pytest.mark.asyncio
async def test_async_setup_entry_data_migration(hass: HomeAssistant):
    """Test migration from entry.data to entry.options when entry has old data."""
    from custom_components.wifi_ssid_monitor.const import (
        CONF_INTERFACE,
        CONF_KNOWN_SSIDS,
        CONF_SCAN_INTERVAL,
        DOMAIN,
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="wifi_ssid_monitor_wlan0",
        title="WiFi SSID Monitor",
        data={
            CONF_INTERFACE: "wlan0",
            CONF_KNOWN_SSIDS: "MyNetwork1",
        },
        options={},
        entry_id="test_entry_id_migrate",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.data == {}
    assert entry.options.get(CONF_INTERFACE) == "wlan0"
    assert entry.options.get(CONF_KNOWN_SSIDS) == "MyNetwork1"
    assert entry.options.get(CONF_SCAN_INTERVAL) == 600


@pytest.mark.asyncio
async def test_async_setup_entry_migrate_legacy_proximity_dbm(
    hass: HomeAssistant,
):
    """Legacy proximity_rssi_threshold (dBm, negative) is migrated to percent."""
    from custom_components.wifi_ssid_monitor.const import (
        CONF_INTERFACE,
        CONF_PROXIMITY_SIGNAL_THRESHOLD,
        CONF_SCAN_INTERVAL,
        DEFAULT_SCAN_INTERVAL,
        DOMAIN,
        LEGACY_CONF_PROXIMITY_RSSI_THRESHOLD,
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="wifi_ssid_monitor_wlan0_mig_prox",
        title="WiFi SSID Monitor",
        data={},
        options={
            CONF_INTERFACE: "wlan0",
            LEGACY_CONF_PROXIMITY_RSSI_THRESHOLD: -60,
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
        },
        entry_id="test_entry_prox_mig",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert LEGACY_CONF_PROXIMITY_RSSI_THRESHOLD not in entry.options
    assert entry.options[CONF_PROXIMITY_SIGNAL_THRESHOLD] == 80


@pytest.mark.asyncio
async def test_async_setup_entry_migrate_legacy_proximity_bad_type(
    hass: HomeAssistant,
):
    """Unparsable legacy proximity threshold defaults to the normal default."""
    from custom_components.wifi_ssid_monitor.const import (
        CONF_INTERFACE,
        CONF_PROXIMITY_SIGNAL_THRESHOLD,
        CONF_SCAN_INTERVAL,
        DEFAULT_PROXIMITY_SIGNAL_THRESHOLD,
        DEFAULT_SCAN_INTERVAL,
        DOMAIN,
        LEGACY_CONF_PROXIMITY_RSSI_THRESHOLD,
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="wifi_ssid_monitor_wlan0_mig_prox_bad",
        title="WiFi SSID Monitor",
        data={},
        options={
            CONF_INTERFACE: "wlan0",
            LEGACY_CONF_PROXIMITY_RSSI_THRESHOLD: "not-a-number",
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
        },
        entry_id="test_entry_prox_bad",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert (
        entry.options[CONF_PROXIMITY_SIGNAL_THRESHOLD]
        == DEFAULT_PROXIMITY_SIGNAL_THRESHOLD
    )


@pytest.mark.asyncio
async def test_async_setup_entry_migrate_legacy_proximity_already_present(
    hass: HomeAssistant,
):
    """When the new key already exists, legacy is not migrated over it."""
    from custom_components.wifi_ssid_monitor.const import (
        CONF_INTERFACE,
        CONF_PROXIMITY_SIGNAL_THRESHOLD,
        CONF_SCAN_INTERVAL,
        DEFAULT_SCAN_INTERVAL,
        DOMAIN,
        LEGACY_CONF_PROXIMITY_RSSI_THRESHOLD,
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="wifi_ssid_monitor_wlan0_mig_prox_exist",
        title="WiFi SSID Monitor",
        data={},
        options={
            CONF_INTERFACE: "wlan0",
            LEGACY_CONF_PROXIMITY_RSSI_THRESHOLD: -50,
            CONF_PROXIMITY_SIGNAL_THRESHOLD: 90,
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
        },
        entry_id="test_entry_prox_exist",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.options[CONF_PROXIMITY_SIGNAL_THRESHOLD] == 90


@pytest.mark.asyncio
async def test_async_setup_entry_migrate_legacy_proximity_positive(
    hass: HomeAssistant,
):
    """A positive legacy value is treated as already percentage."""
    from custom_components.wifi_ssid_monitor.const import (
        CONF_INTERFACE,
        CONF_PROXIMITY_SIGNAL_THRESHOLD,
        CONF_SCAN_INTERVAL,
        DEFAULT_SCAN_INTERVAL,
        DOMAIN,
        LEGACY_CONF_PROXIMITY_RSSI_THRESHOLD,
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="wifi_ssid_monitor_wlan0_mig_prox_pos",
        title="WiFi SSID Monitor",
        data={},
        options={
            CONF_INTERFACE: "wlan0",
            LEGACY_CONF_PROXIMITY_RSSI_THRESHOLD: 75,
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
        },
        entry_id="test_entry_prox_pos",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.options[CONF_PROXIMITY_SIGNAL_THRESHOLD] == 75


@pytest.mark.asyncio
async def test_async_setup_entry_migrate_legacy_scan_bands_all(
    hass: HomeAssistant,
):
    """Legacy scan_bands='all' enables all three band switches."""
    from custom_components.wifi_ssid_monitor.const import (
        CONF_INTERFACE,
        CONF_SCAN_INTERVAL,
        CONF_SHOW_5GHZ,
        CONF_SHOW_6GHZ,
        CONF_SHOW_24GHZ,
        DEFAULT_SCAN_INTERVAL,
        DOMAIN,
        LEGACY_CONF_SCAN_BANDS,
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="wifi_ssid_monitor_wlan0_mig_bands",
        title="WiFi SSID Monitor",
        data={},
        options={
            CONF_INTERFACE: "wlan0",
            LEGACY_CONF_SCAN_BANDS: "all",
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
        },
        entry_id="test_entry_bands_all",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert LEGACY_CONF_SCAN_BANDS not in entry.options
    assert entry.options[CONF_SHOW_24GHZ] is True
    assert entry.options[CONF_SHOW_5GHZ] is True
    assert entry.options[CONF_SHOW_6GHZ] is True


@pytest.mark.asyncio
async def test_get_networks_service(hass: HomeAssistant, mock_config_entry):
    """Test the get_networks service returns networks data."""
    from custom_components.wifi_ssid_monitor.const import DOMAIN

    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    result = await hass.services.async_call(
        DOMAIN,
        "get_networks",
        {"scope": "all", "band": "all"},
        blocking=True,
        return_response=True,
    )

    assert "networks" in result
    assert "count" in result
    assert "total_matched" in result


@pytest.mark.asyncio
async def test_get_networks_service_with_data(
    hass: HomeAssistant, mock_config_entry, mock_coordinator
):
    """Test the get_networks service with network data."""
    from custom_components.wifi_ssid_monitor.const import DOMAIN

    mock_config_entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
            return_value=[],
        ),
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # Inject data directly into the coordinator
    coordinator = mock_config_entry.runtime_data
    coordinator.data = {
        "count": 2,
        "ssids": ["MyNetwork1", "UnknownNet"],
        "unknown_ssids": ["UnknownNet"],
        "unknown_count": 1,
        "interface": "wlan0",
        "networks": {
            "MyNetwork1": {
                "bssid": "AA:BB:CC:00:00:01",
                "signal": 80,
                "channel": 11,
                "band": "2.4 GHz",
                "hidden": False,
                "ssid_anomaly": False,
                "mode": "infrastructure",
                "key": "MyNetwork1",
            },
            "UnknownNet": {
                "bssid": "AA:BB:CC:00:00:02",
                "signal": 55,
                "channel": 48,
                "band": "5 GHz",
                "hidden": False,
                "ssid_anomaly": False,
                "mode": "infrastructure",
                "key": "UnknownNet",
            },
        },
        "last_seen": {"UnknownNet": "2026-07-22T11:00:00"},
        "first_seen": {"UnknownNet": "2026-07-01T09:00:00"},
        "visit_counts": {"UnknownNet": 42},
        "new_24h": 0,
        "strongest_unknown_signal": 55,
        "strongest_unknown_ssid": "UnknownNet",
        "signal_unit": "percent",
    }

    result = await hass.services.async_call(
        DOMAIN,
        "get_networks",
        {"scope": "unknown", "band": "5", "quantity": 10},
        blocking=True,
        return_response=True,
    )

    assert result["count"] == 1
    assert result["total_matched"] == 1
    assert result["networks"][0]["ssid"] == "UnknownNet"
    assert result["networks"][0]["band"] == "5 GHz"


@pytest.mark.asyncio
async def test_get_networks_service_filters(hass: HomeAssistant, mock_config_entry):
    """Test the get_networks service filter parameters."""
    from custom_components.wifi_ssid_monitor.const import DOMAIN

    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    coordinator = mock_config_entry.runtime_data
    coordinator.data = {
        "count": 4,
        "ssids": ["Known1", "Known2", "UnkA", "UnkB"],
        "unknown_ssids": ["UnkA", "UnkB"],
        "unknown_count": 2,
        "interface": "wlan0",
        "networks": {
            "Known1": {
                "bssid": "AA:BB:CC:00:00:01",
                "signal": 90,
                "channel": 6,
                "band": "2.4 GHz",
                "hidden": False,
                "ssid_anomaly": False,
                "mode": "infrastructure",
                "key": "Known1",
            },
            "Known2": {
                "bssid": "AA:BB:CC:00:00:02",
                "signal": 85,
                "channel": 36,
                "band": "5 GHz",
                "hidden": False,
                "ssid_anomaly": False,
                "mode": "infrastructure",
                "key": "Known2",
            },
            "UnkA": {
                "bssid": "AA:BB:CC:00:00:03",
                "signal": 60,
                "channel": 1,
                "band": "2.4 GHz",
                "hidden": False,
                "ssid_anomaly": False,
                "mode": "infrastructure",
                "key": "UnkA",
            },
            "UnkB": {
                "bssid": "AA:BB:CC:00:00:04",
                "signal": 40,
                "channel": 11,
                "band": "2.4 GHz",
                "hidden": False,
                "ssid_anomaly": False,
                "mode": "infrastructure",
                "key": "UnkB",
            },
        },
        "last_seen": {},
        "first_seen": {},
        "visit_counts": {},
        "new_24h": 0,
        "strongest_unknown_signal": 60,
        "strongest_unknown_ssid": "UnkA",
        "signal_unit": "percent",
    }

    # known scope: only known networks
    result1 = await hass.services.async_call(
        DOMAIN,
        "get_networks",
        {"scope": "known", "band": "all"},
        blocking=True,
        return_response=True,
    )
    assert result1["total_matched"] == 2
    assert {n["ssid"] for n in result1["networks"]} == {"Known1", "Known2"}

    # specific band filter
    result2 = await hass.services.async_call(
        DOMAIN,
        "get_networks",
        {"scope": "all", "band": "2.4"},
        blocking=True,
        return_response=True,
    )
    assert result2["total_matched"] == 3
    assert all(n["band"] == "2.4 GHz" for n in result2["networks"])

    # min_signal filter
    result3 = await hass.services.async_call(
        DOMAIN,
        "get_networks",
        {"scope": "all", "band": "all", "min_signal": 85},
        blocking=True,
        return_response=True,
    )
    assert result3["total_matched"] == 2

    # keyword filter
    result4 = await hass.services.async_call(
        DOMAIN,
        "get_networks",
        {"scope": "all", "band": "all", "keyword": "unk"},
        blocking=True,
        return_response=True,
    )
    assert result4["total_matched"] == 2

    # exclude filter
    result5 = await hass.services.async_call(
        DOMAIN,
        "get_networks",
        {"scope": "all", "band": "all", "exclude": "known"},
        blocking=True,
        return_response=True,
    )
    assert result5["total_matched"] == 2

    # quantity cap
    result6 = await hass.services.async_call(
        DOMAIN,
        "get_networks",
        {"scope": "all", "band": "all", "quantity": 1},
        blocking=True,
        return_response=True,
    )
    assert result6["count"] == 1
    assert len(result6["networks"]) == 1


@pytest.mark.asyncio
async def test_add_known_ssid_service(hass: HomeAssistant, mock_config_entry):
    """Test the add_ssid service."""
    from custom_components.wifi_ssid_monitor.const import (
        CONF_KNOWN_SSIDS,
        DOMAIN,
    )

    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        "add_ssid",
        {"ssid": "NewSSID"},
        blocking=True,
    )

    current = mock_config_entry.options.get(CONF_KNOWN_SSIDS, "")
    assert "NewSSID" in current


@pytest.mark.asyncio
async def test_add_known_ssid_service_already_exists(
    hass: HomeAssistant, mock_config_entry
):
    """Test the add_ssid service when SSID already exists."""
    from custom_components.wifi_ssid_monitor.const import (
        CONF_KNOWN_SSIDS,
        DOMAIN,
    )

    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    original = mock_config_entry.options.get(CONF_KNOWN_SSIDS, "")

    await hass.services.async_call(
        DOMAIN,
        "add_ssid",
        {"ssid": "MyNetwork1"},
        blocking=True,
    )

    assert mock_config_entry.options.get(CONF_KNOWN_SSIDS, "") == original


@pytest.mark.asyncio
async def test_add_known_ssid_service_with_entry_id(
    hass: HomeAssistant, mock_config_entry
):
    """Test the add_ssid service with a specific config_entry_id."""
    from custom_components.wifi_ssid_monitor.const import (
        CONF_KNOWN_SSIDS,
        DOMAIN,
    )

    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        "add_ssid",
        {"ssid": "NewSSID", "config_entry_id": mock_config_entry.entry_id},
        blocking=True,
    )

    current = mock_config_entry.options.get(CONF_KNOWN_SSIDS, "")
    assert "NewSSID" in current


@pytest.mark.asyncio
async def test_add_known_ssid_service_deduplication(
    hass: HomeAssistant, mock_config_entry
):
    """Test add_ssid service deduplicates a runtime-added SSID."""
    from custom_components.wifi_ssid_monitor.const import (
        CONF_KNOWN_SSIDS,
        DOMAIN,
    )

    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        "add_ssid",
        {"ssid": "BrandNew"},
        blocking=True,
    )

    options_after_first = mock_config_entry.options.get(CONF_KNOWN_SSIDS, "")

    await hass.services.async_call(
        DOMAIN,
        "add_ssid",
        {"ssid": "BrandNew"},
        blocking=True,
    )

    options_after_second = mock_config_entry.options.get(CONF_KNOWN_SSIDS, "")
    assert options_after_second == options_after_first
    assert options_after_first.count("BrandNew") == 1


@pytest.mark.asyncio
async def test_async_reload_entry(hass: HomeAssistant, mock_config_entry):
    """Test reloading the entry."""
    mock_config_entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
            return_value=[],
        ),
        patch("homeassistant.config_entries.ConfigEntries.async_reload") as mock_reload,
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        from custom_components.wifi_ssid_monitor.const import CONF_INTERFACE

        # Update options to change interface and trigger reload branch
        new_options = {**mock_config_entry.options, CONF_INTERFACE: "wlan1"}
        hass.config_entries.async_update_entry(mock_config_entry, options=new_options)
        await hass.async_block_till_done()

        mock_reload.assert_called_once_with(mock_config_entry.entry_id)


@pytest.mark.asyncio
async def test_async_reload_entry_options(hass: HomeAssistant, mock_config_entry):
    """Test reloading entry options without full reload."""
    mock_config_entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
            return_value=[],
        ),
        patch(
            "custom_components.wifi_ssid_monitor.coordinator.WifiScanCoordinator.async_refresh"
        ) as mock_refresh,
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Refresh is called once during setup now (background task)
        assert mock_refresh.call_count == 1
        mock_refresh.reset_mock()

        from custom_components.wifi_ssid_monitor.const import (
            CONF_KNOWN_SSIDS,
            CONF_SCAN_INTERVAL,
        )

        coordinator = mock_config_entry.runtime_data

        # Update scan interval
        new_options = {**mock_config_entry.options, CONF_SCAN_INTERVAL: 120}
        hass.config_entries.async_update_entry(mock_config_entry, options=new_options)
        await hass.async_block_till_done()

        assert coordinator.update_interval.total_seconds() == 120
        mock_refresh.assert_not_called()

        # Update known SSIDs
        new_options = {**mock_config_entry.options, CONF_KNOWN_SSIDS: "NewNet"}
        hass.config_entries.async_update_entry(mock_config_entry, options=new_options)
        await hass.async_block_till_done()

        mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_setup_entry_failure(hass: HomeAssistant, mock_config_entry):
    """Test setup entry failure when integration cannot be loaded."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.WifiScanCoordinator",
        side_effect=Exception("Coordinator creation failed"),
    ):
        assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert getattr(mock_config_entry, "runtime_data", None) is None


@pytest.mark.asyncio
async def test_add_known_ssid_service_invalid_entry_id(
    hass: HomeAssistant, mock_config_entry
):
    """Test add_known_ssid service raises HomeAssistantError with bogus entry_id."""
    from homeassistant.exceptions import HomeAssistantError

    from custom_components.wifi_ssid_monitor.const import DOMAIN

    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    with pytest.raises(HomeAssistantError, match=r"No .* entry found with ID"):
        await hass.services.async_call(
            DOMAIN,
            "add_ssid",
            {"ssid": "NewSSID", "config_entry_id": "nonexistent_id"},
            blocking=True,
        )


@pytest.mark.asyncio
async def test_remove_known_ssid_service(hass: HomeAssistant, mock_config_entry):
    """Test the remove_ssid service."""
    from custom_components.wifi_ssid_monitor.const import CONF_KNOWN_SSIDS, DOMAIN

    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert "MyNetwork1" in mock_config_entry.options.get(CONF_KNOWN_SSIDS, "")

    await hass.services.async_call(
        DOMAIN,
        "remove_ssid",
        {"ssid": "MyNetwork1"},
        blocking=True,
    )

    current = mock_config_entry.options.get(CONF_KNOWN_SSIDS, "")
    assert "MyNetwork1" not in current


@pytest.mark.asyncio
async def test_remove_known_ssid_service_not_present(
    hass: HomeAssistant, mock_config_entry
):
    """Test remove_ssid when SSID is not present (silent success)."""
    from custom_components.wifi_ssid_monitor.const import CONF_KNOWN_SSIDS, DOMAIN

    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    original = mock_config_entry.options.get(CONF_KNOWN_SSIDS, "")

    await hass.services.async_call(
        DOMAIN,
        "remove_ssid",
        {"ssid": "NonExistentSSID"},
        blocking=True,
    )

    assert mock_config_entry.options.get(CONF_KNOWN_SSIDS, "") == original


@pytest.mark.asyncio
async def test_remove_known_ssid_service_with_entry_id(
    hass: HomeAssistant, mock_config_entry
):
    """Test the remove_ssid service with a specific config_entry_id."""
    from custom_components.wifi_ssid_monitor.const import CONF_KNOWN_SSIDS, DOMAIN

    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        "remove_ssid",
        {"ssid": "MyNetwork1", "config_entry_id": mock_config_entry.entry_id},
        blocking=True,
    )

    current = mock_config_entry.options.get(CONF_KNOWN_SSIDS, "")
    assert "MyNetwork1" not in current


@pytest.mark.asyncio
async def test_remove_known_ssid_service_invalid_entry_id(
    hass: HomeAssistant, mock_config_entry
):
    """Test remove_ssid service raises HomeAssistantError with bogus entry_id."""
    from homeassistant.exceptions import HomeAssistantError

    from custom_components.wifi_ssid_monitor.const import DOMAIN

    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    with pytest.raises(HomeAssistantError, match=r"No .* entry found with ID"):
        await hass.services.async_call(
            DOMAIN,
            "remove_ssid",
            {"ssid": "MyNetwork1", "config_entry_id": "nonexistent_id"},
            blocking=True,
        )


@pytest.mark.asyncio
async def test_async_remove_entry(hass: HomeAssistant, mock_config_entry):
    """Test async_remove_entry removes stored data."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # Remove the entry, which triggers async_remove_entry
    await hass.config_entries.async_remove(mock_config_entry.entry_id)
    await hass.async_block_till_done()


@pytest.mark.asyncio
async def test_scan_now_service(hass: HomeAssistant, mock_config_entry):
    """Test the scan_now service triggers a coordinator refresh."""
    from custom_components.wifi_ssid_monitor.const import DOMAIN

    mock_config_entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
            return_value=[],
        ),
        patch(
            "custom_components.wifi_ssid_monitor.coordinator.WifiScanCoordinator.async_refresh"
        ) as mock_refresh,
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        mock_refresh.reset_mock()

        await hass.services.async_call(DOMAIN, "scan_now", {}, blocking=True)
        await hass.async_block_till_done()

        mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_scan_now_service_with_entry_id(hass: HomeAssistant, mock_config_entry):
    """Test the scan_now service with a specific config_entry_id."""
    from custom_components.wifi_ssid_monitor.const import DOMAIN

    mock_config_entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
            return_value=[],
        ),
        patch(
            "custom_components.wifi_ssid_monitor.coordinator.WifiScanCoordinator.async_refresh"
        ) as mock_refresh,
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        mock_refresh.reset_mock()

        await hass.services.async_call(
            DOMAIN,
            "scan_now",
            {"config_entry_id": mock_config_entry.entry_id},
            blocking=True,
        )
        await hass.async_block_till_done()

        mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_scan_now_service_invalid_entry_id(
    hass: HomeAssistant, mock_config_entry
):
    """Test scan_now service raises HomeAssistantError with bogus entry_id."""
    from homeassistant.exceptions import HomeAssistantError

    from custom_components.wifi_ssid_monitor.const import DOMAIN

    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    with pytest.raises(HomeAssistantError, match=r"No .* entry found with ID"):
        await hass.services.async_call(
            DOMAIN,
            "scan_now",
            {"config_entry_id": "nonexistent_id"},
            blocking=True,
        )


@pytest.mark.asyncio
async def test_clear_last_seen_service(hass: HomeAssistant, mock_config_entry):
    """Test the clear_last_seen service clears coordinator history."""
    from custom_components.wifi_ssid_monitor.const import DOMAIN

    mock_config_entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
            return_value=[],
        ),
        patch(
            "custom_components.wifi_ssid_monitor.coordinator.WifiScanCoordinator.async_clear_history"
        ) as mock_clear,
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        await hass.services.async_call(DOMAIN, "clear_last_seen", {}, blocking=True)
        await hass.async_block_till_done()

        mock_clear.assert_called_once()


@pytest.mark.asyncio
async def test_clear_last_seen_service_with_entry_id(
    hass: HomeAssistant, mock_config_entry
):
    """Test the clear_last_seen service with a specific config_entry_id."""
    from custom_components.wifi_ssid_monitor.const import DOMAIN

    mock_config_entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
            return_value=[],
        ),
        patch(
            "custom_components.wifi_ssid_monitor.coordinator.WifiScanCoordinator.async_clear_history"
        ) as mock_clear,
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        await hass.services.async_call(
            DOMAIN,
            "clear_last_seen",
            {"config_entry_id": mock_config_entry.entry_id},
            blocking=True,
        )
        await hass.async_block_till_done()

        mock_clear.assert_called_once()


@pytest.mark.asyncio
async def test_clear_last_seen_service_invalid_entry_id(
    hass: HomeAssistant, mock_config_entry
):
    """Test clear_last_seen service raises HomeAssistantError with bogus entry_id."""
    from homeassistant.exceptions import HomeAssistantError

    from custom_components.wifi_ssid_monitor.const import DOMAIN

    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    with pytest.raises(HomeAssistantError, match=r"No .* entry found with ID"):
        await hass.services.async_call(
            DOMAIN,
            "clear_last_seen",
            {"config_entry_id": "nonexistent_id"},
            blocking=True,
        )


@pytest.mark.asyncio
async def test_set_known_ssids_service(hass: HomeAssistant, mock_config_entry):
    """Test the set_ssids service."""
    from custom_components.wifi_ssid_monitor.const import CONF_KNOWN_SSIDS, DOMAIN

    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    result = await hass.services.async_call(
        DOMAIN,
        "set_ssids",
        {"values": "ReplacedNet1,ReplacedNet2"},
        blocking=True,
        return_response=True,
    )

    assert (
        mock_config_entry.options.get(CONF_KNOWN_SSIDS) == "ReplacedNet1,ReplacedNet2"
    )
    assert (
        result["new_entries"][mock_config_entry.entry_id] == "ReplacedNet1,ReplacedNet2"
    )
    assert result["old_entries"][mock_config_entry.entry_id] == "MyNetwork1,MyNetwork2"


@pytest.mark.asyncio
async def test_set_known_ssids_service_with_entry_id(
    hass: HomeAssistant, mock_config_entry
):
    """Test the set_ssids service with a specific config_entry_id."""
    from custom_components.wifi_ssid_monitor.const import CONF_KNOWN_SSIDS, DOMAIN

    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    result = await hass.services.async_call(
        DOMAIN,
        "set_ssids",
        {
            "values": "ReplacedNet",
            "config_entry_id": mock_config_entry.entry_id,
        },
        blocking=True,
        return_response=True,
    )

    assert mock_config_entry.options.get(CONF_KNOWN_SSIDS) == "ReplacedNet"
    assert result["new_entries"][mock_config_entry.entry_id] == "ReplacedNet"
    assert result["old_entries"][mock_config_entry.entry_id] == "MyNetwork1,MyNetwork2"


@pytest.mark.asyncio
async def test_set_known_ssids_service_invalid_entry_id(
    hass: HomeAssistant, mock_config_entry
):
    """Test set_ssids service raises HomeAssistantError with bogus entry_id."""
    from homeassistant.exceptions import HomeAssistantError

    from custom_components.wifi_ssid_monitor.const import DOMAIN

    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    with pytest.raises(HomeAssistantError, match=r"No .* entry found with ID"):
        await hass.services.async_call(
            DOMAIN,
            "set_ssids",
            {"values": "Test", "config_entry_id": "nonexistent_id"},
            blocking=True,
        )
