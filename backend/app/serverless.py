"""Arranque para plataformas sin servidor (Vercel Functions u otras con disco efímero).

Cada instancia nueva ("arranque en frío") prepara su base antes de atender la primera petición, con
los mismos pasos que el contenedor Docker (`migrar` + `importar`):

1. aplica las migraciones de Alembic sobre `TV_DATABASE_URL`;
2. importa catálogos, eventos citados y el contrato `resultados/contrato/expedientes.json`
   (idempotente por hash de contenido: con una base compartida no duplica nada);
3. si se definen `TV_ADMIN_EMAIL` y `TV_ADMIN_PASSWORD`, asegura el administrador.

Con SQLite en `/tmp` cada instancia tiene su propia copia de solo lectura de los resultados
publicados: sirve para la demostración pública. Lo que se escriba (usuarios, claves, expedientes
nuevos) no persiste entre instancias; para eso se usa PostgreSQL (`TV_DATABASE_URL=postgresql+psycopg://…`).
No hay secretos por defecto: en producción `Settings` exige `TV_JWT_SECRETO` de 32 caracteres o más.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI

from app.core.config import obtener_settings
from app.importacion import importar_todo
from app.main import create_app
from app.services import usuarios

RAIZ_BACKEND = Path(__file__).resolve().parents[1]
log = logging.getLogger("terraverdict.serverless")


def _migrar(database_url: str) -> None:
    config = Config(str(RAIZ_BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(RAIZ_BACKEND / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")


def preparar() -> FastAPI:
    settings = obtener_settings()
    inicio = time.perf_counter()
    _migrar(settings.database_url)
    app = create_app(settings)
    with app.state.fabrica_sesiones() as sesion:
        resumen = importar_todo(
            sesion, settings.raiz_datos, incluir_ciencia=settings.importar_resultados_ciencia
        )
        email, contrasena = os.environ.get("TV_ADMIN_EMAIL"), os.environ.get("TV_ADMIN_PASSWORD")
        if email and contrasena:
            usuarios.asegurar_admin(sesion, email, contrasena)
    log.info(
        "arranque_en_frio",
        extra={
            "segundos": round(time.perf_counter() - inicio, 2),
            "expedientes": resumen["expedientes_total"],
        },
    )
    return app


app = preparar()
