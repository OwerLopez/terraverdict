"""Filtro ENSO: x ~ a + b·t + c·ONI, errores HAC (Newey-West).

OLS con residuos independientes sobreestima la significancia cuando hay
autocorrelación; HAC con maxlags=floor(n^0.25) es la alternativa mínima.
"""
from __future__ import annotations

import numpy as np
import statsmodels.api as sm
from scipy import stats


def filtro_enso(anios: np.ndarray, x: np.ndarray, oni: dict[int, float]) -> dict:
    o = np.array([oni.get(int(a), np.nan) for a in anios])
    ok = ~np.isnan(o)
    if ok.sum() < 10:
        return {"evaluada": False, "motivo": "ONI insuficiente"}
    t = anios[ok] - anios[ok].mean()
    X = sm.add_constant(np.column_stack([t, o[ok]]))
    maxlags = max(1, int(ok.sum() ** 0.25))
    ajuste = sm.OLS(x[ok], X).fit(cov_type="HAC", cov_kwds={"maxlags": maxlags})
    r, p_r = stats.pearsonr(x[ok], o[ok])
    return {
        "evaluada": True, "n": int(ok.sum()),
        "r_pearson_con_oni": float(r), "p_pearson": float(p_r),
        "pendiente_sin_enso_por_decada": 10 * float(ajuste.params[1]),
        "p_pendiente_sin_enso_hac": float(ajuste.pvalues[1]),
        "coef_oni": float(ajuste.params[2]), "p_coef_oni_hac": float(ajuste.pvalues[2]),
    }
