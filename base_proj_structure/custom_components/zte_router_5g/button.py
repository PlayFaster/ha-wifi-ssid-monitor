import logging
from dataclasses import dataclass

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.const import CONF_HOST

from .const import DOMAIN
from .coordinator import ZTERouterDataUpdateCoordinator
from .helpers import get_router_model

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class ZTEButtonEntityDescription(ButtonEntityDescription):
    """Describes ZTE button entity."""

    group: str = "router"


# Define metadata for the Reboot button
REBOOT_DESCRIPTION = ZTEButtonEntityDescription(
    key="reboot",
    translation_key="reboot",
    icon="mdi:restart",
    device_class=ButtonDeviceClass.RESTART,
    group="router",
)

# Define metadata for the Delete SMS button
DELETE_SMS_DESCRIPTION = ZTEButtonEntityDescription(
    key="delete_all",
    translation_key="delete_all",
    icon="mdi:email-remove",
    group="sms",
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the button platform."""
    coordinator: ZTERouterDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    api = coordinator.api

    # Create the button entities using their respective descriptions
    async_add_entities(
        [
            ZTERebootButton(api, coordinator, entry, REBOOT_DESCRIPTION),
            ZTEDeleteAllSMSButton(api, coordinator, entry, DELETE_SMS_DESCRIPTION),
        ],
        True,
    )


class ZTERebootButton(ButtonEntity):
    """Button to reboot the ZTE router."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    entity_description: ZTEButtonEntityDescription

    def __init__(
        self,
        api,
        coordinator: ZTERouterDataUpdateCoordinator,
        entry,
        description: ZTEButtonEntityDescription,
    ):
        """Initialize the reboot button."""
        self.entity_description = description
        self._api = api
        self._coordinator = coordinator
        self._entry = entry

        # Registry identification based on the description key
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"

    @property
    def device_info(self):
        """Return device information linking to the main router device."""
        host = self._entry.options[CONF_HOST]
        return {
            "identifiers": {(DOMAIN, host)},
            "name": self._entry.title,
            "manufacturer": "ZTE",
            "configuration_url": f"http://{host}",
            "model": get_router_model(self._coordinator.data),
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            # Direct async call
            await self._api.reboot()
        except Exception as err:
            _LOGGER.error("%s: Reboot failed: %s", self._entry.title, err)


class ZTEDeleteAllSMSButton(ButtonEntity):
    """Button to delete all SMS messages."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    entity_description: ZTEButtonEntityDescription

    def __init__(
        self,
        api,
        coordinator: ZTERouterDataUpdateCoordinator,
        entry,
        description: ZTEButtonEntityDescription,
    ):
        """Initialize the delete all SMS button."""
        self.entity_description = description
        self._api = api
        self._coordinator = coordinator
        self._entry = entry

        self._attr_unique_id = f"{entry.unique_id}_delete_all"

    @property
    def device_info(self):
        """Return device information. Anchors to the SMS sub-device."""
        host = self._entry.options[CONF_HOST]
        return {
            "identifiers": {(DOMAIN, f"{host}_sms")},
            "name": f"{self._entry.title} SMS",
            "manufacturer": "ZTE",
            "via_device": (DOMAIN, host),
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            # Direct async call
            await self._api.delete_all()
            # Request refresh so SMS sensors update immediately
            await self._coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("%s: Delete SMS failed: %s", self._entry.title, err)
