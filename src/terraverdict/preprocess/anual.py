"""Series anuales a partir del JSON mensual de POWER (misma lógica del análisis preliminar)."""
from __future__ import annotations

import calendar

import numpy as np


def mensual(par: dict, nombre: str) -> dict[tuple[int, int], float]:
    out = {}
    for k, v in par[nombre].items():
        anio, mes = int(k[:4]), int(k[4:])
        if mes <= 12 and v not in (-999, -999.0):       # mes 13 = promedio anual de POWER
            out[(anio, mes)] = float(v)
    return out


def temperatura_media_anual(t2m: dict, inicio: int, fin: int) -> tuple[np.ndarray, np.ndarray]:
    a = [y for y in range(inicio, fin + 1) if all((y, m) in t2m for m in range(1, 13))]
    return np.array(a), np.array([np.mean([t2m[(y, m)] for m in range(1, 13)]) for y in a])


def lluvia_dic_mar(pr: dict, inicio: int, fin: int) -> tuple[np.ndarray, np.ndarray]:
    """Año hidrológico: dic(año-1) + ene-mar(año). POWER entrega mm/día -> × días del mes."""
    def tot(y):
        ks = [(y - 1, 12), (y, 1), (y, 2), (y, 3)]
        return sum(pr[k] * calendar.monthrange(*k)[1] for k in ks) if all(k in pr for k in ks) else None
    a = [y for y in range(inicio + 1, fin + 1) if tot(y) is not None]
    return np.array(a), np.array([tot(y) for y in a])
