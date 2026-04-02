"""Binary sensor platform for WiFi SSID Monitor."""

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

NEW_NETWORK_DESCRIPTION = BinarySensorEntityDescription(
    key="new_network",
    translation_key="new_network",
    icon="mdi:wifi-alert",
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the binary sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [WifiScanBinarySensor(coordinator, entry, NEW_NETWORK_DESCRIPTION)]
    )


class WifiScanBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Implementation of WiFi SSID Monitor binary sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, description):
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"

    @property
    def is_on(self) -> bool:
        """Return true if unknown networks are detected."""
        if not self.coordinator.data:
            return False
        return self.coordinator.data.get("unknown_count", 0) > 0

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.title,
            "manufacturer": "PlayFaster",
        }
