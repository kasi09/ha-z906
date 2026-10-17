"""Setup, entity states and commands."""

import pytest

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.z906.const import DOMAIN

from .conftest import HOST, OK, UNIQUE_ID

pytestmark = pytest.mark.usefixtures("no_events")

ENTITIES = {
    "media_player": "media_player.logitech_z906",
    "select": "select.logitech_z906_sound_mode",
    "switch": "switch.logitech_z906_dolby_dts_5_1",
    "number": "number.logitech_z906_center",
}


async def _setup(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=UNIQUE_ID, data={CONF_HOST: HOST})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_states(hass: HomeAssistant, device) -> None:
    entry = await _setup(hass)
    assert entry.state is ConfigEntryState.LOADED

    player = hass.states.get("media_player.logitech_z906")
    assert player.state == "on"
    assert player.attributes["volume_level"] == pytest.approx(13 / 43)
    assert player.attributes["source"] == "Optisch 1"
    assert player.attributes["sound_mode"] == "3D"
    assert player.attributes["is_volume_muted"] is False

    assert hass.states.get("select.logitech_z906_sound_mode").state == "3d"
    assert hass.states.get("switch.logitech_z906_dolby_dts_5_1").state == "off"
    assert hass.states.get("number.logitech_z906_center").state == "20"
    assert hass.states.get("number.logitech_z906_subwoofer").state == "16"
    assert hass.states.get("sensor.logitech_z906_temperature").state == "45"
    assert hass.states.get("sensor.logitech_z906_input_level").state == "510"
    assert hass.states.get("sensor.logitech_z906_wifi_signal").state == "-55"
    assert hass.states.get("sensor.logitech_z906_brownouts").state == "0"

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_amplifier_disconnected(hass: HomeAssistant, board) -> None:
    board.get(f"http://{HOST}/status", json={"status": "disconnected"})
    await _setup(hass)

    assert hass.states.get("media_player.logitech_z906").state == "unavailable"
    # Board diagnostics stay available
    assert hass.states.get("sensor.logitech_z906_wifi_signal").state == "-55"


async def test_board_unreachable(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(f"http://{HOST}/info", exc=TimeoutError())
    entry = MockConfigEntry(domain=DOMAIN, unique_id=UNIQUE_ID, data={CONF_HOST: HOST})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY


@pytest.mark.parametrize(
    ("domain", "service", "data", "path", "value"),
    [
        ("media_player", "select_source", {"source": "Cinch"}, "/input/1", None),
        ("media_player", "select_sound_mode", {"sound_mode": "4.1"}, "/input/effect/2", None),
        ("media_player", "volume_mute", {"is_volume_muted": True}, "/mute/on", None),
        ("media_player", "turn_off", {}, "/power/off", None),
        ("media_player", "volume_up", {}, "/volume/main/up", None),
        ("media_player", "volume_set", {"volume_level": 0.5}, "/volume/main/set", "128"),
        ("select", "select_option", {"option": "off"}, "/input/effect/3", None),
        ("switch", "turn_on", {}, "/input/decode/on", None),
        ("number", "set_value", {"value": 30}, "/volume/center/set", "178"),
    ],
)
async def test_commands(hass: HomeAssistant, device, domain, service, data, path, value) -> None:
    device.get(f"http://{HOST}{path}", json=OK)
    await _setup(hass)

    await hass.services.async_call(
        domain, service, {"entity_id": ENTITIES[domain], **data}, blocking=True
    )

    calls = [call[1] for call in device.mock_calls if call[1].path == path]
    assert calls, f"{path} not requested"
    if value is not None:
        # 0.5 of 43 -> 128 of 255, 30 of 43 -> 178 of 255
        assert calls[-1].query.get("value") == value
