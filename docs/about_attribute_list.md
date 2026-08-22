# About Attributes — WiFi SSID Monitor 💡

<!-- GENERATED:start -->

| Entity | Platform | Key | Note |
| :-- | :-- | :-- | :-- |
| Proximity Signal Threshold | Number | `proximity_signal_threshold` | Signal quality at which the Proximity Alert fires, 0-100%. Higher means the network must be closer. Raise it if the alert is noisy. |
| Scan Interval | Number | `scan_interval` | How often a scheduled scan runs. |
| Total SSID Count | Sensor | `count` | Every network in range after your band and hidden-network filters. Unknown SSID Count is the subset not matching your known list. |
| Interface | Sensor | `interface` | The WiFi adapter being scanned, for example wlan0. Every count and list here is what this one adapter can see — a different adapter, or one moved elsewhere in the building, sees a different set. |
| New Networks (24h) | Sensor | `new_24h` | Networks first seen by this integration in the last 24 hours — not by your hardware. Resets if you clear the history. |
| Strongest Unknown Signal | Sensor | `strongest_unknown_signal` | Signal quality of the closest unknown network, 0-100%. Higher is closer. |
| Strongest Unknown SSID | Sensor | `strongest_unknown_ssid` | The closest unknown network by signal. Carries the per-network detail attributes. Reads 'None Detected' when nothing is in range. |
| Unknown SSID Count | Sensor | `unknown_count` | Networks in range that do not match your Known SSIDs list, plus any on the denylist. The per-network detail is on Strongest Unknown SSID. |
| Include Hidden Networks | Switch | `include_hidden` | Include networks that do not broadcast a name. Each is listed separately as Hidden-<last 4 of BSSID> where the BSSID is known. |
| Show 2.4 GHz | Switch | `show_24ghz` | Include 2.4 GHz networks in all counts and lists. Turning every band switch off shows no networks at all, not all of them. |
| Show 5 GHz | Switch | `show_5ghz` | Include 5 GHz networks in all counts and lists. Turning every band switch off shows no networks at all, not all of them. |
| Show 6 GHz | Switch | `show_6ghz` | Include 6 GHz (WiFi 6E/7) networks in all counts and lists. Turning every band switch off shows no networks at all, not all of them. |
| Pause Polling | Switch | `stop_polling` | Temporarily suspends background polling without disabling the integration. Entities hold their last values rather than going unavailable, and manual refresh actions still reach the device. |

## Entities without an `about` note (5)

The following entities carry no `about` attribute (self-explanatory or intentionally unannotated):

| Entity             | Platform      | Key                  | Group  |
| :----------------- | :------------ | :------------------- | :----- |
| Integration Health | Binary sensor | `integration_health` | System |
| New Network Alert  | Binary sensor | `new_network`        | System |
| Proximity Alert    | Binary sensor | `proximity_alert`    | System |
| Scan Now           | Button        | `scan_now`           | System |
| Last Updated       | Sensor        | `last_updated`       | System |

<!-- GENERATED:end -->
