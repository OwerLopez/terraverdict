"""Invariantes dinámicos: dimensión de correlación, exponente de Lyapunov, entropías y prueba 0-1.

- Dimensión de correlación D2: Grassberger y Procaccia (1983), doi:10.1016/0167-2789(83)90298-1,
  con ventana de Theiler (Theiler, 1986) y norma del máximo.
- Mayor exponente de Lyapunov: Rosenstein, Collins y De Luca (1993), doi:10.1016/0167-2789(93)90009-P.
- Entropía de permutación: Bandt y Pompe (2002), doi:10.1103/PhysRevLett.88.174102.
- Entropía muestral: Richman y Moorman (2000), doi:10.1152/ajpheart.2000.278.6.H2039.
- Prueba 0-1: Gottwald y Melbourne (2004), doi:10.1098/rspa.2003.1183; implementación de
  Gottwald y Melbourne (2009), doi:10.1137/080718851. Solo distingue caos de dinámica regular
  en sistemas deterministas: el ruido también da K ≈ 1, por eso nunca se usa sola.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.spatial import cKDTree

from .embedding import _vecino_lejano_en_tiempo, embeber


def _radios(Y: np.ndarray, n: int = 32, rng: np.random.Generator | None = None) -> np.ndarray:
    rng = rng or np.random.default_rng(0)
    i = rng.integers(0, len(Y), 20000)
    j = rng.integers(0, len(Y), 20000)
    d = np.max(np.abs(Y[i] - Y[j]), axis=1)
    d = d[d > 0]
    lo, hi = np.quantile(d, 0.0005), np.quantile(d, 0.5)
    return np.logspace(np.log10(lo), np.log10(hi), n)


def integral_correlacion(Y: np.ndarray, radios: np.ndarray, theiler: int) -> tuple[np.ndarray, int]:
    """C(r) sobre pares con |i−j| > theiler (norma del máximo). Devuelve C y el número de pares."""
    n = len(Y)
    arbol = cKDTree(Y)
    total = np.asarray(
        arbol.count_neighbors(arbol, radios, p=np.inf), dtype=float
    )  # pares ordenados con i = j incluidos
    cerca = np.full(len(radios), float(n))  # pares (i, i)
    for d in range(1, theiler + 1):
        dist = np.max(np.abs(Y[d:] - Y[:-d]), axis=1)
        cerca += 2 * (dist[:, None] <= radios[None, :]).sum(0)
    pares = n * n - n - 2 * sum(n - d for d in range(1, theiler + 1))
    return (total - cerca) / pares, pares


def pendiente_escalamiento(log_r: np.ndarray, log_c: np.ndarray, min_puntos: int = 6) -> dict:
    """Pendiente en la región donde la pendiente local es más estable (región de escalamiento)."""
    ok = np.isfinite(log_c)
    log_r, log_c = log_r[ok], log_c[ok]
    if len(log_r) < min_puntos + 1:
        return {"pendiente": float("nan"), "desde": None, "hasta": None, "dispersion_local": float("nan")}
    local = np.diff(log_c) / np.diff(log_r)
    mejor, mejor_i = np.inf, 0
    for i in range(len(local) - min_puntos + 1):
        s = float(np.std(local[i : i + min_puntos]))
        if s < mejor:
            mejor, mejor_i = s, i
    sel = slice(mejor_i, mejor_i + min_puntos + 1)
    pendiente = float(np.polyfit(log_r[sel], log_c[sel], 1)[0])
    return {
        "pendiente": pendiente,
        "desde": float(np.exp(log_r[sel][0])),
        "hasta": float(np.exp(log_r[sel][-1])),
        "dispersion_local": mejor,
    }


def dimension_correlacion(x: np.ndarray, tau: int, m_valores: list[int], theiler: int, max_puntos: int = 4000) -> dict:
    """D2(m) para cada m y diagnóstico de saturación."""
    x = np.asarray(x, float)
    if len(x) > max_puntos:
        x = x[:max_puntos]
    curvas, d2 = [], []
    for m in m_valores:
        Y = embeber(x, m, tau)
        radios = _radios(Y)
        c, pares = integral_correlacion(Y, radios, theiler)
        minimo = 50 / pares  # al menos ~50 pares para estimar C(r)
        log_c = np.where(c > minimo, np.log(np.maximum(c, 1e-300)), np.nan)
        ajuste = pendiente_escalamiento(np.log(radios), log_c)
        d2.append(ajuste["pendiente"])
        curvas.append(
            {
                "m": m,
                "log_r": np.log(radios).round(4).tolist(),
                "log_c": [None if not np.isfinite(v) else round(float(v), 4) for v in log_c],
                "region": [ajuste["desde"], ajuste["hasta"]],
            }
        )
    d2a = np.array(d2)
    # Cota de Eckmann y Ruelle (1992): con N puntos no se puede medir D2 mayor que ~2·log10(N).
    cota = 2 * np.log10(len(x)) - 1
    # Saturación: 3 valores consecutivos de m con variación relativa < 10 %, una meseta claramente
    # por debajo de la dimensión de embedding (el ruido da D2 ≈ m) y por debajo de la cota de datos.
    meseta = None
    for i in range(len(d2a) - 2):
        v = d2a[i : i + 3]
        if not np.all(np.isfinite(v)):
            continue
        media = float(np.mean(v))
        rel = float(np.ptp(v) / max(media, 1e-9))
        if rel < 0.10 and media < m_valores[i] - 0.5 and media < cota and (meseta is None or rel < meseta[1]):
            meseta = (i, rel, media)
    satura = meseta is not None
    return {
        "m": list(m_valores),
        "d2": [round(float(v), 4) for v in d2a],
        "satura": satura,
        "cota_eckmann_ruelle": round(float(cota), 3),
        "meseta_m": [m_valores[meseta[0]], m_valores[meseta[0] + 2]] if meseta else None,
        "d2_saturado": round(meseta[2], 4) if meseta else None,
        "curvas": curvas,
    }


def lyapunov_rosenstein(
    x: np.ndarray, m: int, tau: int, theiler: int, k_max: int = 40, dt: float = 1.0, max_puntos: int = 5000
) -> dict:
    """Mayor exponente de Lyapunov (unidades: 1/dt) y curva de divergencia promedio."""
    x = np.asarray(x, float)[:max_puntos]
    Y = embeber(x, m, tau)
    n = len(Y)
    j, d = _vecino_lejano_en_tiempo(cKDTree(Y), Y, theiler)
    i = np.arange(n)
    ok = (j >= 0) & (d > 0)
    i, j = i[ok], j[ok]
    k_max = int(min(k_max, n // 10))
    curva = []
    for k in range(k_max):
        val = (i + k < n) & (j + k < n)
        dist = np.linalg.norm(Y[i[val] + k] - Y[j[val] + k], axis=1)
        dist = dist[dist > 0]
        curva.append(float(np.mean(np.log(dist))) if len(dist) else float("nan"))
    y = np.array(curva)
    if np.sum(np.isfinite(y)) < 6 or not np.all(np.isfinite(y[:6])):
        return {"lambda": float("nan"), "curva": y.tolist(), "ajuste": None}
    # Región lineal: dentro del 80 % del ascenso, la ventana donde la pendiente local es más estable.
    # Así se evita el transitorio inicial (alineación con la dirección inestable) y la saturación.
    techo = np.nanmax(y)
    limite = int(np.argmax(y >= y[0] + 0.8 * (techo - y[0]))) if techo > y[0] else len(y) - 1
    limite = max(limite, 6)
    local = np.diff(y[: limite + 1])
    ancho = max(4, limite // 3)
    inicio = min(range(len(local) - ancho + 1), key=lambda i: float(np.std(local[i : i + ancho])))
    pasos = np.arange(inicio, inicio + ancho + 1)
    pend = float(np.polyfit(pasos, y[pasos], 1)[0])
    return {"lambda": pend / dt, "curva": [round(float(v), 4) for v in y], "ajuste": [int(pasos[0]), int(pasos[-1])]}


def entropia_permutacion(x: np.ndarray, orden: int = 5, retardo: int = 1) -> float:
    """Entropía de permutación normalizada en [0, 1] (1 = máxima aleatoriedad ordinal)."""
    Y = embeber(np.asarray(x, float), orden, retardo)
    patrones = np.argsort(Y, axis=1, kind="stable")
    codigos = (patrones * (orden ** np.arange(orden))).sum(1)
    _, conteos = np.unique(codigos, return_counts=True)
    p = conteos / conteos.sum()
    return float(-(p * np.log(p)).sum() / math.log(math.factorial(orden)))


def entropia_muestral(x: np.ndarray, m: int = 2, r: float | None = None) -> float:
    """SampEn(m, r) con r = 0,2·σ por defecto; inf si no hay coincidencias de longitud m+1."""
    x = np.asarray(x, float)
    r = 0.2 * float(np.std(x)) if r is None else r
    n = len(x) - m

    def pares(longitud: int) -> float:
        Y = embeber(x, longitud, 1)[:n]
        arbol = cKDTree(Y)
        return (arbol.count_neighbors(arbol, r, p=np.inf) - n) / 2

    b, a = pares(m), pares(m + 1)
    return float("inf") if a == 0 or b == 0 else float(-np.log(a / b))


def prueba_01(x: np.ndarray, n_c: int = 100, rng: np.random.Generator | None = None) -> dict:
    """Prueba 0-1 (método de correlación). K≈0: regular; K≈1: caótica (o estocástica)."""
    rng = rng or np.random.default_rng(1)
    x = np.asarray(x, float)
    n = len(x)
    ncut = max(10, n // 10)
    j = np.arange(1, n + 1)
    pasos = np.arange(1, ncut + 1)
    ks = []
    media2 = float(np.mean(x)) ** 2
    for c in rng.uniform(np.pi / 5, 4 * np.pi / 5, n_c):
        p = np.cumsum(x * np.cos(j * c))
        q = np.cumsum(x * np.sin(j * c))
        msd = np.array([np.mean((p[k:] - p[:-k]) ** 2 + (q[k:] - q[:-k]) ** 2) for k in pasos])
        d = msd - media2 * (1 - np.cos(pasos * c)) / (1 - np.cos(c))
        if np.std(d) == 0:
            continue
        ks.append(float(np.corrcoef(pasos, d)[0, 1]))
    return {"K": float(np.median(ks)) if ks else float("nan"), "n_c": len(ks)}
