from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.wifi_scan_ssid.const import (
    CONF_INTERFACE,
    CONF_KNOWN_SSIDS,
    CONF_SCAN_INTERVAL,
    DOMAIN,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations."""
    yield


@pytest.fixture
def mock_config_entry():
    """Mock a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id="wifi_scan_wlan0",
        title="Wifi Scan wlan0",
        data={
            CONF_INTERFACE: "wlan0",
        },
        options={
            CONF_KNOWN_SSIDS: "MyNetwork1,MyNetwork2",
            CONF_SCAN_INTERVAL: 60,
        },
        entry_id="test_entry_id",
    )


@pytest.fixture
def mock_wifi_api():
    """Mock WifiScanAPI."""
    api = MagicMock()
    api.get_access_points = AsyncMock(
        return_value=[
            {"ssid": "MyNetwork1", "signal": -50},
            {"ssid": "UnknownNet", "signal": -70},
        ]
    )
    return api


@pytest.fixture
def mock_coordinator(hass, mock_config_entry, mock_wifi_api):
    """Mock WifiScanCoordinator."""
    from custom_components.wifi_scan_ssid.coordinator import WifiScanCoordinator

    coordinator = WifiScanCoordinator(hass, mock_config_entry, mock_wifi_api)
    coordinator.data = {
        "count": 2,
        "ssids": ["MyNetwork1", "UnknownNet"],
        "unknown_ssids": ["UnknownNet"],
        "unknown_count": 1,
    }
    return coordinator


class MockResponse:
    """Helper to mock aiohttp responses."""

    def __init__(self, json_data=None, status=200, text_data=""):
        self._json_data = json_data
        self.status = status
        self._text_data = text_data

    async def json(self, **kwargs):
        return self._json_data

    async def text(self):
        return self._text_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def mock_aiohttp_client():
    """Fixture to mock aiohttp ClientSession."""
    session = MagicMock()
    session.get = MagicMock()
    return session
