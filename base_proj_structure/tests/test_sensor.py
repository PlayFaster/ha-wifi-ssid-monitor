from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.util import dt as dt_util

from custom_components.zte_router_5g.const import DOMAIN
from custom_components.zte_router_5g.sensor import (
    MSG_RECENT_DESCRIPTION,
    MSG_TOTAL_DESCRIPTION,
    SENSOR_TYPES,
    ZTEDataSensor,
    ZTEMsgContentSensor,
    ZTEMsgSensor,
    async_setup_entry,
)

# --- TESTS FOR ZTEDataSensor ---


def test_data_sensor_rsrp_simple(mock_coordinator, mock_config_entry):
    """Test standard technical sensor extraction."""
    mock_coordinator.data = {"lte_rsrp": "-95"}
    description = next(d for d in SENSOR_TYPES if d.key == "lte_rsrp")
    sensor = ZTEDataSensor(mock_coordinator, mock_config_entry, description)

    assert sensor.native_value == "-95"


def test_data_sensor_z5g_case_sensitivity(mock_coordinator, mock_config_entry):
    """Test the specific case-sensitive mapping for 5G keys."""
    # The router provides 'Z5g_rsrp' but our key is 'z5g_rsrp'
    mock_coordinator.data = {"Z5g_rsrp": "-102"}
    description = next(d for d in SENSOR_TYPES if d.key == "z5g_rsrp")
    sensor = ZTEDataSensor(mock_coordinator, mock_config_entry, description)
    assert sensor.native_value == "-102"

    # Test sinr
    mock_coordinator.data = {"Z5g_SINR": "15"}
    description = next(d for d in SENSOR_TYPES if d.key == "z5g_sinr")
    sensor = ZTEDataSensor(mock_coordinator, mock_config_entry, description)
    assert sensor.native_value == "15"


def test_data_sensor_byte_to_gb_conversion(mock_coordinator, mock_config_entry):
    """Test that monthly_rx_bytes is converted from bytes to GB."""
    # 2GB in bytes
    mock_coordinator.data = {"monthly_rx_bytes": "2147483648"}
    description = next(d for d in SENSOR_TYPES if d.key == "monthly_rx_bytes")
    sensor = ZTEDataSensor(mock_coordinator, mock_config_entry, description)

    # 2147483648 / 1073741824 = 2.0
    assert sensor.native_value == 2.0


def test_data_sensor_monthly_total_sum(mock_coordinator, mock_config_entry):
    """Test the manual summing and conversion of monthly_total_bytes."""
    mock_coordinator.data = {
        "monthly_rx_bytes": "1073741824",  # 1GB
        "monthly_tx_bytes": "536870912",  # 0.5GB
    }
    description = next(d for d in SENSOR_TYPES if d.key == "monthly_total_bytes")
    sensor = ZTEDataSensor(mock_coordinator, mock_config_entry, description)

    assert sensor.native_value == 1.5

    # Test error path
    mock_coordinator.data = {"monthly_rx_bytes": "invalid"}
    assert sensor.native_value is None


def test_data_sensor_uptime_calculation(mock_coordinator, mock_config_entry):
    """Test the complex uptime to timestamp conversion."""
    # Mock 'now' to a fixed point
    now = dt_util.now().replace(second=0, microsecond=0)
    # 3600 seconds = 1 hour uptime
    mock_coordinator.data = {"realtime_time": "3600"}

    description = next(d for d in SENSOR_TYPES if d.key == "device_uptime")
    sensor = ZTEDataSensor(mock_coordinator, mock_config_entry, description)

    with patch("homeassistant.util.dt.now", return_value=now):
        # Result should be exactly 1 hour ago
        expected_time = now - timedelta(seconds=3600)
        assert sensor.native_value == expected_time

    # Test empty case
    mock_coordinator.data = {"realtime_time": ""}
    assert sensor.native_value is None

    # Test exception case
    mock_coordinator.data = {"realtime_time": "invalid"}
    assert sensor.native_value is None


def test_data_sensor_last_updated(mock_coordinator, mock_config_entry):
    """Test the last_updated sensor."""
    now = dt_util.now()
    mock_coordinator.last_update_success_time = now
    # Ensure data is truthy so the property proceeds
    mock_coordinator.data = {"some": "data"}

    description = next(d for d in SENSOR_TYPES if d.key == "last_updated")
    sensor = ZTEDataSensor(mock_coordinator, mock_config_entry, description)

    assert sensor.native_value == now


def test_data_sensor_error_handling(mock_coordinator, mock_config_entry):
    """Test error handling in native_value."""
    mock_coordinator.data = {"monthly_rx_bytes": "invalid"}
    description = next(d for d in SENSOR_TYPES if d.key == "monthly_rx_bytes")
    sensor = ZTEDataSensor(mock_coordinator, mock_config_entry, description)

    # Should return original value if float conversion fails
    assert sensor.native_value == "invalid"


def test_data_sensor_device_info(mock_coordinator, mock_config_entry):
    """Test device_info for main and data groups."""
    # Main group sensor
    description = next(d for d in SENSOR_TYPES if d.key == "lte_rsrp")
    sensor = ZTEDataSensor(mock_coordinator, mock_config_entry, description)
    info = sensor.device_info
    assert info["identifiers"] == {(DOMAIN, "192.168.0.1")}
    assert info["name"] == "My ZTE Router"

    # Data group sensor
    description = next(d for d in SENSOR_TYPES if d.key == "monthly_rx_bytes")
    sensor = ZTEDataSensor(mock_coordinator, mock_config_entry, description)
    info = sensor.device_info
    assert info["identifiers"] == {(DOMAIN, "192.168.0.1_monthly")}


# --- TESTS FOR ZTEMsgSensor (SMS Counts) ---


def test_msg_sensor_summing(mock_coordinator, mock_config_entry):
    """Test that all 6 SMS storage keys are summed correctly."""
    mock_coordinator.data = {
        "sms_nv_rev_total": "10",
        "sms_nv_send_total": "5",
        "sms_nv_draftbox_total": "1",
        "sms_sim_rev_total": "2",
        "sms_sim_send_total": "0",
        "sms_sim_draftbox_total": "1",
    }
    sensor = ZTEMsgSensor(mock_coordinator, mock_config_entry, MSG_TOTAL_DESCRIPTION)

    # Sum: 10 + 5 + 1 + 2 + 0 + 1 = 19
    assert sensor.native_value == 19

    # Test exception handling
    mock_coordinator.data = {"sms_nv_rev_total": "invalid"}
    assert sensor.native_value is None


def test_msg_sensor_attributes(mock_coordinator, mock_config_entry):
    """Test that extra state attributes provide the raw breakdown."""
    mock_coordinator.data = {"sms_nv_total": "15", "sms_sim_total": "5"}
    sensor = ZTEMsgSensor(mock_coordinator, mock_config_entry, MSG_TOTAL_DESCRIPTION)

    attrs = sensor.extra_state_attributes
    assert attrs["sms_nv_total"] == 15
    assert attrs["sms_sim_total"] == 5

    # Test exception handling
    mock_coordinator.data = {"sms_nv_total": "invalid"}
    assert sensor.extra_state_attributes == {}


# --- TESTS FOR ZTEMsgContentSensor (Recent SMS) ---


def test_msg_content_extraction(mock_coordinator, mock_config_entry):
    """Test extraction of the last SMS content."""
    mock_coordinator.data = {
        "last_sms": {
            "id": "1",
            "content_decoded": "Hello from ZTE!",
            "number_decoded": "123456",
            "date_decoded": "2023-10-10 10:00:00",
        }
    }
    sensor = ZTEMsgContentSensor(
        mock_coordinator, mock_config_entry, MSG_RECENT_DESCRIPTION
    )

    assert sensor.native_value == "Hello from ZTE!"
    assert sensor.extra_state_attributes["number"] == "123456"
    assert sensor.extra_state_attributes["id"] == "1"
    assert sensor.device_info["identifiers"] == {(DOMAIN, "192.168.0.1_sms")}


def test_msg_content_empty_state(mock_coordinator, mock_config_entry):
    """Test handling when no messages exist."""
    mock_coordinator.data = {}
    sensor = ZTEMsgContentSensor(
        mock_coordinator, mock_config_entry, MSG_RECENT_DESCRIPTION
    )

    assert sensor.native_value == "No messages"
    assert sensor.extra_state_attributes == {}


@pytest.mark.asyncio
async def test_sensor_setup_entry():
    """Test platform setup."""
    hass = MagicMock()
    entry = MagicMock()
    entry.entry_id = "test"
    # hass.data[DOMAIN][entry_id] is the coordinator
    hass.data = {DOMAIN: {"test": MagicMock()}}

    async_add_entities = MagicMock()
    await async_setup_entry(hass, entry, async_add_entities)
    async_add_entities.assert_called_once()
