"""
events.py — Random event pool and dispatcher.

All event metadata and probabilities are loaded from config.json.
No I/O occurs here; descriptions are returned as strings for ui.py to render.
"""

import json
import math
import random
from pathlib import Path
from typing import Optional

from entities import Submarine, World

_CFG_PATH = Path(__file__).parent / "config.json"
with open(_CFG_PATH, "r", encoding="utf-8") as _f:
    _CFG: dict = json.load(_f)

_EVENT_IDS: list[str] = list(_CFG["events"].keys())


def maybe_trigger_event(
    submarine: Submarine,
    world: World,
    difficulty_config: dict,
    rng: random.Random,
) -> Optional[tuple[str, str]]:
    if rng.random() >= difficulty_config["event_probability"]:
        return None

    event_id = rng.choice(_EVENT_IDS)
    description = _dispatch(event_id, submarine, world, rng)
    submarine.suffered_events.append(event_id)
    return event_id, description


def _dispatch(
    event_id: str, submarine: Submarine, world: World, rng: random.Random
) -> str:
    return {
        "LEAK": _apply_leak,
        "GHOST": _apply_ghost,
        "BEACON": _apply_beacon,
        "BIOLUM": _apply_biolum,
        "LANDSLIDE": _apply_landslide,
    }[event_id](submarine, world, rng)


def _apply_leak(submarine: Submarine, world: World, rng: random.Random) -> str:
    amount = _CFG["events"]["LEAK"]["effect"]["oxygen_damage"]
    submarine.apply_cost("oxygen", amount)
    return f"Microfuga detectada. Oxigeno reducido en {amount} unidades."


def _apply_ghost(submarine: Submarine, world: World, rng: random.Random) -> str:
    submarine.state_flags["ghost_scan_active"] = True
    return "Interferencia en el sonar. El proximo escaneo devolvera datos falsos."


def _apply_beacon(submarine: Submarine, world: World, rng: random.Random) -> str:
    submarine.state_flags["beacon_active"] = True
    dx = world.atalaya_x - submarine.x
    dy = world.atalaya_y - submarine.y
    parts = []
    if dy > 0:
        parts.append("norte")
    elif dy < 0:
        parts.append("sur")
    if dx > 0:
        parts.append("este")
    elif dx < 0:
        parts.append("oeste")
    direction = "-".join(parts) if parts else "posicion actual"
    return f"Faro de emergencia captado. El Atalaya se encuentra al {direction}."


def _apply_biolum(submarine: Submarine, world: World, rng: random.Random) -> str:
    radius = _CFG["events"]["BIOLUM"]["effect"]["reveal_elements_radius"]
    names_es = {k: v["name_es"] for k, v in _CFG["elements"].items()}
    revealed = [
        el
        for (ex, ey), el in world.placed_elements.items()
        if not el.used
        and math.sqrt((ex - submarine.x) ** 2 + (ey - submarine.y) ** 2) <= radius
    ]
    if not revealed:
        return "Banco bioluminiscente. No se detectan elementos proximos en el radio de iluminacion."
    parts = [f"{names_es.get(el.type_id, el.type_id)} en ({el.x},{el.y})" for el in revealed]
    return f"Banco bioluminiscente. Elementos revelados: {', '.join(parts)}."


def _apply_landslide(submarine: Submarine, world: World, rng: random.Random) -> str:
    adjacent = [
        (submarine.x + dx, submarine.y + dy)
        for dx in (-1, 0, 1)
        for dy in (-1, 0, 1)
        if (dx, dy) != (0, 0) and world.in_bounds(submarine.x + dx, submarine.y + dy)
    ]
    if not adjacent:
        return "Derrumbe submarino. Ninguna coordenada adyacente disponible para bloquear."
    tile = rng.choice(adjacent)
    world.blocked_tiles.add(tile)
    return f"Derrumbe submarino. La coordenada {tile} ha quedado bloqueada permanentemente."
