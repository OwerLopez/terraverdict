"""Pendiente de Theil-Sen por década con IC (scipy usa 'alpha' como nivel de confianza)."""

from __future__ import annotations

import numpy as np
from scipy import stats


def sen_por_decada(anios: np.ndarray, x: np.ndarray, ic_nivel: float = 0.90) -> dict:
    pend, ord0, lo, hi = stats.theilslopes(x, anios, alpha=ic_nivel)
    return {
        "sen_por_decada": 10 * float(pend),
        "ic_por_decada": [10 * float(lo), 10 * float(hi)],
        "pendiente": float(pend),
        "ordenada": float(ord0),
    }
