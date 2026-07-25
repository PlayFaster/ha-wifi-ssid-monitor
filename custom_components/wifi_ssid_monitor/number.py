"""Number platform for WiFi SSID Monitor.

Both numbers are option-backed and read ``entry.options`` in their property
rather than caching a value at construction — a cached copy goes stale the
moment the option is changed from anywhere else.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Final

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_PROXIMITY_SIGNAL_THRESHOLD,
    CONF_SCAN_INTERVAL,
    DEFAULT_PROXIMITY_SIGNAL_THRESHOLD,
    DEFAULT_SCAN_INTERVAL,
)
from .coordinator import WifiScanCoordinator
from .entity import WifiScanEntity

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0

_DEBOUNCE_SECONDS = 2


@dataclass(frozen=True, kw_only=True)
class WifiNumberEntityDescription(NumberEntityDescription):
    """Describes an option-backed number."""

    option_key: str
    option_default: float
    # Options are stored in seconds but shown in minutes; the scale keeps the
    # stored unit and the displayed unit from drifting apart.
    scale: int = 1
    about: str | None = None


NUMBER_TYPES: Final[tuple[WifiNumberEntityDescription, ...]] = (
    WifiNumberEntityDescription(
        key="scan_interval",
        translation_key="scan_interval",
        native_min_value=1,
        native_max_value=180,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        option_key=CONF_SCAN_INTERVAL,
        option_default=DEFAULT_SCAN_INTERVAL,
        scale=60,
        about=(
            "How often a scheduled scan runs. This is the only place the scan "
            "interval is set — it is no longer in the Configure dialog."
        ),
    ),
    WifiNumberEntityDescription(
        key="proximity_signal_threshold",
        translation_key="proximity_signal_threshold",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        option_key=CONF_PROXIMITY_SIGNAL_THRESHOLD,
        option_default=DEFAULT_PROXIMITY_SIGNAL_THRESHOLD,
        about=(
            "Signal quality at which the Proximity Alert fires, 0-100%. Higher "
            "means the network must be closer. Raise it if the alert is noisy."
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the number platform."""
    coordinator: WifiScanCoordinator = entry.runtime_data
    async_add_entities(
        WifiOptionNumber(coordinator, entry, description)
        for description in NUMBER_TYPES
    )


class WifiOptionNumber(WifiScanEntity, NumberEntity):
    """A number whose value is a config-entry option."""

    entity_description: WifiNumberEntityDescription

    def __init__(
        self,
        coordinator: WifiScanCoordinator,
        entry: ConfigEntry,
        description: WifiNumberEntityDescription,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"
        self._pending: asyncio.Task[None] | None = None
        self._optimistic: float | None = None

    @property
    def available(self) -> bool:
        """Remain available while the coordinator is down — this is a control."""
        return True

    @property
    def native_value(self) -> float:
        """Return the stored option, converted to the displayed unit."""
        if self._optimistic is not None:
            return self._optimistic
        description = self.entity_description
        stored = self._entry.options.get(
            description.option_key, description.option_default
        )
        if description.scale == 1:
            return float(stored)
        return float(max(1, round(stored / description.scale)))

    async def async_set_native_value(self, value: float) -> None:
        """Update the option behind this number, debounced."""
        # Show the new value immediately; the debounce only delays the write,
        # and a slider that lags the user's finger feels broken.
        self._optimistic = value
        self.async_write_ha_state()

        if self._pending:
            self._pending.cancel()
        self._pending = self.hass.async_create_task(self._async_debounced_apply(value))

    async def async_will_remove_from_hass(self) -> None:
        """Cancel any pending debounced update on removal."""
        if self._pending:
            self._pending.cancel()

    async def _async_debounced_apply(self, value: float) -> None:
        """Persist the option after the debounce window."""
        description = self.entity_description
        try:
            await asyncio.sleep(_DEBOUNCE_SECONDS)
            stored = int(value) * description.scale

            new_options = {**self._entry.options, description.option_key: stored}
            self.hass.config_entries.async_update_entry(
                self._entry, options=new_options
            )
            self._optimistic = None
            self.async_write_ha_state()

        except asyncio.CancelledError:
            _LOGGER.debug("%s change superseded (debounced)", description.key)
        except Exception:
            _LOGGER.exception("Failed to apply %s change", description.key)
            self._optimistic = None
            self.async_write_ha_state()
