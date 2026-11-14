"""Geometrías GeoJSON (RFC 7946, EPSG:4326), dominios y unidades de análisis."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.domain.vocabulario import EstadoGeometria, TipoUnidad
from app.schemas.comun import Esquema, IdSlug


class Geometria(BaseModel):
    type: Literal["Point", "MultiPoint", "LineString", "MultiLineString", "Polygon", "MultiPolygon"]
    coordinates: list[Any]

    @field_validator("coordinates")
    @classmethod
    def _no_vacio(cls, valor: list[Any]) -> list[Any]:
        if not valor:
            raise ValueError("Las coordenadas no pueden estar vacías.")
        return valor


class DominioSalida(Esquema):
    id: str
    nombre: str
    descripcion: str
    tipo: str
    bbox: list[float] = Field(description="[lon_min, lat_min, lon_max, lat_max] en EPSG:4326.")
    aproximado: bool
    geometria: Geometria | None
    metadatos: dict[str, Any]


class UnidadSalida(Esquema):
    id: str
    dominio_id: str
    tipo: TipoUnidad
    nombre: str
    geometria: Geometria | None
    estado_geometria: EstadoGeometria
    metadatos: dict[str, Any]


class UnidadCrear(Esquema):
    id: IdSlug
    dominio_id: str
    tipo: TipoUnidad
    nombre: str = Field(min_length=2, max_length=200)
    geometria: Geometria | None = None
    estado_geometria: EstadoGeometria = EstadoGeometria.pendiente
    metadatos: dict[str, Any] = Field(default_factory=dict)


class GeometriaActualizar(Esquema):
    geometria: Geometria
    estado_geometria: EstadoGeometria


class Feature(BaseModel):
    type: Literal["Feature"] = "Feature"
    id: str
    geometry: Geometria | None
    properties: dict[str, Any]


class FeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[Feature]
