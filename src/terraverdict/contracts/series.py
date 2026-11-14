"""Contrato de una serie (sección 4.2 del diseño). Un contrato roto DETIENE el pipeline."""
from __future__ import annotations

import math
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

UNIDADES = {"mm/mes", "mm/dia", "mm", "K", "C", "km2", "hm3", "m3/s", "1"}
CENTINELAS = {-9999.0, -999.0, -99.0}


class Serie(BaseModel):
    variable: str
    producto: str
    version: str
    doi: str | None = None
    familia: str
    unidad: str
    frecuencia: Literal["anual", "mensual", "diaria"]
    fechas: list[date]
    valores: list[float | None]
    frac_valida: list[float] | None = None

    @field_validator("unidad")
    @classmethod
    def _unidad(cls, v: str) -> str:
        if v not in UNIDADES:
            raise ValueError(f"unidad '{v}' fuera del vocabulario controlado {sorted(UNIDADES)}")
        return v

    @model_validator(mode="after")
    def _coherencia(self) -> "Serie":
        if len(self.fechas) != len(self.valores):
            raise ValueError("fechas y valores deben tener la misma longitud")
        if self.fechas != sorted(set(self.fechas)):
            raise ValueError("fechas deben ser únicas y ordenadas")
        if self.frac_valida is not None:
            if len(self.frac_valida) != len(self.valores) or any(not 0 <= f <= 1 for f in self.frac_valida):
                raise ValueError("frac_valida debe estar en [0,1] y alinearse con valores")
        for v in self.valores:
            if v is not None and (v in CENTINELAS or math.isnan(v)):
                raise ValueError(f"centinela/NaN sin convertir a nulo: {v}")
        return self


def limpiar_centinelas(valores: list[float]) -> list[float | None]:
    return [None if (v in CENTINELAS or math.isnan(v)) else v for v in valores]
