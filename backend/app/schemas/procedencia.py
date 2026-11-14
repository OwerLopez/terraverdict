"""Procedencia: de dónde viene cada resultado y cómo se calculó (trazabilidad completa)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import Field, StringConstraints, model_validator

from app.schemas.comun import Esquema, Metricas

Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class ReferenciaFuente(Esquema):
    fuente_id: str = Field(description="ID de una fuente del catálogo (GET /fuentes).")
    coleccion: str | None = None
    version: str | None = None
    doi: str | None = None
    url: str | None = None
    consultado_utc: datetime | None = None


class Codigo(Esquema):
    repositorio: str | None = None
    commit: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{7,40}$")] | None = None
    script: str | None = None


class Paso(Esquema):
    """Un paso del proceso que produjo el resultado; alimenta el grafo "Cómo llegué a esto"."""

    id: Annotated[str, StringConstraints(pattern=r"^[a-z0-9_]{2,40}$")]
    nombre: Annotated[str, StringConstraints(min_length=2, max_length=120)]
    descripcion: str | None = None
    entradas: list[str] = Field(default_factory=list, description="IDs de pasos o datos previos.")
    salidas: list[str] = Field(default_factory=list)
    metricas: Metricas = Field(default_factory=dict)


class Procedencia(Esquema):
    fuentes: list[ReferenciaFuente] = Field(min_length=1)
    codigo: Codigo | None = None
    preregistro_sha256: Sha256 | None = None
    ejecucion_id: str | None = Field(None, description="ID de la ejecución del pipeline (POST /ejecuciones).")
    hash_entradas: dict[str, Sha256] = Field(default_factory=dict)
    pasos: list[Paso] = Field(default_factory=list)
    generado_utc: datetime

    @model_validator(mode="after")
    def _pasos_coherentes(self) -> Procedencia:
        ids = [p.id for p in self.pasos]
        if len(ids) != len(set(ids)):
            raise ValueError("Los IDs de los pasos deben ser únicos.")
        conocidos = set(ids)
        for paso in self.pasos:
            faltantes = [e for e in paso.entradas if e.startswith("paso:") and e[5:] not in conocidos]
            if faltantes:
                raise ValueError(f"El paso '{paso.id}' referencia pasos inexistentes: {faltantes}")
        return self
