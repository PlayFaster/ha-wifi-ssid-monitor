"""Fixtures for WiFi SSID Monitor tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.wifi_ssid_monitor.const import (
    CONF_INTERFACE,
    CONF_KNOWN_SSIDS,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    DOMAIN,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations."""
    return


@pytest.fixture
def mock_config_entry():
    """Mock a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id="wifi_ssid_monitor_wlan0",
        title="WiFi SSID Monitor",
        data={},
        options={
            CONF_NAME: "WiFi SSID Monitor",
            CONF_INTERFACE: "wlan0",
            CONF_KNOWN_SSIDS: "MyNetwork1,MyNetwork2",
            CONF_SCAN_INTERVAL: 60,
        },
        entry_id="test_entry_id",
    )


@pytest.fixture
def mock_wifi_api():
    """Mock WifiScanAPI returning the real Supervisor shape.

    The Supervisor reports ``signal`` as a 0-100 percentage and ``frequency``
    in MHz (there is no ``channel`` field).
    """
    api = MagicMock()
    api.get_access_points = AsyncMock(
        return_value=[
            {
                "mac": "AA:BB:CC:00:00:01",
                "ssid": "MyNetwork1",
                "signal": 80,
                "frequency": 2462,
                "mode": "infrastructure",
            },
            {
                "mac": "AA:BB:CC:00:00:02",
                "ssid": "UnknownNet",
                "signal": 55,
                "frequency": 5240,
                "mode": "infrastructure",
            },
        ]
    )
    api.interface = "wlan0"
    api.last_response_had_ap_key = True
    return api


@pytest.fixture
def mock_coordinator(hass, mock_config_entry, mock_wifi_api):
    """Mock WiFi SSID Monitor coordinator."""
    from custom_components.wifi_ssid_monitor.coordinator import WifiScanCoordinator

    coordinator = WifiScanCoordinator(hass, mock_config_entry, mock_wifi_api, "1.7.0")
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
        "last_seen": {},
        "first_seen": {},
        "visit_counts": {},
        "new_24h": 0,
        "strongest_unknown_signal": 55,
        "strongest_unknown_ssid": "UnknownNet",
        "signal_unit": "percent",
    }
    return coordinator


class MockResponse:
    """Helper to mock aiohttp responses."""

    def __init__(self, json_data=None, status=200, text_data="", json_error=False):
        """Initialize the mock response."""
        self._json_data = json_data
        self.status = status
        self._text_data = text_data
        self._json_error = json_error

    async def json(self, **kwargs):
        """Return the JSON data."""
        if self._json_error:
            import aiohttp

            raise aiohttp.ContentTypeError(MagicMock(), MagicMock())
        return self._json_data

    async def text(self):
        """Return the text data."""
        return self._text_data

    async def __aenter__(self):
        """Enter the context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""


@pytest.fixture
def mock_aiohttp_client():
    """Fixture to mock aiohttp ClientSession."""
    session = MagicMock()
    session.get = MagicMock()
    return session


@pytest.fixture(autouse=True)
def schedule_background_tasks():
    """Make `entry.async_create_background_task` actually run the coroutine.

    dev_standards Section 11 names this fixture explicitly. `async_setup_entry`
    offloads the first fetch with `entry.async_create_background_task` (Section
    1, non-blocking startup), and a mock that accepts the coroutine without
    scheduling it produces two problems at once: the first refresh never runs,
    so tests assert against a coordinator that never fetched, and Python emits
    "coroutine was never awaited" warnings that make the real signal harder to
    see.

    Scheduling it with `asyncio.create_task` keeps the production path intact —
    the task is created and awaited normally — so a test that calls
    `await hass.async_block_till_done()` afterwards observes exactly what
    Home Assistant would.

    Autouse and non-invasive: it delegates to the real implementation, so it
    changes nothing today. It exists so that a future change to how HA tracks
    background tasks fails visibly here rather than silently skipping the first
    fetch in every setup test.
    """
    import asyncio

    from homeassistant.config_entries import ConfigEntry

    original = ConfigEntry.async_create_background_task

    def _create(self, hass, target, name, eager_start=True):
        task = original(self, hass, target, name, eager_start=eager_start)
        assert isinstance(task, asyncio.Task | asyncio.Future), (
            f"background task {name!r} was not scheduled — the coroutine would "
            f"never be awaited and the first fetch would silently not happen"
        )
        return task

    with patch.object(ConfigEntry, "async_create_background_task", _create):
        yield
