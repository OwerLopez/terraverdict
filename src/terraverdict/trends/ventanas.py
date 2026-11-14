"""Robustez ante el periodo. OJO: las ventanas se solapan casi por completo, así que
NO son evidencia independiente (hallazgo 7). Se reporta como robustez, con un peso
menor que ENSO, sensor e independencia.
"""

from __future__ import annotations

import numpy as np
import pymannkendall as pmk
from scipy import stats


def ventanas(anios: np.ndarray, x: np.ndarray, signo_ref: float, L_min: int = 20, alpha: float = 0.10) -> dict:
    n, mismos, sig, total = len(x), 0, 0, 0
    for i in range(n):
        for j in range(i + L_min - 1, n):
            p_ij = stats.theilslopes(x[i : j + 1], anios[i : j + 1])[0]
            total += 1
            mismos += int(np.sign(p_ij) == signo_ref)
            sig += int(pmk.original_test(x[i : j + 1]).p < alpha)
    if total == 0:
        return {"n_ventanas": 0, "pct_mismo_signo": None, "pct_significativas": None}
    return {"n_ventanas": total, "pct_mismo_signo": 100 * mismos / total, "pct_significativas": 100 * sig / total}
