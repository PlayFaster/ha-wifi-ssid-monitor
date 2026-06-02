# WiFi SSID Monitor for Home Assistant

[![HACS Integration](https://img.shields.io/badge/HACS-Integration-orange.svg)](https://hacs.xyz/) [![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5?logo=homeassistant&logoColor=white)](https://hacs.xyz/docs/faq/custom_repositories) [![Latest Release](https://img.shields.io/github/v/release/PlayFaster/ha-wifi-ssid-monitor?label=Release&logo=github)](https://github.com/PlayFaster/ha-wifi-ssid-monitor/releases) [![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0) [![Validate](https://github.com/PlayFaster/ha-wifi-ssid-monitor/actions/workflows/validate.yaml/badge.svg)](https://github.com/PlayFaster/ha-wifi-ssid-monitor/actions/workflows/validate.yaml) ![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/PlayFaster/6d1d30e996dd53f04d2c2fc6b6cddece/raw/coverage.json) [![Last Commit](https://img.shields.io/github/last-commit/PlayFaster/ha-wifi-ssid-monitor?label=Last%20commit)](https://github.com/PlayFaster/ha-wifi-ssid-monitor/commits/main)

A Home Assistant integration that monitors and reports on WiFi networks in your environment using the Home Assistant Supervisor API.

> [!NOTE]
>
> **Is this the right integration for you?**
>
> - **If you want to monitor WiFi networks** in your vicinity, track connection uptime, or detect rogue/unauthorized access points, then **yes**.
> - **This integration is for you if** you want:
>   - **Rogue AP Detection** — Count detectable networks and alert on unknown SSIDs.
>   - **Smart Device Setup Tracking** — Identify when new devices enter pairing/AP mode.
>   - **Dynamic Polling** — Change scan intervals directly from the Home Assistant UI or via automations.
>
> Requires a Home Assistant Supervised or HAOS installation with physical WiFi hardware. The Supervisor API is not available on container or core installations.

## 🔧 Compatibility & Requirements

**💻 Tested Hardware:**

- **Fully Tested**: Home Assistant OS (HAOS) on **Raspberry Pi 4** and **Intel (standard x86) Mini PC** with compatible WiFi hardware.

**🌐 Network & System:**

- Local network access and a **Home Assistant OS (HAOS)** or **Supervised** installation is required to access the Supervisor Network API.
- WiFi must be enabled under **Settings > System > Network**.

**🏠 Home Assistant Version:**

- Minimum: Home Assistant **2024.1.0**
- Minimum Python: **3.12+**

## 🎯 Use Cases

- **Security Monitoring (Rogue Network Detection)**: Monitor for unexpected WiFi networks in your environment that could indicate unauthorized access points or security threats. Get alerted instantly when unrecognized SSIDs are broadcast in range.
- **Device Management (Smart Device Setup Detection)**: Identify when smart home devices enter pairing or recovery mode (broadcasting their own setup APs) due to a fresh installation or an unexpected reset.
- **Network Uptime (Known Network Monitoring)**: Track whether your own home networks remain online. Get notified if one of your personal access points stops broadcasting or goes offline.
- **Dynamic Performance Tuning**: Automatically lower the scan frequency during high-traffic or evening hours and speed it up during security cycles to minimize system load.

## ✅ Features

- **Real-time SSID Scanning**: Count all detectable WiFi networks in range.
- **Unknown Network Detection**: Identify networks not in your pre-configured known list.
- **Detailed Attributes**: View complete lists of detected and unknown SSIDs inside sensor attributes.
- **Dynamic Polling Control**: Adjust the scan frequency (1–180 minutes) from the HA UI or via automations.
- **Auto-detected Interface**: WiFi interfaces (e.g., `wlan0`) are automatically populated during setup where available. This can be entered manually if auto-detection is not successful.

## 🔍 What You Get

This integration provides **6 entities** (all enabled by default) organized under a single WiFi SSID Monitor device.

### Sensors

| Entity | Type | Description |
| --- | --- | --- |
| `sensor.wifi_ssid_monitor_total_ssid_count` | Measurement | Total number of detected WiFi networks |
| `sensor.wifi_ssid_monitor_unknown_ssid_count` | Measurement | Count of networks not in your known list |
| `sensor.wifi_ssid_monitor_last_updated` | Diagnostic | Timestamp of the last successful WiFi scan |
| `sensor.wifi_ssid_monitor_interface` | Diagnostic | Name of the monitored WiFi interface |

**Attributes:** The total and unknown count sensors include SSID attributes:

- `ssids`: List of all detected (`total`) or unknown (`unknown`) network names.

### Binary Sensors

| Entity | Description |
| --- | --- |
| `binary_sensor.wifi_ssid_monitor_new_network_alert` | On when unknown networks are detected; Off when all detected networks are known |

### Number Entities

| Entity                                   | Description                               |
| ---------------------------------------- | ----------------------------------------- |
| `number.wifi_ssid_monitor_scan_interval` | Adjustable scan frequency (1–180 minutes) |

### 📊 Long Term Statistics (LTS)

Home Assistant stores Long Term Statistics for numeric sensors that have a `state_class` set. This integration enables LTS for sensors where tracking trend data is useful:

| Sensors with LTS enabled | Why |
| :-- | :-- |
| `sensor.wifi_ssid_monitor_total_ssid_count` | Track WiFi network density trends over time |
| `sensor.wifi_ssid_monitor_unknown_ssid_count` | Monitor for unrecognized network spikes in your environment |

The following diagnostic sensors have **no LTS** to avoid unnecessary database growth:

- `sensor.wifi_ssid_monitor_interface` (Text diagnostic)
- `sensor.wifi_ssid_monitor_last_updated` (Timestamp diagnostic)

## 💡 Example Automations

### 🚨 Rogue Network Detection Alert

This automation fires when an unknown network is detected and sends a notification to your mobile phone.

```yaml
alias: "Alert on Rogue WiFi Network"
triggers:
  trigger: state
  entity_id: binary_sensor.wifi_ssid_monitor_new_network_alert
  to: "on"
actions:
  action: notify.mobile_app_phone
  data:
    message: "Unknown WiFi network detected: {{ states('sensor.wifi_ssid_monitor_unknown_ssid_count') }} unknown network(s) found"
```

### 📟 Smart Device Setup Detection

Detect when a smart home device enters access point (pairing) mode.

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
      {% set device_aps = ['mfg1_new', 'mfg2_resets', 'mfg3'] | lower %}
      {{ device_aps | select('in', ssids) | list | length > 0 }}
actions:
  - action: notify.mobile_app_phone
    data:
      message: |
        Smart Device in AP Mode Detected: {{ states('sensor.wifi_ssid_monitor_unknown_ssid_count') }} APs found.
```

### 🌐 Home WiFi Offline Alert

Monitor whether one of your own networks has stopped broadcasting.

```yaml
alias: "Alert if Home WiFi Offline"
triggers:
  trigger: numeric_state
  entity_id: sensor.wifi_ssid_monitor_total_ssid_count
  below: 2
  for:
    minutes: 5
conditions:
  - condition: state
    entity_id: binary_sensor.wifi_ssid_monitor_new_network_alert
    state: "off"
actions:
  - action: notify.mobile_app_phone
    data:
      message: "WiFi network count has dropped — a home network may be offline"
```

### ⏯️ Dynamic Polling Control

Automatically adjust the scan frequency between day and evening hours.

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

## 📸 Screenshots

| Integration Overview | Sensor Entities |
| :-: | :-: |
| ![Integration Overview](.github/images/wifi_ssid_mon_integration_screen.png) | ![Sensor Entities](.github/images/wifi_ssid_mon_sensors_screen.png) |

| Setup | Network Interface Configuration |
| :-: | :-: |
| ![Setup](.github/images/wifi_ssid_mon_setup_screen.png) | ![Interface Configuration](.github/images/wlan_name_sys_netw.png) |

## 📥 Installation

### ✨ HACS (Recommended)

1. Add this repository as a **Custom Repository** in HACS:
   - Open HACS in Home Assistant
   - Click **Custom repositories** (⋮ menu)
   - Add repository URL and Type: `Integration`
2. Search for "WiFi SSID Monitor" and click **Download**
3. Restart Home Assistant
4. Go to **Settings > Devices & Services > Add Integration** and search for "WiFi SSID Monitor"

### 💾 Manual Installation

1. Download the repository
2. Copy the `custom_components/wifi_ssid_monitor` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant
4. Go to **Settings > Devices & Services > Add Integration** and search for "WiFi SSID Monitor"

## ⚙️ Configuration

### 🔧 Initial Setup

Setup is handled entirely via the UI under **Settings > Devices & Services > Add Integration**.

| Parameter | Required | Description |
| :-- | :-- | :-- |
| **WiFi Interface** | **Yes** | The network interface to monitor (e.g., `wlan0`). Autopopulated where available. |
| **Known SSIDs** | No | Comma-separated list of WiFi networks to treat as known (e.g., `Home-WiFi, Guest-Network`). |
| **Integration Name** | No | Display name shown in the UI for this integration instance (default: `WiFi SSID Monitor`). |

### 🛠️ Runtime Options

After setup, settings can be updated by clicking **Configure** on the integration card:

| Parameter | Default | Range | Description |
| :-- | :-- | :-- | :-- |
| **Known SSIDs** | — | String | Update the comma-separated list of known networks. |
| **Scan Interval** | `600` | 60–10800s | Adjust polling frequency (in seconds; equivalent to 1–180 minutes). |
| **WiFi Interface** | `wlan0` | String | Change which WiFi interface is monitored. |

> [!TIP]
>
> **Finding Your WiFi Interface Name:**
>
> 1. In Home Assistant, go to **Settings > System > Network**.
> 2. Check **Configure network interfaces**.
> 3. Your WiFi interface will typically be listed as `wlan0`, `wlan1`, `wlp2s0`, or similar.

## 🏗️ Under the Hood - Technical Architecture

### 🔄 Polling & 3-Strike Resilience 🩹

The integration utilizes a custom polling mechanism designed to interact with the Home Assistant Supervisor Network API:

- **Supervisor Endpoint**: Polls the endpoint `/network/interface/{interface}/accesspoints` to gather access point configurations.
- **3-Strike Logic**: To prevent entities flickering to `Unavailable` due to temporary network congestion or Supervisor latency, the integration holds its last known values for up to 3 consecutive failures. If the 4th consecutive poll fails, the entities are marked `Unavailable` and an issue is raised in the Home Assistant repairs center.
- **Immediate Refresh**: Updating the **Known SSIDs** list via the configuration options menu triggers an immediate background scan, bypassing the scheduled timer. (Changing the scan interval only updates the timer, it does not trigger an immediate scan).

### 🆔 Stable Entities & Reconfiguration

- **Interface-Based Identity**: The integration registers its unique ID based on `wifi_ssid_monitor_{interface}`. This prevents duplicate configurations for the same interface and ensures entity history remains stable.
- **Data Validation**: Values retrieved from the Supervisor API are run through guard validations. Out-of-bounds metrics (e.g., total count exceeding 256) are filtered to prevent database corruption.

## ❓ FAQ & Troubleshooting

### Integration Fails to Load

**Issue:** "Failed to connect to Supervisor API" or similar errors.

**Causes & Solutions:**

- **WiFi hardware unavailable**: Verify your Home Assistant system has physical WiFi capabilities enabled under **Settings > System > Network**.
- **Invalid interface**: Ensure the interface name is correct and configured on your host OS.

### No Networks Detected

- Verify the interface name is correct for your system.
- Ensure WiFi is enabled in **Settings > System > Network**.
- Check that networks are actively broadcasting in range of the system.
- Review the Home Assistant logs for detailed error messages.

## 🗑️ Removal

To remove the integration from Home Assistant:

1. Go to **Settings > Devices & Services**.
2. Find the **WiFi SSID Monitor** card and click into it.
3. Click the **three dots** (⋮) next to the gear icon and select **Delete**.
4. Confirm deletion.

To fully uninstall (HACS):

1. Go to **HACS > Integrations**.
2. Find the **WiFi SSID Monitor** and click into it.
3. Click the **three dots** (⋮) at the top right and select **Remove**.
4. Restart Home Assistant.

## ⚠️ Known Limitations /❔ What's Missing?

- **Hidden Networks (No Broadcasted SSID)**: WiFi access points that do not broadcast an SSID are grouped together as a single `[hidden]` entry in the network count and SSID lists. If multiple hidden networks are present in your area, the total count will reflect only one `[hidden]` entry regardless of how many physical hidden APs are detected. This is a limitation of the current implementation — hidden networks cannot be individually identified without SSID data.

## 📝 Maintenance Status

This is a **personal project**. Support and updates are provided on a **"best-effort"** basis only. While I use this integration daily and aim to keep it functional with the latest Home Assistant releases, I cannot guarantee immediate fixes for issues or compatibility with all releases.

## 🤝 Contributors & Acknowledgements

- This project was developed with the assistance of AI to ensure code quality and adherence to best practices.

## 📄 License [![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

This project is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.

---

💬 **Questions or Issues?** Visit the [GitHub repository](https://github.com/PlayFaster/ha-wifi-ssid-monitor).
