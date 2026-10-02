# Project Complexity & Health: ha-wifi-ssid-monitor

**Last Measured:** 2026-10-02T15:56:48.407869+00:00 · **Release:** `2.0.5` · **Dev Version:** `2.0.5-dev8`

## 1. Executive Summary

| Metric | Value | Verdict / Evaluation |
| :-- | :-: | :-- |
| **PlayFaster Health Index** | **`93` / 100** | `EXCELLENT` ($\ge 90$ Excellent · $\ge 80$ Good · $\ge 70$ Warning) |
| **Max McCabe Complexity ($V(G)$)** | **13** | `PASS (<20)` in `async_register_services` ($< 20$ Pass · $20–23$ Warn · $\ge 24$ Fail) |
| **Mean Complexity per Routine** | **2.65** | Across 139 routines (Ideal $< 4.0$ per routine) |
| **Danger Routines ($\ge 20$)** | **0** | Zero tolerance (refactor or decompose) |
| **Elevated Routines ($10–19$)** | **3** | Monitor closely; candidate for cleanup |
| **Mean Routine Length** | **12.8 code lines** | Target $\le 15$ code lines ideal |
| **Largest Routine Length** | **105 code lines** | `_process_scan` in `coordinator.py` (Target $\le 40$ ideal, $> 80$ warn, $> 150$ fail) |
| **Routines > 80 Code Lines** | **1** | Candidate for functional decomposition |
| **Largest Module** | **546 code lines** | `coordinator.py` (Warn $> 1,500$ code lines module bloat) |
| **Modules > 1,500 Code Lines** | **0** | Candidate for module decomposition |
| **Code Suppressions (`# noqa`)** | **1** | Zero preferred; review regularly |
| **Type Suppressions (`# type: ignore`)** | **0** | Mypy strict compliance |
| **Source Python SLOC** | **2,502** | Across 15 files in custom_components/ (code statements) |
| **Docstring Volume** | **470 lines** | Interface and contract documentation |
| **Comment Density** | **11.6%** | 291 inline comment lines (Healthy implementation rationale) |
| **Platform Declarations SLOC** | **672 lines** | Across 5 platform files |
| **Core Engine / Driver SLOC** | **1,830 lines** | Across 10 coordinator/API/helper files |
| **Static Entities** | **18 entities** | Scale indicator (`all_sensors.md`) |
| **Platform SLOC / Entity** | **37.3 lines/entity** | Target 20 – 45 lines/entity declarative efficiency |
| **Test-to-Source Ratio** | **2.34×** | 5,862 test lines ($\ge 1.5×$ recommended) |
| **Pytest Coverage** | **100%** | 457 tests executed |
| **Pytest Duration** | **95.52s** | Full test suite wall-clock execution time |

## 2. High Complexity Routines ($\ge 10$)

| Score | Routine Symbol | Location | Status |
| :-: | :-- | :-- | :-- |
| **13** | `async_register_services` | `services.py:263` | `ELEVATED` |
| **11** | `get_access_points` | `api.py:43` | `ELEVATED` |
| **10** | `_process_scan` | `coordinator.py:543` | `ELEVATED` |

## 3. Active Code Suppressions (`custom_components/`)

| Line | Rule Bypassed | File |
| :-: | :-- | :-- |
| 357 | `BLE001` | `coordinator.py` |

## 4. Comment Quality & Density Audits

### 4.1 High Comment Density Files (> 25% comments/code)

| Module | Rationale / Advisory |
| :-- | :-- |
| `const.py` | Inspect for commented-out dead code or procedural narration |
| `parse.py` | Inspect for commented-out dead code or procedural narration |

### 4.2 Contiguous Comment Blocks (> 8 lines)

| Location | Length | Advisory |
| :-- | :-: | :-- |
| `health.py:22` | 10 lines | Long procedural block; consider moving architecture notes to docs |
| `sensor.py:138` | 10 lines | Long procedural block; consider moving architecture notes to docs |
| `const.py:150` | 9 lines | Long procedural block; consider moving architecture notes to docs |
| `coordinator.py:362` | 9 lines | Long procedural block; consider moving architecture notes to docs |
| `coordinator.py:652` | 9 lines | Long procedural block; consider moving architecture notes to docs |
