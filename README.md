# WiFi SSID Monitor for Home Assistant

![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg) ![Latest Release](https://img.shields.io/github/v/release/PlayFaster/ha-wifi-ssid-monitor?label=Release&logo=github) [![Validate](https://github.com/PlayFaster/ha-wifi-ssid-monitor/actions/workflows/validate.yaml/badge.svg)](https://github.com/PlayFaster/ha-wifi-ssid-monitor/actions/workflows/validate.yaml) ![Last Commit](https://img.shields.io/github/last-commit/PlayFaster/ha-wifi-ssid-monitor?label=Last%20commit)

Home Assistant integration that uses the system's WiFi (via Supervisor API) to scan for SSIDs, count them, and identify unknown networks.

## ✅ Features

- **SSID Counting**: Real-time count of all detectable WiFi networks.
- **Unknown SSID Detection**: Identifies networks not in your pre-defined "known" list.
- **Detailed Attributes**: Lists all detected SSIDs and unknown SSIDs as sensor attributes.
- **Configurable Interface**: Specify which WiFi interface to use (e.g., `wlan0`).
- **Configurable Polling**: Adjust the refresh rate directly from the UI.

## ✨ Installation

### HACS

1. Add this URL as a **Custom Repository** in HACS.
2. Click Download.
3. Restart Home Assistant and add via the UI.

### Manual

1. Copy the `custom_components/wifi_ssid_monitor` folder to your Home Assistant `custom_components` directory.
2. Restart Home Assistant.
3. Go to **Settings > Devices & Services > Add Integration** and search for "WiFi SSID Monitor".

## Configuration

Setup is handled entirely via the UI. You can configure:

- **Wifi Interface**: The system interface to use (default: `wlan0`).
- **Known SSIDs**: A comma-separated list of WiFi network names you consider "known".

> [!TIP]
>
> 1. The name of the wifi interface can generally be found in **Settings > System > Network > Configure network interfaces**.
> 2. Known SSIDs can be changed at any time via the **Configure** (gear icon) button on the integration entry.

## 🛠 Maintenance Status

This is a **personal project**. Support and updates are provided on a **"best-effort"** basis only.

## Contributors & Acknowledgements

- This project was developed with the assistance of Gemini AI to ensure code quality and best practices.
