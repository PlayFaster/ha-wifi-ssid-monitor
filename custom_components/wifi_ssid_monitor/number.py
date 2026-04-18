"""Number platform for WiFi SSID Monitor."""

import asyncio
import logging

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.const import UnitOfTime
from homeassistant.helpers.entity import EntityCategory

from .const import CONF_NAME, CONF_SCAN_INTERVAL, DOMAIN
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

    # Read initial value from entry options (in minutes)
    # Default to 10 if not set (600 seconds).
    # Use round() to handle any non-minute-aligned intervals gracefully
    raw_val = entry.options.get(CONF_SCAN_INTERVAL, 600)
    initial_value = max(1, round(raw_val / 60))

    async_add_entities(
        [
            WifiScanIntervalNumber(
                coordinator, entry, SCAN_INTERVAL_DESCRIPTION, initial_value
            )
        ]
    )


class WifiScanIntervalNumber(NumberEntity):
    """Number entity to control the scan interval in minutes."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: WifiScanCoordinator,
        entry,
        description: NumberEntityDescription,
        initial_value,
    ):
        """Initialize the number entity."""
        self._coordinator = coordinator
        self._entry = entry
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"
        self._attr_native_value = initial_value
        self._refresh_task = None

    async def async_set_native_value(self, value: float) -> None:
        """Update the scan interval."""
        self._attr_native_value = value
        self.async_write_ha_state()

        if self._refresh_task:
            self._refresh_task.cancel()

        self._refresh_task = asyncio.create_task(self._async_debounced_apply(value))

    async def _async_debounced_apply(self, value: float) -> None:
        """Apply the new interval with a debounce."""
        try:
            await asyncio.sleep(2)
            val_minutes = int(value)
            val_seconds = val_minutes * 60

            _LOGGER.debug("Applying new scan interval: %s minutes", val_minutes)

            # Persist to options. This will trigger the update listener in __init__.py
            new_options = dict(self._entry.options)
            new_options[CONF_SCAN_INTERVAL] = val_seconds
            self.hass.config_entries.async_update_entry(
                self._entry, options=new_options
            )

        except asyncio.CancelledError:
            _LOGGER.debug("Scan interval change cancelled (debounced)")
        except Exception as err:
            _LOGGER.error("Failed to apply scan interval change: %s", err)
            # Revert the UI value on failure (use round to match initial value logic)
            self._attr_native_value = max(
                1, round(self._entry.options.get(CONF_SCAN_INTERVAL, 600) / 60)
            )
            self.async_write_ha_state()

    @property
    def device_info(self):
        """Return device information."""
        name = self._entry.options.get(CONF_NAME, self._entry.title)
        model = f"v{self._coordinator.version} ({self._coordinator.api.interface})"
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": name,
            "manufacturer": "PlayFaster",
            "model": model,
        }
