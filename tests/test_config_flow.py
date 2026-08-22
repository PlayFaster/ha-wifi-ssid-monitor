"""Tests for WiFi SSID Monitor config flow."""

from unittest.mock import patch

import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import AbortFlow
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.wifi_ssid_monitor.api import WifiScanError
from custom_components.wifi_ssid_monitor.const import (
    CONF_DENYLIST_SSIDS,
    CONF_INTERFACE,
    CONF_KNOWN_SSIDS,
    CONF_LAST_SEEN_TTL_DAYS,
    DEFAULT_LAST_SEEN_TTL_DAYS,
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
                "name": "WiFi SSID Monitor",
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
        "scan_interval": 600,
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
                "name": "WiFi SSID Monitor",
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
                "name": "WiFi SSID Monitor",
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
                "name": "WiFi SSID Monitor",
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
                "name": "WiFi SSID Monitor",
                CONF_INTERFACE: "wlan0",
                CONF_KNOWN_SSIDS: "MyNet1",
            },
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


@pytest.mark.asyncio
async def test_user_flow_abort_flow(hass: HomeAssistant):
    """Test user setup flow when AbortFlow is raised."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    with patch(
        "custom_components.wifi_ssid_monitor.config_flow._validate_input",
        side_effect=AbortFlow("already_configured"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "name": "WiFi SSID Monitor",
                CONF_INTERFACE: "wlan0",
                CONF_KNOWN_SSIDS: "MyNet1",
            },
        )

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"


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
                "name": "WiFi SSID Monitor",
                CONF_INTERFACE: "wlan1",
                CONF_KNOWN_SSIDS: "NewNet1",
                CONF_DENYLIST_SSIDS: "",
                CONF_LAST_SEEN_TTL_DAYS: DEFAULT_LAST_SEEN_TTL_DAYS,
            },
        )

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "name": "WiFi SSID Monitor",
        CONF_INTERFACE: "wlan1",
        CONF_KNOWN_SSIDS: "NewNet1",
        CONF_DENYLIST_SSIDS: "",
        CONF_LAST_SEEN_TTL_DAYS: DEFAULT_LAST_SEEN_TTL_DAYS,
        "scan_interval": 60,
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
                "name": "WiFi SSID Monitor",
                CONF_INTERFACE: "wlan1",
                CONF_KNOWN_SSIDS: "NewNet1",
                CONF_DENYLIST_SSIDS: "",
                CONF_LAST_SEEN_TTL_DAYS: DEFAULT_LAST_SEEN_TTL_DAYS,
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
                "name": "WiFi SSID Monitor",
                CONF_INTERFACE: "wlan1",
                CONF_KNOWN_SSIDS: "NewNet1",
                CONF_DENYLIST_SSIDS: "",
                CONF_LAST_SEEN_TTL_DAYS: DEFAULT_LAST_SEEN_TTL_DAYS,
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


# ---------------------------------------------------------------------------
# The two helpers, driven over the real transport
# ---------------------------------------------------------------------------
#
# The flow tests below patch `_validate_input` and `_get_wifi_interfaces`
# because they are testing the *flow* — which step follows which, which error
# key is shown, which entry is created. That is legitimate, and it is recorded
# in `tests/test_depth_allowlist.txt`.
#
# What it cannot cover is the helpers themselves, and patching the module's own
# functions puts the mock exactly where a defect would be. These drive them for
# real over `aioclient_mock`, so `api.py` runs and the interface list is
# *derived* from a Supervisor payload rather than handed over by the test.
# `dev_standards.md` Section 11: fake the transport, not the API object.

_NETWORK_INFO_URL = "http://supervisor/network/info"
_ACCESSPOINTS_URL = "http://supervisor/network/interface/wlan0/accesspoints"


@pytest.mark.asyncio
async def test_the_interface_list_is_derived_from_a_supervisor_payload(
    hass: HomeAssistant, aioclient_mock
):
    """Only wireless interfaces, and both spellings of "wireless".

    The Supervisor reports `wifi` on generic-x86-64 and `wireless` on a
    Raspberry Pi 4. Matching only the first made auto-detection return nothing
    on Pi hardware. That filter lives in `api.py`, so it only runs when the
    payload is the input — the previous version of this test set the return
    value directly and could not have caught it.
    """
    import os

    from custom_components.wifi_ssid_monitor.config_flow import _get_wifi_interfaces

    aioclient_mock.get(
        _NETWORK_INFO_URL,
        json={
            "data": {
                "interfaces": [
                    {"interface": "wlan0", "type": "wifi"},
                    {"interface": "wlp2s0", "type": "wireless"},
                    {"interface": "eth0", "type": "ethernet"},
                    {"interface": "", "type": "wifi"},
                ]
            }
        },
    )

    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        assert await _get_wifi_interfaces(hass) == ["wlan0", "wlp2s0"]


@pytest.mark.asyncio
async def test_an_unreachable_supervisor_yields_no_interfaces(
    hass: HomeAssistant, aioclient_mock
):
    """A real 500 becomes a real `WifiScanError`, and the flow sees `[]`.

    This half is the **swallow**: whatever `api.py` raises, the picker gets an
    empty list and the flow falls back to a free-text field rather than
    exploding. The raise itself is a separate assertion below, because from out
    here the two are indistinguishable — a 500 leaves the payload empty, so
    deleting the status guard also returns `[]` and this test alone cannot
    tell. Setting `side_effect = WifiScanError` proved neither.
    """
    import os

    from custom_components.wifi_ssid_monitor.config_flow import _get_wifi_interfaces

    aioclient_mock.get(_NETWORK_INFO_URL, status=500)

    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        assert await _get_wifi_interfaces(hass) == []


@pytest.mark.asyncio
async def test_a_bad_status_raises_rather_than_reporting_no_interfaces(
    hass: HomeAssistant, aioclient_mock
):
    """The other half: `api.py` must **raise**, not return an empty list.

    Asserted against the API object directly, because that is the only place
    the distinction is visible. Without this, deleting
    `raise WifiScanError(f"API returned status {status}")` passes every test in
    this file — a Supervisor outage would then be reported to the user as "this
    machine has no WiFi interfaces", which is a different and much worse lie.
    """
    import os

    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    from custom_components.wifi_ssid_monitor.api import WifiScanAPI

    aioclient_mock.get(_NETWORK_INFO_URL, status=500)

    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        api = WifiScanAPI(async_get_clientsession(hass), "")
        with pytest.raises(WifiScanError, match="500"):
            await api.get_interfaces()


@pytest.mark.asyncio
async def test_a_missing_token_yields_no_interfaces(
    hass: HomeAssistant, aioclient_mock
):
    """No token is the add-on-not-privileged case, and must not raise."""
    import os

    from custom_components.wifi_ssid_monitor.config_flow import _get_wifi_interfaces

    with patch.dict(os.environ, {}, clear=True):
        assert await _get_wifi_interfaces(hass) == []


@pytest.mark.asyncio
async def test_validate_input_accepts_a_real_response(
    hass: HomeAssistant, aioclient_mock
):
    """`_validate_input` succeeds, and the interface it was given reached the wire.

    "It does not raise" is a real contract but a weak assertion. What actually
    has to be true is that the chosen interface ended up in the URL — the bug
    this replaces a test for was exactly that: the old version passed a dict
    here, and nothing noticed because no URL was ever built.
    """
    import os

    from custom_components.wifi_ssid_monitor.config_flow import _validate_input

    aioclient_mock.get(_ACCESSPOINTS_URL, json={"data": {"accesspoints": []}})

    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        await _validate_input(hass, "wlan0")

    assert len(aioclient_mock.mock_calls) == 1
    assert str(aioclient_mock.mock_calls[0][1]) == _ACCESSPOINTS_URL


@pytest.mark.asyncio
async def test_validate_input_raises_when_the_interface_does_not_answer(
    hass: HomeAssistant, aioclient_mock
):
    """The error the flow turns into `cannot_connect`, produced for real.

    `_validate_input` has no `try`, so it is the propagation that matters: a
    bad status inside `api.py` has to arrive here as `WifiScanError`.
    """
    import os

    from custom_components.wifi_ssid_monitor.config_flow import _validate_input

    aioclient_mock.get(_ACCESSPOINTS_URL, status=404)

    with (
        patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}),
        pytest.raises(WifiScanError),
    ):
        await _validate_input(hass, "wlan0")


@pytest.mark.asyncio
async def test_the_user_flow_end_to_end_with_nothing_patched(
    hass: HomeAssistant, aioclient_mock
):
    """The whole flow over the real transport, patching neither helper.

    Every other flow test below stubs both functions. This one proves they are
    genuinely reachable through the flow and that what they return survives
    into the created entry — the interface offered by the picker comes from a
    Supervisor payload, and validation of the chosen interface is a real
    request.
    """
    import os

    aioclient_mock.get(
        _NETWORK_INFO_URL,
        json={"data": {"interfaces": [{"interface": "wlan0", "type": "wifi"}]}},
    )
    aioclient_mock.get(_ACCESSPOINTS_URL, json={"data": {"accesspoints": []}})

    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM

        with patch(
            "custom_components.wifi_ssid_monitor.async_setup_entry", return_value=True
        ):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    "name": "WiFi SSID Monitor",
                    CONF_INTERFACE: "wlan0",
                    CONF_KNOWN_SSIDS: "MyNet1",
                },
            )
            await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["options"][CONF_INTERFACE] == "wlan0"


@pytest.mark.asyncio
async def test_reauth_flow(hass: HomeAssistant, mock_config_entry):
    """Test reauth flow."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": mock_config_entry.entry_id,
        },
        data=mock_config_entry.data,
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    with (
        patch(
            "custom_components.wifi_ssid_monitor.config_flow._validate_input",
            return_value=None,
        ),
        patch(
            "custom_components.wifi_ssid_monitor.async_setup_entry", return_value=True
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={},
        )
        await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"


@pytest.mark.asyncio
async def test_reauth_flow_errors(hass: HomeAssistant, mock_config_entry):
    """Test reauth flow error handling."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": mock_config_entry.entry_id,
        },
        data=mock_config_entry.data,
    )

    # Test cannot_connect
    with patch(
        "custom_components.wifi_ssid_monitor.config_flow._validate_input",
        side_effect=WifiScanError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={},
        )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    # Test unknown exception
    with patch(
        "custom_components.wifi_ssid_monitor.config_flow._validate_input",
        side_effect=Exception,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={},
        )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


@pytest.mark.asyncio
async def test_reconfigure_flow(hass: HomeAssistant, mock_config_entry):
    """Test reconfiguration flow."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.config_flow._get_wifi_interfaces",
        return_value=["wlan0"],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_RECONFIGURE,
                "entry_id": mock_config_entry.entry_id,
            },
            data=mock_config_entry.data,
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    with (
        patch(
            "custom_components.wifi_ssid_monitor.config_flow._get_wifi_interfaces",
            return_value=["wlan0"],
        ),
        patch(
            "custom_components.wifi_ssid_monitor.config_flow._validate_input",
            return_value=None,
        ),
        patch(
            "custom_components.wifi_ssid_monitor.async_setup_entry", return_value=True
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                "name": "WiFi SSID Monitor",
                CONF_INTERFACE: "wlan0",
                CONF_KNOWN_SSIDS: "UpdatedNet",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.options[CONF_KNOWN_SSIDS] == "UpdatedNet"


@pytest.mark.asyncio
async def test_reconfigure_flow_interface_change(
    hass: HomeAssistant, mock_config_entry
):
    """Test reconfiguration flow with interface change."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.config_flow._get_wifi_interfaces",
        return_value=["wlan0", "wlan1"],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_RECONFIGURE,
                "entry_id": mock_config_entry.entry_id,
            },
        )

    with (
        patch(
            "custom_components.wifi_ssid_monitor.config_flow._get_wifi_interfaces",
            return_value=["wlan0", "wlan1"],
        ),
        patch(
            "custom_components.wifi_ssid_monitor.config_flow._validate_input",
            return_value=None,
        ),
        patch(
            "custom_components.wifi_ssid_monitor.async_setup_entry", return_value=True
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                "name": "WiFi SSID Monitor",
                CONF_INTERFACE: "wlan1",
                CONF_KNOWN_SSIDS: "UpdatedNet",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.options[CONF_INTERFACE] == "wlan1"


@pytest.mark.asyncio
async def test_reconfigure_flow_already_configured(
    hass: HomeAssistant, mock_config_entry
):
    """Test reconfigure flow when interface is already used by another entry."""
    mock_config_entry.add_to_hass(hass)

    # Create another entry for wlan1
    other_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Other",
        data={},
        options={CONF_INTERFACE: "wlan1"},
        unique_id="wifi_ssid_monitor_wlan1",
    )
    other_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.config_flow._get_wifi_interfaces",
        return_value=["wlan0", "wlan1"],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_RECONFIGURE,
                "entry_id": mock_config_entry.entry_id,
            },
        )

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
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                "name": "WiFi SSID Monitor",
                CONF_INTERFACE: "wlan1",
                CONF_KNOWN_SSIDS: "UpdatedNet",
            },
        )

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.asyncio
async def test_reconfigure_flow_errors(hass: HomeAssistant, mock_config_entry):
    """Test reconfiguration flow error handling."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.config_flow._get_wifi_interfaces",
        return_value=["wlan0"],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_RECONFIGURE,
                "entry_id": mock_config_entry.entry_id,
            },
        )

    # Test cannot_connect
    with (
        patch(
            "custom_components.wifi_ssid_monitor.config_flow._get_wifi_interfaces",
            return_value=["wlan0"],
        ),
        patch(
            "custom_components.wifi_ssid_monitor.config_flow._validate_input",
            side_effect=WifiScanError,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                "name": "WiFi SSID Monitor",
                CONF_INTERFACE: "wlan0",
                CONF_KNOWN_SSIDS: "UpdatedNet",
            },
        )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    # Test unknown exception
    with (
        patch(
            "custom_components.wifi_ssid_monitor.config_flow._get_wifi_interfaces",
            return_value=["wlan0"],
        ),
        patch(
            "custom_components.wifi_ssid_monitor.config_flow._validate_input",
            side_effect=Exception,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                "name": "WiFi SSID Monitor",
                CONF_INTERFACE: "wlan0",
                CONF_KNOWN_SSIDS: "UpdatedNet",
            },
        )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


@pytest.mark.asyncio
async def test_reconfigure_flow_abort_flow(hass: HomeAssistant, mock_config_entry):
    """Test reconfigure flow when AbortFlow is raised."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.config_flow._get_wifi_interfaces",
        return_value=["wlan0", "wlan1"],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_RECONFIGURE,
                "entry_id": mock_config_entry.entry_id,
            },
        )

    with (
        patch(
            "custom_components.wifi_ssid_monitor.config_flow._get_wifi_interfaces",
            return_value=["wlan0", "wlan1"],
        ),
        patch(
            "custom_components.wifi_ssid_monitor.config_flow._validate_input",
            side_effect=AbortFlow("already_configured"),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                "name": "WiFi SSID Monitor",
                CONF_INTERFACE: "wlan1",
                CONF_KNOWN_SSIDS: "UpdatedNet",
            },
        )

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.asyncio
async def test_options_flow_name_change(hass: HomeAssistant, mock_config_entry):
    """Test options flow with name change."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.config_flow._get_wifi_interfaces",
        return_value=["wlan0"],
    ):
        result = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )

    with (
        patch(
            "custom_components.wifi_ssid_monitor.config_flow._get_wifi_interfaces",
            return_value=["wlan0"],
        ),
        patch(
            "custom_components.wifi_ssid_monitor.config_flow._validate_input",
            return_value=None,
        ),
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                "name": "New Name",
                CONF_INTERFACE: "wlan0",
                CONF_KNOWN_SSIDS: "NewNet1",
                CONF_DENYLIST_SSIDS: "",
                CONF_LAST_SEEN_TTL_DAYS: DEFAULT_LAST_SEEN_TTL_DAYS,
            },
        )

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert mock_config_entry.title == "New Name"


@pytest.mark.asyncio
async def test_reconfigure_flow_current_missing_from_api(
    hass: HomeAssistant, mock_config_entry
):
    """Test reconfigure flow when current interface not in API list."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.config_flow._get_wifi_interfaces",
        return_value=["wlan1"],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_RECONFIGURE,
                "entry_id": mock_config_entry.entry_id,
            },
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    schema = result["data_schema"].schema
    interface_key = next(k for k in schema if k == "wifi_interface")
    assert "wlan0" in schema[interface_key].container


@pytest.mark.asyncio
async def test_reconfigure_exposes_full_settings(
    hass: HomeAssistant, mock_config_entry
):
    """Reconfigure now shows the full settings set, not just the setup essentials."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.config_flow._get_wifi_interfaces",
        return_value=["wlan0"],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_RECONFIGURE,
                "entry_id": mock_config_entry.entry_id,
            },
        )

    assert result["step_id"] == "reconfigure"
    keys = {str(k) for k in result["data_schema"].schema}
    for field in (
        CONF_INTERFACE,
        CONF_KNOWN_SSIDS,
        CONF_DENYLIST_SSIDS,
        CONF_LAST_SEEN_TTL_DAYS,
    ):
        assert field in keys


@pytest.mark.asyncio
async def test_reconfigure_and_options_schemas_match(
    hass: HomeAssistant, mock_config_entry
):
    """Both edit paths must render the same field set from the shared schema builder."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.config_flow._get_wifi_interfaces",
        return_value=["wlan0"],
    ):
        reconfigure = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_RECONFIGURE,
                "entry_id": mock_config_entry.entry_id,
            },
        )
        options = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )

    reconfigure_keys = {str(k) for k in reconfigure["data_schema"].schema}
    options_keys = {str(k) for k in options["data_schema"].schema}
    assert reconfigure_keys == options_keys


@pytest.mark.asyncio
async def test_reconfigure_persists_extra_settings(
    hass: HomeAssistant, mock_config_entry
):
    """Reconfigure now writes the full settings set, not only name/interface/known."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.config_flow._get_wifi_interfaces",
        return_value=["wlan0"],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_RECONFIGURE,
                "entry_id": mock_config_entry.entry_id,
            },
        )

    with (
        patch(
            "custom_components.wifi_ssid_monitor.config_flow._get_wifi_interfaces",
            return_value=["wlan0"],
        ),
        patch(
            "custom_components.wifi_ssid_monitor.config_flow._validate_input",
            return_value=None,
        ),
        patch(
            "custom_components.wifi_ssid_monitor.async_setup_entry", return_value=True
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                "name": "WiFi SSID Monitor",
                CONF_INTERFACE: "wlan0",
                CONF_KNOWN_SSIDS: "MyNetwork1,MyNetwork2",
                CONF_DENYLIST_SSIDS: "DenyNet",
                CONF_LAST_SEEN_TTL_DAYS: 30,
            },
        )
        await hass.async_block_till_done()

    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.options[CONF_DENYLIST_SSIDS] == "DenyNet"
    assert mock_config_entry.options[CONF_LAST_SEEN_TTL_DAYS] == 30
