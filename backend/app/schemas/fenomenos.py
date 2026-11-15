"""Catálogo de fenómenos naturales (config/fenomenos.yaml) y capas del mapa."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.schemas.comun import Esquema
from app.schemas.geo import Feature


class VariableFenomeno(Esquema):
    id: str
    nombre: str
    unidad: str | None = None
    rol: str | None = None
    relevancia: str | None = Field(None, description="Prior físico: alta, media o baja.")
    fuente: str | None = None
    justificacion: str
    limitaciones: str | None = None
    detalles: dict[str, Any] = Field(default_factory=dict, description="Resolución, cobertura, parámetro…")


class FenomenoSalida(Esquema):
    id: str
    nombre: str
    procesos: str
    objetivo: dict[str, Any]
    variables: list[VariableFenomeno]
    metricas: list[str]
    dominio_bbox: list[float] | None = None


class CatalogoFenomenos(Esquema):
    version: int
    verificado: str
    particion_temporal: dict[str, list[str]]
    abstencion: dict[str, float | int]
    fenomenos: list[FenomenoSalida]
    acceso_fuentes_nacionales: dict[str, dict[str, str]]
    via_integracion_nacional: str | None = None
    aviso: str


class CapaGeoJSON(Esquema):
    """FeatureCollection con metadatos de su origen (el expediente del que sale cada punto)."""

    type: str = "FeatureCollection"
    features: list[Feature]
    expediente_id: str | None = Field(
        None, description="Expediente vigente del que sale la capa; null si no hay."
    )
    generado_utc: str | None = None
    fuente: str | None = None
    nota: str | None = None


class PanoramaNacional(Esquema):
    """Escala nacional vigente: el resultado completo del expediente `panorama_nacional` más reciente."""

    expediente_id: str | None = Field(
        None, description="Expediente del que sale el panorama; null si no hay."
    )
    generado_utc: str | None = None
    resultado: dict[str, Any] | None = Field(
        None, description="Contenido validado con ResultadoPanoramaNacional al publicarse."
    )
    aviso: str
