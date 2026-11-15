"""Escala nacional sobre un recorte REAL (POWER de Arequipa, Lima y Callao; USGS 2013–2022), sin red."""

from __future__ import annotations

from pathlib import Path

import pytest

from terraverdict.experimentos import nacional
from terraverdict.publicar import convertir

RAW = Path(__file__).resolve().parents[1] / "fixtures" / "raw_nacional"


@pytest.fixture(scope="module")
def resultado() -> dict:
    r = nacional.ejecutar(RAW, registro=lambda _: None, config=RAW / "nacional.yaml", descargar_faltantes=False)
    r["procedencia"] = {
        "commit": None,
        "generado_utc": "2026-11-15T00:00:00+00:00",
        "config_sha256": "0" * 64,
        "preregistro_sha256": "0" * 64,
        "crudos": {},
    }
    return r


def test_tres_departamentos_y_celda_compartida(resultado: dict) -> None:
    deps = {d["id"]: d for d in resultado["departamentos"]}
    assert set(deps) == {"arequipa", "lima", "callao"}
    assert deps["lima"]["comparte_celda_con"] == "callao"  # misma celda POWER: no se duplica el clima
    assert deps["lima"]["temperatura_media_c"] == deps["callao"]["temperatura_media_c"]
    # el resumen de veredictos cuenta celdas distintas, no departamentos
    assert sum(resultado["resumen_veredictos"]["temperatura"].values()) == 2


def test_sello_nunca_es_robusta_con_una_sola_familia(resultado: dict) -> None:
    for d in resultado["departamentos"]:
        for var in ("tendencia_temperatura", "tendencia_lluvia"):
            t = d[var]
            assert t["veredicto"] != "robusta"
            assert t["ic90_por_decada"][0] <= t["sen_por_decada"] <= t["ic90_por_decada"][1]


def test_spi_marcado_no_fiable_en_clima_arido(resultado: dict) -> None:
    deps = {d["id"]: d for d in resultado["departamentos"]}
    assert deps["callao"]["lluvia_anual_media_mm"] < nacional.UMBRAL_SPI_MM
    assert deps["callao"]["spi"]["confiable"] is False


def test_sismicidad_nacional_real(resultado: dict) -> None:
    s = resultado["sismicidad"]
    assert s["eventos"] > 500 and s["mc"] >= 4.5
    assert 0.6 < s["valor_b"]["b"] < 1.5
    assert all(c["n"] >= 1 for c in s["grilla"])


def test_cumple_el_contrato_del_backend(resultado: dict) -> None:
    pytest.importorskip("app.schemas.expedientes")
    from app.schemas.expedientes import ExpedienteCrear

    (exp,) = convertir.de_nacional(resultado)
    validado = ExpedienteCrear.model_validate(exp)
    assert validado.resultado.tipo == "panorama_nacional"
    assert validado.dominio_id == "peru_nacional"
    assert "config/nacional.yaml" in validado.procedencia.hash_entradas
