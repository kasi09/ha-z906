"""Base entity for the Logitech Z906."""

from __future__ import annotations

from typing import Any

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo, format_mac
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import Z906Error
from .const import DOMAIN
from .coordinator import Z906Coordinator


class Z906Entity(CoordinatorEntity[Z906Coordinator]):
    """Entity of one Z906, available while the amplifier answers."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: Z906Coordinator, key: str) -> None:
        super().__init__(coordinator)
        info = coordinator.info
        mac = format_mac(info["mac"])
        self._attr_unique_id = f"{mac}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac)},
            connections={(CONNECTION_NETWORK_MAC, mac)},
            name="Logitech Z906",
            manufacturer="Logitech",
            model="Z906",
            sw_version=info.get("firmware"),
            hw_version=info.get("chip"),
            configuration_url=coordinator.client.base_url,
        )

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.connected

    @property
    def status(self) -> dict[str, Any]:
        return self.coordinator.data.status

    async def _command(self, path: str, params: dict[str, Any] | None = None) -> None:
        try:
            await self.coordinator.async_command(path, params)
        except Z906Error as err:
            raise HomeAssistantError(f"Z906: {err}") from err

    async def _set_level(self, channel: str, level: float) -> None:
        try:
            await self.coordinator.async_set_level(channel, level)
        except Z906Error as err:
            raise HomeAssistantError(f"Z906: {err}") from err
