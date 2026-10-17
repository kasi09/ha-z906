"""Fixtures for the Z906 tests."""

from collections.abc import Generator
from unittest.mock import patch

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"

HOST = "192.0.2.10"
MAC = "AA:BB:CC:11:22:33"
UNIQUE_ID = "aa:bb:cc:11:22:33"
INFO = {"mac": MAC, "hostname": "logitech-z906-xiao", "firmware": "2.3.0", "chip": "ESP32-S3"}
HEALTH = {
    "reset": 1,
    "boots": 4,
    "brownouts": 0,
    "uptime": 63,
    "rssi": -55,
    "tx_power": 34,
    "heap": 249136,
    "min_heap": 192720,
}
STATUS = {
    "main_level": 13,
    "center_level": 20,
    "rear_level": 27,
    "sub_level": 16,
    "current_input": 2,
    "current_fx": 0,
    "muted": False,
    "decode_mode": False,
    "fx_input_1": 2,
    "fx_input_2": 0,
    "fx_input_3": 0,
    "fx_input_4": 3,
    "fx_input_5": 3,
    "fx_input_aux": 0,
    "spdif_status": 12,
    "signal_status": 0,
    "stby": 0,
    "auto_stby": 142,
}
OK = {"status": "connected", "success": True}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations) -> None:
    """Load custom_components/z906."""


@pytest.fixture
def no_events() -> Generator[None]:
    """Keep the SSE listener from running in tests."""

    async def idle(self) -> None:
        return None

    with patch(
        "custom_components.z906.coordinator.Z906Coordinator.async_listen_events", idle
    ):
        yield


@pytest.fixture
def board(aioclient_mock):
    """A Z906 board answering /info and /health."""
    base = f"http://{HOST}"
    aioclient_mock.get(f"{base}/info", json=INFO)
    aioclient_mock.get(f"{base}/health", json=HEALTH)
    return aioclient_mock


@pytest.fixture
def device(board):
    """A Z906 board with the amplifier connected."""
    base = f"http://{HOST}"
    board.get(f"{base}/status", json={"status": "connected", "data": STATUS})
    board.get(f"{base}/temperature", json={**OK, "value": 45})
    board.get(f"{base}/input/volume", json={**OK, "value": 510})
    return board
