# Supervisor Scan Behavior: WiFi SSID Monitor

How the Home Assistant Supervisor answers the access-point scan that this integration polls, measured on two real hosts on 2026-10-01. The figures size the mock Supervisor in `.devcontainer/mock_supervisor.py` and record what a scan can and cannot be relied on to show. The tables carry counts, timings and signal tiers only. No SSID or BSSID from either host appears in this document.

---

## Method

The probe called `GET /network/interface/wlan0/accesspoints` back to back for 300 s on each host, with no pause between calls. The call went through the Home Assistant WebSocket `supervisor/api` command, which reaches the Supervisor with an administrator long-lived access token. Each call was timed and its result set hashed, and the response fields were recorded.

| Host | Hardware | Scans | Duration |
| :-- | :-- | --: | --: |
| 1 | Raspberry Pi 4 | 60, all successful | 298 s |
| 2 | Intel mini PC | 57, all successful | 295 s |

The probe script, its README and the raw results are in the project's `local_only/supervisor_scan_probe` notes folder. The results hold neighboring BSSIDs, so that folder is not committed.

---

## Scan latency

Every call performs a live scan. The Supervisor returns no cached result, so a call takes about 5 s whatever the polling interval.

| Measure | Host 1 (Raspberry Pi 4) | Host 2 (Intel mini PC) |
| :-- | :-- | :-- |
| Minimum | 5.02 s | 5.08 s |
| Median | 5.03 s | 5.10 s |
| Mean | 5.04 s | 5.27 s |
| Maximum | 5.69 s | 10.46 s |
| Calls over 6 s | 0 of 60 | 3 of 57 (6.06 s, 8.04 s and 10.46 s) |

One call in 117 took longer than 10 s, and it happened on host 2.

---

## How often the result changes

A result set is the list of access points a call returns. Two consecutive calls, 5 s apart, usually returned different sets.

| Measure | Host 1 (Raspberry Pi 4) | Host 2 (Intel mini PC) |
| :-- | :-- | :-- |
| Consecutive result sets that differed | 49 of 59 (83%) | 52 of 56 (93%) |
| Distinct result sets in the run | 33 of 60 | 50 of 57 |
| Access points per scan, minimum, median, maximum | 5, 5, 7 | 5, 8, 8 |
| Distinct radios seen, 2.4 GHz and 5 GHz | 3 and 4 | 6 and 2 |

---

## Presence by signal tier

A network is placed in a tier by its mean signal across the run, as a percentage of 0 to 100. Networks above 67 were present in every scan on both hosts. Every network below about 55 was intermittent.

| Tier | Mean signal | Host 1 (Raspberry Pi 4) | Host 2 (Intel mini PC) |
| :-- | :-- | :-- | :-- |
| Strong | above 67 | 5 networks, present in every scan | 5 networks, present in every scan |
| Medium | about 50 | none | 3 networks, all 2.4 GHz, present in 40, 46 and 48 of 57 scans (70%, 81% and 84%) |
| Weak | about 33 | 2 networks, both 5 GHz, present in 7 of 60 scans each (12%) | none |

The weak tier rests on one host and the medium tier on the other.

---

## Signal swing

The swing is the difference between the highest and lowest signal a network reported during the run.

| Measure | Host 1 (Raspberry Pi 4) | Host 2 (Intel mini PC) |
| :-- | :-- | :-- |
| Swing of the 5 strong networks, in points | 7, 7, 7, 7, 10 | 3, 3, 8, 8, 25 |
| Swing of the medium networks, in points | none | 4, 5, 7 |
| Change between consecutive scans of a strong network, median, 90th percentile, maximum | 0, 2, 7 | 0, 2, 22 |

---

## Response

- **Fields**: each access point carries `frequency` (MHz), `mac`, `mode`, `signal` and `ssid`, on both hosts. `signal` is a percentage.
- **Interfaces**: `wlan0` reports its type as `wireless` and `enabled: False` on both hosts, and the ethernet interface is `end0` on host 1 and `enp1s0` on host 2. The scan call returned results for `wlan0` although the interface reports `enabled: False`.
- **Access**: the `supervisor/api` WebSocket command reaches the Supervisor when the connection carries an administrator token.

---

## What this means for the integration

A scan is a point sample. A weak network can be absent from one scan and present in the next, and a medium network was absent from between 16% and 30% of scans on host 2. A count of unknown networks, `new_network` events and `last_seen` therefore move without any change in the surroundings, and a signal threshold sees swings of several points in a network that has not moved.

Networks above a signal of 67 were present in every scan on both hosts, and every network below about 55 was intermittent.

---

## Limits

- Two hosts, one location each, and about five minutes of scanning on each. The figures describe those runs and are not a distribution.
- The weak tier appears on host 1 only and the medium tier on host 2 only.
- Signal swing and presence depend on the surrounding radio environment and on the radio hardware, and a different location can differ.
- The latency spike is one call in 117, with two smaller delays of 6.06 s and 8.04 s on the same host.
