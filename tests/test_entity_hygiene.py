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
MIN_ENTITIES_SWEPT = 2

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
