from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.zte_router_5g import async_setup_entry, async_unload_entry
from custom_components.zte_router_5g.const import (
    CONF_SCAN_INTERVAL,
    CONF_STOP_POLLING,
    DOMAIN,
)
from custom_components.zte_router_5g.coordinator import ZTERouterDataUpdateCoordinator


@pytest.fixture(autouse=True)
def mock_report_usage():
    """Mock report_usage to avoid 'Frame helper not set up' error."""
    with patch("homeassistant.helpers.frame.report_usage"):
        yield


@pytest.fixture
def mock_hass():
    """Create a mock HomeAssistant instance with necessary async methods."""
    hass = MagicMock()
    hass.data = {}
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    hass.config_entries.async_update_entry = MagicMock()

    # Mock async_create_task and close coroutine to avoid RuntimeWarning
    def mock_create_task(coro):
        coro.close()
        return MagicMock()

    hass.async_create_task = MagicMock(side_effect=mock_create_task)
    return hass


@pytest.mark.asyncio
async def test_setup_entry_success(mock_hass, mock_config_entry):
    """Test successful setup of the integration."""
    mock_config_entry.entry_id = "test_entry"
    mock_config_entry.options = {
        "host": "192.168.0.1",
        "password": "pass",
        CONF_STOP_POLLING: False,
        CONF_SCAN_INTERVAL: 60,
    }

    with (
        patch("custom_components.zte_router_5g.ZTERouterAPI"),
        patch("custom_components.zte_router_5g.async_get_clientsession"),
    ):
        assert await async_setup_entry(mock_hass, mock_config_entry) is True

        assert mock_config_entry.entry_id in mock_hass.data[DOMAIN]
        coordinator = mock_hass.data[DOMAIN][mock_config_entry.entry_id]
        assert isinstance(coordinator, ZTERouterDataUpdateCoordinator)

        mock_hass.config_entries.async_forward_entry_setups.assert_called_once()
        mock_hass.async_create_task.assert_called_once()


@pytest.mark.asyncio
async def test_unload_entry_success(mock_hass, mock_config_entry):
    """Test successful unloading of the integration."""
    mock_api = MagicMock()
    mock_coordinator = MagicMock()
    mock_coordinator.api = mock_api
    mock_config_entry.entry_id = "test_entry"
    mock_hass.data = {DOMAIN: {"test_entry": mock_coordinator}}

    assert await async_unload_entry(mock_hass, mock_config_entry) is True
    assert DOMAIN not in mock_hass.data


@pytest.mark.asyncio
async def test_async_update_data_success(mock_hass, mock_config_entry):
    """Test the coordinator's update method success path."""
    mock_config_entry.entry_id = "test_entry"
    mock_config_entry.options = {
        "host": "192.168.0.1",
        "password": "pass",
        CONF_STOP_POLLING: False,
        CONF_SCAN_INTERVAL: 60,
    }

    with (
        patch("custom_components.zte_router_5g.ZTERouterAPI") as mock_api_class,
        patch("custom_components.zte_router_5g.async_get_clientsession"),
    ):
        mock_api = mock_api_class.return_value
        mock_api.get_all_data = AsyncMock(return_value={"network_type": "LTE"})
        mock_api.get_sms_capacity = AsyncMock(return_value={"total": 10})
        mock_api.get_last_sms_content = AsyncMock(return_value={"content": "hello"})

        # Setup to get the coordinator
        await async_setup_entry(mock_hass, mock_config_entry)
        coordinator = mock_hass.data[DOMAIN]["test_entry"]

        data = await coordinator._async_update_data()

        assert data["network_type"] == "LTE"
        assert data["total"] == 10
        assert data["last_sms"] == {"content": "hello"}
        assert coordinator.consecutive_failures == 0


@pytest.mark.asyncio
async def test_async_update_data_paused(mock_hass, mock_config_entry):
    """Test update data when paused."""
    mock_config_entry.entry_id = "test_entry"
    mock_config_entry.options = {
        "host": "192.168.0.1",
        "password": "pass",
        CONF_STOP_POLLING: True,
        CONF_SCAN_INTERVAL: 60,
    }

    with (
        patch("custom_components.zte_router_5g.ZTERouterAPI"),
        patch("custom_components.zte_router_5g.async_get_clientsession"),
    ):
        await async_setup_entry(mock_hass, mock_config_entry)
        coordinator = mock_hass.data[DOMAIN]["test_entry"]

        # Case 1: Paused but NOT first run
        coordinator.data = {"cached": "data"}
        data = await coordinator._async_update_data()
        assert data == {"cached": "data"}

        # Case 2: Paused and first run -> attempts fetch (mock failure)
        coordinator.data = None
        coordinator.api.get_all_data = AsyncMock(side_effect=Exception("Fail"))

        with patch("asyncio.sleep", AsyncMock()):
            data = await coordinator._async_update_data()
            assert data == {}


@pytest.mark.asyncio
async def test_async_update_data_retry_and_resilience(mock_hass, mock_config_entry):
    """Test retry logic and failure resilience."""
    mock_config_entry.entry_id = "test_entry"
    mock_config_entry.options = {
        "host": "192.168.0.1",
        "password": "pass",
        CONF_STOP_POLLING: False,
        CONF_SCAN_INTERVAL: 60,
    }

    with (
        patch("custom_components.zte_router_5g.ZTERouterAPI"),
        patch("custom_components.zte_router_5g.async_get_clientsession"),
    ):
        await async_setup_entry(mock_hass, mock_config_entry)
        coordinator = mock_hass.data[DOMAIN]["test_entry"]
        coordinator.data = {"old": "data"}

        coordinator.api.get_all_data = AsyncMock(
            side_effect=Exception("Persistent Fail")
        )

        # Test retry logic and holding values
        with patch("asyncio.sleep", AsyncMock()):
            data = await coordinator._async_update_data()
            assert data == {"old": "data"}
            assert coordinator.consecutive_failures == 1

            with pytest.raises(UpdateFailed):
                await coordinator._async_update_data()
            assert coordinator.consecutive_failures == 2


@pytest.mark.asyncio
async def test_background_setup_failure(mock_hass, mock_config_entry):
    """Test that background setup failure is handled gracefully."""
    mock_config_entry.entry_id = "test_entry"
    mock_config_entry.options = {
        "host": "192.168.0.1",
        "password": "pass",
    }

    with (
        patch("custom_components.zte_router_5g.ZTERouterAPI") as mock_api_class,
        patch("custom_components.zte_router_5g.async_get_clientsession"),
    ):
        mock_api = mock_api_class.return_value
        mock_api.try_set_protocol = AsyncMock(side_effect=Exception("Background Fail"))

        background_coro = None

        def mock_capture_task(coro):
            nonlocal background_coro
            background_coro = coro
            return MagicMock()

        mock_hass.async_create_task = mock_capture_task

        await async_setup_entry(mock_hass, mock_config_entry)

        if background_coro:
            await background_coro
