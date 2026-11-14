"""Expediente inmutable: resultado + procedencia + hash de entradas."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel

SCHEMA_VERSION = "0.1"


class Procedencia(BaseModel):
    productos: list[dict[str, Any]]
    preregistro_sha256: str
    codigo_commit: str | None = None
    entradas_sha256: str
    generado_utc: str


class Expediente(BaseModel):
    schema_version: str = SCHEMA_VERSION
    id: str
    tipo: str                       # "tendencia" | "relevancia" | "atribucion" | "pronostico" | ...
    objeto: dict[str, Any]
    periodo: dict[str, Any]
    resultado: dict[str, Any]
    veredicto: str
    serie: dict[str, float] = {}      # {año: valor} para graficar; la trazabilidad la da entradas_sha256
    advertencias: list[str] = []
    procedencia: Procedencia


if __name__ == "__main__":   # python -m terraverdict.contracts.expediente > web/src/schema.json
    import json
    print(json.dumps(Expediente.model_json_schema(), indent=1))
