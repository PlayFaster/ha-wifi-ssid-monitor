<!-- markdownlint-disable MD033 -->

# WiFi SSID Monitor for Home Assistant

[![HACS Integration](https://img.shields.io/badge/HACS-Integration-orange.svg)](https://hacs.xyz/) [![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5?logo=homeassistant&logoColor=white)](https://hacs.xyz/docs/faq/custom_repositories) [![Latest Release](https://img.shields.io/github/v/release/PlayFaster/ha-wifi-ssid-monitor?label=Release&logo=github)](https://github.com/PlayFaster/ha-wifi-ssid-monitor/releases) [![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0) [![Validate](https://github.com/PlayFaster/ha-wifi-ssid-monitor/actions/workflows/validate.yaml/badge.svg)](https://github.com/PlayFaster/ha-wifi-ssid-monitor/actions/workflows/validate.yaml) ![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/PlayFaster/6d1d30e996dd53f04d2c2fc6b6cddece/raw/coverage.json) [![Last Commit](https://img.shields.io/github/last-commit/PlayFaster/ha-wifi-ssid-monitor?label=Last%20commit)](https://github.com/PlayFaster/ha-wifi-ssid-monitor/commits/main)

---

![WiFi SSID Monitor Logo](custom_components/wifi_ssid_monitor/brand/dark_logo.png)

---

A Home Assistant integration that monitors and reports on WiFi networks in your environment using the Home Assistant Supervisor Network API.

- **WiFi Environment Awareness**: Regularly scans for visible WiFi SSIDs, signal quality (0–100%), frequency bands, and access point (AP) modes.
- **Rogue SSID & Security Alerting**: Distinguishes known networks from unexpected arrivals, firing immediate **New Network** events and a **Proximity Alert** when an unknown AP gets too close.
- **Smart Device Setup Tracking**: Can detect when smart home devices enter access-point/pairing mode due to fresh installation or unexpected factory resets.
- **Dynamic Polling & Zero Noise**: Fully automatable scan interval, band filtering switches, hidden network controls, and database recorder exclusions.

> [!NOTE]
>
> **Is this the right integration for you?**
>
> - **If you want to monitor WiFi networks in your vicinity**, track connection uptime, or detect rogue/unauthorized access points, then **yes**.
> - **This integration is for you if** you want:
>   - **Rogue AP Detection** — Count detectable networks and alert on unknown SSIDs.
>   - **Smart Device Setup Tracking** — Identify when new devices enter pairing/AP mode.
>   - **Dynamic Polling** — Change scan intervals directly from the Home Assistant UI or via automations.
>
> Requires a Home Assistant Supervised or HAOS installation with physical WiFi hardware. The Supervisor API is not available on plain container or core installations.
>
> If you run a Ubiquiti UniFi Network on a UDM Gateway with UniFI Access Points you may be interested in my [UniFi Network Monitor](https://github.com/PlayFaster/ha-unifi-network-monitor) which provides similar capability (Rogue Access Point monitoring) but across all of your UniFi Access Points.

---

> [!WARNING]
>
> **Upgrading from 1.6.x to 2.0.0 or above — breaking changes.** This release corrects long-standing signal-unit and band-filter bugs, which required renaming several things. There are also some moves. This was not done lightly, but the previous set-up was incorrect for most systems.
>
> 1. **`sensor.wifi_ssid_monitor_strongest_unknown_rssi` is removed**, replaced by `sensor.wifi_ssid_monitor_strongest_unknown_signal` (0–100%, not dBm). The old entity becomes unavailable — delete it when convenient; its long-term statistics are kept (delete in Developer Tools > Statistics). Update any dashboard or automation referencing it.
> 2. **Signal is now a 0–100% quality figure** everywhere. Higher means closer. The Proximity Alert now compares on this scale, and its threshold moved to the **Proximity Signal Threshold** number entity (default 80%). A stored dBm threshold is migrated automatically.
> 3. **The list-management services were renamed and merged.** `add_known_ssid` → `add_ssid`, `remove_known_ssid` → `remove_ssid`, `set_known_ssids` → `set_ssids`, each now taking a required `target: known | denylist` (and `set_known_ssids`'s `known_ssids` field is now `values`). **There are no aliases** — automations calling the old names will fail. Update them, including any copied from the guest-network example below.
> 4. **Four settings moved out of the Configure dialog** and are now entities on the device page: **Scan Interval**, **Include Hidden Networks**, and the band filter (now three **Show 2.4/5/6 GHz** switches). The old `scan_bands` option is migrated.

## 📋 Table of Contents

- [WiFi SSID Monitor for Home Assistant](#wifi-ssid-monitor-for-home-assistant)
  - [📋 Table of Contents](#-table-of-contents)
  - [🔧 Compatibility \& Requirements](#-compatibility--requirements)
  - [🎯 Use Cases](#-use-cases)
  - [✅ Features](#-features)
  - [🔍 What You Get](#-what-you-get)
  - [📸 Screenshots](#-screenshots)
  - [📡 Unknown Network Detection](#-unknown-network-detection)
  - [💡 Example Automations](#-example-automations)
  - [📥 Installation](#-installation)
  - [🔧 Configuration](#-configuration)
  - [🧹 Actions (Services)](#-actions-services)
  - [🔩 Under the Hood - Technical Architecture](#-under-the-hood---technical-architecture)
  - [❓ FAQ \& Troubleshooting](#-faq--troubleshooting)
  - [❗ Known Limitations /❔ What's Missing?](#-known-limitations--whats-missing)
  - [❌ Removal](#-removal)
  - [📝 Maintenance Status](#-maintenance-status)
  - [🤝 Contributors \& Acknowledgements](#-contributors--acknowledgements)
  - [📄 License](#-license)

## 🔧 Compatibility & Requirements

**💻 Tested Hardware:**

- **Fully Tested**: Home Assistant OS (HAOS) on **Raspberry Pi 4** and **Intel (standard x86) Mini PC** with compatible physical WiFi hardware.

**🌐 Network & System:**

- Local network access and a **Home Assistant OS (HAOS)** or **Supervised** installation is required to access the Supervisor Network API.
- WiFi must be enabled under **Settings > System > Network**.

**🏠 Home Assistant Version:**

- Minimum: Home Assistant **2024.8.0**
- Minimum Python: **3.12+** (this is built into and handled by HA, but relevant for non-standard installs).

## 🎯 Use Cases

- **Security Monitoring (Rogue Network Detection)**: Monitor for unexpected WiFi networks in your environment that could indicate unauthorized access points or security threats. Get alerted instantly when unrecognized SSIDs are broadcast in range.
- **Device Management (Smart Device Setup Detection)**: Identify when smart home devices enter pairing or recovery mode (broadcasting their own setup APs) due to a fresh installation or an unexpected reset.
- **Network Uptime (Known Network Monitoring)**: Track whether your own home networks remain online. Get notified if one of your personal access points stops broadcasting or goes offline.
- **Dynamic Performance Tuning**: Automatically lower the scan frequency during high-traffic or evening hours and speed it up during security cycles to minimize system load.

## ✅ Features

### 📡 Network Scanning & Detection

- **Real-time SSID Scanning**: Count all detectable WiFi networks in range and view full SSID lists with signal quality and frequency band in sensor attributes.
- **Unknown Network Detection**: Identify networks not in your known list, with wildcard pattern matching (e.g., `Guest_*`) for flexible filtering.
- **Proximity Alert**: A binary sensor fires when an unknown network's signal quality exceeds a configurable threshold, indicating a nearby rogue AP.
- **Auto-detected Interface**: WiFi interfaces (e.g., `wlan0`) are automatically populated during setup where available.

### 🧰 Filtering & History

- **Band Filter**: Independently show or hide 2.4 GHz, 5 GHz, and 6 GHz networks via three switches, to reduce noise from neighboring networks.
- **SSID Denylist**: Mark specific SSID patterns as permanently unknown — useful for neighbor networks that should never be whitelisted.
- **Hidden Network Control**: Toggle whether un-broadcasted (hidden) SSIDs are counted or silently ignored.
- **Last Seen Tracking**: Each unknown SSID records when it was last detected, first detected, and how many times it has appeared — all persisted across Home Assistant restarts with a configurable keep time.

### 🔄 Dynamic Polling

- **Dynamic Polling Control**: Adjust the scan frequency (1–180 minutes) from the HA UI or via automations.
- **On-Demand Scan**: Trigger an immediate scan at any time using the **Scan Now** button entity or the `wifi_ssid_monitor.scan_now` service — no need to wait for the next interval.

> [!TIP]
>
> **Scan interval can be controlled dynamically, via automation**
>
> - Lower it (e.g. 1–5 minutes) during security sweeps or when you want faster rogue-AP detection, and raise it afterwards to reduce system load.

### 🔌 Service API

- **Service API**: Six callable services cover the full management lifecycle — add, remove, or replace the known **and** denylist, query live networks (`get_networks`), trigger on-demand scans, and clear history. See [Actions (Services)](#-actions-services) for full parameters and examples.

## 🔍 What You Get

This integration provides its 18 entities under a single **WiFi SSID Monitor** device — sensors, binary sensors, numbers, switches, and a button, all enabled by default.

| Category / Entity Type | Enabled / Total | Description & Key Metrics |
| :-- | :-: | :-- |
| 📊 **Sensors** | 7 / 7 | Total Count, Unknown Count, New 24h, Interface, Last Updated, Strongest Unknown SSID & Signal |
| 🔐 **Binary Sensors** | 3 / 3 | New Network Alert, Proximity Alert, Integration Health |
| 🔢 **Number Entities** | 2 / 2 | Scan Interval (1–180 min), Proximity Signal Threshold (0–100%) |
| 🔘 **Switch Entities** | 5 / 5 | Pause Polling, Include Hidden Networks, Show 2.4 / 5 / 6 GHz |
| 🔘 **Button Entities** | 1 / 1 | Scan Now |
| **Total Base Install** | **18 / 18** | Complete integration entity set |

> [!TIP]
>
> **Not sure what a sensor does?** Many entities carry a short built-in **About** note. Click the entity, open the **⋮ (three-dots) menu → Details** (More Info), and look for the **`about`** attribute — a one-line explanation of that entity.
>
> These **About** notes — and the bulky per-network detail on **Strongest Unknown SSID** — are set **unrecorded**. Home Assistant still shows them live in the entity's details, but **never writes them to the history/recorder database**. That keeps informational or high-churn values from bloating your database, with no downside to what you see day-to-day.

<details>

<summary>
&nbsp; &nbsp; ➕ &nbsp; &nbsp; Click to Expand for the full entity breakdown:
</summary><br>

---

### 📊 Sensors

| Entity | Type | Description |
| :-- | :-- | :-- |
| `sensor.wifi_ssid_monitor_total_ssid_count` | Measurement | Total number of detected WiFi networks |
| `sensor.wifi_ssid_monitor_unknown_ssid_count` | Measurement | Count of networks not in your known list |
| `sensor.wifi_ssid_monitor_last_updated` | Diagnostic | Timestamp of the last successful WiFi scan |
| `sensor.wifi_ssid_monitor_interface` | Diagnostic | Name of the monitored WiFi interface |
| `sensor.wifi_ssid_monitor_new_networks_24h` | Measurement | Networks first seen by this integration in the last 24 hours |
| `sensor.wifi_ssid_monitor_strongest_unknown_ssid` | Diagnostic | SSID name of the closest unknown network (highest signal); reads `None Detected` when no unknown networks are visible. Carries the per-network detail attributes |
| `sensor.wifi_ssid_monitor_strongest_unknown_signal` | Measurement | Signal quality of the closest unknown network (0–100%, higher is closer); `unknown` when no unknown networks are visible |

> [!NOTE]
>
> **Signal is a 0–100% quality figure, not dBm.** The Supervisor reports signal as a percentage; earlier versions used dBm. Higher means a stronger, closer signal. See the upgrade warning at the top of this page if you are upgrading.

**Attributes:** The detail for each unknown network lives on **Strongest Unknown SSID**, as a `networks` list capped at the 25 strongest (with `networks_truncated: true` when more exist — use the `get_networks` action for the full set). Each entry carries `ssid`, `bssid`, `signal`, `channel`, `band`, `hidden`, `ssid_anomaly`, `first_seen`, `last_seen` and `visit_count`. The count sensors additionally expose a plain `ssids` list. All of these attributes are excluded from the recorder.

### 🔐 Binary Sensors

| Entity | Description |
| :-- | :-- |
| `binary_sensor.wifi_ssid_monitor_new_network_alert` | On when unknown networks are detected; Off when all detected networks are known |
| `binary_sensor.wifi_ssid_monitor_proximity_alert` | On when an unknown network's signal meets or exceeds the configured threshold |
| `binary_sensor.wifi_ssid_monitor_integration_health` | On when the integration detects a problem with its own data — an unreachable Supervisor, a changed payload, or all known networks vanishing at once. Always available, even during an outage; detail is in the `issues` attribute |

The `proximity_alert` sensor exposes `strongest_unknown_signal` (0–100% of the closest unknown network) and `threshold` (the configured limit) as state attributes.

### 🔢 Number Entities

| Entity | Default | Description |
| :-- | :-- | :-- |
| `number.wifi_ssid_monitor_scan_interval` | 10 min | Scan interval (1–180 minutes). This is now the only place the interval is set |
| `number.wifi_ssid_monitor_proximity_signal_threshold` | 80% | Signal quality (0–100%) at which the Proximity Alert fires; higher requires a closer network |

### 🔘 Switch Entities

| Entity | Default | Description |
| :-- | :-- | :-- |
| `switch.wifi_ssid_monitor_pause_polling` | Off | Pauses scheduled scans. Explicit actions (Scan Now, a control change, the `scan_now` service) still fetch |
| `switch.wifi_ssid_monitor_include_hidden_networks` | On | Include networks that do not broadcast a name |
| `switch.wifi_ssid_monitor_show_2_4_ghz` | On | Include 2.4 GHz networks in all counts and lists |
| `switch.wifi_ssid_monitor_show_5_ghz` | On | Include 5 GHz networks in all counts and lists |
| `switch.wifi_ssid_monitor_show_6_ghz` | On | Include 6 GHz (WiFi 6E/7) networks in all counts and lists |

> [!NOTE]
>
> **Turning every band switch off shows no networks**, not all of them. Leave at least one band on.

### 🔘 Button Entities

| Entity | Description |
| :-- | :-- |
| `button.wifi_ssid_monitor_scan_now` | Triggers an immediate on-demand WiFi scan, even while Pause Polling is on |

### 📣 Bus Events

The integration fires a `wifi_ssid_monitor_new_network` event on the Home Assistant event bus each time a **genuinely new** network is seen for the first time. Unlike the `new_network_alert` binary sensor (which is simply on/off while any unknown network is present), this event fires once **per network** and survives restarts — the existing set is recorded silently on the first scan after start or a history reset, so a restart never replays the backlog. Emission is rate-limited to 10 events per scan cycle (any excess is counted and logged, never silently dropped).

Payload fields:

| Field | Description |
| :-- | :-- |
| `entry_id` | The config entry that saw the network |
| `key` | Stable history key (the SSID, or `hidden:<bssid>` for a cloaked network) |
| `ssid` | Display name (`Hidden-<last 4 of BSSID>` for a cloaked network) |
| `bssid` | Access point MAC, where reported |
| `band` | `2.4 GHz` / `5 GHz` / `6 GHz`, or `null` if undetermined |
| `channel` | WiFi channel, where derivable |
| `signal` | Signal quality 0–100% |
| `hidden` | `true` if the network does not broadcast a name |
| `ssid_anomaly` | `true` if the name is hidden or contains control/zero-width/RTL characters |
| `mode` | Reported AP mode, where present |
| `first_seen` | ISO timestamp this integration first saw the network |

```yaml
alias: "Alert on Any New WiFi Network"
triggers:
  - trigger: event
    event_type: wifi_ssid_monitor_new_network
actions:
  - action: persistent_notification.create
    data:
      message: >
        New WiFi network seen: {{ trigger.event.data.ssid }} ({{ trigger.event.data.band }}, {{ trigger.event.data.signal }}%)
```

### 📊 Long Term Statistics (LTS)

Home Assistant stores Long Term Statistics for numeric sensors that have a `state_class` set. This integration enables LTS for sensors where tracking trend data is useful:

| Sensors with LTS enabled | Why |
| :-- | :-- |
| `sensor.wifi_ssid_monitor_total_ssid_count` | Track WiFi network density trends over time |
| `sensor.wifi_ssid_monitor_unknown_ssid_count` | Monitor for unrecognized network spikes in your environment |
| `sensor.wifi_ssid_monitor_strongest_unknown_signal` | Monitor signal-quality trends of nearby unknown networks |
| `sensor.wifi_ssid_monitor_new_networks_24h` | Track the rate at which new networks appear |

The remaining sensors (text, timestamp, non-measurement) do not get added to LTS based on Home Assistant design.

---

</details>

<br>

## 📸 Screenshots

<details>

<summary>
&nbsp; &nbsp; ➕ &nbsp; &nbsp; Click to Expand for Integration Screenshots:
</summary><br>

<table width="100%">
  <tr>
    <td colspan="2" align="center" valign="top">
      <strong>Integration Overview</strong><br><br>
      <img src=".github/images/wifi_ssid_mon_integration_screen.png" alt="Integration Overview" width="60%">
    </td>
  </tr>
  <tr>
    <td align="center" valign="top" width="50%">
      <strong>Sensor Entities</strong><br><br>
      <img src=".github/images/wifi_ssid_mon_sensors_screen.png" alt="Sensor Entities" width="75%">
    </td>
    <td align="center" valign="top" width="50%">
      <strong>Setup</strong><br><br>
      <img src=".github/images/wifi_ssid_mon_setup_screen.png" alt="Setup" width="88%">
    </td>
  </tr>
  <tr>
    <td colspan="2" align="center" valign="top">
      <strong>Network Interface Configuration</strong><br><br>
      <img src=".github/images/wlan_name_sys_netw.png" alt="Network Interface Configuration" width="40%">
    </td>
  </tr>
</table>

---

</details>

## 📡 Unknown Network Detection

Detecting **unknown** WiFi networks — SSIDs in range that are not on your known list — is the core of this integration. Every scan compares what the interface can see against your known list and denylist, and surfaces the rest as "unknown". That catches an "evil twin" AP imitating your SSID, a device broadcasting its own setup network after a factory reset, or simply a new neighbor's router appearing nearby.

<details>

<summary>
&nbsp; &nbsp; ➕ &nbsp; &nbsp; Click to Expand for Details:
</summary><br>

**Sensors & alert:**

- **Unknown SSID Count (`sensor.wifi_ssid_monitor_unknown_ssid_count`)**: Count of networks in range that don't match your Known SSIDs list (plus any on the denylist), after your band and hidden-network filters.
- **Strongest Unknown SSID (`sensor.wifi_ssid_monitor_strongest_unknown_ssid`)**: The name of the closest unknown network by signal; reads `None Detected` when nothing unknown is in range.
  - _Attributes_: a `networks` list (the strongest, up to 25 listed) with each network's `ssid`, `bssid`, `signal` (0–100%), `channel`, `band`, `hidden`, `ssid_anomaly`, `first_seen`, `last_seen`, and `visit_count`. `networks_truncated: true` flags if the list was capped — use the `get_networks` action for the complete set.
- **Strongest Unknown Signal (`sensor.wifi_ssid_monitor_strongest_unknown_signal`)**: The signal quality (0–100%, higher is closer) of the strongest unknown network; `unknown` when nothing unknown is visible.
- **New Networks (24h) (`sensor.wifi_ssid_monitor_new_networks_24h`)**: Count of networks this integration first saw within a rolling 24 hours (LTS-enabled for trends).
- **Proximity Alert (`binary_sensor.wifi_ssid_monitor_proximity_alert`)**: A `PROBLEM` binary sensor that turns `on` when the strongest unknown network's signal is **at or above** your **Proximity Signal Threshold** (e.g. 90% is closer/stronger than 80%).

**Hidden & spoofed networks:**

- **Individual hidden naming**: A network that does not broadcast a name is identified from its BSSID as `Hidden-<last 4 hex>` (e.g. `Hidden-A2D3`), so distinct cloaked APs stay distinguishable instead of collapsing into one entry. Only an AP that reports no BSSID at all falls back to a shared `[hidden]` label.
- **Anomaly flag**: `ssid_anomaly` is set when a name is hidden **or** contains control, zero-width, or right-to-left characters — the toolkit for making one network's name render identically to another's. Those characters are replaced with a visible `·` marker so the difference is apparent rather than invisible.

**Tuning (control entities on the device page):**

- **Show 2.4 / 5 / 6 GHz** (`switch`) — include or drop each band from all counts and lists.
- **Include Hidden Networks** (`switch`) — count un-broadcast networks or ignore them entirely.
- **Proximity Signal Threshold** (`number`, 0–100%) — the "nearby" cut-off; raise it to require a closer network before the alert fires.

The **Known SSIDs** and **Always-Unknown (denylist)** lists are set in **Configure** (or via the `add_ssid` / `remove_ssid` / `set_ssids` actions). Both accept `fnmatch` wildcards and can match either the SSID or the BSSID. See [Runtime Options](#-runtime-options).

**On-demand & automations:**

- **`get_networks` action** — query the current network set on demand with your own scope / band / signal / keyword / exclude filters (see [Actions](#-actions-services)).
- **`wifi_ssid_monitor_new_network` event** — fires once per genuinely-new network, for triggering automations (see [Events](#-events)).

### 🕒 Network appearance history

For each network, the integration keeps a small persisted record — `first_seen` (when HA first tracked it), `last_seen`, and `visit_count` (scan cycles seen) — pruned by the **Last Seen History TTL** option (default 90 days) plus a hard safety cap. It powers the `first_seen` / `visit_count` fields on the `get_networks` response and the per-network detail attributes, and the **New Networks (24h)** sensor.

**Caveats:** `first_seen` is "first seen by _Home Assistant_", not by your hardware — on first install everything counts as new for 24 h. And devices using randomized MAC addresses can make **hidden** entries churn. Use `clear_last_seen` to reset.

### 📘 How to use it

1. Look at the typical signal levels of your neighbors' WiFi in the **Strongest Unknown SSID** attributes or via `get_networks`. _(Before you add them to your denylist, this is a good way to gauge what "nearby" signal levels look like in your setup.)_
2. Set your **Proximity Signal Threshold** slightly above that normal background level (e.g. if neighbors sit around 40–50%, set the threshold to 70–80%).
3. Optionally narrow the noise: add known-friendly SSIDs to the **denylist**, or turn off a band you don't care about.
4. Set up an automation to notify you when the **Proximity Alert** turns `on`, or trigger on the `wifi_ssid_monitor_new_network` event (see the examples below).

---

</details>

<br>

## 💡 Example Automations

> [!NOTE]
>
> Entity IDs are derived from your integration/device name (e.g. `sensor.wifi_ssid_monitor_...`) and **may differ between installs**, or if you have renamed entities. Use the entity picker in the Automation editor rather than copying the IDs below verbatim. The examples are illustrative.

---

> [!NOTE]
>
> Use your own preferred Automation notifier

<details>

<summary>&nbsp; &nbsp; &nbsp; &nbsp; ➕ &nbsp; Click to Expand for Notification Options:

</summary>

<br>

Replace

```yaml
action: persistent_notification.create
```

with

```yaml
action: notify.send_message
target:
  entity_id: notify.your_specific_phone
```

---

</details>

### 🔒 Security & Detection Automations

#### 🚨 Rogue Network Detection Alert

<details>

<summary> &nbsp; &nbsp; Notify when an unknown network is detected.<br>
&nbsp; &nbsp; &nbsp; &nbsp; ➕ &nbsp; Click to Expand for Automation Detail:

</summary><br>

```yaml
alias: "Alert on Rogue WiFi Network"
triggers:
  - trigger: state
    entity_id: binary_sensor.wifi_ssid_monitor_new_network_alert
    to: "on"
actions:
  - action: persistent_notification.create
    data:
      message: |
        Unknown WiFi network detected: {{ states('sensor.wifi_ssid_monitor_unknown_ssid_count') }} unknown network(s) found
```

---

</details>

#### 📡 Proximity Alert Notification

<details>

<summary> &nbsp; &nbsp; Alert when an unknown network is detected unusually close (signal at/above your threshold).<br>
&nbsp; &nbsp; &nbsp; &nbsp; ➕ &nbsp; Click to Expand for Automation Detail:

</summary><br>

```yaml
alias: "Alert on Nearby Unknown WiFi"
description: "Fires when an unknown network signal exceeds the proximity threshold"
triggers:
  - trigger: state
    entity_id: binary_sensor.wifi_ssid_monitor_proximity_alert
    to: "on"
actions:
  - action: persistent_notification.create
    data:
      message: |
        Unknown WiFi detected nearby! Signal: {{ state_attr('binary_sensor.wifi_ssid_monitor_proximity_alert', 'strongest_unknown_signal') }}%. Networks: {{ state_attr('sensor.wifi_ssid_monitor_unknown_ssid_count', 'ssids') | join(', ') }}
```

---

</details>

#### 📟 Smart Device Setup Detection

<details>

<summary> &nbsp; &nbsp; Detect when a smart home device enters access point (pairing) mode.<br>
&nbsp; &nbsp; &nbsp; &nbsp; ➕ &nbsp; Click to Expand for Automation Detail:

</summary><br>

```yaml
alias: Alert if Device in AP Mode
triggers:
  - trigger: state
    entity_id: binary_sensor.wifi_ssid_monitor_new_network_alert
    to: "on"
conditions:
  - condition: template
    alias: Check If Unknown SSID Is a Known Smart Device
    value_template: |
      {% set ssids = state_attr('sensor.wifi_ssid_monitor_unknown_ssid_count', 'ssids') | string | lower %}
      {% set device_aps = ['mfg1_new', 'mfg2_resets', 'mfg3'] | map('lower') | list %}
      {{ device_aps | select('in', ssids) | list | length > 0 }}
actions:
  - action: persistent_notification.create
    data:
      message: |
        Smart Device in AP Mode Detected: {{ states('sensor.wifi_ssid_monitor_unknown_ssid_count') }} APs found.
```

---

</details>

#### 🌐 Home WiFi Offline Alert

<details>

<summary> &nbsp; &nbsp; Monitor whether one of your own networks has stopped broadcasting.<br>
&nbsp; &nbsp; &nbsp; &nbsp; ➕ &nbsp; Click to Expand for Automation Detail:

</summary><br>

```yaml
alias: "Alert if Home WiFi Offline"
triggers:
  - trigger: numeric_state
    entity_id: sensor.wifi_ssid_monitor_total_ssid_count
    below: 2
    for:
      minutes: 5
conditions:
  - condition: state
    entity_id: binary_sensor.wifi_ssid_monitor_new_network_alert
    state: "off"
actions:
  - action: persistent_notification.create
    data:
      message: "WiFi network count has dropped — a home network may be offline"
```

---

</details>

### 🔄 Polling & Scanning Automations

#### 🔄 Dynamic Polling Control

<details>

<summary> &nbsp; &nbsp; Automatically adjust the scan frequency between day and evening hours.<br>
&nbsp; &nbsp; &nbsp; &nbsp; ➕ &nbsp; Click to Expand for Automation Detail:

</summary><br>

```yaml
alias: "WiFi: Set Scan Interval Based on Time"
description: "Adjusts SSID scan interval for day and evening cycles"
mode: single
triggers:
  - trigger: time
    at: "08:00:00"
    id: "day"
  - trigger: time
    at: "18:00:00"
    id: "evening"
actions:
  - choose:
      - conditions:
          - condition: trigger
            id: "day"
        sequence:
          - action: number.set_value
            target:
              entity_id: number.wifi_ssid_monitor_scan_interval
            data:
              value: 10
      - conditions:
          - condition: trigger
            id: "evening"
        sequence:
          - action: number.set_value
            target:
              entity_id: number.wifi_ssid_monitor_scan_interval
            data:
              value: 20
```

---

</details>

#### 🔍 Security Scan on Arrival

<details>

<summary> &nbsp; &nbsp; Trigger an immediate scan the moment someone arrives home.<br>
&nbsp; &nbsp; &nbsp; &nbsp; ➕ &nbsp; Click to Expand for Automation Detail:

</summary><br>

```yaml
alias: "WiFi: Scan on Arrival"
description: "Runs an on-demand WiFi scan when someone arrives home"
triggers:
  - trigger: state
    entity_id: person.your_name
    to: "home"
actions:
  - action: button.press
    target:
      entity_id: button.wifi_ssid_monitor_scan_now
```

---

</details>

### 🧹 List & History Management Automations

#### 🔀 Dynamic Guest Network Whitelisting

<details>

<summary> &nbsp; &nbsp; Whitelist a guest network when its switch turns on, and remove it when it turns off.<br>
&nbsp; &nbsp; &nbsp; &nbsp; ➕ &nbsp; Click to Expand for Automation Detail:

</summary><br>

```yaml
alias: "WiFi: Manage Guest Network Whitelist"
description: "Dynamically updates known networks when Guest WiFi status changes"
mode: single
triggers:
  - trigger: state
    entity_id: switch.router_guest_wifi
actions:
  - choose:
      - conditions:
          - condition: state
            entity_id: switch.router_guest_wifi
            state: "on"
        sequence:
          - action: wifi_ssid_monitor.add_ssid
            data:
              ssid: "MyGuestWiFi_*"
              target: known
      - conditions:
          - condition: state
            entity_id: switch.router_guest_wifi
            state: "off"
        sequence:
          - action: wifi_ssid_monitor.remove_ssid
            data:
              ssid: "MyGuestWiFi_*"
              target: known
```

---

</details>

#### 🧹 Weekly History Cleanup

<details>

<summary> &nbsp; &nbsp; Prune the persistent scan history once a week.<br>
&nbsp; &nbsp; &nbsp; &nbsp; ➕ &nbsp; Click to Expand for Automation Detail:

</summary><br>

Prevents the list of temporary, one-off unknown SSIDs from growing too large.

```yaml
alias: "WiFi: Weekly History Reset"
description: "Clears persistent last-seen, first-seen, and visit-count history weekly"
triggers:
  - trigger: time
    at: "00:00:00"
conditions:
  - condition: time
    weekday:
      - sun
actions:
  - action: wifi_ssid_monitor.clear_last_seen
```

---

</details>

## 📥 Installation

### ✨ HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=PlayFaster&repository=ha-wifi-ssid-monitor&category=integration)

Use the **shortcut badge** above, then proceed to Step 3 — or just …

1. Add this [repository](https://github.com/PlayFaster/ha-wifi-ssid-monitor) as a **Custom Repository** in HACS:
   - Open HACS in Home Assistant
   - Click **Custom repositories** (⋮ menu)
   - Add repository URL and Type: `Integration`
2. Search for "WiFi SSID Monitor" and click **Download**
3. Restart Home Assistant
4. Go to **Settings > Devices & Services > Add Integration** and search for "WiFi SSID Monitor"

### 💾 Manual Installation

1. Download the [latest release](https://github.com/PlayFaster/ha-wifi-ssid-monitor/releases).
2. Copy the `custom_components/wifi_ssid_monitor` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant
4. Go to **Settings > Devices & Services > Add Integration** and search for "WiFi SSID Monitor"

### 🔄 Updating

Standard HACS custom-repository integration update behavior:

<details>

<summary>
&nbsp; &nbsp; ➕ &nbsp; &nbsp; Click to Expand for Details:
</summary><br>

- New releases show up in **HACS** as normal. Update there, then restart Home Assistant.
- For manual installs: replace the `custom_components/wifi_ssid_monitor` folder and restart.
- Your settings and entity customizations carry over — Configure options, renamed entities, enabled/disabled choices, and dashboards.
- Any new entities in a release appear on the first restart after updating.

> [!NOTE]
>
> **Upgrading from 1.6.x?** See the breaking-changes warning at the top of this page — the strongest-unknown sensor, the proximity threshold, the band filter, and the list-management services all changed. Update any affected dashboards and automations.

---

</details>
<br>

## 🔧 Configuration

### 🔧 Initial Setup

Setup is handled entirely via the UI under **Settings > Devices & Services > Add Integration**.

- **WiFi Interface** (required) — The network interface to monitor (e.g., `wlan0`). Auto-populated where available.
- **Known SSIDs** — Comma-separated list of WiFi networks to treat as known (e.g., `Home-WiFi, Guest-Network`).
- **Integration Name** — Display name shown in the UI for this integration instance (default: `WiFi SSID Monitor`).

### 🔨 Runtime Options

After setup, settings can be updated by clicking **Configure** on the integration card:

| Parameter | Default | Range | Description |
| :-- | :-- | :-- | :-- |
| **Integration Name** | `WiFi SSID Monitor` | String | Display name shown in the UI for this integration instance. |
| **Known SSIDs** | — | String | Comma-separated list of known networks. Wildcards supported (e.g., `Guest_*`). Case-sensitive. |
| **Always-Unknown SSIDs** | — | String | Comma-separated fnmatch patterns permanently treated as unknown, even if they also match an entry in the known list. Useful for flagging neighbor networks that should never be whitelisted. |
| **WiFi Interface** | `wlan0` | String | Change which WiFi interface is monitored. |
| **Last Seen History TTL** | `90` | 0–366 days | Number of days to retain `last_seen`, `first_seen`, and `visit_counts` history entries. Set to `0` to keep all history indefinitely. |

> [!NOTE]
>
> **Scan Interval, Band Filter, Include Hidden Networks and Proximity Threshold are control entities now — not fields in this dialog.** They live on the device page as switches and numbers so they can be changed from a dashboard or an automation without reopening Configure. See the **Runtime Controls & Settings** below for the full list.

### 🔘 Runtime Controls & Settings (Entities)

Several settings are exposed as control entities so you can drive them from dashboards or automations, rather than reopening Configure:

- **Pause Polling** (`switch`) — halt scheduled scanning temporarily. Manual actions (Scan Now, a control change, `scan_now`) still fetch while paused.
- **Scan Interval** (`number`) — minutes between scheduled scans (1–180, default 10). This is the only place the interval is set.
- **Proximity Signal Threshold** (`number`) — signal quality (0–100%) at or above which an unknown network trips the Proximity Alert (default 80%).
- **Include Hidden Networks** (`switch`) — count un-broadcast networks or ignore them entirely (default on).
- **Show 2.4 GHz / Show 5 GHz / Show 6 GHz** (`switch` × 3) — include or drop each band from all counts and lists (all default on).
- **Scan Now** (`button`) — an immediate on-demand scan (works even while Pause Polling is on).

Changing any of these applies **immediately** — even while Pause Polling is on, an explicit change triggers a fresh scan (a bare scan-interval change just re-arms the timer).

---

> [!TIP]
>
> **Finding Your WiFi Interface Name:**
>
> 1. In Home Assistant, go to **Settings > System > Network**.
> 2. Check **Configure network interfaces**.
> 3. Your WiFi interface will typically be listed as `wlan0`, `wlan1`, `wlp2s0`, or similar.

### 🔧 Explaining the Configuration Options

#### 1. Wildcard SSID Matching (Known & Always-Unknown)

SSID matching supports standard shell wildcards (`fnmatch` patterns):

- `*` — Matches anything, including an empty string (e.g., `Guest_*` matches `Guest_Home` and `Guest_`).
- `?` — Matches any single character (e.g., `IoT_?` matches `IoT_1` but not `IoT_12`).
- `[seq]` — Matches any character in the sequence (e.g., `Home_[12]` matches `Home_1` and `Home_2`).

#### 2. Proximity Alert Threshold & Signal Quality

The Supervisor reports signal as a **0–100% quality figure**, and the Proximity Threshold is set on the same scale. Higher is closer:

- **90–100%** (Very Strong) — The broadcasting device is extremely close, likely in the same room.
- **70–90%** (Strong/Medium) — Nearby, typically within the home or property boundary (default threshold: 80%).
- **40–70%** (Weak) — Moderately distant, such as a neighbor's network or a device out on the street.
- **0–40%** (Very Weak) — At the edge of detection.

Raise the threshold if the alert is noisy in a dense WiFi environment; lower it to catch more distant networks.

#### 3. Last Seen History TTL

The integration keeps track of how often and when unknown networks are seen:

- `first_seen` — Timestamp of the very first scan cycle the SSID was detected.
- `last_seen` — Timestamp of the most recent scan cycle the SSID was detected.
- `visit_counts` — Total number of scan cycles in which the SSID has appeared. To prevent storage bloat, any SSID that has not been seen for longer than the TTL window is pruned automatically from history on the next scan. Setting this to `0` disables pruning.

## 🧹 Actions (Services)

All actions accept an optional `config_entry_id` to target a specific integration entry. Leave it blank to apply to all configured entries.

The list-management services take a `target` of `known` or `denylist`, so the same three actions manage both lists.

| Action / Service | Type | Description |
| :-- | :-: | :-- |
| `wifi_ssid_monitor.add_ssid` | Command | Adds an SSID or pattern to the known or denylist; triggers an immediate re-scan |
| `wifi_ssid_monitor.remove_ssid` | Command | Removes an SSID or pattern from the known or denylist; triggers a re-scan if the list changes |
| `wifi_ssid_monitor.set_ssids` | Response | Replaces the entire known or denylist; returns the new and previous lists as response data |
| `wifi_ssid_monitor.scan_now` | Command | Triggers an immediate WiFi scan, even while Pause Polling is on |
| `wifi_ssid_monitor.clear_last_seen` | Command | Clears all `last_seen`, `first_seen`, and `visit_counts` history |
| `wifi_ssid_monitor.get_networks` | Response | Returns the current networks with signal and history, filtered and sorted — a response action |

---

### `add_ssid` / `remove_ssid`

| Parameter         |  Type  | Required | Description                                  |
| :---------------- | :----: | :------: | :------------------------------------------- |
| `ssid`            | String | **Yes**  | SSID or pattern to add/remove                |
| `target`          |  Enum  | **Yes**  | `known` or `denylist`                        |
| `config_entry_id` | String |    No    | Target a specific entry; blank = all entries |

```yaml
action: wifi_ssid_monitor.add_ssid
data:
  ssid: "MyHomeNetwork"
  target: known
```

---

### `set_ssids`

Replaces the entire known **or** denylist in one call. Returns the new and previous lists per entry for undo/audit capabilities.

| Parameter | Type | Required | Description |
| :-- | :-: | :-: | :-- |
| `values` | String | **Yes** | Comma-separated SSIDs and patterns — replaces the target list entirely |
| `target` | Enum | **Yes** | `known` or `denylist` |
| `config_entry_id` | String | No | Target a specific entry; blank = all entries |

```yaml
action: wifi_ssid_monitor.set_ssids
response_variable: result
data:
  values: "Home-WiFi, Guest_*"
  target: known
```

---

### `scan_now` / `clear_last_seen`

Both take only the optional `config_entry_id`. `scan_now` fetches even while Pause Polling is on; `clear_last_seen` clears all three history stores.

---

### `get_networks`

Returns the currently visible networks with their signal and history, filtered and sorted by signal. Reads live scan data directly, so it works even when the passive sensors are unavailable or their attribute list is capped.

> [!TIP]
>
> **Instant Diagnostic Inspection**: You can run `wifi_ssid_monitor.get_networks` directly from **Developer Tools > Actions** in the Home Assistant UI to inspect live network data immediately without creating an automation.

| Parameter | Type | Required | Description |
| :-- | :-: | :-: | :-- |
| `scope` | Enum | No | `unknown` (default), `known`, or `all` |
| `band` | Enum | No | `2.4`, `5`, `6`, or `all` (default) |
| `min_signal` | Integer | No | Only include networks at or above this quality (0–100%) |
| `quantity` | Integer | No | Maximum to return (default 50, max 500) |
| `keyword` / `exclude` | String | No | Comma-separated include/exclude terms |
| `config_entry_id` | String | No | Target a specific entry; blank = all entries |

```yaml
action: wifi_ssid_monitor.get_networks
response_variable: result
data:
  scope: unknown
  min_signal: 60
```

The response carries `networks` (the capped list), `count`, and `total_matched` (the true match count before the `quantity` cap).

### 📨 Events

Alongside the actions, the integration fires a bus event you can use as an automation trigger. It fires **once** per newly-seen network, records the existing set silently on startup or after a history reset (no replay), and is rate-limited to 10 per scan cycle.

| Event type | Fires when | `trigger.event.data` fields |
| :-- | :-- | :-- |
| `wifi_ssid_monitor_new_network` | A network is seen for the first time | `entry_id`, `key`, `ssid`, `bssid`, `band`, `channel`, `signal`, `hidden`, `ssid_anomaly`, `mode`, `first_seen` |

Full field descriptions and a worked example are in [Bus Events](#-bus-events) under _What You Get_.

## 🔩 Under the Hood - Technical Architecture

Details on how this custom component is structured — the Supervisor API and payload normalization, actions and events, self-diagnosis, data polling and resilience, entity identity, and the files it writes.

<details>

<summary>
&nbsp; &nbsp; ➕ &nbsp; &nbsp; Click to Expand for Details:
</summary><br>

### 🎬 Actions & Events (for automations)

Beyond passive entities, the integration exposes an on-demand **action** and a fire-and-forget **event**:

- **Action** (`get_networks`) is a response service — it performs its own fresh read of the current scan and returns data, so it works even when the passive sensors are unavailable, filtered, or capped. See [Actions](#-actions-services).
- **Event** (`wifi_ssid_monitor_new_network`) fires once per newly-seen network. It records the existing set silently on startup or after a history reset (no replay), and is rate-limited so a busy location cannot flood your automations. See [Events](#-events).

### 🩺 Self-diagnosis (Integration Health)

Some failures are **silent** — a scan succeeds but the data is wrong (e.g. a Supervisor update renames a field, or reports signal in a different unit). The **Integration Health** sensor (a `problem` binary sensor, always available even during an outage) watches for these:

- **`on`** when the integration detects a problem with its own data — an unreachable Supervisor, a payload that parsed to nothing, an interface that vanished, a signal-unit change, or every known network disappearing at once.
- **Repair issues** are raised for the few conditions you can act on: **`interface_missing`** (the monitored interface is no longer reported — reconfigure to pick the right one), **`signal_format_changed`** (the Supervisor changed how it reports signal — review the Proximity Threshold), and **`supervisor_unavailable`** (repeated fetch failures).

It's deliberately cautious: it gives startup grace before judging drift, requires a condition to persist over several cycles before flipping, and auto-recovers on the next clean scan. Details — `issues`, `severity`, `checks_failed`, `signal_unit`, `last_good_scan` — live in the sensor's attributes; put it on a dashboard or alert on it to catch breakage early instead of months later.

### 🔄 Data Polling & 3-Strike Resilience 🩹

The integration utilizes a custom polling mechanism designed to interact with the Home Assistant Supervisor Network API:

- **Supervisor Endpoint**: Polls the endpoint `/network/interface/{interface}/accesspoints` to gather access point configurations.
- **3-Strike Logic**: To prevent entities flickering to `Unavailable` due to temporary network congestion or Supervisor latency, the integration holds its last known values for up to 3 consecutive failures. If the 4th consecutive poll fails, the entities are marked `Unavailable` and an issue is raised in the Home Assistant repairs center.
- **Immediate Refresh**: Updating filter or pattern lists triggers an immediate background scan. You can also trigger an immediate scan at any time by pressing the **Scan Now** button entity or by calling the `wifi_ssid_monitor.scan_now` service. (Changing the scan interval updates the timer without forcing an immediate fetch; Pause Polling halts polling without forcing a fetch.)

### 🆔 Stable Entities & Interface Identity

- **Interface-Based Identity**: The integration registers its unique ID based on `wifi_ssid_monitor_{interface}`. This prevents duplicate configurations for the same interface and ensures entity history remains stable.
- **Data Validation & Normalization Boundary**: Values retrieved from the Supervisor API pass through a single parsing boundary (`parse.py`). Signal is normalized to a 0–100% quality scale, frequencies are mapped to channels and 2.4/5/6 GHz bands, and out-of-bounds metrics are safely clamped.

### 💾 Files Written to `config/.storage`

The integration persists three history stores across restarts using `homeassistant.helpers.storage`. All three are written per config entry, so a setup monitoring two interfaces has two sets. Writes are coalesced (not one write per scan) to spare SD cards.

| File | Holds | Classification | Cost of deletion |
| :-- | :-- | :-- | :-- |
| `wifi_ssid_monitor.<entry_id>.last_seen` | When each network was last detected | **Derived cache** | None — repopulates on the next scan |
| `wifi_ssid_monitor.<entry_id>.first_seen` | When each network was first detected | **User history** | Permanent — first-seen dates are lost |
| `wifi_ssid_monitor.<entry_id>.visit_counts` | How many scans each network has appeared in | **User history** | Permanent — appearance counts reset; **New Networks (24h)** re-baselines |

Entries older than the **Last Seen History TTL** (default 90 days) are pruned automatically, and a hard cap bounds total growth in a busy location. Set TTL to `0` to retain indefinitely. All three are **deleted automatically** when the integration is removed — see [Removal](#-removal).

> 💡 To clear history deliberately, use the **`wifi_ssid_monitor.clear_last_seen`** action rather than deleting a file by hand — it does the same job cleanly while Home Assistant is running. Editing or deleting anything in `.storage` should be done with Home Assistant **stopped**.

### 🔄 Dynamic Polling & Standard System Options

- **Both Available**: The integration provides dynamic polling controls, to change the scan interval or trigger an on-demand scan. It also functions normally with the standard Home Assistant **System options** > **Enable polling for changes** toggle.

---

</details>

<br>

## ❓ FAQ & Troubleshooting

### 🔌 Setup & Connectivity

#### 🔌 **Integration Fails to Load ("Failed to connect to Supervisor API")**

<details>

<summary>
&nbsp; &nbsp; ➕ &nbsp; &nbsp; Click to Expand for Details:
</summary><br>

- **WiFi hardware unavailable**: Verify your Home Assistant system has physical WiFi capabilities enabled under **Settings > System > Network**.
- **Invalid interface**: Ensure the interface name is correct and configured on your host OS.
- **Not a HAOS / Supervised install**: The Supervisor Network API is only available on Home Assistant OS or Supervised installations — not on Container or Core.

---

</details>

#### ❔ **No Networks Detected (count reads zero)**

<details>

<summary>
&nbsp; &nbsp; ➕ &nbsp; &nbsp; Click to Expand for Details:
</summary><br>

- Verify the interface name is correct for your system under **Settings > System > Network**.
- Ensure WiFi is enabled and the interface is active.
- Check that networks are actively broadcasting in range of the system.
- Check the **Integration Health** binary sensor — its `issues` attribute names what it detected (e.g. a missing interface).
- Review the Home Assistant logs for detailed error messages.

---

</details>

### 📊 Detection, Signals & History

#### 📶 **Proximity Alert Fires Too Often**

<details>

<summary>
&nbsp; &nbsp; ➕ &nbsp; &nbsp; Click to Expand for Details:
</summary><br>

- **Threshold is too permissive**: raise **Proximity Signal Threshold** (the number entity) toward 90% to require a closer network before the alert fires — signal is a 0–100% quality figure, higher is closer.
- **Persistent unknown networks in range**: call `wifi_ssid_monitor.get_networks` or check the `networks` attribute on **Strongest Unknown SSID** to see which network is triggering it, then decide whether to add it to the Known SSIDs list.

---

</details>

#### ❔ **Fewer Networks Detected Than Expected**

<details>

<summary>
&nbsp; &nbsp; ➕ &nbsp; &nbsp; Click to Expand for Details:
</summary><br>

- The number of WiFi networks this integration can detect depends heavily on the **physical location of your Home Assistant hardware**.
- A system placed centrally in an open area of your home will typically see most networks in range, including expected SSIDs and any rogue signals.
- A system tucked into a metal IT rack, a utility cupboard, or a corner of your home may see significantly fewer networks — metal enclosures and walls attenuate WiFi signals and can reduce scan coverage substantially.

---

</details>

#### 🎯 **Known SSID Pattern Not Matching**

<details>

<summary>
&nbsp; &nbsp; ➕ &nbsp; &nbsp; Click to Expand for Details:
</summary><br>

- **Case mismatch**: Pattern matching is case-sensitive. Verify the pattern casing exactly matches the SSID (e.g., `Guest_*` will not match `guest_wifi`).
- **Missing wildcard**: A plain string is treated as an exact match. Use `Guest_*` or `*guest*` for partial matches.
- **Trailing spaces**: The Known SSIDs field strips leading/trailing whitespace from each entry, but double-check there are no invisible characters.

---

</details>

#### 🕒 **History Contains Stale or Unexpected Entries**

<details>

<summary>
&nbsp; &nbsp; ➕ &nbsp; &nbsp; Click to Expand for Details:
</summary><br>

The `first_seen` / `last_seen` / `visit_count` fields (on **Strongest Unknown SSID** and the `get_networks` response) may hold entries for networks not seen recently, or grow larger than expected.

- **Automatic TTL pruning**: entries older than the **Last Seen History TTL** (default 90 days) are pruned on the next scan. Adjust it in **Configure**, or set `0` to keep all entries indefinitely.
- **Manual reset**: call the `wifi_ssid_monitor.clear_last_seen` action from **Developer Tools > Actions** to clear all three history stores immediately (for the targeted entry, or all entries if `config_entry_id` is omitted).

---

</details>

### 🧰 Troubleshooting Tips

#### 🐛 **How do I download diagnostics?**

<details>

<summary>
&nbsp; &nbsp; ➕ &nbsp; &nbsp; Click to Expand for Details:
</summary><br>

**Settings > Devices & Services > WiFi SSID Monitor > ⋮ (three dots) > Download diagnostics.**

This is the most useful file to attach to a GitHub issue. It captures your options, the current scan data, and the network history in one JSON file.

**It is sanitized before it is written**, so it is safe to share:

- **Your own lists are redacted outright** — the Known SSIDs and Always-Unknown (denylist) values.
- **Everything identifying about nearby networks is pseudonymized**, not blanked. Each SSID becomes `ssid-1`, `ssid-2`… and each BSSID becomes `bssid-1`, `bssid-2`… The same network keeps the same token everywhere it appears — including where an SSID is used as a dictionary key — so the file still reads sensibly.
- **What deliberately stays:** signal quality, channel, band, counts, timestamps, and health flags — the non-identifying substance a maintainer needs.

Nearby-network detections describe **other people's** equipment, which is why the SSID is tokenized and the BSSID redacted.

---

**If setup itself is failing**, there is no config entry yet, so there are no diagnostics to download. In that case capture a log instead — add this to `configuration.yaml` and restart:

```yaml
logger:
  default: warning
  logs:
    custom_components.wifi_ssid_monitor: debug
```

Logs are then visible under **Settings > System > Logs** (click **Load Full Logs**).

> [!IMPORTANT]
>
> **Log files have NO redaction of any kind** — unlike the diagnostics file above, nothing is stripped or pseudonymized. Review a log before pasting it anywhere. In particular, at debug level the raw Supervisor access-point sample (including nearby SSIDs and BSSIDs) can appear in the log.

---

</details>

#### 🔄 **I deleted and re-added the integration — why did my settings and history come back?**

<details>

<summary>
&nbsp; &nbsp; ➕ &nbsp; &nbsp; Click to Expand for Details:
</summary><br>

Because Home Assistant keeps most of it on purpose. This is **Home Assistant behavior, not something this integration controls**, and for most people it's the desirable outcome — re-add the same interface and things carry on where they left off.

| What | How long Home Assistant keeps it | On re-add |
| :-- | :-- | :-- |
| **Long-term statistics** (long-range graphs) | Indefinitely — never deleted | Continue unbroken |
| **Recent detailed history** | Recorder retention (10 days by default) | Continues |
| **Entity IDs** (`sensor.…`) | Reused as long as nothing else took the name | Dashboards & automations keep working |
| Renames, icons, areas, labels, enabled/disabled state | **30 days**, in the entity registry | Restored |
| **Network history** (this integration's `.storage` files) | Not kept — deleted with the integration | Starts fresh |

The **30 days** applies only to that fourth row. Statistics aren't on a timer at all, and your entity IDs come back either way. Only this integration's own `first_seen` / `visit_count` history is genuinely lost — **New Networks (24h)** rebaselines.

> [!TIP]
>
> If you're re-adding to fix a problem rather than to reset data, try **⋮ > Reload** on the integration first — it re-reads everything and re-applies your settings without removing anything.

---

</details>

## ❗ Known Limitations /❔ What's Missing?

- **Hidden Networks (No Broadcasted SSID)**: hidden APs are identified individually as `Hidden-<last 4 of BSSID>` where the Supervisor reports a BSSID, so multiple hidden networks in range are counted and tracked separately. Only an AP that reports no BSSID at all falls back to a shared `[hidden]` label. Disable hidden tracking entirely with the **Include Hidden Networks** switch. Note that phones and laptops using randomized MAC addresses can cause hidden entries to churn.
- **Strongest Unknown Signal Returns "unknown" When No Unknown Networks Visible**: `sensor.wifi_ssid_monitor_strongest_unknown_signal` returns `unknown` when nothing unknown is in range — normal and expected, not a fault (a fault shows as `unavailable`). The companion **Strongest Unknown SSID** reads `None Detected` in the same situation, which is the "all clear" state, not an error.
- **Pattern Matching is Case-Sensitive**: Known SSID patterns (including wildcards like `Guest_*`) are matched case-sensitively. `homewifi` and `HomeWiFi` are treated as different networks — make sure your patterns match the exact casing of the SSIDs you want to filter.

## ❌ Removal

To remove the integration from Home Assistant:

<details>

<summary>
&nbsp; &nbsp; ➕ &nbsp; &nbsp; Click to Expand for Details:
</summary><br>

1. Go to **Settings > Devices & Services**.
2. Find the **WiFi SSID Monitor** card and click into it.
3. Click the **three dots** (⋮) next to the gear icon and select **Delete**.
4. Confirm deletion.

To fully uninstall (HACS):

1. Go to **HACS**.
2. Find the **WiFi SSID Monitor** and click into it.
3. Click the **three dots** (⋮) at the top right and select **Remove**.
4. Restart Home Assistant.

**What deletion removes, and what it keeps:**

- The integration's three [`.storage` history files](#-files-written-to-configstorage) (`last_seen`, `first_seen`, `visit_counts`) are **deleted automatically** on removal. `first_seen` dates and `visit_counts` are **user history and cannot be recovered** — if you may re-add the integration and want them, export them first via `get_networks`. `last_seen` is a cache and simply repopulates.
- Home Assistant does **not** immediately discard the entities and device. It retains them in `deleted_entities`/`deleted_devices` for **30 days** and restores their names, entity IDs, enabled state, area and options if you re-add the same interface within that window. State history ages out on the recorder's `purge_keep_days` (default 10), and **long-term statistics are never purged automatically** — old LTS shows as `no_state` in **Developer Tools > Statistics** and is removed only by hand there. See [why settings and history come back](#-i-deleted-and-re-added-the-integration--why-did-my-settings-and-history-come-back) for the full picture.

---

</details>

<br>

## 📝 Maintenance Status

This is a **personal project**. Support and updates are provided on a **"best-effort"** basis only. While I use this integration daily and aim to keep it functional with the latest Home Assistant releases, I cannot guarantee immediate fixes for issues or compatibility with all releases.

## 🤝 Contributors & Acknowledgements

- **Personal prior work**: The structure and integration architecture draw on my own custom components [ZTE Router 5G](https://github.com/PlayFaster/ha-zte-router-5g-monitor) and [Huawei Router 5G](https://github.com/PlayFaster/ha-huawei-router-5g-monitor) Monitors.

- This project was developed with the assistance of AI to ensure code quality and adherence to best practices.

## 📄 License

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

This project is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.

---

💬 **Questions or Issues?** Visit the [GitHub repository](https://github.com/PlayFaster/ha-wifi-ssid-monitor).
