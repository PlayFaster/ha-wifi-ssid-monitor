from unittest.mock import patch

import pytest
from homeassistant import data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.wifi_scan_ssid.const import (
    CONF_INTERFACE,
    CONF_KNOWN_SSIDS,
    CONF_SCAN_INTERVAL,
    DOMAIN,
)


@pytest.mark.asyncio
async def test_user_flow(hass: HomeAssistant):
    """Test the user setup flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(
        "custom_components.wifi_scan_ssid.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_INTERFACE: "wlan0",
                CONF_KNOWN_SSIDS: "MyNet1,MyNet2",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "Wifi Scan (wlan0)"
    assert result["data"] == {
        CONF_INTERFACE: "wlan0",
        CONF_KNOWN_SSIDS: "MyNet1,MyNet2",
    }
    assert result["options"] == {
        CONF_INTERFACE: "wlan0",
        CONF_KNOWN_SSIDS: "MyNet1,MyNet2",
        CONF_SCAN_INTERVAL: 180,
    }
    assert len(mock_setup_entry.mock_calls) == 1


@pytest.mark.asyncio
async def test_options_flow(hass: HomeAssistant, mock_config_entry):
    """Test the options flow."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_INTERFACE: "wlan1",
            CONF_KNOWN_SSIDS: "NewNet1",
            CONF_SCAN_INTERVAL: 60,
        },
    )

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_INTERFACE: "wlan1",
        CONF_KNOWN_SSIDS: "NewNet1",
        CONF_SCAN_INTERVAL: 60,
    }
