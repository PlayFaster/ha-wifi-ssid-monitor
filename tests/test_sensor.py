"""Tests for WiFi SSID Monitor sensors."""

from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.wifi_ssid_monitor.const import DOMAIN
from custom_components.wifi_ssid_monitor.sensor import SENSOR_TYPES, WifiScanSensor


@pytest.fixture
def data_initial() -> dict:
    """Return a coordinator data dict in the current shape."""
    return {
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
        "last_seen": {},
        "first_seen": {},
        "visit_counts": {},
        "new_24h": 0,
        "strongest_unknown_signal": 55,
        "strongest_unknown_ssid": "UnknownNet",
        "signal_unit": "percent",
    }


async def _setup(hass, entry):
    entry.add_to_hass(hass)
    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry.runtime_data


@pytest.mark.asyncio
async def test_count_sensors(hass: HomeAssistant, mock_config_entry, data_initial):
    """Total and unknown count states plus their ssids attribute."""
    coordinator = await _setup(hass, mock_config_entry)
    coordinator.data = data_initial
    coordinator.last_update_success = True
    coordinator.async_update_listeners()
    await hass.async_block_till_done()

    state = hass.states.get("sensor.wifi_ssid_monitor_total_ssid_count")
    assert state.state == "2"
    assert state.attributes["ssids"] == ["MyNetwork1", "UnknownNet"]

    state = hass.states.get("sensor.wifi_ssid_monitor_unknown_ssid_count")
    assert state.state == "1"
    assert state.attributes["ssids"] == ["UnknownNet"]

    state = hass.states.get("sensor.wifi_ssid_monitor_interface")
    assert state.state == "wlan0"

    await coordinator.async_shutdown()


@pytest.mark.asyncio
async def test_strongest_unknown_sensors(
    hass: HomeAssistant, mock_config_entry, data_initial
):
    """The strongest-unknown SSID and signal sensors and the detail attribute."""
    coordinator = await _setup(hass, mock_config_entry)
    coordinator.data = data_initial
    coordinator.last_update_success = True
    coordinator.async_update_listeners()
    await hass.async_block_till_done()

    ssid = hass.states.get("sensor.wifi_ssid_monitor_strongest_unknown_ssid")
    assert ssid.state == "UnknownNet"
    # The per-network detail lives here now, as a list.
    networks = ssid.attributes["networks"]
    assert isinstance(networks, list)
    assert networks[0]["ssid"] == "UnknownNet"
    assert networks[0]["signal"] == 55
    assert networks[0]["band"] == "5 GHz"

    signal = hass.states.get("sensor.wifi_ssid_monitor_strongest_unknown_signal")
    assert signal.state == "55"

    await coordinator.async_shutdown()


@pytest.mark.asyncio
async def test_strongest_unknown_none_detected(
    hass: HomeAssistant, mock_config_entry, data_initial
):
    """With nothing unknown, the SSID reads the affirmative sentinel."""
    coordinator = await _setup(hass, mock_config_entry)
    data_initial["unknown_ssids"] = []
    data_initial["strongest_unknown_ssid"] = None
    data_initial["strongest_unknown_signal"] = None
    coordinator.data = data_initial
    coordinator.last_update_success = True
    coordinator.async_update_listeners()
    await hass.async_block_till_done()

    ssid = hass.states.get("sensor.wifi_ssid_monitor_strongest_unknown_ssid")
    assert ssid.state == "None Detected"
    # The numeric partner stays unknown — no invented zero.
    signal = hass.states.get("sensor.wifi_ssid_monitor_strongest_unknown_signal")
    assert signal.state == "unknown"

    await coordinator.async_shutdown()


@pytest.mark.asyncio
async def test_history_attributes_on_strongest(
    hass: HomeAssistant, mock_config_entry, data_initial
):
    """first_seen/last_seen/visit_count ride each network detail entry."""
    from homeassistant.util import dt as dt_util

    coordinator = await _setup(hass, mock_config_entry)
    now = dt_util.now()
    data_initial["last_seen"] = {"UnknownNet": now}
    data_initial["first_seen"] = {"UnknownNet": now}
    data_initial["visit_counts"] = {"UnknownNet": 3}
    coordinator.data = data_initial
    coordinator.last_update_success = True
    coordinator.async_update_listeners()
    await hass.async_block_till_done()

    state = hass.states.get("sensor.wifi_ssid_monitor_strongest_unknown_ssid")
    entry = state.attributes["networks"][0]
    assert entry["visit_count"] == 3
    assert entry["first_seen"] is not None
    assert entry["last_seen"] is not None

    await coordinator.async_shutdown()


@pytest.mark.asyncio
async def test_new_24h_sensor(hass: HomeAssistant, mock_config_entry, data_initial):
    """The New Networks (24h) sensor reflects the data value."""
    coordinator = await _setup(hass, mock_config_entry)
    data_initial["new_24h"] = 4
    coordinator.data = data_initial
    coordinator.last_update_success = True
    coordinator.async_update_listeners()
    await hass.async_block_till_done()

    state = hass.states.get("sensor.wifi_ssid_monitor_new_networks_24h")
    assert state.state == "4"

    await coordinator.async_shutdown()


@pytest.mark.asyncio
async def test_sensors_no_data(hass: HomeAssistant, mock_config_entry):
    """With no data, count sensors are unknown and carry no ssids."""
    coordinator = await _setup(hass, mock_config_entry)
    coordinator.data = None
    coordinator.async_update_listeners()
    await hass.async_block_till_done()

    state = hass.states.get("sensor.wifi_ssid_monitor_total_ssid_count")
    assert state.state == "unknown"
    assert "ssids" not in state.attributes

    await coordinator.async_shutdown()


@pytest.mark.asyncio
async def test_guard_bands(hass: HomeAssistant, mock_config_entry):
    """The count sensor rejects out-of-band values."""
    coordinator = await _setup(hass, mock_config_entry)

    for value, expected in [
        ({"wrong_key": "x"}, "unknown"),
        ({"count": None}, "unknown"),
        ({"count": -1}, "unknown"),
        ({"count": 1000}, "unknown"),
        ({"count": 0}, "0"),
        ({"count": 256}, "256"),
        ({"count": 257}, "unknown"),
    ]:
        coordinator.data = value
        coordinator.async_update_listeners()
        state = hass.states.get("sensor.wifi_ssid_monitor_total_ssid_count")
        assert state.state == expected, value

    await coordinator.async_shutdown()


@pytest.mark.asyncio
async def test_value_fn_wrong_type(hass: HomeAssistant, mock_config_entry):
    """A non-dict data payload is handled without raising."""
    coordinator = await _setup(hass, mock_config_entry)
    coordinator.data = [1, 2, 3]
    coordinator.async_update_listeners()
    await hass.async_block_till_done()

    state = hass.states.get("sensor.wifi_ssid_monitor_total_ssid_count")
    assert state.state == "unknown"

    await coordinator.async_shutdown()


def test_device_info(mock_config_entry, mock_coordinator):
    """The sensor reports the shared device info."""
    sensor = WifiScanSensor(mock_coordinator, mock_config_entry, SENSOR_TYPES[0])
    info = sensor.device_info
    assert info["identifiers"] == {(DOMAIN, mock_config_entry.entry_id)}
    assert info["name"] == "WiFi SSID Monitor"
    assert info["manufacturer"] == "PlayFaster"


@pytest.mark.asyncio
async def test_strongest_unknown_detail_truncated(
    hass: HomeAssistant, mock_config_entry
):
    """When more than NETWORK_ATTR_MAX unknown networks, networks_truncated is set."""
    from custom_components.wifi_ssid_monitor.const import NETWORK_ATTR_MAX

    coordinator = await _setup(hass, mock_config_entry)
    many_unknowns = [f"Unknown{i}" for i in range(NETWORK_ATTR_MAX + 5)]
    data = {
        "count": len(many_unknowns),
        "ssids": many_unknowns,
        "unknown_ssids": many_unknowns,
        "unknown_count": len(many_unknowns),
        "interface": "wlan0",
        "networks": {
            label: {
                "bssid": f"AA:BB:CC:00:{i // 256:02X}:{i % 256:02X}",
                "signal": 50,
                "channel": 6,
                "band": "2.4 GHz",
                "hidden": False,
                "ssid_anomaly": False,
                "mode": "infrastructure",
                "key": label,
            }
            for i, label in enumerate(many_unknowns)
        },
        "last_seen": {},
        "first_seen": {},
        "visit_counts": {},
        "new_24h": 0,
        "strongest_unknown_signal": 50,
        "strongest_unknown_ssid": many_unknowns[0],
        "signal_unit": "percent",
    }
    coordinator.data = data
    coordinator.last_update_success = True
    coordinator.async_update_listeners()
    await hass.async_block_till_done()

    state = hass.states.get("sensor.wifi_ssid_monitor_strongest_unknown_ssid")
    networks = state.attributes["networks"]
    assert len(networks) == NETWORK_ATTR_MAX
    assert state.attributes["networks_truncated"] is True

    await coordinator.async_shutdown()
