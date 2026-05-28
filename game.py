"""
game.py — Turn loop, per-turn mechanics and end-condition evaluation.

Sets up the World and Submarine from the validated parameters and runs the
turn loop (pending drift, action resolution, element effects, oxygen decay,
random events) until an end condition fires (spec §10), then determines the
final result: full win, partial win, loss or voluntary quit.

All numeric constants are loaded from config.json. The only I/O performed
here is through ui (prompt_action, print_turn).
"""

import json
import math
import random
from pathlib import Path
from typing import Optional

import events
import ui
from entities import Element, Submarine, World

_CFG_PATH = Path(__file__).parent / "config.json"
with open(_CFG_PATH, "r", encoding="utf-8") as _f:
    CFG: dict = json.load(_f)

# Sanity guard against an unbounded loop. The real terminator is the
# end-condition check; LOSE_STEPS always fires at the step limit long before
# this cap, so it should never be the actual reason a mission ends.
_SANITY_CAP = 10000

_MOVE_ACTIONS = {"N", "S", "E", "O"}
_MOVE_VERB = {
    "N": "Ascenso al norte",
    "S": "Descenso al sur",
    "E": "Avance al este",
    "O": "Avance al oeste",
}


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def _snapshot(submarine: Submarine) -> dict:
    return {
        "oxygen": submarine.oxygen,
        "battery": submarine.battery,
        "hull": submarine.hull,
    }


def _element_names() -> dict[str, str]:
    return {key: val["name_es"] for key, val in CFG["elements"].items()}


def _build_scan_report(
    submarine: Submarine, world: World, rng: random.Random, radius: int
) -> str:
    """Return a Spanish scan description; corrupted if a ghost sonar is active."""
    names = _element_names()
    if submarine.state_flags.pop("ghost_scan_active", False):
        fake = []
        for _ in range(rng.randint(1, 3)):
            type_id = rng.choice(list(names.keys()))
            fx = rng.randint(world.x_min, world.x_max)
            fy = rng.randint(world.y_min, world.y_max)
            fake.append(f"{names[type_id]} en ({fx},{fy})")
        return "Escaneo corrompido por sonar fantasma: " + ", ".join(fake) + "."

    found = []
    for (ex, ey), el in world.placed_elements.items():
        if el.used:
            continue
        distance = math.sqrt((ex - submarine.x) ** 2 + (ey - submarine.y) ** 2)
        if distance <= radius:
            found.append(f"{names[el.type_id]} en ({ex},{ey})")
    if not found:
        return "Escaneo completado: sin elementos en el radio de barrido."
    return "Escaneo completado: " + ", ".join(found) + "."


def _narrow_known_zone(world: World, reduction_pct: int) -> None:
    """Shrink the suspected Atalaya zone toward its true position by reduction_pct."""
    factor = (100 - reduction_pct) / 100.0
    zone = world.known_atalaya_zone
    ax, ay = world.atalaya_x, world.atalaya_y
    zone["x_min"] = int(round(ax - (ax - zone["x_min"]) * factor))
    zone["x_max"] = int(round(ax + (zone["x_max"] - ax) * factor))
    zone["y_min"] = int(round(ay - (ay - zone["y_min"]) * factor))
    zone["y_max"] = int(round(ay + (zone["y_max"] - ay) * factor))


def _move_squid(world: World, element: Element, rng: random.Random) -> None:
    move_range = CFG["elements"]["SQUID"]["move_range"]
    candidates = [
        (element.x + dx, element.y + dy)
        for dx in range(-move_range, move_range + 1)
        for dy in range(-move_range, move_range + 1)
        if not (dx == 0 and dy == 0)
    ]
    valid = [
        pos
        for pos in candidates
        if world.in_bounds(pos[0], pos[1])
        and pos not in world.placed_elements
        and pos not in world.blocked_tiles
        and pos != (world.atalaya_x, world.atalaya_y)
    ]
    if not valid:
        return
    new_pos = rng.choice(valid)
    del world.placed_elements[(element.x, element.y)]
    element.x, element.y = new_pos
    world.placed_elements[new_pos] = element


def _apply_element(
    element: Element, submarine: Submarine, world: World, rng: random.Random
) -> str:
    """Apply one element's effect and return a Spanish description for the turn."""
    cfg = CFG["elements"][element.type_id]
    name = cfg["name_es"]
    effect = cfg["effect"]
    pos = f"({element.x},{element.y})"

    if element.type_id == "HYDRO":
        if element.used:
            return f"{name} en {pos}, ya agotada."
        submarine.set_resource("battery", effect["battery_set"])
        element.used = True
        return f"{name} en {pos}. Bateria recargada a {effect['battery_set']}."

    if element.type_id == "WRECK":
        if element.used:
            return f"{name} en {pos}, ya inspeccionados."
        _narrow_known_zone(world, effect["atalaya_range_reduction_pct"])
        element.used = True
        return (
            f"{name} en {pos}. Nueva pista: rango sospechado del Atalaya reducido "
            f"un {effect['atalaya_range_reduction_pct']}%."
        )

    if element.type_id == "CURRENT":
        dx = rng.randint(*effect["next_turn_drift_x_range"])
        dy = rng.randint(*effect["next_turn_drift_y_range"])
        submarine.state_flags["pending_drift"] = (dx, dy)
        return f"{name} en {pos}. Arrastre pendiente para el proximo turno: ({dx},{dy})."

    if element.type_id == "SQUID":
        damage = effect["hull_damage"]
        submarine.apply_cost("hull", damage)
        _move_squid(world, element, rng)
        return f"{name} en {pos}. Ataque: -{damage} casco."

    if element.type_id == "CAVE":
        if element.used:
            return f"{name} en {pos}, refugio ya utilizado."
        submarine.set_resource("hull", effect["hull_set"])
        element.used = True
        return f"{name} en {pos}. Refugio seguro: casco reparado a {effect['hull_set']}."

    if element.type_id == "PRESSURE":
        if element.used:
            return f"{name} en {pos}, ya liberada."
        element.used = True
        if rng.random() < effect["bonus_probability"]:
            submarine.state_flags["free_scan_available"] = True
            return f"{name} en {pos}. Bonus: proximo escaneo gratuito."
        penalty = effect["penalty_effect"]
        submarine.apply_cost("hull", penalty["hull_damage"])
        submarine.apply_cost("oxygen", penalty["oxygen_damage"])
        return (
            f"{name} en {pos}. Penalizacion: -{penalty['hull_damage']} casco, "
            f"-{penalty['oxygen_damage']} oxigeno."
        )

    return f"{name} en {pos}."


def _apply_action(
    action: str,
    submarine: Submarine,
    world: World,
    rng: random.Random,
    notes: list[str],
) -> None:
    """Resolve the chosen action, mutating submarine/world and appending cause notes."""
    if action in _MOVE_ACTIONS:
        cfg = CFG["actions"][action]
        submarine.apply_cost("battery", cfg["battery_cost"])
        target_x = submarine.x + cfg["dx"]
        target_y = submarine.y + cfg["dy"]
        if not world.in_bounds(target_x, target_y):
            submarine.bound_violations += 1
            notes.append(
                f"Movimiento bloqueado: limite del mundo. "
                f"Violaciones: {submarine.bound_violations}."
            )
        elif (target_x, target_y) in world.blocked_tiles:
            notes.append("Movimiento bloqueado: derrumbe en la coordenada destino.")
        else:
            submarine.x, submarine.y = target_x, target_y
            notes.append(f"{_MOVE_VERB[action]}.")
        return

    if action == "escanear":
        cfg = CFG["actions"]["escanear"]
        free = submarine.state_flags.pop("free_scan_available", False)
        if not free:
            submarine.apply_cost("battery", cfg["battery_cost"])
        report = _build_scan_report(submarine, world, rng, cfg["scan_radius"])
        notes.append(report + (" (escaneo gratuito)" if free else ""))
        return

    if action == "esperar":
        cfg = CFG["actions"]["esperar"]
        submarine.apply_cost("battery", cfg["battery_cost"])
        submarine.apply_cost("oxygen", cfg["oxygen_cost"])
        submarine.apply_gain(
            "hull", cfg["hull_repair"], cap=CFG["resources"]["hull_initial"]
        )
        notes.append(f"Espera y reparacion: +{cfg['hull_repair']} casco.")
        return

    if action == "salir":
        submarine.state_flags["quit"] = True
        notes.append("Mision abandonada voluntariamente por el capitan.")
        return


def _apply_oxygen_decay(submarine: Submarine) -> tuple[int, Optional[str]]:
    """Apply per-turn oxygen decay (depth-dependent). Returns (decay, note)."""
    res = CFG["resources"]
    world_cfg = CFG["world"]
    decay = res["oxygen_decay_base"]
    if submarine.y <= world_cfg["depth_penalty_threshold_1"]:
        decay += res["oxygen_decay_depth_1"]
    if submarine.y <= world_cfg["depth_penalty_threshold_2"]:
        decay += res["oxygen_decay_depth_2"]
    submarine.apply_cost("oxygen", decay)
    note = None
    if decay > res["oxygen_decay_base"]:
        note = f"Mayor consumo de oxigeno por profundidad (-{decay})."
    return decay, note


def _evaluate_end(
    submarine: Submarine, world: World, difficulty_config: dict
) -> Optional[str]:
    """Return the end-condition id if one fired this turn, else None (spec §10).

    Fixed evaluation order: hull, oxygen, bounds, steps, quit, full win.
    """
    res = CFG["resources"]
    end_cfg = CFG["end_conditions"]
    if submarine.hull <= res["hull_min"]:
        return "LOSE_HULL"
    if submarine.oxygen <= res["oxygen_min"]:
        return "LOSE_OXY"
    if submarine.bound_violations >= end_cfg["bound_violation_limit"]:
        return "LOSE_BOUNDS"
    if submarine.steps >= difficulty_config["step_limit"]:
        return "LOSE_STEPS"
    if submarine.state_flags.get("quit"):
        return "QUIT"
    at_base = (submarine.x, submarine.y) == (world.base_x, world.base_y)
    resources_ok = (
        submarine.oxygen > res["oxygen_min"]
        and submarine.battery > res["battery_min"]
        and submarine.hull > res["hull_min"]
    )
    # WIN_FULL is checked last, so reaching (0,0) with the Atalaya found and
    # resources still positive wins even if oxygen would deplete next turn.
    if at_base and submarine.atalaya_found and resources_ok:
        return "WIN_FULL"
    return None


def _determine_result(end_id: str, submarine: Submarine) -> str:
    """Map a fired end condition to the final mission result (spec §10, §13)."""
    if end_id == "WIN_FULL":
        return "WIN_FULL"
    # salir is always a voluntary quit: a captain at the goal would not choose
    # it, and _evaluate_end already ranks QUIT ahead of WIN_FULL.
    if end_id == "QUIT":
        return "QUIT"
    # Any losing end condition with the Atalaya already located is a partial
    # success (found it but did not make it home alive).
    if submarine.atalaya_found:
        return "WIN_PARTIAL"
    return end_id


def run_mission(params: dict, rng: random.Random) -> dict:
    """
    Set up the world and submarine from params and run the turn loop.

    Args:
        params: validated initial parameters (captain_name, submarine_name,
                difficulty, x0, y0, oxygen).
        rng: seeded random generator shared across the mission.

    Returns:
        A complete result dict describing how the mission ended (spec §13).
    """
    difficulty = params["difficulty"]
    difficulty_config = CFG["difficulty"][difficulty]
    res = CFG["resources"]

    world = World(difficulty, rng)
    submarine = Submarine(
        x=params["x0"],
        y=params["y0"],
        oxygen=params["oxygen"],
        battery=res["battery_initial"],
        hull=res["hull_initial"],
    )

    turn_history: list[dict] = []
    end_id: Optional[str] = None

    iterations = 0
    while iterations < _SANITY_CAP:
        iterations += 1

        pos_before = (submarine.x, submarine.y)
        resources_before = _snapshot(submarine)
        cause_parts: list[str] = []

        action = ui.prompt_action()

        drift = submarine.state_flags.pop("pending_drift", None)
        if drift is not None:
            submarine.x = _clamp(submarine.x + drift[0], world.x_min, world.x_max)
            submarine.y = _clamp(submarine.y + drift[1], world.y_min, world.y_max)
            cause_parts.append(
                f"Corriente abisal arrastra el submarino ({drift[0]},{drift[1]})."
            )

        notes: list[str] = []
        _apply_action(action, submarine, world, rng, notes)
        cause_parts.extend(notes)

        # Mark arrival before applying any same-tile element damage, so a
        # hull-killing element on the arrival turn still resolves to WIN_PARTIAL
        # (Atalaya found) rather than a plain loss.
        if (submarine.x, submarine.y) == (world.atalaya_x, world.atalaya_y) \
                and not submarine.atalaya_found:
            submarine.atalaya_found = True
            cause_parts.append(
                f"Atalaya localizado en ({world.atalaya_x}, {world.atalaya_y})."
            )

        element_desc: Optional[str] = None
        moved = (submarine.x, submarine.y) != pos_before
        if moved:
            element = world.element_at(submarine.x, submarine.y)
            if element is not None:
                ex, ey, etype = element.x, element.y, element.type_id
                element_desc = _apply_element(element, submarine, world, rng)
                submarine.visited_elements.add((ex, ey, etype))

        _, oxy_note = _apply_oxygen_decay(submarine)
        if oxy_note:
            cause_parts.append(oxy_note)

        event = events.maybe_trigger_event(submarine, world, difficulty_config, rng)
        event_desc = event[1] if event is not None else None

        submarine.steps += 1

        cause = " ".join(part for part in cause_parts if part) or "Turno sin incidencias."
        turn_data = {
            "step": submarine.steps,
            "action": action,
            "pos_before": pos_before,
            "pos_after": (submarine.x, submarine.y),
            "resources_before": resources_before,
            "resources_after": _snapshot(submarine),
            "element": element_desc,
            "event": event_desc,
            "cause": cause,
        }
        turn_history.append(turn_data)
        ui.print_turn(turn_data)

        end_id = _evaluate_end(submarine, world, difficulty_config)
        if end_id is not None:
            break

    # The loop only exits via _evaluate_end in practice (LOSE_STEPS guarantees
    # termination). A cap-out is treated as a time-out so the result is defined.
    if end_id is None:
        end_id = "LOSE_STEPS"

    final_result = _determine_result(end_id, submarine)

    return {
        "end_condition_id": end_id,
        "final_result": final_result,
        "captain_name": params["captain_name"],
        "sub_name": params["submarine_name"],
        "initial_params": params,
        "final_position": (submarine.x, submarine.y),
        "steps": submarine.steps,
        "final_resources": {
            "oxygen": submarine.oxygen,
            "battery": submarine.battery,
            "hull": submarine.hull,
        },
        "atalaya_position": (world.atalaya_x, world.atalaya_y),
        "atalaya_found": submarine.atalaya_found,
        "visited_elements": sorted(submarine.visited_elements),
        "suffered_events": list(submarine.suffered_events),
        "turn_history": turn_history,
    }
