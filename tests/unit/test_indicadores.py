"""Indicadores de la portada: ENSO, SPI-3 actual, sequía según ENSO y gradiente altitudinal."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from terraverdict.publicar import indicadores as I


def _oni(tmp_path, valores: list[tuple[str, int, float]]):
    texto = "SEAS YR TOTAL ANOM\n" + "\n".join(f"{s} {a} 27.0 {v}" for s, a, v in valores) + "\n"
    f = tmp_path / "oni.ascii.txt"
    f.write_text(texto, encoding="utf-8")
    return I.oni_trimestral(f)


def test_episodio_el_nino_exige_cinco_trimestres(tmp_path):
    base = [("DJF", 2026, -0.4), ("JFM", 2026, -0.2), ("FMA", 2026, 0.1), ("MAM", 2026, 0.46)]
    seguidos = [("AMJ", 2026, 0.95), ("MJJ", 2026, 1.39), ("JJA", 2026, 1.8), ("JAS", 2026, 2.16)]
    cuatro = I.enso(_oni(tmp_path, base + seguidos), None)["oni"]
    assert cuatro["trimestres_consecutivos_nino"] == 4
    assert cuatro["episodio_noaa"] == "sin_episodio"
    cinco = I.enso(_oni(tmp_path, base + seguidos + [("ASO", 2026, 2.46)]), None)["oni"]
    assert cinco["trimestres_consecutivos_nino"] == 5
    assert cinco["episodio_noaa"] == "el_nino"
    assert cinco["intensidad"] == "nino_fuerte"


def test_nino_mensual_lee_columnas_de_sstoi(tmp_path):
    f = tmp_path / "sstoi.indices"
    f.write_text(
        "YR MON  NINO1+2   ANOM   NINO3    ANOM   NINO4    ANOM NINO3.4    ANOM\n"
        "2026  10   26.12    5.25   29.24    4.16   29.88    1.20   30.01    3.25\n",
        encoding="utf-8",
    )
    (fila,) = I.nino_mensual(f)
    assert fila == {"anio": 2026, "mes": 10, "nino12_anom": 5.25, "nino34_anom": 3.25}


def test_mensual_completo_descarta_meses_incompletos():
    dias = pd.date_range("2020-01-01", "2020-03-15", freq="D")
    s = pd.Series(1.0, index=dias)
    s[pd.Timestamp("2020-02-10")] = np.nan
    m = I.mensual_completo(s)
    assert list(m.index.strftime("%Y-%m")) == ["2020-01"]  # febrero tiene un hueco y marzo está incompleto
    assert m.iloc[0] == 31.0


def test_spi3_marca_no_confiable_la_estacion_seca():
    rng = np.random.default_rng(0)
    meses = pd.date_range("1981-01-01", "2026-10-01", freq="MS")
    # Lluvia estacional: abundante dic–mar, casi nula jun–sep.
    medias = {1: 60, 2: 70, 3: 50, 4: 15, 5: 4, 6: 0.5, 7: 0.5, 8: 0.5, 9: 1, 10: 5, 11: 10, 12: 35}
    lluvia = pd.Series([rng.gamma(2.0, medias[f.month] / 2.0) for f in meses], index=meses)
    r = I.spi3_actual(lluvia)
    por_mes = {f["mes"][-2:]: f["confiable"] for f in r["serie"]}
    assert por_mes["08"] is False and por_mes["02"] is True
    assert r["ultimo_confiable"]["confiable"] is True


def test_wilson_contiene_la_proporcion_y_es_valido():
    lo, hi = I.wilson(2, 5)
    assert 0 <= lo < 0.4 < hi <= 1
    assert I.wilson(0, 0) == (0.0, 1.0)


def test_sequia_por_enso_cuenta_por_categoria():
    meses = pd.date_range("1981-01-01", "2020-12-01", freq="MS")
    rng = np.random.default_rng(1)
    lluvia = pd.Series(rng.gamma(2.0, 20.0, len(meses)), index=meses)
    oni = [{"trimestre": "DJF", "anio": a, "valor": (2.0 if a % 7 == 0 else 0.0)} for a in range(1981, 2021)]
    r = I.sequia_por_enso(lluvia, oni)
    total = sum(c["n"] for c in r["categorias"])
    assert total == len(r["temporadas"])
    assert all(c["ic90"][0] <= (c["frecuencia"] or 0) <= c["ic90"][1] for c in r["categorias"] if c["n"])
    assert 0 <= r["fisher_nino_vs_resto"]["p_unilateral"] <= 1


def test_altitud_gradiente_y_referencia():
    r = I.altitud(
        {"estacion": "X", "nombre": "AREQUIPA", "elevacion_m": 2520.0, "temperatura_media_c": 14.9, "cobertura": 0.95},
        {"lon": 0, "lat": 0, "elevacion_celda_m": 4232.5, "temperatura_media_c": 5.88},
        {"lon": 0, "lat": 0, "elevacion_celda_m": 3330.3, "temperatura_media_c": 10.88},
    )
    assert r["diferencia_c"] == pytest.approx(9.02)
    assert r["gradiente_observado_c_km"] == pytest.approx(9.02 / 1.7125, abs=0.01)
    assert r["esperado_con_referencia_c"] == pytest.approx(6.5 * 1.7125, abs=0.01)


def test_power_media_lee_elevacion_de_la_celda(tmp_path):
    f = tmp_path / "power.json"
    datos = {d.strftime("%Y%m%d"): 10.0 for d in pd.date_range("1991-01-01", "2020-12-31")}
    f.write_text(json.dumps({"geometry": {"coordinates": [-71.25, -15.95, 4232.48]}, "properties": {"parameter": {"T2M": datos}}}), encoding="utf-8")
    r = I.power_media(f)
    assert r["elevacion_celda_m"] == 4232.5 and r["temperatura_media_c"] == 10.0


def test_fin_de_entrenamiento_coincide_con_la_particion_congelada():
    from terraverdict.config import cargar_yaml

    particion = cargar_yaml("config/fenomenos.yaml")["particion_temporal"]
    assert str(particion["entrenamiento"][1]) == I.FIN_ENTRENAMIENTO
