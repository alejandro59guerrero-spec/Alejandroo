"""Perfil de cada liga: tu historial en ella y sus tasas base en partidos terminados.

Las tasas base son lo mismo que muestran sitios de estadísticas como scores24
(goles por partido, Más de 2.5, Ambos marcan), pero calculadas sobre partidos
verificados gol a gol y con intervalo de confianza, más lo que importa en vivo:
cuánto pasa después del 75'.
"""
from __future__ import annotations

from analysis.validar_patrones import DATA, leer_csv

from .partidos import Partido
from .stats import wilson


def tasas_base(ps: list[Partido]) -> dict:
    n = len(ps)
    goles = [sum(p.final) for p in ps]
    o25 = sum(g >= 3 for g in goles)
    btts = sum(p.final[0] > 0 and p.final[1] > 0 for p in ps)
    tarde = sum(any(m is not None and m >= 75 for m, _ in p.goles) for p in ps)
    goles_2t = sum(1 for p in ps for m, _ in p.goles if m is not None and m > 45)
    total = sum(goles)
    return {
        "n": n,
        "goles_partido": total / n if n else None,
        "over25": o25 / n if n else None, "over25_ic": wilson(o25, n),
        "btts": btts / n if n else None,
        "gol_desde_75": tarde / n if n else None, "gol_desde_75_ic": wilson(tarde, n),
        "parte_2t": goles_2t / total if total else None,
    }


def tu_historial() -> dict[str, dict]:
    """Patas por liga: jugadas, ganadas y neto a stake 1 (como si fueran simples)."""
    out: dict[str, dict] = {}
    for r in leer_csv(DATA / "legs.csv"):
        x = out.setdefault(r["liga"], {"n": 0, "k": 0, "neto": 0.0, "cuotas": 0.0})
        gano = r["resultado"] == "W"
        c = float(r["cuota"])
        x["n"] += 1
        x["k"] += gano
        x["cuotas"] += c
        x["neto"] += (c - 1) if gano else -1
    for x in out.values():
        x["cuota_media"] = x.pop("cuotas") / x["n"]
    return out


def perfil(todos: list[Partido], factor_liga: dict[str, float], min_partidos: int = 4) -> dict:
    """Tabla de ligas con tu historial y tasas base, más la referencia de toda la muestra."""
    tuyo = tu_historial()
    por_liga: dict[str, list[Partido]] = {}
    for p in todos:
        por_liga.setdefault(p.liga, []).append(p)
    filas = []
    for liga in sorted(set(tuyo) | set(por_liga)):
        ps = por_liga.get(liga, [])
        t = tuyo.get(liga)
        if len(ps) < min_partidos and (not t or t["n"] < 3):
            continue  # una o dos patas sueltas no dicen nada de la liga
        filas.append({"liga": liga, "tuyo": t,
                      "base": tasas_base(ps) if len(ps) >= min_partidos else {"n": len(ps)},
                      "factor": factor_liga.get(liga)})
    filas.sort(key=lambda f: (-(f["base"]["n"]), -(f["tuyo"]["n"] if f["tuyo"] else 0)))
    return {"global": tasas_base(todos), "ligas": filas, "min_partidos": min_partidos}
