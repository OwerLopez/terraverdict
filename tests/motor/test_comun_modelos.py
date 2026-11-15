"""Marco de experimentos sin fuga de datos y redes del zoológico."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import torch

from terraverdict.experimentos.comun import Particion, construir, evaluar_zoo
from terraverdict.modelos.entrenamiento import entrenar, fijar_semilla, predecir
from terraverdict.modelos.redes import ARQUITECTURAS, REFERENCIAS

PARTICION = Particion(("2000-01-01", "2009-12-31"), ("2010-01-01", "2011-12-31"), ("2012-01-01", "2013-12-31"))


def _serie_ar(semilla: int = 0) -> tuple[pd.DataFrame, pd.Series]:
    g = np.random.default_rng(semilla)
    idx = pd.date_range("2000-01-01", "2013-12-31", freq="D")
    x = np.zeros(len(idx))
    for i in range(1, len(idx)):
        x[i] = 0.8 * x[i - 1] + g.normal()
    df = pd.DataFrame({"x": x, "z": g.normal(size=len(idx))}, index=idx)
    return df, df["x"].shift(-1)


def test_particiones_disjuntas_y_por_fecha_del_objetivo() -> None:
    df, objetivo = _serie_ar()
    d = construir(df, objetivo, 7, PARTICION, horizonte_fecha=pd.Timedelta(days=1))
    h = pd.Timedelta(days=1)
    assert (d.fechas["entrenamiento"] + h).max() <= pd.Timestamp(PARTICION.entrenamiento[1])
    assert (d.fechas["validacion"] + h).min() >= pd.Timestamp(PARTICION.validacion[0])
    assert (d.fechas["validacion"] + h).max() <= pd.Timestamp(PARTICION.validacion[1])
    assert (d.fechas["prueba"] + h).min() >= pd.Timestamp(PARTICION.prueba[0])
    todas = [set(d.fechas[p]) for p in ("entrenamiento", "validacion", "prueba")]
    assert not (todas[0] & todas[1]) and not (todas[1] & todas[2]) and not (todas[0] & todas[2])


def test_normalizacion_solo_con_entrenamiento() -> None:
    df, objetivo = _serie_ar()
    alterado = df.copy()
    alterado.loc[alterado.index > PARTICION.entrenamiento[1], "x"] += 50.0
    a = construir(df, objetivo, 7, PARTICION)
    b = construir(alterado, objetivo, 7, PARTICION)
    assert a.normalizacion == b.normalizacion
    np.testing.assert_array_equal(a.X["entrenamiento"], b.X["entrenamiento"])


def test_ventana_termina_en_t_y_objetivo_es_t_mas_1() -> None:
    df, objetivo = _serie_ar()
    d = construir(df, objetivo, 5, PARTICION)
    t = d.fechas["validacion"][10]
    media, desv = d.normalizacion["x"]
    esperado = ((df.loc[t - pd.Timedelta(days=4) : t, "x"] - media) / desv).to_numpy(np.float32)
    np.testing.assert_allclose(d.X["validacion"][10][:, 0], esperado, rtol=1e-5)
    assert d.y["validacion"][10] == pytest.approx(df["x"].loc[t + pd.Timedelta(days=1)])


def test_zoologico_no_mira_la_prueba() -> None:
    """Cambiar el objetivo de prueba no cambia nada de lo que se decide con validación."""
    df, objetivo = _serie_ar(1)
    d = construir(df, objetivo, 7, PARTICION)

    def refs(dd) -> dict:
        return {p: {"climatologia": np.zeros(len(dd.y[p]))} for p in ("validacion", "prueba")}

    a = evaluar_zoo(d, "regresion", refs(d), redes=["mlp"], semillas=(0,), epocas=5, registro=lambda _: None)
    d.y["prueba"] = d.y["prueba"] * -3 + 7
    b = evaluar_zoo(d, "regresion", refs(d), redes=["mlp"], semillas=(0,), epocas=5, registro=lambda _: None)
    for k in a["modelos"]:
        assert a["modelos"][k]["puntaje_validacion"] == pytest.approx(b["modelos"][k]["puntaje_validacion"])
        assert a["modelos"][k]["q_conformal_90"] == b["modelos"][k]["q_conformal_90"]
    assert a["ranking_validacion"] == b["ranking_validacion"]
    assert a["modelos"]["ridge"]["prueba"]["habilidad_climatologia"] > 0.5  # AR(1) φ = 0,8: R² ≈ 0,64


@pytest.mark.parametrize("nombre", sorted(ARQUITECTURAS))
def test_cada_red_forma_de_salida_y_referencia(nombre: str) -> None:
    torch.manual_seed(0)
    modelo = ARQUITECTURAS[nombre](14, 3, 1)
    salida = modelo(torch.randn(5, 14, 3))
    assert salida.shape == (5, 1) and torch.isfinite(salida).all()
    assert REFERENCIAS[nombre]


def test_entrenamiento_reproducible_y_aprende() -> None:
    g = np.random.default_rng(0)
    X = g.normal(size=(600, 8, 2)).astype(np.float32)
    y = X[:, -1, 0] * 2 + 0.1 * g.normal(size=600)
    resultados = []
    for _ in range(2):
        fijar_semilla(3)  # antes de crear la red: la inicialización también depende de la semilla
        m, h = entrenar(ARQUITECTURAS["mlp"](8, 2, 1), X[:500], y[:500], X[500:], y[500:], epocas=40, semilla=3)
        resultados.append(predecir(m, X[500:]))
    np.testing.assert_array_equal(resultados[0], resultados[1])
    assert np.mean((resultados[0] - y[500:]) ** 2) < 0.2 * np.var(y[500:])
    assert h.mejor_epoca <= len(h.perdida_validacion) - 1
