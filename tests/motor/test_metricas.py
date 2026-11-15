"""Propiedades de las métricas de verificación con datos sintéticos de respuesta conocida."""

from __future__ import annotations

import numpy as np
import pytest

from terraverdict.evaluacion import metricas as M


@pytest.fixture
def rng() -> np.random.Generator:
    return np.random.default_rng(42)


def test_habilidad_cero_frente_a_si_misma(rng: np.random.Generator) -> None:
    y = rng.normal(size=500)
    p = y + rng.normal(scale=0.5, size=500)
    assert M.habilidad_mse(y, p, p) == pytest.approx(0.0, abs=1e-12)
    pr = rng.uniform(size=500)
    eventos = (rng.uniform(size=500) < pr).astype(float)
    assert M.habilidad_brier(eventos, pr, pr) == pytest.approx(0.0, abs=1e-12)


def test_habilidad_perfecta_y_peor_que_referencia(rng: np.random.Generator) -> None:
    y = rng.normal(size=500)
    ref = np.zeros_like(y)
    assert M.habilidad_mse(y, y, ref) == pytest.approx(1.0)
    assert M.habilidad_mse(y, -y, ref) < 0  # duplicar el error hace la habilidad negativa


def test_habilidad_referencia_constante_exacta_es_nan() -> None:
    y = np.ones(10)
    assert np.isnan(M.habilidad_mse(y, y + 1, y))


def test_diebold_mariano_perdidas_iguales() -> None:
    perdida = np.random.default_rng(0).exponential(size=300)
    r = M.diebold_mariano(perdida, perdida)
    assert r["diferencia_media"] == 0.0
    assert np.isnan(r["estadistico"]) and np.isnan(r["p"])  # varianza nula: no hay prueba que hacer


def test_diebold_mariano_misma_distribucion_no_rechaza() -> None:
    rechazos = 0
    for s in range(200):
        g = np.random.default_rng(s)
        rechazos += M.diebold_mariano(g.exponential(size=200), g.exponential(size=200))["p"] < 0.10
    assert 0.04 <= rechazos / 200 <= 0.17  # tamaño nominal del 10 %


def test_diebold_mariano_detecta_modelo_mejor(rng: np.random.Generator) -> None:
    y = rng.normal(size=400)
    bueno, malo = (y - (y + rng.normal(scale=0.3, size=400))) ** 2, (y - rng.normal(size=400)) ** 2
    r = M.diebold_mariano(bueno, malo)
    assert r["estadistico"] < 0 and r["p"] < 0.01


def test_bootstrap_bloques_cubre_la_media(rng: np.random.Generator) -> None:
    x = rng.normal(loc=2.0, size=600)
    lo, hi = M.bootstrap_bloques(lambda a: float(np.mean(a)), x, bloque=10, n=400)
    assert lo < 2.0 < hi and hi - lo < 0.3


def test_tabla_contingencia_cuenta_bien() -> None:
    y = np.array([1, 1, 0, 0, 1, 0])
    p = np.array([0.9, 0.2, 0.8, 0.1, 0.7, 0.3])
    t = M.tabla_contingencia(y, p, 0.5)
    assert (t["aciertos"], t["falsas_alarmas"], t["fallos"], t["correctos_negativos"]) == (2, 1, 1, 2)
    assert t["pod"] == pytest.approx(2 / 3) and t["far"] == pytest.approx(1 / 3) and t["csi"] == pytest.approx(0.5)


def test_confiabilidad_ece_bajo_si_calibrado(rng: np.random.Generator) -> None:
    p = rng.uniform(size=20000)
    y = (rng.uniform(size=20000) < p).astype(float)
    assert M.confiabilidad(y, p)["ece"] < 0.02
    assert M.confiabilidad(y, np.clip(p + 0.2, 0, 1))["ece"] > 0.1


def test_poisson_verosimilitud_maxima_en_la_tasa_real(rng: np.random.Generator) -> None:
    y = rng.poisson(3.0, size=5000)
    ll = {mu: M.log_verosimilitud_poisson(y, np.full(len(y), mu)) for mu in (2.0, 3.0, 4.0)}
    assert ll[3.0] > ll[2.0] and ll[3.0] > ll[4.0]
