import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ZTERouterAPI
from .const import DOMAIN
from .coordinator import ZTERouterDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.SENSOR,
    Platform.BUTTON,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ZTE Router 5G Monitor from a config entry with Background Safety."""
    session = async_get_clientsession(hass)
    api = ZTERouterAPI(
        session,
        entry.options[CONF_HOST],
        entry.options.get(CONF_USERNAME),
        entry.options[CONF_PASSWORD],
    )

    # Create the specialized coordinator
    coordinator = ZTERouterDataUpdateCoordinator(hass, entry, api)

    # Store for platform access
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward platforms immediately so entities appear in HA
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # BACKGROUND INITIALIZATION TASK
    # Offloads the initial connection to prevent blocking HA startup
    async def _async_background_setup():
        try:
            await api.try_set_protocol(5)
            await api.login(5)
            await coordinator.async_refresh()
            _LOGGER.info("%s: Background initialization complete.", entry.title)
        except Exception as err:
            _LOGGER.warning(
                "%s: Background initialization failed (will retry): %s",
                entry.title,
                err,
            )

    hass.async_create_task(_async_background_setup())

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and release resources."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        # Note: No need to close api.session as it's managed by HA core
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
    return unload_ok
