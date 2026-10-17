"""Data coordinator: polls the board and follows its event stream."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field, replace
import logging
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import Z906Client, Z906Error, parse_status_event
from .const import DOMAIN, POLL_INTERVAL, SSE_RETRY_MAX, SSE_RETRY_MIN

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class Z906Data:
    """Snapshot of board and amplifier."""

    connected: bool = False
    status: dict[str, Any] = field(default_factory=dict)
    health: dict[str, Any] = field(default_factory=dict)
    temperature: int | None = None
    input_level: int | None = None


type Z906ConfigEntry = ConfigEntry[Z906Coordinator]


class Z906Coordinator(DataUpdateCoordinator[Z906Data]):
    """Polls /status and /health, pushes changes from /events."""

    config_entry: Z906ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: Z906ConfigEntry,
        client: Z906Client,
        info: dict[str, Any],
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=POLL_INTERVAL,
        )
        self.client = client
        self.info = info

    async def _async_update_data(self) -> Z906Data:
        try:
            health = await self.client.health()
            status = await self.client.status()
            temperature = input_level = None
            if status is not None:
                temperature = await self.client.value("/temperature")
                input_level = await self.client.value("/input/volume")
        except Z906Error as err:
            raise UpdateFailed(str(err)) from err
        return Z906Data(
            connected=status is not None,
            status=status or {},
            health=health,
            temperature=temperature,
            input_level=input_level,
        )

    async def async_listen_events(self) -> None:
        """Follow /events forever, reconnecting with backoff."""
        retry = SSE_RETRY_MIN
        while True:
            try:
                async for event, data in self.client.events():
                    retry = SSE_RETRY_MIN
                    if event != "status" or self.data is None:
                        continue
                    status = parse_status_event(data)
                    # The firmware sends zeros while the amplifier is not
                    # connected; the next poll reports that instead.
                    if status and self.data.connected:
                        self.async_set_updated_data(replace(self.data, status=status))
            except asyncio.CancelledError:
                raise
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                _LOGGER.debug("Event stream of %s lost: %s", self.client.host, err)
            await asyncio.sleep(retry)
            retry = min(retry * 2, SSE_RETRY_MAX)

    async def async_command(self, path: str, params: dict[str, Any] | None = None) -> None:
        """Run a command; the event stream delivers the new state."""
        await self.client.command(path, params)
        await self.async_request_refresh()

    async def async_set_level(self, channel: str, level: float) -> None:
        await self.client.set_level(channel, level)
        await self.async_request_refresh()
