# Numeric Guard Bands: WiFi SSID Monitor

Guard bands reject physically impossible readings before they reach the state machine. A value outside its band returns `None`, so the entity reads `unknown` rather than recording a spike that would then live in long-term statistics forever.

**This document describes code.** Nothing generates it, so it is reconciled by hand against the entity descriptions — in both directions, since a band listed here that does not exist is as much a defect as one that exists and is not listed. Last reconciled **2026-08-03**.

Coverage is enforced by `tests/test_sensor.py::test_every_numeric_sensor_has_a_guard_band`, which fails if any sensor carrying a unit or a `state_class` declares no bounds, and by `::test_unguarded_allowlist_has_no_dead_entries`, which fails if an exemption outlives the sensor it was granted for.

---

## Approach

Limits are declared on the `WifiSensorEntityDescription` beside the sensor they belong to, and enforced once in the shared `native_value` property:

```python
if isinstance(value, int | float):
    if description.min_limit is not None and value < description.min_limit:
        return None
    if description.max_limit is not None and value > description.max_limit:
        return None
```

Declaring the limit next to the sensor keeps it visible where it is read, and means changing one is a single number rather than a branch in a shared function.

**A correct check over a description that declares nothing is a no-op**, and reviewing the enforcement above tells you nothing about how many sensors reach it — which is why coverage is a test rather than a convention.

---

## Sensor guard bands

Every sensor carrying a `native_unit_of_measurement` or a `state_class` appears here. Source: `sensor.py` → `SENSOR_TYPES`.

| Sensor | Key | Why it needs bounds | Min | Max | Rationale |
| :-- | :-- | :-- | --: | --: | :-- |
| Total SSID Count | `count` | `state_class` | 0 | 256 | A count cannot be negative; 256 is far above any real environment, so anything higher is an artifact. |
| Unknown SSID Count | `unknown_count` | `state_class` | 0 | 256 | Same reasoning; it is a subset of the above. |
| New Networks (24h) | `new_24h` | `state_class` | 0 | 4096 | Derived from the persisted first-seen history, which is capped at 2,000 entries — the ceiling sits above that cap so a legitimate value is never discarded. |
| Strongest Unknown Signal | `strongest_unknown_signal` | unit + `state_class` | 0 | 100 | A percentage. `parse.py` already clamps to 0–100 when converting from dBm; the band is the second line of defense for a value that arrives as a percentage and is out of range. |

### Sensors that correctly have no bounds

Listed so their absence reads as deliberate rather than missed. None carries a unit or a `state_class`, so none can reach long-term statistics.

| Sensor | Key | Why no band |
| :-- | :-- | :-- |
| Interface | `interface` | Text — the adapter name. |
| Last Updated | `last_updated` | A `TIMESTAMP` device class, not a number. |
| Strongest Unknown SSID | `strongest_unknown_ssid` | Text — a network name, or `None Detected`. |

There is currently **no exemption allow-list**: `UNGUARDED_ALLOWLIST` in `tests/test_sensor.py` is empty, because every sensor that needs a band has one. An entry there would need a written reason.

---

## Control ranges

Distinct from guard bands. These are the limits Home Assistant enforces on the input itself, so an out-of-range value cannot be submitted rather than being rejected after the fact. Source: `number.py` → `NUMBER_TYPES`.

| Control | Key | Min | Max | Step | Unit |
| :-- | :-- | --: | --: | --: | :-- |
| Scan Interval | `scan_interval` | 1 | 180 | 1 | minutes |
| Proximity Threshold | `proximity_signal_threshold` | 0 | 100 | 1 | % |

---

## State class

No sensor uses `SensorStateClass.TOTAL`, and `tests/test_sensor.py::test_no_sensor_uses_the_total_state_class` keeps it that way with an empty allow-list. Under plain `TOTAL`, Home Assistant recognizes a counter reset only from a `last_reset` attribute this integration does not publish, so a resetting counter records each rollover as a large negative delta and walks the statistics sum backwards. `TOTAL_INCREASING` is the correct class for a genuine counter; the four sensors above are `MEASUREMENT`, which is correct for values that go up and down.

---

## Version Control

- **v1.0.1** (2026-05-05) - Created.
- **v1.0.2** (2026-06-11) - Added `Strongest Unknown RSSI` guard band entry (−100 to 0 dBm). Removed stale "Future Extensions" note - signal strength sensor is now implemented (v1.6.0-dev4).
- **v1.0.3** (2026-06-12) - Updated network counter names and keys to `Total SSID Count` (`total_ssid_count`) and `Unknown SSID Count` (`unknown_ssid_count`) to match HA runtime.
- **v1.0.4** (2026-07-23) - Updated signal metric to `Strongest Unknown Signal` (0–100%) clamped via `parse.py` boundary.
- **v2.0.0** (2026-08-03) - **Reconciled against the source in both directions for the first time**, per `dev_standards` §6, which requires it because nothing generates this document and no test compared it to the code. Four corrections. **Two bands existed and were undocumented**: `new_24h` (0–4096) and the `proximity_signal_threshold` control range (0–100). **One was understated** — Strongest Unknown Signal was described as clamped in the parse boundary only, when the description also declares `min_limit=0, max_limit=100`. **The Key column was wrong throughout**: it listed entity-id suffixes (`total_ssid_count`) rather than the description keys (`count`), and the worked example used a `name=` field that is the §12 anti-pattern and does not appear in the code. And the "Future Extensions" section that v1.0.2 records as removed was **still present**, proposing channel validation. Added the sensors that correctly have no bounds, so their absence reads as deliberate; added the control-range and state-class sections; and pointed at the three tests that now enforce coverage, exemption hygiene and the `TOTAL` ban, none of which existed when this document was last edited.
