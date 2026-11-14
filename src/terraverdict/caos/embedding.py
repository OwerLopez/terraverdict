"""Reconstrucción del espacio de fases por retardos (Takens, 1981).

- Retardo τ: primer mínimo de la información mutua promedio (Fraser y Swinney, 1986,
  doi:10.1103/PhysRevA.33.1134); si no existe, primer cruce de la autocorrelación por 1/e.
- Dimensión m: falsos vecinos más cercanos (Kennel, Brown y Abarbanel, 1992,
  doi:10.1103/PhysRevA.45.3403), excluyendo vecinos temporales (ventana de Theiler).
"""

from __future__ import annotations

import numpy as np
from scipy.spatial import cKDTree


def embeber(x: np.ndarray, m: int, tau: int) -> np.ndarray:
    """Matriz de vectores de retardo [x_t, x_{t+τ}, …, x_{t+(m-1)τ}] (filas = tiempo)."""
    x = np.asarray(x, float)
    n = len(x) - (m - 1) * tau
    if n <= 0:
        raise ValueError(f"Serie demasiado corta para m={m}, τ={tau}")
    return np.column_stack([x[i * tau : i * tau + n] for i in range(m)])


def _rangos_uniformes(x: np.ndarray) -> np.ndarray:
    orden = np.argsort(x, kind="stable")
    r = np.empty(len(x))
    r[orden] = (np.arange(len(x)) + 0.5) / len(x)
    return r


def informacion_mutua(x: np.ndarray, max_lag: int, bins: int | None = None) -> np.ndarray:
    """Información mutua promedio I(τ) en nats para τ = 0..max_lag (histograma sobre rangos)."""
    u = _rangos_uniformes(np.asarray(x, float))
    bins = bins or max(8, int(np.sqrt(len(u) / 5)))
    salida = []
    for lag in range(max_lag + 1):
        a, b = (u, u) if lag == 0 else (u[:-lag], u[lag:])
        h, _, _ = np.histogram2d(a, b, bins=bins, range=[[0, 1], [0, 1]])
        p = h / h.sum()
        px, py = p.sum(1, keepdims=True), p.sum(0, keepdims=True)
        nz = p > 0
        salida.append(float((p[nz] * np.log(p[nz] / (px @ py)[nz])).sum()))
    return np.array(salida)


def autocorrelacion(x: np.ndarray, max_lag: int) -> np.ndarray:
    x = np.asarray(x, float) - np.mean(x)
    var = float(x @ x)
    return np.array([1.0 if k == 0 else float(x[:-k] @ x[k:]) / var for k in range(max_lag + 1)])


def retardo_optimo(x: np.ndarray, max_lag: int = 60) -> dict:
    """τ = mínimo entre el primer mínimo de la AMI y el primer cruce |ACF| < 1/e.

    En mapas (caos de tiempo discreto) la AMI cae al piso de ruido en pocos pasos y su "primer
    mínimo" aparece por fluctuaciones del estimador en retardos grandes; la autocorrelación ya
    es ~0 en τ = 1. Tomar el menor de ambos criterios estándar evita retardos excesivos, que
    degradan la reconstrucción (validado con logístico, Hénon y Lorenz en las pruebas).
    """
    max_lag = int(min(max_lag, len(x) // 10))
    ami = informacion_mutua(x, max_lag)
    tau_ami = next((k for k in range(1, len(ami) - 1) if ami[k] < ami[k - 1] and ami[k] <= ami[k + 1]), None)
    acf = autocorrelacion(x, max_lag)
    debajo = np.nonzero(np.abs(acf[1:]) < 1 / np.e)[0]
    tau_acf = int(debajo[0]) + 1 if len(debajo) else None
    candidatos = {k: v for k, v in {"primer_minimo_ami": tau_ami, "acf_1_e": tau_acf}.items() if v}
    if not candidatos:
        return {"tau": 1, "metodo": "por_defecto", "tau_ami": None, "tau_acf": None, "ami": ami.tolist()}
    metodo = min(candidatos, key=lambda k: candidatos[k])
    return {
        "tau": int(candidatos[metodo]),
        "metodo": metodo,
        "tau_ami": tau_ami,
        "tau_acf": tau_acf,
        "ami": ami.tolist(),
    }


def _vecino_lejano_en_tiempo(arbol: cKDTree, Y: np.ndarray, theiler: int, k: int = 24):
    """Índice y distancia del vecino más cercano con |i−j| > theiler (−1 si no hay)."""
    k = min(k, len(Y))
    dist, idx = arbol.query(Y, k=k)
    filas = np.arange(len(Y))[:, None]
    validos = np.abs(idx - filas) > theiler
    primero = np.argmax(validos, axis=1)
    hay = validos[np.arange(len(Y)), primero]
    j = np.where(hay, idx[np.arange(len(Y)), primero], -1)
    d = np.where(hay, dist[np.arange(len(Y)), primero], np.nan)
    return j, d


def falsos_vecinos(
    x: np.ndarray, tau: int, m_max: int = 10, theiler: int | None = None, rtol: float = 15.0, atol: float = 2.0
) -> list[float]:
    """Fracción de falsos vecinos para m = 1..m_max (criterios 1 y 2 de Kennel et al.)."""
    x = np.asarray(x, float)
    theiler = tau if theiler is None else theiler
    ra = float(np.std(x))
    fracciones = []
    for m in range(1, m_max + 1):
        n = len(x) - m * tau  # puntos que existen también en dimensión m+1
        if n < 50:
            break
        Y = embeber(x, m, tau)[:n]
        j, d = _vecino_lejano_en_tiempo(cKDTree(Y), Y, theiler)
        ok = (j >= 0) & (d > 0)
        i = np.nonzero(ok)[0]
        jj = j[ok]
        extra = np.abs(x[i + m * tau] - x[jj + m * tau])
        r_m = d[ok]
        r_m1 = np.sqrt(r_m**2 + extra**2)
        falso = (extra / r_m > rtol) | (r_m1 / ra > atol)
        fracciones.append(float(np.mean(falso)) if len(falso) else float("nan"))
    return fracciones


def dimension_embedding(fnn: list[float], umbral: float = 0.01, meseta: float = 0.01) -> int:
    """Primera m con FNN < umbral; con ruido, la FNN no llega a cero y se toma el inicio de la
    meseta (la fracción deja de bajar más de ``meseta`` al aumentar m)."""
    for m, f in enumerate(fnn, start=1):
        if f < umbral:
            return m
    for m in range(1, len(fnn)):
        if fnn[m - 1] - fnn[m] < meseta:
            return m
    return int(np.nanargmin(fnn)) + 1 if fnn else 1


def periodo_medio(x: np.ndarray) -> float:
    """Periodo medio (inverso de la frecuencia media del espectro), en muestras."""
    x = np.asarray(x, float) - np.mean(x)
    potencia = np.abs(np.fft.rfft(x)) ** 2
    f = np.fft.rfftfreq(len(x))
    if potencia[1:].sum() == 0:
        return 1.0
    fmedia = float((f[1:] * potencia[1:]).sum() / potencia[1:].sum())
    return 1.0 / fmedia if fmedia > 0 else float(len(x))
