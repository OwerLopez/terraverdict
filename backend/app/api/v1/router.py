from fastapi import APIRouter

from app.api.v1 import (
    asistente,
    auth,
    catalogo,
    ciencia,
    expedientes,
    fenomenos,
    geo,
    metricas,
    procesos,
    series,
    sistema,
)

router_v1 = APIRouter()
for modulo in (
    sistema,
    auth,
    catalogo,
    geo,
    series,
    expedientes,
    fenomenos,
    metricas,
    ciencia,
    procesos,
    asistente,
):
    router_v1.include_router(modulo.router)
