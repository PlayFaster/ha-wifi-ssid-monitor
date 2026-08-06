"""Recorder hygiene — dev_standards Section 14.

The failure this guards is silent. When an attribute is added to an entity and
not added to ``_unrecorded_attributes``, nothing errors and nothing looks
wrong; the value is simply written to the recorder database on every state
change, forever. This project had exactly that: ``severity`` and
``networks_scanned`` were published but never excluded, the second of them
changing on every scan.

Section 14 (Standard Version 1.12.0) makes the default total: every key an
entity can publish must be unrecorded, and a recorded attribute is an exception
needing a written justification. Attributes exist to carry detail about
something that does not merit its own entity — they are not a history
mechanism. A value whose history is genuinely wanted should be promoted to an
entity, or templated into one by the user.

The sweep runs against live entities rather than reading source because
description-driven entities build their attributes from a function on the
entity description, and no static check can see through that.
"""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.wifi_ssid_monitor.const import DOMAIN

# Attributes deliberately left recorded, with the justification Section 14
# requires. Empty by design — adding an entry here is a visible, reviewable
# act, whereas forgetting to extend `_unrecorded_attributes` is not. That
# asymmetry is the entire point of the allow-list.
ALLOWED_RECORDED: frozenset[str] = frozenset()

# Below this, the sweep is not meaningfully exercising the integration and a
# pass would be vacuous — a fixture that stops producing attributes would let
# a real regression through silently.
#
# Measured 2026-08-03: 16 of the integration's 18 entities publish attributes;
# the other two publish none and are skipped, which is correct. Set to the
# real figure rather than a token floor — at 2 the guard passed while 14
# entities went uninspected, which is the failure it exists to prevent.
MIN_ENTITIES_SWEPT = 16

_ACCESS_POINTS = [
    {
        "mac": "AA:BB:CC:00:00:01",
        "ssid": "MyNetwork1",
        "signal": 80,
        "frequency": 2462,
        "mode": "infrastructure",
    },
    {
        "mac": "AA:BB:CC:00:00:02",
        "ssid": "UnknownNet",
        "signal": 55,
        "frequency": 5240,
        "mode": "infrastructure",
    },
]


@pytest.mark.asyncio
async def test_no_entity_publishes_a_recorded_attribute(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """Section 14: `_unrecorded_attributes` must cover every published key."""
    mock_config_entry.add_to_hass(hass)

    with (
        # Force disabled-by-default entities to be added. Without this the
        # sweep silently skips them — they are never instantiated, so their
        # attributes are never inspected. Verified in `zte_router_5g` by
        # mutation: removing a key from a disabled-by-default sensor's
        # `_unrecorded_attributes` did not fail the sweep until this patch was
        # added, and adding it immediately surfaced a real offender.
        patch(
            "homeassistant.helpers.entity.Entity.entity_registry_enabled_default",
            property(lambda self: True),
        ),
        patch(
            "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
            new=AsyncMock(return_value=list(_ACCESS_POINTS)),
        ),
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        checked = 0
        offenders: list[str] = []
        for component in hass.data["entity_components"].values():
            for entity in component.entities:
                platform = getattr(entity, "platform", None)
                if platform is None or platform.platform_name != DOMAIN:
                    continue
                published = set(entity.extra_state_attributes or {})
                if not published:
                    continue
                checked += 1
                leaked = published - entity._unrecorded_attributes - ALLOWED_RECORDED
                if leaked:
                    offenders.append(f"{entity.entity_id}: {sorted(leaked)}")

    assert not offenders, "attributes published but recorded:\n" + "\n".join(offenders)
    assert checked >= MIN_ENTITIES_SWEPT, (
        f"sweep inspected only {checked} entities — the fixture has gone stale "
        f"and this test is passing vacuously"
    )


def test_health_detail_is_unrecorded() -> None:
    """Regression guard for the specific miss found on 2026-07-27.

    `severity` and `networks_scanned` were published by the health sensor but
    absent from `_unrecorded_attributes`, which had fallen behind
    `extra_state_attributes` as the attribute set grew.
    """
    from custom_components.wifi_ssid_monitor.binary_sensor import (
        WifiHealthBinarySensor,
    )

    unrecorded = WifiHealthBinarySensor._unrecorded_attributes
    for name in (
        "issues",
        "severity",
        "degraded_capabilities",
        "drift",
        "signal_unit",
        "last_good_update",
        "networks_scanned",
    ):
        assert name in unrecorded, f"Section 14 requires '{name}' to be unrecorded"


# ---------------------------------------------------------------------------
# Section 12 (b) and (c): icon coverage.
#
# Two properties, deliberately not merged, and neither comparing one artefact
# against another:
#
#  (b) Entities — swept LIVE, not from a description list. Descriptions here
#      live in a mix of module-level tuples (`SENSOR_TYPES`) and standalone
#      singletons (`HEALTH_DESCRIPTION`), so any static enumeration drifts the
#      moment a platform is added. And the check is PER-PLATFORM: flattening
#      `icons.json` into one key set lets an entry filed under the wrong
#      platform satisfy it while the entity still renders a default icon.
#
#  (c) Actions — every registered action carries an icon, and every icon names
#      a real action. Action icons appear in the automation and script editors
#      and in Tools -> Actions; they never appear on the device page
#      or on an entity, so an integration missing them looks entirely normal
#      until someone opens the action picker. That invisibility is why this
#      went unnoticed across the project family until 2026-08-03.
#
# Required by dev_standards Section 12 (Standard Version 1.21.0), which
# extended the section from entity icons to action icons.
# ---------------------------------------------------------------------------

import json  # noqa: E402
import pathlib  # noqa: E402

_ICONS = json.loads(
    (
        pathlib.Path(__file__).parent.parent
        / "custom_components"
        / "wifi_ssid_monitor"
        / "icons.json"
    ).read_text(encoding="utf-8")
)


@pytest.mark.asyncio
async def test_every_live_entity_has_an_icon_or_a_device_class(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """Section 12(b): every entity resolves an icon, checked per platform."""
    mock_config_entry.add_to_hass(hass)

    entity_icons: dict[str, dict] = _ICONS.get("entity", {})

    with (
        patch(
            "homeassistant.helpers.entity.Entity.entity_registry_enabled_default",
            property(lambda self: True),
        ),
        patch(
            "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
            new=AsyncMock(return_value=list(_ACCESS_POINTS)),
        ),
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        checked = 0
        offenders: list[str] = []
        seen_keys: set[tuple[str, str]] = set()

        for component in hass.data["entity_components"].values():
            for entity in component.entities:
                platform = getattr(entity, "platform", None)
                if platform is None or platform.platform_name != DOMAIN:
                    continue
                checked += 1

                key = entity.translation_key
                domain = entity.entity_id.split(".", 1)[0]

                # Recorded before the device_class skip below. An entity with a
                # device class may still carry an explicit icon entry — that is
                # a deliberate override, not a dead entry — so it must count as
                # "seen" or the dead-entry check below reports a false positive.
                seen_keys.add((domain, key))

                # A device class supplies a sensible default icon on its own.
                if getattr(entity, "device_class", None) is not None:
                    continue

                # Per-platform lookup on purpose: an entry filed under the
                # wrong platform must not satisfy this.
                if key not in entity_icons.get(domain, {}):
                    offenders.append(
                        f"{entity.entity_id} (icons.entity.{domain}.{key})"
                    )

    assert not offenders, (
        "entities with no device_class and no icons.json entry under their own "
        "platform:\n" + "\n".join(offenders)
    )
    assert checked >= MIN_ENTITIES_SWEPT, (
        f"icon sweep inspected only {checked} entities — the fixture has gone "
        f"stale and this test is passing vacuously"
    )

    # Dead entries mask genuine gaps and inflate any count-based assessment.
    declared = {(plat, key) for plat, keys in entity_icons.items() for key in keys}
    dead = sorted(declared - seen_keys)
    assert not dead, f"icons.json entity entries matching no live entity: {dead}"


@pytest.mark.asyncio
async def test_every_registered_action_has_an_icon(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """Section 12(c): the services block matches the registered actions, both ways."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wifi_ssid_monitor.api.WifiScanAPI.get_access_points",
        new=AsyncMock(return_value=list(_ACCESS_POINTS)),
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Truth comes from what HA has actually registered, never from the
        # icon file being tested.
        registered = set(hass.services.async_services().get(DOMAIN, {}))

    assert registered, "no actions registered — this test would pass vacuously"

    declared = _ICONS.get("services", {})

    missing = sorted(registered - set(declared))
    assert not missing, (
        f"registered actions with no icons.json entry: {missing}. These render "
        f"with the generic default in the automation editor and the Actions picker."
    )

    dead = sorted(set(declared) - registered)
    assert not dead, f"icons.json service entries matching no registered action: {dead}"

    # The nested `{"service": "mdi:..."}` form, not the legacy bare string:
    # only the object form can carry per-section icons.
    flat = sorted(k for k, v in declared.items() if not isinstance(v, dict))
    assert not flat, (
        f"action icons declared in the legacy flat form: {flat}. Use "
        f'{{"service": "mdi:..."}} so a `sections` icon can be added later.'
    )
