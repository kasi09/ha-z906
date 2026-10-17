"""HTTP and Server-Sent Events client for the Z906RemoteESP32 firmware."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
import json
from typing import Any

import aiohttp

from .const import LEVEL_MAX, RAW_MAX

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=10)


class Z906Error(Exception):
    """The device could not be reached or answered with an error."""


class Z906Client:
    """Talks to one Z906RemoteESP32 board."""

    def __init__(self, session: aiohttp.ClientSession, host: str) -> None:
        self._session = session
        self.host = host

    @property
    def base_url(self) -> str:
        return f"http://{self.host}"

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            async with self._session.get(
                self.base_url + path, params=params, timeout=REQUEST_TIMEOUT
            ) as resp:
                resp.raise_for_status()
                return await resp.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
            raise Z906Error(f"{path}: {err}") from err

    # Device, answered without the amplifier

    async def info(self) -> dict[str, Any]:
        """MAC, hostname, firmware and chip of the board."""
        return await self._get("/info")

    async def health(self) -> dict[str, Any]:
        """Reset reason, brownouts, RSSI and heap of the board."""
        return await self._get("/health")

    # Amplifier

    async def status(self) -> dict[str, Any] | None:
        """All status fields, or None while the amplifier does not answer."""
        data = await self._get("/status")
        if data.get("status") != "connected":
            return None
        return data.get("data")

    async def value(self, path: str) -> Any:
        """Value of a GET endpoint, or None while the amplifier does not answer."""
        data = await self._get(path)
        if data.get("status") != "connected":
            return None
        return data.get("value")

    async def command(self, path: str, params: dict[str, Any] | None = None) -> None:
        data = await self._get(path, params)
        if data.get("status") != "connected":
            raise Z906Error("amplifier not connected")

    async def set_level(self, channel: str, level: float) -> None:
        """Set main, center, rear or sub to a level of 0-43."""
        raw = round(max(0.0, min(level, LEVEL_MAX)) * RAW_MAX / LEVEL_MAX)
        await self.command(f"/volume/{channel}/set", {"value": raw})

    async def events(self) -> AsyncIterator[tuple[str, str]]:
        """Yield (event, data) from /events until the connection drops."""
        timeout = aiohttp.ClientTimeout(total=None, sock_connect=10, sock_read=60)
        async with self._session.get(
            self.base_url + "/events",
            headers={"Accept": "text/event-stream"},
            timeout=timeout,
        ) as resp:
            resp.raise_for_status()
            async for item in parse_sse(resp.content):
                yield item


async def parse_sse(lines: AsyncIterator[bytes]) -> AsyncIterator[tuple[str, str]]:
    """Turn raw SSE lines into (event, data) pairs."""
    event, data = "message", []
    async for raw in lines:
        line = raw.decode("utf-8", "replace").rstrip("\r\n")
        if not line:
            if data:
                yield event, "\n".join(data)
            event, data = "message", []
        elif line.startswith("event:"):
            event = line[6:].strip()
        elif line.startswith("data:"):
            data.append(line[5:].lstrip())


def parse_status_event(data: str) -> dict[str, Any] | None:
    """Status fields from the data of an SSE 'status' event."""
    try:
        return json.loads(data).get("status")
    except (ValueError, AttributeError):
        return None
