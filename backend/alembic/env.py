"""Entorno de Alembic: usa TV_DATABASE_URL y los metadatos de los modelos."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import obtener_settings
from app.db import models  # noqa: F401  (registra los modelos en los metadatos)
from app.db.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

url = config.get_main_option("sqlalchemy.url") or obtener_settings().database_url
config.set_main_option("sqlalchemy.url", url)
target_metadata = Base.metadata


def ejecutar_offline() -> None:
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()


def ejecutar_online() -> None:
    motor = engine_from_config(
        config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    with motor.connect() as conexion:
        context.configure(connection=conexion, target_metadata=target_metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    ejecutar_offline()
else:
    ejecutar_online()
