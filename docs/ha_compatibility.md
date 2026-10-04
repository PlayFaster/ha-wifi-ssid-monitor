# Home Assistant Compatibility

What Home Assistant versions this integration supports and the status of any changing core APIs.

**Reviewed 2026-09-30.**

> [!IMPORTANT]
>
> **This integration has zero active deprecation exposures.** It uses a single-device architecture without sub-devices, requires no device registry lookups, and explicitly passes `config_entry` to its coordinator.

---

## Supported versions

| Type | Version / Status | Note |
| :-- | :-- | :-- |
| **Minimum** | **2025.2.0** | Declared in `README.md` |
| **Tested against** | **2026.9.4** | `pytest-homeassistant-custom-component` 0.13.367 (development container) |
| **Enforced by** | `hacs.json` | `"homeassistant": "2025.2.0"` |
| **Functional floor** | `ConfigFlowResult`, typed entry handlers | Established in HA 2024.8 |
| **Python** | 3.13 or later | Required by Home Assistant 2025.2.0. Tests run on Python 3.14 |

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
| `voluptuous` imports | N/A (replaced by probatio in 2026.9) | None announced | Config flow and schemas | **Compatible**: HA aliases `voluptuous` to probatio via `install_as_voluptuous()` |
| Flow and service schema types (probatio) | 2026.10, type hints only | None announced | `voluptuous` imports in the config flow, services and schemas | **Compliant**: runtime is unaffected, and a shared `pyproject.toml` override makes Mypy treat `voluptuous` as untyped. Mypy run pending (C-037). |
| Device-class enums in `const` modules | 2026.10, type hints only | None announced | `BinarySensorDeviceClass` imported from the platform package | **Compliant**: the package re-export still works, and a shared `pyproject.toml` override makes Mypy count it as an export. Mypy run pending (C-037). |

---

## Upcoming milestones

- **Zero pending actions:** Because WiFi SSID Monitor binds all entities to a single host device without sub-devices, future Home Assistant core device-registry scoping changes (2026.8+ / 2027.8) do not require changes or compatibility shims.
- **Home Assistant 2026.10:** core types flow and service schemas as probatio and moves the device-class enums to `const` modules. This affects type checking only. The two Mypy overrides in the shared `pyproject.toml` are removed when the integration imports probatio directly or the floor passes the move.

---

## Version Control

| Version | Date | Author | Description |
| :-- | :-- | :-- | :-- |
| **v1.0.0** | 2026-08-21 | Antigravity | Initial creation addressing chore C-001. |
| **v1.1.0** | 2026-08-21 | Antigravity | Streamlined to standard lean project compatibility format (Option A). |
| **v1.2.0** | 2026-09-23 | Claude | Compatibility audit: tested-against updated to 2026.9.3; `voluptuous` → probatio row added. |
| **v1.2.1** | 2026-09-23 | Claude | Added Python row to supported versions; recorded the planned 2025.2.0 minimum for the next release. |
| **v1.3.0** | 2026-09-23 | Claude | Minimum raised from 2024.8.0 to 2025.2.0 (Python 3.13); planned-floor milestone removed. |
| **v1.4.0** | 2026-09-30 | Claude | Compatibility audit: tested-against updated to 2026.9.4 (`pytest-homeassistant-custom-component` 0.13.367); rows for probatio-typed schemas and `const`-module device classes; 2026.10 milestone. |
