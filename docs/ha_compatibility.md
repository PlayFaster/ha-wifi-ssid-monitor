# Home Assistant Compatibility

What Home Assistant versions this integration supports and the status of any changing core APIs.

**Reviewed 2026-08-21.**

> [!IMPORTANT]
>
> **This integration has zero active deprecation exposures.** It uses a single-device architecture without sub-devices, requires no device registry lookups, and explicitly passes `config_entry` to its coordinator.

---

## Supported versions

| Type | Version / Status | Note |
| :-- | :-- | :-- |
| **Minimum** | **2024.8.0** | Declared in `README.md` |
| **Tested against** | **2026.8.0** | Development container environment |
| **Enforced by** | `hacs.json` | `"homeassistant": "2024.8.0"` |
| **Functional floor** | `ConfigFlowResult`, typed entry handlers | Established in HA 2024.8 |

---

## Deprecation & compatibility ledger

| API / Feature | Deprecated in | Removed in | Integration Exposure | Status |
| :-- | :-- | :-- | :-- | :-- |
| `DeviceInfo.via_device` identifier tuple | 2026.8 | **2027.8** | None — single device | **N/A** |
| `async_get_device(identifiers=…)` | 2026.8 | **2027.8** | None — no lookups | **N/A** |
| Implicit coordinator `config_entry` detection | 2024.8 | **2026.8** | `DataUpdateCoordinator` | **Done** — passed explicitly |
| `BaseTrackerEntity.battery_level` | 2026.6 | **2027.7** | None — no tracker platform | **N/A** |
| `TrackerEntity.location_name` | 2026.6 | **2027.7** | None — no tracker platform | **N/A** |
| `data_entry_flow.section` | N/A (added 2024.11) | N/A | None — flat config schema | **N/A** |

---

## Upcoming milestones

- **Zero pending actions:** Because WiFi SSID Monitor binds all entities to a single host device without sub-devices, future Home Assistant core device-registry scoping changes (2026.8+ / 2027.8) do not require changes or compatibility shims.

---

## Version Control

| Version | Date | Author | Description |
| :-- | :-- | :-- | :-- |
| **v1.0.0** | 2026-08-21 | Antigravity | Initial creation addressing chore C-001. |
| **v1.1.0** | 2026-08-21 | Antigravity | Streamlined to standard lean project compatibility format (Option A). |
