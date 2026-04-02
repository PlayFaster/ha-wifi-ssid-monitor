from unittest.mock import MagicMock

import pytest

from custom_components.zte_router_5g.binary_sensor import (
    BEST_CONN_DESCRIPTION,
    ZTEBestConnectionSensor,
    async_setup_entry,
)
from custom_components.zte_router_5g.const import DOMAIN


def test_binary_sensor_is_on(mock_coordinator, mock_config_entry):
    """Test the optimal connection logic."""
    sensor = ZTEBestConnectionSensor(
        mock_coordinator, mock_config_entry, BEST_CONN_DESCRIPTION
    )

    # 1. Both active
    mock_coordinator.data = {"network_type": "ENDC", "wan_lte_ca": "ca_activated"}
    assert sensor.is_on is True
    assert sensor.icon == "mdi:signal"

    # 2. Only one active
    mock_coordinator.data = {"network_type": "LTE", "wan_lte_ca": "ca_activated"}
    assert sensor.is_on is False
    assert sensor.icon == "mdi:signal-cellular-1"

    # 3. None active
    mock_coordinator.data = {}
    assert sensor.is_on is False


def test_binary_sensor_device_info(mock_coordinator, mock_config_entry):
    """Test device_info links to router."""
    sensor = ZTEBestConnectionSensor(
        mock_coordinator, mock_config_entry, BEST_CONN_DESCRIPTION
    )
    info = sensor.device_info
    assert info["identifiers"] == {(DOMAIN, "192.168.0.1")}
    assert info["manufacturer"] == "ZTE"


@pytest.mark.asyncio
async def test_binary_sensor_setup_entry():
    """Test platform setup."""
    hass = MagicMock()
    entry = MagicMock()
    entry.entry_id = "test"
    coordinator = MagicMock()
    hass.data = {DOMAIN: {"test": coordinator}}

    async_add_entities = MagicMock()
    await async_setup_entry(hass, entry, async_add_entities)
    async_add_entities.assert_called_once()
