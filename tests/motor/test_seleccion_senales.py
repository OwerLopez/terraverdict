"""Selección de variables (mRMR) y procesamiento de señales."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from terraverdict.seleccion.variables import mrmr
from terraverdict.senales.procesamiento import (
    climatologia_diaria,
    escalas,
    regimenes,
    spi,
    ventana_adaptativa,
)


def test_mrmr_descarta_ruido_y_redundancia() -> None:
    g = np.random.default_rng(0)
    n = 1500
    a, b, ruido = g.normal(size=n), g.normal(size=n), g.normal(size=n)
    copia_a = a + g.normal(scale=0.05, size=n)
    y = a + 0.7 * b + g.normal(scale=0.3, size=n)
    X = np.column_stack([a, b, ruido, copia_a])
    r = mrmr(X, y, ["a", "b", "ruido", "copia_a"], {}, clasificacion=False)
    assert r["seleccionadas"][:2] == ["a", "b"]
    assert "ruido" not in r["seleccionadas"]
    assert "copia_a" not in r["seleccionadas"]  # redundante con a


def test_mrmr_respeta_prior_y_variables_fijas() -> None:
    g = np.random.default_rng(1)
    n = 1500
    a, b = g.normal(size=n), g.normal(size=n)
    y = a + b + g.normal(scale=0.3, size=n)
    r = mrmr(np.column_stack([a, b]), y, ["a", "b"], {"a": "baja", "b": "alta"}, clasificacion=False, siempre=["a"])
    assert r["seleccionadas"] == ["a", "b"]
    assert r["detalle"][0]["peso_fisico"] == 1.0


def _lluvia_mensual(anios: int, semilla: int) -> pd.Series:
    g = np.random.default_rng(semilla)
    idx = pd.date_range("1981-01-01", periods=12 * anios, freq="MS")
    forma = 1.5 + np.cos(2 * np.pi * idx.month / 12)  # ciclo anual en la forma de la gamma
    valores = g.gamma(forma, 30.0)
    valores[g.uniform(size=len(idx)) < 0.05] = 0.0  # meses secos (probabilidad de cero)
    return pd.Series(valores, index=idx)


def test_spi_normal_estandar_en_entrenamiento() -> None:
    lluvia = _lluvia_mensual(60, 3)
    s = spi(lluvia, 3, "2020-12-31")
    ent = s[s.index <= "2020-12-31"].dropna()
    assert abs(ent.mean()) < 0.1 and abs(ent.std() - 1) < 0.1
    assert stats.shapiro(ent.to_numpy()).pvalue > 0.01


def test_spi_no_usa_datos_posteriores_al_entrenamiento() -> None:
    lluvia = _lluvia_mensual(45, 4)
    alterada = lluvia.copy()
    alterada[alterada.index > "2015-12-31"] *= 5  # el futuro cambia mucho
    a, b = spi(lluvia, 3, "2015-12-31"), spi(alterada, 3, "2015-12-31")
    pd.testing.assert_series_equal(a[a.index <= "2015-12-31"], b[b.index <= "2015-12-31"])
    assert (b[b.index > "2016-03-31"] > a[a.index > "2016-03-31"]).all()


def test_climatologia_armonica_sin_fuga() -> None:
    idx = pd.date_range("2000-01-01", "2010-12-31", freq="D")
    base = 10 + 5 * np.sin(2 * np.pi * idx.dayofyear / 365.25)
    s = pd.Series(base, index=idx)
    alterada = s.copy()
    alterada[alterada.index > "2008-12-31"] += 100
    c1, c2 = climatologia_diaria(s, hasta="2008-12-31"), climatologia_diaria(alterada, hasta="2008-12-31")
    assert np.allclose(c1, c2) and np.allclose(c1, base, atol=0.05)


def test_regimenes_detecta_cambio_de_media() -> None:
    g = np.random.default_rng(5)
    idx = pd.date_range("1980-01-01", periods=480, freq="MS")
    x = np.r_[g.normal(0, 1, 240), g.normal(2, 1, 240)]
    r = regimenes(pd.Series(x, index=idx), tamano_minimo=36)
    assert len(r["puntos_cambio"]) == 1
    assert abs(pd.Timestamp(r["puntos_cambio"][0]) - idx[240]) <= pd.Timedelta(days=31 * 6)
    sin_cambio = regimenes(pd.Series(g.normal(size=480), index=idx), tamano_minimo=36)
    assert sin_cambio["puntos_cambio"] == []


def test_escalas_recupera_periodo_anual() -> None:
    t = np.arange(365 * 20)
    x = np.sin(2 * np.pi * t / 365.25) + np.random.default_rng(6).normal(scale=0.3, size=len(t))
    r = escalas(x, paso_dias=1.0)
    assert r["picos_periodograma"][0]["periodo_dias"] == pytest.approx(365.25, rel=0.02)
    assert sum(e["fraccion_varianza"] for e in r["por_escala"]) <= 1.0


def test_ventana_adaptativa_elige_la_mejor_y_reporta_todas() -> None:
    r = ventana_adaptativa([3, 7, 14], lambda L: -abs(L - 9), {"acf": 9, "nula": 0})
    assert r["elegida"] == 9
    assert set(r["puntuacion_validacion"]) == {3, 7, 9, 14}
