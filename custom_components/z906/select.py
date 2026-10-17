"""Sound mode (effect) of the current input."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import EFFECT_KEYS
from .coordinator import Z906ConfigEntry
from .entity import Z906Entity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Z906ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([Z906EffectSelect(entry.runtime_data)])


class Z906EffectSelect(Z906Entity, SelectEntity):
    """3D, 2.1, 4.1 or off."""

    _attr_translation_key = "effect"
    _attr_options = EFFECT_KEYS

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "effect")

    @property
    def current_option(self) -> str | None:
        index = self.status.get("current_fx")
        return EFFECT_KEYS[index] if index is not None and 0 <= index < len(EFFECT_KEYS) else None

    async def async_select_option(self, option: str) -> None:
        await self._command(f"/input/effect/{EFFECT_KEYS.index(option)}")
