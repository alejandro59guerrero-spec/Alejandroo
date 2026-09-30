"""Hoja en vivo de un partido: qué apostar y a qué cuota mínima según lo que pase.

Se prepara antes del partido con las cuotas prepartido (1X2 y Más de 2.5). Durante
el partido solo buscas la fila del minuto y el marcador y comparas con la cuota de
tu casa. Sin datos en vivo: funciona aunque Sofascore esté bloqueado.
"""
from __future__ import annotations

import json
from pathlib import Path

from .envivo import UMBRAL_ALTA, oportunidades
from .modelo import Modelo, prob_over_sin_margen, prob_sin_margen

RAIZ = Path(__file__).resolve().parent.parent
JSON_HOY = RAIZ / "patterns" / "hoy.json"
MINUTOS = (30, 45, 55, 65, 75)
MARCADORES = ((0, 0), (1, 0), (0, 1), (1, 1), (2, 0), (0, 2), (2, 1), (1, 2), (2, 2), (3, 0), (0, 3))


def modelo_partido(base: Modelo, pt: dict) -> tuple[Modelo, dict]:
    """Modelo ajustado al partido y las probabilidades prepartido que usa."""
    p1 = px = p2 = po = None
    if pt.get("c1") and pt.get("cx") and pt.get("c2"):
        p1, px, p2 = prob_sin_margen(pt["c1"], pt["cx"], pt["c2"])
    elif pt.get("c1"):
        p1 = (1 / pt["c1"]) / 1.05  # solo la cuota del local: margen típico
    if pt.get("o25"):
        po = prob_over_sin_margen(pt["o25"], pt.get("u25"))
    elif pt.get("p_o25"):
        po = pt["p_o25"]
    m = base.con_mercado(p1, po, pt.get("liga"))
    return m, {"local": p1, "empate": px, "visitante": p2, "over25": po,
               "goles_esperados": sum(m.equipos)}


def hoja(base: Modelo, pt: dict) -> dict:
    m, pre = modelo_partido(base, pt)
    filas = []
    for t in MINUTOS:
        for gl, gv in MARCADORES:
            if gl + gv > 1 + t // 30:  # marcadores raros para ese minuto
                continue
            ops = oportunidades({"gl": gl, "gv": gv, "minuto": t}, m, None)
            p_gol = m.prob_mas_goles(1, t)
            r = m.prob_1x2(gl, gv, t)
            filas.append({
                "minuto": t, "marcador": f"{gl}:{gv}",
                "over": {"linea": gl + gv + 0.5, "p": p_gol, "cuota_min": 1 / p_gol},
                "lider": None if gl == gv else {"lado": "local" if gl > gv else "visitante",
                                                "p": r["local" if gl > gv else "visitante"],
                                                "cuota_min": 1 / r["local" if gl > gv else "visitante"]},
                "empate_sigue": r["empate"] if gl == gv else None,
                "patrones": sorted({o["patron"] for o in ops}),
                "alta": any(o["alta"] for o in ops),
            })
    return {**pt, "prepartido": pre, "filas": filas}


def cargar_hoy() -> dict:
    return json.loads(JSON_HOY.read_text(encoding="utf-8")) if JSON_HOY.exists() else {"partidos": []}


def markdown(hojas: list[dict], fecha: str) -> str:
    L = [f"# Hojas en vivo · {fecha}", "",
         "Busca el minuto y el marcador del partido. Entra solo si tu cuota es MAYOR que la cuota mínima "
         f"y la fila tiene un patrón. En negrita: probabilidad del modelo de {UMBRAL_ALTA * 100:.0f}% o más.",
         "El modelo parte de las cuotas prepartido (1X2 y Más de 2.5) y del reparto de goles por minuto "
         "de los partidos terminados de la muestra. No ve tiros, presión ni cambios: si el partido está "
         "muerto, la probabilidad real es menor.", ""]
    for h in hojas:
        pre = h["prepartido"]
        L.append(f"## {h['local']} vs {h['visitante']} · {h['liga']} · {h.get('hora', '')}")
        L.append("")
        partes = [f"goles esperados {pre['goles_esperados']:.2f}"]
        if pre["local"]:
            partes.append(f"1X2 sin margen {pre['local'] * 100:.0f}/{pre['empate'] * 100:.0f}/{pre['visitante'] * 100:.0f}"
                          if pre["empate"] else f"gana el local {pre['local'] * 100:.0f}%")
        if pre["over25"]:
            partes.append(f"Más de 2.5 {pre['over25'] * 100:.0f}%")
        L.append("Prepartido: " + ", ".join(partes) + f". Fuente de cuotas: {h.get('fuente', '—')}.")
        L.append("")
        L.append("| Min | Marcador | Más de | Prob. | Cuota mín. | Gana el que va arriba | Cuota mín. | Patrón |")
        L.append("|---|---|---|---|---|---|---|---|")
        for f in h["filas"]:
            o = f["over"]
            b = lambda p: f"**{p * 100:.0f}%**" if p >= UMBRAL_ALTA else f"{p * 100:.0f}%"
            lid = f["lider"]
            lt = f"{b(lid['p'])} ({lid['lado']})" if lid else f"empate sigue {f['empate_sigue'] * 100:.0f}%"
            lc = f"{lid['cuota_min']:.2f}" if lid else "—"
            L.append(f"| {f['minuto']}' | {f['marcador']} | {o['linea']} | {b(o['p'])} | {o['cuota_min']:.2f} | "
                     f"{lt} | {lc} | {' '.join(f['patrones']) or '—'} |")
        L.append("")
    return "\n".join(L) + "\n"
