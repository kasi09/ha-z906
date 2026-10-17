"""Event stream parsing."""

from custom_components.z906.api import parse_sse, parse_status_event


async def _lines(*lines: bytes):
    for line in lines:
        yield line


async def test_parse_sse() -> None:
    stream = _lines(
        b"id: 1\r\n",
        b"event: status\r\n",
        b'data: {"status":{"main_level":13}}\r\n',
        b"\r\n",
        b"event: heartbeat\n",
        b"data: ping\n",
        b"\n",
        b"retry: 1000\n",
        b"\n",
    )
    events = [item async for item in parse_sse(stream)]
    assert events == [("status", '{"status":{"main_level":13}}'), ("heartbeat", "ping")]
    assert parse_status_event(events[0][1]) == {"main_level": 13}
    assert parse_status_event("ping") is None
