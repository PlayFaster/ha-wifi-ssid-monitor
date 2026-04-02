from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import CONF_HOST
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ZTERouterDataUpdateCoordinator
from .helpers import get_router_model

# Define the entity description for static metadata
BEST_CONN_DESCRIPTION = BinarySensorEntityDescription(
    key="best_connection",
    translation_key="best_connection",
    device_class=BinarySensorDeviceClass.CONNECTIVITY,
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the binary sensor platform."""
    coordinator: ZTERouterDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    # Pass the description object into the sensor
    async_add_entities(
        [ZTEBestConnectionSensor(coordinator, entry, BEST_CONN_DESCRIPTION)]
    )


class ZTEBestConnectionSensor(
    CoordinatorEntity[ZTERouterDataUpdateCoordinator], BinarySensorEntity
):
    """Binary sensor to check for optimal 5G/LTE CA connection."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    entity_description: BinarySensorEntityDescription

    def __init__(
        self,
        coordinator: ZTERouterDataUpdateCoordinator,
        entry,
        description: BinarySensorEntityDescription,
    ):
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry

        # Unique ID generated from description key for registry stability
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"

    @property
    def is_on(self) -> bool:
        """Return true if both 5G and LTE CA are active."""
        data = self.coordinator.data
        if not data:
            return False
        # Optimal connection logic based on raw data keys
        return (
            data.get("network_type") == "ENDC"
            and data.get("wan_lte_ca") == "ca_activated"
        )

    @property
    def icon(self) -> str:
        """Return icon based on connection status."""
        return "mdi:signal" if self.is_on else "mdi:signal-cellular-1"

    @property
    def device_info(self):
        """Return device information linking to the main router device."""
        host = self._entry.options[CONF_HOST]
        return {
            "identifiers": {(DOMAIN, host)},
            "name": self._entry.title,
            "manufacturer": "ZTE",
            "configuration_url": f"http://{host}",
            "model": get_router_model(self.coordinator.data),
        }
