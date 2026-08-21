# Home Assistant Compatibility

What Home Assistant versions this integration supports, which HA APIs it depends on, and the status of any changing core APIs.

**Reviewed 2026-08-21.**

> [!IMPORTANT]
>
> **This integration has zero active deprecation exposures.** It does not manage sub-devices (no `via_device` links or device registry lookups), does not implement a `device_tracker` platform, and explicitly passes `config_entry` to its coordinator. This file exists so compatibility stays confirmed by audit rather than by assumption.

---

## Supported versions

| Type | Note |
| :-- | :-- |
| **Minimum** | 2024.8.0 (declared in `README.md`) |
| **Tested against** | 2026.8.0 — the version in the development container |
| **Enforced by** | `hacs.json` → `"homeassistant": "2024.8.0"`. HACS refuses installation below it. |
| **Verified at the minimum?** | **Code-verified.** Functional code gating analysis confirms 2024.8.0 APIs; not tested against a live 2024.8 instance. |

**The floor is set by `ConfigEntry.runtime_data` and `ConfigFlowResult`** (both introduced in HA 2024.6), alongside modern typed config flow handling and coordinator entry associations established in HA 2024.8.0. See [`ha_minimum_version_matrix.md`](file:///c:/Local/Code/ha-dev-pf/shared/SharedNotes/info/ha_min_ver_xproj/ha_minimum_version_matrix.md) for the cross-project gating analysis.

---

## Deprecation ledger

Every HA behavior or API relevant to custom integrations that is deprecated, moving, or newly available.

| API / behavior | Deprecated | **Removed** | Our exposure | State |
| :-- | :-- | :-- | :-- | :-- |
| `DeviceInfo.via_device` identifier tuple | 2026.8 | **2027.8** | None — single device keyed on `(DOMAIN, entry.entry_id)` | **N/A** |
| `async_get_device(identifiers=…)` | 2026.8 | **2027.8** | None — no device registry search calls | **N/A** |
| Implicit coordinator `config_entry` detection | 2024.8 | 2026.8 | `DataUpdateCoordinator` | **Done** — `config_entry=entry` passed explicitly |
| `BaseTrackerEntity.battery_level` | 2026.6 | **2027.7** | None — no `device_tracker` platform | **N/A** |
| `TrackerEntity.location_name` | 2026.6 | **2027.7** | None — no `device_tracker` platform | **N/A** |
| `data_entry_flow.section` | N/A (added 2024.11) | N/A | None — flat config/options schema | **N/A** |

---

## Architectural & compatibility notes

### 1. Supervisor Network API prerequisite

This integration queries the Home Assistant Supervisor Network API (`/network/interface/{interface}/accesspoints`) via the host's client session. It requires:
- A **Home Assistant OS (HAOS)** or **Supervised** installation.
- Physical WiFi hardware available and enabled under **Settings > System > Network**.
- It is incompatible with standalone Home Assistant Container or Core installations because no Supervisor API exists in those environments.

### 2. Single-device identity model

The integration creates a single Home Assistant device representing the host machine's WiFi adapter:
- Keyed on `identifiers={(DOMAIN, entry.entry_id)}`.
- Supervisor exposes no host hardware MAC address and there is no remote router IP, so `entry_id` serves as the stable identifier for the lifetime of the config entry.
- Because there are no attached sub-devices, no `_compat.py` shim layer is needed for device registry compatibility.

### 3. Unrecorded attributes mixin

The `WifiAboutEntity` mixin routes static `about` notes into `_unrecorded_attributes`. This allows informational documentation to display in the Home Assistant UI (e.g. More Info dialogs) without incurring database writes in the recorder history.

### 4. Automation examples (`note:` key)

Documentation examples in `README.md` utilize the `note:` key introduced in **Home Assistant 2026.6** to preserve inline comments inside the HA automation editor. The documentation explicitly notes that users on older versions may omit the `note:` key without affecting functionality.

---

## How to re-check this document

Re-check when the development container's HA version is upgraded, and at minimum when a new HA major version is released:

1. Read the HA developer blog entries since the review date.
2. Verify if any newly deprecated core helpers or entity attributes touch the integration's sensor, binary_sensor, number, button, switch, or coordinator implementations.
3. Update the **Reviewed** date upon review.

---

## Version Control

| Version | Date | Author | Description |
| :-- | :-- | :-- | :-- |
| **v1.0.0** | 2026-08-21 | Antigravity | Initial creation addressing chore C-001. Records version floor (2024.8.0), zero deprecation exposure status, and architecture notes. |
