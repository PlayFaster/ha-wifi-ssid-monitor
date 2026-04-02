from custom_components.zte_router_5g.helpers import get_router_model


def test_get_router_model_none():
    """Test get_router_model with None data."""
    assert get_router_model(None) == "ZTE Router"


def test_get_router_model_empty():
    """Test get_router_model with empty dict."""
    assert get_router_model({}) == "ZTE Router"


def test_get_router_model_unknown():
    """Test get_router_model with unknown model string."""
    assert get_router_model({"wa_inner_version": "UNKNOWN_MODEL_123"}) == "ZTE Router"


def test_get_router_model_known():
    """Test get_router_model with known model strings."""
    assert (
        get_router_model({"wa_inner_version": "IRL_H3G_MC7010DV1.0.0B01"}) == "MC7010"
    )
    assert get_router_model({"wa_inner_version": "MC801A_V1.0.0"}) == "MC801"
    assert get_router_model({"wa_inner_version": "MC888_FIRMWARE"}) == "MC888"
    assert get_router_model({"wa_inner_version": "MC889_PRO"}) == "MC889"
