"""Tests for WiFi SSID Monitor coordinator."""

from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util

from custom_components.wifi_ssid_monitor.api import WifiScanError
from custom_components.wifi_ssid_monitor.const import (
    CONF_INCLUDE_HIDDEN,
    CONF_LAST_SEEN_TTL_DAYS,
    CONF_SHOW_5GHZ,
    CONF_SHOW_24GHZ,
    EVENT_NEW_NETWORK,
)
from custom_components.wifi_ssid_monitor.coordinator import WifiScanCoordinator

# Frequencies for the two bands, so fixtures don't rely on a channel field.
FREQ_24 = 2437  # channel 6
FREQ_5 = 5240  # channel 48


def _coord(hass, entry, api):
    return WifiScanCoordinator(hass, entry, api, "1.7.0")


@pytest.mark.asyncio
async def test_update_success(hass, mock_config_entry, mock_wifi_api):
    """A successful update dedupes SSIDs and computes the unknown set."""
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_wifi_api.get_access_points.return_value = [
        {"mac": "AA:BB:CC:00:00:01", "ssid": "Net1", "signal": 50, "frequency": FREQ_5},
        {"mac": "AA:BB:CC:00:00:02", "ssid": "Net2", "signal": 40, "frequency": FREQ_5},
        {"mac": "AA:BB:CC:00:00:03", "ssid": "Net1", "signal": 90, "frequency": FREQ_5},
        {
            "mac": "AA:BB:CC:00:00:04",
            "ssid": "MyNetwork1",
            "signal": 95,
            "frequency": FREQ_5,
        },
    ]

    data = await coordinator._async_update_data()

    assert data["count"] == 3
    assert data["ssids"] == ["MyNetwork1", "Net1", "Net2"]
    assert data["unknown_ssids"] == ["Net1", "Net2"]
    assert data["unknown_count"] == 2
    assert data["interface"] == "wlan0"
    # Signal is a percentage now; the last-seen Net1 row (90) wins the map.
    assert data["networks"]["Net1"]["signal"] == 90
    assert data["strongest_unknown_signal"] == 90
    assert data["strongest_unknown_ssid"] == "Net1"
    assert set(data["last_seen"]) == {"MyNetwork1", "Net1", "Net2"}
    assert coordinator._failure_count == 0
    assert coordinator.last_update_success_time is not None


@pytest.mark.asyncio
async def test_dbm_signal_converted(hass, mock_config_entry, mock_wifi_api):
    """A negative (dBm) signal is converted to a percentage."""
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_wifi_api.get_access_points.return_value = [
        {
            "mac": "AA:BB:CC:00:00:09",
            "ssid": "DbmNet",
            "signal": -60,
            "frequency": FREQ_5,
        },
    ]
    data = await coordinator._async_update_data()
    # dbm_to_pct(-60) == 80
    assert data["networks"]["DbmNet"]["signal"] == 80


@pytest.mark.asyncio
async def test_known_parsing_with_spaces(hass, mock_config_entry, mock_wifi_api):
    """Known-list parsing tolerates spaces and empty entries."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry, options={"known_wifi_ids": " Net1 , Net2, ,Net3"}
    )
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_wifi_api.get_access_points.return_value = [
        {"mac": f"AA:BB:CC:00:00:0{i}", "ssid": s, "signal": 60, "frequency": FREQ_5}
        for i, s in enumerate(["Net1", "Net2", "Net3", "Net4"], start=1)
    ]
    data = await coordinator._async_update_data()
    assert data["count"] == 4
    assert data["unknown_ssids"] == ["Net4"]


@pytest.mark.asyncio
async def test_wildcard_known(hass, mock_config_entry, mock_wifi_api):
    """Wildcard patterns match case-sensitively."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, "known_wifi_ids": "Guest_*,IoT_?"},
    )
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_wifi_api.get_access_points.return_value = [
        {
            "mac": "AA:BB:CC:00:00:01",
            "ssid": "Guest_Home",
            "signal": 60,
            "frequency": FREQ_5,
        },
        {
            "mac": "AA:BB:CC:00:00:02",
            "ssid": "IoT_1",
            "signal": 60,
            "frequency": FREQ_5,
        },
        {
            "mac": "AA:BB:CC:00:00:03",
            "ssid": "guest_home",
            "signal": 60,
            "frequency": FREQ_5,
        },
        {
            "mac": "AA:BB:CC:00:00:04",
            "ssid": "Rogue",
            "signal": 60,
            "frequency": FREQ_5,
        },
    ]
    data = await coordinator._async_update_data()
    assert data["unknown_ssids"] == ["Rogue", "guest_home"]
    assert data["unknown_count"] == 2


@pytest.mark.asyncio
async def test_denylist_overrides_known(hass, mock_config_entry, mock_wifi_api):
    """A denylisted network is unknown even if it matches the known list."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={
            **mock_config_entry.options,
            "known_wifi_ids": "Home*",
            "denylist_ssids": "HomeGuest",
        },
    )
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_wifi_api.get_access_points.return_value = [
        {
            "mac": "AA:BB:CC:00:00:01",
            "ssid": "HomeMain",
            "signal": 60,
            "frequency": FREQ_5,
        },
        {
            "mac": "AA:BB:CC:00:00:02",
            "ssid": "HomeGuest",
            "signal": 60,
            "frequency": FREQ_5,
        },
    ]
    data = await coordinator._async_update_data()
    assert data["unknown_ssids"] == ["HomeGuest"]


@pytest.mark.asyncio
async def test_hidden_named_by_bssid(hass, mock_config_entry, mock_wifi_api):
    """Hidden networks with a BSSID are individually named, not collapsed."""
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_wifi_api.get_access_points.return_value = [
        {"mac": "AA:BB:CC:00:11:22", "ssid": "", "signal": 60, "frequency": FREQ_24},
        {"mac": "AA:BB:CC:00:33:44", "ssid": "", "signal": 60, "frequency": FREQ_24},
    ]
    data = await coordinator._async_update_data()
    assert data["count"] == 2
    assert "Hidden-1122" in data["ssids"]
    assert "Hidden-3344" in data["ssids"]


@pytest.mark.asyncio
async def test_include_hidden_false(hass, mock_config_entry, mock_wifi_api):
    """Hidden networks are excluded when the option is off."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, CONF_INCLUDE_HIDDEN: False},
    )
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_wifi_api.get_access_points.return_value = [
        {
            "mac": "AA:BB:CC:00:00:01",
            "ssid": "VisibleA",
            "signal": 60,
            "frequency": FREQ_5,
        },
        {"mac": "AA:BB:CC:00:11:22", "ssid": "", "signal": 60, "frequency": FREQ_24},
    ]
    data = await coordinator._async_update_data()
    assert data["count"] == 1
    assert data["ssids"] == ["VisibleA"]


@pytest.mark.asyncio
async def test_band_filter_hides_5ghz(hass, mock_config_entry, mock_wifi_api):
    """With 5 GHz switched off, 5 GHz networks are excluded."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, CONF_SHOW_5GHZ: False},
    )
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_wifi_api.get_access_points.return_value = [
        {
            "mac": "AA:BB:CC:00:00:01",
            "ssid": "Net2G",
            "signal": 60,
            "frequency": FREQ_24,
        },
        {
            "mac": "AA:BB:CC:00:00:02",
            "ssid": "Net5G",
            "signal": 60,
            "frequency": FREQ_5,
        },
    ]
    data = await coordinator._async_update_data()
    assert data["ssids"] == ["Net2G"]


@pytest.mark.asyncio
async def test_band_filter_unknown_band_passes(hass, mock_config_entry, mock_wifi_api):
    """An unresolved band is never dropped by a band filter."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, CONF_SHOW_24GHZ: False},
    )
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_wifi_api.get_access_points.return_value = [
        {
            "mac": "AA:BB:CC:00:00:01",
            "ssid": "Net2G",
            "signal": 60,
            "frequency": FREQ_24,
        },
        # No frequency at all -> band None -> must still pass.
        {"mac": "AA:BB:CC:00:00:02", "ssid": "NetUnknown", "signal": 60},
    ]
    data = await coordinator._async_update_data()
    # 2.4 hidden, unknown-band kept.
    assert data["ssids"] == ["NetUnknown"]


@pytest.mark.asyncio
async def test_timeout_cold_start_raises(hass, mock_config_entry, mock_wifi_api):
    """A timeout with no prior data raises ConfigEntryNotReady."""
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_wifi_api.get_access_points.side_effect = TimeoutError
    with pytest.raises(ConfigEntryNotReady):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_cold_start_flags_health_immediately(
    hass, mock_config_entry, mock_wifi_api
):
    """The very first failure flags the health snapshot (no held values)."""
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_wifi_api.get_access_points.side_effect = WifiScanError("down")
    with pytest.raises(ConfigEntryNotReady):
        await coordinator._async_update_data()
    assert coordinator.health_snapshot["problem"] is True


@pytest.mark.asyncio
async def test_resilience_holds_then_fails(hass, mock_config_entry, mock_wifi_api):
    """Last-known values are held for 3 failures, then UpdateFailed."""
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    initial = {"count": 1, "ssids": ["Net1"], "unknown_ssids": [], "networks": {}}
    coordinator.data = initial
    mock_wifi_api.get_access_points.side_effect = WifiScanError("down")

    for expected in range(1, 4):
        result = await coordinator._async_update_data()
        assert result == initial
        assert coordinator._failure_count == expected

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_resilience_resets_on_success(hass, mock_config_entry, mock_wifi_api):
    """A successful fetch resets the failure counter."""
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    coordinator.data = {"count": 0, "ssids": [], "unknown_ssids": [], "networks": {}}
    mock_wifi_api.get_access_points.side_effect = WifiScanError("fail")
    await coordinator._async_update_data()
    await coordinator._async_update_data()
    assert coordinator._failure_count == 2

    mock_wifi_api.get_access_points.side_effect = None
    mock_wifi_api.get_access_points.return_value = [
        {"mac": "AA:BB:CC:00:00:01", "ssid": "Net1", "signal": 60, "frequency": FREQ_5}
    ]
    await coordinator._async_update_data()
    assert coordinator._failure_count == 0


@pytest.mark.asyncio
async def test_pause_returns_cached(hass, mock_config_entry, mock_wifi_api):
    """While paused, a scheduled poll returns cached data without fetching."""
    from custom_components.wifi_ssid_monitor.const import CONF_STOP_POLLING

    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, CONF_STOP_POLLING: True},
    )
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    cached = {"count": 1, "ssids": ["Held"], "networks": {}}
    coordinator.data = cached

    result = await coordinator._async_update_data()
    assert result is cached
    mock_wifi_api.get_access_points.assert_not_called()


@pytest.mark.asyncio
async def test_force_refresh_bypasses_pause(hass, mock_config_entry, mock_wifi_api):
    """async_force_refresh fetches even while paused."""
    from custom_components.wifi_ssid_monitor.const import CONF_STOP_POLLING

    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, CONF_STOP_POLLING: True},
    )
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    coordinator.data = {"count": 0, "ssids": [], "networks": {}}
    mock_wifi_api.get_access_points.return_value = [
        {"mac": "AA:BB:CC:00:00:01", "ssid": "Fresh", "signal": 60, "frequency": FREQ_5}
    ]

    await coordinator.async_force_refresh()
    await hass.async_block_till_done()
    assert "Fresh" in coordinator.data["ssids"]


@pytest.mark.asyncio
async def test_new_network_event_baseline_then_fires(
    hass, mock_config_entry, mock_wifi_api
):
    """The first scan is a silent baseline; a later new network fires an event."""
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    events = []
    hass.bus.async_listen(EVENT_NEW_NETWORK, lambda e: events.append(e))

    mock_wifi_api.get_access_points.return_value = [
        {"mac": "AA:BB:CC:00:00:01", "ssid": "First", "signal": 60, "frequency": FREQ_5}
    ]
    await coordinator._async_update_data()
    await hass.async_block_till_done()
    assert events == []  # baseline is silent

    mock_wifi_api.get_access_points.return_value = [
        {
            "mac": "AA:BB:CC:00:00:01",
            "ssid": "First",
            "signal": 60,
            "frequency": FREQ_5,
        },
        {
            "mac": "AA:BB:CC:00:00:02",
            "ssid": "Second",
            "signal": 60,
            "frequency": FREQ_5,
        },
    ]
    await coordinator._async_update_data()
    await hass.async_block_till_done()
    assert len(events) == 1
    assert events[0].data["ssid"] == "Second"


@pytest.mark.asyncio
async def test_initialize_loads_all_stores(hass, mock_config_entry, mock_wifi_api):
    """async_initialize loads all three history stores."""
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    now = dt_util.now()
    await coordinator.store.async_save({"NetA": now.isoformat()})
    await coordinator.store_first_seen.async_save({"NetB": now.isoformat()})
    await coordinator.store_visit_counts.async_save({"NetC": 5})

    await coordinator.async_initialize()

    assert coordinator._last_seen == {"NetA": now}
    assert coordinator._first_seen == {"NetB": now}
    assert coordinator._visit_counts == {"NetC": 5}


@pytest.mark.asyncio
async def test_initialize_handles_store_error(hass, mock_config_entry, mock_wifi_api):
    """A store load exception degrades to empty history."""
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    coordinator.store.async_load = AsyncMock(side_effect=Exception("boom"))
    coordinator.store_first_seen.async_load = AsyncMock(return_value=None)
    coordinator.store_visit_counts.async_load = AsyncMock(return_value=None)
    await coordinator.async_initialize()
    assert coordinator._last_seen == {}


@pytest.mark.asyncio
async def test_clear_history(hass, mock_config_entry, mock_wifi_api):
    """async_clear_history empties every history map."""
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    coordinator._last_seen = {"Net1": dt_util.now()}
    coordinator._first_seen = {"Net1": dt_util.now()}
    coordinator._visit_counts = {"Net1": 3}
    await coordinator.async_clear_history()
    assert coordinator._last_seen == {}
    assert coordinator._first_seen == {}
    assert coordinator._visit_counts == {}


@pytest.mark.asyncio
async def test_ttl_expiry(hass, mock_config_entry, mock_wifi_api):
    """TTL expiry prunes a network absent from the scan across all maps."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, CONF_LAST_SEEN_TTL_DAYS: 30},
    )
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    old = dt_util.now() - timedelta(days=100)
    coordinator._last_seen = {"OldNet": old, "NewNet": old}
    coordinator._first_seen = {"OldNet": old, "NewNet": old}
    coordinator._visit_counts = {"OldNet": 1, "NewNet": 5}

    mock_wifi_api.get_access_points.return_value = [
        {
            "mac": "AA:BB:CC:00:00:01",
            "ssid": "NewNet",
            "signal": 60,
            "frequency": FREQ_5,
        }
    ]
    await coordinator._async_update_data()

    assert "OldNet" not in coordinator._last_seen
    assert "OldNet" not in coordinator._first_seen
    assert "OldNet" not in coordinator._visit_counts
    assert coordinator._visit_counts["NewNet"] == 6


@pytest.mark.asyncio
async def test_flush_stores(hass, mock_config_entry, mock_wifi_api):
    """Flushing writes the current history immediately."""
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    now = dt_util.now()
    coordinator._last_seen = {"Net1": now}
    await coordinator.async_flush_stores()
    loaded = await coordinator.store.async_load()
    assert loaded == {"Net1": now.isoformat()}


@pytest.mark.asyncio
async def test_config_entry_associated(hass, mock_config_entry, mock_wifi_api):
    """The coordinator passes config_entry to the base class."""
    mock_config_entry.add_to_hass(hass)
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    assert coordinator.config_entry is mock_config_entry


@pytest.mark.asyncio
async def test_initialize_handles_all_store_errors_and_corrupt_timestamps(
    hass, mock_config_entry, mock_wifi_api
):
    """Store load errors on first_seen and visit_counts degrade gracefully."""
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    coordinator.store.async_load = AsyncMock(
        return_value={"Good": "2026-01-01T12:00:00+00:00", "Bad": "corrupt-iso"}
    )
    coordinator.store_first_seen.async_load = AsyncMock(
        side_effect=Exception("first_seen store failure")
    )
    coordinator.store_visit_counts.async_load = AsyncMock(
        side_effect=Exception("visit_counts store failure")
    )
    await coordinator.async_initialize()
    assert "Good" in coordinator._last_seen
    assert "Bad" not in coordinator._last_seen
    assert coordinator._first_seen == {}
    assert coordinator._visit_counts == {}


@pytest.mark.asyncio
async def test_prune_history_overflow_and_invalid_band(
    hass, mock_config_entry, mock_wifi_api
):
    """Overflow pruning caps history entries, and invalid band names pass through."""
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    now = dt_util.now()
    # Populate 2005 entries to exceed HISTORY_MAX_ENTRIES (2000)
    for i in range(2005):
        coordinator._last_seen[f"Net_{i:04d}"] = now - timedelta(seconds=i)
    coordinator._prune_history(now, 365)
    assert len(coordinator._last_seen) == 2000
    assert "Net_2004" not in coordinator._last_seen  # Oldest pruned

    # Test _band_allowed with unknown/invalid band option (line 560)
    assert coordinator._band_allowed("UnknownBand", {}) is True


@pytest.mark.asyncio
async def test_health_drift_strikes_repair_lifecycle_and_exception(
    hass, mock_config_entry, mock_wifi_api
):
    """Health drift strike accumulation creates and resolves repair issues."""
    from unittest.mock import patch

    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_config_entry.add_to_hass(hass)

    # 1. First scan with interface missing -> strike 1
    mock_wifi_api.last_interface_present = False
    mock_wifi_api.get_access_points.return_value = []
    await coordinator._async_update_data()
    assert coordinator.health_snapshot["problem"] is False

    # 2. Second scan -> strike 2 (limit is 3)
    await coordinator._async_update_data()
    assert coordinator.health_snapshot["problem"] is False

    # 3. Third scan -> strike 3 -> repair created
    await coordinator._async_update_data()
    assert coordinator.health_snapshot["problem"] is True
    assert "interface_missing" in coordinator._active_repairs

    # 4. Fourth scan with repair already active -> hits continue on line 365
    await coordinator._async_update_data()
    assert "interface_missing" in coordinator._active_repairs

    # 5. Fifth scan with interface restored -> strikes reset -> repair deleted
    mock_wifi_api.last_interface_present = True
    await coordinator._async_update_data()
    assert coordinator.health_snapshot["problem"] is False
    assert "interface_missing" not in coordinator._active_repairs

    # 6. Diagnosis exception handling (line 518-519)
    with patch(
        "custom_components.wifi_ssid_monitor.coordinator.run_checks",
        side_effect=RuntimeError("Diagnosis failure"),
    ):
        data = await coordinator._async_update_data()
        assert data is not None


@pytest.mark.asyncio
async def test_signal_unit_change_and_event_suppression(
    hass, mock_config_entry, mock_wifi_api
):
    """Signal unit changes are logged, and event caps suppress bursts."""
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_config_entry.add_to_hass(hass)

    # Baseline scan to complete event baseline
    mock_wifi_api.get_access_points.return_value = [
        {
            "mac": "AA:BB:CC:00:00:01",
            "ssid": "BaseNet",
            "signal": 80,
            "frequency": FREQ_5,
        }
    ]
    await coordinator._async_update_data()
    assert coordinator._baseline_signal_unit == "percent"

    # Event fire after baseline with no new keys (line 597)
    coordinator._fire_new_network_events(set(), {})

    # Signal unit change notification (lines 526-531)
    coordinator._baseline_signal_unit = "dBm"
    mock_wifi_api.get_access_points.return_value = [
        {
            "mac": "AA:BB:CC:00:00:01",
            "ssid": "BaseNet",
            "signal": 80,
            "frequency": FREQ_5,
        }
    ]
    await coordinator._async_update_data()
    assert coordinator._baseline_signal_unit == "percent"

    # Create 15 new networks to exceed NEW_NETWORK_EVENT_MAX_PER_CYCLE (10)
    burst_aps = [
        {
            "mac": f"AA:BB:CC:00:{i:02x}:01",
            "ssid": f"BurstNet_{i:02d}",
            "signal": 70,
            "frequency": FREQ_5,
        }
        for i in range(15)
    ]
    mock_wifi_api.get_access_points.return_value = burst_aps

    events_fired = []
    hass.bus.async_listen(EVENT_NEW_NETWORK, lambda evt: events_fired.append(evt))

    await coordinator._async_update_data()
    assert len(events_fired) == 10  # Capped at 10


@pytest.mark.asyncio
async def test_event_fire_missing_key_in_network_map(
    hass, mock_config_entry, mock_wifi_api
):
    """Event fire loop handles missing key and listener exceptions gracefully."""
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_config_entry.add_to_hass(hass)
    coordinator._event_baseline_done = True

    from homeassistant.core import callback

    @callback
    def bad_listener(event):
        raise RuntimeError("Event listener failure")

    hass.bus.async_listen("wifi_ssid_monitor_new_network", bad_listener)
    network_map = {
        "NetA": {
            "key": "NetA",
            "ssid": "NetA",
            "bssid": "AA:11",
            "band": "5 GHz",
            "channel": 36,
            "signal": 80,
            "hidden": False,
            "ssid_anomaly": False,
        }
    }
    coordinator._fire_new_network_events({"NetA", "NonExistentKey"}, network_map)


@pytest.mark.asyncio
async def test_fetch_failure_interface_missing_repair(
    hass, mock_config_entry, mock_wifi_api
):
    """Fetch failure with interface missing creates interface_missing repair issue."""
    from unittest.mock import patch

    from homeassistant.exceptions import ConfigEntryNotReady

    from custom_components.wifi_ssid_monitor.api import WifiScanError

    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_config_entry.add_to_hass(hass)

    mock_wifi_api.last_interface_present = False
    mock_wifi_api.get_access_points.side_effect = WifiScanError(
        "API returned status 400"
    )

    # Test run_checks exception handling in fetch failure (lines 312-313)
    with (
        patch(
            "custom_components.wifi_ssid_monitor.coordinator.run_checks",
            side_effect=RuntimeError("Diagnosis failure"),
        ),
        pytest.raises(ConfigEntryNotReady),
    ):
        await coordinator._async_update_data()

    # Call _async_update_data 3 more times to exceed fetch strike budget (3)
    for _ in range(3):
        with pytest.raises(ConfigEntryNotReady):
            await coordinator._async_update_data()

    assert coordinator.health_snapshot["problem"] is True
    assert "interface_missing" in coordinator._active_repairs
