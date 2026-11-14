"""Series temporales y observaciones."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import Field, field_validator, model_validator

from app.domain.unidades_medida import es_unidad_valida
from app.domain.vocabulario import Frecuencia
from app.schemas.comun import Esquema, IdSlug, NumeroFinitoOpcional
from app.schemas.procedencia import Procedencia


class SerieCrear(Esquema):
    """Registro de una serie publicada por el pipeline (etapa E5/E7)."""

    id: IdSlug = Field(
        description="ID estable. Convención: '<dominio>.<unidad>:<variable>:<fuente>:<frecuencia en minúsculas>'.",
        examples=["chili_analisis.cabecera_power:temperatura_aire_2m:power_mensual:p1y"],
    )
    dominio_id: str
    unidad_id: str | None = None
    variable_id: str
    fuente_id: str
    unidad: str = Field(description="Código de unidad de medida (GET /unidades-medida).")
    frecuencia: Frecuencia
    agregacion: dict[str, Any] = Field(
        default_factory=dict,
        description="Cómo se agregó cada valor, p. ej. {'tipo': 'suma_temporada', 'meses': [12, 1, 2, 3]}.",
    )
    descripcion: str = Field(min_length=5, max_length=2000)
    procedencia: Procedencia

    @field_validator("unidad")
    @classmethod
    def _unidad_valida(cls, valor: str) -> str:
        if not es_unidad_valida(valor):
            raise ValueError(f"Unidad '{valor}' fuera del vocabulario controlado.")
        return valor


class SerieSalida(Esquema):
    id: str
    dominio_id: str
    unidad_id: str | None
    variable_id: str
    fuente_id: str
    unidad: str
    frecuencia: Frecuencia
    agregacion: dict[str, Any]
    descripcion: str
    procedencia: Procedencia
    version: int
    t_inicio: date | None
    t_fin: date | None
    n_observaciones: int
    creado_en: datetime
    actualizado_en: datetime


class ObservacionEntrada(Esquema):
    t: date = Field(description="Inicio del periodo que representa el valor (ISO 8601).")
    valor: NumeroFinitoOpcional = Field(None, description="null = sin dato válido (nunca interpolado).")
    frac_valida: NumeroFinitoOpcional = Field(None, ge=0, le=1)
    calidad: str | None = Field(None, max_length=20)


class ObservacionesCarga(Esquema):
    observaciones: list[ObservacionEntrada] = Field(min_length=1, max_length=100_000)
    reemplazar: bool = Field(False, description="true = borra las observaciones previas de la serie.")

    @model_validator(mode="after")
    def _fechas_unicas(self) -> ObservacionesCarga:
        fechas = [o.t for o in self.observaciones]
        if len(fechas) != len(set(fechas)):
            raise ValueError("Hay fechas repetidas en la carga.")
        return self


class ResultadoCarga(Esquema):
    serie_id: str
    insertadas: int
    actualizadas: int
    version: int
    t_inicio: date | None
    t_fin: date | None
    n_observaciones: int


class ObservacionSalida(Esquema):
    t: date
    valor: float | None
    frac_valida: float | None
    calidad: str | None


class ObservacionesSalida(Esquema):
    serie_id: str
    unidad: str
    frecuencia: Frecuencia
    version: int
    observaciones: list[ObservacionSalida]
