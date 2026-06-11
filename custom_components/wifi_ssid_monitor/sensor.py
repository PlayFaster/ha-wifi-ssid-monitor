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
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_NAME, DOMAIN
from .coordinator import WifiScanCoordinator

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


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
        state_class=SensorStateClass.MEASUREMENT,
        min_limit=0,
        max_limit=256,
        value_fn=lambda data: data.get("count"),
    ),
    WifiSensorEntityDescription(
        key="unknown_count",
        translation_key="unknown_count",
        state_class=SensorStateClass.MEASUREMENT,
        min_limit=0,
        max_limit=256,
        value_fn=lambda data: data.get("unknown_count"),
    ),
    WifiSensorEntityDescription(
        key="interface",
        translation_key="interface",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("interface"),
    ),
    WifiSensorEntityDescription(
        key="last_updated",
        translation_key="last_updated",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: None,  # Handled in native_value
    ),
    WifiSensorEntityDescription(
        key="strongest_unknown_ssid",
        translation_key="strongest_unknown_ssid",
        value_fn=lambda data: data.get("strongest_unknown_ssid"),
    ),
    WifiSensorEntityDescription(
        key="strongest_unknown_rssi",
        translation_key="strongest_unknown_rssi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement="dBm",
        state_class=SensorStateClass.MEASUREMENT,
        min_limit=-100,
        max_limit=0,
        value_fn=lambda data: data.get("strongest_unknown_rssi"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: WifiScanCoordinator = entry.runtime_data
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
    def native_value(self) -> Any | None:
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
        except (KeyError, AttributeError):
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
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return SSIDs with signal and band data as attributes."""
        if not self.coordinator.data or not isinstance(self.coordinator.data, dict):
            return {}

        networks: dict[str, Any] = self.coordinator.data.get("networks", {})

        if self.entity_description.key == "count":
            ssids: list[str] = self.coordinator.data.get("ssids") or []
            attrs: dict[str, Any] = {"ssids": ssids}
            signal_data = {
                ssid: networks[ssid]["rssi"]
                for ssid in ssids
                if ssid in networks and networks[ssid].get("rssi") is not None
            }
            if signal_data:
                attrs["signal_strengths"] = signal_data
            band_data = {
                ssid: networks[ssid]["band"]
                for ssid in ssids
                if ssid in networks and networks[ssid].get("band")
            }
            if band_data:
                attrs["bands"] = band_data
            return attrs

        if self.entity_description.key == "unknown_count":
            unknown_ssids: list[str] = self.coordinator.data.get("unknown_ssids") or []
            last_seen: dict[str, Any] = self.coordinator.data.get("last_seen", {})
            first_seen: dict[str, Any] = self.coordinator.data.get("first_seen", {})
            visit_counts: dict[str, Any] = self.coordinator.data.get("visit_counts", {})
            u_attrs: dict[str, Any] = {"ssids": unknown_ssids}
            u_signal = {
                ssid: networks[ssid]["rssi"]
                for ssid in unknown_ssids
                if ssid in networks and networks[ssid].get("rssi") is not None
            }
            if u_signal:
                u_attrs["signal_strengths"] = u_signal
            u_bands = {
                ssid: networks[ssid]["band"]
                for ssid in unknown_ssids
                if ssid in networks and networks[ssid].get("band")
            }
            if u_bands:
                u_attrs["bands"] = u_bands
            u_last_seen = {
                ssid: last_seen[ssid].isoformat()
                for ssid in unknown_ssids
                if ssid in last_seen
            }
            if u_last_seen:
                u_attrs["last_seen"] = u_last_seen
            u_first_seen = {
                ssid: first_seen[ssid].isoformat()
                for ssid in unknown_ssids
                if ssid in first_seen
            }
            if u_first_seen:
                u_attrs["first_seen"] = u_first_seen
            u_visit_counts = {
                ssid: visit_counts[ssid]
                for ssid in unknown_ssids
                if ssid in visit_counts
            }
            if u_visit_counts:
                u_attrs["visit_counts"] = u_visit_counts
            return u_attrs

        return {}

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return device information."""
        name = self._entry.options.get(CONF_NAME, self._entry.title)
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": name,
            "manufacturer": "PlayFaster",
            "model": f"v{self.coordinator.version} ({self.coordinator.api.interface})",
        }
