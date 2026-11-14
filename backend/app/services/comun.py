"""Utilidades compartidas por los servicios."""

from __future__ import annotations

from typing import Any, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core.errors import NoEncontrado

M = TypeVar("M")


def obtener_o_404(sesion: Session, modelo: type[M], ident: Any, nombre: str) -> M:
    objeto = sesion.get(modelo, ident)
    if objeto is None:
        raise NoEncontrado(f"{nombre} '{ident}' no existe.")
    return objeto


def paginar(
    sesion: Session, consulta: Select[Any], limite: int, desplazamiento: int
) -> tuple[list[Any], int]:
    total = sesion.scalar(select(func.count()).select_from(consulta.order_by(None).subquery())) or 0
    items = list(sesion.scalars(consulta.limit(limite).offset(desplazamiento)))
    return items, int(total)


def exigir_existencia(sesion: Session, referencias: dict[str, tuple[type[Any], Any]]) -> None:
    """Valida claves foráneas antes de escribir, con un error legible por campo."""
    errores = [
        {"campo": campo, "mensaje": f"'{valor}' no existe.", "tipo": "referencia"}
        for campo, (modelo, valor) in referencias.items()
        if valor is not None and sesion.get(modelo, valor) is None
    ]
    if errores:
        raise NoEncontrado("Referencias inexistentes.", errores=errores)
