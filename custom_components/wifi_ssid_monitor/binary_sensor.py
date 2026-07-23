"""Binary sensor platform for WiFi SSID Monitor."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_PROXIMITY_SIGNAL_THRESHOLD,
    DEFAULT_PROXIMITY_SIGNAL_THRESHOLD,
)
from .coordinator import WifiScanCoordinator
from .entity import WifiScanEntity

PARALLEL_UPDATES = 0

NEW_NETWORK_DESCRIPTION = BinarySensorEntityDescription(
    key="new_network",
    translation_key="new_network",
)

PROXIMITY_ALERT_DESCRIPTION = BinarySensorEntityDescription(
    key="proximity_alert",
    translation_key="proximity_alert",
    device_class=BinarySensorDeviceClass.PROBLEM,
)

HEALTH_DESCRIPTION = BinarySensorEntityDescription(
    key="integration_health",
    translation_key="integration_health",
    device_class=BinarySensorDeviceClass.PROBLEM,
    entity_category=EntityCategory.DIAGNOSTIC,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor platform."""
    coordinator: WifiScanCoordinator = entry.runtime_data
    async_add_entities(
        [
            WifiScanBinarySensor(coordinator, entry, NEW_NETWORK_DESCRIPTION),
            WifiProximityBinarySensor(coordinator, entry, PROXIMITY_ALERT_DESCRIPTION),
            WifiHealthBinarySensor(coordinator, entry, HEALTH_DESCRIPTION),
        ]
    )


class WifiScanBinarySensor(WifiScanEntity, BinarySensorEntity):
    """On when any unknown network is currently detected."""

    _attr_about = (
        "On whenever at least one unknown network is in range. For a one-shot "
        "trigger per newly-seen network, use the wifi_ssid_monitor_new_network "
        "bus event instead."
    )

    def __init__(
        self,
        coordinator: WifiScanCoordinator,
        entry: ConfigEntry,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"

    @property
    def is_on(self) -> bool:
        """Return true if any unknown networks are currently detected."""
        if not self.coordinator.data:
            return False
        return bool(self.coordinator.data.get("unknown_count", 0) > 0)


class WifiProximityBinarySensor(WifiScanEntity, BinarySensorEntity):
    """On when an unknown network's signal is at or above the threshold."""

    _attr_about = (
        "On when the closest unknown network's signal reaches the Proximity "
        "Threshold. Signal is a 0-100% quality figure — higher means closer."
    )

    _unrecorded_attributes = WifiScanEntity._unrecorded_attributes | frozenset(
        {"strongest_unknown_signal", "threshold"}
    )

    def __init__(
        self,
        coordinator: WifiScanCoordinator,
        entry: ConfigEntry,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the proximity alert binary sensor."""
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"

    @property
    def _threshold(self) -> int:
        return int(
            self._entry.options.get(
                CONF_PROXIMITY_SIGNAL_THRESHOLD, DEFAULT_PROXIMITY_SIGNAL_THRESHOLD
            )
        )

    @property
    def _strongest(self) -> int | None:
        if not self.coordinator.data:
            return None
        value = self.coordinator.data.get("strongest_unknown_signal")
        return int(value) if isinstance(value, int | float) else None

    @property
    def is_on(self) -> bool:
        """Return true when the strongest unknown signal meets the threshold."""
        strongest = self._strongest
        if strongest is None:
            return False
        return strongest >= self._threshold

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the strongest signal and the configured threshold."""
        return self._with_about(
            {
                "strongest_unknown_signal": self._strongest,
                "threshold": self._threshold,
            }
        )


class WifiHealthBinarySensor(WifiScanEntity, BinarySensorEntity):
    """Self-diagnosis sensor: on when the integration detects a problem.

    This exists for the failure Home Assistant cannot see — a scan that
    succeeds while the data underneath has changed shape or meaning.
    """

    _attr_about = (
        "On when the integration detects a problem with its own data — an "
        "unreachable Supervisor, a changed payload, or all known networks "
        "vanishing at once. Details are in the issues attribute."
    )

    _unrecorded_attributes = frozenset(
        {"about", "issues", "checks_failed", "signal_unit", "last_good_scan"}
    )

    def __init__(
        self,
        coordinator: WifiScanCoordinator,
        entry: ConfigEntry,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the health sensor."""
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"

    @property
    def available(self) -> bool:
        """Always available — including when nothing else is.

        The default CoordinatorEntity.available returns last_update_success,
        which would take this sensor down at precisely the moment it has
        something to report. A health sensor that disappears during an outage
        is worse than no health sensor at all, because its silence is
        indistinguishable from health.
        """
        return True

    @property
    def is_on(self) -> bool:
        """Return true when a problem has been detected."""
        return bool(self.coordinator.health_snapshot.get("problem"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the health snapshot detail."""
        snapshot = self.coordinator.health_snapshot
        return self._with_about(
            {
                "issues": list(snapshot.get("issues") or []),
                "severity": snapshot.get("severity"),
                "checks_failed": list(snapshot.get("checks_failed") or []),
                "signal_unit": snapshot.get("signal_unit"),
                "last_good_scan": snapshot.get("last_good_scan"),
                "networks_scanned": snapshot.get("networks_scanned"),
            }
        )
