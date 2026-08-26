#!/usr/bin/env python3
"""Automated fault drill: mock Supervisor faults, asserted through live HA.

Replaces the attended `fault_drill.sh`. That version made a human do the
polling, and the coordinator's 10-second refresh debounce meant three button
presses were not three fetches — so nobody could tell a slow check from a
broken one. It still found two real defects; this makes finding the next one
cheap.

**What it does.** Arms a fault on the mock Supervisor, drives real scans
through the `wifi_ssid_monitor.scan_now` action, and asserts the resulting
Integration Health attributes and Repairs entries over Home Assistant's own
APIs. No entity is mutated, nothing is written to `.storage`.

**Why the pacing.** `scan_now` routes through `async_request_refresh`, which
Home Assistant debounces with a 10-second cooldown. Calls made inside that
window coalesce into one fetch, so this waits `SCAN_SPACING` between them and
polls for the expected state rather than assuming a call produced a poll. That
is the whole reason the manual version was confusing.

**Token** comes from `.notes/ha_restart/token.txt`, which is where this
workspace keeps it deliberately. Nothing here reads `.storage/auth`.

Run through the `Mock: Fault Drill` task. `--quick` shortens the waits for a
smoke test; the full run takes a few minutes because several findings must
survive a strike budget before they confirm, which is the behaviour under test.
"""
# ruff: noqa: T201
# T201: the console report is this script's entire output; there is no logger
# to route it through and a caller reading the transcript is the point.
# INP001: a standalone dev-container script, never imported.

from __future__ import annotations

import argparse
import asyncio
import pathlib
import sys
import time
from typing import Any

import aiohttp

HA = "http://localhost:8123"
SUPERVISOR = "http://supervisor"
TOKEN_FILE = pathlib.Path(".notes/ha_restart/token.txt")
STAMP = pathlib.Path(".notes/fault_drill_last.txt")
REPORT = pathlib.Path(".reports/fault_drill.txt")
DOMAIN = "wifi_ssid_monitor"

# Longer than HA's 10-second refresh debounce, or the calls coalesce.
SCAN_SPACING = 11.0
MAX_SCANS = 8

_TRANSCRIPT: list[str] = []


def print(*args: Any, **kwargs: Any) -> None:  # noqa: A001
    """Print to the screen and keep a colour-stripped copy for the report.

    A run nobody can read afterwards is the defect `dev_standards` Section 22
    records against the first hardware script: it printed everything and filed
    nothing, so no run could be reviewed and a skip left no trace.
    """
    import builtins
    import re

    line = " ".join(str(a) for a in args)
    _TRANSCRIPT.append(re.sub(r"\x1b\[[0-9;]*m", "", line))
    builtins.print(line, **kwargs)


GREEN, RED, YELLOW, CYAN, OFF = (
    "\033[1;32m",
    "\033[1;31m",
    "\033[1;33m",
    "\033[1;36m",
    "\033[0m",
)


class Drill:
    """Drives the mock and reads Home Assistant back."""

    def __init__(self, session: aiohttp.ClientSession, token: str, quick: bool):
        """Hold the session, the auth header and the scan pacing."""
        self.s = session
        self.headers = {"Authorization": f"Bearer {token}"}
        # NOT configurable downwards. Anything under HA's 10-second
        # refresh debounce makes the calls coalesce, and the drill then
        # measures nothing while appearing to run.
        self.spacing = SCAN_SPACING
        self.max_scans = 4 if quick else MAX_SCANS
        self.failures: list[str] = []
        self.checks = 0
        # Counted, never written into the strings. Hardcoded step numbers
        # printed 1 2 3 4 6 6 5 8 the first time the scenarios were reordered.
        self.step = 0

    # ------------------------------------------------------------ plumbing

    async def fault(self, mode: str) -> None:
        """Arm a mock fault, or clear one with mode="off"."""
        async with self.s.get(f"{SUPERVISOR}/mock/fault", params={"mode": mode}):
            pass

    async def states(self) -> list[dict[str, Any]]:
        """Return every Home Assistant state object."""
        async with self.s.get(f"{HA}/api/states", headers=self.headers) as r:
            r.raise_for_status()
            return await r.json()

    async def health_entities(self) -> list[str]:
        """Every Integration Health sensor this integration owns."""
        found = [
            s["entity_id"]
            for s in await self.states()
            if s["entity_id"].startswith("binary_sensor.")
            and "integration_health" in s["entity_id"]
            and DOMAIN in s["entity_id"]
        ]
        if not found:
            raise SystemExit(
                f"{RED}No Integration Health entity found. Is the integration "
                f"loaded and the entry set up?{OFF}"
            )
        return sorted(found)

    async def health(self, entity_id: str) -> dict[str, Any]:
        """Return one health snapshot, with the entity state folded in.

        `problem` is the entity *state*, not an attribute — the sensor
        publishes `issues`, `severity`, `degraded_capabilities` and `drift`,
        and expresses the problem flag as on/off. Folding it in as `_state`
        keeps every predicate reading from one dict.
        """
        async with self.s.get(
            f"{HA}/api/states/{entity_id}", headers=self.headers
        ) as r:
            r.raise_for_status()
            return await r.json()

    async def snapshot(self, entity_id: str) -> dict[str, Any]:
        """Return the health attributes plus `_state` (on / off)."""
        state = await self.health(entity_id)
        return {**state["attributes"], "_state": state["state"]}

    async def scan(self) -> None:
        """Ask the integration to scan now, through its own action."""
        async with self.s.post(
            f"{HA}/api/services/{DOMAIN}/scan_now", headers=self.headers, json={}
        ) as r:
            r.raise_for_status()

    async def repairs(self) -> set[str]:
        """Issue ids currently raised for this domain, over the WebSocket API.

        The issue registry has no REST endpoint. Reading `.storage` instead
        would be reading Home Assistant's private state, and would miss issues
        that have not been flushed to disk.
        """
        async with self.s.ws_connect(f"{HA}/api/websocket") as ws:
            await ws.receive_json()  # auth_required
            await ws.send_json(
                {
                    "type": "auth",
                    "access_token": self.headers["Authorization"].split()[1],
                }
            )
            auth = await ws.receive_json()
            if auth.get("type") != "auth_ok":
                raise SystemExit(f"{RED}WebSocket auth failed: {auth}{OFF}")
            await ws.send_json({"id": 1, "type": "repairs/list_issues"})
            msg = await ws.receive_json()
            issues = msg.get("result", {}).get("issues", [])
            return {i["issue_id"] for i in issues if i.get("domain") == DOMAIN}

    def banner(self, title: str) -> None:
        """Print the next step heading, numbered by position."""
        self.step += 1
        print(f"\n{CYAN}{self.step}. {title}{OFF}")

    # ------------------------------------------------------------ assertions

    def check(self, ok: bool, label: str, detail: str = "") -> bool:
        """Record one assertion and print it as it happens."""
        self.checks += 1
        if ok:
            print(f"      {GREEN}PASS{OFF}  {label}")
        else:
            print(f"      {RED}FAIL{OFF}  {label}{(' - ' + detail) if detail else ''}")
            self.failures.append(label)
        return ok

    async def drive_until(
        self, entity_id: str, predicate, label: str, max_scans: int | None = None
    ) -> dict[str, Any]:
        """Scan until the health snapshot satisfies `predicate`, or give up.

        Polls for the outcome rather than assuming a scan happened. A finding
        that needs a strike budget will take several passes; that is the
        behaviour being tested, not slowness to be worked around.
        """
        max_scans = max_scans or self.max_scans
        snapshot: dict[str, Any] = {}
        for attempt in range(1, max_scans + 1):
            await self.scan()
            await asyncio.sleep(self.spacing)
            snapshot = await self.snapshot(entity_id)
            if predicate(snapshot):
                print(f"      (reached after {attempt} scan(s))")
                return snapshot
            print(
                f"      ... scan {attempt}/{max_scans}: "
                f"severity={snapshot.get('severity')!r}"
            )
        self.check(False, label, f"never reached it in {max_scans} scans")
        return snapshot

    async def drive_until_repair(
        self, key: str, label: str, max_scans: int | None = None
    ) -> set[str]:
        """Scan until a repair containing `key` is raised, or give up."""
        max_scans = max_scans or self.max_scans
        raised: set[str] = set()
        for attempt in range(1, max_scans + 1):
            await self.scan()
            await asyncio.sleep(self.spacing)
            raised = await self.repairs()
            if any(key in issue for issue in raised):
                print(f"      (repair raised after {attempt} scan(s))")
                return raised
            print(f"      ... scan {attempt}/{max_scans}: repairs={sorted(raised)}")
        self.check(False, label, f"no {key} repair in {max_scans} scans")
        return raised

    # ------------------------------------------------------------ scenarios

    async def scenario_interface_missing(self, entity_id: str) -> None:
        """Assert a 400 reports `error`, names the interface, then repairs."""
        self.banner("Interface gone (400)")
        await self.fault("unknown_interface")
        snap = await self.drive_until(
            entity_id,
            lambda s: s.get("severity") == "error",
            "a failing fetch reports `error`",
        )
        self.check(
            snap.get("severity") == "error",
            "severity is `error` once the fetch budget is spent",
            f"got {snap.get('severity')!r}",
        )
        self.check(
            "interface_missing" in (snap.get("degraded_capabilities") or []),
            "the missing interface is named, not just `supervisor_unreachable`",
            str(snap.get("degraded_capabilities")),
        )
        # No repair is raised for this any more: a missing interface is
        # reported on the health sensor, where it can be automated on, and the
        # Repairs panel is kept for the one condition asking the user to act.
        raised = await self.repairs()
        self.check(
            not any("interface_missing" in i for i in raised),
            "a missing interface raises no repair card",
            str(sorted(raised)),
        )

    async def scenario_recovery(self, entity_id: str, label: str) -> None:
        """Assert clearing the fault returns to `ok` and drops every repair."""
        self.banner(label)
        await self.fault("off")
        snap = await self.drive_until(
            entity_id,
            lambda s: s.get("_state") == "off" and s.get("severity") == "ok",
            "recovery returns to `ok`",
        )
        self.check(
            snap.get("severity") == "ok",
            "severity returns to `ok`, never blank",
            f"got {snap.get('severity')!r}",
        )
        raised = await self.repairs()
        self.check(not raised, "every repair cleared itself", str(sorted(raised)))

    async def scenario_supervisor_down(self, entity_id: str) -> None:
        """Assert a 500 reports `error` without taking the sensor down."""
        self.banner("Supervisor unreachable (500)")
        await self.fault("down")
        snap = await self.drive_until(
            entity_id,
            lambda s: s.get("severity") == "error",
            "a total outage reports `error`",
        )
        self.check(
            "supervisor_unreachable" in (snap.get("degraded_capabilities") or []),
            "the outage is named `supervisor_unreachable`",
            str(snap.get("degraded_capabilities")),
        )
        health = await self.health(entity_id)
        self.check(
            health["state"] != "unavailable",
            "Integration Health stays available during the outage (S19)",
            f"state={health['state']!r}",
        )
        # The one condition that still earns a card. Waits on the repair rather
        # than the attributes: the snapshot names the outage as soon as the
        # fetch budget is spent, while the card waits for the strike budget.
        raised = await self.drive_until_repair(
            "conn_error", "a `conn_error` repair is raised"
        )
        self.check(
            any("conn_error" in i for i in raised),
            "a `conn_error` repair is raised",
            str(sorted(raised)),
        )

    async def scenario_signal_flip(self, entity_id: str) -> None:
        """Assert a unit flip confirms as drift and raises its repair."""
        self.banner("Signal unit flip to dBm (held until reload)")
        await self.fault("dbm")
        snap = await self.drive_until(
            entity_id,
            lambda s: bool(s.get("drift")),
            "the unit flip confirms as drift",
        )
        self.check(bool(snap.get("drift")), "`drift` names the flip", str(snap))
        self.check(
            snap.get("severity") == "warning",
            "drift reports `warning`, not `error`",
            f"got {snap.get('severity')!r}",
        )
        raised = await self.repairs()
        self.check(
            not any("signal_format_changed" in i for i in raised),
            "a signal-unit flip raises no repair card; it is drift on health",
            str(sorted(raised)),
        )
        # The baseline is held deliberately, so this one does NOT self-clear.
        # Recovery is a reload, which is the honest duration: the user's
        # proximity threshold stays meaningless until they act.
        print(f"      {YELLOW}note{OFF}  held until reload, by design")
        await self.fault("off")
        await self.reload_entries()

    async def scenario_drift_without_a_card(self, entity_id: str) -> None:
        """Drift must warn without raising an actionable repair."""
        self.banner("Payload drift, no accesspoints key")
        await self.fault("no_ap_key")
        snap = await self.drive_until(
            entity_id,
            lambda s: bool(s.get("drift")),
            "the missing key confirms as drift",
        )
        self.check(
            snap.get("severity") == "warning",
            "drift reports `warning`",
            f"got {snap.get('severity')!r}",
        )
        raised = await self.repairs()
        self.check(
            not any("interface_missing" in i or "conn_error" in i for i in raised),
            "no actionable repair is raised for drift alone",
            str(sorted(raised)),
        )

    async def reload_entries(self) -> None:
        """Reload every entry for this domain, to re-baseline after a flip."""
        async with self.s.get(
            f"{HA}/api/config/config_entries/entry", headers=self.headers
        ) as r:
            if r.status != 200:
                print(f"      {YELLOW}could not list entries to reload{OFF}")
                return
            entries = await r.json()
        for entry in [e for e in entries if e.get("domain") == DOMAIN]:
            async with self.s.post(
                f"{HA}/api/config/config_entries/entry/{entry['entry_id']}/reload",
                headers=self.headers,
            ):
                pass
        await asyncio.sleep(self.spacing)


def _write_report() -> None:
    """File the transcript from a `finally`, so an aborted run still leaves one."""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(_TRANSCRIPT) + "\n", encoding="utf-8")


async def main() -> int:
    """Run every scenario, report, and record a clean pass."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quick",
        action="store_true",
        help="fewer scans per step; the spacing is fixed by HA's debounce",
    )
    args = parser.parse_args()

    if not TOKEN_FILE.exists():
        print(f"{RED}✖  Fault Drill: NOT RUN{OFF}")
        print(f"No token at {TOKEN_FILE}.")
        return 1
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()

    started = time.time()
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{SUPERVISOR}/mock/fault") as r:
                r.raise_for_status()
        except Exception:  # noqa: BLE001 - any failure here means the same
            # thing to the caller: the mock is not reachable. Naming the
            # aiohttp errors individually would add nothing and would go
            # stale with the library.
            print(f"{RED}✖  Fault Drill: NOT RUN{OFF}")
            print("The mock is not answering on /mock/fault. It is a separate")
            print("container and does not reload when HA restarts:")
            print("    docker restart supervisor_mock")
            return 1

        drill = Drill(session, token, args.quick)
        try:
            entities = await drill.health_entities()
        except SystemExit as exc:
            print(exc)
            return 1

        entity_id = entities[0]
        print(f"{CYAN}Fault drill{OFF} - asserting against {entity_id}")
        if len(entities) > 1:
            print(f"  ({len(entities)} health entities found; driving the first)")

        try:
            await drill.scenario_interface_missing(entity_id)
            await drill.scenario_recovery(entity_id, "Recovery")
            await drill.scenario_supervisor_down(entity_id)
            await drill.scenario_recovery(entity_id, "Recovery")
            await drill.scenario_drift_without_a_card(entity_id)
            await drill.scenario_recovery(entity_id, "Recovery")
            # Last on purpose. This is the only scenario whose finding is held
            # until the entry reloads, so running anything after it inherits
            # its repairs and reports them as leftovers.
            await drill.scenario_signal_flip(entity_id)
            await drill.scenario_recovery(entity_id, "Final state")
        finally:
            # However this ends, the mock must not be left faulted: the next
            # person would debug the fault instead of their own change.
            await drill.fault("off")
            _write_report()

        took = int(time.time() - started)
        print()
        if drill.failures:
            print(
                f"{RED}✖  Fault Drill: FAILED{OFF} - "
                f"{len(drill.failures)} of {drill.checks} checks, {took}s"
            )
            for f in drill.failures:
                print(f"     - {f}")
            print(f"Report: {REPORT}")
            _write_report()
            return 1

        STAMP.parent.mkdir(parents=True, exist_ok=True)
        STAMP.write_text(
            f"{int(time.time())} {time.strftime('%Y-%m-%dT%H:%M:%S%z')}\n",
            encoding="utf-8",
        )
        print(
            f"{GREEN}✔  Fault Drill: PASSED{OFF} - "
            f"{drill.checks} checks, {took}s, recorded in {STAMP}"
        )
        print()
        print("Still worth one look, because no API can judge it:")
        print("  - does each Repairs card read like a sentence a user can act on?")
        print("  - does the Integration Health more-info dialog read clearly?")
        # Written again, last, so the filed report carries the verdict. The
        # `finally` above covers the aborted run; this covers the normal one.
        print(f"Report: {REPORT}")
        _write_report()
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
