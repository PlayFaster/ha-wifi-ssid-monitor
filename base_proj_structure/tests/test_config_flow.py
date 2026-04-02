from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import AbortFlow, FlowResultType

from custom_components.zte_router_5g.api import ZTEAuthError, ZTEConnectionError
from custom_components.zte_router_5g.config_flow import (
    ZTEConfigFlow,
    ZTEOptionsFlow,
    _validate_credentials,
)
from custom_components.zte_router_5g.const import DEFAULT_NAME


@pytest.mark.asyncio
async def test_validate_credentials_success():
    """Test _validate_credentials success."""
    hass = MagicMock()
    user_input = {CONF_HOST: "1.1.1.1", CONF_PASSWORD: "pass"}

    with (
        patch(
            "custom_components.zte_router_5g.config_flow.ZTERouterAPI"
        ) as mock_api_class,
        patch("custom_components.zte_router_5g.config_flow.async_get_clientsession"),
    ):
        mock_api = mock_api_class.return_value
        mock_api.try_set_protocol = AsyncMock()
        mock_api.login = AsyncMock()

        await _validate_credentials(hass, user_input)
        mock_api.login.assert_called_once()


@pytest.mark.asyncio
async def test_config_flow_user_step_success():
    """Test successful config flow user step."""
    flow = ZTEConfigFlow()
    flow.hass = MagicMock()
    flow.context = {}
    flow.hass.config_entries.async_entry_for_domain_unique_id.return_value = None

    user_input = {
        CONF_HOST: "192.168.0.1",
        CONF_USERNAME: "admin",
        CONF_PASSWORD: "password",
    }

    with patch(
        "custom_components.zte_router_5g.config_flow._validate_credentials",
        return_value=None,
    ):
        result = await flow.async_step_user(user_input)

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == DEFAULT_NAME
    assert result["options"] == user_input


@pytest.mark.asyncio
async def test_config_flow_user_step_errors():
    """Test error branches in config flow user step."""
    flow = ZTEConfigFlow()
    flow.hass = MagicMock()
    flow.context = {}

    # Test ZTEAuthError
    with patch(
        "custom_components.zte_router_5g.config_flow._validate_credentials",
        side_effect=ZTEAuthError,
    ):
        result = await flow.async_step_user({CONF_HOST: "1.1.1.1", CONF_PASSWORD: "p"})
        assert result["errors"] == {"base": "invalid_auth"}

    # Test ZTEConnectionError
    with patch(
        "custom_components.zte_router_5g.config_flow._validate_credentials",
        side_effect=ZTEConnectionError,
    ):
        result = await flow.async_step_user({CONF_HOST: "1.1.1.1", CONF_PASSWORD: "p"})
        assert result["errors"] == {"base": "cannot_connect"}

    # Test AbortFlow
    with (
        patch(
            "custom_components.zte_router_5g.config_flow._validate_credentials",
            side_effect=AbortFlow("already_configured"),
        ),
        pytest.raises(AbortFlow),
    ):
        await flow.async_step_user({CONF_HOST: "1.1.1.1", CONF_PASSWORD: "p"})

    # Test Exception (unknown)
    with patch(
        "custom_components.zte_router_5g.config_flow._validate_credentials",
        side_effect=Exception("Unknown"),
    ):
        result = await flow.async_step_user({CONF_HOST: "1.1.1.1", CONF_PASSWORD: "p"})
        assert result["errors"] == {"base": "unknown"}


def test_async_get_options_flow():
    """Test getting the options flow."""
    flow = ZTEConfigFlow()
    entry = MagicMock()
    options_flow = flow.async_get_options_flow(entry)
    assert isinstance(options_flow, ZTEOptionsFlow)


@pytest.mark.asyncio
async def test_options_flow_init_success():
    """Test successful options flow init step."""
    entry = MagicMock()
    entry.options = {CONF_HOST: "192.168.0.1", CONF_PASSWORD: "old_password"}
    flow = ZTEOptionsFlow(entry)
    flow.hass = MagicMock()

    user_input = {CONF_HOST: "192.168.0.1", CONF_PASSWORD: "new_password"}

    with patch(
        "custom_components.zte_router_5g.config_flow._validate_credentials",
        return_value=None,
    ):
        result = await flow.async_step_init(user_input)

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_HOST: "192.168.0.1", CONF_PASSWORD: "new_password"}


@pytest.mark.asyncio
async def test_options_flow_errors():
    """Test error branches in options flow."""
    entry = MagicMock()
    entry.options = {CONF_HOST: "1.1.1.1", CONF_PASSWORD: "p"}
    flow = ZTEOptionsFlow(entry)
    flow.hass = MagicMock()

    # Test ZTEConnectionError
    with patch(
        "custom_components.zte_router_5g.config_flow._validate_credentials",
        side_effect=ZTEConnectionError,
    ):
        result = await flow.async_step_init({CONF_HOST: "1.1.1.1", CONF_PASSWORD: "p"})
        assert result["errors"] == {"base": "cannot_connect"}

    # Test Exception
    with patch(
        "custom_components.zte_router_5g.config_flow._validate_credentials",
        side_effect=Exception,
    ):
        result = await flow.async_step_init({CONF_HOST: "1.1.1.1", CONF_PASSWORD: "p"})
        assert result["errors"] == {"base": "unknown"}
