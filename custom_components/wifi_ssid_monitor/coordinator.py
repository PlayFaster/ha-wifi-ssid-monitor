"""DataUpdateCoordinator for WiFi SSID Monitor integration."""

from __future__ import annotations

import asyncio
import fnmatch
import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import WifiScanAPI
from .const import (
    BAND_5,
    BAND_6,
    BAND_24,
    CANARY_MIN_VISITS,
    CONF_DENYLIST_SSIDS,
    CONF_INCLUDE_HIDDEN,
    CONF_KNOWN_SSIDS,
    CONF_LAST_SEEN_TTL_DAYS,
    CONF_SCAN_INTERVAL,
    CONF_SHOW_5GHZ,
    CONF_SHOW_6GHZ,
    CONF_SHOW_24GHZ,
    CONF_STOP_POLLING,
    DEFAULT_INCLUDE_HIDDEN,
    DEFAULT_LAST_SEEN_TTL_DAYS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SHOW_BAND,
    DEFAULT_STOP_POLLING,
    DOMAIN,
    EVENT_NEW_NETWORK,
    FETCH_STRIKE_LIMIT,
    HEALTH_DRIFT_STRIKE_LIMIT,
    HEALTH_STARTUP_GRACE_SCANS,
    HISTORY_MAX_ENTRIES,
    ISSUE_SUPERVISOR_UNAVAILABLE,
    NEW_NETWORK_EVENT_MAX_PER_CYCLE,
    STORAGE_VERSION,
    first_seen_storage_key,
    last_seen_storage_key,
    visit_counts_storage_key,
)
from .health import SEVERITY_SERIOUS, Finding, ScanFacts, run_checks
from .parse import (
    history_key,
    normalize_access_point,
    resolve_hidden_collisions,
)

_LOGGER = logging.getLogger(__name__)

_BAND_OPTION_KEYS = {
    BAND_24: CONF_SHOW_24GHZ,
    BAND_5: CONF_SHOW_5GHZ,
    BAND_6: CONF_SHOW_6GHZ,
}

# Stores are saved through async_delay_save rather than on every poll; a scan
# every 10 minutes writing three files is needless SD-card wear.
_SAVE_DELAY_SECONDS = 30


class WifiScanCoordinator(DataUpdateCoordinator):
    """Class to manage fetching WiFi SSID Monitor data."""

    _failure_count: int
    last_update_success_time: datetime | None

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, api: WifiScanAPI, version: str
    ) -> None:
        """Initialize the coordinator."""
        self.api = api
        self.entry = entry
        self.version = version
        self.last_known_ssids = entry.options.get(CONF_KNOWN_SSIDS, "")
        # Snapshot of the options seen at the last reload, so the update
        # listener can tell a live-tunable change from a structural one.
        self.last_reload_options: dict[str, Any] = dict(entry.options)
        self.last_update_success_time: datetime | None = None
        self._failure_count = 0
        self._last_seen: dict[str, datetime] = {}
        self._first_seen: dict[str, datetime] = {}
        self._visit_counts: dict[str, int] = {}

        self.store: Store[dict[str, str]] = Store(
            hass, version=STORAGE_VERSION, key=last_seen_storage_key(entry.entry_id)
        )
        self.store_first_seen: Store[dict[str, str]] = Store(
            hass, version=STORAGE_VERSION, key=first_seen_storage_key(entry.entry_id)
        )
        self.store_visit_counts: Store[dict[str, int]] = Store(
            hass, version=STORAGE_VERSION, key=visit_counts_storage_key(entry.entry_id)
        )

        # A one-shot flag set by every explicit user action. Without it, a
        # Refresh Now or a control change is silently swallowed while polling
        # is paused — exactly when the user most wants a fetch.
        self._force_refresh_once = False

        # Health state lives OUTSIDE self.data on purpose. `data` is None before
        # the first success and frozen at last-good values during an outage, so
        # a verdict held there cannot describe the failure that stopped it
        # being updated — it would keep asserting the last known state, which
        # was healthy.
        self.health_snapshot: dict[str, Any] = {
            "problem": False,
            "severity": None,
            "issues": [],
            "checks_failed": [],
            "signal_unit": None,
            "last_good_scan": None,
        }
        self._drift_strikes: dict[str, int] = {}
        self._baseline_signal_unit: str | None = None
        self._scans_completed = 0
        self._active_repairs: set[str] = set()

        # New-network events are baselined on the first poll so a restart never
        # replays the existing backlog into a user's automations.
        self._event_baseline_done = False

        scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{entry.title} Data",
            update_interval=timedelta(seconds=scan_interval),
        )

    # ---------------------------------------------------------------- storage

    async def async_initialize(self) -> None:
        """Load all persisted SSID history data from storage."""
        results = await asyncio.gather(
            self.store.async_load(),
            self.store_first_seen.async_load(),
            self.store_visit_counts.async_load(),
            return_exceptions=True,
        )

        last_seen_data, first_seen_data, visit_counts_data = results

        if isinstance(last_seen_data, BaseException):
            _LOGGER.warning(
                "Failed to load last_seen data; starting with empty history"
            )
        elif last_seen_data:
            self._last_seen = _parse_timestamps(last_seen_data)

        if isinstance(first_seen_data, BaseException):
            _LOGGER.warning(
                "Failed to load first_seen data; starting with empty history"
            )
        elif first_seen_data:
            self._first_seen = _parse_timestamps(first_seen_data)

        if isinstance(visit_counts_data, BaseException):
            _LOGGER.warning(
                "Failed to load visit_counts data; starting with empty history"
            )
        elif visit_counts_data:
            self._visit_counts = dict(visit_counts_data)

    def _schedule_save(self) -> None:
        """Queue a coalesced write of all three history stores."""
        self.store.async_delay_save(
            lambda: {k: v.isoformat() for k, v in self._last_seen.items()},
            _SAVE_DELAY_SECONDS,
        )
        self.store_first_seen.async_delay_save(
            lambda: {k: v.isoformat() for k, v in self._first_seen.items()},
            _SAVE_DELAY_SECONDS,
        )
        self.store_visit_counts.async_delay_save(
            lambda: dict(self._visit_counts), _SAVE_DELAY_SECONDS
        )

    async def async_flush_stores(self) -> None:
        """Write any pending delayed save immediately.

        Required on unload: a reload fires no HOMEASSISTANT_STOP, so a pending
        coalesced save would otherwise be lost on every options change.
        """
        await asyncio.gather(
            self.store.async_save(
                {k: v.isoformat() for k, v in self._last_seen.items()}
            ),
            self.store_first_seen.async_save(
                {k: v.isoformat() for k, v in self._first_seen.items()}
            ),
            self.store_visit_counts.async_save(dict(self._visit_counts)),
            return_exceptions=True,
        )

    async def async_clear_history(self) -> None:
        """Clear all persisted SSID history and save empty state to storage."""
        self._last_seen = {}
        self._first_seen = {}
        self._visit_counts = {}
        self._event_baseline_done = False
        await asyncio.gather(
            self.store.async_save({}),
            self.store_first_seen.async_save({}),
            self.store_visit_counts.async_save({}),
        )

    # ---------------------------------------------------------------- control

    async def async_force_refresh(self) -> None:
        """Fetch now, even if polling is paused.

        Scheduled polls still respect the pause; explicit user actions do not.
        """
        self._force_refresh_once = True
        await self.async_refresh()

    @property
    def polling_paused(self) -> bool:
        """Return whether the Pause Polling switch is on."""
        return bool(self.entry.options.get(CONF_STOP_POLLING, DEFAULT_STOP_POLLING))

    # ---------------------------------------------------------------- history

    @property
    def last_seen(self) -> dict[str, datetime]:
        """Return the last-seen history, keyed by network identity."""
        return self._last_seen

    @property
    def first_seen(self) -> dict[str, datetime]:
        """Return the first-seen history, keyed by network identity."""
        return self._first_seen

    @property
    def visit_counts(self) -> dict[str, int]:
        """Return the visit-count history, keyed by network identity."""
        return self._visit_counts

    def established_known_keys(self, known_patterns: list[str]) -> set[str]:
        """Return known networks seen often enough to expect them present.

        Derived from the visit-count history rather than a dedicated baseline
        store — a fourth `.storage` file would carry its own documentation and
        removal duties for information already recorded here.
        """
        return {
            key
            for key, count in self._visit_counts.items()
            if count >= CANARY_MIN_VISITS
            and any(fnmatch.fnmatch(key, p) for p in known_patterns)
        }

    def _prune_history(self, now: datetime, ttl_days: int) -> None:
        """Apply TTL expiry and the hard entry cap to all three histories."""
        if ttl_days > 0:
            cutoff = now - timedelta(days=ttl_days)
            expired = {k for k, t in self._last_seen.items() if t <= cutoff}
            self._drop_keys(expired)

        # A cap on top of the TTL bounds growth in a busy location, where a TTL
        # measured in months is no bound at all.
        overflow = len(self._last_seen) - HISTORY_MAX_ENTRIES
        if overflow > 0:
            oldest = sorted(self._last_seen, key=lambda k: self._last_seen[k])
            self._drop_keys(set(oldest[:overflow]))

    def _drop_keys(self, keys: set[str]) -> None:
        if not keys:
            return
        self._last_seen = {k: v for k, v in self._last_seen.items() if k not in keys}
        self._first_seen = {k: v for k, v in self._first_seen.items() if k not in keys}
        self._visit_counts = {
            k: v for k, v in self._visit_counts.items() if k not in keys
        }

    # ----------------------------------------------------------------- health

    def _record_fetch_failure_health(self, err: str) -> None:
        """Flag a total outage or missing interface on the health snapshot.

        Cold start flags immediately: there are no held values, so waiting out
        the strike budget would leave the user with an unexplained, wholly
        unavailable integration for up to three poll intervals. At runtime the
        strike budget applies, so a single blip raises no alarm.
        """
        cold_start = self.data is None
        if not cold_start and self._failure_count <= FETCH_STRIKE_LIMIT:
            return

        facts = ScanFacts(
            interface=self.api.interface,
            interface_present=self.api.last_interface_present,
            established_known=self.established_known_keys(
                _split_patterns(self.entry.options.get(CONF_KNOWN_SSIDS, ""))
            ),
            scans_completed=self._scans_completed,
        )
        try:
            findings = run_checks(facts)
        except Exception:  # noqa: BLE001
            findings = []

        if any(f.key == "interface_missing" for f in findings):
            self._apply_health(facts)
            return

        self.health_snapshot = {
            **self.health_snapshot,
            "problem": True,
            "severity": SEVERITY_SERIOUS,
            "issues": [f"Cannot reach the Supervisor API: {err}"],
            "checks_failed": ["supervisor_unreachable"],
            "cold_start": cold_start,
        }

    def _apply_health(self, facts: ScanFacts) -> None:
        """Run the checks and fold the result into the snapshot.

        Wrapped by the caller: a malformed payload must never crash the update
        this is meant to be diagnosing.
        """
        findings = run_checks(facts)

        # Startup grace: drift verdicts need a baseline to differ from.
        if self._scans_completed < HEALTH_STARTUP_GRACE_SCANS:
            findings = [f for f in findings if f.key == "interface_missing"]

        confirmed: list[Finding] = []
        for finding in findings:
            strikes = self._drift_strikes.get(finding.key, 0) + 1
            self._drift_strikes[finding.key] = strikes
            if strikes >= HEALTH_DRIFT_STRIKE_LIMIT:
                confirmed.append(finding)

        # A condition that stopped firing resets, so recovery is automatic.
        fired = {f.key for f in findings}
        for key in list(self._drift_strikes):
            if key not in fired:
                del self._drift_strikes[key]

        severity = None
        if confirmed:
            severity = (
                SEVERITY_SERIOUS
                if any(f.severity == SEVERITY_SERIOUS for f in confirmed)
                else confirmed[0].severity
            )

        self.health_snapshot = {
            "problem": bool(confirmed),
            "severity": severity,
            "issues": [f.message for f in confirmed],
            "checks_failed": [f.key for f in confirmed],
            "signal_unit": facts.signal_unit,
            "baseline_signal_unit": self._baseline_signal_unit,
            "last_good_scan": (
                self.last_update_success_time.isoformat()
                if self.last_update_success_time
                else None
            ),
            "networks_scanned": facts.total_aps,
        }
        self._sync_repairs(confirmed)

    def _sync_repairs(self, findings: list[Finding]) -> None:
        """Raise and clear the repair issues, keeping them to the actionable few."""
        wanted = {f.repair: f for f in findings if f.repair}

        for key, finding in wanted.items():
            if key in self._active_repairs:
                continue
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                key,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=key,
                translation_placeholders={"detail": finding.message},
            )
            self._active_repairs.add(key)

        for key in list(self._active_repairs - set(wanted)):
            ir.async_delete_issue(self.hass, DOMAIN, key)
            self._active_repairs.discard(key)

    # ------------------------------------------------------------------ fetch

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the API with resilience and timeout."""
        forced = self._force_refresh_once
        self._force_refresh_once = False

        if self.polling_paused and not forced and self.data is not None:
            _LOGGER.debug("Polling paused; returning cached data")
            cached: dict[str, Any] = self.data
            return cached

        try:
            async with asyncio.timeout(30):
                access_points = await self.api.get_access_points()
        except Exception as err:
            self._failure_count += 1
            self._record_fetch_failure_health(str(err))

            if self.data and self._failure_count <= FETCH_STRIKE_LIMIT:
                _LOGGER.warning(
                    "Error fetching WiFi data (failure %d/%d), "
                    "holding last known values: %s",
                    self._failure_count,
                    FETCH_STRIKE_LIMIT,
                    err,
                )
                held: dict[str, Any] = self.data
                return held

            _LOGGER.error("Failed to fetch WiFi networks: %s", err)
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                ISSUE_SUPERVISOR_UNAVAILABLE,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=ISSUE_SUPERVISOR_UNAVAILABLE,
            )
            if not self.data:
                raise ConfigEntryNotReady(
                    f"Error communicating with API: {err}"
                ) from err
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        # Success: reset the failure state and clear the outage repair.
        self._failure_count = 0
        now = dt_util.now()
        self.last_update_success_time = now
        ir.async_delete_issue(self.hass, DOMAIN, ISSUE_SUPERVISOR_UNAVAILABLE)

        return self._process_scan(access_points, now)

    def _process_scan(
        self, access_points: list[dict[str, Any]], now: datetime
    ) -> dict[str, Any]:
        """Normalize, filter, record history and build the data payload."""
        options = self.entry.options

        normalized = [normalize_access_point(ap) for ap in access_points]
        resolve_hidden_collisions(normalized)

        # Health runs on the *unfiltered* set: a filter hiding everything is a
        # thing to detect, not a thing to be blinded by.
        signal_units = {n["signal_unit"] for n in normalized if n["signal_unit"]}
        signal_unit = next(iter(signal_units)) if len(signal_units) == 1 else None

        include_hidden = options.get(CONF_INCLUDE_HIDDEN, DEFAULT_INCLUDE_HIDDEN)
        visible = [n for n in normalized if include_hidden or not n["hidden"]]
        visible = [n for n in visible if self._band_allowed(n["band"], options)]

        known_str = options.get(CONF_KNOWN_SSIDS, "")
        self.last_known_ssids = known_str
        known_patterns = _split_patterns(known_str)
        denylist_patterns = _split_patterns(options.get(CONF_DENYLIST_SSIDS, ""))

        network_map: dict[str, dict[str, Any]] = {}
        for net in visible:
            network_map[net["label"]] = {
                "bssid": net["mac"],
                "signal": net["signal_pct"],
                "signal_raw": net["signal_raw"],
                "channel": net["channel"],
                "band": net["band"],
                "hidden": net["hidden"],
                "ssid_anomaly": net["ssid_anomaly"],
                "mode": net["mode"],
                "key": history_key(net),
            }

        labels = sorted(network_map)
        seen_keys = {v["key"] for v in network_map.values()}

        new_keys = self._update_history(seen_keys, now)
        self._fire_new_network_events(new_keys, network_map)

        ttl_days = options.get(CONF_LAST_SEEN_TTL_DAYS, DEFAULT_LAST_SEEN_TTL_DAYS)
        self._prune_history(now, ttl_days)
        self._schedule_save()

        unknown_labels = sorted(
            label
            for label in labels
            if _is_unknown(
                network_map[label]["key"],
                network_map[label]["bssid"],
                known_patterns,
                denylist_patterns,
            )
        )

        strongest_label: str | None = None
        strongest_signal: int | None = None
        for label in unknown_labels:
            signal = network_map[label]["signal"]
            if signal is not None and (
                strongest_signal is None or signal > strongest_signal
            ):
                strongest_signal = signal
                strongest_label = label

        self._scans_completed += 1
        try:
            self._apply_health(
                ScanFacts(
                    total_aps=len(normalized),
                    normalized=normalized,
                    response_had_ap_key=self.api.last_response_had_ap_key,
                    interface=self.api.interface,
                    interface_present=self.api.last_interface_present,
                    signal_unit=signal_unit,
                    baseline_signal_unit=self._baseline_signal_unit,
                    established_known=self.established_known_keys(known_patterns),
                    seen_keys=seen_keys,
                    scans_completed=self._scans_completed,
                )
            )
        except Exception:  # noqa: BLE001 - diagnosis must never break the scan
            _LOGGER.debug(
                "Health computation failed; treating as healthy", exc_info=True
            )

        if signal_unit and self._baseline_signal_unit is None:
            self._baseline_signal_unit = signal_unit
        elif signal_unit and signal_unit != self._baseline_signal_unit:
            _LOGGER.info(
                "Supervisor signal unit changed from %s to %s",
                self._baseline_signal_unit,
                signal_unit,
            )
            self._baseline_signal_unit = signal_unit

        return {
            "count": len(labels),
            "ssids": labels,
            "unknown_ssids": unknown_labels,
            "unknown_count": len(unknown_labels),
            "interface": self.api.interface,
            "networks": network_map,
            "last_seen": dict(self._last_seen),
            "first_seen": dict(self._first_seen),
            "visit_counts": dict(self._visit_counts),
            "new_24h": self._count_new_within(now, hours=24),
            "strongest_unknown_signal": strongest_signal,
            "strongest_unknown_ssid": strongest_label,
            "signal_unit": signal_unit,
        }

    def _band_allowed(self, band: str | None, options: Any) -> bool:
        """Return whether a band passes the show/hide switches.

        An unresolved band always passes. Dropping it is what made the old
        filter hide every network the moment the payload stopped carrying a
        channel — an unknown value must never be treated as a failed match.
        """
        if band is None:
            return True
        option_key = _BAND_OPTION_KEYS.get(band)
        if option_key is None:
            return True
        return bool(options.get(option_key, DEFAULT_SHOW_BAND))

    def _update_history(self, seen_keys: set[str], now: datetime) -> set[str]:
        """Record this scan against the history, returning genuinely new keys."""
        new_keys: set[str] = set()
        for key in seen_keys:
            if key not in self._first_seen:
                self._first_seen[key] = now
                new_keys.add(key)
            self._last_seen[key] = now
            self._visit_counts[key] = self._visit_counts.get(key, 0) + 1
        return new_keys

    def _count_new_within(self, now: datetime, hours: int) -> int:
        """Count networks first seen by this integration within the window."""
        cutoff = now - timedelta(hours=hours)
        return sum(1 for ts in self._first_seen.values() if ts >= cutoff)

    def _fire_new_network_events(
        self, new_keys: set[str], network_map: dict[str, dict[str, Any]]
    ) -> None:
        """Fire a bus event per genuinely new network.

        The first scan after a start or a history reset records the existing
        set silently — without that, every restart would replay the whole
        backlog into a user's automations.
        """
        if not self._event_baseline_done:
            self._event_baseline_done = True
            if new_keys:
                _LOGGER.debug(
                    "Baselined %d existing networks; no events fired", len(new_keys)
                )
            return

        if not new_keys:
            return

        by_key = {v["key"]: (label, v) for label, v in network_map.items()}
        emitted = 0
        for key in sorted(new_keys):
            entry = by_key.get(key)
            if entry is None:
                continue
            if emitted >= NEW_NETWORK_EVENT_MAX_PER_CYCLE:
                break
            label, net = entry
            first_seen_ts = self._first_seen.get(key)
            self.hass.bus.async_fire(
                EVENT_NEW_NETWORK,
                {
                    "entry_id": self.entry.entry_id,
                    "key": key,
                    "ssid": label,
                    "bssid": net["bssid"],
                    "band": net["band"],
                    "channel": net["channel"],
                    "signal": net["signal"],
                    "hidden": net["hidden"],
                    "ssid_anomaly": net["ssid_anomaly"],
                    "mode": net.get("mode"),
                    "first_seen": (
                        first_seen_ts.isoformat() if first_seen_ts else None
                    ),
                },
            )
            emitted += 1

        suppressed = len(new_keys) - emitted
        if suppressed > 0:
            # Counted and logged rather than dropped silently: a burst is
            # information about the environment, not noise to be discarded.
            _LOGGER.info(
                "%s: %d new-network events suppressed this cycle (cap %d)",
                self.entry.title,
                suppressed,
                NEW_NETWORK_EVENT_MAX_PER_CYCLE,
            )


def _parse_timestamps(raw: dict[str, str]) -> dict[str, datetime]:
    """Parse stored ISO timestamps, skipping anything unreadable."""
    parsed: dict[str, datetime] = {}
    for key, value in raw.items():
        try:
            parsed[key] = datetime.fromisoformat(value)
        except (TypeError, ValueError):
            _LOGGER.debug("Discarding unreadable stored timestamp for %s", key)
    return parsed


def _split_patterns(raw: str) -> list[str]:
    """Split a comma-separated pattern list, dropping blanks."""
    return [item.strip() for item in raw.split(",") if item.strip()]


def _is_unknown(
    key: str,
    bssid: str | None,
    known_patterns: list[str],
    denylist_patterns: list[str],
) -> bool:
    """Return whether a network counts as unknown.

    Matches against both the network key (SSID / hidden label) and the BSSID
    (MAC address), so users can specify either SSID names/wildcards or hardware
    BSSIDs in the known list or denylist.

    The denylist wins: a network matching both lists is always unknown.
    """
    for p in denylist_patterns:
        if fnmatch.fnmatch(key, p) or (bssid and fnmatch.fnmatch(bssid, p)):
            return True
    for p in known_patterns:
        if fnmatch.fnmatch(key, p) or (bssid and fnmatch.fnmatch(bssid, p)):
            return False
    return True
