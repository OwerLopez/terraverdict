"""Errores de dominio y respuestas en formato *Problem Details* (RFC 9457 / RFC 7807).

Toda respuesta de error de la API tiene ``Content-Type: application/problem+json`` y el
cuerpo ``{type, title, status, detail, instance, codigo, request_id, errores}``. El campo
``codigo`` es estable y está pensado para que los clientes reaccionen sin leer textos.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import request_id_actual

log = logging.getLogger("terraverdict.errores")

TIPO_BASE = "https://github.com/DiegoNiS/terraverdict/blob/main/docs/api/README.md#errores"


class ErrorDominio(Exception):
    status: int = 400
    codigo: str = "solicitud_invalida"
    titulo: str = "Solicitud inválida"

    def __init__(self, detalle: str, *, errores: list[dict[str, Any]] | None = None) -> None:
        super().__init__(detalle)
        self.detalle = detalle
        self.errores = errores


class NoAutenticado(ErrorDominio):
    status, codigo, titulo = 401, "no_autenticado", "Autenticación requerida"


class Prohibido(ErrorDominio):
    status, codigo, titulo = 403, "prohibido", "Permisos insuficientes"


class NoEncontrado(ErrorDominio):
    status, codigo, titulo = 404, "no_encontrado", "Recurso no encontrado"


class Conflicto(ErrorDominio):
    status, codigo, titulo = 409, "conflicto", "Conflicto con el estado actual"


class TransicionInvalida(ErrorDominio):
    status, codigo, titulo = 409, "transicion_invalida", "Transición de estado no permitida"


class ReglaCientifica(ErrorDominio):
    """Un resultado viola una regla de publicación (p. ej., publicar sin habilidad)."""

    status, codigo, titulo = 422, "regla_cientifica", "El resultado no cumple una regla de publicación"


class DemasiadasSolicitudes(ErrorDominio):
    status, codigo, titulo = 429, "demasiadas_solicitudes", "Demasiadas solicitudes"


class ServicioNoDisponible(ErrorDominio):
    status, codigo, titulo = 503, "servicio_no_disponible", "Servicio no disponible"


def respuesta_problema(
    request: Request,
    *,
    status: int,
    codigo: str,
    titulo: str,
    detalle: str | None = None,
    errores: list[dict[str, Any]] | None = None,
    cabeceras: dict[str, str] | None = None,
) -> JSONResponse:
    cuerpo: dict[str, Any] = {
        "type": f"{TIPO_BASE}-{codigo}",
        "title": titulo,
        "status": status,
        "detail": detalle,
        "instance": request.url.path,
        "codigo": codigo,
        "request_id": request_id_actual(),
    }
    if errores:
        cuerpo["errores"] = errores
    return JSONResponse(
        jsonable_encoder(cuerpo),
        status_code=status,
        media_type="application/problem+json",
        headers=cabeceras,
    )


def problema_interno(request: Request) -> JSONResponse:
    """Respuesta 500 sin detalles internos; el ``request_id`` permite encontrar la traza en los registros."""
    return respuesta_problema(
        request,
        status=500,
        codigo="error_interno",
        titulo="Error interno",
        detalle="Ocurrió un error inesperado. Comparta el request_id con el equipo.",
    )


_CODIGOS_HTTP = {
    400: ("solicitud_invalida", "Solicitud inválida"),
    401: ("no_autenticado", "Autenticación requerida"),
    403: ("prohibido", "Permisos insuficientes"),
    404: ("no_encontrado", "Recurso no encontrado"),
    405: ("metodo_no_permitido", "Método no permitido"),
    409: ("conflicto", "Conflicto con el estado actual"),
    429: ("demasiadas_solicitudes", "Demasiadas solicitudes"),
}


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(ErrorDominio)
    async def _dominio(request: Request, exc: ErrorDominio) -> JSONResponse:
        cabeceras = {"WWW-Authenticate": "Bearer"} if exc.status == 401 else None
        return respuesta_problema(
            request,
            status=exc.status,
            codigo=exc.codigo,
            titulo=exc.titulo,
            detalle=exc.detalle,
            errores=exc.errores,
            cabeceras=cabeceras,
        )

    @app.exception_handler(RequestValidationError)
    async def _validacion(request: Request, exc: RequestValidationError) -> JSONResponse:
        errores = [
            {
                "campo": ".".join(str(p) for p in e.get("loc", ())),
                "mensaje": e.get("msg"),
                "tipo": e.get("type"),
            }
            for e in exc.errors()
        ]
        return respuesta_problema(
            request,
            status=422,
            codigo="validacion",
            titulo="Los datos enviados no cumplen el contrato",
            detalle=f"{len(errores)} error(es) de validación.",
            errores=errores,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        codigo, titulo = _CODIGOS_HTTP.get(exc.status_code, ("error_http", "Error HTTP"))
        detalle = exc.detail if isinstance(exc.detail, str) else None
        return respuesta_problema(
            request, status=exc.status_code, codigo=codigo, titulo=titulo, detalle=detalle
        )

    @app.exception_handler(Exception)
    async def _inesperado(request: Request, exc: Exception) -> JSONResponse:
        # Último recurso: normalmente ``IdSolicitudMiddleware`` responde antes con el request_id.
        log.exception("Error no controlado", extra={"ruta": request.url.path})
        return problema_interno(request)
