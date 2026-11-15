"""Punto de entrada de la API (``uvicorn app.main:app``)."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.v1.router import router_v1
from app.core.config import Settings, obtener_settings
from app.core.errors import registrar_manejadores
from app.core.logging import configurar_logging
from app.core.middleware import CabecerasSeguridadMiddleware, IdSolicitudMiddleware
from app.core.security import LimitadorVentana
from app.db.session import crear_fabrica_sesiones, crear_motor

DESCRIPCION = """
API de **TerraVerdict**: ciencia de datos geoespaciales para saber qué cambia en una cuenca de
montaña, por qué, con cuánta confianza y dónde actuar (caso piloto: Arequipa, Perú).

* **Lectura pública:** catálogo de fuentes verificadas, series, expedientes, eventos y procesos.
* **Escritura del pipeline:** cuentas de servicio con clave `X-API-Key` (alcances `ingesta` y `trabajador`).
* **Personas:** token Bearer (`POST /api/v1/auth/token`) con roles `lector`, `analista` y `admin`.
* **Errores:** `application/problem+json` (RFC 9457) con un `codigo` estable.
* **Contratos de integración:** ver `docs/integracion-ciencia-datos.md`.

Ningún dato científico se genera en esta API: solo se publica lo que el pipeline calcula y valida.
"""

ETIQUETAS = [
    {"name": "Sistema", "description": "Salud del servicio, resumen y vocabularios."},
    {"name": "Autenticación y acceso", "description": "Tokens JWT, usuarios y claves API de servicio."},
    {"name": "Catálogo", "description": "Fuentes verificadas, variables, problemas, eventos y verificación."},
    {"name": "Dominios y unidades", "description": "Zonas de estudio y unidades de análisis en GeoJSON."},
    {"name": "Series", "description": "Series temporales publicadas por el pipeline."},
    {"name": "Expedientes", "description": "Resultados científicos inmutables con procedencia."},
    {
        "name": "Fenómenos naturales",
        "description": "Catálogo científico de fenómenos y capas GeoJSON del mapa.",
    },
    {"name": "Ciencia de datos", "description": "Matriz de Relevancia y ejecuciones del pipeline."},
    {"name": "Procesos", "description": "Cola de procesos científicos y su bitácora."},
    {"name": "Asistente", "description": "Asistente conversacional y verificador numérico."},
]


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or obtener_settings()
    configurar_logging(settings.log_nivel)
    motor = crear_motor(settings.database_url)

    app = FastAPI(
        title="TerraVerdict API",
        version=__version__,
        description=DESCRIPCION,
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_tags=ETIQUETAS,
        license_info={"name": "MIT"},
        contact={"name": "TerraVerdict", "url": "https://github.com/DiegoNiS/terraverdict"},
        swagger_ui_parameters={"persistAuthorization": True, "displayRequestDuration": True},
    )
    app.state.settings = settings
    app.state.motor = motor
    app.state.fabrica_sesiones = crear_fabrica_sesiones(motor)
    app.state.limitador_login = LimitadorVentana(settings.login_intentos_por_minuto, 60)

    # El último en añadirse es el más externo: CORS → cabeceras de seguridad → request_id → app.
    # Así, incluso el 500 que genera IdSolicitudMiddleware lleva las cabeceras de seguridad.
    app.add_middleware(IdSolicitudMiddleware)
    app.add_middleware(CabecerasSeguridadMiddleware, hsts=settings.entorno == "produccion")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origenes,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID", "If-None-Match"],
        expose_headers=["X-Request-ID", "ETag", "Location"],
        max_age=600,
    )
    registrar_manejadores(app)
    app.include_router(router_v1, prefix="/api/v1")
    return app


app = create_app()
