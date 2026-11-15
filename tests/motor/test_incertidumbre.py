"""Intervalos conformales, calibración, deriva y abstención."""

from __future__ import annotations

import numpy as np
import pytest

from terraverdict.evaluacion import metricas as M
from terraverdict.evaluacion.incertidumbre import (
    CalibradorIsotonico,
    cobertura,
    cuantil_conformal,
    decidir_abstencion,
    deriva,
    intervalos_conformales,
    psi,
)


def test_cobertura_conformal_con_datos_intercambiables() -> None:
    """Con residuos i.i.d. la cobertura marginal es ≥ 90 % y no mucho mayor (Vovk et al., 2005)."""
    coberturas = []
    for s in range(50):
        g = np.random.default_rng(s)
        x_cal, x_prueba = g.normal(size=300), g.normal(size=2000)
        y_cal, y_prueba = 2 * x_cal + g.standard_t(4, 300), 2 * x_prueba + g.standard_t(4, 2000)
        q = cuantil_conformal(y_cal - 2 * x_cal, 0.90)
        lo, hi = intervalos_conformales(2 * x_prueba, q)
        coberturas.append(cobertura(y_prueba, lo, hi))
    media = float(np.mean(coberturas))
    assert 0.895 <= media <= 0.92


def test_cuantil_conformal_usa_correccion_de_muestra_finita() -> None:
    r = np.arange(1, 11, dtype=float)  # n = 10: k = ceil(11·0,9) − 1 = 9 → el máximo
    assert cuantil_conformal(r, 0.90) == 10.0
    assert cuantil_conformal(-r, 0.50) == 6.0  # usa |residuo|


def test_calibracion_isotonica_reduce_ece() -> None:
    g = np.random.default_rng(1)
    verdadera = g.uniform(size=6000)
    y = (g.uniform(size=6000) < verdadera).astype(float)
    sesgada = verdadera**3  # subestima sistemáticamente
    cal = CalibradorIsotonico().ajustar(sesgada[:3000], y[:3000])
    antes = M.confiabilidad(y[3000:], sesgada[3000:])["ece"]
    despues = M.confiabilidad(y[3000:], cal.transformar(sesgada[3000:]))["ece"]
    assert despues < antes / 3
    assert cal.transformar(np.array([0.0, 1.0])).tolist() == pytest.approx([1e-4, 1 - 1e-4], abs=0.05)


def test_psi_distingue_estabilidad_y_deriva() -> None:
    g = np.random.default_rng(2)
    ref = g.normal(size=5000)
    assert psi(ref, g.normal(size=5000)) < 0.1
    assert psi(ref, g.normal(loc=1.0, size=5000)) > 0.25
    d = deriva({"a": ref, "b": ref}, {"a": g.normal(size=3000), "b": g.normal(loc=1.0, size=3000)})
    assert not d["a"]["deriva"] and d["b"]["deriva"] and d["b"]["ks_p"] < 1e-6


def test_abstencion() -> None:
    assert decidir_abstencion(habilidad_validacion=0.1, minimo=0.0)["publicar"]
    sin_habilidad = decidir_abstencion(habilidad_validacion=-0.01, minimo=0.0)
    assert sin_habilidad["abstencion"] and len(sin_habilidad["motivos"]) == 1
    assert decidir_abstencion(habilidad_validacion=float("nan"), minimo=0.0)["abstencion"]
    pocos = decidir_abstencion(habilidad_validacion=0.2, minimo=0.0, n_eventos=28, eventos_minimos=30)
    assert pocos["abstencion"] and "28" in pocos["motivos"][0]
    con_deriva = decidir_abstencion(habilidad_validacion=0.2, minimo=0.0, deriva_detectada=True)
    assert con_deriva["publicar"] and con_deriva["advertencias"]  # la deriva advierte, no bloquea
