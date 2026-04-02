import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import CONF_SCAN_INTERVAL, CONF_STOP_POLLING

_LOGGER = logging.getLogger(__name__)


class ZTERouterDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching ZTE Router data with resilience and pausing."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api):
        """Initialize the coordinator."""
        self.api = api
        self.entry = entry
        self.consecutive_failures = 0
        self.last_update_success_time = None

        # Determine the initial update interval from entry options
        scan_interval = entry.options.get(CONF_SCAN_INTERVAL, 180)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{entry.title} Data",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self):
        """Fetch data from API with resilience and pausing."""
        # Check entry.options directly for real-time responsiveness to the UI switch
        is_paused = self.entry.options.get(CONF_STOP_POLLING, False)
        is_first_run = self.data is None

        # 1. If paused and NOT the first run, return cached data immediately
        if is_paused and not is_first_run:
            _LOGGER.debug(
                "%s: Polling is paused; returning cached data.", self.entry.title
            )
            return self.data

        # 2. Attempt fetch with 1 retry
        last_error = None
        for attempt in range(2):
            try:
                # Direct async calls, no more executor jobs!
                data = await self.api.get_all_data()
                sms_cap = await self.api.get_sms_capacity()
                last_sms = await self.api.get_last_sms_content()

                data.update(sms_cap)
                data["last_sms"] = last_sms

                # Success path
                self.last_update_success_time = dt_util.now()
                self.consecutive_failures = 0
                return data

            except Exception as err:
                last_error = err
                if attempt == 0:
                    _LOGGER.warning(
                        "%s: Fetch failed: %s. Retrying in 30 seconds...",
                        self.entry.title,
                        err,
                    )
                    await asyncio.sleep(30)
                else:
                    _LOGGER.warning(
                        "%s: Second fetch attempt failed for this cycle: %s",
                        self.entry.title,
                        err,
                    )

        # 3. Failure resilience — hold last known values for one cycle
        self.consecutive_failures += 1

        if self.data is not None and self.consecutive_failures == 1:
            _LOGGER.warning(
                "%s: Fetch failed. Holding last known values.", self.entry.title
            )
            return self.data

        # 4. Safe startup bypass — if paused on first run, start with empty data
        if is_paused:
            _LOGGER.warning(
                "%s: Initial fetch failed while paused. Starting with empty data.",
                self.entry.title,
            )
            return {}

        _LOGGER.error(
            "%s: Connection lost. Marking entities unavailable.", self.entry.title
        )
        raise UpdateFailed(f"Communication error: {last_error}")
