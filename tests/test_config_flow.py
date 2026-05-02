"""Tests for WiFi SSID Monitor config flow."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.wifi_ssid_monitor.api import WifiScanError
from custom_components.wifi_ssid_monitor.const import (
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

    with (
        patch(
            "custom_components.wifi_ssid_monitor.async_setup_entry", return_value=True
        ) as mock_setup_entry,
        patch(
            "custom_components.wifi_ssid_monitor.config_flow._validate_input",
            return_value=None,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_INTERFACE: "wlan0",
                CONF_KNOWN_SSIDS: "MyNet1,MyNet2",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "WiFi SSID Monitor"
    assert result["data"] == {}
    assert result["options"] == {
        "name": "WiFi SSID Monitor",
        CONF_INTERFACE: "wlan0",
        CONF_KNOWN_SSIDS: "MyNet1,MyNet2",
        CONF_SCAN_INTERVAL: 600,
    }
    assert len(mock_setup_entry.mock_calls) == 1


@pytest.mark.asyncio
async def test_user_flow_multiple_instances(hass: HomeAssistant, mock_config_entry):
    """Test user setup flow when an instance is already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    with (
        patch(
            "custom_components.wifi_ssid_monitor.async_setup_entry", return_value=True
        ) as mock_setup_entry,
        patch(
            "custom_components.wifi_ssid_monitor.config_flow._validate_input",
            return_value=None,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_INTERFACE: "wlan1",
                CONF_KNOWN_SSIDS: "OtherNet",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "WiFi SSID Monitor"
    assert len(mock_setup_entry.mock_calls) >= 1


@pytest.mark.asyncio
async def test_user_flow_already_configured(hass: HomeAssistant, mock_config_entry):
    """Test user setup flow when interface is already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    with patch(
        "custom_components.wifi_ssid_monitor.config_flow._validate_input",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_INTERFACE: "wlan0",
                CONF_KNOWN_SSIDS: "MyNet1,MyNet2",
            },
        )

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.asyncio
async def test_user_flow_cannot_connect(hass: HomeAssistant):
    """Test user setup flow when cannot connect."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    with patch(
        "custom_components.wifi_ssid_monitor.config_flow._validate_input",
        side_effect=WifiScanError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_INTERFACE: "wlan0",
                CONF_KNOWN_SSIDS: "MyNet1",
            },
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


@pytest.mark.asyncio
async def test_user_flow_unknown_exception(hass: HomeAssistant):
    """Test user setup flow when an unknown exception occurs."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    with patch(
        "custom_components.wifi_ssid_monitor.config_flow._validate_input",
        side_effect=Exception,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_INTERFACE: "wlan0",
                CONF_KNOWN_SSIDS: "MyNet1",
            },
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


@pytest.mark.asyncio
async def test_user_flow_with_interfaces(hass: HomeAssistant):
    """Test user setup flow when interfaces are found."""
    with patch(
        "custom_components.wifi_ssid_monitor.config_flow._get_wifi_interfaces",
        return_value=["wlan0", "wlan1"],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    # Check that wlan0 is in the selection
    schema = result["data_schema"].schema
    # Look for CONF_INTERFACE key (might be a vol.Required object)
    interface_key = next(k for k in schema if k == CONF_INTERFACE)
    assert "wlan0" in schema[interface_key].container


@pytest.mark.asyncio
async def test_options_flow(hass: HomeAssistant, mock_config_entry):
    """Test the options flow."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.config_flow._get_wifi_interfaces",
        return_value=["wlan0", "wlan1"],
    ):
        result = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"

    with (
        patch(
            "custom_components.wifi_ssid_monitor.config_flow._get_wifi_interfaces",
            return_value=["wlan0", "wlan1"],
        ),
        patch(
            "custom_components.wifi_ssid_monitor.config_flow._validate_input",
            return_value=None,
        ),
    ):
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
        "name": "WiFi SSID Monitor",
        CONF_INTERFACE: "wlan1",
        CONF_KNOWN_SSIDS: "NewNet1",
        CONF_SCAN_INTERVAL: 60,
    }


@pytest.mark.asyncio
async def test_options_flow_cannot_connect(hass: HomeAssistant, mock_config_entry):
    """Test options flow when cannot connect."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.config_flow._get_wifi_interfaces",
        return_value=["wlan0", "wlan1"],
    ):
        result = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )

    with (
        patch(
            "custom_components.wifi_ssid_monitor.config_flow._get_wifi_interfaces",
            return_value=["wlan0", "wlan1"],
        ),
        patch(
            "custom_components.wifi_ssid_monitor.config_flow._validate_input",
            side_effect=WifiScanError,
        ),
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_INTERFACE: "wlan1",  # Changed interface to trigger validation
                CONF_KNOWN_SSIDS: "NewNet1",
                CONF_SCAN_INTERVAL: 60,
            },
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


@pytest.mark.asyncio
async def test_options_flow_unknown_exception(hass: HomeAssistant, mock_config_entry):
    """Test options flow when unknown exception occurs."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.config_flow._get_wifi_interfaces",
        return_value=["wlan0", "wlan1"],
    ):
        result = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )

    with (
        patch(
            "custom_components.wifi_ssid_monitor.config_flow._get_wifi_interfaces",
            return_value=["wlan0", "wlan1"],
        ),
        patch(
            "custom_components.wifi_ssid_monitor.config_flow._validate_input",
            side_effect=Exception,
        ),
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_INTERFACE: "wlan1",
                CONF_KNOWN_SSIDS: "NewNet1",
                CONF_SCAN_INTERVAL: 60,
            },
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


@pytest.mark.asyncio
async def test_options_flow_no_detected_interfaces(
    hass: HomeAssistant, mock_config_entry
):
    """Test options flow when no interfaces are detected by API."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.config_flow._get_wifi_interfaces",
        return_value=[],
    ):
        result = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    # Even if API returned [], it should still show the current interface
    schema = result["data_schema"].schema
    interface_key = next(k for k in schema if k == CONF_INTERFACE)
    assert "wlan0" in schema[interface_key].container


@pytest.mark.asyncio
async def test_validate_input_helper(hass: HomeAssistant):
    """Test _validate_input helper."""
    from custom_components.wifi_ssid_monitor.config_flow import _validate_input

    with patch(
        "custom_components.wifi_ssid_monitor.config_flow.WifiScanAPI"
    ) as mock_api:
        mock_instance = mock_api.return_value
        mock_instance.validate = AsyncMock()
        await _validate_input(hass, {CONF_INTERFACE: "wlan0"})
        assert len(mock_instance.validate.mock_calls) == 1


@pytest.mark.asyncio
async def test_get_wifi_interfaces_helper(hass: HomeAssistant):
    """Test _get_wifi_interfaces helper."""
    from custom_components.wifi_ssid_monitor.config_flow import _get_wifi_interfaces

    with patch(
        "custom_components.wifi_ssid_monitor.config_flow.WifiScanAPI"
    ) as mock_api:
        mock_instance = mock_api.return_value
        mock_instance.get_interfaces = AsyncMock(return_value=["wlan0"])

        interfaces = await _get_wifi_interfaces(hass)
        assert interfaces == ["wlan0"]

        # Test error case
        mock_instance.get_interfaces.side_effect = WifiScanError
        interfaces = await _get_wifi_interfaces(hass)
        assert interfaces == []
