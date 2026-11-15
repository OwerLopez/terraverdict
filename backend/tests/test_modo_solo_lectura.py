"""Producción sin TV_JWT_SECRETO: la API sirve la consulta pública y no emite ni acepta tokens."""

from __future__ import annotations

from pathlib import Path

import jwt
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import RAIZ_REPO, Settings
from app.db.base import Base
from app.importacion import importar_todo
from app.main import create_app


def _cliente(tmp_path: Path, **extra: object) -> TestClient:
    s = Settings(
        entorno="produccion",
        database_url=f"sqlite:///{tmp_path / 'p.db'}",
        raiz_datos=RAIZ_REPO,
        cors_origenes=["https://terraverdict.vercel.app"],
        log_nivel="WARNING",
        **extra,  # type: ignore[arg-type]
    )
    app = create_app(s)
    Base.metadata.create_all(app.state.motor)
    with app.state.fabrica_sesiones() as sesion:
        importar_todo(sesion, RAIZ_REPO, incluir_ciencia=False)
    return TestClient(app)


def test_sin_secreto_la_consulta_publica_funciona_y_el_login_falla_cerrado(tmp_path: Path) -> None:
    c = _cliente(tmp_path)
    assert c.get("/api/v1/expedientes").status_code == 200
    r = c.post("/api/v1/auth/token", data={"username": "a@b.pe", "password": "x" * 12})
    assert r.status_code == 503 and r.json()["codigo"] == "servicio_no_disponible"


def test_sin_secreto_se_rechaza_un_token_firmado_con_el_secreto_de_desarrollo(tmp_path: Path) -> None:
    c = _cliente(tmp_path)
    falso = jwt.encode(
        {"sub": "1", "rol": "admin", "iat": 1, "exp": 4_102_444_800, "iss": "terraverdict", "typ": "access"},
        "solo-para-desarrollo-cambiar-en-produccion",
        algorithm="HS256",
    )
    r = c.get("/api/v1/auth/yo", headers={"Authorization": f"Bearer {falso}"})
    assert r.status_code in (401, 503) and r.status_code != 200


def test_secreto_corto_en_produccion_impide_arrancar() -> None:
    with pytest.raises(ValidationError, match="32 caracteres"):
        Settings(entorno="produccion", jwt_secreto="corto", cors_origenes=["https://x.pe"])  # type: ignore[arg-type]


def test_con_secreto_largo_hay_sesiones() -> None:
    s = Settings(entorno="produccion", jwt_secreto="s" * 48, cors_origenes=["https://x.pe"])  # type: ignore[arg-type]
    assert s.sesiones_habilitadas
    assert not Settings(entorno="produccion", cors_origenes=["https://x.pe"]).sesiones_habilitadas
