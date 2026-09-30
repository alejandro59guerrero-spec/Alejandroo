"""Reglas de patrones.

El texto y los parámetros viven en `patterns/patrones.json`. Aquí se traduce
cada código a una condición sobre el estado del partido y a un resultado que
se mide en el backtest.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from .partidos import Partido

RAIZ = Path(__file__).resolve().parent.parent
JSON_PATRONES = RAIZ / "patterns" / "patrones.json"
CHECKPOINTS = (30, 45, 60, 70, 80)


def cargar() -> dict[str, dict]:
    data = json.loads(JSON_PATRONES.read_text(encoding="utf-8"))
    return {p["codigo"]: p for p in data["patrones"]}


def faltan_para_over(linea: float, goles: int) -> int:
    return max(0, math.floor(linea) + 1 - goles)


# ------------------------------------------------------------------ apuestas reales
def clasificar_apuesta(ap: dict, cfg: dict[str, dict]) -> list[str]:
    """Códigos que cumple una apuesta del usuario.

    `ap` necesita: mercado, minuto, gl, gv, lado (1x2), linea (over), roja
    ('no', 'local', 'visitante', 'ambos').
    """
    out = []
    m, gl, gv = ap["minuto"], ap["gl"], ap["gv"]
    goles = gl + gv
    roja = ap.get("roja", "no") not in ("no", "", None, "sin_dato")
    merc = ap["mercado"]
    if merc == "over" and ap.get("linea") is not None:
        p1 = cfg["P1"]["params"]
        falt = faltan_para_over(ap["linea"], goles)
        if goles >= p1["goles_min"] and falt == p1["faltan"] and m <= p1["minuto_max"]:
            out.append("P1")
        if goles == 0 and falt >= cfg["A2"]["params"]["faltan_min"]:
            out.append("A2")
    if roja and merc in ("over", "btts"):
        out.append("P3")
    if merc in ("1x2", "bb") and ap.get("lado") in ("local", "visitante"):
        propio, rival = (gl, gv) if ap["lado"] == "local" else (gv, gl)
        rival_lado = "visitante" if ap["lado"] == "local" else "local"
        if propio > rival and merc == "1x2":
            out.append("P2")
        if propio == rival:
            if ap.get("roja") == rival_lado:
                out.append("P4")
            out.append("A1")
    if merc == "corners":
        out.append("A3")
    return out


# ------------------------------------------------------------------ backtest
def _primer_checkpoint(p: Partido, cond) -> tuple[int, dict] | None:
    for c in CHECKPOINTS:
        est = p.estado(c)
        if cond(est):
            return c, est
    return None


def evaluar_en_partido(codigo: str, p: Partido, cfg: dict[str, dict]) -> list[dict]:
    """Casos del patrón en un partido terminado.

    Devuelve una lista de casos {minuto, estado, exito, detalle}. Como máximo un
    caso por partido y lado, en el primer checkpoint donde se cumple la condición.
    """
    casos = []
    if codigo == "P1":
        prm = cfg["P1"]["params"]
        hit = _primer_checkpoint(p, lambda e: e["goles"] >= prm["goles_min"] and e["minuto"] <= prm["minuto_max"])
        if hit:
            c, e = hit
            gh, ga = p.goles_despues(c)
            casos.append({"minuto": c, "estado": e, "exito": gh + ga >= 1,
                          "detalle": f"Over {e['goles'] + 0.5}"})
    elif codigo == "P2":
        hit = _primer_checkpoint(p, lambda e: abs(e["dif"]) >= cfg["P2"]["params"]["dif_min"])
        if hit:
            c, e = hit
            lider_local = e["dif"] > 0
            h, a = p.final
            casos.append({"minuto": c, "estado": e, "exito": (h > a) if lider_local else (a > h),
                          "detalle": f"Gana el {'local' if lider_local else 'visitante'} (ventaja {abs(e['dif'])})"})
    elif codigo == "P3":
        if not p.rojas_fiables or not p.rojas:
            return casos
        prm = cfg["P3"]["params"]
        hit = _primer_checkpoint(p, lambda e: e["hay_roja"] and e["minuto"] <= prm["minuto_max"])
        if hit:
            c, e = hit
            gh, ga = p.goles_despues(c)
            casos.append({"minuto": c, "estado": e, "exito": gh + ga >= 1,
                          "detalle": f"Over {e['goles'] + 0.5} tras roja"})
    elif codigo == "P4":
        if not p.rojas_fiables or not p.rojas:
            return casos
        hit = _primer_checkpoint(p, lambda e: e["dif"] == 0 and (e["rojas_local"] != e["rojas_visita"]))
        if hit:
            c, e = hit
            con_uno_mas_local = e["rojas_visita"] > e["rojas_local"]
            h, a = p.final
            casos.append({"minuto": c, "estado": e, "exito": (h > a) if con_uno_mas_local else (a > h),
                          "detalle": f"Gana el {'local' if con_uno_mas_local else 'visitante'} con uno más"})
    elif codigo == "A1":
        hit = _primer_checkpoint(p, lambda e: e["dif"] == 0 and e["minuto"] >= 45)
        if hit:
            c, e = hit
            h, a = p.final
            # éxito del anti-patrón = el empate se rompe (condición necesaria para ganar un 1x2)
            casos.append({"minuto": c, "estado": e, "exito": h != a,
                          "detalle": "El empate se rompe antes del final"})
    elif codigo == "A2":
        hit = _primer_checkpoint(p, lambda e: e["goles"] == 0 and e["minuto"] >= 45)
        if hit:
            c, e = hit
            gh, ga = p.goles_despues(c)
            casos.append({"minuto": c, "estado": e, "exito": gh + ga >= cfg["A2"]["params"]["faltan_min"],
                          "detalle": "Llegan 2 goles o más",
                          "extra": {"llega_1": gh + ga >= 1}})
    return casos
