"""Normaliza respuestas de Sofascore a las tablas del proyecto.

Tablas (CSV en `data/sofascore/`, legibles por DuckDB con read_csv_auto):
    partidos.csv   mismo formato que data/backtest/partidos.csv más event_id
    tiros.csv      event_id, minuto, lado, xg, tipo
    presion.csv    event_id, minuto, valor (positivo = presiona el local)
    stats.csv      event_id, periodo, clave, local, visita
"""
from __future__ import annotations

import csv
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR = RAIZ / "data" / "sofascore"


def minuto_incidente(inc: dict) -> int:
    """Minuto normalizado: el añadido del 1T queda en 45 y el del 2T en 90."""
    t = int(inc.get("time") or 0)
    return min(t, 120)


def goles_y_rojas(incidentes: dict) -> tuple[list[tuple[int, str]], list[tuple[int, str]]]:
    """Goles (minuto, H/A) asignados por el cambio de marcador y rojas (minuto, H/A)."""
    incs = sorted((incidentes or {}).get("incidents", []),
                  key=lambda i: (int(i.get("time") or 0), int(i.get("addedTime") or 0)))
    goles, rojas = [], []
    h = a = 0
    for inc in incs:
        tipo = inc.get("incidentType")
        if tipo == "goal":
            nh, na = inc.get("homeScore"), inc.get("awayScore")
            if nh is not None and na is not None:
                if nh > h:
                    goles.append((minuto_incidente(inc), "H"))
                elif na > a:
                    goles.append((minuto_incidente(inc), "A"))
                h, a = nh, na
            else:
                goles.append((minuto_incidente(inc), "H" if inc.get("isHome") else "A"))
        elif tipo == "card" and inc.get("incidentClass") in ("red", "yellowRed"):
            rojas.append((minuto_incidente(inc), "H" if inc.get("isHome") else "A"))
    return goles, rojas


def fila_partido(evento: dict, incidentes: dict) -> dict | None:
    ev = (evento or {}).get("event", evento or {})
    if (ev.get("status") or {}).get("type") != "finished":
        return None
    goles, rojas = goles_y_rojas(incidentes)
    fh = (ev.get("homeScore") or {}).get("normaltime", (ev.get("homeScore") or {}).get("current"))
    fa = (ev.get("awayScore") or {}).get("normaltime", (ev.get("awayScore") or {}).get("current"))
    completo = fh is not None and fa is not None and \
        (sum(1 for _, s in goles if s == "H"), sum(1 for _, s in goles if s == "A")) == (fh, fa)
    torneo = (ev.get("tournament") or {})
    import datetime as _dt
    fecha = _dt.datetime.fromtimestamp(ev.get("startTimestamp", 0), tz=_dt.timezone.utc).strftime("%Y-%m-%d")
    return {
        "liga": (torneo.get("uniqueTournament") or {}).get("name") or torneo.get("name", ""),
        "fecha": fecha,
        "local": (ev.get("homeTeam") or {}).get("name", ""),
        "visitante": (ev.get("awayTeam") or {}).get("name", ""),
        "final": f"{fh}:{fa}",
        "goles": ";".join(f"{s}{m}" for m, s in goles),
        "rojas": ";".join(f"{s}{m}" for m, s in rojas),
        "completo": "1" if completo else "0",
        "fuente": f"sofascore:{ev.get('id')}",
        "origen": "sofascore",
        "event_id": ev.get("id"),
    }


def filas_tiros(eid: int, shotmap: dict) -> list[dict]:
    out = []
    for s in (shotmap or {}).get("shotmap", []):
        out.append({"event_id": eid, "minuto": int(s.get("time") or 0),
                    "lado": "H" if s.get("isHome") else "A",
                    "xg": s.get("xg"), "tipo": s.get("shotType", "")})
    return out


def filas_presion(eid: int, graph: dict) -> list[dict]:
    return [{"event_id": eid, "minuto": p.get("minute"), "valor": p.get("value")}
            for p in (graph or {}).get("graphPoints", [])]


def filas_stats(eid: int, stats: dict) -> list[dict]:
    out = []
    for per in (stats or {}).get("statistics", []):
        for g in per.get("groups", []):
            for it in g.get("statisticsItems", []):
                out.append({"event_id": eid, "periodo": per.get("period"),
                            "clave": it.get("key") or it.get("name"),
                            "local": it.get("homeValue", it.get("home")),
                            "visita": it.get("awayValue", it.get("away"))})
    return out


def anexar(nombre: str, filas: list[dict]) -> None:
    if not filas:
        return
    DIR.mkdir(parents=True, exist_ok=True)
    path = DIR / nombre
    nuevo = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        if nuevo:
            w.writeheader()
        w.writerows(filas)


def estado_extendido(eid: int, minuto: int, tiros: list[dict], presion: list[dict]) -> dict:
    """Tiros, xG y presión acumulados hasta `minuto` para un partido."""
    t = [x for x in tiros if x["event_id"] == eid and int(x["minuto"]) <= minuto]
    pr = [x for x in presion if x["event_id"] == eid and x["minuto"] is not None and int(x["minuto"]) <= minuto]
    ult10 = [float(x["valor"]) for x in pr if int(x["minuto"]) > minuto - 10]
    return {
        "tiros_local": sum(1 for x in t if x["lado"] == "H"),
        "tiros_visita": sum(1 for x in t if x["lado"] == "A"),
        "a_puerta_local": sum(1 for x in t if x["lado"] == "H" and x["tipo"] in ("save", "goal")),
        "a_puerta_visita": sum(1 for x in t if x["lado"] == "A" and x["tipo"] in ("save", "goal")),
        "xg_local": round(sum(float(x["xg"] or 0) for x in t if x["lado"] == "H"), 2),
        "xg_visita": round(sum(float(x["xg"] or 0) for x in t if x["lado"] == "A"), 2),
        "presion_ult10": round(sum(ult10) / len(ult10), 1) if ult10 else None,
    }
