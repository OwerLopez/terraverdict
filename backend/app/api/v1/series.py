"""Series temporales: consulta pública y publicación por el pipeline."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Header, Query, Response, status

from app.api.deps import Ingesta, PaginacionDep, SesionDep
from app.db.models import Serie
from app.schemas.comun import Pagina, errores
from app.schemas.series import (
    ObservacionesCarga,
    ObservacionesSalida,
    ObservacionSalida,
    ResultadoCarga,
    SerieCrear,
    SerieSalida,
)
from app.services import series as servicio
from app.services.comun import obtener_o_404

router = APIRouter(prefix="/series", tags=["Series"])


@router.get("", response_model=Pagina[SerieSalida], summary="Listar series publicadas")
def listar(
    sesion: SesionDep,
    pagina: PaginacionDep,
    dominio_id: str | None = None,
    unidad_id: str | None = None,
    variable_id: str | None = None,
    fuente_id: str | None = None,
) -> Pagina[SerieSalida]:
    limite, desplazamiento = pagina
    items, total = servicio.listar_series(
        sesion,
        dominio_id=dominio_id,
        unidad_id=unidad_id,
        variable_id=variable_id,
        fuente_id=fuente_id,
        limite=limite,
        desplazamiento=desplazamiento,
    )
    return Pagina(
        items=[SerieSalida.model_validate(s) for s in items],
        total=total,
        limite=limite,
        desplazamiento=desplazamiento,
    )


@router.post(
    "",
    response_model=SerieSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una serie (pipeline)",
    responses=errores(401, 403, 404, 409, 422),
)
def crear(datos: SerieCrear, _: Ingesta, sesion: SesionDep) -> SerieSalida:
    return SerieSalida.model_validate(servicio.crear_serie(sesion, datos))


@router.get("/{serie_id}", response_model=SerieSalida, summary="Detalle de una serie", responses=errores(404))
def obtener(serie_id: str, sesion: SesionDep) -> SerieSalida:
    return SerieSalida.model_validate(obtener_o_404(sesion, Serie, serie_id, "Serie"))


@router.get(
    "/{serie_id}/observaciones",
    response_model=ObservacionesSalida,
    summary="Observaciones de una serie",
    description="Devuelve `ETag` con la versión de la serie; los clientes pueden usar `If-None-Match`.",
    responses={**errores(404), 304: {"description": "Sin cambios desde la versión indicada."}},
)
def observaciones(
    serie_id: str,
    sesion: SesionDep,
    response: Response,
    desde: Annotated[date | None, Query(description="Fecha mínima inclusiva.")] = None,
    hasta: Annotated[date | None, Query(description="Fecha máxima inclusiva.")] = None,
    if_none_match: Annotated[str | None, Header(description="ETag recibido previamente.")] = None,
) -> ObservacionesSalida | Response:
    serie = obtener_o_404(sesion, Serie, serie_id, "Serie")
    etag = f'W/"{serie.id}:v{serie.version}:{desde}:{hasta}"'
    cabeceras = {"ETag": etag, "Cache-Control": "public, max-age=60"}
    if if_none_match == etag:
        return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers=cabeceras)
    serie, filas = servicio.observaciones(sesion, serie_id, desde, hasta)
    response.headers.update(cabeceras)
    return ObservacionesSalida(
        serie_id=serie.id,
        unidad=serie.unidad,
        frecuencia=serie.frecuencia,
        version=serie.version,
        observaciones=[ObservacionSalida.model_validate(o) for o in filas],
    )


@router.put(
    "/{serie_id}/observaciones",
    response_model=ResultadoCarga,
    summary="Cargar observaciones (idempotente por fecha)",
    description="Inserta o actualiza por fecha. Cada cambio incrementa la versión de la serie.",
    responses=errores(401, 403, 404, 422),
)
def cargar(serie_id: str, carga: ObservacionesCarga, _: Ingesta, sesion: SesionDep) -> ResultadoCarga:
    return servicio.cargar_observaciones(sesion, serie_id, carga)
