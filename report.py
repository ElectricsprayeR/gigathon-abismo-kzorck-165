"""report.py — Final mission report builder."""

import json
from pathlib import Path
from typing import Any

_CFG_PATH = Path(__file__).parent / "config.json"
with open(_CFG_PATH, "r", encoding="utf-8") as _f:
    CFG: dict = json.load(_f)

_DIFFICULTY_LABELS: dict[str, str] = {
    "facil": "Facil",
    "normal": "Normal",
    "dificil": "Dificil",
}

_RESULT_LABELS: dict[str, str] = {
    "WIN_FULL": "EXITO TOTAL",
    "WIN_PARTIAL": "EXITO PARCIAL",
    "LOSE_OXY": "FRACASO — ASFIXIA",
    "LOSE_HULL": "FRACASO — IMPLOSION",
    "LOSE_STEPS": "FRACASO — TIEMPO AGOTADO",
    "LOSE_BOUNDS": "FRACASO — NAVEGACION ERRATICA",
    "QUIT": "ABANDONO VOLUNTARIO",
}


def _element_name(type_id: str) -> str:
    return CFG["elements"].get(type_id, {}).get("name_es", type_id)


def _event_name(event_id: str) -> str:
    return CFG["events"].get(event_id, {}).get("name_es", event_id)


def _sep(char: str = "=", width: int = 48) -> str:
    return char * width


def print_report(result: dict[str, Any]) -> None:
    params: dict = result["initial_params"]
    final_res: dict = result["final_resources"]
    end_id: str = result["end_condition_id"]
    final_result: str = result["final_result"]
    visited: list[tuple[int, int, str]] = result["visited_elements"]
    events_suffered: list[str] = result["suffered_events"]

    lines: list[str] = []
    w = _sep

    lines.append(w())
    lines.append("INFORME FINAL DE MISION — SUBMARINO ABISMO")
    lines.append(w())

    lines.append("")
    lines.append("IDENTIFICACION")
    lines.append(w("-"))
    lines.append(f"  Capitan      : {result['captain_name']}")
    lines.append(f"  Submarino    : {result['sub_name']}")

    lines.append("")
    lines.append("PARAMETROS INICIALES")
    lines.append(w("-"))
    lines.append(f"  Posicion inicial : ({params['x0']}, {params['y0']})")
    lines.append(f"  Oxigeno inicial  : {params['oxygen']}")
    lines.append(f"  Dificultad       : {_DIFFICULTY_LABELS.get(params['difficulty'], params['difficulty'])}")
    diff_cfg = CFG["difficulty"][params["difficulty"]]
    lines.append(f"  Limite de turnos : {diff_cfg['step_limit']}")
    lines.append(f"  Limites del mundo: x [{CFG['world']['x_min']}, {CFG['world']['x_max']}]  "
                 f"y [{CFG['world']['y_min']}, {CFG['world']['y_max']}]")

    lines.append("")
    lines.append("RESULTADO DE LA EXPEDICION")
    lines.append(w("-"))
    fx, fy = result["final_position"]
    lines.append(f"  Posicion final   : ({fx}, {fy})")
    lines.append(f"  Turnos jugados   : {result['steps']}")
    lines.append(f"  Oxigeno final    : {final_res['oxygen']}")
    lines.append(f"  Bateria final    : {final_res['battery']}")
    lines.append(f"  Casco final      : {final_res['hull']}")

    lines.append("")
    lines.append("EL ATALAYA")
    lines.append(w("-"))
    ax, ay = result["atalaya_position"]
    lines.append(f"  Posicion real    : ({ax}, {ay})")
    found_label = "Si" if result["atalaya_found"] else "No"
    lines.append(f"  Localizado       : {found_label}")

    lines.append("")
    lines.append("ELEMENTOS VISITADOS")
    lines.append(w("-"))
    if visited:
        seen_types: list[str] = []
        for _x, _y, type_id in visited:
            label = f"{_element_name(type_id)} ({_x}, {_y})"
            if label not in seen_types:
                seen_types.append(label)
        for item in seen_types:
            lines.append(f"  - {item}")
    else:
        lines.append("  Ninguno.")

    lines.append("")
    lines.append("EVENTOS SUFRIDOS")
    lines.append(w("-"))
    if events_suffered:
        for ev_id in events_suffered:
            lines.append(f"  - {_event_name(ev_id)} ({ev_id})")
    else:
        lines.append("  Ninguno.")

    lines.append("")
    lines.append("CAUSA DE FINALIZACION")
    lines.append(w("-"))
    lines.append(f"  Codigo  : {end_id}")
    lines.append(f"  Detalle : {_RESULT_LABELS.get(end_id, end_id)}")

    lines.append("")
    lines.append("RESULTADO FINAL")
    lines.append(w("-"))
    result_label = _RESULT_LABELS.get(final_result, final_result)
    lines.append(f"  {result_label}")
    narrative = CFG["narratives"].get(final_result, "")
    if narrative:
        lines.append(f"  {narrative}")

    lines.append("")
    lines.append(w())

    print("\n".join(lines))
