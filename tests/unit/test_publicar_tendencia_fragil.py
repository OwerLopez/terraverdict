"""Regresión del 422 "'fragil' exige al menos una prueba fallida": el contrato debe nombrar la prueba fallida."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

from terraverdict.publicar.convertir import de_tendencia

RAIZ = Path(__file__).resolve().parents[2]
EXPEDIENTE = RAIZ / "expedientes" / "TV-CHILI_REGULADO-LLUVIA_DIC_MAR-001.json"


def _base() -> dict:
    return json.loads(EXPEDIENTE.read_text(encoding="utf-8"))


@pytest.mark.parametrize("prueba", ["palanca", "ventanas", "enso", "sensor", "independencia"])
def test_fragil_marca_la_prueba_fallida_en_el_sello(prueba: str) -> None:
    e = _base()
    sello = e["resultado"]["sello"]
    sello.update(codigo="fragil", fallan=[prueba], pendientes=[])
    if prueba == "palanca":
        e["resultado"].setdefault("palanca", {})["evaluada"] = True
    e["resultado"]["mk"]["p_conservador"] = 0.01  # significativa: el único camino a 'fragil'
    r = de_tendencia(e, alfa=0.1)["resultado"]
    assert r["veredicto"] == "fragil"
    assert r["sello"][prueba]["estado"] == "fallida"


def test_palanca_fallida_aparece_aunque_falte_la_marca_de_evaluada() -> None:
    e = _base()
    e["resultado"]["sello"].update(codigo="fragil", fallan=["palanca"], pendientes=[])
    e["resultado"]["palanca"] = {}
    e["resultado"]["mk"]["p_conservador"] = 0.01
    r = de_tendencia(e, alfa=0.1)["resultado"]
    assert r["sello"]["palanca"]["estado"] == "fallida"


def test_prueba_desconocida_falla_al_convertir_y_no_en_la_api() -> None:
    e = copy.deepcopy(_base())
    e["resultado"]["sello"].update(fallan=["prueba_inventada"], pendientes=[])
    with pytest.raises(ValueError, match="prueba_inventada"):
        de_tendencia(e, alfa=0.1)


def test_el_contrato_valida_en_el_backend() -> None:
    """El expediente convertido pasa el validador del backend (sin 422)."""
    sys.path.insert(0, str(RAIZ / "backend"))
    try:
        from app.schemas.expedientes import ExpedienteCrear
    except ModuleNotFoundError:  # entorno sin el backend instalado
        pytest.skip("backend no disponible en este entorno")
    e = _base()
    ExpedienteCrear.model_validate(de_tendencia(e, alfa=0.1))
