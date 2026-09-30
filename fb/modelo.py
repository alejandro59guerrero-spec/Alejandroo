"""Modelo de Poisson en vivo.

Idea: los goles que faltan siguen un proceso de Poisson cuya tasa depende del
tramo del partido, de la liga y de si hay una roja. Con esa tasa se calcula la
probabilidad de cada mercado y la cuota mínima para que la apuesta tenga valor.

Todo se estima con los partidos de `data/backtest/partidos.csv` y se contrae
hacia valores de referencia cuando la muestra es chica.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

from .partidos import Partido
from .stats import poisson_pmf

# Tramos del partido: (inicio, fin, minutos reales con añadido típico)
TRAMOS = [(0, 15, 15), (15, 30, 15), (30, 45, 17), (45, 60, 15), (60, 75, 15), (75, 90, 19)]
FIN_REAL = 94  # 90 más ~4 de añadido
GOLES_REF = 2.6  # referencia por partido cuando la muestra es chica
REPARTO_REF = [0.13, 0.14, 0.17, 0.17, 0.18, 0.21]  # reparto de goles por tramo, referencia


def _tramo(minuto: int) -> int:
    """Tramo de un gol. El añadido del 1T se registra como 45 y cae en el tramo 30-45."""
    if minuto < 15:
        return 0
    if minuto < 30:
        return 1
    if minuto <= 45:
        return 2
    if minuto < 60:
        return 3
    if minuto < 75:
        return 4
    return 5


@dataclass
class Modelo:
    tasa_tramo: list[float]            # goles por minuto real en cada tramo
    factor_liga: dict[str, float] = field(default_factory=dict)
    mult_roja: float = 1.0             # multiplicador de goles tras una roja
    reparto_roja: float = 0.62         # parte de los goles que hace el equipo con uno más
    ventaja_local: float = 0.55        # parte de los goles del local sin rojas
    n_partidos: int = 0
    notas: list[str] = field(default_factory=list)
    equipos: tuple[float, float] | None = None  # goles esperados en 90' (local, visitante)

    # ------------------------------------------------------------ ajuste
    @classmethod
    def ajustar(cls, partidos: list[Partido], fuerza_tramo: float = 15.0,
                fuerza_liga: float = 12.0, fuerza_roja: float = 4.0) -> "Modelo":
        """Estima tasas. Las `fuerza_*` son partidos (o goles) equivalentes de la referencia."""
        n = len(partidos)
        goles_tramo = [0] * len(TRAMOS)
        for p in partidos:
            for m, _ in p.goles:
                if m is not None:
                    goles_tramo[_tramo(m)] += 1
        total = sum(goles_tramo)
        media = total / n if n else GOLES_REF
        # goles por partido en cada tramo, contraídos hacia la referencia
        tasas = []
        for i, (_, _, dur) in enumerate(TRAMOS):
            ref = GOLES_REF * REPARTO_REF[i]
            est = (goles_tramo[i] + ref * fuerza_tramo) / (n + fuerza_tramo)
            tasas.append(est / dur)

        # factor por liga, contraído hacia 1
        por_liga: dict[str, list[int]] = {}
        for p in partidos:
            por_liga.setdefault(p.liga, []).append(sum(p.final))
        factor = {}
        for liga, gs in por_liga.items():
            factor[liga] = ((sum(gs) + media * fuerza_liga) / (len(gs) + fuerza_liga)) / media if media else 1.0

        m = cls(tasas, factor, n_partidos=n)
        # efecto de la roja: goles observados tras la roja contra los esperados
        obs = esp = 0.0
        once = diez = 0
        for p in partidos:
            rojas = [(mm, s) for mm, s in p.rojas if mm is not None and s in "HA"]
            if not rojas or not p.rojas_fiables:
                continue
            mr, lado = min(rojas)
            esp += m.lambda_restante(mr, liga=p.liga, aplicar_roja=False)
            for mg, s in p.goles:
                if mg is not None and mg > mr:
                    obs += 1
                    if s == lado:
                        diez += 1
                    else:
                        once += 1
        if esp > 0:
            m.mult_roja = (obs + fuerza_roja) / (esp + fuerza_roja)
            m.notas.append(f"Roja: {obs:.0f} goles observados tras la roja contra {esp:.1f} esperados.")
        if once + diez:
            m.reparto_roja = (once + 0.62 * 8) / (once + diez + 8)
            m.notas.append(f"Tras la roja marcó el equipo con uno más {once} veces y el de 10 {diez} veces.")
        m.notas.append(f"Goles por partido en la muestra: {media:.2f} en {n} partidos.")
        return m

    # ------------------------------------------------------------ uso
    def _restante_base(self, minuto: int) -> float:
        lam = 0.0
        for i, (a, b, dur) in enumerate(TRAMOS):
            if i == 2 and minuto >= 45:
                continue  # el primer tiempo ya terminó
            fin_real = a + dur  # incluye el añadido típico del tramo
            lam += self.tasa_tramo[i] * max(0.0, fin_real - max(minuto, a))
        return lam

    def lambda_restante(self, minuto: int, liga: str | None = None, aplicar_roja: bool = False) -> float:
        """Goles esperados desde `minuto` hasta el final."""
        lam = self._restante_base(minuto)
        if self.equipos:
            # perfil temporal de la liga escalado a los goles esperados de estos dos equipos
            lam = lam / self._restante_base(0) * sum(self.equipos)
        elif liga:
            lam *= self.factor_liga.get(liga, 1.0)
        if aplicar_roja:
            lam *= self.mult_roja
        return lam

    def prob_mas_goles(self, k: int, minuto: int, liga: str | None = None, roja: bool = False) -> float:
        lam = self.lambda_restante(minuto, liga, roja)
        return max(0.0, 1.0 - sum(poisson_pmf(i, lam) for i in range(k)))

    def prob_over(self, linea: float, goles: int, minuto: int, liga: str | None = None,
                  roja: bool = False) -> dict:
        """Probabilidad de ganar, empatar (devolución) y perder un Over."""
        lam = self.lambda_restante(minuto, liga, roja)
        entera = abs(linea - round(linea)) < 1e-9
        necesita = math.floor(linea) + 1 - goles
        if necesita <= 0:
            return {"gana": 1.0, "nula": 0.0, "pierde": 0.0, "lambda": lam}
        p_menos = sum(poisson_pmf(i, lam) for i in range(necesita))
        p_nula = poisson_pmf(necesita - 1, lam) if entera and necesita - 1 >= 0 and goles + necesita - 1 == linea else 0.0
        gana = 1.0 - p_menos
        return {"gana": gana, "nula": p_nula, "pierde": max(0.0, 1.0 - gana - p_nula), "lambda": lam}

    def _lambdas_equipos(self, minuto: int, liga: str | None, rojas_local: int, rojas_visita: int):
        roja = rojas_local + rojas_visita > 0
        lam = self.lambda_restante(minuto, liga, roja)
        base = self.equipos[0] / sum(self.equipos) if self.equipos else self.ventaja_local
        if rojas_local > rojas_visita:
            parte_local = (base + 1 - self.reparto_roja) / 2 if self.equipos else 1 - self.reparto_roja
        elif rojas_visita > rojas_local:
            parte_local = (base + self.reparto_roja) / 2 if self.equipos else self.reparto_roja
        else:
            parte_local = base
        return lam * parte_local, lam * (1 - parte_local)

    def prob_1x2(self, gl: int, gv: int, minuto: int, liga: str | None = None,
                 rojas_local: int = 0, rojas_visita: int = 0) -> dict:
        """Probabilidad final de local, empate y visitante desde el estado actual."""
        lh, la = self._lambdas_equipos(minuto, liga, rojas_local, rojas_visita)
        pl = pe = pv = 0.0
        for i in range(12):
            pi = poisson_pmf(i, lh)
            for j in range(12):
                pj = poisson_pmf(j, la)
                d = (gl + i) - (gv + j)
                if d > 0:
                    pl += pi * pj
                elif d == 0:
                    pe += pi * pj
                else:
                    pv += pi * pj
        s = pl + pe + pv
        return {"local": pl / s, "empate": pe / s, "visitante": pv / s}

    def prob_evento(self, gl: int, gv: int, minuto: int, evento, liga: str | None = None,
                    rojas_local: int = 0, rojas_visita: int = 0) -> float:
        """P(evento(final_local, final_visita)) sumando sobre la distribución de goles restantes."""
        lh, la = self._lambdas_equipos(minuto, liga, rojas_local, rojas_visita)
        tot = acc = 0.0
        for i in range(12):
            pi = poisson_pmf(i, lh)
            for j in range(12):
                pij = pi * poisson_pmf(j, la)
                tot += pij
                if evento(gl + i, gv + j):
                    acc += pij
        return acc / tot if tot else 0.0

    def prob_btts(self, gl: int, gv: int, minuto: int, liga: str | None = None,
                  rojas_local: int = 0, rojas_visita: int = 0) -> float:
        lh, la = self._lambdas_equipos(minuto, liga, rojas_local, rojas_visita)
        p_l = 1.0 if gl > 0 else 1 - math.exp(-lh)
        p_v = 1.0 if gv > 0 else 1 - math.exp(-la)
        return p_l * p_v

    def con_equipos(self, gf_local: float, gc_local: float, gf_visita: float, gc_visita: float) -> "Modelo":
        """Copia del modelo con la fuerza de cada equipo.

        Usa los promedios por partido de goles a favor (gf) y en contra (gc) que
        publican sitios como scores24: goles esperados del local = (gf_local +
        gc_visita) / 2 y del visitante = (gf_visita + gc_local) / 2. Idealmente,
        promedios del local jugando en casa y del visitante jugando fuera.
        """
        import copy
        m = copy.copy(self)
        m.equipos = ((gf_local + gc_visita) / 2, (gf_visita + gc_local) / 2)
        return m

    def con_fuerza(self, p_local_pre: float, liga: str | None = None) -> "Modelo":
        """Copia del modelo cuyo reparto de goles reproduce la probabilidad prepartido del local.

        `p_local_pre` sale de la cuota prepartido (1/cuota sin margen). Sin este dato
        el modelo trata a los dos equipos casi iguales y subestima al favorito.
        """
        import copy
        lo, hi = 0.15, 0.85
        for _ in range(40):
            mid = (lo + hi) / 2
            m = copy.copy(self)
            m.ventaja_local = mid
            if m.prob_1x2(0, 0, 0, liga)["local"] < p_local_pre:
                lo = mid
            else:
                hi = mid
        m = copy.copy(self)
        m.ventaja_local = (lo + hi) / 2
        return m

    # ------------------------------------------------------------ exportar
    def a_json(self) -> dict:
        return {
            "tramos": [[a, b, d] for a, b, d in TRAMOS],
            "tasa_tramo": [round(t, 5) for t in self.tasa_tramo],
            "factor_liga": {k: round(v, 3) for k, v in sorted(self.factor_liga.items())},
            "mult_roja": round(self.mult_roja, 3),
            "reparto_roja": round(self.reparto_roja, 3),
            "ventaja_local": self.ventaja_local,
            "n_partidos": self.n_partidos,
            "notas": self.notas,
        }

    def guardar(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.a_json(), ensure_ascii=False, indent=2), encoding="utf-8")


def cuota_minima(p: float, colchon: float = 0.0) -> float:
    """Cuota a partir de la cual la apuesta tiene valor esperado positivo."""
    if p <= 0:
        return float("inf")
    return (1 + colchon) / p


def valor_esperado(p_gana: float, cuota: float, p_nula: float = 0.0) -> float:
    """Ganancia esperada por unidad apostada. Una nula devuelve el stake."""
    return p_gana * (cuota - 1) - (1 - p_gana - p_nula)
