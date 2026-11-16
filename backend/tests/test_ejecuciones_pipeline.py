"""Ejecuciones reales del pipeline importadas como procesos (contrato `ejecuciones.json`).

La estructura de abajo es solo para probar el contrato del importador; los datos reales los escribe
`tv publicar --exportar` desde `data/raw/registro_descarga.json` y `resultados/indice.json`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import Proceso
from app.importacion import importar_ejecuciones

EJECUCIONES = [
    {
        "clave": "ingesta:usgs",
        "tipo": "ingesta",
        "estado": "completado",
        "parametros": {"fuente_id": "usgs_comcat", "paso": "usgs"},
        "trabajador": "tv ingest-fenomenos",
        "finalizado_utc": "2026-11-15T23:24:00+00:00",
        "error": None,
        "eventos": [{"nivel": "info", "mensaje": "Descargado usgs_1973.csv (10 bytes)", "datos": {"sha256": "ab"}}],
    },
    {
        "clave": "ingesta:modis_lst_ciudad",
        "tipo": "ingesta",
        "estado": "fallido",
        "parametros": {"fuente_id": "modis_lst_ornl", "paso": "modis_lst_ciudad"},
        "trabajador": "tv ingest-fenomenos",
        "finalizado_utc": "2026-11-15T23:30:00+00:00",
        "error": {"mensaje": "HTTP 502"},
        "eventos": [],
    },
    {
        "clave": "experimento:relevancia:2026-11-16T00:10:00+00:00",
        "tipo": "relevancia",
        "estado": "completado",
        "parametros": {"problema_id": "P1", "experimento": "relevancia", "commit": "abc"},
        "trabajador": "tv experimentos",
        "finalizado_utc": "2026-11-16T00:10:00+00:00",
        "segundos": 42.0,
        "script": "tv experimentos (relevancia)",
        "error": None,
        "eventos": [{"nivel": "info", "mensaje": "Corrida completa", "datos": {"commit": "abc"}}],
    },
]


def _raiz(tmp_path: Path, lista: list[dict[str, Any]]) -> Path:
    (tmp_path / "resultados" / "contrato").mkdir(parents=True)
    (tmp_path / "resultados" / "contrato" / "ejecuciones.json").write_text(json.dumps(lista), encoding="utf-8")
    return tmp_path


def test_importa_ejecuciones_terminadas_con_eventos_e_idempotente(app: Any, tmp_path: Path) -> None:
    raiz = _raiz(tmp_path, EJECUCIONES)
    with app.state.fabrica_sesiones() as s:
        assert importar_ejecuciones(s, raiz) == {"leidas": 3, "nuevas": 3, "fuentes_integradas": 1}
        assert importar_ejecuciones(s, raiz) == {"leidas": 3, "nuevas": 0, "fuentes_integradas": 1}
        procesos = {p.tipo + ":" + p.estado: p for p in s.scalars(select(Proceso))}
        rel = procesos["relevancia:completado"]
        assert rel.progreso == 1.0 and rel.solicitado_por == "pipeline"
        assert (rel.finalizado_en - rel.iniciado_en).total_seconds() == pytest.approx(42.0)
        assert procesos["ingesta:fallido"].error == {"mensaje": "HTTP 502"}
        assert procesos["ingesta:completado"].eventos[0].datos == {"sha256": "ab"}


def test_rechaza_ejecuciones_sin_terminar_o_sin_parametros(app: Any, tmp_path: Path) -> None:
    pendiente = [{**EJECUCIONES[0], "estado": "en_curso"}]
    with app.state.fabrica_sesiones() as s, pytest.raises(ValueError, match="terminada"):
        importar_ejecuciones(s, _raiz(tmp_path / "a", pendiente))
    sin_parametro = [{**EJECUCIONES[2], "parametros": {"experimento": "relevancia"}}]
    with app.state.fabrica_sesiones() as s, pytest.raises(ValueError, match="problema_id"):
        importar_ejecuciones(s, _raiz(tmp_path / "b", sin_parametro))


def test_la_api_lista_las_ejecuciones(app: Any, cliente: TestClient, tmp_path: Path) -> None:
    with app.state.fabrica_sesiones() as s:
        importar_ejecuciones(s, _raiz(tmp_path, EJECUCIONES))
    r = cliente.get("/api/v1/procesos").json()
    assert r["total"] == 3
    assert {p["estado"] for p in r["items"]} == {"completado", "fallido"}


def test_solo_una_descarga_completada_con_sha256_integra_una_fuente(app: Any, tmp_path: Path) -> None:
    from app.db.models import Fuente

    with app.state.fabrica_sesiones() as s:
        antes_modis = s.get(Fuente, "modis_lst_ornl").estado_verificacion
        r = importar_ejecuciones(s, _raiz(tmp_path, EJECUCIONES))
        assert r["fuentes_integradas"] == 1
        usgs = s.get(Fuente, "usgs_comcat")
        assert usgs.estado_verificacion == "integrado"
        assert usgs.evidencia["integracion"]["archivos"] == 1
        assert usgs.evidencia["integracion"]["ejemplo"]["sha256"] == "ab"
        # La descarga de MODIS falló: su estado no cambia.
        assert s.get(Fuente, "modis_lst_ornl").estado_verificacion == antes_modis
