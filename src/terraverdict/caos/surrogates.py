"""Pruebas de hipótesis con datos sustitutos (surrogates).

Hipótesis nula: la serie es una transformación estática y monótona de un proceso gaussiano lineal.
Los sustitutos IAAFT conservan el espectro de potencia (autocorrelación lineal) y la distribución
de amplitudes, y destruyen cualquier estructura no lineal.

Theiler et al. (1992), Physica D 58, 77–94, doi:10.1016/0167-2789(92)90102-S;
Schreiber y Schmitz (1996), PRL 77, 635, doi:10.1103/PhysRevLett.77.635;
Schreiber y Schmitz (2000), Physica D 142, 346–382, doi:10.1016/S0167-2789(00)00043-9.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from scipy.spatial import cKDTree

from .embedding import _vecino_lejano_en_tiempo, embeber


def iaaft(x: np.ndarray, rng: np.random.Generator, iteraciones: int = 200) -> np.ndarray:
    x = np.asarray(x, float)
    ordenados = np.sort(x)
    amplitudes = np.abs(np.fft.rfft(x))
    s = rng.permutation(x)
    for _ in range(iteraciones):
        fases = np.angle(np.fft.rfft(s))
        s_nuevo = np.fft.irfft(amplitudes * np.exp(1j * fases), n=len(x))
        rangos = np.argsort(np.argsort(s_nuevo))
        s_sig = ordenados[rangos]
        if np.array_equal(s_sig, s):
            break
        s = s_sig
    return s


def asimetria_temporal(x: np.ndarray, lag: int = 1) -> float:
    """Estadístico de irreversibilidad temporal: ⟨(x_{t+l}−x_t)³⟩ / ⟨(x_{t+l}−x_t)²⟩^{3/2}."""
    d = np.asarray(x, float)[lag:] - np.asarray(x, float)[:-lag]
    den = float(np.mean(d**2)) ** 1.5
    return float(np.mean(d**3) / den) if den > 0 else 0.0


def error_prediccion_no_lineal(
    x: np.ndarray, m: int, tau: int, horizonte: int = 1, k: int = 5, theiler: int | None = None
) -> float:
    """Error cuadrático normalizado de un predictor de análogos (vecinos en el espacio reconstruido).

    Una serie con determinismo no lineal se predice mejor que sus sustitutos (Sugihara y May, 1990,
    doi:10.1038/344734a0).
    """
    x = np.asarray(x, float)
    theiler = tau * m if theiler is None else theiler
    Y = embeber(x, m, tau)
    n = len(Y) - horizonte
    Y = Y[:n]
    futuro = x[(m - 1) * tau + horizonte : (m - 1) * tau + horizonte + n]
    arbol = cKDTree(Y)
    kk = min(k + 2 * theiler + 1, n)
    _, idx = arbol.query(Y, k=kk)
    pred = np.empty(n)
    for i in range(n):
        vecinos = [j for j in idx[i] if abs(j - i) > theiler][:k]
        pred[i] = futuro[vecinos].mean() if vecinos else np.nan
    ok = np.isfinite(pred)
    var = float(np.var(futuro[ok]))
    return float(np.mean((pred[ok] - futuro[ok]) ** 2) / var) if var > 0 else float("nan")


def prueba(
    x: np.ndarray, estadistico: Callable[[np.ndarray], float], n_sustitutos: int, cola: str, rng: np.random.Generator
) -> dict:
    """Prueba por rangos. cola: 'menor' (original menor que sustitutos), 'mayor' o 'dos'.

    p = (1 + #sustitutos al menos tan extremos) / (n + 1): con 99 sustitutos el p mínimo es 0,01.
    """
    original = float(estadistico(x))
    valores = np.array([estadistico(iaaft(x, rng)) for _ in range(n_sustitutos)], float)
    valores = valores[np.isfinite(valores)]
    if cola == "menor":
        extremos = int(np.sum(valores <= original))
    elif cola == "mayor":
        extremos = int(np.sum(valores >= original))
    else:
        centro = float(np.median(valores))
        extremos = int(np.sum(np.abs(valores - centro) >= abs(original - centro)))
    return {
        "original": original,
        "sustitutos_media": float(np.mean(valores)),
        "sustitutos_p05": float(np.quantile(valores, 0.05)),
        "sustitutos_p95": float(np.quantile(valores, 0.95)),
        "n_sustitutos": len(valores),
        "p": (1 + extremos) / (len(valores) + 1),
        "valores": np.round(valores, 5).tolist(),
    }


__all__ = ["_vecino_lejano_en_tiempo", "asimetria_temporal", "error_prediccion_no_lineal", "iaaft", "prueba"]
