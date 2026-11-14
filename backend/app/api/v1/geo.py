"""Dominios espaciales y unidades de análisis (GeoJSON, EPSG:4326)."""

from __future__ import annotations

from fastapi import APIRouter, status
from sqlalchemy import select

from app.api.deps import Ingesta, SesionDep
from app.core.errors import Conflicto
from app.db.models import Dominio, Unidad
from app.schemas.comun import errores
from app.schemas.geo import (
    DominioSalida,
    Feature,
    FeatureCollection,
    GeometriaActualizar,
    UnidadCrear,
    UnidadSalida,
)
from app.services.comun import exigir_existencia, obtener_o_404

router = APIRouter(tags=["Dominios y unidades"])


@router.get(
    "/dominios", response_model=list[DominioSalida], summary="Dominios de análisis y de entrenamiento"
)
def listar_dominios(sesion: SesionDep) -> list[Dominio]:
    return list(sesion.scalars(select(Dominio).order_by(Dominio.id)))


@router.get(
    "/dominios/{dominio_id}",
    response_model=DominioSalida,
    summary="Detalle de un dominio",
    responses=errores(404),
)
def obtener_dominio(dominio_id: str, sesion: SesionDep) -> Dominio:
    return obtener_o_404(sesion, Dominio, dominio_id, "Dominio")


@router.get(
    "/dominios/{dominio_id}/unidades",
    response_model=FeatureCollection,
    summary="Unidades de análisis de un dominio como GeoJSON",
    description="Las unidades sin geometría (`estado_geometria = pendiente`) se incluyen con `geometry: null`.",
    responses=errores(404),
)
def unidades_geojson(dominio_id: str, sesion: SesionDep) -> FeatureCollection:
    obtener_o_404(sesion, Dominio, dominio_id, "Dominio")
    unidades = sesion.scalars(select(Unidad).where(Unidad.dominio_id == dominio_id).order_by(Unidad.id))
    return FeatureCollection(
        features=[
            Feature(
                id=u.id,
                geometry=u.geometria,
                properties={
                    "nombre": u.nombre,
                    "tipo": u.tipo,
                    "estado_geometria": u.estado_geometria,
                    **u.metadatos,
                },
            )
            for u in unidades
        ]
    )


@router.get(
    "/unidades/{unidad_id}",
    response_model=UnidadSalida,
    summary="Detalle de una unidad",
    responses=errores(404),
)
def obtener_unidad(unidad_id: str, sesion: SesionDep) -> Unidad:
    return obtener_o_404(sesion, Unidad, unidad_id, "Unidad")


@router.post(
    "/unidades",
    response_model=UnidadSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una unidad de análisis (pipeline, etapa E1)",
    responses=errores(401, 403, 404, 409, 422),
)
def crear_unidad(datos: UnidadCrear, _: Ingesta, sesion: SesionDep) -> Unidad:
    if sesion.get(Unidad, datos.id):
        raise Conflicto(f"La unidad '{datos.id}' ya existe.")
    exigir_existencia(sesion, {"dominio_id": (Dominio, datos.dominio_id)})
    unidad = Unidad(
        id=datos.id,
        dominio_id=datos.dominio_id,
        tipo=datos.tipo.value,
        nombre=datos.nombre,
        geometria=datos.geometria.model_dump() if datos.geometria else None,
        estado_geometria=datos.estado_geometria.value,
        metadatos=datos.metadatos,
    )
    sesion.add(unidad)
    sesion.commit()
    return unidad


@router.put(
    "/unidades/{unidad_id}/geometria",
    response_model=UnidadSalida,
    summary="Publicar la geometría delimitada de una unidad",
    responses=errores(401, 403, 404, 422),
)
def actualizar_geometria(unidad_id: str, datos: GeometriaActualizar, _: Ingesta, sesion: SesionDep) -> Unidad:
    unidad = obtener_o_404(sesion, Unidad, unidad_id, "Unidad")
    unidad.geometria = datos.geometria.model_dump()
    unidad.estado_geometria = datos.estado_geometria.value
    sesion.commit()
    return unidad
