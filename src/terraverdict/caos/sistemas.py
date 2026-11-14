"""Sistemas de referencia con propiedades CONOCIDAS, usados solo para validar los métodos.

No son datos de Arequipa ni se presentan como tales: sirven para comprobar que cada estimador
recupera el valor teórico antes de aplicarlo a series reales.

Valores de referencia de la literatura:
- Mapa logístico r=4: λ = ln 2 ≈ 0,693 por iteración.
- Mapa de Hénon (a=1,4; b=0,3): λ ≈ 0,42; D2 ≈ 1,21 (Grassberger y Procaccia, 1983).
- Lorenz (σ=10, ρ=28, β=8/3): λ ≈ 0,906 por unidad de tiempo; D2 ≈ 2,05.
- AR(1) gaussiano: proceso lineal estocástico (la hipótesis nula de los sustitutos es cierta).
"""

from __future__ import annotations

import numpy as np


def logistico(n: int, r: float = 4.0, x0: float = 0.4, descartar: int = 500) -> np.ndarray:
    x = np.empty(n + descartar)
    x[0] = x0
    for i in range(1, n + descartar):
        x[i] = r * x[i - 1] * (1 - x[i - 1])
    return x[descartar:]


def henon(n: int, a: float = 1.4, b: float = 0.3, descartar: int = 500) -> np.ndarray:
    x, y = 0.1, 0.1
    salida = np.empty(n)
    for i in range(n + descartar):
        x, y = 1 - a * x * x + y, b * x
        if i >= descartar:
            salida[i - descartar] = x
    return salida


def lorenz(n: int, dt: float = 0.01, submuestreo: int = 5, descartar: int = 2000) -> tuple[np.ndarray, float]:
    """Componente x integrada con Runge-Kutta 4; devuelve (serie, paso efectivo)."""

    def f(s: np.ndarray) -> np.ndarray:
        x, y, z = s
        return np.array([10 * (y - x), x * (28 - z) - y, x * y - 8 / 3 * z])

    s = np.array([1.0, 1.0, 1.0])
    total = (n + descartar) * submuestreo
    salida = np.empty(n)
    for i in range(total):
        k1 = f(s)
        k2 = f(s + dt / 2 * k1)
        k3 = f(s + dt / 2 * k2)
        k4 = f(s + dt * k3)
        s = s + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        j = i // submuestreo - descartar
        if i % submuestreo == 0 and 0 <= j < n:
            salida[j] = s[0]
    return salida, dt * submuestreo


def ar1(n: int, phi: float = 0.7, rng: np.random.Generator | None = None) -> np.ndarray:
    rng = rng or np.random.default_rng(0)
    e = rng.standard_normal(n + 200)
    x = np.empty_like(e)
    x[0] = e[0]
    for i in range(1, len(e)):
        x[i] = phi * x[i - 1] + e[i]
    return x[200:]


def seno(n: int, periodo: float = 37.3, ruido: float = 0.0, rng: np.random.Generator | None = None) -> np.ndarray:
    rng = rng or np.random.default_rng(0)
    t = np.arange(n)
    return np.sin(2 * np.pi * t / periodo) + ruido * rng.standard_normal(n)
