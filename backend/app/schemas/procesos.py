"""Procesos científicos: cola de trabajo entre la API y los trabajadores de ciencia de datos."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from app.domain.vocabulario import EstadoProceso, NivelEvento, TipoProceso
from app.schemas.comun import Esquema


class ProcesoCrear(Esquema):
    tipo: TipoProceso
    parametros: dict[str, Any] = Field(default_factory=dict)
    prioridad: int = Field(0, ge=0, le=10)


class ErrorProceso(Esquema):
    mensaje: str = Field(min_length=3, max_length=1000)
    detalle: dict[str, Any] | None = None


class ProcesoSalida(Esquema):
    id: str
    tipo: TipoProceso
    parametros: dict[str, Any]
    estado: EstadoProceso
    prioridad: int
    solicitado_por: str
    trabajador: str | None
    progreso: float | None
    expediente_id: str | None
    error: ErrorProceso | None
    creado_en: datetime
    iniciado_en: datetime | None
    finalizado_en: datetime | None
    ultimo_latido: datetime | None


class ReclamoProceso(Esquema):
    trabajador: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9._:-]+$")
    tipos: list[TipoProceso] = Field(min_length=1)


class ProcesoActualizar(Esquema):
    estado: EstadoProceso | None = None
    progreso: float | None = Field(None, ge=0, le=1)
    expediente_id: str | None = None
    error: ErrorProceso | None = None


class EventoProcesoCrear(Esquema):
    nivel: NivelEvento = NivelEvento.info
    mensaje: str = Field(min_length=1, max_length=2000)
    datos: dict[str, Any] | None = None


class EventoProcesoSalida(Esquema):
    id: int
    proceso_id: str
    t: datetime
    nivel: NivelEvento
    mensaje: str
    datos: dict[str, Any] | None
