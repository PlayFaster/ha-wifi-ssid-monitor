import logging

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.const import CONF_HOST
from homeassistant.helpers.entity import EntityCategory

from .const import CONF_STOP_POLLING, DOMAIN
from .coordinator import ZTERouterDataUpdateCoordinator
from .helpers import get_router_model

_LOGGER = logging.getLogger(__name__)

# Define the entity description for static metadata
PAUSE_POLLING_DESCRIPTION = SwitchEntityDescription(
    key="pause_polling",
    translation_key="pause_polling",
    icon="mdi:pause-circle-outline",
    entity_category=EntityCategory.CONFIG,
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the switch platform."""
    coordinator: ZTERouterDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Read initial state from entry options (survives restarts)
    initial_state = entry.options.get(CONF_STOP_POLLING, False)

    async_add_entities(
        [
            ZTEPausePollingSwitch(
                coordinator, entry, PAUSE_POLLING_DESCRIPTION, initial_state
            )
        ]
    )


class ZTEPausePollingSwitch(SwitchEntity):
    """Switch to pause/resume polling with persistence."""

    _attr_has_entity_name = True
    _attr_should_poll = False  # State is managed by user interaction and memory
    entity_description: SwitchEntityDescription

    def __init__(
        self,
        coordinator: ZTERouterDataUpdateCoordinator,
        entry,
        description: SwitchEntityDescription,
        initial_state,
    ):
        """Initialize the switch."""
        self._coordinator = coordinator
        self._entry = entry
        self.entity_description = description

        # Registry identification
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"
        self._attr_is_on = initial_state

    @property
    def is_on(self) -> bool:
        """Return true if polling is paused."""
        return self._entry.options.get(CONF_STOP_POLLING, False)

    async def async_turn_on(self, **kwargs):
        """Pause polling."""
        _LOGGER.debug("Pausing ZTE Router polling")
        await self._async_set_state(True)

    async def async_turn_off(self, **kwargs):
        """Resume polling."""
        _LOGGER.debug("Resuming ZTE Router polling")
        await self._async_set_state(False)

    async def _async_set_state(self, state: bool):
        """Update memory, state, and persist to options."""
        # 1. Persist to ConfigEntry Options (saves to .storage)
        # This ensures the pause state survives a Home Assistant restart.
        new_options = dict(self._entry.options)
        new_options[CONF_STOP_POLLING] = state
        self.hass.config_entries.async_update_entry(self._entry, options=new_options)

        # Signal to HA that the state has changed
        self.async_write_ha_state()

        # 2. If we just resumed, trigger an immediate coordinator refresh
        if not state:
            await self._coordinator.async_request_refresh()

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
