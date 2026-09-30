"""Apuestas reales del usuario evaluadas con el modelo en vivo."""
from __future__ import annotations

import math

from analysis.validar_patrones import DATA, enriquecer, leer_csv

from .modelo import Modelo, cuota_minima, valor_esperado
from .patrones import cargar as cargar_patrones, clasificar_apuesta


def patas_en_vivo() -> list[dict]:
    tickets = {t["ticket_id"]: t for t in leer_csv(DATA / "tickets.csv")}
    return [e for e in enriquecer(leer_csv(DATA / "legs.csv"), tickets) if e["fase"] != "prepartido"]


def _rojas(e: dict) -> tuple[int, int]:
    r = e.get("roja_equipo", "no")
    return (1 if r in ("local", "ambos") else 0, 1 if r in ("visitante", "ambos") else 0)


def prob_apuesta(e: dict, m: Modelo) -> dict | None:
    """Probabilidad del modelo para la pata `e` en el estado en que se apostó."""
    if not e["con_dato"] or e["minuto"] == "":
        return None
    gl, gv = map(int, e["marcador_apuesta"].split(":"))
    minuto = int(e["minuto"])
    rl, rv = _rojas(e)
    liga = e.get("liga")
    merc = e["mercado"]
    linea = float(e["linea"]) if e.get("linea") else None
    lado = e.get("lado")
    nula = 0.0
    if merc == "over" and linea is not None:
        r = m.prob_over(linea, gl + gv, minuto, liga, roja=rl + rv > 0)
        p, nula = r["gana"], r["nula"]
    elif merc == "btts":
        p = m.prob_btts(gl, gv, minuto, liga, rl, rv)
    elif merc == "1x2" and lado in ("local", "visitante"):
        r = m.prob_1x2(gl, gv, minuto, liga, rl, rv)
        p = r[lado]
    elif merc == "dc" and lado in ("local", "visitante"):
        r = m.prob_1x2(gl, gv, minuto, liga, rl, rv)
        p = r[lado] + r["empate"]
    elif merc == "bb" and lado in ("local", "visitante") and linea is not None:
        umbral = math.floor(linea) + 1
        if lado == "local":
            p = m.prob_evento(gl, gv, minuto, lambda h, a: h > a and h + a >= umbral, liga, rl, rv)
        else:
            p = m.prob_evento(gl, gv, minuto, lambda h, a: a > h and h + a >= umbral, liga, rl, rv)
    elif merc == "bb" and "Ambos" in e.get("seleccion", ""):
        umbral = math.floor(linea or 2.5) + 1
        p = m.prob_evento(gl, gv, minuto, lambda h, a: h > 0 and a > 0 and h + a >= umbral, liga, rl, rv)
    elif merc == "clasifica" and lado in ("local", "visitante"):
        r = m.prob_1x2(gl, gv, minuto, liga, rl, rv)
        p = r[lado] + r["empate"] * 0.5  # prórroga o penales como moneda al aire
    else:
        return None
    cuota = float(e["cuota"])
    return {
        "p": p, "p_nula": nula, "cuota_min": cuota_minima(p) if p > 0 else float("inf"),
        "ev": valor_esperado(p, cuota, nula),
        "cuota": cuota, "gano": e["resultado"] == "W",
    }


def evaluar(m: Modelo) -> list[dict]:
    cfg = cargar_patrones()
    out = []
    for e in patas_en_vivo():
        r = prob_apuesta(e, m)
        if r is None:
            continue
        gl, gv = map(int, e["marcador_apuesta"].split(":"))
        ap = {"mercado": e["mercado"], "minuto": int(e["minuto"]), "gl": gl, "gv": gv,
              "lado": e.get("lado"), "linea": float(e["linea"]) if e.get("linea") else None,
              "roja": e.get("roja_equipo")}
        if e.get("roja_equipo") in ("local", "visitante") and e.get("lado") in ("local", "visitante"):
            ap["roja"] = e["roja_equipo"]
        r.update({"partido": e["partido"], "seleccion": e["seleccion"], "minuto": int(e["minuto"]),
                  "marcador": e["marcador_apuesta"], "mercado": e["mercado"], "tipo_ticket": e["tipo_ticket"],
                  "patrones": clasificar_apuesta(ap, cfg), "confianza": e["confianza"], "liga": e.get("liga", "")})
        out.append(r)
    return out
