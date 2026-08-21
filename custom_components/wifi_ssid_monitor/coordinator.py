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
    ALL_REPAIR_KEYS,
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
    COORDINATOR_TIMEOUT_SECONDS,
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
from .health import (
    SEVERITY_ERROR,
    SEVERITY_UNKNOWN,
    Finding,
    ScanFacts,
    run_checks,
    worst_severity,
)
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
            # `problem` stays False through cold start on purpose. Section 19
            # maps `unknown` to the sensor being on, but firing the problem
            # sensor on every restart is the jitter the same section forbids,
            # and it would clear itself one poll later. `zte_router_5g` pairs
            # `unknown` with `problem: False` for the same reason.
            "problem": False,
            # Nothing has been fetched, so no verdict is possible. Section 19
            # forbids `None` here: rendered beside three empty lists it is
            # indistinguishable from a sensor that never populated.
            "severity": SEVERITY_UNKNOWN,
            "issues": [],
            "degraded_capabilities": [],
            "drift": [],
            "signal_unit": None,
            "last_good_update": None,
        }
        self._drift_strikes: dict[str, int] = {}
        self._baseline_signal_unit: str | None = None
        # Logged once, not once per poll: the baseline is now held, so
        # the mismatch recurs on every scan until the entry is reloaded.
        self._signal_flip_logged = False
        self._scans_completed = 0
        self._active_repairs: set[str] = set()

        # New-network events are baselined on the first poll so a restart never
        # replays the existing backlog into a user's automations.
        self._event_baseline_done = False

        # Set by async_flush_stores so a late poll cannot re-arm a
        # delayed write after the final flush.
        self._shutting_down = False

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
        """Queue a coalesced write of all three history stores.

        A no-op once the flush has run: a poll already awaiting the API when
        unload starts completes afterwards and would otherwise arm a 30-second
        write on a coordinator nothing will flush again.
        """
        if self._shutting_down:
            return
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
        self._shutting_down = True
        results = await asyncio.gather(
            self.store.async_save(
                {k: v.isoformat() for k, v in self._last_seen.items()}
            ),
            self.store_first_seen.async_save(
                {k: v.isoformat() for k, v in self._first_seen.items()}
            ),
            self.store_visit_counts.async_save(dict(self._visit_counts)),
            return_exceptions=True,
        )
        # The load side logs its failures; the write side must match, or a
        # disk-full or permissions error silently loses the history and
        # nothing in the log explains why it reset.
        for name, result in zip(
            ("last_seen", "first_seen", "visit_counts"), results, strict=True
        ):
            if isinstance(result, BaseException):
                _LOGGER.warning(
                    "Failed to flush the %s store on unload: %s", name, result
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

        Uses ``async_request_refresh`` rather than ``async_refresh``. The two
        look interchangeable and are not: HA builds the coordinator's debouncer
        with ``immediate=True``, so the first call fetches straight away and the
        10-second cooldown only coalesces the ones behind it. A single press
        behaves identically either way; ten rapid presses become one fetch here
        and ten with ``async_refresh``. That coalescing is the reason an action
        a script can call in a loop is safe to route through this.
        """
        self._force_refresh_once = True
        await self.async_request_refresh()

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

        missing = [f for f in findings if f.key == "interface_missing"]
        if missing and not cold_start:
            # At runtime a 400/404 can be transient — the Supervisor
            # restarting mid-poll produces one — and there are held values
            # to show meanwhile, so corroboration is worth the wait.
            #
            # Guarded because this whole method runs inside the fetch
            # error handler: _apply_health re-runs the checks and touches
            # the issue registry, and anything raised here would replace
            # the Supervisor error that actually caused the failure. The
            # _process_scan call site guards it for the same reason.
            try:
                self._apply_health(facts)
            except Exception:
                _LOGGER.debug(
                    "Health computation failed on the failure path; "
                    "leaving the previous snapshot",
                    exc_info=True,
                )
            # Deliberately NOT returning here. `_apply_health` exists to
            # corroborate the *repair* over the drift budget; it must not get
            # to describe a fetch that has already failed past its strike
            # budget as `ok`. It used to, and the effect was that a missing
            # interface — permanent and user-fixable — reported healthy for
            # two more polls than an unreachable Supervisor, which is usually
            # transient. Found by the attended fault drill, 2026-08-21.

        elif missing:
            # Cold start publishes without corroboration, for the reason in
            # this method's docstring: there is nothing held, so three polls of
            # "no problem" against a wholly unavailable integration is the
            # worst answer available. Routing this through _apply_health applied
            # the strike budget anyway and produced exactly that.
            finding = missing[0]
            self.health_snapshot = {
                **self.health_snapshot,
                "problem": True,
                "severity": finding.severity,
                "issues": [finding.message],
                "degraded_capabilities": [finding.key],
                "drift": [],
                "cold_start": True,
            }
            self._sync_repairs(missing)
            return

        # The fetch failed past its budget, so this is an outage either way.
        # Which one is named depends on whether the Supervisor told us the
        # interface is gone or simply did not answer.
        self.health_snapshot = {
            **self.health_snapshot,
            "problem": True,
            # Total outage — Section 19 reserves `error` for exactly this.
            "severity": SEVERITY_ERROR,
            "issues": [
                missing[0].message
                if missing
                else f"Cannot reach the Supervisor API: {err}"
            ],
            "degraded_capabilities": [
                missing[0].key if missing else "supervisor_unreachable"
            ],
            # No payload arrived, so no drift verdict is possible this cycle.
            "drift": [],
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

        # No confirmed finding is a positive verdict, not an absent one:
        # Section 19 requires `ok` rather than `None` so a healthy sensor and
        # one that never reported cannot be confused.
        severity = worst_severity([f.severity for f in confirmed])

        self.health_snapshot = {
            "problem": bool(confirmed),
            "severity": severity,
            "issues": [f.message for f in confirmed],
            # Section 19 publishes these separately: a failed capability is not
            # the same thing as the payload changing shape underneath a
            # successful fetch, and an automation reacting to one should not
            # fire on the other. Every confirmed finding lands in exactly one.
            "degraded_capabilities": [f.key for f in confirmed if not f.is_drift],
            "drift": [f.message for f in confirmed if f.is_drift],
            "signal_unit": facts.signal_unit,
            "baseline_signal_unit": self._baseline_signal_unit,
            "last_good_update": (
                self.last_update_success_time.isoformat()
                if self.last_update_success_time
                else None
            ),
            "networks_scanned": facts.total_aps,
        }
        self._sync_repairs(confirmed)

    def _issue_id(self, key: str) -> str:
        """Scope a repair issue to this config entry.

        The issue registry keys on ``(domain, issue_id)``, so a bare key gives
        every entry the same slot. This integration supports one entry per
        interface, and with two configured the healthy one deletes the failing
        one's repair on every successful poll.

        The **translation** stays keyed on the bare type — the scoped id is an
        identity, not a message.
        """
        return f"{key}_{self.entry.entry_id}"

    def _sync_repairs(self, findings: list[Finding]) -> None:
        """Raise and clear the repair issues, keeping them to the actionable few."""
        wanted = {f.repair: f for f in findings if f.repair}

        for key, finding in wanted.items():
            if key in self._active_repairs:
                continue
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                self._issue_id(key),
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=key,
                translation_placeholders={
                    "detail": finding.message,
                    "entry": self.entry.title,
                },
            )
            self._active_repairs.add(key)

        # Deletion sweeps every repair this integration can raise, NOT just the
        # ones this coordinator remembers raising. `_active_repairs` is
        # per-instance, and the issue registry outlives the instance: after a
        # reload or a Home Assistant restart the set is empty, so a set-driven
        # delete could never clear a card raised before it. These issues are
        # `is_fixable=False`, so that card had no UI path out and sat in the
        # Repairs panel for ever. `async_delete_issue` is a no-op for an issue
        # that is not there, which is what makes the stateless sweep cheap.
        for key in set(ALL_REPAIR_KEYS) - set(wanted):
            ir.async_delete_issue(self.hass, DOMAIN, self._issue_id(key))
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
            async with asyncio.timeout(COORDINATOR_TIMEOUT_SECONDS):
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
                self._issue_id(ISSUE_SUPERVISOR_UNAVAILABLE),
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=ISSUE_SUPERVISOR_UNAVAILABLE,
                translation_placeholders={"entry": self.entry.title},
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
        ir.async_delete_issue(
            self.hass, DOMAIN, self._issue_id(ISSUE_SUPERVISOR_UNAVAILABLE)
        )

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

        # Several radios can share one label — a dual-band AP, or every node of
        # a mesh. Merging them is deliberate (see history_key), but the reading
        # that survives must be the strongest, not whichever the Supervisor
        # listed last. This is a rogue detector: the question it answers is how
        # strong the strongest thing broadcasting that name is, and list order
        # is not an answer to it. A None signal never displaces a real one, but
        # a network whose radios all report None is still published.
        network_map: dict[str, dict[str, Any]] = {}
        for net in visible:
            existing = network_map.get(net["label"])
            if existing is not None:
                incoming = net["signal_pct"]
                current = existing["signal"]
                if incoming is None or (current is not None and incoming <= current):
                    continue
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

        # The counter is incremented AFTER the health pass, not before, so
        # `_apply_health` sees the number of scans completed *before* this one.
        # Incrementing first made HEALTH_STARTUP_GRACE_SCANS grant one fewer
        # scan of grace than its name says — a 2 meant one scan.
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
        except Exception:
            _LOGGER.debug(
                "Health computation failed; treating as healthy", exc_info=True
            )
        self._scans_completed += 1

        if signal_unit and self._baseline_signal_unit is None:
            self._baseline_signal_unit = signal_unit
        elif signal_unit and signal_unit != self._baseline_signal_unit:
            # The baseline is deliberately NOT moved to the new unit. Adopting
            # it here made `check_signal_unit_flip` unraisable: it fired once,
            # took one strike of the three it needs, and then stopped firing
            # because the baseline now matched — at which point `_apply_health`
            # deleted the strike count. One of three repair issues could never
            # appear. Holding the baseline lets the strike budget do its job,
            # and the finding persists until the entry is reloaded, which is
            # the right duration: a unit flip invalidates the user's proximity
            # threshold until they act on it.
            if not self._signal_flip_logged:
                _LOGGER.info(
                    "Supervisor signal unit changed from %s to %s",
                    self._baseline_signal_unit,
                    signal_unit,
                )
                self._signal_flip_logged = True

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
            continue
    # The count, not the keys. A key here is a neighbouring network's SSID or
    # its Hidden-<last4> label — third-party data, in a file with no redaction
    # layer (dev_standards Section 20). How many entries were unreadable is
    # also the more useful diagnostic: one is a corrupt row, all of them is a
    # storage-format change.
    discarded = len(raw) - len(parsed)
    if discarded:
        _LOGGER.debug("Discarded %d unreadable stored timestamp(s)", discarded)
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
