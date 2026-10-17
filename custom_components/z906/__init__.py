"""The Logitech Z906 integration (Z906RemoteESP32 firmware)."""

from __future__ import annotations

from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import Z906Client, Z906Error
from .coordinator import Z906ConfigEntry, Z906Coordinator

PLATFORMS: list[Platform] = [
    Platform.MEDIA_PLAYER,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: Z906ConfigEntry) -> bool:
    """Set up a Z906 board from a config entry."""
    client = Z906Client(async_get_clientsession(hass), entry.data[CONF_HOST])
    try:
        info = await client.info()
    except Z906Error as err:
        raise ConfigEntryNotReady(f"{client.host} not reachable: {err}") from err

    coordinator = Z906Coordinator(hass, entry, client, info)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    # Cancelled automatically when the entry is unloaded
    entry.async_create_background_task(
        hass, coordinator.async_listen_events(), f"z906 events {client.host}"
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: Z906ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
