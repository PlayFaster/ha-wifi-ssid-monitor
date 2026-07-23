"""Button platform for WiFi SSID Monitor."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import WifiScanCoordinator
from .entity import WifiScanEntity

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


class WifiScanButton(WifiScanEntity, ButtonEntity):
    """Button to trigger an immediate on-demand WiFi scan."""

    _attr_about = (
        "Runs a scan immediately, including while Pause Polling is on — an "
        "explicit request is always honoured."
    )

    def __init__(
        self,
        coordinator: WifiScanCoordinator,
        entry: ConfigEntry,
        description: ButtonEntityDescription,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"

    @property
    def available(self) -> bool:
        """Remain available while the coordinator is down.

        A button whose entire purpose is to retry must not disappear when the
        thing it retries has failed.
        """
        return True

    async def async_press(self) -> None:
        """Trigger an immediate WiFi scan.

        Uses the force path, not a bare refresh: a pause-aware coordinator
        short-circuits a plain request to cached data, which would silently
        swallow the press at exactly the moment the user wanted a fetch.
        """
        await self.coordinator.async_force_refresh()
        if not self.coordinator.last_update_success:
            raise HomeAssistantError(
                "WiFi scan failed — check Home Assistant Repairs for details",
                translation_domain=DOMAIN,
                translation_key="scan_failed",
            )
