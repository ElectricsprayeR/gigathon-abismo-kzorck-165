"""
entities.py — Core game objects: Submarine, World, Element.

All numeric constants are loaded from config.json at module load time.
No I/O occurs here; this file is pure data and logic.

Design note — single Element dataclass vs subclasses: all six element types
share identical structure (position, type id, consumed flag). Type-specific
behaviour is fully described by config.json data, so subclassing would add
indirection with no benefit.
"""

import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_CFG_PATH = Path(__file__).parent / "config.json"
with open(_CFG_PATH, "r", encoding="utf-8") as _f:
    CFG: dict = json.load(_f)


@dataclass
class Element:
    type_id: str
    x: int
    y: int
    used: bool = False


@dataclass
class Submarine:
    x: int
    y: int
    oxygen: int
    battery: int
    hull: int
    steps: int = 0
    visited_elements: set[tuple[int, int, str]] = field(default_factory=set)
    suffered_events: list[str] = field(default_factory=list)
    bound_violations: int = 0
    atalaya_found: bool = False
    state_flags: dict[str, object] = field(default_factory=dict)

    def is_alive(self) -> bool:
        r = CFG["resources"]
        return self.oxygen > r["oxygen_min"] and self.hull > r["hull_min"]

    def apply_cost(self, resource_name: str, amount: int) -> None:
        current = getattr(self, resource_name)
        setattr(self, resource_name, max(CFG["resources"].get(f"{resource_name}_min", 0), current - amount))

    def apply_gain(self, resource_name: str, amount: int, cap: Optional[int] = None) -> None:
        current = getattr(self, resource_name)
        new_val = current + amount
        if cap is not None:
            new_val = min(cap, new_val)
        setattr(self, resource_name, new_val)

    def set_resource(self, resource_name: str, value: int) -> None:
        setattr(self, resource_name, value)


class World:
    def __init__(self, difficulty: str, rng: random.Random) -> None:
        w = CFG["world"]
        self.x_min: int = w["x_min"]
        self.x_max: int = w["x_max"]
        self.y_min: int = w["y_min"]
        self.y_max: int = w["y_max"]
        self.base_x: int = w["base_x"]
        self.base_y: int = w["base_y"]

        zone = CFG["difficulty"][difficulty]["atalaya_zone"]
        self.atalaya_x: int = rng.randint(zone["x_min"], zone["x_max"])
        self.atalaya_y: int = rng.randint(zone["y_min"], zone["y_max"])

        self.known_atalaya_zone: dict = dict(zone)

        self.placed_elements: dict[tuple[int, int], Element] = {}
        self.blocked_tiles: set[tuple[int, int]] = set()

        self.place_elements(difficulty, rng)

    def in_bounds(self, x: int, y: int) -> bool:
        return self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max

    def element_at(self, x: int, y: int) -> Optional[Element]:
        return self.placed_elements.get((x, y))

    def place_elements(self, difficulty: str, rng: random.Random) -> None:
        counts = CFG["difficulty"][difficulty]["element_counts"]
        occupied: set[tuple[int, int]] = {
            (self.base_x, self.base_y),
            (self.atalaya_x, self.atalaya_y),
        }

        for type_id, count in counts.items():
            placed = 0
            attempts = 0
            max_attempts = count * 200
            while placed < count and attempts < max_attempts:
                x = rng.randint(self.x_min, self.x_max)
                y = rng.randint(self.y_min, self.y_max)
                pos = (x, y)
                if pos not in occupied:
                    occupied.add(pos)
                    self.placed_elements[pos] = Element(type_id=type_id, x=x, y=y)
                    placed += 1
                attempts += 1

    def distance_to_atalaya(self, x: int, y: int) -> float:
        return math.sqrt((x - self.atalaya_x) ** 2 + (y - self.atalaya_y) ** 2)
