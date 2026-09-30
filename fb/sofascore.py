"""Cliente mínimo de la API pública de Sofascore con caché en disco.

Uso responsable: 1 petición por segundo por defecto, reintentos con espera
exponencial y caché gzip en `data/raw/sofascore/` para no repetir descargas.
La carpeta `data/raw/` está fuera de git.

Endpoints usados (API no oficial; puede cambiar sin aviso):
    event/{id}                     datos del partido
    event/{id}/incidents           goles, tarjetas, penales, añadido
    event/{id}/statistics          estadísticas por periodo (ALL, 1ST, 2ND)
    event/{id}/shotmap             cada tiro con minuto y xG
    event/{id}/graph               presión minuto a minuto
    sport/football/scheduled-events/{AAAA-MM-DD}
    unique-tournament/{ut}/seasons
    unique-tournament/{ut}/season/{s}/events/last/{pagina}
"""
from __future__ import annotations

import gzip
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CACHE = RAIZ / "data" / "raw" / "sofascore"
BASE = "https://api.sofascore.com/api/v1/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://www.sofascore.com/",
}


class SofascoreError(RuntimeError):
    pass


class Cliente:
    def __init__(self, pausa: float = 1.0, reintentos: int = 4, cache: Path = CACHE, base: str = BASE):
        self.pausa = pausa
        self.reintentos = reintentos
        self.cache = cache
        self.base = base
        self._ultima = 0.0

    def _ruta_cache(self, ruta: str) -> Path:
        return self.cache / (ruta.strip("/").replace("/", "__") + ".json.gz")

    def get(self, ruta: str, usar_cache: bool = True) -> dict | None:
        """GET a la API. Devuelve None si el recurso no existe (404)."""
        archivo = self._ruta_cache(ruta)
        if usar_cache and archivo.exists():
            with gzip.open(archivo, "rt", encoding="utf-8") as f:
                return json.load(f)
        espera = 2.0
        for intento in range(self.reintentos + 1):
            dt = time.time() - self._ultima
            if dt < self.pausa:
                time.sleep(self.pausa - dt)
            self._ultima = time.time()
            req = urllib.request.Request(self.base + ruta.lstrip("/"), headers=HEADERS)
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    data = json.loads(r.read().decode("utf-8"))
                archivo.parent.mkdir(parents=True, exist_ok=True)
                with gzip.open(archivo, "wt", encoding="utf-8") as f:
                    json.dump(data, f)
                return data
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return None
                if e.code in (403, 429, 500, 502, 503) and intento < self.reintentos:
                    time.sleep(espera)
                    espera *= 2
                    continue
                raise SofascoreError(f"HTTP {e.code} en {ruta}") from e
            except (urllib.error.URLError, TimeoutError) as e:
                if intento < self.reintentos:
                    time.sleep(espera)
                    espera *= 2
                    continue
                raise SofascoreError(f"Sin conexión a Sofascore ({e}). Revisa el acceso de red.") from e
        return None

    # ---------------------------------------------------------------- atajos
    def evento(self, eid: int) -> dict | None:
        return self.get(f"event/{eid}")

    def incidentes(self, eid: int) -> dict | None:
        return self.get(f"event/{eid}/incidents")

    def estadisticas(self, eid: int) -> dict | None:
        return self.get(f"event/{eid}/statistics")

    def tiros(self, eid: int) -> dict | None:
        return self.get(f"event/{eid}/shotmap")

    def presion(self, eid: int) -> dict | None:
        return self.get(f"event/{eid}/graph")

    def eventos_del_dia(self, fecha: str) -> list[dict]:
        d = self.get(f"sport/football/scheduled-events/{fecha}") or {}
        return d.get("events", [])

    def temporadas(self, ut: int) -> list[dict]:
        d = self.get(f"unique-tournament/{ut}/seasons") or {}
        return d.get("seasons", [])

    def ultimos_eventos(self, ut: int, temporada: int, paginas: int = 5) -> list[dict]:
        out = []
        for pag in range(paginas):
            d = self.get(f"unique-tournament/{ut}/season/{temporada}/events/last/{pag}", usar_cache=False)
            if not d:
                break
            out.extend(d.get("events", []))
            if not d.get("hasNextPage"):
                break
        return out


def probar() -> tuple[bool, str]:
    """Paso 0 del plan: comprueba si la red permite llegar a Sofascore."""
    try:
        d = Cliente(pausa=0, reintentos=0).get("sport/football/scheduled-events/2026-09-27", usar_cache=False)
        n = len((d or {}).get("events", []))
        return True, f"Sofascore responde: {n} partidos el 27/09/2026."
    except SofascoreError as e:
        return False, str(e)
