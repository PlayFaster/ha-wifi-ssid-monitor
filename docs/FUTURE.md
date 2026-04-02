# Future Roadmap: Wifi Scan SSID

This document outlines potential features and enhancements for the Wifi Scan SSID integration. These are suggestions intended to improve security, utility, and user experience.

## 1. Enhanced Data & Signal Metrics

- **Signal Strength (RSSI) Tracking**: Add sensors or attributes to monitor the strength of specific networks. This helps determine the physical proximity of "unknown" networks.
- **Frequency & Band Identification**: Expose whether a network is operating on the 2.4GHz or 5GHz band to assist in interference troubleshooting.
- **Channel Crowding Map**: Identify which WiFi channels are most congested in the local area to help optimize home router settings.

## 2. Smarter Identification Logic

- **BSSID (MAC Address) Support**: Track unique BSSIDs to prevent SSID spoofing and provide a more reliable "Known List."
- **Pattern Matching (Regex/Wildcards)**: Allow the "Known SSIDs" list to support patterns (e.g., `Guest_WiFi_*`) to automatically ignore transient networks following a naming convention.
- **Hidden Network Management**: Add a configuration toggle to explicitly include or exclude networks that do not broadcast their SSID.

## 3. Interactive UI & Automation

- **"Add to Known" Service**: Implement a Home Assistant service that allows users to instantly add a detected "Unknown" SSID to the known list via the UI or automations.
- **Manual Scan Button**: Add a `button` entity to trigger an immediate, on-demand scan regardless of the current interval.
- **"Last Seen" Tracking**: Maintain timestamps for each network to identify when they were last detected in the area.

## 4. Advanced Security & Alerts

- **"First Seen" Events**: Trigger a specific event the very first time a completely new hardware BSSID is detected.
- **Proximity Alerts**: A binary sensor that triggers if an unknown network's signal strength crosses a specific high-threshold (indicating it is very close or inside the premises).

## 5. System & Diagnostic Improvements

- **Multi-Interface Support**: Allow the integration to aggregate results from multiple WiFi cards (e.g., internal + USB) simultaneously.
- **Hardware Health Monitoring**: Add a diagnostic sensor to monitor the status of the WiFi adapter hardware and alert if it enters a stalled state.
- **System Role Attribute**: Re-integrate the "System Role" logic from the original script to provide more context on the scanning environment.
