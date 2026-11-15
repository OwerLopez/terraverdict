"""Cadena de custodia: un crudo o un resultado alterado se detecta y detiene el pipeline."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from terraverdict.ingest.manifest import guardar_crudo
from terraverdict.integridad import (
    IntegridadComprometida,
    exigir_crudos_integros,
    exigir_resultado_integro,
    sellar_resultados,
    verificar_crudos,
    verificar_resultados,
)


def test_crudo_alterado_detiene_el_entrenamiento(tmp_path: Path) -> None:
    guardar_crudo(tmp_path / "fuente", "datos.csv", b"a,b\n1,2\n", url="https://ejemplo", producto="PRUEBA")
    assert exigir_crudos_integros(tmp_path)["verificados"] == 1
    (tmp_path / "fuente" / "datos.csv").write_bytes(b"a,b\n1,999\n")
    with pytest.raises(IntegridadComprometida):
        exigir_crudos_integros(tmp_path)


def test_faltante_y_sin_manifiesto_se_informan_sin_ser_fatales(tmp_path: Path) -> None:
    guardar_crudo(tmp_path / "fuente", "a.csv", b"1", url="u", producto="P")
    (tmp_path / "fuente" / "a.csv").unlink()
    (tmp_path / "fuente" / "intruso.csv").write_bytes(b"x")
    informe = verificar_crudos(tmp_path)
    assert (
        informe["ok"]
        and informe["faltantes"] == ["fuente/a.csv"]
        and informe["sin_manifiesto"] == ["fuente/intruso.csv"]
    )


def test_resultado_alterado_no_se_publica(tmp_path: Path) -> None:
    (tmp_path / "sismos.json").write_text(json.dumps({"b": 1.0}))
    (tmp_path / "indice.json").write_text(json.dumps({"sellos_sha256": sellar_resultados(tmp_path)}))
    exigir_resultado_integro(tmp_path / "sismos.json")
    assert verificar_resultados(tmp_path)["ok"]
    (tmp_path / "sismos.json").write_text(json.dumps({"b": 0.5}))
    assert not verificar_resultados(tmp_path)["ok"]
    with pytest.raises(IntegridadComprometida):
        exigir_resultado_integro(tmp_path / "sismos.json")


def test_fixtures_reales_coinciden_con_sus_manifiestos(tmp_path: Path) -> None:
    raw = Path(__file__).resolve().parents[1] / "fixtures" / "raw_nacional"
    if not any(raw.glob("*/manifiesto.json")):
        pytest.skip("el recorte nacional no trae manifiestos")
    destino = tmp_path / "raw"
    shutil.copytree(raw, destino)
    assert verificar_crudos(destino)["ok"]
