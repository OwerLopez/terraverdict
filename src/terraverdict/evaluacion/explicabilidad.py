"""Explicabilidad agnóstica al modelo: importancia por permutación de variables completas.

Se permuta cada variable en TODOS los pasos de la ventana (no paso a paso) para no romper la
estructura temporal de las demás (Breiman, 2001, doi:10.1023/A:1010933404324; Fisher, Rudin y
Dominici, 2019). La importancia es el aumento de la pérdida; se repite con varias semillas.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np


def importancia_permutacion(
    predecir: Callable[[np.ndarray], np.ndarray],
    X: np.ndarray,
    y: np.ndarray,
    perdida: Callable[[np.ndarray, np.ndarray], float],
    nombres: list[str],
    repeticiones: int = 5,
    semilla: int = 0,
) -> list[dict[str, Any]]:
    rng = np.random.default_rng(semilla)
    base = perdida(y, predecir(X))
    salida: list[dict[str, Any]] = []
    for f, nombre in enumerate(nombres):
        aumentos = []
        for _ in range(repeticiones):
            Xp = X.copy()
            Xp[:, :, f] = Xp[rng.permutation(len(X)), :, f]
            aumentos.append(perdida(y, predecir(Xp)) - base)
        salida.append(
            {
                "variable": nombre,
                "importancia": float(np.mean(aumentos)),
                "desviacion": float(np.std(aumentos)),
                "perdida_base": float(base),
            }
        )
    total = sum(max(0.0, float(s["importancia"])) for s in salida) or 1.0
    for s in salida:
        s["importancia_relativa"] = max(0.0, float(s["importancia"])) / total
    return sorted(salida, key=lambda s: -s["importancia"])
