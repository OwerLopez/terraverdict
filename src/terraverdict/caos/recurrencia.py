"""Análisis de cuantificación de recurrencias (RQA).

Eckmann, Kamphorst y Ruelle (1987), doi:10.1209/0295-5075/4/9/004;
Marwan, Romano, Thiel y Kurths (2007), Physics Reports 438, doi:10.1016/j.physrep.2006.11.001.
El umbral ε se fija para una tasa de recurrencia objetivo, lo que hace comparables las series.
"""

from __future__ import annotations

import numpy as np
from scipy.spatial.distance import cdist


def _longitudes(fila: np.ndarray) -> np.ndarray:
    """Longitudes de las rachas de True en un vector booleano."""
    b = np.concatenate([[False], fila, [False]]).astype(np.int8)
    cambios = np.diff(b)
    return np.nonzero(cambios == -1)[0] - np.nonzero(cambios == 1)[0]


def matriz_recurrencia(Y: np.ndarray, tasa: float = 0.05, theiler: int = 1) -> tuple[np.ndarray, float]:
    D = cdist(Y, Y, metric="chebyshev")
    n = len(Y)
    mascara = np.abs(np.subtract.outer(np.arange(n), np.arange(n))) > theiler
    eps = float(np.quantile(D[mascara], tasa))
    R = (eps >= D) & mascara
    return R, eps


def rqa(
    Y: np.ndarray, tasa: float = 0.05, l_min: int = 2, theiler: int = 1, max_puntos: int = 1500, miniatura: int = 120
) -> dict:
    if len(Y) > max_puntos:  # segmento contiguo central: conserva la estructura temporal
        inicio = (len(Y) - max_puntos) // 2
        Y = Y[inicio : inicio + max_puntos]
    R, eps = matriz_recurrencia(Y, tasa, theiler)
    n = len(R)
    total = int(R.sum())
    diagonales = np.concatenate([_longitudes(np.diagonal(R, k)) for k in range(theiler + 1, n)] or [np.array([], int)])
    verticales = np.concatenate([_longitudes(R[:, k]) for k in range(n)] or [np.array([], int)])
    largas = diagonales[diagonales >= l_min]
    largas_v = verticales[verticales >= l_min]
    puntos_sup = total / 2  # R es simétrica: las diagonales se cuentan en el triángulo superior
    det = float(largas.sum() / puntos_sup) if puntos_sup else float("nan")
    lam = float(largas_v.sum() / total) if total else float("nan")
    if len(largas):
        _, conteo = np.unique(largas, return_counts=True)
        p = conteo / conteo.sum()
        entr = float(-(p * np.log(p)).sum())
    else:
        entr = 0.0
    # miniatura para la interfaz: densidad de recurrencias por bloque (0..1)
    b = max(1, n // miniatura)
    nb = n // b
    mini = R[: nb * b, : nb * b].reshape(nb, b, nb, b).mean(axis=(1, 3))
    return {
        "n": n,
        "epsilon": eps,
        "tasa_recurrencia": float(total / (n * n)),
        "determinismo": det,
        "laminaridad": lam,
        "longitud_media_diagonal": float(largas.mean()) if len(largas) else 0.0,
        "longitud_max_diagonal": int(largas.max()) if len(largas) else 0,
        "entropia_diagonales": entr,
        "tiempo_atrapamiento": float(largas_v.mean()) if len(largas_v) else 0.0,
        "miniatura": np.round(mini, 3).tolist(),
    }
