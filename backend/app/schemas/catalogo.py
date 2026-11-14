"""Catálogo: fuentes, variables, unidades de medida, problemas, eventos y verificación."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import Field

from app.domain.vocabulario import CategoriaEvento, CotaCifra, EstadoVerificacion, PrecisionFecha
from app.schemas.comun import Esquema


class FuenteSalida(Esquema):
    id: str
    nombre: str
    coleccion: str | None
    version: str | None
    acceso: list[str]
    familia: str | None
    url: str | None
    licencia: str | None
    periodo: list[str | None] | None
    resolucion: dict[str, str] | None
    usos: list[str]
    advertencia: str | None
    por_confirmar: str | None
    estado_verificacion: EstadoVerificacion
    verificado_en: datetime | None
    evidencia: dict[str, Any] | None = Field(None, description="Resultado crudo de la verificación.")


class VariableSalida(Esquema):
    id: str
    nombre: str
    simbolo: str
    unidad: str
    grupo: str
    descripcion: str
    relacion: str | None


class UnidadMedidaSalida(Esquema):
    codigo: str
    simbolo: str
    nombre: str
    ucum: str


class ProblemaSalida(Esquema):
    id: str
    nombre: str
    objetivo: str
    candidatas: list[str]
    muestras: str
    viabilidad: str
    dominio_entrenamiento: str


class Cifra(Esquema):
    valor: float
    unidad: str = Field(description="Código de unidad; ver GET /api/v1/unidades-medida.")
    descripcion: str
    cota: CotaCifra = Field(
        default=CotaCifra.exacta,
        description="Si la fuente da una cota ('más del 70 %') en lugar de un valor exacto.",
    )


class ReferenciaDocumental(Esquema):
    titulo: str
    url: str
    medio: str | None = None
    fecha_publicacion: str | None = None


class EventoDocumentadoSalida(Esquema):
    id: str
    fecha: date
    precision: PrecisionFecha
    categoria: CategoriaEvento
    titulo: str
    descripcion: str
    cifras: list[Cifra]
    fuentes: list[ReferenciaDocumental]


class InformeVerificacionSalida(Esquema):
    id: str
    tipo: str
    generado_utc: datetime
    total: int
    correctas: int
    datos: dict[str, Any]


class VerificacionResumen(Esquema):
    fuentes: InformeVerificacionSalida | None
    enlaces: InformeVerificacionSalida | None
    estados_fuentes: dict[str, int]
