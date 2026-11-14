"""Fixtures: cada prueba usa una base SQLite nueva con los datos reales del repositorio."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import RAIZ_REPO, Settings
from app.db.base import Base
from app.domain.vocabulario import Alcance, Rol
from app.importacion import importar_todo
from app.main import create_app
from app.schemas.auth import ClaveCrear, UsuarioCrear
from app.services import usuarios

CONTRASENA = "contrasena-de-prueba-segura"


@pytest.fixture()
def app(tmp_path: Path) -> Any:
    settings = Settings(
        entorno="pruebas",
        database_url=f"sqlite:///{tmp_path / 'prueba.db'}",
        raiz_datos=RAIZ_REPO,
        login_intentos_por_minuto=5,
        log_nivel="WARNING",
    )
    aplicacion = create_app(settings)
    Base.metadata.create_all(aplicacion.state.motor)
    with aplicacion.state.fabrica_sesiones() as sesion:
        importar_todo(sesion, RAIZ_REPO)
        for email, rol in (
            ("admin@tv.pe", Rol.admin),
            ("analista@tv.pe", Rol.analista),
            ("lector@tv.pe", Rol.lector),
        ):
            usuarios.crear_usuario(
                sesion, UsuarioCrear(email=email, nombre=email.split("@")[0], contrasena=CONTRASENA, rol=rol)
            )
    yield aplicacion
    aplicacion.state.motor.dispose()


@pytest.fixture()
def sesion(app: Any) -> Iterator[Session]:
    with app.state.fabrica_sesiones() as s:
        yield s


@pytest.fixture()
def cliente(app: Any) -> TestClient:
    return TestClient(app)


def token(cliente: TestClient, email: str) -> dict[str, str]:
    r = cliente.post("/api/v1/auth/token", data={"username": email, "password": CONTRASENA})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def admin(cliente: TestClient) -> dict[str, str]:
    return token(cliente, "admin@tv.pe")


@pytest.fixture()
def analista(cliente: TestClient) -> dict[str, str]:
    return token(cliente, "analista@tv.pe")


@pytest.fixture()
def lector(cliente: TestClient) -> dict[str, str]:
    return token(cliente, "lector@tv.pe")


def _clave(sesion: Session, nombre: str, *alcances: Alcance) -> dict[str, str]:
    _, clave = usuarios.crear_clave(sesion, ClaveCrear(nombre=nombre, alcances=list(alcances)), None)
    return {"X-API-Key": clave}


@pytest.fixture()
def ingesta(sesion: Session) -> dict[str, str]:
    return _clave(sesion, "pipeline-pruebas", Alcance.ingesta)


@pytest.fixture()
def trabajador(sesion: Session) -> dict[str, str]:
    return _clave(sesion, "trabajador-a", Alcance.trabajador)


@pytest.fixture()
def otro_trabajador(sesion: Session) -> dict[str, str]:
    return _clave(sesion, "trabajador-b", Alcance.trabajador)


PROCEDENCIA = {
    "fuentes": [{"fuente_id": "imerg_final_mensual", "coleccion": "GPM_3IMERGM", "version": "07"}],
    "codigo": {"repositorio": "DiegoNiS/terraverdict", "commit": "abc1234"},
    "pasos": [
        {"id": "descarga", "nombre": "Descarga"},
        {"id": "tendencia", "nombre": "Theil-Sen", "entradas": ["paso:descarga"]},
    ],
    "generado_utc": "2026-11-14T00:00:00Z",
}


def prueba_tendencia(**cambios: Any) -> dict[str, Any]:
    """Estructura válida de una tendencia. Solo para pruebas de contrato: nunca se importa como dato real."""
    resultado: dict[str, Any] = {
        "tipo": "tendencia",
        "periodo": {"desde": "1998", "hasta": "2025"},
        "n": 28,
        "pendiente": {"valor": 1.0, "intervalo": {"lo": 0.5, "hi": 1.5}, "unidad": "mm/decada"},
        "significancia": {"p_mann_kendall": 0.2, "p_hamed_rao": 0.3, "p_conservador": 0.3},
        "sello": {
            k: {"estado": "pendiente"}
            for k in ("ventanas", "enso", "sensor", "independencia", "detectabilidad")
        },
        "veredicto": "preliminar",
    }
    resultado.update(cambios)
    return {
        "dominio_id": "chili_analisis",
        "titulo": "Prueba de contrato de tendencia",
        "resumen": "Expediente sintético usado solo por las pruebas automatizadas.",
        "resultado": resultado,
        "procedencia": PROCEDENCIA,
    }
