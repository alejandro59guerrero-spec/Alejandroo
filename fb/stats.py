"""Herramientas estadísticas sin dependencias externas."""
from __future__ import annotations

import math


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalo de confianza de Wilson para una proporción."""
    if n == 0:
        return 0.0, 1.0
    p = k / n
    den = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / den
    margen = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, centro - margen), min(1.0, centro + margen)


def shrink(k: int, n: int, p0: float, fuerza: float = 20.0) -> float:
    """Bayes empírico beta-binomial: acerca k/n a la media global p0.

    `fuerza` es el peso de la media global en partidos equivalentes. Con pocos
    partidos la estimación queda cerca de p0; con muchos, cerca de k/n.
    """
    return (k + p0 * fuerza) / (n + fuerza)


def binom_p_mayor(k: int, n: int, p0: float) -> float:
    """P(X >= k) con X ~ Binomial(n, p0): valor p unilateral de 'acierto > p0'."""
    if n == 0:
        return 1.0
    total = 0.0
    for i in range(k, n + 1):
        total += math.comb(n, i) * p0 ** i * (1 - p0) ** (n - i)
    return min(1.0, total)


def benjamini_hochberg(pvals: list[float], q: float = 0.10) -> list[bool]:
    """Devuelve qué hipótesis sobreviven al control de falsos descubrimientos."""
    m = len(pvals)
    orden = sorted(range(m), key=lambda i: pvals[i])
    corte = -1
    for rango, i in enumerate(orden, start=1):
        if pvals[i] <= q * rango / m:
            corte = rango
    ok = [False] * m
    for rango, i in enumerate(orden, start=1):
        if rango <= corte:
            ok[i] = True
    return ok


def poisson_pmf(k: int, lam: float) -> float:
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam + k * math.log(lam) - math.lgamma(k + 1))


def poisson_al_menos(k: int, lam: float) -> float:
    """P(N >= k) con N ~ Poisson(lam)."""
    if k <= 0:
        return 1.0
    return max(0.0, 1.0 - sum(poisson_pmf(i, lam) for i in range(k)))


def brier(pares: list[tuple[float, int]]) -> float:
    """Brier score de pares (probabilidad, resultado 0/1). Menor es mejor."""
    if not pares:
        return float("nan")
    return sum((p - y) ** 2 for p, y in pares) / len(pares)


def tabla_fiabilidad(pares: list[tuple[float, int]], cortes=(0, .2, .4, .6, .8, 1.0001)):
    """Agrupa predicciones por tramo y compara probabilidad media con frecuencia real."""
    filas = []
    for lo, hi in zip(cortes[:-1], cortes[1:]):
        g = [(p, y) for p, y in pares if lo <= p < hi]
        if g:
            filas.append((lo, min(hi, 1.0), len(g), sum(p for p, _ in g) / len(g), sum(y for _, y in g) / len(g)))
    return filas
