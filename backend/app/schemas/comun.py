"""Esquemas compartidos: paginación, errores y utilidades de validación."""

from __future__ import annotations

import math
from typing import Annotated, Any, Generic, TypeVar

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints

T = TypeVar("T")

IdSlug = Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9_.:-]{1,199}$")]
"""Identificador estable: minúsculas, dígitos y ``_ . : -`` (máx. 200)."""


def _finito(valor: float | None) -> float | None:
    if valor is not None and not math.isfinite(valor):
        raise ValueError("Se esperaba un número finito (sin NaN ni infinito).")
    return valor


NumeroFinito = Annotated[float, AfterValidator(_finito)]
NumeroFinitoOpcional = Annotated[float | None, AfterValidator(_finito)]
Metricas = dict[str, float | int | str | bool | None]


class Esquema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid", str_strip_whitespace=True)


class Pagina(BaseModel, Generic[T]):
    items: list[T]
    total: int = Field(ge=0)
    limite: int = Field(ge=1)
    desplazamiento: int = Field(ge=0)


class ErrorCampo(BaseModel):
    campo: str
    mensaje: str | None = None
    tipo: str | None = None


class ProblemaHTTP(BaseModel):
    """Cuerpo de error (RFC 9457, *Problem Details for HTTP APIs*)."""

    type: str
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None
    codigo: str = Field(description="Código estable para que el cliente reaccione sin leer textos.")
    request_id: str | None = None
    errores: list[ErrorCampo] | None = None


_DESCRIPCIONES = {
    400: "Solicitud inválida.",
    401: "Falta autenticación o el token es inválido.",
    403: "La identidad no tiene permisos para esta operación.",
    404: "El recurso no existe.",
    409: "Conflicto con el estado actual del recurso.",
    422: "Los datos no cumplen el contrato o una regla de publicación científica.",
    429: "Se superó el límite de solicitudes.",
    503: "Servicio o módulo todavía no conectado.",
}


def errores(*codigos: int) -> dict[int | str, dict[str, Any]]:
    return {
        c: {
            "model": ProblemaHTTP,
            "description": _DESCRIPCIONES.get(c, "Error."),
            "content": {"application/problem+json": {}},
        }
        for c in codigos
    }


class Mensaje(BaseModel):
    mensaje: str
