"""Binary sensor platform for WiFi SSID Monitor."""

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_NAME, DOMAIN
from .coordinator import WifiScanCoordinator

NEW_NETWORK_DESCRIPTION = BinarySensorEntityDescription(
    key="new_network",
    translation_key="new_network",
    icon="mdi:wifi-alert",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor platform."""
    coordinator: WifiScanCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [WifiScanBinarySensor(coordinator, entry, NEW_NETWORK_DESCRIPTION)]
    )


class WifiScanBinarySensor(CoordinatorEntity[WifiScanCoordinator], BinarySensorEntity):
    """Implementation of WiFi SSID Monitor binary sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WifiScanCoordinator,
        entry: ConfigEntry,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"

    @property
    def is_on(self) -> bool:
        """Return true if any unknown networks are currently detected."""
        if not self.coordinator.data:
            return False
        return self.coordinator.data.get("unknown_count", 0) > 0

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
