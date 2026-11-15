"""Selección de variables por relevancia, redundancia y plausibilidad física.

mRMR (Peng, Long y Ding, 2005, doi:10.1109/TPAMI.2005.159) con información mutua estimada por
k vecinos (Kraskov, Stögbauer y Grassberger, 2004, doi:10.1103/PhysRevE.69.066138, en scikit-learn),
ponderada por el prior físico del catálogo (alta = 1,0; media = 0,8; baja = 0,6).

- Relevancia: IM(variable; objetivo).
- Redundancia: |ρ de Spearman| máxima con las variables ya elegidas, en [0, 1]. No se usa IM entre
  variables porque, con un objetivo binario, la relevancia está acotada por la entropía del evento
  (≈ 0,26 nats con una tasa del 7 %) y la IM entre variables continuas no: restarlas mezcla escalas
  y descarta casi todo (defecto encontrado el 2026-11-15, ver docs/bitacora.md).
- Puntaje: peso · IM · (1 − redundancia), la forma multiplicativa (relevancia descontada) en lugar
  de la diferencia de Peng et al.
- Una variable sin señal no entra aunque esté disponible: su IM descontada debe superar la máxima
  IM obtenida contra 50 permutaciones del objetivo (≈ percentil 98 del nulo; el estimador KSG es
  positivo con ruido puro y su nulo tiene cola larga).
"""

from __future__ import annotations

import numpy as np
from scipy import stats
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
    permutaciones: int = 50,
) -> dict:
    estimar = mutual_info_classif if clasificacion else mutual_info_regression
    mi = estimar(X, y, n_neighbors=5, random_state=semilla)
    rng = np.random.default_rng(semilla)
    nula = np.array([estimar(X, rng.permutation(y), n_neighbors=5, random_state=semilla) for _ in range(permutaciones)])
    umbral = nula.max(axis=0)  # máximo de 50 permutaciones ≈ percentil 98 del nulo
    seleccion = list(siempre or [])
    sin_senal = [i for i, n in enumerate(nombres) if n not in seleccion and mi[i] <= umbral[i]]
    candidatas = [i for i, n in enumerate(nombres) if n not in seleccion and i not in sin_senal]
    rho = np.abs(stats.spearmanr(X).statistic) if X.shape[1] > 2 else np.abs(np.corrcoef(stats.rankdata(X, axis=0).T))
    elegidas_idx = [nombres.index(n) for n in seleccion]
    tabla: list[dict] = [
        {
            "variable": nombres[i],
            "informacion_mutua": float(mi[i]),
            "redundancia": None,
            "peso_fisico": None,
            "puntaje": None,
            "fija": True,
        }
        for i in elegidas_idx
    ]
    while candidatas and len(elegidas_idx) < maximo:
        puntajes = []
        for i in candidatas:
            r = float(np.max(rho[i, elegidas_idx])) if elegidas_idx else 0.0
            p = PESOS.get(prior.get(nombres[i], "media"), 0.8)
            puntajes.append((p * mi[i] * (1 - r), i, r, p))
        puntaje, i, r, p = max(puntajes)
        if mi[i] * (1 - r) <= umbral[i]:
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
                "fija": False,
            }
        )
    descartadas = [
        {
            "variable": nombres[i],
            "informacion_mutua": float(mi[i]),
            "umbral_nulo": float(umbral[i]),
            "motivo": "sin señal frente al objetivo permutado" if i in sin_senal else "redundante o sin ganancia",
        }
        for i in sorted([*sin_senal, *candidatas])
    ]
    return {
        "seleccionadas": [nombres[i] for i in elegidas_idx],
        "detalle": tabla,
        "descartadas": descartadas,
        "informacion_mutua": {n: float(v) for n, v in zip(nombres, mi, strict=False)},
        "umbral_nulo": {n: float(v) for n, v in zip(nombres, umbral, strict=False)},
        "permutaciones": permutaciones,
        "redundancia": "|rho de Spearman| máxima con las ya elegidas",
    }
