"""De punta a punta: experimentos sobre el recorte real → informe → publicación en el backend.

Corre el orquestador sobre tests/fixtures/raw_reducido (un MLP, una semilla), genera el informe,
convierte los resultados al contrato de expedientes y los publica en una instancia real del backend
(SQLite temporal, catálogos importados del repositorio, clave de servicio `ingesta`).
Comprueba que el backend acepta todo, que publicar dos veces es idempotente y que las capas del
mapa salen de los expedientes publicados. Se omite si el backend no está instalado.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from terraverdict.config import cargar_preregistro, cargar_yaml
from terraverdict.experimentos import ejecutar, informe
from terraverdict.publicar import cliente, convertir

fastapi_testclient = pytest.importorskip("fastapi.testclient")
pytest.importorskip("app.main")

RAIZ = Path(__file__).resolve().parents[2]
RAW = RAIZ / "tests" / "fixtures" / "raw_reducido"
PARTICION = {
    "entrenamiento": ["2008-01-01", "2016-12-31"],
    "validacion": ["2017-01-01", "2018-12-31"],
    "prueba": ["2019-01-01", "2020-12-31"],
}


@pytest.fixture(scope="module")
def resultados(tmp_path_factory: pytest.TempPathFactory) -> Path:
    tmp = tmp_path_factory.mktemp("res")
    c = cargar_yaml(RAIZ / "config" / "fenomenos.yaml")
    c["particion_temporal"] = PARTICION
    (tmp / "fenomenos.yaml").write_text(yaml.safe_dump(c, allow_unicode=True), encoding="utf-8")
    ejecutar.ejecutar(raw=RAW, salida=tmp / "resultados", config=tmp / "fenomenos.yaml", redes=["mlp"], semillas=(0,))
    return tmp / "resultados"


@pytest.fixture(scope="module")
def backend(tmp_path_factory: pytest.TempPathFactory) -> Any:
    from app.core.config import RAIZ_REPO, Settings
    from app.db.base import Base
    from app.domain.vocabulario import Alcance
    from app.importacion import importar_todo
    from app.main import create_app
    from app.schemas.auth import ClaveCrear
    from app.services import usuarios

    tmp = tmp_path_factory.mktemp("db")
    app = create_app(Settings(entorno="pruebas", database_url=f"sqlite:///{tmp / 'p.db'}", raiz_datos=RAIZ_REPO))
    Base.metadata.create_all(app.state.motor)
    with app.state.fabrica_sesiones() as s:
        importar_todo(s, RAIZ_REPO, incluir_ciencia=False)  # este test publica él mismo
        _, clave = usuarios.crear_clave(s, ClaveCrear(nombre="pipeline-integracion", alcances=[Alcance.ingesta]), None)
    yield fastapi_testclient.TestClient(app), clave
    app.state.motor.dispose()


def test_indice_con_todos_los_experimentos(resultados: Path) -> None:
    indice = json.loads((resultados / "indice.json").read_text())
    assert set(indice["experimentos"]) == {
        "volcanes",
        "deslizamientos",
        "sismos",
        "fuentes",
        "sequia",
        "sequia_chirps",
        "lluvia_extrema",
        "lluvia_extrema_chirps",
        "caos",
        "historial",
    }
    # El historial (modo rápido: dos cortes) reevalúa el diseño congelado de los resultados principales
    historial = json.loads((resultados / "historial.json").read_text())
    evaluadas = [t for t in historial["pronostico"].values() if "anios" in t]
    assert evaluadas and all(a["regimen"] in ("validacion_del_diseno", "fuera_de_muestra") for t in evaluadas for a in t["anios"])
    p = json.loads((resultados / "caos.json").read_text())["procedencia"]
    assert p["preregistro_sha256"] == cargar_preregistro(RAIZ / "preregistro.yaml").sha256


def test_informe_solo_con_cifras_de_los_json(resultados: Path) -> None:
    texto = informe.generar(resultados)
    for seccion in (
        "## Resumen",
        "NASA POWER",
        "CHIRPS",
        "## Sismos",
        "## Volcanes",
        "## Dinámica",
        "## Contraste entre fuentes",
        "## Limitaciones",
    ):
        assert seccion in texto
    lluvia = json.loads((resultados / "lluvia_extrema.json").read_text())
    umbral = informe.n(lluvia["zoo"]["modelos"][lluvia["zoo"]["mejor_validacion"]]["puntaje_validacion"])
    assert umbral in texto  # la cifra del informe es la del JSON, con el mismo redondeo


def test_publicacion_idempotente_en_el_backend(resultados: Path, backend: Any) -> None:
    http, clave = backend
    lista = convertir.de_resultados(resultados) + convertir.de_expedientes(RAIZ / "expedientes", 0.10)
    tipos = {e["resultado"]["tipo"] for e in lista}
    assert {"comparacion_modelos", "sismicidad", "recurrencia", "inventario", "caos", "tendencia"} <= tipos

    primera = cliente.publicar(lista, "", clave, s=http)
    errores = [(i["titulo"], i["errores"]) for i in primera if i["estado"] == "error"]
    assert not errores, errores
    assert {i["estado"] for i in primera} == {"creado"}
    segunda = cliente.publicar(lista, "", clave, s=http)
    assert {i["estado"] for i in segunda} == {"ya_existia"}
    assert [i["id"] for i in primera] == [i["id"] for i in segunda]

    sismos = http.get("/api/v1/capas/sismos", params={"magnitud_min": 5}).json()
    assert sismos["expediente_id"] and sismos["features"]
    volcanes = http.get("/api/v1/capas/volcanes").json()
    assert any(f["properties"]["nombre"] == "Misti, El" for f in volcanes["features"])
    assert http.get("/api/v1/capas/deslizamientos").json()["features"]
