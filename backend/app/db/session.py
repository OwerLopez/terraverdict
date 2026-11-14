"""Motor y fábrica de sesiones. SQLite en desarrollo; PostgreSQL en producción."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from fastapi import Request
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker


def crear_motor(url: str) -> Engine:
    argumentos: dict[str, Any] = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        argumentos["connect_args"] = {"check_same_thread": False}
    motor = create_engine(url, **argumentos)
    if url.startswith("sqlite"):

        @event.listens_for(motor, "connect")
        def _pragmas(conexion: Any, _registro: Any) -> None:
            cursor = conexion.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    return motor


def crear_fabrica_sesiones(motor: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=motor, autoflush=False, expire_on_commit=False)


def obtener_sesion(request: Request) -> Iterator[Session]:
    fabrica: sessionmaker[Session] = request.app.state.fabrica_sesiones
    with fabrica() as sesion:
        yield sesion
