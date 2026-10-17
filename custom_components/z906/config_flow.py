"""Config flow: manual host entry and zeroconf discovery."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .api import Z906Client, Z906Error
from .const import DOMAIN

TITLE = "Logitech Z906"


class Z906ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add a Z906RemoteESP32 board."""

    VERSION = 1

    def __init__(self) -> None:
        self._host: str | None = None
        self._name: str | None = None

    async def _async_info(self, host: str) -> dict[str, Any]:
        return await Z906Client(async_get_clientsession(self.hass), host).info()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            try:
                info = await self._async_info(host)
            except Z906Error:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(format_mac(info["mac"]))
                self._abort_if_unique_id_configured(updates={CONF_HOST: host})
                return self.async_create_entry(title=TITLE, data={CONF_HOST: host})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
            errors=errors,
        )

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        mac = discovery_info.properties.get("mac")
        if not mac:
            return self.async_abort(reason="not_supported")
        self._host = discovery_info.host
        await self.async_set_unique_id(format_mac(mac))
        # Follows a new DHCP address of an already added board
        self._abort_if_unique_id_configured(updates={CONF_HOST: self._host})

        try:
            await self._async_info(self._host)
        except Z906Error:
            return self.async_abort(reason="cannot_connect")

        self._name = discovery_info.hostname.removesuffix(".local.").removesuffix(".")
        self.context["title_placeholders"] = {"name": self._name}
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title=TITLE, data={CONF_HOST: self._host})
        self._set_confirm_only()
        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={"name": self._name or "", "host": self._host or ""},
        )
