"""Comandos de Football Brain.

    python -m fb.cli reporte                      análisis v2, modelo y datos de la app
    python -m fb.cli inyectar-app                 mete patterns/datos_app.json en app/index.html
    python -m fb.cli sofascore-probar             comprueba el acceso a Sofascore
    python -m fb.cli buscar --fecha 2026-09-27 --equipo Criciuma
    python -m fb.cli descargar --torneo 390 --temporada 72603 --paginas 10
    python -m fb.cli descargar-evento --id 12345678

Todo corre con Python 3.10+ estándar, en esta nube o en C:\\CLOUDE\\PRONOSTICOS.
"""
from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return "".join(ch for ch in s if ch.isalnum() or ch == " ").strip()


def cmd_reporte(_):
    from .reporte import generar, MD, JSON_APP
    d = generar()
    print(f"Reporte: {MD.relative_to(RAIZ)}  Datos app: {JSON_APP.relative_to(RAIZ)}")
    for f in d["fichas"]:
        b = f["backtest"]
        print(f"  {f['codigo']} {f['nombre']:36s} backtest {b['k']}/{b['n']}  tuyo {f['tuyo']['k']}/{f['tuyo']['n']}  {f['semaforo']}")


def cmd_inyectar(_):
    """Reemplaza el bloque de datos de la app entre marcadores."""
    app = RAIZ / "app" / "index.html"
    datos = (RAIZ / "patterns" / "datos_app.json").read_text(encoding="utf-8")
    patrones = (RAIZ / "patterns" / "patrones.json").read_text(encoding="utf-8")
    html = app.read_text(encoding="utf-8")
    ini, fin = "/*DATOS_APP_INICIO*/", "/*DATOS_APP_FIN*/"
    a, b = html.index(ini) + len(ini), html.index(fin)
    bloque = f"\nconst DATOS = {json.dumps(json.loads(datos), ensure_ascii=False, separators=(',', ':'))};\n" \
             f"const PATRONES_JSON = {json.dumps(json.loads(patrones), ensure_ascii=False, separators=(',', ':'))};\n"
    app.write_text(html[:a] + bloque + html[b:], encoding="utf-8")
    print(f"Datos inyectados en {app.relative_to(RAIZ)} ({len(bloque) // 1024} KB)")


def cmd_probar(_):
    from .sofascore import probar
    ok, msg = probar()
    print(("OK  " if ok else "BLOQUEADO  ") + msg)
    if not ok:
        print("Habilita api.sofascore.com en Network access del entorno, o corre este comando en tu PC.")
    return 0 if ok else 1


def cmd_buscar(a):
    from .sofascore import Cliente
    q = _norm(a.equipo)
    for ev in Cliente().eventos_del_dia(a.fecha):
        h, v = ev["homeTeam"]["name"], ev["awayTeam"]["name"]
        if q in _norm(h) or q in _norm(v):
            t = ev.get("tournament", {}).get("name", "")
            print(f"{ev['id']}  {h} vs {v}  [{t}]")


def _descargar_evento(cli, eid: int) -> dict | None:
    from . import etl
    ev = cli.evento(eid)
    inc = cli.incidentes(eid)
    fila = etl.fila_partido(ev, inc)
    if not fila:
        return None
    etl.anexar("tiros.csv", etl.filas_tiros(eid, cli.tiros(eid)))
    etl.anexar("presion.csv", etl.filas_presion(eid, cli.presion(eid)))
    etl.anexar("stats.csv", etl.filas_stats(eid, cli.estadisticas(eid)))
    etl.anexar("partidos.csv", [fila])
    return fila


def cmd_descargar_evento(a):
    from .sofascore import Cliente
    f = _descargar_evento(Cliente(), a.id)
    print(f or "El partido no está terminado o no existe.")


def cmd_descargar(a):
    from .sofascore import Cliente
    cli = Cliente()
    evs = cli.ultimos_eventos(a.torneo, a.temporada, a.paginas)
    print(f"{len(evs)} partidos encontrados")
    for i, ev in enumerate(evs, 1):
        f = _descargar_evento(cli, ev["id"])
        if f:
            print(f"[{i}/{len(evs)}] {f['local']} {f['final']} {f['visitante']}  completo={f['completo']}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="fb")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("reporte").set_defaults(fn=cmd_reporte)
    sub.add_parser("inyectar-app").set_defaults(fn=cmd_inyectar)
    sub.add_parser("sofascore-probar").set_defaults(fn=cmd_probar)
    b = sub.add_parser("buscar")
    b.add_argument("--fecha", required=True)
    b.add_argument("--equipo", required=True)
    b.set_defaults(fn=cmd_buscar)
    d = sub.add_parser("descargar")
    d.add_argument("--torneo", type=int, required=True)
    d.add_argument("--temporada", type=int, required=True)
    d.add_argument("--paginas", type=int, default=5)
    d.set_defaults(fn=cmd_descargar)
    e = sub.add_parser("descargar-evento")
    e.add_argument("--id", type=int, required=True)
    e.set_defaults(fn=cmd_descargar_evento)
    a = p.parse_args(argv)
    return a.fn(a) or 0


if __name__ == "__main__":
    sys.exit(main())
