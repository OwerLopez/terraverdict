"""Historial de métricas: cortes sin fuga, regímenes honestos y dinámica en ventanas que distingue caos de ruido."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from terraverdict.caos.sistemas import logistico
from terraverdict.experimentos.comun import Tarea
from terraverdict.experimentos.historial import caos_ventanas, cortes, orden_permutacion, origen_movil


def test_cortes_sin_solapamiento_ni_fuga() -> None:
    lista = cortes(2016, 2025)
    assert [int(p.prueba[0][:4]) for p in lista] == list(range(2016, 2026))
    for p in lista:
        fin_ent = pd.Timestamp(p.entrenamiento[1])
        ini_val, fin_val = pd.Timestamp(p.validacion[0]), pd.Timestamp(p.validacion[1])
        ini_pru = pd.Timestamp(p.prueba[0])
        assert fin_ent < ini_val <= fin_val < ini_pru  # entrenamiento < validación < prueba
        assert ini_pru.year - fin_ent.year == 2  # Y−2 / Y−1 / Y


@pytest.mark.parametrize(("n", "orden"), [(100, 3), (300, 4), (1000, 5), (5000, 6)])
def test_orden_permutacion_respeta_n_mayor_que_5_factorial(n: int, orden: int) -> None:
    assert orden_permutacion(n) == orden


def _tarea_ar1(registro_hasta: list[str]) -> Tarea:
    rng = np.random.default_rng(3)
    fechas = pd.date_range("1990-01-01", "2024-12-01", freq="MS")
    x = np.zeros(len(fechas))
    for i in range(1, len(x)):
        x[i] = 0.8 * x[i - 1] + rng.normal()
    serie = pd.Series(x, index=fechas)
    X = pd.DataFrame({"x": serie})

    def referencias(hasta: str):
        registro_hasta.append(hasta)
        media = float(serie[serie.index <= pd.Timestamp(hasta)].mean())

        def construir(d):
            return {
                p: {"climatologia": np.full(len(d.y[p]), media), "persistencia": serie.reindex(d.fechas[p]).to_numpy()}
                for p in ("validacion", "prueba")
            }

        return construir

    return Tarea(
        nombre="ar1_sintetica",
        tipo="regresion",
        X=X,
        objetivo=serie.shift(-1),
        horizonte=pd.DateOffset(months=1),
        referencias=referencias,
        epocas=5,
        bloque_bootstrap=3,
    )


def test_origen_movil_regimenes_referencias_y_agregado() -> None:
    hastas: list[str] = []
    t = _tarea_ar1(hastas)
    r = origen_movil(t, ["x"], 6, "mlp", 2019, 2023, frontera_diseno=2020, registro=lambda _: None)
    anios = {a["anio"]: a for a in r["anios"]}
    assert set(anios) == {2019, 2020, 2021, 2022, 2023}
    assert {y for y, a in anios.items() if a["regimen"] == "validacion_del_diseno"} == {2019, 2020}
    # Las referencias se ajustan solo con datos hasta Y−2: nunca ven la validación ni la prueba del corte
    assert hastas == [f"{y - 2}-12-31" for y in range(2019, 2024)]
    for a in anios.values():
        assert a["n"]["prueba"] == 12 and set(a["modelos"]) >= {"ref_climatologia", "ridge", "mlp"}
    # Un AR(1) con φ = 0,8 es predecible: el clásico lineal supera a la climatología en el agregado
    fuera = r["agregado"]["fuera_de_muestra"]
    assert fuera["ridge"]["valor"] > 0.3 and fuera["ridge"]["anios"] == 3
    assert fuera["ref_climatologia"]["valor"] == pytest.approx(0.0, abs=1e-12)


def test_origen_movil_omite_anios_sin_datos_suficientes() -> None:
    t = _tarea_ar1([])
    r = origen_movil(t, ["x"], 6, "mlp", 2024, 2025, frontera_diseno=2020, registro=lambda _: None)
    anios = {a["anio"]: a for a in r["anios"]}
    assert "omitido" not in anios[2024]
    assert anios[2025]["omitido"]  # no hay objetivo observado en 2025
    assert not anios[2025].get("modelos")


@pytest.mark.slow
def test_caos_en_ventanas_distingue_mapa_logistico_de_ruido() -> None:
    rng = np.random.default_rng(0)
    fechas = pd.date_range("2000-01-01", periods=1460, freq="D")
    caotica = pd.Series(logistico(1460), index=fechas)
    ruido = pd.Series(rng.normal(size=1460), index=fechas)
    vc = caos_ventanas(caotica, 2, 1, 39, np.random.default_rng(1))
    vr = caos_ventanas(ruido, 2, 1, 39, np.random.default_rng(1))
    assert [f["fin"] for f in vc] == [2001, 2002, 2003]
    for c, r in zip(vc, vr, strict=True):
        assert c["entropia_permutacion"] < r["entropia_permutacion"]  # el caos determinista tiene orden ordinal
        assert c["p_no_linealidad"] <= 0.05 < r["p_no_linealidad"]  # y se distingue de su sustituto lineal
        assert c["lyapunov"] > 0
