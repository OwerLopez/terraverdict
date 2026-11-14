"""Años necesarios para detectar la pendiente observada (Weatherhead et al., 1998)."""
from __future__ import annotations

import numpy as np


def detectabilidad(anios: np.ndarray, x: np.ndarray, pendiente: float, ordenada: float) -> dict:
    resid = x - (ordenada + pendiente * anios)
    phi = float(np.corrcoef(resid[:-1], resid[1:])[0, 1])
    sigma = float(np.std(resid, ddof=1))
    base = {"sigma_ruido": sigma, "phi_ar1": phi, "anios_disponibles": int(len(x))}
    if pendiente == 0 or not np.isfinite(phi) or phi >= 1:
        return {**base, "anios_necesarios": None}
    n_star = ((3.3 * sigma / abs(pendiente)) * np.sqrt((1 + phi) / (1 - phi))) ** (2 / 3)
    return {**base, "anios_necesarios": float(n_star)}
