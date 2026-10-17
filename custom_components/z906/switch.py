"""Dolby Digital / DTS 5.1 decoding."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import Z906ConfigEntry
from .entity import Z906Entity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Z906ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([Z906DecodeSwitch(entry.runtime_data)])


class Z906DecodeSwitch(Z906Entity, SwitchEntity):
    """5.1 decoding on the digital inputs."""

    _attr_translation_key = "decode"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "decode")

    @property
    def is_on(self) -> bool | None:
        return self.status.get("decode_mode")

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._command("/input/decode/on")

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._command("/input/decode/off")
