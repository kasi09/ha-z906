"""Amplifier temperature, input level and board diagnostics."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import Z906ConfigEntry, Z906Coordinator, Z906Data
from .entity import Z906Entity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class Z906SensorDescription(SensorEntityDescription):
    value_fn: Callable[[Z906Data], Any]
    # Board diagnostics stay available while the amplifier is off the bus
    needs_amplifier: bool = True


SENSORS: tuple[Z906SensorDescription, ...] = (
    Z906SensorDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.temperature,
    ),
    Z906SensorDescription(
        key="input_level",
        translation_key="input_level",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.input_level,
    ),
    Z906SensorDescription(
        key="rssi",
        translation_key="rssi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        needs_amplifier=False,
        value_fn=lambda d: d.health.get("rssi"),
    ),
    Z906SensorDescription(
        key="brownouts",
        translation_key="brownouts",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        needs_amplifier=False,
        value_fn=lambda d: d.health.get("brownouts"),
    ),
    Z906SensorDescription(
        key="uptime",
        translation_key="uptime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        needs_amplifier=False,
        value_fn=lambda d: d.health.get("uptime"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Z906ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities(Z906Sensor(entry.runtime_data, desc) for desc in SENSORS)


class Z906Sensor(Z906Entity, SensorEntity):
    entity_description: Z906SensorDescription

    def __init__(self, coordinator: Z906Coordinator, description: Z906SensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        if self.entity_description.needs_amplifier:
            return super().available
        return self.coordinator.last_update_success

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data)
