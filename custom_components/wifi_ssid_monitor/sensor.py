"""Sensor platform for WiFi SSID Monitor."""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Final

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_NAME, DOMAIN
from .coordinator import WifiScanCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class WifiSensorEntityDescription(SensorEntityDescription):
    """Describes WiFi sensor entity."""

    value_fn: Callable[[Any], Any]
    min_limit: float | None = None
    max_limit: float | None = None


SENSOR_TYPES: Final[tuple[WifiSensorEntityDescription, ...]] = (
    WifiSensorEntityDescription(
        key="count",
        translation_key="total_count",
        icon="mdi:wifi",
        state_class=SensorStateClass.MEASUREMENT,
        min_limit=0,
        max_limit=256,
        value_fn=lambda data: data.get("count"),
    ),
    WifiSensorEntityDescription(
        key="unknown_count",
        translation_key="unknown_count",
        icon="mdi:wifi-off",
        state_class=SensorStateClass.MEASUREMENT,
        min_limit=0,
        max_limit=256,
        value_fn=lambda data: data.get("unknown_count"),
    ),
    WifiSensorEntityDescription(
        key="interface",
        translation_key="interface",
        icon="mdi:lan",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("interface"),
    ),
    WifiSensorEntityDescription(
        key="last_updated",
        translation_key="last_updated",
        icon="mdi:update",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: None,  # Handled in native_value
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: WifiScanCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        WifiScanSensor(coordinator, entry, description) for description in SENSOR_TYPES
    ]
    async_add_entities(entities)


class WifiScanSensor(CoordinatorEntity[WifiScanCoordinator], SensorEntity):
    """Implementation of WiFi SSID Monitor sensors."""

    _attr_has_entity_name = True
    entity_description: WifiSensorEntityDescription

    def __init__(
        self,
        coordinator: WifiScanCoordinator,
        entry: ConfigEntry,
        description: WifiSensorEntityDescription,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"

    @property
    def native_value(self):
        """Return the value of the sensor."""
        if not self.coordinator.data:
            return None

        description = self.entity_description
        key = description.key

        # Special case: Last Updated
        if key == "last_updated":
            return self.coordinator.last_update_success_time

        try:
            value = description.value_fn(self.coordinator.data)
        except KeyError, AttributeError:
            return None

        if value is None:
            return None

        # Apply Guard Bands (Standard 4)
        if isinstance(value, int | float):
            if description.min_limit is not None and value < description.min_limit:
                return None
            if description.max_limit is not None and value > description.max_limit:
                return None

        return value

    @property
    def extra_state_attributes(self):
        """Return SSIDs as attributes."""
        if not self.coordinator.data:
            return {}
        if self.entity_description.key == "count":
            return {"ssids": self.coordinator.data.get("ssids")}
        if self.entity_description.key == "unknown_count":
            return {"ssids": self.coordinator.data.get("unknown_ssids")}
        return {}

    @property
    def device_info(self):
        """Return device information."""
        name = self._entry.options.get(CONF_NAME, self._entry.title)
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": name,
            "manufacturer": "PlayFaster",
            "model": f"v{self.coordinator.version} ({self.coordinator.api.interface})",
        }
