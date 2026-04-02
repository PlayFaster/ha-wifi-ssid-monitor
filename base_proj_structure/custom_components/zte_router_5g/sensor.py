import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Final

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import CONF_HOST, UnitOfInformation
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import ZTERouterDataUpdateCoordinator
from .helpers import get_router_model

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class ZTESensorEntityDescription(SensorEntityDescription):
    """Describes ZTE sensor entity."""

    group: str = "router"


# Descriptions for technical router sensors
SENSOR_TYPES: Final[tuple[ZTESensorEntityDescription, ...]] = (
    ZTESensorEntityDescription(
        key="lte_rsrp",
        translation_key="lte_rsrp",
        icon="mdi:signal",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="dBm",
    ),
    ZTESensorEntityDescription(
        key="lte_rsrq",
        translation_key="lte_rsrq",
        icon="mdi:signal",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="dBm",
    ),
    ZTESensorEntityDescription(
        key="lte_rssi",
        translation_key="lte_rssi",
        icon="mdi:signal",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="dBm",
    ),
    ZTESensorEntityDescription(
        key="lte_snr",
        translation_key="lte_snr",
        icon="mdi:waveform",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="dB",
    ),
    ZTESensorEntityDescription(
        key="z5g_rsrp",
        translation_key="z5g_rsrp",
        icon="mdi:signal",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="dBm",
    ),
    ZTESensorEntityDescription(
        key="z5g_sinr",
        translation_key="z5g_sinr",
        icon="mdi:waveform",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="dB",
    ),
    ZTESensorEntityDescription(
        key="signalbar",
        translation_key="signalbar",
        icon="mdi:signal",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ZTESensorEntityDescription(
        key="network_type",
        translation_key="network_type",
        icon="mdi:transmission-tower",
    ),
    ZTESensorEntityDescription(
        key="monthly_rx_bytes",
        translation_key="monthly_rx_bytes",
        icon="mdi:download",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=2,
        group="data",
    ),
    ZTESensorEntityDescription(
        key="monthly_tx_bytes",
        translation_key="monthly_tx_bytes",
        icon="mdi:upload",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=2,
        group="data",
    ),
    ZTESensorEntityDescription(
        key="monthly_total_bytes",
        translation_key="monthly_total_bytes",
        icon="mdi:swap-vertical-bold",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=2,
        group="data",
    ),
    ZTESensorEntityDescription(
        key="last_updated",
        translation_key="last_updated",
        icon="mdi:update",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ZTESensorEntityDescription(
        key="device_uptime",
        translation_key="device_uptime",
        icon="mdi:clock-start",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ZTESensorEntityDescription(
        key="cell_id",
        translation_key="cell_id",
        icon="mdi:transmission-tower",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ZTESensorEntityDescription(
        key="lan_ipaddr",
        translation_key="lan_ipaddr",
        icon="mdi:map-marker-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ZTESensorEntityDescription(
        key="wan_ipaddr",
        translation_key="wan_ipaddr",
        icon="mdi:map-marker-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ZTESensorEntityDescription(
        key="wan_apn",
        translation_key="wan_apn",
        icon="mdi:numeric-3-circle-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ZTESensorEntityDescription(
        key="wan_connect_status",
        translation_key="wan_connect_status",
        icon="mdi:transmission-tower",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ZTESensorEntityDescription(
        key="lte_ca_pcell_band",
        translation_key="lte_ca_pcell_band",
        icon="mdi:transmission-tower",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ZTESensorEntityDescription(
        key="lte_ca_pcell_bandwidth",
        translation_key="lte_ca_pcell_bandwidth",
        icon="mdi:transmission-tower",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ZTESensorEntityDescription(
        key="lte_pci",
        translation_key="lte_pci",
        icon="mdi:transmission-tower",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ZTESensorEntityDescription(
        key="mdm_mcc",
        translation_key="mdm_mcc",
        icon="mdi:transmission-tower",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ZTESensorEntityDescription(
        key="mdm_mnc",
        translation_key="mdm_mnc",
        icon="mdi:transmission-tower",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ZTESensorEntityDescription(
        key="network_provider",
        translation_key="network_provider",
        icon="mdi:numeric-3-circle-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ZTESensorEntityDescription(
        key="nr5g_action_band",
        translation_key="nr5g_action_band",
        icon="mdi:transmission-tower",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ZTESensorEntityDescription(
        key="nr5g_action_channel",
        translation_key="nr5g_action_channel",
        icon="mdi:transmission-tower",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ZTESensorEntityDescription(
        key="nr5g_pci",
        translation_key="nr5g_pci",
        icon="mdi:transmission-tower",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ZTESensorEntityDescription(
        key="rmcc",
        translation_key="rmcc",
        icon="mdi:transmission-tower",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ZTESensorEntityDescription(
        key="rmnc",
        translation_key="rmnc",
        icon="mdi:transmission-tower",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ZTESensorEntityDescription(
        key="wan_active_band",
        translation_key="wan_active_band",
        icon="mdi:transmission-tower",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ZTESensorEntityDescription(
        key="wan_active_channel",
        translation_key="wan_active_channel",
        icon="mdi:transmission-tower",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ZTESensorEntityDescription(
        key="wan_lte_ca",
        translation_key="wan_lte_ca",
        icon="mdi:transmission-tower",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ZTESensorEntityDescription(
        key="wa_inner_version",
        translation_key="wa_inner_version",
        icon="mdi:transmission-tower",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)

# Descriptions for SMS sensors.
# Keys are 'msg_total' / 'msg_recent' (not 'sms_*') to avoid the double-'sms'
# entity_id that would result from the "ZTE 5G SMS" sub-device name prefix,
# e.g. we want 'zte_5g_sms_msg_total' not 'zte_5g_sms_sms_total'.
MSG_TOTAL_DESCRIPTION = ZTESensorEntityDescription(
    key="msg_total",
    translation_key="msg_total",
    icon="mdi:message-plus-outline",
    state_class=SensorStateClass.MEASUREMENT,
    group="sms",
)

MSG_RECENT_DESCRIPTION = ZTESensorEntityDescription(
    key="msg_recent",
    translation_key="msg_recent",
    icon="mdi:message-badge-outline",
    group="sms",
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor platform."""
    coordinator: ZTERouterDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        ZTEDataSensor(coordinator, entry, description) for description in SENSOR_TYPES
    ]
    entities.append(ZTEMsgSensor(coordinator, entry, MSG_TOTAL_DESCRIPTION))
    entities.append(ZTEMsgContentSensor(coordinator, entry, MSG_RECENT_DESCRIPTION))
    async_add_entities(entities)


class ZTEDataSensor(CoordinatorEntity, SensorEntity):
    """Implementation of technical router sensors."""

    _attr_has_entity_name = True
    entity_description: ZTESensorEntityDescription

    def __init__(self, coordinator, entry, description):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"

    @property
    def native_value(self):
        """Return the value of the sensor."""
        data = self.coordinator.data
        if not data:
            return None

        key = self.entity_description.key

        if key == "last_updated":
            return self.coordinator.last_update_success_time

        if key == "device_uptime":
            uptime_seconds = data.get("realtime_time")
            if not uptime_seconds:
                return None
            try:
                seconds = int(float(uptime_seconds))
                boot_time = dt_util.now() - timedelta(seconds=seconds)
                return boot_time.replace(second=0, microsecond=0)
            except Exception as e:
                _LOGGER.debug(
                    "Failed to calculate device_uptime for %s: %s", self._entry.title, e
                )
                return None

        # monthly_total_bytes is calculated here by summing rx+tx.
        # The router returns these as bytes but we convert
        #    them to GB values sum and round.
        # NOTE: Do NOT add 'monthly_total_bytes' to the generic conversion
        # block below — it would cause a double-conversion bug.
        if key == "monthly_total_bytes":
            try:
                rx = float(data.get("monthly_rx_bytes", 0))
                tx = float(data.get("monthly_tx_bytes", 0))
                return round((rx + tx) / 1073741824, 2)
            except Exception as e:
                _LOGGER.debug(
                    "Failed to calculate monthly_total_bytes for %s: %s",
                    self._entry.title,
                    e,
                )
                return None

        # Case-sensitive mapping for specific raw data keys
        raw_key = key
        if key == "z5g_rsrp":
            raw_key = "Z5g_rsrp"
        if key == "z5g_sinr":
            raw_key = "Z5g_SINR"

        val = data.get(raw_key)
        if val in [None, ""]:
            return None

        # Round rx/tx values to 2dp for display consistency.
        # The router returns Bytes but changing to GB values rounded.
        # monthly_total_bytes is explicitly excluded here as it is handled above;
        # the guard prevents a double-conversion bug if that block is ever refactored.
        if "monthly" in key and "_bytes" in key and key != "monthly_total_bytes":
            try:
                return round(float(val) / 1073741824, 2)
            except Exception as e:
                _LOGGER.debug(
                    "Failed to convert %s value '%s' to GB for %s: %s",
                    key,
                    val,
                    self._entry.title,
                    e,
                )
                return val

        return val

    @property
    def device_info(self):
        """Return device information."""
        host = self._entry.options[CONF_HOST]
        if self.entity_description.group == "data":
            return {
                "identifiers": {(DOMAIN, f"{host}_monthly")},
                "name": f"{self._entry.title} Monthly",
                "manufacturer": "ZTE",
                "via_device": (DOMAIN, host),
            }
        return {
            "identifiers": {(DOMAIN, host)},
            "name": self._entry.title,
            "manufacturer": "ZTE",
            "configuration_url": f"http://{host}",
            "model": get_router_model(self.coordinator.data),
        }


class ZTEMsgSensor(CoordinatorEntity, SensorEntity):
    """Implementation of the message total count sensor."""

    _attr_has_entity_name = True
    entity_description: ZTESensorEntityDescription

    def __init__(self, coordinator, entry, description: ZTESensorEntityDescription):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"

    @property
    def native_value(self):
        """Return total message count."""
        data = self.coordinator.data
        if not data:
            return None
        keys = [
            "sms_nv_rev_total",
            "sms_nv_send_total",
            "sms_nv_draftbox_total",
            "sms_sim_rev_total",
            "sms_sim_send_total",
            "sms_sim_draftbox_total",
        ]
        try:
            return sum(int(data.get(k, 0)) for k in keys)
        except Exception as e:
            _LOGGER.debug(
                "Failed to calculate total SMS count for %s: %s", self._entry.title, e
            )
            return None

    @property
    def extra_state_attributes(self):
        """Return detailed message counts."""
        data = self.coordinator.data
        if not data:
            return {}
        try:
            return {
                "sms_nv_total": int(data.get("sms_nv_total", 0)),
                "sms_sim_total": int(data.get("sms_sim_total", 0)),
                "sms_nv_rev_total": int(data.get("sms_nv_rev_total", 0)),
                "sms_nv_send_total": int(data.get("sms_nv_send_total", 0)),
                "sms_nv_draftbox_total": int(data.get("sms_nv_draftbox_total", 0)),
                "sms_sim_rev_total": int(data.get("sms_sim_rev_total", 0)),
                "sms_sim_send_total": int(data.get("sms_sim_send_total", 0)),
                "sms_sim_draftbox_total": int(data.get("sms_sim_draftbox_total", 0)),
            }
        except Exception as e:
            _LOGGER.debug(
                "Failed to parse SMS attributes for %s: %s", self._entry.title, e
            )
            return {}

    @property
    def device_info(self):
        """Return device information linking to the SMS sub-device."""
        host = self._entry.options[CONF_HOST]
        return {
            "identifiers": {(DOMAIN, f"{host}_sms")},
            "name": f"{self._entry.title} SMS",
            "manufacturer": "ZTE",
            "via_device": (DOMAIN, host),
        }


class ZTEMsgContentSensor(CoordinatorEntity, SensorEntity):
    """Implementation of the most recent message content sensor."""

    _attr_has_entity_name = True
    entity_description: ZTESensorEntityDescription

    def __init__(self, coordinator, entry, description: ZTESensorEntityDescription):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"

    @property
    def native_value(self):
        """Return the content of the most recent message."""
        if not self.coordinator.data:
            return "No messages"
        msg = self.coordinator.data.get("last_sms", {})
        return msg.get("content_decoded", "No messages")

    @property
    def extra_state_attributes(self):
        """Return metadata for the most recent message."""
        if not self.coordinator.data:
            return {}
        msg = self.coordinator.data.get("last_sms", {})
        return {
            "id": msg.get("id"),
            "number": msg.get("number_decoded"),
            "date": msg.get("date_decoded"),
        }

    @property
    def device_info(self):
        """Return device information linking to the SMS sub-device."""
        host = self._entry.options[CONF_HOST]
        return {
            "identifiers": {(DOMAIN, f"{host}_sms")},
            "name": f"{self._entry.title} SMS",
            "via_device": (DOMAIN, host),
        }
