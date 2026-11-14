"""Middleware ASGI: identificador de solicitud, registro de acceso y cabeceras de seguridad."""

from __future__ import annotations

import logging
import re
import time
import uuid

from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import problema_interno
from app.core.logging import fijar_request_id, restaurar_request_id

log = logging.getLogger("terraverdict.acceso")
_ID_VALIDO = re.compile(r"^[A-Za-z0-9._-]{8,64}$")
_RUTAS_DOCS = ("/api/docs", "/api/redoc", "/api/openapi.json")


class IdSolicitudMiddleware:
    """Propaga ``X-Request-ID`` (o genera uno) y registra cada solicitud con su duración.

    También responde a los errores no controlados: el manejador de ``Exception`` de Starlette
    corre fuera de la pila de middleware, cuando el ``request_id`` ya no existe, y la
    respuesta 500 saldría sin él. Aquí el 500 conserva su ``request_id`` y su cabecera.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        entrante = dict(scope.get("headers") or []).get(b"x-request-id", b"").decode("latin-1")
        rid = entrante if _ID_VALIDO.match(entrante) else uuid.uuid4().hex
        token = fijar_request_id(rid)
        inicio = time.perf_counter()
        estado = {"codigo": 500, "iniciada": False}

        async def enviar(mensaje: Message) -> None:
            if mensaje["type"] == "http.response.start":
                estado["codigo"] = mensaje["status"]
                estado["iniciada"] = True
                mensaje.setdefault("headers", [])
                mensaje["headers"].append((b"x-request-id", rid.encode()))
            await send(mensaje)

        try:
            await self.app(scope, receive, enviar)
        except Exception:
            if estado["iniciada"]:
                raise  # la respuesta ya empezó: no se puede reemplazar
            log.exception("Error no controlado", extra={"ruta": scope.get("path")})
            await problema_interno(Request(scope))(scope, receive, enviar)
        finally:
            log.info(
                "solicitud",
                extra={
                    "metodo": scope.get("method"),
                    "ruta": scope.get("path"),
                    "estado": estado["codigo"],
                    "ms": round((time.perf_counter() - inicio) * 1000, 1),
                },
            )
            restaurar_request_id(token)


class CabecerasSeguridadMiddleware:
    """Cabeceras defensivas para todas las respuestas de la API."""

    def __init__(self, app: ASGIApp, *, hsts: bool = False) -> None:
        self.app = app
        self.hsts = hsts

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        es_docs = str(scope.get("path", "")).startswith(_RUTAS_DOCS)

        async def enviar(mensaje: Message) -> None:
            if mensaje["type"] == "http.response.start":
                cab = mensaje.setdefault("headers", [])
                cab.extend(
                    [
                        (b"x-content-type-options", b"nosniff"),
                        (b"x-frame-options", b"DENY"),
                        (b"referrer-policy", b"strict-origin-when-cross-origin"),
                        (b"permissions-policy", b"geolocation=(), camera=(), microphone=()"),
                        (b"cross-origin-opener-policy", b"same-origin"),
                    ]
                )
                if not es_docs:
                    cab.append((b"content-security-policy", b"default-src 'none'; frame-ancestors 'none'"))
                if self.hsts:
                    cab.append((b"strict-transport-security", b"max-age=31536000; includeSubDomains"))
            await send(mensaje)

        await self.app(scope, receive, enviar)
