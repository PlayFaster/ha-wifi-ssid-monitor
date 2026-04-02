"""Number platform for WiFi SSID Monitor."""

import asyncio
import logging

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.const import UnitOfTime
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SCAN_INTERVAL, DOMAIN
from .coordinator import WifiScanCoordinator

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL_DESCRIPTION = NumberEntityDescription(
    key="scan_interval",
    translation_key="scan_interval",
    icon="mdi:timer-cog-outline",
    native_min_value=1,
    native_max_value=180,
    native_step=1,
    native_unit_of_measurement=UnitOfTime.MINUTES,
    entity_category=EntityCategory.CONFIG,
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the number platform."""
    coordinator: WifiScanCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([WifiScanIntervalNumber(coordinator, SCAN_INTERVAL_DESCRIPTION)])


class WifiScanIntervalNumber(CoordinatorEntity, NumberEntity):
    """Number entity to control the scan interval in minutes."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: WifiScanCoordinator,
        description: NumberEntityDescription,
    ):
        """Initialize the number entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_{description.key}"
        self._refresh_task = None

    @property
    def native_value(self) -> float | None:
        """Return the state of the entity."""
        raw_val = self.coordinator.config_entry.options.get(CONF_SCAN_INTERVAL, 600)
        return max(1, raw_val // 60)

    async def async_set_native_value(self, value: float) -> None:
        """Update the scan interval."""
        if self._refresh_task:
            self._refresh_task.cancel()

        self._refresh_task = asyncio.create_task(self._async_debounced_apply(value))

    async def _async_debounced_apply(self, value: float) -> None:
        """Apply the new interval with a debounce."""
        try:
            await asyncio.sleep(2)
            val_minutes = int(value)
            val_seconds = val_minutes * 60

            _LOGGER.debug("Persisting new scan interval: %s minutes", val_minutes)

            # Persist to options. This triggers the update listener in __init__.py
            # which will update the coordinator interval and trigger a refresh.
            new_options = dict(self.coordinator.config_entry.options)
            new_options[CONF_SCAN_INTERVAL] = val_seconds
            self.hass.config_entries.async_update_entry(
                self.coordinator.config_entry, options=new_options
            )

        except asyncio.CancelledError:
            pass
        except Exception as err:
            _LOGGER.error("Failed to apply scan interval change: %s", err)

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.config_entry.entry_id)},
            "name": self.coordinator.config_entry.title,
            "manufacturer": "PlayFaster",
        }
