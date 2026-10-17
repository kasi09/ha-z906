"""Config flow."""

from ipaddress import ip_address
from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.z906.api import Z906Error
from custom_components.z906.const import DOMAIN

from .conftest import HOST, INFO, MAC, UNIQUE_ID

INFO_PATH = "custom_components.z906.config_flow.Z906Client.info"
SETUP_PATH = "custom_components.z906.async_setup_entry"

DISCOVERY = ZeroconfServiceInfo(
    ip_address=ip_address(HOST),
    ip_addresses=[ip_address(HOST)],
    hostname="logitech-z906-xiao.local.",
    name="logitech-z906-xiao._z906._tcp.local.",
    port=80,
    type="_z906._tcp.local.",
    properties={"mac": MAC, "version": "2.3.0"},
)


async def test_user_flow(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    with patch(INFO_PATH, AsyncMock(return_value=INFO)), patch(SETUP_PATH, return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: HOST}
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_HOST: HOST}
    assert result["result"].unique_id == UNIQUE_ID


async def test_user_flow_cannot_connect(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(INFO_PATH, AsyncMock(side_effect=Z906Error("timeout"))):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: HOST}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_zeroconf_flow(hass: HomeAssistant) -> None:
    with patch(INFO_PATH, AsyncMock(return_value=INFO)):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=DISCOVERY
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "zeroconf_confirm"

    with patch(SETUP_PATH, return_value=True):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_HOST: HOST}
    assert result["result"].unique_id == UNIQUE_ID


async def test_zeroconf_updates_host(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=UNIQUE_ID, data={CONF_HOST: "192.0.2.99"}
    )
    entry.add_to_hass(hass)
    with patch(SETUP_PATH, return_value=True):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=DISCOVERY
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.data[CONF_HOST] == HOST
