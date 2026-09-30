#!/usr/bin/env python3
"""Football Brain · validación de patrones en vivo.

Lee data/tickets.csv y data/legs.csv (historial real de Ecuabet) y:
  1. Resume tickets reales (stake variable) y a stake plano.
  2. Calcula para cada pata en vivo el minuto de juego al apostar, el marcador,
     los goles que faltaban y si había roja.
  3. Clasifica cada pata en patrones con reglas fijas y mide acierto, intervalo
     de Wilson al 95 %, cuota media, break-even y ROI a stake plano.
  4. Escribe reports/analisis_patrones.md y data/legs_enriquecido.csv.

Solo usa la biblioteca estándar: corre igual en la PC del usuario.
"""
from __future__ import annotations

import csv
import math
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
REPORTS = ROOT / "reports"

MIN_MUESTRA = 10  # por debajo de esto no se declara nada


# ---------------------------------------------------------------- utilidades
def leer_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def minuto_de_juego(emision: str, inicio: str) -> tuple[int | None, str]:
    """Minuto de juego estimado a partir de la hora del ticket y del saque.

    <=47 min transcurridos: primer tiempo. 48-62: descanso o inicio del 2T
    (se toma 46). >62: segundo tiempo, se restan ~17 min de pausa y añadido.
    """
    t = (datetime.fromisoformat(emision) - datetime.fromisoformat(inicio)).total_seconds() / 60
    if t < 0:
        return None, "prepartido"
    if t <= 47:
        return int(t), "1T"
    if t <= 62:
        return 46, "descanso"
    return min(int(t - 17), 95), "2T"


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    p = k / n
    den = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / den
    margen = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, centro - margen), min(1.0, centro + margen)


def parse_marcador(m: str) -> tuple[int, int] | None:
    if not m or ":" not in m:
        return None
    a, b = m.split(":")
    return int(a), int(b)


# ------------------------------------------------------------ enriquecimiento
def enriquecer(legs: list[dict], tickets: dict[str, dict]) -> list[dict]:
    out = []
    for leg in legs:
        t = tickets[leg["ticket_id"]]
        minuto, fase = minuto_de_juego(t["emision"], leg["inicio"])
        e = dict(leg)
        e["tipo_ticket"] = t["tipo"]
        e["minuto"] = "" if minuto is None else minuto
        e["fase"] = fase
        e["cuota"] = float(leg["cuota"])
        e["gano"] = leg["resultado"] == "W"
        e["con_dato"] = leg["marcador_apuesta"] not in ("", "sin_dato", "pre") and leg["confianza"] != "sin_dato"
        e["estado_sel"] = ""
        e["goles_apuesta"] = ""
        e["goles_faltan"] = ""
        e["roja_a_favor"] = False
        e["hay_roja"] = leg["roja_equipo"] in ("local", "visitante", "ambos")
        sc = parse_marcador(leg["marcador_apuesta"])
        if sc and e["con_dato"]:
            h, a = sc
            e["goles_apuesta"] = h + a
            if leg["lado"] in ("local", "visitante"):
                propio, rival = (h, a) if leg["lado"] == "local" else (a, h)
                e["estado_sel"] = "gana" if propio > rival else ("empata" if propio == rival else "pierde")
                rival_lado = "visitante" if leg["lado"] == "local" else "local"
                e["roja_a_favor"] = leg["roja_equipo"] == rival_lado
            if leg["linea"]:
                linea = float(leg["linea"])
                e["goles_faltan"] = max(0, math.floor(linea) + 1 - (h + a))
        out.append(e)
    return out


# ------------------------------------------------------------------ patrones
def en_vivo(e):
    return e["fase"] != "prepartido" and e["con_dato"]


PATRONES = [
    # (codigo, nombre, regla legible, tipo, predicado)
    ("P1", "Over con partido abierto",
     "Mercado Over de goles. Ya hay 2 o más goles, falta 1 solo gol para ganar la línea y el minuto es 75 o menos.",
     "a favor",
     lambda e: en_vivo(e) and e["mercado"] == "over" and e["goles_apuesta"] >= 2
     and e["goles_faltan"] == 1 and e["minuto"] <= 75),
    ("P2", "1x2 al equipo que ya gana",
     "Mercado 1x2 (ganador). El equipo elegido va ganando por 1 o más goles al apostar.",
     "a favor",
     lambda e: en_vivo(e) and e["mercado"] == "1x2" and e["estado_sel"] == "gana"),
    ("P3", "Roja: apostar a goles",
     "Hubo roja antes de apostar y la apuesta es a goles (Over o Ambos marcan).",
     "a favor",
     lambda e: en_vivo(e) and e["hay_roja"] and e["mercado"] in ("over", "btts")),
    ("P4", "Roja: 1x2 al equipo con uno más",
     "El rival del equipo elegido tiene una roja y la apuesta es que el equipo con uno más gane.",
     "a validar",
     lambda e: en_vivo(e) and e["roja_a_favor"] and e["mercado"] in ("1x2", "bb")),
    ("A1", "1x2 con el partido empatado",
     "Mercado 1x2 (o Bet Builder con ganador) y el marcador está empatado al apostar.",
     "anti-patrón",
     lambda e: en_vivo(e) and e["mercado"] in ("1x2", "bb") and e["estado_sel"] == "empata"),
    ("A2", "Over sin goles",
     "Mercado Over y el partido va 0:0 al apostar.",
     "anti-patrón",
     lambda e: en_vivo(e) and e["mercado"] == "over" and e["goles_apuesta"] == 0),
    ("A3", "Córners (Over de tiros de esquina)",
     "Cualquier Over de córners.",
     "anti-patrón",
     lambda e: e["fase"] != "prepartido" and e["mercado"] == "corners"),
]


def medir(rows: list[dict]) -> dict:
    n = len(rows)
    k = sum(r["gano"] for r in rows)
    cuota_media = sum(r["cuota"] for r in rows) / n if n else 0
    neto = sum((r["cuota"] - 1) if r["gano"] else -1 for r in rows)
    lo, hi = wilson(k, n)
    be = 1 / cuota_media if cuota_media else 0
    if n < MIN_MUESTRA:
        veredicto = "Sin muestra suficiente"
    elif lo > be:
        veredicto = "Edge probado"
    elif k / n > be:
        veredicto = "Prometedor, no probado"
    else:
        veredicto = "Sin edge"
    return dict(n=n, k=k, tasa=k / n if n else 0, lo=lo, hi=hi, cuota=cuota_media,
                be=be, neto=neto, roi=neto / n if n else 0, veredicto=veredicto)


def pct(x: float) -> str:
    return f"{x * 100:.0f}%"


# ------------------------------------------------------------------- reporte
def main() -> None:
    tickets_l = leer_csv(DATA / "tickets.csv")
    tickets = {t["ticket_id"]: t for t in tickets_l}
    legs = enriquecer(leer_csv(DATA / "legs.csv"), tickets)

    # --- tickets
    def resumen(ts):
        stake = sum(float(t["stake"]) for t in ts)
        ret = sum(float(t["retorno"]) for t in ts)
        gan = sum(t["estado"] == "ganado" for t in ts)
        plano = sum(float(t["retorno"]) / float(t["stake"]) - 1 for t in ts)
        return dict(n=len(ts), gan=gan, stake=stake, ret=ret, neto=ret - stake,
                    roi=(ret - stake) / stake if stake else 0,
                    roi_plano=plano / len(ts) if ts else 0)

    grupos = {
        "Todos": tickets_l,
        "Simples": [t for t in tickets_l if t["tipo"] == "simple"],
        "Combinadas en vivo": [t for t in tickets_l if t["tipo"] == "combinada" and t["modo"] == "vivo"],
        "Combinadas prepartido": [t for t in tickets_l if t["modo"] == "prepartido"],
    }
    res_t = {k: resumen(v) for k, v in grupos.items()}
    tot = res_t["Todos"]
    assert tot["n"] == 45, tot
    assert abs(tot["stake"] - 81.71) < 0.01 and abs(tot["ret"] - 97.26) < 0.01, tot

    # --- combinadas perdidas por una pata
    por_ticket: dict[str, list[dict]] = {}
    for e in legs:
        por_ticket.setdefault(e["ticket_id"], []).append(e)
    combis = [t for t in tickets_l if t["tipo"] == "combinada"]
    una_pata = [t for t in combis if t["estado"] != "ganado"
                and sum(not e["gano"] for e in por_ticket[t["ticket_id"]]) == 1]

    # --- patas en vivo como simples a stake plano
    vivas = [e for e in legs if e["fase"] != "prepartido"]
    con_dato = [e for e in vivas if e["con_dato"]]
    todas_vivas = medir(vivas)

    # --- patrones
    res_p = []
    for cod, nombre, regla, tipo, pred in PATRONES:
        rows = [e for e in legs if pred(e)]
        res_p.append((cod, nombre, regla, tipo, medir(rows), rows))

    # --- escritura
    REPORTS.mkdir(exist_ok=True)
    L = []
    w = L.append
    w("# Football Brain · Análisis de patrones en vivo")
    w("")
    w(f"Generado por `analysis/validar_patrones.py` el {datetime.now():%Y-%m-%d %H:%M}. "
      "Fuente: historial Ecuabet del 19 al 29 de septiembre de 2026 más reconstrucción web "
      "del marcador al minuto de cada apuesta.")
    w("")
    w("## 1. Resultado real de los tickets")
    w("")
    w("| Grupo | Tickets | Ganados | Apostado | Retorno | Neto | ROI real | ROI a stake plano |")
    w("|---|---|---|---|---|---|---|---|")
    for k, r in res_t.items():
        w(f"| {k} | {r['n']} | {r['gan']} | ${r['stake']:.2f} | ${r['ret']:.2f} | "
          f"{r['neto']:+.2f} | {r['roi'] * 100:+.1f}% | {r['roi_plano'] * 100:+.1f}% |")
    w("")
    huanc = next(t for t in tickets_l if t["ticket_id"] == "5462496161")
    sin_h = tot["neto"] - (float(huanc["retorno"]) - float(huanc["stake"]))
    w(f"El ticket de Sport Huancayo aporta +${float(huanc['retorno']) - float(huanc['stake']):.2f} "
      f"de los +${tot['neto']:.2f}. Sin él, el neto queda en {sin_h:+.2f}. "
      "Con 45 tickets y stakes variables, el saldo positivo no demuestra ventaja.")
    w("")
    w(f"**Combinadas que se cayeron por una sola pata:** {len(una_pata)} de {len(combis)} combinadas. "
      "La combinada multiplica el riesgo: una sola pata falla y se pierde todo.")
    w("")
    w("## 2. Todas las patas en vivo como si fueran simples")
    w("")
    w(f"- Patas en vivo: {len(vivas)}. Con marcador reconstruido al minuto: {len(con_dato)}.")
    w(f"- Acierto por pata: {pct(todas_vivas['tasa'])} con cuota media {todas_vivas['cuota']:.2f} "
      f"y break-even {pct(todas_vivas['be'])}.")
    w(f"- ROI a stake plano de 1 unidad: {todas_vivas['roi'] * 100:+.1f}%. Neto {todas_vivas['neto']:+.2f} unidades.")
    w("")
    w("## 3. Patrones: regla exacta, tasa histórica y límite")
    w("")
    w("| Código | Patrón | Tipo | n | Aciertos | Tasa | IC 95% | Cuota media | Break-even | ROI plano | Veredicto |")
    w("|---|---|---|---|---|---|---|---|---|---|---|")
    for cod, nombre, _, tipo, m, _ in res_p:
        w(f"| {cod} | {nombre} | {tipo} | {m['n']} | {m['k']} | {pct(m['tasa'])} | "
          f"{pct(m['lo'])}–{pct(m['hi'])} | {m['cuota']:.2f} | {pct(m['be'])} | "
          f"{m['roi'] * 100:+.0f}% | {m['veredicto']} |")
    w("")
    for cod, nombre, regla, tipo, m, rows in res_p:
        w(f"### {cod} · {nombre}")
        w("")
        w(f"**Regla:** {regla}")
        w("")
        w(f"**Tasa histórica:** {m['k']}/{m['n']} ({pct(m['tasa'])}), intervalo 95% {pct(m['lo'])}–{pct(m['hi'])}. "
          f"Cuota media {m['cuota']:.2f}, break-even {pct(m['be'])}, ROI plano {m['roi'] * 100:+.0f}%.")
        w("")
        w(f"**Veredicto:** {m['veredicto']}.")
        w("")
        if rows:
            w("| Partido | Apuesta | Minuto | Marcador al apostar | Roja | Cuota | Final | Resultado |")
            w("|---|---|---|---|---|---|---|---|")
            for e in sorted(rows, key=lambda r: r["inicio"]):
                if e["roja_equipo"] == "sin_dato":
                    roja = "sin dato"
                elif e["hay_roja"]:
                    roja = f"{e['roja_equipo']} {e['roja_min']}'" if e["roja_min"] else e["roja_equipo"]
                else:
                    roja = "no"
                w(f"| {e['partido']} | {e['seleccion']} | {e['minuto']}' | {e['marcador_apuesta']} | {roja} | "
                  f"{e['cuota']:.2f} | {e['marcador_final']} | {'Ganó' if e['gano'] else 'Perdió'} |")
            w("")
    w("## 4. Patas sin reconstrucción fiable")
    w("")
    w("Estas patas quedan fuera de los patrones porque no hay fuente con minutos o las fuentes se contradicen:")
    w("")
    for e in vivas:
        if not e["con_dato"]:
            w(f"- {e['partido']} ({e['seleccion']}, {e['marcador_final']}). {e['nota']}")
    w("")
    w("## 5. Método y límites")
    w("")
    w("- El minuto se calcula con la hora de emisión del ticket menos la hora de inicio del partido. "
      "Error esperado de ±3 minutos por añadido y retrasos del saque.")
    w("- El marcador al apostar sale de crónicas y fichas de partido encontradas por búsqueda web. "
      "Cuando la fuente choca con la cuota tomada, manda la cuota y la confianza baja.")
    w("- Tiros, ataques peligrosos y xG al minuto exacto no estaban disponibles. "
      "La app registra desde ahora el ritmo percibido al apostar para cubrir ese hueco.")
    w(f"- Ningún patrón llega a {MIN_MUESTRA} casos con edge probado. Son hipótesis a validar con apuestas "
      "nuevas, registradas antes de conocer el resultado.")
    (REPORTS / "analisis_patrones.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    # --- CSV enriquecido
    campos = ["ticket_id", "tipo_ticket", "partido", "liga", "inicio", "fase", "minuto", "mercado",
              "seleccion", "lado", "linea", "cuota", "marcador_apuesta", "goles_apuesta", "goles_faltan",
              "estado_sel", "roja_equipo", "roja_min", "roja_a_favor", "marcador_final", "resultado",
              "confianza", "patrones", "fuente"]
    with (DATA / "legs_enriquecido.csv").open("w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        wr.writeheader()
        for e in legs:
            e = dict(e)
            e["patrones"] = " ".join(cod for cod, *_, pred in PATRONES if pred(e))
            wr.writerow(e)

    # --- consola
    print(f"Tickets: {tot['n']} | apostado ${tot['stake']:.2f} | retorno ${tot['ret']:.2f} | neto {tot['neto']:+.2f}")
    print(f"Patas en vivo: {len(vivas)} | con dato: {len(con_dato)} | combinadas caídas por 1 pata: {len(una_pata)}")
    for cod, nombre, _, _, m, _ in res_p:
        print(f"{cod} {nombre:34s} {m['k']:>2}/{m['n']:<2} {pct(m['tasa']):>4}  BE {pct(m['be']):>4}  "
              f"ROI {m['roi'] * 100:+5.0f}%  {m['veredicto']}")


if __name__ == "__main__":
    main()
