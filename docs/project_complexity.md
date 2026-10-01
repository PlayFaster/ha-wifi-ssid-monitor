# Project Complexity & Health: ha-wifi-ssid-monitor

**Last Measured:** 2026-10-01T01:31:26.677177+00:00 · **Release:** `2.0.5` · **Dev Version:** `2.0.5-dev7`

## 1. Executive Summary

| Metric | Value | Verdict / Evaluation |
| :-- | :-: | :-- |
| **PlayFaster Health Index** | **`81` / 100** | `ACTION REQUIRED` ($\ge 90$ Excellent · $\ge 80$ Good · $\ge 70$ Warning) |
| **Max McCabe Complexity ($V(G)$)** | **24** | `FAIL (>=24)` in `async_register_services` ($< 20$ Pass · $20–23$ Warn · $\ge 24$ Fail) |
| **Mean Complexity per Routine** | **2.74** | Across 138 routines (Ideal $< 4.0$ per routine) |
| **Danger Routines ($\ge 20$)** | **1** | Zero tolerance (refactor or decompose) |
| **Elevated Routines ($10–19$)** | **2** | Monitor closely; candidate for cleanup |
| **Mean Routine Length** | **13.2 code lines** | Target $\le 15$ code lines ideal |
| **Largest Routine Length** | **140 code lines** | `async_register_services` in `services.py` (Target $\le 40$ ideal, $> 80$ warn, $> 150$ fail) |
| **Routines > 80 Code Lines** | **2** | Candidate for functional decomposition |
| **Largest Module** | **546 code lines** | `coordinator.py` (Warn $> 1,500$ code lines module bloat) |
| **Modules > 1,500 Code Lines** | **0** | Candidate for module decomposition |
| **Code Suppressions (`# noqa`)** | **1** | Zero preferred; review regularly |
| **Type Suppressions (`# type: ignore`)** | **0** | Mypy strict compliance |
| **Source Python SLOC** | **2,486** | Across 15 files in custom_components/ (code statements) |
| **Docstring Volume** | **469 lines** | Interface and contract documentation |
| **Comment Density** | **11.7%** | 291 inline comment lines (Healthy implementation rationale) |
| **Platform Declarations SLOC** | **672 lines** | Across 5 platform files |
| **Core Engine / Driver SLOC** | **1,814 lines** | Across 10 coordinator/API/helper files |
| **Static Entities** | **18 entities** | Scale indicator (`all_sensors.md`) |
| **Platform SLOC / Entity** | **37.3 lines/entity** | Target 20 – 45 lines/entity declarative efficiency |
| **Test-to-Source Ratio** | **2.28×** | 5,659 test lines ($\ge 1.5×$ recommended) |
| **Pytest Coverage** | **100%** | 414 tests executed |
| **Pytest Duration** | **84.04s** | Full test suite wall-clock execution time |

## 2. High Complexity Routines ($\ge 10$)

| Score | Routine Symbol | Location | Status |
| :-: | :-- | :-- | :-- |
| **24** | `async_register_services` | `services.py:148` | `FAIL` |
| **11** | `get_access_points` | `api.py:43` | `ELEVATED` |
| **11** | └─ `_handle_get_networks` | `services.py:204` | `ELEVATED (nested)` |
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
