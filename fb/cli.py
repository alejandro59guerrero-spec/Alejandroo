"""Comandos de Football Brain.

    python -m fb.cli reporte                      análisis v2, modelo y datos de la app
    python -m fb.cli inyectar-app                 mete patterns/datos_app.json en app/index.html
    python -m fb.cli sofascore-probar             comprueba el acceso a Sofascore
    python -m fb.cli buscar --fecha 2026-09-27 --equipo Criciuma
    python -m fb.cli descargar --torneo 390 --temporada 72603 --paginas 10
    python -m fb.cli descargar-evento --id 12345678
    python -m fb.cli en-vivo --servir 8765        escáner en vivo, página en la red local
    python -m fb.cli hoja                         hojas en vivo de patterns/hoy.json (sin datos en vivo)

Todo corre con Python 3.10+ estándar, en esta nube o en C:\\CLOUDE\\PRONOSTICOS.
"""
from __future__ import annotations

import argparse
import time
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


def cmd_hoja(_):
    """Hojas en vivo de los partidos de patterns/hoy.json."""
    from . import partidos
    from .hoja import cargar_hoy, hoja, markdown
    from .modelo import Modelo
    hoy = cargar_hoy()
    m = Modelo.ajustar(partidos.cargar())
    hojas = [hoja(m, pt) for pt in hoy["partidos"]]
    salida = RAIZ / "reports" / "hoja_en_vivo.md"
    salida.write_text(markdown(hojas, hoy.get("fecha", "")), encoding="utf-8")
    print(f"{len(hojas)} hojas en {salida.relative_to(RAIZ)}")
    return hojas


def cmd_en_vivo(a):
    """Escanea partidos en vivo cada `--cada` segundos. Ctrl+C para salir."""
    import socket
    import threading
    from functools import partial
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

    from . import partidos
    from .envivo import escanear, html_reporte
    from .modelo import Modelo
    from .sofascore import Cliente, SofascoreError

    m = Modelo.ajustar(partidos.cargar())
    cli = Cliente(pausa=0.5, reintentos=1)
    salida = RAIZ / "reports" / "en_vivo.html"
    salida.parent.mkdir(exist_ok=True)
    if a.servir:
        handler = partial(SimpleHTTPRequestHandler, directory=str(salida.parent))
        srv = ThreadingHTTPServer(("0.0.0.0", a.servir), handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except OSError:
            ip = "IP-de-tu-PC"
        print(f"Abre en la PC http://localhost:{a.servir}/en_vivo.html  y en el celular (misma WiFi) http://{ip}:{a.servir}/en_vivo.html")
    while True:
        try:
            filas = escanear(cli, m, solo_mis_ligas=not a.todas)
        except SofascoreError as e:
            print(f"Sofascore no responde: {e}")
            filas = []
        salida.write_text(html_reporte(filas, a.cada), encoding="utf-8")
        print(f"\n{len(filas)} oportunidades")
        for f in filas[:25]:
            marca = "ALTA" if f["alta"] else "    "
            print(f"{marca} {f['p'] * 100:3.0f}%  min {f['cuota_min']:.2f}  {f['minuto']:>3}' {f['marcador']:5s} {f['patron']}  {f['mercado']:14s} {f['partido']} [{f['liga']}]")
        if a.una_vez:
            return 0
        time.sleep(a.cada)


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
    sub.add_parser("hoja").set_defaults(fn=lambda a: cmd_hoja(a) and 0)
    v = sub.add_parser("en-vivo")
    v.add_argument("--cada", type=int, default=60, help="segundos entre escaneos")
    v.add_argument("--servir", type=int, default=0, help="puerto para ver la página en la red local")
    v.add_argument("--todas", action="store_true", help="incluye ligas fuera de tu historial")
    v.add_argument("--una-vez", action="store_true")
    v.set_defaults(fn=cmd_en_vivo)
    a = p.parse_args(argv)
    return a.fn(a) or 0


if __name__ == "__main__":
    sys.exit(main())
