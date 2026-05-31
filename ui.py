"""ui.py — All terminal I/O: prompts, validation, turn display, banners."""

import json
import sys
from pathlib import Path

_CFG_PATH = Path(__file__).parent / "config.json"
with open(_CFG_PATH, "r", encoding="utf-8") as _f:
    _CFG: dict = json.load(_f)

_LINE_WIDE = "=" * 64
_LINE_THIN = "-" * 64

_ACTION_LABELS: dict[str, str] = {
    "N": "Mover norte (+y, subir)",
    "S": "Mover sur   (-y, bajar)",
    "E": "Mover este  (+x)",
    "O": "Mover oeste (-x)",
    "escanear": "Revelar elementos en radio 10  [-5 bateria]",
    "esperar": "Reparar casco +5               [-2 bateria, -2 oxigeno]",
    "salir": "Abandonar mision               [fracaso voluntario]",
}


def _safe_input(prompt: str) -> str:
    try:
        return input(prompt)
    except (KeyboardInterrupt, EOFError):
        print("\nMision cancelada. Hasta la proxima, capitan.")
        sys.exit(0)


def _prompt_string(label: str, default: str, min_len: int, max_len: int, max_attempts: int) -> str:
    for attempt in range(max_attempts):
        raw = _safe_input(f"{label} [default: {default}]: ").strip()
        remaining = max_attempts - attempt - 1
        if not raw:
            if remaining:
                print(f"  El nombre no puede estar vacio. Intentos restantes: {remaining}.")
                continue
            break
        if not (min_len <= len(raw) <= max_len):
            if remaining:
                print(f"  Longitud invalida ({len(raw)}). Entre {min_len} y {max_len} caracteres. "
                      f"Intentos restantes: {remaining}.")
                continue
            break
        return raw
    print(f"  Demasiados intentos fallidos. Usando valor por defecto: '{default}'.")
    return default


def _prompt_int(label: str, min_val: int, max_val: int, default: int, max_attempts: int) -> int:
    for attempt in range(max_attempts):
        raw = _safe_input(f"{label} [default: {default}]: ").strip()
        if not raw:
            print(f"  Usando valor por defecto: {default}.")
            return default
        remaining = max_attempts - attempt - 1
        try:
            value = int(raw)
        except ValueError:
            if remaining:
                print(f"  Valor no valido. Introduce un numero entero. Intentos restantes: {remaining}.")
                continue
            break
        if not (min_val <= value <= max_val):
            if remaining:
                print(f"  Fuera de rango. El valor debe estar entre {min_val} y {max_val}. "
                      f"Intentos restantes: {remaining}.")
                continue
            break
        return value
    print(f"  Demasiados intentos fallidos. Usando valor por defecto: {default}.")
    return default


def _prompt_choice(label: str, choices: list[str], default: str, max_attempts: int) -> str:
    options = " / ".join(choices)
    for attempt in range(max_attempts):
        raw = _safe_input(f"{label} ({options}) [default: {default}]: ").strip().lower()
        if not raw:
            print(f"  Usando valor por defecto: {default}.")
            return default
        if raw in choices:
            return raw
        remaining = max_attempts - attempt - 1
        if remaining:
            print(f"  Opcion no valida. Elige entre: {options}. Intentos restantes: {remaining}.")
    print(f"  Demasiados intentos fallidos. Usando valor por defecto: {default}.")
    return default


_END_CONDITION_DESCRIPTIONS: dict[str, str] = {
    "WIN_FULL":    "Victoria: Atalaya localizado y regreso a la base con recursos positivos.",
    "LOSE_HULL":   "Derrota: el casco llega a cero (implosion).",
    "LOSE_OXY":    "Derrota: el oxigeno llega a cero (asfixia).",
    "LOSE_BOUNDS": "Derrota: cinco salidas del area de operaciones.",
    "LOSE_STEPS":  "Derrota: limite de turnos agotado sin completar objetivos.",
    "QUIT":        "Abandono voluntario de la mision.",
}


def print_mission_briefing(params: dict, world: object, difficulty_cfg: dict) -> None:
    world_cfg = _CFG["world"]
    zone = world.known_atalaya_zone

    print()
    print(_LINE_WIDE)
    print("   BRIEFING DE MISION")
    print(_LINE_WIDE)
    print(f"Capitan:        {params['captain_name']}")
    print(f"Submarino:      {params['submarine_name']}")
    print(f"Posicion inicial: ({params['x0']}, {params['y0']})")
    print()
    print("Recursos iniciales:")
    print(f"  Oxigeno:  {params['oxygen']}")
    print(f"  Bateria:  {_CFG['resources']['battery_initial']}")
    print(f"  Casco:    {_CFG['resources']['hull_initial']}")
    print()
    print("Limites del mundo:")
    print(f"  X: [{world_cfg['x_min']}, {world_cfg['x_max']}]")
    print(f"  Y: [{world_cfg['y_min']}, {world_cfg['y_max']}]  (y=0 es la superficie)")
    print(f"  Base de operaciones: ({world_cfg['base_x']}, {world_cfg['base_y']})")
    print()
    print("Zona sospechada del Atalaya:")
    print(f"  X: [{zone['x_min']}, {zone['x_max']}]")
    print(f"  Y: [{zone['y_min']}, {zone['y_max']}]")
    print()
    print("Dificultad:")
    print(f"  Limite de turnos:        {difficulty_cfg['step_limit']}")
    print(f"  Probabilidad de evento:  {int(difficulty_cfg['event_probability'] * 100)}% por turno")
    print()
    print("Condiciones de finalizacion:")
    for code, desc in _END_CONDITION_DESCRIPTIONS.items():
        print(f"  {code:<14} {desc}")
    print(_LINE_WIDE)
    print()


def print_banner() -> None:
    print(_LINE_WIDE)
    print("   ABISMO -- MISION DE RESCATE")
    print("   Gigathon 2026 -- Simulador de expedicion submarina")
    print(_LINE_WIDE)
    print("  Objetivo: localizar el buque Atalaya en la fosa abisal")
    print("            y regresar a la base con vida.")
    print(_LINE_WIDE)


def prompt_initial_params() -> dict:
    v = _CFG["validation"]
    diff_cfg = _CFG["difficulty"]
    max_attempts = v["max_attempts"]

    print()
    print("--- Configuracion de la mision ---")
    print()

    captain_name = _prompt_string(
        "Nombre del capitan (1-30 caracteres)",
        v["captain_name"]["default"],
        v["captain_name"]["min_length"],
        v["captain_name"]["max_length"],
        max_attempts,
    )

    submarine_name = _prompt_string(
        "Nombre del submarino (1-30 caracteres)",
        v["submarine_name"]["default"],
        v["submarine_name"]["min_length"],
        v["submarine_name"]["max_length"],
        max_attempts,
    )

    difficulty = _prompt_choice(
        "Nivel de dificultad",
        v["difficulty"]["choices"],
        v["difficulty"]["default"],
        max_attempts,
    )

    x0 = _prompt_int(
        f"Posicion inicial X ({v['x_initial']['min']} a {v['x_initial']['max']})",
        v["x_initial"]["min"],
        v["x_initial"]["max"],
        v["x_initial"]["default"],
        max_attempts,
    )

    y0 = _prompt_int(
        f"Posicion inicial Y ({v['y_initial']['min']} a {v['y_initial']['max']})",
        v["y_initial"]["min"],
        v["y_initial"]["max"],
        v["y_initial"]["default"],
        max_attempts,
    )

    oxy_default = diff_cfg[difficulty]["oxygen_initial"]
    oxy_min = v["oxygen_initial"]["min"]
    oxy_max = v["oxygen_initial"]["max"]
    oxygen = _prompt_int(
        f"Oxigeno inicial ({oxy_min} a {oxy_max}, sugerido para {difficulty}: {oxy_default})",
        oxy_min,
        oxy_max,
        oxy_default,
        max_attempts,
    )

    return {
        "captain_name": captain_name,
        "submarine_name": submarine_name,
        "difficulty": difficulty,
        "x0": x0,
        "y0": y0,
        "oxygen": oxygen,
    }


def prompt_action() -> str:
    print()
    print("Acciones disponibles:")
    for key, label in _ACTION_LABELS.items():
        print(f"  {key:<10} {label}")

    while True:
        raw = _safe_input("Accion > ").strip()
        upper = raw.upper()
        lower = raw.lower()
        if upper in {"N", "S", "E", "O"}:
            return upper
        if lower in {"escanear", "esperar", "salir"}:
            return lower
        print("  Entrada no valida. Elige una accion del menu anterior.")


def print_turn(turn_data: dict) -> None:
    step: int = turn_data["step"]
    action: str = turn_data["action"]
    pb = turn_data["pos_before"]
    pa = turn_data["pos_after"]
    rb = turn_data["resources_before"]
    ra = turn_data["resources_after"]
    element: str = turn_data.get("element") or "ninguno."
    event: str = turn_data.get("event") or "ninguno."
    cause: str = turn_data["cause"]

    action_label = _ACTION_LABELS.get(action, action)

    oxy_b, oxy_a = rb["oxygen"], ra["oxygen"]
    bat_b, bat_a = rb["battery"], ra["battery"]
    hul_b, hul_a = rb["hull"], ra["hull"]

    def _delta(before: int, after: int) -> str:
        diff = after - before
        if diff == 0:
            return ""
        sign = "+" if diff > 0 else ""
        return f"  ({sign}{diff})"

    print(_LINE_WIDE)
    print(f"TURNO {step}")
    print(_LINE_THIN)
    print(f"Accion elegida: {action_label}")
    print(f"Posicion:  ({pb[0]}, {pb[1]})  ->  ({pa[0]}, {pa[1]})")
    print("Recursos:")
    print(f"  Oxigeno: {oxy_b} -> {oxy_a}{_delta(oxy_b, oxy_a)}")
    print(f"  Bateria: {bat_b} -> {bat_a}{_delta(bat_b, bat_a)}")
    print(f"  Casco:   {hul_b} -> {hul_a}{_delta(hul_b, hul_a)}")
    print(f"Elemento: {element}")
    print(f"Evento:   {event}")
    print(f"Causa: {cause}")
    print(_LINE_WIDE)


def ask_restart() -> bool:
    while True:
        raw = _safe_input("Iniciar nueva mision? (s/n): ").strip().lower()
        if raw in {"s", "si", "sí"}:
            return True
        if raw in {"n", "no"}:
            return False
        print("  Responde 's' para si o 'n' para no.")


def print_farewell() -> None:
    print()
    print(_LINE_WIDE)
    print("   Mision concluida. Que las profundidades guarden sus secretos.")
    print("   Hasta la proxima expedicion, capitan.")
    print(_LINE_WIDE)
