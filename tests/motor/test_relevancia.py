"""M1 · Matriz de Relevancia: validación del método con datos sintéticos (docs/modulo-relevancia.md §7, R1)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from terraverdict.experimentos.relevancia import Parametros, bss, relevancia

RAPIDO = Parametros(
    remuestreos=30, nulos=30, gbm=(("learning_rate", 0.1), ("max_depth", 2), ("max_iter", 60), ("min_samples_leaf", 40))
)


def _ar1(n: int, phi: float, rng: np.random.Generator) -> np.ndarray:
    x = np.zeros(n)
    e = rng.normal(size=n)
    for i in range(1, n):
        x[i] = phi * x[i - 1] + e[i]
    return (x - x.mean()) / x.std()


def _datos(semilla: int = 0) -> tuple[pd.DataFrame, pd.Series]:
    rng = np.random.default_rng(semilla)
    idx = pd.date_range("2000-01-01", "2015-12-31", freq="D")
    n = len(idx)
    relevante = _ar1(n, 0.7, rng)
    ruido_a = _ar1(n, 0.9, rng)
    ruido_b = 0.8 * ruido_a + 0.6 * _ar1(n, 0.9, rng)  # falsas, correlacionadas entre sí
    inversa = _ar1(n, 0.5, rng)
    logit = -4.2 + 1.6 * relevante - 1.0 * inversa
    y = rng.random(n) < 1 / (1 + np.exp(-logit))
    X = pd.DataFrame({"relevante": relevante, "inversa": inversa, "ruido_a": ruido_a, "ruido_b": ruido_b}, index=idx)
    return X, pd.Series(y.astype(int), index=idx)


@pytest.fixture(scope="module")
def resultado() -> dict:
    X, y = _datos()
    return relevancia(X, y, list(range(2000, 2013)), [2013, 2014, 2015], RAPIDO)


def test_r1_recupera_las_variables_relevantes_en_el_orden_correcto(resultado: dict) -> None:
    por_id = {v["variable_id"]: v for v in resultado["variables"]}
    assert [v["variable_id"] for v in resultado["variables"][:2]] == ["relevante", "inversa"]
    assert por_id["relevante"]["significativa_fdr"] and por_id["inversa"]["significativa_fdr"]
    assert por_id["relevante"]["estabilidad"] >= 0.8


def test_r1_falsos_descubrimientos_cerca_del_fdr_nominal() -> None:
    """Seis semillas consecutivas (0–5, sin elegir): las relevantes se recuperan siempre y la
    proporción media de falsos descubrimientos queda cerca del FDR nominal (10 %)."""
    rapido = Parametros(remuestreos=3, nulos=20, gbm=RAPIDO.gbm)
    proporciones = []
    for s in range(6):
        X, y = _datos(s)
        r = relevancia(X, y, list(range(2000, 2013)), [2013, 2014, 2015], rapido)
        sig = {v["variable_id"] for v in r["variables"] if v["significativa_fdr"]}
        assert {"relevante", "inversa"} <= sig
        proporciones.append(len(sig - {"relevante", "inversa"}) / len(sig))
    assert float(np.mean(proporciones)) <= 0.2


def test_r3_direccion_coherente_con_el_proceso_generador(resultado: dict) -> None:
    por_id = {v["variable_id"]: v for v in resultado["variables"]}
    assert por_id["relevante"]["direccion"] == "positiva"
    assert por_id["inversa"]["direccion"] == "negativa"


def test_habilidad_en_prueba_positiva_y_publicable(resultado: dict) -> None:
    assert resultado["prueba"]["valor"] > 0
    lo, hi = resultado["prueba"]["ic90"]
    assert lo <= resultado["prueba"]["valor"] <= hi
    assert resultado["publicable"] is (lo > 0)


def test_la_prueba_no_interviene_en_importancias_ni_en_k() -> None:
    """Cambiar el objetivo en los años de prueba no altera nada de lo elegido en el desarrollo."""
    X, y = _datos()
    rapido = Parametros(remuestreos=5, nulos=5, gbm=RAPIDO.gbm)
    a = relevancia(X, y, list(range(2000, 2013)), [2013, 2014, 2015], rapido)
    y2 = y.copy()
    y2[y2.index.year >= 2013] = 1 - y2[y2.index.year >= 2013]
    b = relevancia(X, y2, list(range(2000, 2013)), [2013, 2014, 2015], rapido)
    assert a["variables"] == b["variables"] and a["k"] == b["k"] and a["modelo_elegido"] == b["modelo_elegido"]
    assert a["prueba"]["valor"] != b["prueba"]["valor"]


def test_bss_es_cero_para_la_climatologia() -> None:
    y = np.array([0, 0, 1, 0, 1])
    assert bss(y, np.full(5, y.mean()), y.mean()) == pytest.approx(0.0)
