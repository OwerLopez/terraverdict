"""Registro estructurado en JSON con el identificador de solicitud de cada petición."""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)

_ATRIBUTOS_ESTANDAR = set(vars(logging.makeLogRecord({})).keys()) | {"message", "asctime"}


def request_id_actual() -> str | None:
    return _request_id.get()


def fijar_request_id(valor: str | None) -> object:
    return _request_id.set(valor)


def restaurar_request_id(token: object) -> None:
    _request_id.reset(token)  # type: ignore[arg-type]


class FormatoJSON(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        datos = {
            "t": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "nivel": record.levelname,
            "logger": record.name,
            "mensaje": record.getMessage(),
            "request_id": request_id_actual(),
        }
        for clave, valor in record.__dict__.items():
            if clave not in _ATRIBUTOS_ESTANDAR and not clave.startswith("_"):
                datos[clave] = valor
        if record.exc_info:
            datos["excepcion"] = self.formatException(record.exc_info)
        return json.dumps(datos, ensure_ascii=False, default=str)


def configurar_logging(nivel: str = "INFO") -> None:
    raiz = logging.getLogger("terraverdict")
    if any(isinstance(h.formatter, FormatoJSON) for h in raiz.handlers):
        raiz.setLevel(nivel)
        return
    manejador = logging.StreamHandler(sys.stdout)
    manejador.setFormatter(FormatoJSON())
    raiz.addHandler(manejador)
    raiz.setLevel(nivel)
    raiz.propagate = False
