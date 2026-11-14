"""Validación de los estimadores de caos con sistemas de propiedades conocidas.

Estos sistemas son sintéticos y SOLO validan los métodos; no son datos de Arequipa.
Tolerancias fijadas a partir de los valores de referencia de la literatura.
"""

from __future__ import annotations

import numpy as np
import pytest

from terraverdict.caos import sistemas as S
from terraverdict.caos.diagnostico import diagnosticar
from terraverdict.caos.embedding import (
    dimension_embedding,
    falsos_vecinos,
    periodo_medio,
    retardo_optimo,
)
from terraverdict.caos.invariantes import (
    dimension_correlacion,
    entropia_muestral,
    entropia_permutacion,
    lyapunov_rosenstein,
    prueba_01,
)
from terraverdict.caos.recurrencia import rqa
from terraverdict.caos.surrogates import iaaft


def test_lyapunov_logistico_recupera_ln2() -> None:
    x = S.logistico(3000)
    assert lyapunov_rosenstein(x, 2, 1, 1, k_max=15)["lambda"] == pytest.approx(np.log(2), abs=0.05)


def test_henon_dimension_y_lyapunov() -> None:
    x = S.henon(3000)
    d2 = dimension_correlacion(x, 1, list(range(1, 9)), theiler=2)
    assert d2["satura"] and d2["d2_saturado"] == pytest.approx(1.21, abs=0.12)
    assert lyapunov_rosenstein(x, 2, 1, 2, k_max=15)["lambda"] == pytest.approx(0.42, abs=0.05)


def test_lorenz_embedding_dimension_y_lyapunov() -> None:
    x, dt = S.lorenz(4000)
    ret = retardo_optimo(x)
    m = dimension_embedding(falsos_vecinos(x, ret["tau"], 8))
    assert m == 3  # el atractor de Lorenz necesita m = 3
    th = round(periodo_medio(x))
    d2 = dimension_correlacion(x, ret["tau"], list(range(1, 10)), theiler=th)
    assert d2["satura"] and d2["d2_saturado"] == pytest.approx(2.05, abs=0.25)
    assert lyapunov_rosenstein(x, 3, ret["tau"], th, k_max=120, dt=dt)["lambda"] == pytest.approx(0.906, abs=0.15)


def test_ruido_no_satura_y_mapas_usan_tau_1() -> None:
    ruido = np.random.default_rng(5).standard_normal(2000)
    assert not dimension_correlacion(ruido, 1, list(range(1, 11)), theiler=1)["satura"]
    assert retardo_optimo(S.logistico(2000))["tau"] == 1
    assert retardo_optimo(S.henon(2000))["tau"] == 1


def test_prueba_01_separa_regular_de_caotico() -> None:
    assert prueba_01(S.seno(3000))["K"] < 0.1
    assert prueba_01(S.logistico(3000, r=3.97))["K"] > 0.9


def test_entropias_ordenan_aleatoriedad() -> None:
    ruido = np.random.default_rng(2).standard_normal(3000)
    assert entropia_permutacion(ruido) > 0.98
    assert entropia_permutacion(S.logistico(3000)) < 0.8
    assert entropia_muestral(S.seno(2000)) < entropia_muestral(ruido)


def test_iaaft_conserva_distribucion_y_espectro() -> None:
    rng = np.random.default_rng(7)
    x = S.ar1(2048, 0.8, rng) ** 3
    s = iaaft(x, rng)
    assert np.allclose(np.sort(s), np.sort(x))
    ex, es = np.abs(np.fft.rfft(x)), np.abs(np.fft.rfft(s))
    assert np.corrcoef(ex, es)[0, 1] > 0.95


def test_rqa_determinismo_mayor_en_sistema_determinista() -> None:
    from terraverdict.caos.embedding import embeber

    det_logistico = rqa(embeber(S.logistico(1200), 2, 1))["determinismo"]
    det_ruido = rqa(embeber(np.random.default_rng(1).standard_normal(1200), 2, 1))["determinismo"]
    assert det_logistico > det_ruido + 0.2


@pytest.mark.parametrize(
    ("nombre", "serie", "esperado"),
    [
        ("henon", lambda: S.henon(1500), "compatible_con_caos_baja_dimension"),
        ("lorenz", lambda: S.lorenz(2500)[0], "compatible_con_caos_baja_dimension"),
        ("ar1", lambda: S.ar1(1500, 0.7, np.random.default_rng(11)), "lineal_estocastica"),
        ("ar1_transformado", lambda: S.ar1(1500, 0.6, np.random.default_rng(12)) ** 3, "lineal_estocastica"),
        ("seno", lambda: S.seno(1500), "regular"),
    ],
)
def test_diagnostico_integrado(nombre: str, serie, esperado: str) -> None:
    r = diagnosticar(serie(), nombre=nombre, n_sustitutos=39, n_sustitutos_costosos=19)
    assert r["veredicto"] == esperado, (
        r["veredicto"],
        r["condiciones_caos"],
        r["no_linealidad"]["asimetria_temporal"]["p"],
        r["no_linealidad"]["error_prediccion_analogos"]["p"],
    )


def test_diagnostico_se_abstiene_con_pocos_datos() -> None:
    r = diagnosticar(np.random.default_rng(0).standard_normal(200), nombre="corta")
    assert r["veredicto"] == "insuficiente"
