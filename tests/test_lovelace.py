"""The example dashboards only use entity IDs the integration creates."""

from pathlib import Path

import pytest
import yaml

from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.z906.const import DOMAIN

from .conftest import HOST, UNIQUE_ID

LOVELACE = Path(__file__).parent.parent / "lovelace"


def _entities(node) -> set[str]:
    found: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "entity" and isinstance(value, str):
                found.add(value)
            else:
                found |= _entities(value)
    elif isinstance(node, list):
        for item in node:
            found |= _entities(item)
    return found


@pytest.mark.usefixtures("no_events")
@pytest.mark.parametrize("file", sorted(p.name for p in LOVELACE.glob("*.yaml")))
async def test_dashboard_entities_exist(hass: HomeAssistant, device, file: str) -> None:
    # The YAML files target a German Home Assistant
    hass.config.language = "de"
    entry = MockConfigEntry(domain=DOMAIN, unique_id=UNIQUE_ID, data={CONF_HOST: HOST})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    wanted = _entities(yaml.safe_load((LOVELACE / file).read_text(encoding="utf-8")))
    assert wanted
    missing = sorted(e for e in wanted if hass.states.get(e) is None)
    assert not missing, f"{file}: {missing}, existing: {sorted(hass.states.async_entity_ids())}"
