"""Shared helpers for the ZTE Router 5G Monitor integration."""

# Known model strings to detect from the wa_inner_version firmware string.
# e.g. 'IRL_H3G_MC7010DV1.0.0B01' → 'MC7010'
_KNOWN_MODELS = ["MC7010", "MC801", "MC888", "MC889"]


def get_router_model(coordinator_data: dict | None) -> str:
    """Extract the router model from coordinator data.

    Reads the 'wa_inner_version' field (e.g. 'IRL_H3G_MC7010DV1.0.0B01')
    and returns the first matching known model string.
    Falls back to 'ZTE Router' if data is unavailable or no model is recognised.
    """
    if not coordinator_data:
        return "ZTE Router"
    version = coordinator_data.get("wa_inner_version", "")
    for model in _KNOWN_MODELS:
        if model in version:
            return model
    return "ZTE Router"
