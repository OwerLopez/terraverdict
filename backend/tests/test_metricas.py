"""Métricas (M8): catálogo explicado, mapas de calor e historial, todo desde expedientes publicados."""

from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.schemas.expedientes import AnioHistorial


def test_catalogo_de_metricas_explica_cada_metrica_en_dos_idiomas(cliente: TestClient) -> None:
    r = cliente.get("/api/v1/metricas")
    assert r.status_code == 200
    c = r.json()
    ids = [m["id"] for m in c["metricas"]]
    assert len(ids) == len(set(ids)), "ids repetidos en config/metricas.yaml"
    # Las métricas que muestran los expedientes y el historial tienen su ficha
    assert {
        "bss_climatologia",
        "habilidad_climatologia",
        "ganancia_informacion_bits",
        "ic90",
        "p_diebold_mariano",
    } <= set(ids)
    assert {"entropia_permutacion", "lyapunov", "p_no_linealidad", "importancia_permutacion"} <= set(ids)
    for m in c["metricas"]:
        assert m["grupo"] in c["grupos"]
        for campo in ("nombre", "que_mide", "como_leer"):
            assert m[campo]["es"].strip() and m[campo]["en"].strip()
        assert m["cita"].strip()


def test_mapas_vacios_sin_expedientes(cliente: TestClient) -> None:
    m = cliente.get("/api/v1/metricas/mapas").json()
    assert m["tareas"] == [] and m["celdas"] == [] and m["importancia"] == []


def test_historial_sin_expediente_devuelve_resultado_nulo(cliente: TestClient) -> None:
    h = cliente.get("/api/v1/historial").json()
    assert h["expediente_id"] is None and h["resultado"] is None and "No son alertas oficiales" in h["aviso"]


def test_mapas_reorganizan_los_expedientes_cientificos_sin_inventar_cifras(app: Any) -> None:
    from app.core.config import RAIZ_REPO
    from app.importacion import importar_expedientes_ciencia

    with app.state.fabrica_sesiones() as sesion:
        importar_expedientes_ciencia(sesion, RAIZ_REPO)
    cliente = TestClient(app)
    m = cliente.get("/api/v1/metricas/mapas").json()
    assert m["tareas"], "el contrato científico trae comparaciones de modelos"
    ids = {t["expediente_id"] for t in m["tareas"]}
    assert all(c["expediente_id"] in ids for c in m["celdas"])
    # Cada celda coincide con el modelo publicado en su expediente
    t0 = m["tareas"][0]
    detalle = cliente.get(f"/api/v1/expedientes/{t0['expediente_id']}").json()["resultado"]
    publicado = {x["nombre"]: x for x in detalle["modelos"]}
    for c in (c for c in m["celdas"] if c["expediente_id"] == t0["expediente_id"]):
        assert c["puntaje_validacion"] == publicado[c["modelo"]]["puntaje_validacion"]
        assert c["puntaje_prueba"] == publicado[c["modelo"]]["puntaje_prueba"]
    assert set(m["variables"]) == {i["variable"] for i in m["importancia"]}
    familias = [x["familia"] for x in m["modelos"]]
    assert familias == sorted(familias, key=["referencia", "clasico", "red_neuronal", "ensamble"].index)


def test_un_anio_del_historial_tiene_metricas_o_motivo_pero_no_ambos() -> None:
    base = {"anio": 2022, "regimen": "fuera_de_muestra", "n": {"prueba": 12}}
    with pytest.raises(ValidationError):
        AnioHistorial.model_validate(base)  # ni métricas ni motivo
    with pytest.raises(ValidationError):
        AnioHistorial.model_validate(
            {**base, "omitido": "pocos datos", "modelos": {"ridge": {"familia": "clasico", "prueba": 0.1}}}
        )
    assert AnioHistorial.model_validate({**base, "omitido": "pocos datos"}).omitido == "pocos datos"
