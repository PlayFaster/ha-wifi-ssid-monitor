# Signal Metric Guard Bands: WiFi SSID Monitor

To ensure the Home Assistant UI remains clean and professional, we apply "Guard Bands" to incoming network data. If a value falls outside these realistic physical limits, the sensor is marked as `Unavailable` to prevent misleading spikes or impossible values from polluting your long-term statistics.

## Guard Band Strategy

We use a **Declarative Validation** approach. Limits are defined directly within the `WifiSensorEntityDescription` for each sensor. The base sensor class automatically enforces these bounds before passing the value to Home Assistant.

### Why this approach?

- **Readability**: Limits are visible next to the sensor definition.
- **Maintainability**: Changing a limit requires updating only one number, not complex logic.
- **Data Integrity**: Prevents impossible values (e.g., negative counts) from being recorded in the database.
- **UI Stability**: Ensures that dashboards and graphs remain readable and aren't skewed by transient API artifacts or environment glitches.

---

## Validated Metric Limits

| Metric Category | Metric Name | Min | Max | Action if Out of Bounds |
| :-- | :-- | :-- | :-- | :-- |
| **Network Counters** | Total SSID Count | 0 | 256 | Set to `Unavailable` |
|  | Unknown SSID Count | 0 | 256 | Set to `Unavailable` |
| **Signal Strength** | Strongest Unknown Signal | 0 % | 100 % | Clamped in parse boundary (0–100%) |
| **Diagnostics** | Scan Interval | 1 | 180 | Enforced by UI (1-180 min) |

---

## Implementation Details

The `WifiSensorEntityDescription` data-class includes optional `min_limit` and `max_limit` attributes.

**Example Definition:**

```python
WifiSensorEntityDescription(
    key="total_ssid_count",
    name="Total SSID Count",
    ...
    min_limit=0,
    max_limit=256,
    value_fn=lambda data: data.get("total_ssid_count"),
)
```

The `native_value` property in the `WifiScanSensor` class performs the following check:

```python
# Apply Guard Bands (Standard 4)
if isinstance(value, int | float):
    if description.min_limit is not None and value < description.min_limit:
        return None
    if description.max_limit is not None and value > description.max_limit:
        return None
```

## Future Extensions

While the core counters are now protected, future updates may include:

- **Channel Validation**: Guarding against invalid WiFi channel numbers (e.g., >14 for 2.4GHz).

---

## Version Control

- **v1.0.1** (2026-05-05) - Created.
- **v1.0.2** (2026-06-11) - Added `Strongest Unknown RSSI` guard band entry (−100 to 0 dBm). Removed stale "Future Extensions" note — signal strength sensor is now implemented (v1.6.0-dev4).
- **v1.0.3** (2026-06-12) - Updated network counter names and keys to `Total SSID Count` (`total_ssid_count`) and `Unknown SSID Count` (`unknown_ssid_count`) to match HA runtime.
- **v1.0.4** (2026-07-23) - Updated signal metric to `Strongest Unknown Signal` (0–100%) clamped via `parse.py` boundary.
