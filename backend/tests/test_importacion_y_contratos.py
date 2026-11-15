import json
from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.core.config import RAIZ_REPO
from app.db.base import Base
from app.db.models import Expediente, InformeVerificacion, Observacion
from app.importacion import importar_autodema, importar_todo
from app.main import create_app

BACKEND = Path(__file__).resolve().parents[1]


def test_importacion_es_idempotente(sesion: Session) -> None:
    antes = (
        sesion.scalar(select(func.count()).select_from(Expediente)),
        sesion.scalar(select(func.count()).select_from(Observacion)),
        sesion.scalar(select(func.count()).select_from(InformeVerificacion)),
    )
    importar_todo(sesion, RAIZ_REPO, incluir_ciencia=False)
    despues = (
        sesion.scalar(select(func.count()).select_from(Expediente)),
        sesion.scalar(select(func.count()).select_from(Observacion)),
        sesion.scalar(select(func.count()).select_from(InformeVerificacion)),
    )
    assert antes == despues


def test_autodema_valida_consistencia(sesion: Session, tmp_path: Path) -> None:
    (tmp_path / "datos" / "autodema").mkdir(parents=True)
    (tmp_path / "docs" / "verificacion").mkdir(parents=True)
    original = json.loads((RAIZ_REPO / "datos" / "autodema" / "reporte_2024-03-13.json").read_text())
    original["total_chili_volumen_util_hm3"] = 999.0
    (tmp_path / "datos" / "autodema" / "reporte_2024-03-13.json").write_text(json.dumps(original))
    (tmp_path / "docs" / "verificacion" / "evidencia.json").write_text(
        (RAIZ_REPO / "docs" / "verificacion" / "evidencia.json").read_text()
    )
    with pytest.raises(ValueError, match="inconsistente"):
        importar_autodema(sesion, tmp_path)


def test_openapi_versionado_coincide_con_el_codigo() -> None:
    """Si falla: ejecute `python -m app.cli exportar-openapi` y regenere los tipos del frontend."""
    generado = create_app().openapi()
    versionado = json.loads((RAIZ_REPO / "docs" / "api" / "openapi.json").read_text())
    assert generado == versionado


def test_openapi_documenta_errores_y_seguridad() -> None:
    spec = create_app().openapi()
    esquemas = spec["components"]["securitySchemes"]
    assert {"OAuth2PasswordBearer", "APIKeyHeader"} <= set(esquemas)
    post_series = spec["paths"]["/api/v1/series"]["post"]["responses"]
    assert "application/problem+json" in post_series["422"]["content"]


def test_migraciones_reproducen_los_modelos(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'migrada.db'}"
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "alembic"))
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")
    motor = create_engine(url)
    with motor.connect() as conexion:
        diferencias = compare_metadata(MigrationContext.configure(conexion), Base.metadata)
    motor.dispose()
    assert diferencias == [], f"Los modelos cambiaron sin migración: {diferencias}"
