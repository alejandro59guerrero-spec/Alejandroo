"""Cliente de API-Football (api-sports.io) para datos EN VIVO.

Fuente legítima y pensada para acceso programático: a diferencia de las webs de
scraping, sí deja conectarse desde la nube con una clave gratuita. Cubre las ligas
del usuario (Perú, Colombia, Brasil Serie B, Argentina, etc.).

Requiere la variable de entorno API_FOOTBALL_KEY (nunca se guarda en el repo).
Consíguela gratis en https://dashboard.api-football.com y agrega el dominio
`v3.football.api-sports.io` en Network access del entorno.

Plan gratis: 100 peticiones al día. Cada escaneo gasta 1 (lista de vivos) más 1
por partido que pida el detalle de eventos, así que conviene espaciarlo.

Endpoints usados (v3):
    fixtures?live=all              partidos en juego con marcador y minuto
    fixtures/events?fixture={id}   goles y tarjetas al minuto
"""
from __future__ import annotations

import gzip
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CACHE = RAIZ / "data" / "raw" / "apifootball"
BASE = "https://v3.football.api-sports.io/"
ENV_CLAVE = "API_FOOTBALL_KEY"


class ApiFootballError(RuntimeError):
    pass


class SinClave(ApiFootballError):
    pass


class Cliente:
    def __init__(self, clave: str | None = None, pausa: float = 1.0, reintentos: int = 3,
                 cache: Path = CACHE, base: str = BASE):
        self.clave = clave or os.environ.get(ENV_CLAVE, "")
        self.pausa = pausa
        self.reintentos = reintentos
        self.cache = cache
        self.base = base
        self._ultima = 0.0

    def _ruta_cache(self, ruta: str) -> Path:
        return self.cache / (ruta.strip("/").replace("/", "__").replace("?", "__").replace("=", "-") + ".json.gz")

    def get(self, ruta: str, usar_cache: bool = True) -> dict:
        if not self.clave:
            raise SinClave(
                f"Falta la clave de API-Football. Guárdala en la variable {ENV_CLAVE} "
                "(sácala gratis en https://dashboard.api-football.com).")
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
            req = urllib.request.Request(self.base + ruta.lstrip("/"),
                                         headers={"x-apisports-key": self.clave, "Accept": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    data = json.loads(r.read().decode("utf-8"))
                if data.get("errors"):
                    raise ApiFootballError(f"API-Football devolvió errores: {data['errors']}")
                archivo.parent.mkdir(parents=True, exist_ok=True)
                with gzip.open(archivo, "wt", encoding="utf-8") as f:
                    json.dump(data, f)
                return data
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503) and intento < self.reintentos:
                    time.sleep(espera)
                    espera *= 2
                    continue
                raise ApiFootballError(f"HTTP {e.code} en {ruta}") from e
            except (urllib.error.URLError, TimeoutError) as e:
                if intento < self.reintentos:
                    time.sleep(espera)
                    espera *= 2
                    continue
                raise ApiFootballError(f"Sin conexión a API-Football ({e}). Revisa el acceso de red.") from e
        return {}

    # ---------------------------------------------------------------- atajos
    def en_vivo(self) -> list[dict]:
        """Partidos en juego ahora mismo. Cada uno trae league, teams, goals y fixture.status.elapsed."""
        return self.get("fixtures?live=all", usar_cache=False).get("response", [])

    def eventos(self, fixture_id: int) -> list[dict]:
        """Goles y tarjetas del partido, con minuto."""
        return self.get(f"fixtures/events?fixture={fixture_id}", usar_cache=False).get("response", [])

    def estadisticas(self, fixture_id: int) -> list[dict]:
        """Estadísticas acumuladas por equipo: tiros, tiros a puerta, córners, posesión.

        No trae 'ataques peligrosos' ni xG en el plan gratis; puede venir vacía en
        ligas sin cobertura de estadísticas.
        """
        return self.get(f"fixtures/statistics?fixture={fixture_id}", usar_cache=False).get("response", [])


def probar(clave: str | None = None) -> tuple[bool, str]:
    """Comprueba la clave y el acceso a API-Football."""
    try:
        cli = Cliente(clave, pausa=0, reintentos=1)
        vivos = cli.en_vivo()
        return True, f"API-Football responde: {len(vivos)} partidos en vivo ahora mismo."
    except SinClave as e:
        return False, str(e)
    except ApiFootballError as e:
        return False, str(e)
