"""Media player: power, main volume, mute, input and sound mode."""

from __future__ import annotations

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import EFFECTS, INPUTS, LEVEL_MAX
from .coordinator import Z906ConfigEntry
from .entity import Z906Entity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Z906ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([Z906MediaPlayer(entry.runtime_data)])


class Z906MediaPlayer(Z906Entity, MediaPlayerEntity):
    """The Z906 as a speaker."""

    _attr_name = None
    _attr_device_class = MediaPlayerDeviceClass.SPEAKER
    _attr_source_list = INPUTS
    _attr_sound_mode_list = EFFECTS
    _attr_volume_step = 1 / LEVEL_MAX
    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.SELECT_SOURCE
        | MediaPlayerEntityFeature.SELECT_SOUND_MODE
    )

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "media_player")

    @property
    def state(self) -> MediaPlayerState:
        return MediaPlayerState.OFF if self.status.get("stby") else MediaPlayerState.ON

    @property
    def volume_level(self) -> float | None:
        level = self.status.get("main_level")
        return None if level is None else level / LEVEL_MAX

    @property
    def is_volume_muted(self) -> bool | None:
        return self.status.get("muted")

    @property
    def source(self) -> str | None:
        index = self.status.get("current_input")
        return INPUTS[index] if index is not None and 0 <= index < len(INPUTS) else None

    @property
    def sound_mode(self) -> str | None:
        if self.status.get("decode_mode"):
            return None
        index = self.status.get("current_fx")
        return EFFECTS[index] if index is not None and 0 <= index < len(EFFECTS) else None

    async def async_turn_on(self) -> None:
        await self._command("/power/on")

    async def async_turn_off(self) -> None:
        await self._command("/power/off")

    async def async_set_volume_level(self, volume: float) -> None:
        await self._set_level("main", volume * LEVEL_MAX)

    async def async_volume_up(self) -> None:
        await self._command("/volume/main/up")

    async def async_volume_down(self) -> None:
        await self._command("/volume/main/down")

    async def async_mute_volume(self, mute: bool) -> None:
        await self._command("/mute/on" if mute else "/mute/off")

    async def async_select_source(self, source: str) -> None:
        await self._command(f"/input/{INPUTS.index(source)}")

    async def async_select_sound_mode(self, sound_mode: str) -> None:
        await self._command(f"/input/effect/{EFFECTS.index(sound_mode)}")
