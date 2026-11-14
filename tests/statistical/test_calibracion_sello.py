"""E4: con series SIN tendencia (AR(1)), la tasa de 'significativa' debe ser ≈ alpha o menos.
Marcado slow: pytest -m slow"""
import numpy as np
import pytest

from terraverdict.trends.mk import mk_conservador


@pytest.mark.slow
@pytest.mark.parametrize("phi", [0.0, 0.3, 0.6])
def test_falsos_positivos_ar1(phi, pre):
    rng = np.random.default_rng(42)
    n, reps, fp = 44, 400, 0
    for _ in range(reps):
        e = rng.normal(size=n + 50)
        x = np.zeros_like(e)
        for t in range(1, len(e)):
            x[t] = phi * x[t - 1] + e[t]
        fp += mk_conservador(x[50:])["p_conservador"] < pre.alpha
    tasa = fp / reps
    assert tasa <= pre.alpha + 0.04, f"phi={phi}: tasa de falsos positivos {tasa:.3f}"
