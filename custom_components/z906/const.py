"""Constants for the Logitech Z906 integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "z906"

# The amplifier reports levels as 0-43, /volume/<ch>/set takes 0-255
LEVEL_MAX = 43
RAW_MAX = 255

# Index = value of current_input and /input/<n>
INPUTS: list[str] = ["6-Kanal", "Cinch", "Optisch 1", "Optisch 2", "Koaxial", "AUX"]

# Index = value of current_fx and /input/effect/<n>
EFFECTS: list[str] = ["3D", "2.1", "4.1", "Off"]
EFFECT_KEYS: list[str] = ["3d", "2_1", "4_1", "off"]

POLL_INTERVAL = timedelta(seconds=30)
SSE_RETRY_MIN = 5
SSE_RETRY_MAX = 60
