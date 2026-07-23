"""Sensor platform for WiFi SSID Monitor."""

from __future__ import annotations

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
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import NETWORK_ATTR_MAX, NO_NETWORKS_SENTINEL
from .coordinator import WifiScanCoordinator
from .entity import WifiScanEntity

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class WifiSensorEntityDescription(SensorEntityDescription):
    """Describes WiFi sensor entity."""

    value_fn: Callable[[Any], Any]
    min_limit: float | None = None
    max_limit: float | None = None
    about: str | None = None


SENSOR_TYPES: Final[tuple[WifiSensorEntityDescription, ...]] = (
    WifiSensorEntityDescription(
        key="count",
        translation_key="total_count",
        state_class=SensorStateClass.MEASUREMENT,
        min_limit=0,
        max_limit=256,
        value_fn=lambda data: data.get("count"),
        about=(
            "Every network in range after your band and hidden-network filters. "
            "Unknown SSID Count is the subset not matching your known list."
        ),
    ),
    WifiSensorEntityDescription(
        key="unknown_count",
        translation_key="unknown_count",
        state_class=SensorStateClass.MEASUREMENT,
        min_limit=0,
        max_limit=256,
        value_fn=lambda data: data.get("unknown_count"),
        about=(
            "Networks in range that do not match your Known SSIDs list, plus any "
            "on the denylist. The per-network detail is on Strongest Unknown SSID."
        ),
    ),
    WifiSensorEntityDescription(
        key="new_24h",
        translation_key="new_24h",
        state_class=SensorStateClass.MEASUREMENT,
        min_limit=0,
        max_limit=4096,
        value_fn=lambda data: data.get("new_24h"),
        about=(
            "Networks first seen by this integration in the last 24 hours — not "
            "by your hardware. Resets if you clear the history."
        ),
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
        about=(
            "The closest unknown network by signal. Carries the per-network "
            "detail attributes. Reads 'None Detected' when nothing is in range."
        ),
    ),
    WifiSensorEntityDescription(
        key="strongest_unknown_signal",
        translation_key="strongest_unknown_signal",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        min_limit=0,
        max_limit=100,
        value_fn=lambda data: data.get("strongest_unknown_signal"),
        about=(
            "Signal quality of the closest unknown network, 0-100%. Higher is "
            "closer. Replaces the old dBm 'RSSI' sensor."
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: WifiScanCoordinator = entry.runtime_data
    async_add_entities(
        WifiScanSensor(coordinator, entry, description) for description in SENSOR_TYPES
    )


class WifiScanSensor(WifiScanEntity, SensorEntity):
    """Implementation of WiFi SSID Monitor sensors."""

    entity_description: WifiSensorEntityDescription

    # These are lists and maps that change on every scan. The sensor states are
    # still recorded and keep full history; only the attributes are dropped,
    # which keeps the recorder lean and the state well clear of HA's 16 KB
    # per-state limit in a dense WiFi environment.
    _unrecorded_attributes = WifiScanEntity._unrecorded_attributes | frozenset(
        {
            "networks",
            "networks_truncated",
            "ssids",
            "signal_strengths",
            "bands",
            "channels",
            "bssids",
            "last_seen",
            "first_seen",
            "visit_counts",
        }
    )

    def __init__(
        self,
        coordinator: WifiScanCoordinator,
        entry: ConfigEntry,
        description: WifiSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"

    @property
    def native_value(self) -> Any | None:
        """Return the value of the sensor."""
        description = self.entity_description
        key = description.key

        if key == "last_updated":
            return self.coordinator.last_update_success_time

        if not self.coordinator.data:
            return None

        try:
            value = description.value_fn(self.coordinator.data)
        except (KeyError, AttributeError):
            return None

        if value is None:
            # "Nothing in range" is a meaningful, reassuring answer for the SSID
            # sensor, and a bare `unknown` there reads as a broken sensor. The
            # numeric partner deliberately stays `unknown` — inventing a zero
            # would imply a measurement that was never taken.
            if key == "strongest_unknown_ssid":
                return NO_NETWORKS_SENTINEL
            return None

        if isinstance(value, int | float):
            if description.min_limit is not None and value < description.min_limit:
                return None
            if description.max_limit is not None and value > description.max_limit:
                return None

        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the per-network detail, on the sensors that warrant it."""
        data = self.coordinator.data
        if not data or not isinstance(data, dict):
            return self._with_about(None)

        key = self.entity_description.key

        if key == "strongest_unknown_ssid":
            return self._with_about(self._network_detail(data))

        if key == "unknown_count":
            return self._with_about({"ssids": list(data.get("unknown_ssids") or [])})

        if key == "count":
            return self._with_about({"ssids": list(data.get("ssids") or [])})

        return self._with_about(None)

    def _network_detail(self, data: dict[str, Any]) -> dict[str, Any]:
        """Build the unknown-network detail block.

        Capped at the strongest few. The full list is available through the
        get_networks action, which is the right tool for a long list — an
        attribute is not.
        """
        networks: dict[str, Any] = data.get("networks", {})
        unknown: list[str] = list(data.get("unknown_ssids") or [])
        last_seen: dict[str, Any] = data.get("last_seen", {})
        first_seen: dict[str, Any] = data.get("first_seen", {})
        visit_counts: dict[str, Any] = data.get("visit_counts", {})

        ranked = sorted(
            (label for label in unknown if label in networks),
            key=lambda label: (
                networks[label].get("signal") is None,
                -(networks[label].get("signal") or 0),
            ),
        )
        capped = ranked[:NETWORK_ATTR_MAX]

        detail: list[dict[str, Any]] = []
        for label in capped:
            net = networks[label]
            history_id = net.get("key")
            detail.append(
                {
                    "ssid": label,
                    "bssid": net.get("bssid"),
                    "signal": net.get("signal"),
                    "channel": net.get("channel"),
                    "band": net.get("band"),
                    "hidden": net.get("hidden"),
                    "ssid_anomaly": net.get("ssid_anomaly"),
                    "mode": net.get("mode"),
                    "first_seen": _iso(first_seen.get(history_id)),
                    "last_seen": _iso(last_seen.get(history_id)),
                    "visit_count": visit_counts.get(history_id),
                }
            )

        attrs: dict[str, Any] = {"networks": detail}
        if len(ranked) > len(capped):
            attrs["networks_truncated"] = True
        return attrs


def _iso(value: Any) -> str | None:
    """Render a stored datetime as ISO text, tolerating a missing value."""
    return value.isoformat() if hasattr(value, "isoformat") else None
