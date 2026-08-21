"""Tests for WiFi SSID Monitor coordinator."""

from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util

from custom_components.wifi_ssid_monitor import coordinator as coordinator_module
from custom_components.wifi_ssid_monitor.api import WifiScanError
from custom_components.wifi_ssid_monitor.const import (
    CANARY_MIN_VISITS,
    CONF_DENYLIST_SSIDS,
    CONF_INCLUDE_HIDDEN,
    CONF_KNOWN_SSIDS,
    CONF_LAST_SEEN_TTL_DAYS,
    CONF_SHOW_5GHZ,
    CONF_SHOW_24GHZ,
    EVENT_NEW_NETWORK,
    FETCH_STRIKE_LIMIT,
    HEALTH_STARTUP_GRACE_SCANS,
    HISTORY_MAX_ENTRIES,
    ISSUE_SUPERVISOR_UNAVAILABLE,
    NEW_NETWORK_EVENT_MAX_PER_CYCLE,
)
from custom_components.wifi_ssid_monitor.coordinator import WifiScanCoordinator
from custom_components.wifi_ssid_monitor.health import (
    SEVERITY_ERROR,
    SEVERITY_OK,
    SEVERITY_UNKNOWN,
    Finding,
)

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
    with patch.object(coordinator_module.ir, "async_delete_issue") as mock_delete:
        await coordinator._async_update_data()

    # Covers finding ASSERT.1 from recommendations_20260806.md. Recovery does
    # three things on the same three lines (coordinator.py:461-464) and only
    # the counter was asserted: a stale repair left on the user's Repairs
    # panel, or an unset timestamp feeding `last_good_update`, both passed.
    assert coordinator._failure_count == 0
    assert coordinator.last_update_success_time is not None
    assert any(
        call.args[-1] == coordinator._issue_id(ISSUE_SUPERVISOR_UNAVAILABLE)
        for call in mock_delete.call_args_list
    ), "recovery must clear the outage repair issue, on its entry-scoped id"


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

    # async_request_refresh arms a trailing debounce timer; shutting the
    # coordinator down cancels it, which the harness requires.
    await coordinator.async_shutdown()


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
async def test_prune_history_ttl_zero_keeps_everything(
    hass, mock_config_entry, mock_wifi_api
):
    """A TTL of zero means keep forever, not expire immediately.

    Zero is a sentinel, not a duration. Dropping the guard would compute a
    cutoff of "now" and delete every history entry on the next prune — silently,
    because the integration would carry on scanning and simply forget that it
    had ever seen anything before.
    """
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    now = dt_util.now()
    ancient = now - timedelta(days=3650)

    coordinator._last_seen["Ancient"] = ancient
    coordinator._first_seen["Ancient"] = ancient
    coordinator._visit_counts["Ancient"] = 5

    coordinator._prune_history(now, 0)

    assert coordinator._last_seen["Ancient"] == ancient
    assert coordinator._first_seen["Ancient"] == ancient
    assert coordinator._visit_counts["Ancient"] == 5


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
    """A key absent from the map is skipped, and the rest still fire.

    Two failures are possible here and only one of them is a crash. A raising
    listener must not stop the loop, and a key with no matching network must be
    passed over rather than firing an event with missing fields — so this
    asserts which events actually reached the bus, not merely that nothing
    was raised.
    """
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_config_entry.add_to_hass(hass)
    coordinator._event_baseline_done = True

    from homeassistant.core import callback

    @callback
    def bad_listener(event):
        raise RuntimeError("Event listener failure")

    received: list[dict] = []

    @callback
    def recording_listener(event):
        received.append(event.data)

    # The raising listener is registered first: if it aborted delivery, the
    # recorder behind it would see nothing.
    hass.bus.async_listen("wifi_ssid_monitor_new_network", bad_listener)
    hass.bus.async_listen("wifi_ssid_monitor_new_network", recording_listener)
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
    await hass.async_block_till_done()

    # Exactly one event: "NonExistentKey" has no network to describe.
    assert [event["key"] for event in received] == ["NetA"]
    assert received[0]["ssid"] == "NetA"
    assert received[0]["bssid"] == "AA:11"
    assert received[0]["entry_id"] == mock_config_entry.entry_id


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


@pytest.mark.asyncio
async def test_drift_finding_lands_in_drift_not_degraded_capabilities(
    hass, mock_config_entry, mock_wifi_api
):
    """A payload-shape finding is published under `drift`, and only there.

    Section 19 publishes the two separately because an automation reacting to
    a failed capability should not fire on the payload changing shape under a
    successful fetch. This asserts the split at the published-attribute level:
    the unit tests classify the Finding, this proves the classification
    actually reaches the attribute a user's template reads.
    """
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_config_entry.add_to_hass(hass)

    # APs with no frequency resolve to no band — the signature of the payload
    # change this integration was built after.
    mock_wifi_api.get_access_points.return_value = [
        {"mac": "AA:BB:CC:00:00:01", "ssid": "Net1", "signal": 50},
        {"mac": "AA:BB:CC:00:00:02", "ssid": "Net2", "signal": 40},
    ]

    # Startup grace (2 scans) then the drift strike budget (3).
    for _ in range(5):
        await coordinator._async_update_data()

    snapshot = coordinator.health_snapshot
    assert snapshot["problem"] is True
    assert snapshot["drift"], "a payload-shape finding must reach `drift`"
    assert "band_unresolved_all" not in snapshot["degraded_capabilities"], (
        "a drift finding must not also appear under degraded_capabilities"
    )
    assert snapshot["degraded_capabilities"] == []


@pytest.mark.asyncio
async def test_capability_finding_lands_in_degraded_capabilities_not_drift(
    hass, mock_config_entry, mock_wifi_api
):
    """A failed capability is published under `degraded_capabilities`, only.

    The mirror of the test above. Together they fail if the `is_drift` tag on
    either class of check is flipped — which nothing else in the suite does.
    """
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_config_entry.add_to_hass(hass)

    mock_wifi_api.last_interface_present = False
    mock_wifi_api.get_access_points.return_value = []

    for _ in range(3):
        await coordinator._async_update_data()

    snapshot = coordinator.health_snapshot
    assert snapshot["problem"] is True
    assert "interface_missing" in snapshot["degraded_capabilities"]
    assert snapshot["drift"] == [], (
        "a capability finding must not appear under drift — that would raise a "
        "payload-changed alarm for a missing adapter"
    )


# ===========================================================================
# testing_deeper_lev1_review — recommendations_20260806.md
# ===========================================================================


@pytest.mark.asyncio
async def test_established_known_keys_threshold_and_pattern(
    hass, mock_config_entry, mock_wifi_api
):
    """Both terms of the canary's membership test are pinned.

    Covers finding BVA.1 from recommendations_20260806.md.

    This set is the input to `check_known_network_canary` — it decides whether
    the "all your known networks vanished at once" alarm can fire at all. A
    wrong threshold or a broken pattern match empties it, and the check then
    returns None on its first line for every scan, with nothing failing.

    `Neighbour` is the case that pins the second term: a version ignoring
    `known_patterns` would return all four keys.
    """
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    coordinator._visit_counts = {
        "HomeNet": CANARY_MIN_VISITS - 1,
        "OfficeNet": CANARY_MIN_VISITS,
        "LabNet": CANARY_MIN_VISITS + 1,
        "Neighbour": 99,
    }

    result = coordinator.established_known_keys(["Home*", "Office*", "Lab*"])

    assert result == {"OfficeNet", "LabNet"}


@pytest.mark.asyncio
async def test_ttl_expiry_is_exact_at_the_cutoff(
    hass, mock_config_entry, mock_wifi_api
):
    """The TTL boundary is inclusive, asserted one second either side.

    Covers finding BVA.2 from recommendations_20260806.md.

    The existing TTL test uses a timestamp 100 days past a 30-day TTL, which
    cannot distinguish `<=` from `<`. All three history maps are checked
    because `_drop_keys` removes from all three together.
    """
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    now = dt_util.now()
    cutoff = now - timedelta(days=30)

    stamps = {
        "Older": cutoff - timedelta(seconds=1),
        "Exactly": cutoff,
        "Newer": cutoff + timedelta(seconds=1),
    }
    coordinator._last_seen = dict(stamps)
    coordinator._first_seen = dict(stamps)
    coordinator._visit_counts = dict.fromkeys(stamps, 1)

    coordinator._prune_history(now, 30)

    assert set(coordinator._last_seen) == {"Newer"}
    assert set(coordinator._first_seen) == {"Newer"}
    assert set(coordinator._visit_counts) == {"Newer"}


@pytest.mark.asyncio
async def test_startup_grace_filters_drift_findings_independently(
    hass, mock_config_entry, mock_wifi_api
):
    """The grace window is asserted apart from the strike budget.

    Covers finding BVA.3 from recommendations_20260806.md.

    The existing coverage loops five scans with a comment naming "2 grace + 3
    strikes", so the two thresholds are only ever tested multiplied together
    and either could move while the other absorbs it. This asserts on
    `_drift_strikes` rather than on `problem`, because `problem` stays False
    through both windows and would pass either way.
    """
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_config_entry.add_to_hass(hass)

    # No frequency -> no band resolves -> a drift finding, not a capability one.
    mock_wifi_api.get_access_points.return_value = [
        {"mac": "AA:BB:CC:00:00:01", "ssid": "Net1", "signal": 50},
        {"mac": "AA:BB:CC:00:00:02", "ssid": "Net2", "signal": 40},
    ]

    # The constant means what it says: this many scans are inside the window.
    for scan in range(1, HEALTH_STARTUP_GRACE_SCANS + 1):
        await coordinator._async_update_data()
        assert "band_unresolved_all" not in coordinator._drift_strikes, (
            f"scan {scan} is inside the grace window; the finding must be "
            "filtered out, not merely left unconfirmed"
        )

    await coordinator._async_update_data()
    assert coordinator._drift_strikes.get("band_unresolved_all") == 1


@pytest.mark.asyncio
async def test_history_cap_prunes_only_above_the_limit(
    hass, mock_config_entry, mock_wifi_api
):
    """At exactly the cap nothing is dropped; one over drops exactly one.

    Covers finding BVA.4 from recommendations_20260806.md.

    `overflow > 0` versus `>= 0` is invisible when only the over-cap case is
    tested — the latter would sort the whole history and slice nothing on
    every single poll.
    """
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    now = dt_util.now()
    coordinator._last_seen = {
        f"Net_{i:05d}": now - timedelta(seconds=i) for i in range(HISTORY_MAX_ENTRIES)
    }
    oldest = f"Net_{HISTORY_MAX_ENTRIES - 1:05d}"

    coordinator._prune_history(now, 0)

    assert len(coordinator._last_seen) == HISTORY_MAX_ENTRIES
    assert oldest in coordinator._last_seen

    coordinator._last_seen["Net_extra"] = now - timedelta(seconds=HISTORY_MAX_ENTRIES)
    coordinator._prune_history(now, 0)

    assert len(coordinator._last_seen) == HISTORY_MAX_ENTRIES
    assert "Net_extra" not in coordinator._last_seen


@pytest.mark.asyncio
async def test_new_24h_window_is_inclusive_at_the_edge(
    hass, mock_config_entry, mock_wifi_api
):
    """A network first seen exactly 24 hours ago still counts.

    Covers finding BVA.5 from recommendations_20260806.md.
    """
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    now = dt_util.now()
    cutoff = now - timedelta(hours=24)
    coordinator._first_seen = {
        "Older": cutoff - timedelta(seconds=1),
        "Exactly": cutoff,
        "Newer": cutoff + timedelta(seconds=1),
    }

    assert coordinator._count_new_within(now, hours=24) == 2


@pytest.mark.asyncio
async def test_event_cap_at_exactly_the_limit_suppresses_nothing(
    hass, mock_config_entry, mock_wifi_api
):
    """Exactly the cap fires every event and logs no suppression.

    Covers finding BVA.6 from recommendations_20260806.md.

    Tested only above the cap, the suppression notice firing when nothing was
    suppressed would go unseen — `suppressed` is 0 here and the log line must
    not appear.
    """
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_config_entry.add_to_hass(hass)
    coordinator._event_baseline_done = True

    mock_wifi_api.get_access_points.return_value = [
        {
            "mac": f"AA:BB:CC:00:{i:02x}:01",
            "ssid": f"CapNet_{i:02d}",
            "signal": 70,
            "frequency": FREQ_5,
        }
        for i in range(NEW_NETWORK_EVENT_MAX_PER_CYCLE)
    ]

    fired = []
    hass.bus.async_listen(EVENT_NEW_NETWORK, lambda evt: fired.append(evt))

    with patch.object(coordinator_module._LOGGER, "info") as mock_info:
        await coordinator._async_update_data()
        await hass.async_block_till_done()

    assert len(fired) == NEW_NETWORK_EVENT_MAX_PER_CYCLE
    assert not any("suppressed" in str(call) for call in mock_info.call_args_list), (
        "nothing was suppressed, so the suppression notice must not be logged"
    )


@pytest.mark.asyncio
async def test_a_network_known_only_by_its_bssid_is_classified_known(
    hass, mock_config_entry, mock_wifi_api
):
    """A MAC in the known list matches, as the docstring promises.

    Covers finding COMBO.1 from recommendations_20260806.md.

    `_is_unknown` matches each pattern against the network key AND the BSSID.
    Nothing in the suite passed a MAC in either list, so the whole second half
    of both conditions was unexercised — a documented, user-facing capability
    with no test.
    """
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, CONF_KNOWN_SSIDS: "AA:BB:CC:00:00:01"},
    )
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_wifi_api.get_access_points.return_value = [
        {
            "mac": "AA:BB:CC:00:00:01",
            "ssid": "ByMac",
            "signal": 60,
            "frequency": FREQ_5,
        },
        {
            "mac": "AA:BB:CC:00:00:02",
            "ssid": "Other",
            "signal": 50,
            "frequency": FREQ_5,
        },
    ]

    data = await coordinator._async_update_data()

    assert "ByMac" not in data["unknown_ssids"]
    assert "Other" in data["unknown_ssids"]


@pytest.mark.asyncio
async def test_a_bssid_wildcard_matches_every_radio_of_one_vendor(
    hass, mock_config_entry, mock_wifi_api
):
    """A MAC prefix wildcard matches, which is the point of allowing patterns.

    Covers finding COMBO.1 from recommendations_20260806.md.
    """
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, CONF_KNOWN_SSIDS: "AA:BB:CC:*"},
    )
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_wifi_api.get_access_points.return_value = [
        {
            "mac": "AA:BB:CC:00:00:01",
            "ssid": "Mine1",
            "signal": 60,
            "frequency": FREQ_5,
        },
        {
            "mac": "AA:BB:CC:00:00:02",
            "ssid": "Mine2",
            "signal": 50,
            "frequency": FREQ_5,
        },
        {
            "mac": "FF:EE:DD:00:00:03",
            "ssid": "Theirs",
            "signal": 40,
            "frequency": FREQ_5,
        },
    ]

    data = await coordinator._async_update_data()

    assert data["unknown_ssids"] == ["Theirs"]


@pytest.mark.asyncio
async def test_a_network_with_no_bssid_does_not_break_pattern_matching(
    hass, mock_config_entry, mock_wifi_api
):
    """The `bssid and ...` short-circuit is exercised, not just present.

    Covers finding COMBO.1 from recommendations_20260806.md.

    A hidden network whose `mac` is absent reaches `_is_unknown` with
    `bssid=None`. Without the guard, `fnmatch(None, pattern)` raises and takes
    the whole scan down. This asserts the scan completes and classifies.
    """
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, CONF_KNOWN_SSIDS: "AA:BB:CC:*"},
    )
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_wifi_api.get_access_points.return_value = [
        {"ssid": "NoMacNet", "signal": 60, "frequency": FREQ_5},
    ]

    data = await coordinator._async_update_data()

    assert data["count"] == 1
    assert data["unknown_ssids"] == data["ssids"]


@pytest.mark.asyncio
async def test_the_denylist_beats_the_known_list(
    hass, mock_config_entry, mock_wifi_api
):
    """A network on both lists is unknown — the denylist wins.

    Covers finding COMBO.2 from recommendations_20260806.md.

    `_is_unknown` loops the denylist first and returns True on a match. The
    rule is stated in its docstring and nothing enforced it: reordering the
    two loops passed the entire suite.
    """
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={
            **mock_config_entry.options,
            CONF_KNOWN_SSIDS: "Guest*",
            CONF_DENYLIST_SSIDS: "GuestNet",
        },
    )
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_wifi_api.get_access_points.return_value = [
        {
            "mac": "AA:BB:CC:00:00:01",
            "ssid": "GuestNet",
            "signal": 60,
            "frequency": FREQ_5,
        },
        {
            "mac": "AA:BB:CC:00:00:02",
            "ssid": "GuestWifi",
            "signal": 50,
            "frequency": FREQ_5,
        },
    ]

    data = await coordinator._async_update_data()

    assert "GuestNet" in data["unknown_ssids"], "on both lists — denylist wins"
    assert "GuestWifi" not in data["unknown_ssids"], "known only — stays known"


@pytest.mark.asyncio
async def test_supervisor_unreachable_is_published_on_the_runtime_path(
    hass, mock_config_entry, mock_wifi_api
):
    """A warm integration that runs out of strikes publishes the outage.

    Covers finding COMBO.3 from recommendations_20260806.md.

    Two of the four permutations of `not cold_start and _failure_count <=
    FETCH_STRIKE_LIMIT` were covered. This is the fourth: warm start, count
    above the limit — the path where a running integration finally gives up.
    `supervisor_unreachable` appeared in the suite only as a hardcoded fixture
    value, never produced by the code under test.
    """
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_config_entry.add_to_hass(hass)
    coordinator.data = {"count": 0, "ssids": [], "unknown_ssids": [], "networks": {}}
    mock_wifi_api.get_access_points.side_effect = WifiScanError("supervisor gone")

    for _ in range(FETCH_STRIKE_LIMIT):
        await coordinator._async_update_data()
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()

    snapshot = coordinator.health_snapshot
    assert snapshot["problem"] is True
    assert snapshot["severity"] == SEVERITY_ERROR, "a total outage is `error`"
    assert snapshot["degraded_capabilities"] == ["supervisor_unreachable"]
    assert snapshot["drift"] == [], "no payload arrived, so no drift verdict"
    assert snapshot["cold_start"] is False


@pytest.mark.asyncio
async def test_a_scan_reporting_two_signal_units_resolves_to_none(
    hass, mock_config_entry, mock_wifi_api
):
    """Disagreeing units mean no unit, not an arbitrary pick.

    Covers finding COMBO.4 from recommendations_20260806.md.

    Every other test scan reports one unit throughout, so the `else None`
    branch never ran. It matters twice: the payload must not claim a unit it
    cannot determine, and `check_signal_unit_flip` must not read the
    ambiguity as a format change and raise a false drift alarm.
    """
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_config_entry.add_to_hass(hass)
    mock_wifi_api.get_access_points.return_value = [
        {"mac": "AA:BB:CC:00:00:01", "ssid": "Pct", "signal": 60, "frequency": FREQ_5},
        {"mac": "AA:BB:CC:00:00:02", "ssid": "Dbm", "signal": -60, "frequency": FREQ_5},
    ]

    data = await coordinator._async_update_data()

    assert data["signal_unit"] is None
    assert coordinator._baseline_signal_unit is None
    assert coordinator.health_snapshot["drift"] == []


@pytest.mark.asyncio
async def test_a_non_string_stored_timestamp_is_discarded(
    hass, mock_config_entry, mock_wifi_api
):
    """The `TypeError` half of the stored-timestamp guard.

    Covers finding ERR.1 from recommendations_20260806.md, narrowed.

    `test_initialize_handles_all_store_errors_and_corrupt_timestamps` already
    covers the `ValueError` path with a malformed string, so only the
    `TypeError` half was untested — a stored value that is not a string at
    all, which is what a partially-written or hand-edited `.storage` file
    produces. A test using only a bad string passes with `TypeError` removed
    from the clause, so the two are separate cases.
    """
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    coordinator.store.async_load = AsyncMock(
        return_value={
            "Good": "2026-01-01T12:00:00+00:00",
            "IsANumber": 1735732800,
            "IsNull": None,
            "IsAList": ["2026-01-01T12:00:00+00:00"],
        }
    )
    coordinator.store_first_seen.async_load = AsyncMock(return_value={})
    coordinator.store_visit_counts.async_load = AsyncMock(return_value={})

    await coordinator.async_initialize()

    assert set(coordinator._last_seen) == {"Good"}, (
        "the readable entry must survive alongside the unreadable ones"
    )


@pytest.mark.asyncio
async def test_clear_history_twice_is_a_no_op_the_second_time(
    hass, mock_config_entry, mock_wifi_api
):
    """Calling the clear action twice leaves the same state as once.

    Covers finding IDEM.1 from recommendations_20260806.md.

    This is exposed as a user-facing action, so a double-click or a script
    loop calls it twice in quick succession. It also resets the event
    baseline, which must be left armed once — not compounded.
    """
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    now = dt_util.now()
    coordinator._last_seen = {"Net1": now}
    coordinator._first_seen = {"Net1": now}
    coordinator._visit_counts = {"Net1": 3}
    coordinator._event_baseline_done = True

    await coordinator.async_clear_history()
    await coordinator.async_clear_history()

    assert coordinator._last_seen == {}
    assert coordinator._first_seen == {}
    assert coordinator._visit_counts == {}
    assert coordinator._event_baseline_done is False
    assert await coordinator.store.async_load() == {}


@pytest.mark.asyncio
async def test_clearing_history_does_not_replay_the_backlog(
    hass, mock_config_entry, mock_wifi_api
):
    """A mid-session clear re-arms the baseline instead of firing everything.

    Covers finding IDEM.2 from recommendations_20260806.md.

    `async_clear_history` sets `_event_baseline_done` back to False so the
    next scan records the existing set silently. Only the `__init__` path was
    covered — one test set the flag by hand. This covers the reset, which is
    the path a user actually triggers, and where getting it wrong dumps every
    network in range into their automations at once.
    """
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_config_entry.add_to_hass(hass)

    await coordinator._async_update_data()  # baseline established

    fired = []
    hass.bus.async_listen(EVENT_NEW_NETWORK, lambda evt: fired.append(evt))

    await coordinator.async_clear_history()
    await coordinator._async_update_data()
    await hass.async_block_till_done()

    assert fired == [], "every key is new after a clear, and none may fire"

    mock_wifi_api.get_access_points.return_value = [
        *mock_wifi_api.get_access_points.return_value,
        {
            "mac": "AA:BB:CC:00:00:09",
            "ssid": "Arrived",
            "signal": 40,
            "frequency": FREQ_5,
        },
    ]
    await coordinator._async_update_data()
    await hass.async_block_till_done()

    assert len(fired) == 1, "the baseline must re-arm, not stay disabled"
    assert fired[0].data["ssid"] == "Arrived"


@pytest.mark.asyncio
async def test_held_data_during_an_outage_is_the_complete_payload(
    hass, mock_config_entry, mock_wifi_api
):
    """An outage returns the real payload, every key intact.

    Covers finding RETVAL.1 from recommendations_20260806.md.

    The resilience tests use a four-key stub dict, so nothing verified that a
    consumer reading `signal_unit` or `interface` during an outage still finds
    them. This holds a genuine payload and asserts it comes back whole.
    """
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_config_entry.add_to_hass(hass)

    good = await coordinator._async_update_data()
    coordinator.data = good

    mock_wifi_api.get_access_points.side_effect = WifiScanError("down")
    held = await coordinator._async_update_data()

    assert held == good, "the held payload must be the last good one, unaltered"
    for key in ("interface", "signal_unit", "strongest_unknown_ssid", "new_24h"):
        assert key in held, f"{key} must survive an outage"


@pytest.mark.asyncio
async def test_new_24h_reflects_the_pruned_first_seen_map(
    hass, mock_config_entry, mock_wifi_api
):
    """The count is computed after the prune that rewrites its input.

    Covers finding RETVAL.2 from recommendations_20260806.md.

    `new_24h` reads `_first_seen`, which `_prune_history` rewrites earlier in
    the same scan. The two steps were tested separately and their interaction
    was not — a prune removing a recent entry would lower the count silently.
    """
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, CONF_LAST_SEEN_TTL_DAYS: 30},
    )
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    now = dt_util.now()

    # Recent but long absent: inside the 24h window, outside the TTL.
    coordinator._first_seen = {"Stale": now - timedelta(hours=1)}
    coordinator._last_seen = {"Stale": now - timedelta(days=100)}
    coordinator._visit_counts = {"Stale": 1}

    data = await coordinator._async_update_data()

    assert "Stale" not in coordinator._first_seen, "pruned by TTL"
    assert data["new_24h"] == len(data["ssids"]), (
        "only the networks seen this scan count; the pruned entry must not"
    )


# ===========================================================================
# code_review_20260806_2140.md
# ===========================================================================


@pytest.mark.asyncio
async def test_repair_issue_ids_are_scoped_to_the_config_entry(
    hass, mock_config_entry, mock_wifi_api
):
    """Two entries must not share one repair slot.

    Covers finding M2 from code_review_20260806_2140.md.

    The issue registry keys on (domain, issue_id). With a bare key, every
    config entry shares one slot: a healthy adapter's successful poll deletes
    a failing adapter's repair on every cycle, and the Repairs card flickers
    once per scan interval with no indication which adapter is affected.
    Multiple entries are explicit here — one per interface.
    """
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_config_entry.add_to_hass(hass)

    with patch.object(coordinator_module.ir, "async_create_issue") as mock_create:
        coordinator._sync_repairs(
            [
                Finding(
                    key="interface_missing",
                    severity=SEVERITY_ERROR,
                    message="gone",
                    repair="interface_missing",
                )
            ]
        )

    issue_id = mock_create.call_args.args[2]
    assert mock_config_entry.entry_id in issue_id, (
        "the issue id must carry the entry id, or a sibling entry overwrites it"
    )
    assert mock_create.call_args.kwargs["translation_key"] == "interface_missing", (
        "the translation stays keyed on the issue type, not the scoped id"
    )


@pytest.mark.asyncio
async def test_a_cleared_repair_deletes_the_entry_scoped_id(
    hass, mock_config_entry, mock_wifi_api
):
    """The delete must use the same scoped id the create used.

    Covers finding M2 from code_review_20260806_2140.md.

    `ir.async_delete_issue` looks up by id. A create and a delete that
    disagree leaves the repair raised forever with no UI path to clear it.
    """
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_config_entry.add_to_hass(hass)

    finding = Finding(
        key="interface_missing",
        severity=SEVERITY_ERROR,
        message="gone",
        repair="interface_missing",
    )
    with patch.object(coordinator_module.ir, "async_create_issue") as mock_create:
        coordinator._sync_repairs([finding])
    created_id = mock_create.call_args.args[2]

    with patch.object(coordinator_module.ir, "async_delete_issue") as mock_delete:
        coordinator._sync_repairs([])

    assert mock_delete.call_args.args[2] == created_id


@pytest.mark.asyncio
async def test_the_outage_repair_is_also_entry_scoped(
    hass, mock_config_entry, mock_wifi_api
):
    """The supervisor-unavailable repair is raised and cleared on the same id.

    Covers finding M2 from code_review_20260806_2140.md.

    This is the one that flickers: it is deleted on *every* successful poll,
    so with two entries the healthy one clears the failing one's repair each
    cycle.
    """
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_config_entry.add_to_hass(hass)
    coordinator.data = {"count": 0, "ssids": [], "unknown_ssids": [], "networks": {}}
    mock_wifi_api.get_access_points.side_effect = WifiScanError("down")

    with patch.object(coordinator_module.ir, "async_create_issue") as mock_create:
        for _ in range(FETCH_STRIKE_LIMIT):
            await coordinator._async_update_data()
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()
    raised_id = mock_create.call_args.args[2]
    assert mock_config_entry.entry_id in raised_id

    mock_wifi_api.get_access_points.side_effect = None
    with patch.object(coordinator_module.ir, "async_delete_issue") as mock_delete:
        await coordinator._async_update_data()

    assert any(call.args[2] == raised_id for call in mock_delete.call_args_list), (
        "recovery must clear the same id it raised"
    )


@pytest.mark.asyncio
async def test_a_missing_interface_flags_immediately_on_cold_start(
    hass, mock_config_entry, mock_wifi_api
):
    """A cold start with a bad interface name says so on the first poll.

    Covers finding M1 from code_review_20260806_2140.md.

    `_record_fetch_failure_health` documents that a cold start flags at once —
    "there are no held values, so waiting out the strike budget would leave
    the user with an unexplained, wholly unavailable integration". The
    interface-missing case was routed through `_apply_health`, which applies
    the 3-strike budget anyway, so a fresh install with a renamed adapter left
    every entity unavailable while the health sensor read "no problem" for
    two polls.

    The strike budget still applies at runtime — see the test below.
    """
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_config_entry.add_to_hass(hass)
    mock_wifi_api.last_interface_present = False
    mock_wifi_api.get_access_points.side_effect = WifiScanError("no such interface")

    with pytest.raises(ConfigEntryNotReady):
        await coordinator._async_update_data()

    snapshot = coordinator.health_snapshot
    assert snapshot["problem"] is True, "cold start must not wait out the strikes"
    assert snapshot["severity"] == SEVERITY_ERROR
    assert "interface_missing" in snapshot["degraded_capabilities"]
    assert snapshot["cold_start"] is True


@pytest.mark.asyncio
async def test_a_missing_interface_still_takes_three_strikes_at_runtime(
    hass, mock_config_entry, mock_wifi_api
):
    """A running integration keeps the strike budget for a missing interface.

    Covers finding M1 from code_review_20260806_2140.md — the other half.

    The immediate-flag rule is scoped to cold start on purpose. A 400/404 can
    arrive transiently while the Supervisor itself restarts, and with held
    values the user is not blind, so corroboration is worth the wait.
    """
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_config_entry.add_to_hass(hass)
    coordinator.data = {"count": 0, "ssids": [], "unknown_ssids": [], "networks": {}}
    mock_wifi_api.last_interface_present = False
    mock_wifi_api.get_access_points.side_effect = WifiScanError("transient 404")

    for _ in range(FETCH_STRIKE_LIMIT):
        await coordinator._async_update_data()

    assert coordinator.health_snapshot["problem"] is False, (
        "with held values, a blip must not raise an alarm"
    )


@pytest.mark.asyncio
async def test_two_radios_on_one_ssid_keep_the_strongest_reading(
    hass, mock_config_entry, mock_wifi_api
):
    """A dual-band AP or a mesh publishes its strongest signal, not the last.

    Covers finding M4 from code_review_20260806_2140.md.

    Merging by SSID is deliberate — `history_key` says so: "a dual-band AP is
    one network rather than two". What was not deliberate is that the
    surviving *measurement* was whichever entry came last in the Supervisor's
    list, so the published band, channel and signal flipped between an AP's
    two radios as the ordering shifted, with no change in the environment.

    This is a rogue detector: the question it answers is how strong the
    strongest thing broadcasting that name is. List order is not an answer.
    """
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_config_entry.add_to_hass(hass)
    # The strong radio first, so "last wins" would pick the weak one.
    mock_wifi_api.get_access_points.return_value = [
        {
            "mac": "AA:BB:CC:00:00:01",
            "ssid": "MeshNet",
            "signal": 90,
            "frequency": FREQ_5,
        },
        {
            "mac": "AA:BB:CC:00:00:02",
            "ssid": "MeshNet",
            "signal": 30,
            "frequency": FREQ_24,
        },
    ]

    data = await coordinator._async_update_data()

    net = data["networks"]["MeshNet"]
    assert net["signal"] == 90
    assert net["band"] == "5 GHz", "band must come from the winning radio"
    assert net["bssid"] == "AA:BB:CC:00:00:01"
    assert data["strongest_unknown_signal"] == 90


@pytest.mark.asyncio
async def test_the_order_of_two_radios_does_not_change_the_result(
    hass, mock_config_entry, mock_wifi_api
):
    """The same two radios in either order produce the same published entry.

    Covers finding M4 from code_review_20260806_2140.md.

    This is the property that was broken: output that depends on the
    Supervisor's list ordering rather than on the radios themselves.
    """
    strong = {
        "mac": "AA:BB:CC:00:00:01",
        "ssid": "MeshNet",
        "signal": 90,
        "frequency": FREQ_5,
    }
    weak = {
        "mac": "AA:BB:CC:00:00:02",
        "ssid": "MeshNet",
        "signal": 30,
        "frequency": FREQ_24,
    }

    results = []
    for order in ([strong, weak], [weak, strong]):
        coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
        mock_wifi_api.get_access_points.return_value = order
        data = await coordinator._async_update_data()
        results.append(data["networks"]["MeshNet"])

    assert results[0] == results[1]


@pytest.mark.asyncio
async def test_a_radio_with_no_signal_never_displaces_one_with_a_reading(
    hass, mock_config_entry, mock_wifi_api
):
    """An unreadable signal loses to a real one, whichever arrives first.

    Covers finding M4 from code_review_20260806_2140.md.

    `signal_pct` is None when the Supervisor sends nothing parsable. Treating
    None as "not stronger" is what stops a broken reading from displacing a
    good one — but a network where *every* radio reports None must still
    appear, rather than being dropped for having no comparable value.
    """
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_config_entry.add_to_hass(hass)
    mock_wifi_api.get_access_points.return_value = [
        {
            "mac": "AA:BB:CC:00:00:01",
            "ssid": "HasSignal",
            "signal": 40,
            "frequency": FREQ_5,
        },
        {
            "mac": "AA:BB:CC:00:00:02",
            "ssid": "HasSignal",
            "signal": None,
            "frequency": FREQ_5,
        },
        {
            "mac": "AA:BB:CC:00:00:03",
            "ssid": "NoSignal",
            "signal": None,
            "frequency": FREQ_5,
        },
    ]

    data = await coordinator._async_update_data()

    assert data["networks"]["HasSignal"]["signal"] == 40
    assert "NoSignal" in data["networks"], "a network with no reading still exists"
    assert data["networks"]["NoSignal"]["signal"] is None


@pytest.mark.asyncio
async def test_a_late_poll_cannot_rearm_a_save_after_the_flush(
    hass, mock_config_entry, mock_wifi_api
):
    """Once flushed, a delayed save is refused rather than queued.

    Covers finding L7 from code_review_20260806_2140.md.

    Unload flushes, then unloads platforms. A poll already awaiting the API
    completes afterwards and would otherwise arm a 30-second write on a
    coordinator nothing will flush again — landing after the new coordinator
    has taken over the same storage keys.
    """
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    coordinator._last_seen = {"Net1": dt_util.now()}

    await coordinator.async_flush_stores()

    with patch.object(coordinator.store, "async_delay_save") as mock_delay:
        coordinator._schedule_save()

    mock_delay.assert_not_called()


@pytest.mark.asyncio
async def test_a_failed_flush_is_logged_per_store(
    hass, mock_config_entry, mock_wifi_api
):
    """A write failure on unload names which store failed.

    Covers finding L2 from code_review_20260806_2140.md.

    `return_exceptions=True` with the results discarded made a disk-full or
    permissions error invisible: the history silently resets after a reload
    with nothing in the log to explain it. The load side already logs.
    """
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    coordinator.store.async_save = AsyncMock(side_effect=OSError("disk full"))
    coordinator.store_first_seen.async_save = AsyncMock(return_value=None)
    coordinator.store_visit_counts.async_save = AsyncMock(
        side_effect=PermissionError("read-only")
    )

    with patch.object(coordinator_module._LOGGER, "warning") as mock_warn:
        await coordinator.async_flush_stores()

    logged = " ".join(str(call) for call in mock_warn.call_args_list)
    assert "last_seen" in logged
    assert "visit_counts" in logged
    assert "first_seen" not in logged, "the store that succeeded must not be logged"


@pytest.mark.asyncio
async def test_a_raising_health_pass_does_not_replace_the_fetch_error(
    hass, mock_config_entry, mock_wifi_api
):
    """The Supervisor error survives a failure inside the health computation.

    Covers finding L3 from code_review_20260806_2140.md.

    `_record_fetch_failure_health` runs inside the fetch error handler, and
    `_apply_health` re-runs the checks and touches the issue registry. Raising
    there replaced the error that actually caused the failure, so the log
    showed an unrelated traceback instead of naming the Supervisor.
    """
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    mock_config_entry.add_to_hass(hass)
    coordinator.data = {"count": 0, "ssids": [], "unknown_ssids": [], "networks": {}}
    coordinator._failure_count = FETCH_STRIKE_LIMIT + 1
    mock_wifi_api.last_interface_present = False
    mock_wifi_api.get_access_points.side_effect = WifiScanError("supervisor gone")

    with (
        patch.object(
            coordinator, "_apply_health", side_effect=RuntimeError("registry exploded")
        ),
        pytest.raises(UpdateFailed, match="supervisor gone"),
    ):
        await coordinator._async_update_data()


# ---------------------------------------------------------------------------
# Section 19 severity vocabulary — x_project C-014
# ---------------------------------------------------------------------------
#
# The values are a published contract: users write templates against them, and
# the same five words mean the same things on `huawei_router_5g` and
# `zte_router_5g`. `None` is banned outright, because Home Assistant renders it
# as "Unknown" beside three legitimately-empty lists — a healthy sensor and one
# that never populated then look identical on screen.
#
# Nothing guarded either value before 2026-08-21, which is how `None` survived
# in two places for as long as it did.


@pytest.mark.asyncio
async def test_a_healthy_snapshot_says_ok_rather_than_nothing(
    hass, mock_config_entry, mock_wifi_api
):
    """A clean poll publishes `ok`, not `None`."""
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    await coordinator._async_update_data()

    snapshot = coordinator.health_snapshot
    assert snapshot["problem"] is False
    assert snapshot["severity"] == SEVERITY_OK
    assert snapshot["issues"] == []


def test_the_cold_start_snapshot_says_unknown(hass, mock_config_entry, mock_wifi_api):
    """Before the first poll the verdict is `unknown`, and no problem is raised.

    Section 19 maps `unknown` to the sensor being on. It is deliberately paired
    with `problem: False` here: firing the problem sensor on every restart is
    the jitter the same section forbids, and it would clear itself one poll
    later. `zte_router_5g` makes the same pairing.
    """
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)

    assert coordinator.health_snapshot["severity"] == SEVERITY_UNKNOWN
    assert coordinator.health_snapshot["problem"] is False


@pytest.mark.asyncio
async def test_no_code_path_publishes_a_blank_severity(
    hass, mock_config_entry, mock_wifi_api
):
    """Sweep the three snapshot writers; none of them may leave it empty.

    Written as a sweep rather than three assertions because the failure mode is
    a *new* path added later that forgets — which is exactly how the two
    original `None`s got there.
    """
    from custom_components.wifi_ssid_monitor.health import _SEVERITY_RANK

    allowed = set(_SEVERITY_RANK) | {SEVERITY_UNKNOWN}
    coordinator = _coord(hass, mock_config_entry, mock_wifi_api)
    seen = [coordinator.health_snapshot["severity"]]

    # Assigned by hand: driving `_async_update_data` directly bypasses the
    # coordinator wrapper that normally sets `data`, and without held values
    # the failure path below takes the cold-start branch instead of the strike
    # budget — a different writer from the one under test here.
    coordinator.data = await coordinator._async_update_data()
    seen.append(coordinator.health_snapshot["severity"])

    mock_wifi_api.get_access_points.side_effect = WifiScanError("down")
    for _ in range(FETCH_STRIKE_LIMIT):
        await coordinator._async_update_data()
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
    seen.append(coordinator.health_snapshot["severity"])

    assert all(value in allowed for value in seen), seen
    assert None not in seen


@pytest.mark.asyncio
async def test_discarded_timestamps_are_counted_not_named(caplog):
    """A corrupt stored row is logged as a count, never as its network key.

    Section 20, and x_project chore C-020. The key here is a neighbouring
    network's SSID or its Hidden-<last4> label — third-party data, in a file
    with nothing stripping it.
    """
    import logging

    from custom_components.wifi_ssid_monitor.coordinator import _parse_timestamps

    with caplog.at_level(logging.DEBUG):
        parsed = _parse_timestamps(
            {
                "TheNeighbours": "not-a-timestamp",
                "Hidden-9f3a": "also-not",
                "Home": "2026-08-21T12:00:00+00:00",
            }
        )

    assert set(parsed) == {"Home"}
    assert "2" in caplog.text, "the count is what the line is for"
    assert "TheNeighbours" not in caplog.text
    assert "Hidden-9f3a" not in caplog.text
