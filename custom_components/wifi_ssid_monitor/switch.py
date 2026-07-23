"""Switch platform for WiFi SSID Monitor.

Every switch here is option-backed: ``entry.options`` is the single source of
truth, read fresh in the property, so a change made anywhere — this switch, a
service call, the options flow — is reflected everywhere without a reload.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_INCLUDE_HIDDEN,
    CONF_SHOW_5GHZ,
    CONF_SHOW_6GHZ,
    CONF_SHOW_24GHZ,
    CONF_STOP_POLLING,
    DEFAULT_INCLUDE_HIDDEN,
    DEFAULT_SHOW_BAND,
    DEFAULT_STOP_POLLING,
)
from .coordinator import WifiScanCoordinator
from .entity import WifiScanEntity

PARALLEL_UPDATES = 0

_BANDS_OFF_NOTE = (
    "Turning every band switch off shows no networks at all, not all of them."
)


@dataclass(frozen=True, kw_only=True)
class WifiSwitchEntityDescription(SwitchEntityDescription):
    """Describes an option-backed switch."""

    option_key: str
    option_default: bool
    about: str | None = None


SWITCH_TYPES: Final[tuple[WifiSwitchEntityDescription, ...]] = (
    WifiSwitchEntityDescription(
        key="stop_polling",
        translation_key="stop_polling",
        entity_category=EntityCategory.CONFIG,
        option_key=CONF_STOP_POLLING,
        option_default=DEFAULT_STOP_POLLING,
        about=(
            "Pauses scheduled scans. Explicit actions — Scan Now, a control "
            "change, the scan_now service — still fetch. This is separate from "
            "Home Assistant's own 'Enable polling for changes' system option, "
            "which stops the schedule being armed at all."
        ),
    ),
    WifiSwitchEntityDescription(
        key="include_hidden",
        translation_key="include_hidden",
        entity_category=EntityCategory.CONFIG,
        option_key=CONF_INCLUDE_HIDDEN,
        option_default=DEFAULT_INCLUDE_HIDDEN,
        about=(
            "Include networks that do not broadcast a name. Each is listed "
            "separately as Hidden-<last 4 of BSSID> where the BSSID is known."
        ),
    ),
    WifiSwitchEntityDescription(
        key="show_24ghz",
        translation_key="show_24ghz",
        entity_category=EntityCategory.CONFIG,
        option_key=CONF_SHOW_24GHZ,
        option_default=DEFAULT_SHOW_BAND,
        about=f"Include 2.4 GHz networks in all counts and lists. {_BANDS_OFF_NOTE}",
    ),
    WifiSwitchEntityDescription(
        key="show_5ghz",
        translation_key="show_5ghz",
        entity_category=EntityCategory.CONFIG,
        option_key=CONF_SHOW_5GHZ,
        option_default=DEFAULT_SHOW_BAND,
        about=f"Include 5 GHz networks in all counts and lists. {_BANDS_OFF_NOTE}",
    ),
    WifiSwitchEntityDescription(
        key="show_6ghz",
        translation_key="show_6ghz",
        entity_category=EntityCategory.CONFIG,
        option_key=CONF_SHOW_6GHZ,
        option_default=DEFAULT_SHOW_BAND,
        about=(
            "Include 6 GHz (WiFi 6E/7) networks in all counts and lists. "
            f"{_BANDS_OFF_NOTE}"
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    coordinator: WifiScanCoordinator = entry.runtime_data
    async_add_entities(
        WifiOptionSwitch(coordinator, entry, description)
        for description in SWITCH_TYPES
    )


class WifiOptionSwitch(WifiScanEntity, SwitchEntity):
    """A switch whose state is a config-entry option."""

    entity_description: WifiSwitchEntityDescription

    def __init__(
        self,
        coordinator: WifiScanCoordinator,
        entry: ConfigEntry,
        description: WifiSwitchEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"

    @property
    def available(self) -> bool:
        """Remain available while the coordinator is down.

        These are configuration controls, not readings. A user whose Supervisor
        is unreachable should still be able to pause polling or change a filter.
        """
        return True

    @property
    def is_on(self) -> bool:
        """Return the stored option value."""
        return bool(
            self._entry.options.get(
                self.entity_description.option_key,
                self.entity_description.option_default,
            )
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the option."""
        await self._set_state(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the option."""
        await self._set_state(False)

    async def _set_state(self, state: bool) -> None:
        """Persist the option and re-parse with the new setting applied."""
        new_options = {
            **self._entry.options,
            self.entity_description.option_key: state,
        }
        self.hass.config_entries.async_update_entry(self._entry, options=new_options)
        self.async_write_ha_state()
