"""Partidos terminados y su estado en cualquier minuto.

Formato de `data/backtest/partidos.csv`:
    goles  "H9;A12;H45"  lado (H local, A visitante) y minuto. Añadido del 1T se
           guarda como 45 y añadido del 2T como 90.
    rojas  "A17" roja al visitante al 17'. "H?" roja con minuto desconocido.
    completo 1 si están todos los goles con minuto.
    origen backtest (partido ajeno) o historial (partido donde apostó el usuario).
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CSV_PARTIDOS = RAIZ / "data" / "backtest" / "partidos.csv"


def _eventos(txt: str) -> list[tuple[int | None, str]]:
    out = []
    for tok in (txt or "").split(";"):
        tok = tok.strip()
        if not tok:
            continue
        lado, resto = tok[0], tok[1:]
        if lado not in "HA?":
            raise ValueError(f"evento inválido: {tok!r}")
        out.append((int(resto) if resto.isdigit() else None, lado))
    return out


@dataclass
class Partido:
    liga: str
    fecha: str
    local: str
    visitante: str
    final: tuple[int, int]
    goles: list[tuple[int | None, str]]
    rojas: list[tuple[int | None, str]]
    completo: bool
    origen: str = "backtest"
    fuente: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def nombre(self) -> str:
        return f"{self.local} vs {self.visitante}"

    @property
    def rojas_fiables(self) -> bool:
        return all(m is not None and lado in "HA" for m, lado in self.rojas)

    def estado(self, minuto: int) -> dict:
        """Estado del partido tras `minuto` minutos jugados."""
        gh = sum(1 for m, s in self.goles if m is not None and m <= minuto and s == "H")
        ga = sum(1 for m, s in self.goles if m is not None and m <= minuto and s == "A")
        previos = [m for m, _ in self.goles if m is not None and m <= minuto]
        rh = sum(1 for m, s in self.rojas if m is not None and m <= minuto and s == "H")
        ra = sum(1 for m, s in self.rojas if m is not None and m <= minuto and s == "A")
        return {
            "minuto": minuto, "gl": gh, "gv": ga, "goles": gh + ga, "dif": gh - ga,
            "rojas_local": rh, "rojas_visita": ra, "hay_roja": rh + ra > 0,
            "min_ult_gol": max(previos) if previos else None,
            "goles_ult15": sum(1 for m in previos if m > minuto - 15),
        }

    def goles_despues(self, minuto: int) -> tuple[int, int]:
        gh = sum(1 for m, s in self.goles if m is not None and m > minuto and s == "H")
        ga = sum(1 for m, s in self.goles if m is not None and m > minuto and s == "A")
        return gh, ga


def cargar(path: Path = CSV_PARTIDOS, solo_completos: bool = True, origen: str | None = None) -> list[Partido]:
    out = []
    with path.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if solo_completos and r["completo"] != "1":
                continue
            if origen and r.get("origen", "backtest") != origen:
                continue
            h, a = map(int, r["final"].split(":"))
            p = Partido(r["liga"], r["fecha"], r["local"], r["visitante"], (h, a),
                        _eventos(r["goles"]), _eventos(r["rojas"]), r["completo"] == "1",
                        r.get("origen", "backtest"), r.get("fuente", ""))
            if p.completo and (sum(1 for _, s in p.goles if s == "H"), sum(1 for _, s in p.goles if s == "A")) != p.final:
                raise ValueError(f"goles no cuadran con el final en {p.nombre}")
            out.append(p)
    return out
