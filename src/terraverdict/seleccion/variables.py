"""Selección de variables por relevancia, redundancia y plausibilidad física.

mRMR (Peng, Long y Ding, 2005, doi:10.1109/TPAMI.2005.159) con información mutua estimada por
k vecinos (Kraskov, Stögbauer y Grassberger, 2004, doi:10.1103/PhysRevE.69.066138, en scikit-learn),
ponderada por el prior físico del catálogo (alta = 1,0; media = 0,8; baja = 0,6). Una variable
sin señal no entra aunque esté disponible: su información mutua debe superar el percentil 95 de la
que obtiene contra el objetivo permutado (el estimador KSG es positivo incluso con ruido puro), y
su relevancia − redundancia debe ser > 0.
"""

from __future__ import annotations

import numpy as np
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression

PESOS = {"alta": 1.0, "media": 0.8, "baja": 0.6}


def mrmr(
    X: np.ndarray,
    y: np.ndarray,
    nombres: list[str],
    prior: dict[str, str],
    *,
    clasificacion: bool,
    siempre: list[str] | None = None,
    maximo: int = 8,
    semilla: int = 0,
    permutaciones: int = 20,
) -> dict:
    estimar = mutual_info_classif if clasificacion else mutual_info_regression
    mi = estimar(X, y, n_neighbors=5, random_state=semilla)
    rng = np.random.default_rng(semilla)
    nula = np.array([estimar(X, rng.permutation(y), n_neighbors=5, random_state=semilla) for _ in range(permutaciones)])
    umbral = np.quantile(nula, 0.95, axis=0)
    seleccion = list(siempre or [])
    sin_senal = [i for i, n in enumerate(nombres) if n not in seleccion and mi[i] <= umbral[i]]
    candidatas = [i for i, n in enumerate(nombres) if n not in seleccion and i not in sin_senal]
    tabla = []
    redundancia_cache: dict[tuple[int, int], float] = {}

    def red(i: int, j: int) -> float:
        k = (min(i, j), max(i, j))
        if k not in redundancia_cache:
            redundancia_cache[k] = float(
                mutual_info_regression(X[:, [i]], X[:, j], n_neighbors=5, random_state=semilla)[0]
            )
        return redundancia_cache[k]

    elegidas_idx = [nombres.index(n) for n in seleccion]
    while candidatas and len(elegidas_idx) < maximo:
        puntajes = []
        for i in candidatas:
            r = float(np.mean([red(i, j) for j in elegidas_idx])) if elegidas_idx else 0.0
            p = PESOS.get(prior.get(nombres[i], "media"), 0.8)
            puntajes.append((p * (mi[i] - r), i, r, p))
        puntaje, i, r, p = max(puntajes)
        if puntaje <= 0:
            break
        elegidas_idx.append(i)
        candidatas.remove(i)
        tabla.append(
            {
                "variable": nombres[i],
                "informacion_mutua": float(mi[i]),
                "redundancia": r,
                "peso_fisico": p,
                "puntaje": float(puntaje),
            }
        )
    descartadas = [
        {
            "variable": nombres[i],
            "informacion_mutua": float(mi[i]),
            "umbral_nulo_p95": float(umbral[i]),
            "motivo": "sin señal frente al objetivo permutado" if i in sin_senal else "redundante o sin ganancia",
        }
        for i in sorted([*sin_senal, *candidatas])
    ]
    return {
        "seleccionadas": [nombres[i] for i in elegidas_idx],
        "detalle": tabla,
        "descartadas": descartadas,
        "informacion_mutua": {n: float(v) for n, v in zip(nombres, mi, strict=False)},
        "umbral_nulo_p95": {n: float(v) for n, v in zip(nombres, umbral, strict=False)},
        "permutaciones": permutaciones,
    }
