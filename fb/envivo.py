"""Escáner de partidos en vivo.

Lee los partidos en juego de Sofascore, reconstruye el estado (minuto, marcador,
rojas) y evalúa las apuestas que encajan con tus patrones. Ordena por
probabilidad del modelo y marca la cuota mínima para entrar.

Sirve para decidir rápido, no para apostar a ciegas: la última palabra la tiene
la cuota real de tu casa de apuestas contra la cuota mínima.
"""
from __future__ import annotations

import html
import json
import time
import unicodedata
from datetime import datetime
from pathlib import Path

from .modelo import Modelo, cuota_minima

RAIZ = Path(__file__).resolve().parent.parent
JSON_LIGAS = RAIZ / "patterns" / "ligas.json"
UMBRAL_ALTA = 0.75


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return " ".join(s.split())


def cargar_ligas() -> list[dict]:
    return json.loads(JSON_LIGAS.read_text(encoding="utf-8"))["ligas"]


def liga_del_evento(ev: dict, ligas: list[dict]) -> str | None:
    """Nombre de tu liga si el evento pertenece a una de tus ligas ganadoras."""
    t = ev.get("tournament") or {}
    pais = _norm((t.get("category") or {}).get("name", ""))
    nombre = _norm((t.get("uniqueTournament") or {}).get("name") or t.get("name", ""))
    for l in ligas:
        if l["pais"] in pais and any(c in nombre for c in l["claves"]):
            return l["liga"]
    return None


def minuto_en_vivo(ev: dict, ahora: float | None = None) -> int | None:
    """Minuto de juego a partir del inicio del periodo actual."""
    st = ev.get("status") or {}
    desc = _norm(st.get("description", ""))
    if "halftime" in desc or "descanso" in desc:
        return 45
    ini = (ev.get("time") or {}).get("currentPeriodStartTimestamp")
    if not ini:
        return None
    ahora = ahora or time.time()
    trans = max(0, int((ahora - ini) // 60))
    if "2nd" in desc or "second" in desc:
        return min(46 + trans, 95)
    if "1st" in desc or "first" in desc:
        return min(trans + 1, 47)
    return None


def rojas_de(incidentes: dict | None) -> tuple[int, int]:
    rl = rv = 0
    for inc in (incidentes or {}).get("incidents", []):
        if inc.get("incidentType") == "card" and inc.get("incidentClass") in ("red", "yellowRed"):
            if inc.get("isHome"):
                rl += 1
            else:
                rv += 1
    return rl, rv


def oportunidades(estado: dict, m: Modelo, liga_modelo: str | None = None) -> list[dict]:
    """Apuestas que encajan con tus patrones en el estado actual del partido."""
    gl, gv, t = estado["gl"], estado["gv"], estado["minuto"]
    rl, rv = estado.get("rojas_local", 0), estado.get("rojas_visita", 0)
    goles, dif, roja = gl + gv, gl - gv, rl + rv > 0
    out = []
    p_gol = m.prob_mas_goles(1, t, liga_modelo, roja)
    linea = goles + 0.5
    cods = []
    if goles >= 2 and t <= 75:
        cods.append("P1")
    if roja and t <= 80:
        cods.append("P3")
    if goles == 0 and 45 <= t <= 60:
        cods.append("P5")
    if cods:
        out.append({"patron": "+".join(cods), "mercado": f"Más de {linea}", "p": p_gol})
    if dif != 0:
        r = m.prob_1x2(gl, gv, t, liga_modelo, rl, rv)
        lider = "local" if dif > 0 else "visitante"
        pat = "P6" if abs(dif) >= 2 and t >= 60 else "P2"
        out.append({"patron": pat, "mercado": f"Gana el {lider}", "p": r[lider]})
    for o in out:
        o["cuota_min"] = cuota_minima(o["p"])
        o["alta"] = o["p"] >= UMBRAL_ALTA
    return out


def liga_apifootball(fx: dict, ligas: list[dict]) -> str | None:
    """Nombre de tu liga si el fixture de API-Football pertenece a una de tus ligas ganadoras."""
    lg = fx.get("league") or {}
    pais = _norm(lg.get("country", ""))
    nombre = _norm(lg.get("name", ""))
    for l in ligas:
        if l["pais"] in pais and any(c in nombre for c in l["claves"]):
            return l["liga"]
    return None


def estado_apifootball(fx: dict, eventos: list[dict]) -> dict:
    """Estado del partido con la forma que consume oportunidades()."""
    goles = fx.get("goals") or {}
    equipos = fx.get("teams") or {}
    id_local = ((equipos.get("home") or {}).get("id"))
    rl = rv = 0
    for ev in eventos or []:
        if ev.get("type") == "Card" and ev.get("detail") == "Red Card":
            if (ev.get("team") or {}).get("id") == id_local:
                rl += 1
            else:
                rv += 1
    elapsed = ((fx.get("fixture") or {}).get("status") or {}).get("elapsed") or 0
    return {"gl": goles.get("home") or 0, "gv": goles.get("away") or 0,
            "minuto": int(elapsed), "rojas_local": rl, "rojas_visita": rv}


def escanear_apifootball(cliente, m: Modelo, solo_mis_ligas: bool = True) -> list[dict]:
    """Escáner en vivo usando API-Football (api-sports.io)."""
    ligas = cargar_ligas()
    filas = []
    for fx in cliente.en_vivo():
        mi_liga = liga_apifootball(fx, ligas)
        if solo_mis_ligas and not mi_liga:
            continue
        fid = (fx.get("fixture") or {}).get("id")
        eventos = cliente.eventos(fid) if fid else []
        estado = estado_apifootball(fx, eventos)
        if estado["minuto"] <= 0:
            continue
        equipos = fx.get("teams") or {}
        casa = (equipos.get("home") or {}).get("name", "?")
        visita = (equipos.get("away") or {}).get("name", "?")
        for o in oportunidades(estado, m, mi_liga):
            rl, rv = estado["rojas_local"], estado["rojas_visita"]
            filas.append({**o, "partido": f"{casa} vs {visita}",
                          "liga": mi_liga or (fx.get("league") or {}).get("name", ""),
                          "marcador": f"{estado['gl']}:{estado['gv']}", "minuto": estado["minuto"],
                          "rojas": f"{rl}-{rv}" if rl + rv else "", "event_id": fid})
    return sorted(filas, key=lambda f: -f["p"])


def escanear(cliente, m: Modelo, solo_mis_ligas: bool = True, ahora: float | None = None) -> list[dict]:
    datos = cliente.get("sport/football/events/live", usar_cache=False) or {}
    ligas = cargar_ligas()
    filas = []
    for ev in datos.get("events", []):
        if (ev.get("status") or {}).get("type") != "inprogress":
            continue
        mi_liga = liga_del_evento(ev, ligas)
        if solo_mis_ligas and not mi_liga:
            continue
        minuto = minuto_en_vivo(ev, ahora)
        if minuto is None:
            continue
        inc = cliente.get(f"event/{ev['id']}/incidents", usar_cache=False)
        rl, rv = rojas_de(inc)
        estado = {"gl": (ev.get("homeScore") or {}).get("current", 0) or 0,
                  "gv": (ev.get("awayScore") or {}).get("current", 0) or 0,
                  "minuto": minuto, "rojas_local": rl, "rojas_visita": rv}
        for o in oportunidades(estado, m, mi_liga):
            filas.append({**o, "partido": f"{ev['homeTeam']['name']} vs {ev['awayTeam']['name']}",
                          "liga": mi_liga or (ev.get("tournament") or {}).get("name", ""),
                          "marcador": f"{estado['gl']}:{estado['gv']}", "minuto": minuto,
                          "rojas": f"{rl}-{rv}" if rl + rv else "", "event_id": ev["id"]})
    return sorted(filas, key=lambda f: -f["p"])


def html_reporte(filas: list[dict], refresco: int = 60) -> str:
    hora = datetime.now().strftime("%H:%M:%S")
    tr = "".join(
        f"<tr class='{'alta' if f['alta'] else ''}'><td>{html.escape(f['partido'])}<br><small>{html.escape(f['liga'])}</small></td>"
        f"<td>{f['minuto']}'</td><td>{f['marcador']}{' R' + f['rojas'] if f['rojas'] else ''}</td>"
        f"<td>{html.escape(f['mercado'])}</td><td>{f['patron']}</td><td>{f['p'] * 100:.0f}%</td><td><b>{f['cuota_min']:.2f}</b></td></tr>"
        for f in filas) or "<tr><td colspan='7'>Sin partidos de tus ligas que cumplan un patrón en este momento.</td></tr>"
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="{refresco}">
<title>Football Brain en vivo</title><style>
:root{{--bg:#eceff3;--fg:#16212c;--mut:#5a6776;--line:#d3dae2;--card:#fff;--win:#1b7a48;--winbg:#e1f3e8}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0f141a;--fg:#e5ebf1;--mut:#95a3b1;--line:#2b3744;--card:#17202a;--win:#56c78f;--winbg:#16301f}}}}
body{{margin:0;padding:16px;background:var(--bg);color:var(--fg);font:15px/1.4 system-ui,sans-serif}}
h1{{margin:0 0 4px;font-size:22px}}p{{margin:0 0 12px;color:var(--mut)}}
.t{{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:10px}}
table{{width:100%;border-collapse:collapse}}td,th{{padding:8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}
th{{font-size:12px;text-transform:uppercase;color:var(--mut)}}small{{color:var(--mut)}}tr.alta td{{background:var(--winbg)}}tr.alta td:nth-child(6){{color:var(--win);font-weight:700}}
</style></head><body><h1>Partidos en vivo</h1>
<p>Actualizado {hora}. Se recarga cada {refresco} s. Verde: probabilidad del modelo de {UMBRAL_ALTA * 100:.0f}% o más. Entra solo si la cuota de tu casa supera la cuota mínima.</p>
<div class="t"><table><thead><tr><th>Partido</th><th>Min</th><th>Marcador</th><th>Apuesta</th><th>Patrón</th><th>Prob.</th><th>Cuota mín.</th></tr></thead>
<tbody>{tr}</tbody></table></div></body></html>"""
