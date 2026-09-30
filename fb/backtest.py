"""Backtest de patrones y mapa de probabilidades en partidos terminados."""
from __future__ import annotations

from collections import defaultdict

from .modelo import Modelo, cuota_minima
from .partidos import Partido
from .patrones import CHECKPOINTS, cargar as cargar_patrones, evaluar_en_partido
from .stats import binom_p_mayor, brier, shrink, tabla_fiabilidad, wilson


def correr_patrones(partidos: list[Partido], modelo: Modelo) -> dict[str, dict]:
    cfg = cargar_patrones()
    out = {}
    for cod in cfg:
        casos = []
        for p in partidos:
            for c in evaluar_en_partido(cod, p, cfg):
                c["partido"] = p.nombre
                c["liga"] = p.liga
                c["p_modelo"] = _p_modelo(cod, c, p, modelo)
                casos.append(c)
        n = len(casos)
        k = sum(c["exito"] for c in casos)
        lo, hi = wilson(k, n)
        p_mod = [c["p_modelo"] for c in casos if c["p_modelo"] is not None]
        por_liga = defaultdict(lambda: [0, 0])
        for c in casos:
            por_liga[c["liga"]][0] += c["exito"]
            por_liga[c["liga"]][1] += 1
        tasa = k / n if n else 0.0
        ranking = sorted(
            ({"liga": l, "k": kk, "n": nn, "tasa": kk / nn, "tasa_ajustada": shrink(kk, nn, tasa, 8)}
             for l, (kk, nn) in por_liga.items()),
            key=lambda r: -r["tasa_ajustada"])
        out[cod] = {
            "n": n, "k": k, "tasa": tasa, "lo": lo, "hi": hi,
            "p_modelo_media": sum(p_mod) / len(p_mod) if p_mod else None,
            "cuota_min": cuota_minima(shrink(k, n, 0.5, 4)) if n else None,
            "casos": casos, "ligas": ranking,
        }
    return out


def _p_modelo(cod: str, caso: dict, p: Partido, m: Modelo) -> float | None:
    e = caso["estado"]
    t = caso["minuto"]
    roja = e["hay_roja"]
    if cod in ("P1", "P3", "P5"):
        return m.prob_mas_goles(1, t, p.liga, roja)
    if cod == "A2":
        return m.prob_mas_goles(2, t, p.liga, roja)
    if cod in ("P2", "P6"):
        r = m.prob_1x2(e["gl"], e["gv"], t, p.liga, e["rojas_local"], e["rojas_visita"])
        return r["local"] if e["dif"] > 0 else r["visitante"]
    if cod == "P4":
        r = m.prob_1x2(e["gl"], e["gv"], t, p.liga, e["rojas_local"], e["rojas_visita"])
        return r["local"] if e["rojas_visita"] > e["rojas_local"] else r["visitante"]
    if cod == "A1":
        r = m.prob_1x2(e["gl"], e["gv"], t, p.liga, e["rojas_local"], e["rojas_visita"])
        return 1 - r["empate"]
    return None


# ------------------------------------------------------------------ mapa
def mapa_probabilidades(partidos: list[Partido], modelo: Modelo) -> list[dict]:
    """Frecuencia real de cada resultado según minuto, goles y diferencia.

    Cada partido aporta una observación por checkpoint. Las observaciones del
    mismo partido no son independientes; el intervalo es orientativo.
    """
    celdas = defaultdict(lambda: {"n": 0, "mas1": 0, "mas2": 0, "lider_gana": 0, "empate_sigue": 0, "p_mod": 0.0})
    for p in partidos:
        for c in CHECKPOINTS:
            e = p.estado(c)
            g = min(e["goles"], 3)
            d = min(abs(e["dif"]), 2)
            key = (c, g, d)
            x = celdas[key]
            gh, ga = p.goles_despues(c)
            x["n"] += 1
            x["mas1"] += gh + ga >= 1
            x["mas2"] += gh + ga >= 2
            h, a = p.final
            if e["dif"] > 0:
                x["lider_gana"] += h > a
            elif e["dif"] < 0:
                x["lider_gana"] += a > h
            else:
                x["empate_sigue"] += h == a
            x["p_mod"] += modelo.prob_mas_goles(1, c, p.liga, e["hay_roja"])
    filas = []
    for (c, g, d), x in sorted(celdas.items()):
        n = x["n"]
        fila = {"minuto": c, "goles": g, "dif": d, "n": n,
                "mas1": x["mas1"] / n, "mas2": x["mas2"] / n, "p_mod_mas1": x["p_mod"] / n}
        if d > 0:
            fila["lider_gana"] = x["lider_gana"] / n
        else:
            fila["empate_sigue"] = x["empate_sigue"] / n
        fila["lo_mas1"], fila["hi_mas1"] = wilson(x["mas1"], n)
        filas.append(fila)
    return filas


# ------------------------------------------------------------------ calibración
def calibrar(partidos: list[Partido], k: int = 5) -> dict:
    """Validación cruzada: el modelo se ajusta sin el pliegue que predice."""
    pares = []
    for f in range(k):
        prueba = [p for i, p in enumerate(partidos) if i % k == f]
        entreno = [p for i, p in enumerate(partidos) if i % k != f]
        m = Modelo.ajustar(entreno)
        for p in prueba:
            for c in CHECKPOINTS:
                e = p.estado(c)
                gh, ga = p.goles_despues(c)
                pares.append((m.prob_mas_goles(1, c, p.liga, e["hay_roja"]), int(gh + ga >= 1)))
    base = sum(y for _, y in pares) / len(pares)
    return {"n": len(pares), "brier": brier(pares), "brier_base": brier([(base, y) for _, y in pares]),
            "fiabilidad": tabla_fiabilidad(pares)}


# ------------------------------------------------------------------ descubrimiento
def descubrir(partidos: list[Partido], min_n: int = 15, q: float = 0.10) -> list[dict]:
    """Busca situaciones repetidas con alta probabilidad y las valida por fecha.

    Descubre en la mitad más antigua y confirma en la más reciente. Solo
    sobreviven reglas con al menos `min_n` casos en descubrimiento y que pasan
    Benjamini-Hochberg contra el 70% en la mitad de validación.
    """
    from .stats import benjamini_hochberg
    orden = sorted(partidos, key=lambda p: p.fecha)
    mitad = len(orden) // 2
    antiguos, recientes = orden[:mitad], orden[mitad:]
    reglas = []
    for c in CHECKPOINTS:
        for gmin in (0, 1, 2, 3):
            for dif in (None, 0, 1, 2):
                for objetivo in ("mas1", "lider_gana"):
                    if objetivo == "lider_gana" and (dif in (None, 0)):
                        continue
                    reglas.append((c, gmin, dif, objetivo))

    def medir(ps, regla):
        c, gmin, dif, obj = regla
        k = n = 0
        for p in ps:
            e = p.estado(c)
            if e["goles"] < gmin:
                continue
            if dif is not None and min(abs(e["dif"]), 2) != dif:
                continue
            n += 1
            gh, ga = p.goles_despues(c)
            h, a = p.final
            if obj == "mas1":
                k += gh + ga >= 1
            else:
                k += (h > a) if e["dif"] > 0 else (a > h)
        return k, n

    candidatas = []
    for r in reglas:
        k, n = medir(antiguos, r)
        if n >= min_n and k / n >= 0.75:
            candidatas.append((r, k, n))
    pvals, filas = [], []
    for r, k, n in candidatas:
        k2, n2 = medir(recientes, r)
        pv = binom_p_mayor(k2, n2, 0.70) if n2 else 1.0
        pvals.append(pv)
        filas.append({"minuto": r[0], "goles_min": r[1], "dif": r[2], "objetivo": r[3],
                      "k_desc": k, "n_desc": n, "k_val": k2, "n_val": n2, "p_valor": pv})
    ok = benjamini_hochberg(pvals, q) if pvals else []
    for f, s in zip(filas, ok):
        f["confirmada"] = s
    return sorted(filas, key=lambda f: (-f["confirmada"], f["p_valor"]))


# ------------------------------------------------------------------ fuerza de equipos
def validar_equipos(partidos: list[Partido], fuerza: float = 3.0) -> dict:
    """¿Mejora el modelo con goles a favor/en contra de cada equipo?

    Para cada partido, los promedios de cada equipo salen de SUS OTROS partidos de
    la muestra (sin mirar el que se predice), contraídos hacia la media con
    `fuerza` partidos equivalentes. Compara Brier del ganador final y de 'llega
    otro gol' contra el modelo solo de liga, en los checkpoints de patrones.
    """
    base = Modelo.ajustar(partidos)
    media = sum(sum(p.final) for p in partidos) / len(partidos) / 2
    por_equipo: dict[str, list[tuple[int, int]]] = {}
    for p in partidos:
        por_equipo.setdefault(p.local, []).append((p.final[0], p.final[1]))
        por_equipo.setdefault(p.visitante, []).append((p.final[1], p.final[0]))

    def prom(eq, excluir):
        gs = list(por_equipo[eq])
        gs.remove(excluir)
        n = len(gs)
        gf = (sum(g for g, _ in gs) + media * fuerza) / (n + fuerza)
        gc = (sum(c for _, c in gs) + media * fuerza) / (n + fuerza)
        return gf, gc, n

    res = {"liga_1x2": [], "eq_1x2": [], "liga_gol": [], "eq_gol": [], "n": 0}
    for p in partidos:
        gfl, gcl, nl = prom(p.local, (p.final[0], p.final[1]))
        gfv, gcv, nv = prom(p.visitante, (p.final[1], p.final[0]))
        if min(nl, nv) < 2:
            continue
        res["n"] += 1
        eq = base.con_equipos(gfl, gcl, gfv, gcv)
        h, a = p.final
        real = "local" if h > a else "visitante" if a > h else "empate"
        for c in (0,) + CHECKPOINTS:
            e = p.estado(c)
            for mod, k in ((base, "liga"), (eq, "eq")):
                r = mod.prob_1x2(e["gl"], e["gv"], c, None if k == "eq" else p.liga, e["rojas_local"], e["rojas_visita"])
                res[f"{k}_1x2"].append(sum((r[x] - (x == real)) ** 2 for x in r))
                gh, ga = p.goles_despues(c)
                res[f"{k}_gol"].append((mod.prob_mas_goles(1, c, None if k == "eq" else p.liga, e["hay_roja"]) - (gh + ga >= 1)) ** 2)
    prom_ = lambda xs: sum(xs) / len(xs) if xs else float("nan")
    return {"partidos": res["n"], "predicciones": len(res["liga_1x2"]),
            "brier_1x2_liga": prom_(res["liga_1x2"]), "brier_1x2_equipos": prom_(res["eq_1x2"]),
            "brier_gol_liga": prom_(res["liga_gol"]), "brier_gol_equipos": prom_(res["eq_gol"])}


# ------------------------------------------------------------------ supuesto del marcador
def calibracion_por_estado(partidos: list[Partido], modelo: Modelo) -> list[dict]:
    """¿La probabilidad de otro gol depende del marcador? Real contra modelo por estado.

    El modelo supone que no: solo mira minuto, liga y rojas. Si una fila se aleja
    del modelo más que su intervalo, el supuesto falla en ese estado.
    """
    g: dict[tuple[str, str], list] = {}
    for p in partidos:
        for c in CHECKPOINTS:
            e = p.estado(c)
            d = abs(e["dif"])
            est = "empate" if d == 0 else "ventaja de 1" if d == 1 else "ventaja de 2+"
            fase = "hasta el 45'" if c <= 45 else "desde el 60'"
            gh, ga = p.goles_despues(c)
            x = g.setdefault((fase, est), [0, 0, 0.0])
            x[0] += 1
            x[1] += gh + ga >= 1
            x[2] += modelo.prob_mas_goles(1, c, p.liga, e["hay_roja"])
    filas = []
    for (fase, est), (n, k, pm) in sorted(g.items()):
        lo, hi = wilson(k, n)
        filas.append({"fase": fase, "estado": est, "n": n, "real": k / n, "lo": lo, "hi": hi, "modelo": pm / n,
                      "ok": lo <= pm / n <= hi})
    return filas
