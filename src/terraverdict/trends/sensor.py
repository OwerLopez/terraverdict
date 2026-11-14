"""Prueba de sensor: ¿la pendiente sobrevive a un escalón en una transición documentada?
Ajusta x ~ a + b·t (sin escalón) y x ~ a + b·t + c·1[t>=q] (con escalón).
Reporta cambio relativo de b, cambio de signo y AIC. Pettitt como sensibilidad.
"""
from __future__ import annotations

import numpy as np
from scipy import stats


def _ols(X: np.ndarray, y: np.ndarray):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ beta
    n, k = X.shape
    aic = n * np.log(r @ r / n) + 2 * k
    return beta, float(aic)


def pettitt(x: np.ndarray) -> dict:
    n = len(x)
    u = np.array([np.sum([np.sign(x[j] - x[i]) for i in range(t + 1) for j in range(t + 1, n)])
                  for t in range(n - 1)])
    k = float(np.max(np.abs(u)))
    p = float(min(1.0, 2 * np.exp(-6 * k**2 / (n**3 + n**2))))
    return {"indice_quiebre": int(np.argmax(np.abs(u))), "p": p}


def prueba_sensor(anios: np.ndarray, x: np.ndarray, quiebres: dict[str, float]) -> dict:
    t = anios - anios.mean()
    _, aic0 = _ols(np.column_stack([np.ones_like(t), t]), x)
    b0 = _ols(np.column_stack([np.ones_like(t), t]), x)[0][1]
    salida = {}
    for nombre, q in quiebres.items():
        paso = (anios >= q).astype(float)
        if paso.sum() < 5 or (1 - paso).sum() < 5:   # quiebre fuera del periodo útil
            salida[nombre] = {"aplicable": False}
            continue
        beta, aic1 = _ols(np.column_stack([np.ones_like(t), t, paso]), x)
        salida[nombre] = {"aplicable": True, "b_sin_escalon": float(b0), "b_con_escalon": float(beta[1]),
                          "cambio_relativo_b": float(abs(beta[1] - b0) / abs(b0)) if b0 else None,
                          "cambia_signo": bool(np.sign(beta[1]) != np.sign(b0)),
                          "delta_aic": float(aic1 - aic0)}
    return {"quiebres": salida, "pettitt": pettitt(x)}
