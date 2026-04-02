import asyncio
import logging
from datetime import timedelta

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.const import CONF_HOST, UnitOfTime
from homeassistant.helpers.entity import EntityCategory

from .const import CONF_SCAN_INTERVAL, DOMAIN
from .coordinator import ZTERouterDataUpdateCoordinator
from .helpers import get_router_model

_LOGGER = logging.getLogger(__name__)

# Define the entity description for static metadata
POLLING_INTERVAL_DESCRIPTION = NumberEntityDescription(
    key="polling_interval",
    translation_key="polling_interval",
    native_min_value=30,
    native_max_value=3600,
    native_step=30,
    native_unit_of_measurement=UnitOfTime.SECONDS,
    entity_category=EntityCategory.CONFIG,
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the number platform."""
    coordinator: ZTERouterDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Read initial value from entry options (survives restarts)
    initial_value = entry.options.get(CONF_SCAN_INTERVAL, 180)

    async_add_entities(
        [
            ZTEPollingInterval(
                coordinator, entry, POLLING_INTERVAL_DESCRIPTION, initial_value
            )
        ]
    )


class ZTEPollingInterval(NumberEntity):
    """Number entity to control the polling interval with persistence."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    entity_description: NumberEntityDescription

    def __init__(
        self,
        coordinator: ZTERouterDataUpdateCoordinator,
        entry,
        description: NumberEntityDescription,
        initial_value,
    ):
        """Initialize the number entity."""
        self._coordinator = coordinator
        self._entry = entry
        self.entity_description = description

        # Registry identification
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"

        # Local state
        self._attr_native_value = initial_value
        self._refresh_task = None

    async def async_set_native_value(self, value: float) -> None:
        """Handle the UI slider change."""
        # Update local UI state immediately for responsiveness
        self._attr_native_value = value
        self.async_write_ha_state()

        # Cancel any pending update task to reset the debounce timer
        if self._refresh_task:
            self._refresh_task.cancel()

        # Start a new debounced task
        self._refresh_task = asyncio.create_task(self._async_debounced_apply(value))

    async def _async_debounced_apply(self, value: float) -> None:
        """Apply change and persist to ConfigEntry Options after a delay."""
        try:
            # Wait for 2 seconds of inactivity before committing
            await asyncio.sleep(2)
            val_int = int(value)

            _LOGGER.debug("Applying new polling interval: %s seconds", val_int)

            # 1. Update the coordinator's actual update interval
            self._coordinator.update_interval = timedelta(seconds=val_int)

            # 2. Persist to ConfigEntry Options (saves to .storage/core.config_entries)
            # This ensures the setting survives a Home Assistant restart.
            new_options = dict(self._entry.options)
            new_options[CONF_SCAN_INTERVAL] = val_int
            self.hass.config_entries.async_update_entry(
                self._entry, options=new_options
            )

            # 3. Trigger an immediate refresh using the new interval
            await self._coordinator.async_request_refresh()

        except asyncio.CancelledError:
            # Task was cancelled because the user moved the slider again
            pass
        except Exception as err:
            _LOGGER.error("Failed to apply polling interval change: %s", err)

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
