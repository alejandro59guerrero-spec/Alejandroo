"""Reporte v2: Markdown para leer y JSON para la app."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from . import backtest, historial, ligas, partidos
from .modelo import Modelo, cuota_minima
from .patrones import cargar as cargar_patrones

RAIZ = Path(__file__).resolve().parent.parent
MD = RAIZ / "reports" / "analisis_v2.md"
JSON_APP = RAIZ / "patterns" / "datos_app.json"
JSON_MODELO = RAIZ / "patterns" / "modelo.json"


def pct(x):
    return "—" if x is None else f"{x * 100:.0f}%"


def semaforo(n: int, lo: float, cuota_media: float | None, n_tuyo: int = 0, tipo: str = "a_favor") -> str:
    """rojo: menos de 30 casos. verde: el límite inferior supera el break-even de TUS cuotas
    (solo con 5 apuestas tuyas o más para saber qué cuota tomas). Los anti-patrones no llevan color."""
    if tipo == "evitar":
        return "evitar"
    if n < 30:
        return "rojo"
    if cuota_media and n_tuyo >= 5 and lo > 1 / cuota_media:
        return "verde"
    return "ambar"


def _redondear(x):
    if isinstance(x, float):
        return round(x, 3)
    if isinstance(x, dict):
        return {k: _redondear(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_redondear(v) for v in x]
    return x


def generar() -> dict:
    cfg = cargar_patrones()
    bt = partidos.cargar(origen="backtest")
    todos = partidos.cargar()
    m = Modelo.ajustar(todos)
    m.guardar(JSON_MODELO)
    res = backtest.correr_patrones(bt, m)
    mapa = backtest.mapa_probabilidades(bt, m)
    cal = backtest.calibrar(todos)
    desc = backtest.descubrir(bt)
    ev = historial.evaluar(m)
    perfil = ligas.perfil(todos, m.factor_liga)
    equipos = backtest.validar_equipos(todos)
    from .hoja import cargar_hoy, hoja
    hoy = cargar_hoy()
    hoy = {"fecha": hoy.get("fecha"), "partidos": [hoja(m, pt) for pt in hoy["partidos"]]}

    # tus apuestas por patrón (patas en vivo con marcador reconstruido)
    tus = {}
    for cod in cfg:
        rows = [r for r in ev if cod in r["patrones"]]
        n = len(rows)
        k = sum(r["gano"] for r in rows)
        cm = sum(r["cuota"] for r in rows) / n if n else None
        tus[cod] = {"n": n, "k": k, "cuota_media": cm,
                    "neto": sum((r["cuota"] - 1) if r["gano"] else -1 for r in rows),
                    "ejemplos": [{"partido": r["partido"], "seleccion": r["seleccion"], "minuto": r["minuto"],
                                  "marcador": r["marcador"], "cuota": r["cuota"], "gano": r["gano"],
                                  "p_modelo": round(r["p"], 3)} for r in rows]}

    fichas = []
    for cod, p in cfg.items():
        r = res[cod]
        t = tus[cod]
        fichas.append({
            **{k: p[k] for k in ("codigo", "nombre", "tipo", "resumen", "mercado", "entrar_si", "no_entrar_si")},
            "backtest": {"n": r["n"], "k": r["k"], "tasa": r["tasa"], "lo": r["lo"], "hi": r["hi"],
                         "p_modelo": r["p_modelo_media"],
                         # en A1 el evento medido (se rompe el empate) no es una apuesta: sin cuota mínima
                         "cuota_min": None if cod == "A1" else r["cuota_min"],
                         "ligas": [{k2: (round(v, 3) if isinstance(v, float) else v) for k2, v in x.items()}
                                   for x in r["ligas"][:6]]},
            "tuyo": t,
            "semaforo": semaforo(r["n"] + t["n"], r["lo"], t["cuota_media"], t["n"], p["tipo"]),
        })

    # alertas de reconstrucción: la cuota tomada choca con el modelo
    alertas = [r for r in ev if abs(1 / r["cuota"] - r["p"]) > 0.35]

    datos = {
        "generado": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "muestra": {"backtest": len(bt), "total": len(todos),
                    "ligas": sorted({p.liga for p in bt})},
        "modelo": m.a_json(),
        "calibracion": {"n": cal["n"], "brier": round(cal["brier"], 4), "brier_base": round(cal["brier_base"], 4),
                        "fiabilidad": [[round(a, 2), round(b, 2), n, round(pm, 3), round(fr, 3)]
                                       for a, b, n, pm, fr in cal["fiabilidad"]]},
        "fichas": fichas,
        "mapa": [{k: (round(v, 3) if isinstance(v, float) else v) for k, v in f.items()} for f in mapa],
        "descubrimiento": desc,
        "ligas": _redondear(perfil),
        "equipos": _redondear(equipos),
        "hoy": _redondear(hoy),
        "apuestas_modelo": [{k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()} for r in ev],
    }
    JSON_APP.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    _markdown(datos, alertas, m)
    return datos


def _seccion_ligas(w, pf: dict) -> None:
    g = pf["global"]
    w("## Tus ligas")
    w("")
    w("Tu historial es por pata (incluye las de combinadas), con neto a stake 1 como si cada pata fuera simple. "
      "Las tasas base salen de partidos terminados verificados gol a gol "
      f"(tasas con {pf['min_partidos']} partidos o más). Aparecen las ligas con muestra o con 3 patas tuyas o más.")
    w("")
    w(f"Referencia de toda la muestra ({g['n']} partidos): {g['goles_partido']:.2f} goles por partido, "
      f"Más de 2.5 en {pct(g['over25'])}, Ambos marcan en {pct(g['btts'])}, "
      f"hubo gol desde el 75' en {pct(g['gol_desde_75'])} de los partidos y el {pct(g['parte_2t'])} de los goles fue en el 2T.")
    w("")
    w("| Liga | Tus patas | Neto | Partidos | Goles/partido | Más de 2.5 | Ambos marcan | Gol desde 75' | Factor modelo |")
    w("|---|---|---|---|---|---|---|---|---|")
    for f in pf["ligas"]:
        t, b = f["tuyo"], f["base"]
        tu = f"{t['k']}/{t['n']}" if t else "—"
        neto = f"{t['neto']:+.2f}" if t else "—"
        if b.get("goles_partido") is not None:
            lo, hi = b["over25_ic"]
            base = (f"{b['n']} | {b['goles_partido']:.2f} | {pct(b['over25'])} ({pct(lo)}–{pct(hi)}) | "
                    f"{pct(b['btts'])} | {pct(b['gol_desde_75'])}")
        else:
            base = f"{b['n']} | — | — | — | —"
        fac = f"{f['factor']:.2f}" if f["factor"] else "—"
        w(f"| {f['liga']} | {tu} | {neto} | {base} | {fac} |")
    w("")
    w("Cómo leerla: el factor del modelo es la liga contra la media, ya contraído hacia 1 porque las muestras son chicas. "
      "Una liga con 16 partidos y 44% de Más de 2.5 tiene un intervalo de unos 25 puntos. "
      "Sirve para ordenar ligas, no para creer que una liga es 'de goles' con 5 partidos.")
    w("")


def _markdown(d: dict, alertas: list[dict], m: Modelo) -> None:
    L = []
    w = L.append
    w("# Football Brain · Análisis v2")
    w("")
    w(f"Generado el {d['generado']} con `python -m fb.cli reporte`.")
    w("")
    w("## 1. De dónde salen los datos")
    w("")
    w(f"- Partidos terminados con todos los goles al minuto: {d['muestra']['total']}.")
    w(f"- De ellos, {d['muestra']['backtest']} son partidos ajenos a tus apuestas. Solo esos validan patrones.")
    w("- Los otros son los partidos donde apostaste. Sirven para el modelo, no para darte la razón.")
    w("- Fuente: crónicas y fichas de prensa encontradas por búsqueda web, una por partido, con enlace en el CSV.")
    w("- Cada partido se verificó: la lista de goles debe sumar exactamente el marcador final.")
    w("")
    w("## 2. El modelo en vivo")
    w("")
    w("Estima cuántos goles faltan según el minuto, la liga y si hubo roja. "
      "Con eso calcula la probabilidad de cada mercado y la cuota mínima para que la apuesta valga la pena.")
    w("")
    c = d["calibracion"]
    w(f"- Validación cruzada en {c['n']} predicciones de 'llega al menos un gol más'.")
    w(f"- Brier score {c['brier']:.3f} contra {c['brier_base']:.3f} de adivinar siempre la media. Menor es mejor.")
    w("")
    w("| Probabilidad del modelo | Casos | Media predicha | Ocurrió |")
    w("|---|---|---|---|")
    for a, b, n, pm, fr in c["fiabilidad"]:
        w(f"| {pct(a)} a {pct(b)} | {n} | {pct(pm)} | {pct(fr)} |")
    w("")
    for nota in d["modelo"]["notas"]:
        w(f"- {nota}")
    w("- Límite: el modelo no conoce la fuerza de cada equipo. En apuestas a ganador subestima al favorito.")
    w("  La app pide la cuota prepartido del favorito para corregirlo.")
    w("")
    q = d["equipos"]
    w("### ¿Sirven los promedios por equipo (tipo scores24)?")
    w("")
    w("Se probó el modelo con goles a favor y en contra de cada equipo, calculados con sus otros partidos de la "
      "muestra, sin mirar el partido que se predice. Menor Brier es mejor.")
    w("")
    w("| Predicción | Solo liga | Con equipos |")
    w("|---|---|---|")
    w(f"| Ganador final (1X2) | {q['brier_1x2_liga']:.3f} | {q['brier_1x2_equipos']:.3f} |")
    w(f"| Llega al menos un gol más | {q['brier_gol_liga']:.3f} | {q['brier_gol_equipos']:.3f} |")
    w("")
    mejor_gol = q["brier_gol_equipos"] < q["brier_gol_liga"]
    mejor_1x2 = q["brier_1x2_equipos"] < q["brier_1x2_liga"]
    w(f"Solo {q['partidos']} partidos tienen dos o más partidos de cada equipo en la muestra, así que es una señal débil. "
      + ("Para goles ayudó un poco. " if mejor_gol else "Para goles no ayudó. ")
      + ("Para ganador también." if mejor_1x2 else
         "Para ganador empeoró: con 2 o 3 partidos por equipo el promedio es puro ruido. "
         "Para ganador la cuota prepartido resume mucho mejor la fuerza de los equipos."))
    w("")
    w("Uso recomendado en la app: los promedios de la temporada completa (10 partidos o más) sirven para los "
      "mercados de goles. Para ganador usa la cuota prepartido.")
    w("")
    w("## 3. Patrones")
    w("")
    w("| Código | Patrón | Backtest | Tu historial | Cuota mínima | Semáforo |")
    w("|---|---|---|---|---|---|")
    for f in d["fichas"]:
        b, t = f["backtest"], f["tuyo"]
        bt = f"{b['k']}/{b['n']} ({pct(b['tasa'])})" if b["n"] else "sin datos"
        tu = f"{t['k']}/{t['n']}" if t["n"] else "—"
        cm = f"{b['cuota_min']:.2f}" if b["cuota_min"] else "—"
        w(f"| {f['codigo']} | {f['nombre']} | {bt} | {tu} | {cm} | {f['semaforo']} |")
    w("")
    w("Semáforo: rojo con menos de 30 casos en total; ámbar si el intervalo toca el break-even de tus cuotas "
      "(o si aún no hay 5 apuestas tuyas para saber qué cuota tomas); verde si el límite inferior lo supera. "
      "Los anti-patrones (A) no llevan color: se evitan.")
    w("")
    for f in d["fichas"]:
        b, t = f["backtest"], f["tuyo"]
        w(f"### {f['codigo']} · {f['nombre']}")
        w("")
        w(f["resumen"])
        w("")
        if f["entrar_si"]:
            w("**Entra solo si:**")
            for x in f["entrar_si"]:
                w(f"- {x}")
            w("")
        w("**No entres si:**")
        for x in f["no_entrar_si"]:
            w(f"- {x}")
        w("")
        if b["n"]:
            w(f"**En partidos ajenos:** se cumplió {b['k']} de {b['n']} veces ({pct(b['tasa'])}), "
              f"intervalo 95% de {pct(b['lo'])} a {pct(b['hi'])}. El modelo esperaba {pct(b['p_modelo'])}. "
              f"De cada 10 veces, unas {round(b['tasa'] * 10)} salen bien.")
            if b["cuota_min"]:
                w(f"**Cuota mínima para entrar:** {b['cuota_min']:.2f}. Con una cuota menor pierdes dinero a la larga "
                  "aunque aciertes seguido.")
            if b["ligas"]:
                w("**Ligas donde mejor funcionó** (tasa ajustada por tamaño de muestra): " +
                  ", ".join(f"{x['liga']} {x['k']}/{x['n']}" for x in b["ligas"][:4]) + ".")
        else:
            w("**En partidos ajenos:** sin datos para medirlo.")
        if t["n"]:
            w(f"**En tus apuestas:** {t['k']} de {t['n']}, cuota media {t['cuota_media']:.2f}, neto {t['neto']:+.2f} unidades.")
        w("")
    _seccion_ligas(w, d["ligas"])
    w("## 4. Mapa de probabilidades")
    w("")
    w("Frecuencia real en partidos ajenos según minuto, goles y diferencia en el marcador.")
    w("")
    w("| Minuto | Goles | Diferencia | Partidos | Llega 1 gol más | Llegan 2 más | Líder gana / Empate sigue | Modelo 1 gol más |")
    w("|---|---|---|---|---|---|---|---|")
    for f in d["mapa"]:
        if f["n"] < 4:
            continue
        g = f"{f['goles']}+" if f["goles"] == 3 else str(f["goles"])
        dif = "2+" if f["dif"] == 2 else str(f["dif"])
        ult = pct(f.get("lider_gana")) if f["dif"] > 0 else pct(f.get("empate_sigue"))
        w(f"| {f['minuto']}' | {g} | {dif} | {f['n']} | {pct(f['mas1'])} | {pct(f['mas2'])} | {ult} | {pct(f['p_mod_mas1'])} |")
    w("")
    w("## 5. Búsqueda de patrones nuevos")
    w("")
    conf = [x for x in d["descubrimiento"] if x["confirmada"]]
    if conf:
        for x in conf:
            w(f"- Minuto {x['minuto']}, {x['goles_min']}+ goles, diferencia {x['dif']}: "
              f"{x['k_val']}/{x['n_val']} en validación.")
    else:
        w(f"Se probaron situaciones en la mitad más antigua de los partidos y se revisaron en la más reciente. "
          f"Ninguna superó la corrección por pruebas múltiples con {d['muestra']['backtest']} partidos. "
          "Hace falta la muestra grande de Sofascore para confirmar patrones nuevos.")
    w("")
    w("## 6. Tus apuestas contra el modelo")
    w("")
    w("La cuota que tomaste implica una probabilidad. Si el modelo base de la liga da más, había valor; si da menos, "
      "pagaste por algo que el modelo no ve, por ejemplo la fuerza del favorito.")
    w("")
    w("| Partido | Apuesta | Min | Marcador | Cuota | Prob. implícita | Modelo | Cuota mínima | Resultado |")
    w("|---|---|---|---|---|---|---|---|---|")
    for r in sorted(d["apuestas_modelo"], key=lambda r: r["partido"]):
        w(f"| {r['partido']} | {r['seleccion']} | {r['minuto']}' | {r['marcador']} | {r['cuota']:.2f} | "
          f"{pct(1 / r['cuota'])} | {pct(r['p'])} | {r['cuota_min']:.2f} | {'Ganó' if r['gano'] else 'Perdió'} |")
    w("")
    if alertas:
        w("### Reconstrucciones a revisar")
        w("")
        w("La cuota tomada y el modelo difieren más de 35 puntos. O el marcador reconstruido está mal, "
          "o el mercado sabía algo que la base de la liga no refleja.")
        w("")
        for r in alertas:
            w(f"- {r['partido']}: {r['seleccion']} a {r['cuota']:.2f} con {r['marcador']} al {r['minuto']}'. "
              f"Implícita {pct(1 / r['cuota'])}, modelo {pct(r['p'])}.")
        w("")
    w("## 7. Límites")
    w("")
    w("- La muestra de partidos ajenos es chica. Los intervalos son anchos y ninguna regla nueva queda confirmada.")
    w("- La búsqueda web da goles y rojas al minuto. Tiros, xG y presión al minuto llegan con Sofascore "
      "(`python -m fb.cli sofascore-probar`).")
    w("- No existe historial de cuotas en vivo. El ROI solo se mide con tus apuestas registradas en la app.")
    MD.parent.mkdir(exist_ok=True)
    MD.write_text("\n".join(L) + "\n", encoding="utf-8")
