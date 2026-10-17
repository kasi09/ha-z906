"""Center, rear and subwoofer levels."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import LEVEL_MAX
from .coordinator import Z906ConfigEntry
from .entity import Z906Entity

PARALLEL_UPDATES = 1

CHANNELS = ("center", "rear", "sub")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Z906ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities(Z906LevelNumber(entry.runtime_data, ch) for ch in CHANNELS)


class Z906LevelNumber(Z906Entity, NumberEntity):
    """Level of one channel group, 0-43 like the console."""

    _attr_native_min_value = 0
    _attr_native_max_value = LEVEL_MAX
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator, channel: str) -> None:
        super().__init__(coordinator, f"{channel}_level")
        self._channel = channel
        self._attr_translation_key = f"{channel}_level"

    @property
    def native_value(self) -> float | None:
        return self.status.get(f"{self._channel}_level")

    async def async_set_native_value(self, value: float) -> None:
        await self._set_level(self._channel, value)
