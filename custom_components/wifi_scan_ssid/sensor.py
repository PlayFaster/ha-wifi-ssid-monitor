import logging
from typing import Final

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


SENSOR_TYPES: Final[tuple[SensorEntityDescription, ...]] = (
    SensorEntityDescription(
        key="count",
        translation_key="total_count",
        icon="mdi:wifi",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="unknown_count",
        translation_key="unknown_count",
        icon="mdi:wifi-off",
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        WifiScanSensor(coordinator, entry, description) for description in SENSOR_TYPES
    ]
    async_add_entities(entities)


class WifiScanSensor(CoordinatorEntity, SensorEntity):
    """Implementation of Wifi Scan sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, description):
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
        return self.coordinator.data.get(self.entity_description.key)

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
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.title,
            "manufacturer": "PlayFaster",
        }
