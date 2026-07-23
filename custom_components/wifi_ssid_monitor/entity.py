"""Shared entity base classes for WiFi SSID Monitor.

Every platform delegates ``device_info`` here. It was previously copy-pasted
into five classes, which is five places to forget when the device identity
changes.
"""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_NAME, DOMAIN
from .coordinator import WifiScanCoordinator


def build_device_info(
    coordinator: WifiScanCoordinator, entry: ConfigEntry
) -> DeviceInfo:
    """Build the device info for this entry's single device.

    The identifier is the config entry id. Neither rung of the dev_standards
    section 3 identity ladder is available here: the Supervisor exposes no MAC
    for the scanning host, and there is no IP — this integration monitors the
    Home Assistant machine itself. The entry id is not a hardware identity and
    does not survive a delete/re-add, but there is nothing stronger to key on,
    and changing it now would orphan every existing user's entities.
    """
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.options.get(CONF_NAME, entry.title),
        manufacturer="PlayFaster",
        model=f"v{coordinator.version} ({coordinator.api.interface})",
    )


class WifiAboutEntity:
    """Mixin exposing a static, human-facing ``about`` note as an attribute.

    Set the text via ``_attr_about`` (class-level) or an ``about`` field on the
    entity description. The note shows in Developer Tools and the More Info
    dialog but is listed in ``_unrecorded_attributes``, so the recorder never
    writes it to history — it costs nothing however often the state changes.

    List this mixin FIRST in an entity's bases so its ``extra_state_attributes``
    wins over the platform default. Entities that define their own
    ``extra_state_attributes`` should route the result through ``_with_about``.
    """

    _unrecorded_attributes = frozenset({"about"})
    _attr_about: str | None = None

    @property
    def _about_text(self) -> str | None:
        """Resolve the note from ``_attr_about`` or the entity description."""
        if self._attr_about is not None:
            return self._attr_about
        description = getattr(self, "entity_description", None)
        return getattr(description, "about", None) if description is not None else None

    def _with_about(self, attrs: dict[str, Any] | None) -> dict[str, Any]:
        """Merge the about note into an attribute dict."""
        merged = dict(attrs or {})
        about = self._about_text
        if about:
            merged["about"] = about
        return merged

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return just the about note, for entities with no other attributes."""
        return self._with_about(None)


class WifiScanEntity(WifiAboutEntity, CoordinatorEntity[WifiScanCoordinator]):
    """Base for every coordinator-backed entity in this integration."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: WifiScanCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return build_device_info(self.coordinator, self._entry)
