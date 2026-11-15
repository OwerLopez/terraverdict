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


class HistorialMetricas(Esquema):
    """Historial vigente: el resultado completo del expediente `historial_metricas` más reciente."""

    expediente_id: str | None = Field(
        None, description="Expediente del que sale el historial; null si no hay."
    )
    generado_utc: str | None = None
    resultado: dict[str, Any] | None = Field(
        None, description="Contenido validado con ResultadoHistorialMetricas al publicarse."
    )
    aviso: str


class TextoBilingue(Esquema):
    es: str
    en: str


class FichaMetrica(Esquema):
    id: str
    grupo: str
    nombre: TextoBilingue
    formula: str
    que_mide: TextoBilingue
    como_leer: TextoBilingue
    mejor: str = Field(description="mayor, menor, cercano_a_0_9 o informativa.")
    valor_referencia: float | None = Field(None, description="Valor de la referencia o umbral de lectura.")
    cita: str


class CatalogoMetricas(Esquema):
    version: int
    grupos: dict[str, TextoBilingue]
    metricas: list[FichaMetrica]


class TareaMapa(Esquema):
    expediente_id: str
    titulo: str
    fenomeno: str
    tarea: str
    horizonte: str
    metrica_principal: str
    mejor_validacion: str


class ModeloMapa(Esquema):
    nombre: str
    familia: str


class CeldaMetricas(Esquema):
    """Métricas de un modelo en una tarea, tal como se publicaron en su expediente."""

    expediente_id: str
    modelo: str
    puntaje_validacion: float
    puntaje_prueba: float | None = None
    ic90_inferior: float | None = None
    ic90_superior: float | None = None
    p_diebold_mariano: float | None = None
    dispersion_semillas: float | None = None


class CeldaImportancia(Esquema):
    expediente_id: str
    variable: str
    importancia: float
    desviacion: float


class MapasMetricas(Esquema):
    """Matrices para los mapas de calor: modelo × tarea por métrica e importancia tarea × variable."""

    tareas: list[TareaMapa]
    modelos: list[ModeloMapa]
    celdas: list[CeldaMetricas]
    variables: list[str]
    importancia: list[CeldaImportancia]
    aviso: str
