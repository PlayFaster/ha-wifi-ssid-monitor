"""Button platform for WiFi SSID Monitor."""

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_NAME, DOMAIN
from .coordinator import WifiScanCoordinator

PARALLEL_UPDATES = 0

SCAN_NOW_DESCRIPTION = ButtonEntityDescription(
    key="scan_now",
    translation_key="scan_now",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform."""
    coordinator: WifiScanCoordinator = entry.runtime_data
    async_add_entities([WifiScanButton(coordinator, entry, SCAN_NOW_DESCRIPTION)])


class WifiScanButton(ButtonEntity):
    """Button to trigger an immediate on-demand WiFi scan."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WifiScanCoordinator,
        entry: ConfigEntry,
        description: ButtonEntityDescription,
    ) -> None:
        """Initialize the button."""
        self._coordinator = coordinator
        self._entry = entry
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"

    async def async_press(self) -> None:
        """Trigger an immediate WiFi scan."""
        await self._coordinator.async_refresh()
        if not self._coordinator.last_update_success:
            raise HomeAssistantError(
                "WiFi scan failed — check Home Assistant Repairs for details"
            )

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return device information."""
        name = self._entry.options.get(CONF_NAME, self._entry.title)
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": name,
            "manufacturer": "PlayFaster",
            "model": (
                f"v{self._coordinator.version} ({self._coordinator.api.interface})"
            ),
        }
