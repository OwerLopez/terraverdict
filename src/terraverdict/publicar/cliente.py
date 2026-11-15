"""Publicación de expedientes en el backend con una clave de servicio de alcance `ingesta` (ADR-020).

`POST /api/v1/expedientes` es idempotente por hash de contenido: el mismo contenido devuelve 200
con el expediente existente; uno nuevo, 201. Un 422 (regla científica o de contrato violada) no se
reintenta ni se corrige: se informa con el detalle del backend.
"""

from __future__ import annotations

import os
from typing import Any

import requests

from ..ingest.http import sesion


def clave_ingesta() -> str:
    clave = os.environ.get("TV_CLAVE_INGESTA")
    if not clave:
        raise RuntimeError("Falta TV_CLAVE_INGESTA (clave API de alcance 'ingesta': python -m app.cli crear-clave)")
    return clave


def publicar(
    expedientes: list[dict[str, Any]], api: str, clave: str, s: requests.Session | None = None
) -> list[dict[str, Any]]:
    s = s or sesion(reintentos=2)
    s.headers["X-API-Key"] = clave
    salida = []
    for e in expedientes:
        r = s.post(f"{api.rstrip('/')}/api/v1/expedientes", json=e, timeout=120)
        cuerpo = r.json() if r.headers.get("content-type", "").endswith("json") else {"texto": r.text[:500]}
        salida.append(
            {
                "titulo": e["titulo"],
                "tipo": e["resultado"]["tipo"],
                "http": r.status_code,
                "estado": {201: "creado", 200: "ya_existia"}.get(r.status_code, "error"),
                "id": cuerpo.get("id"),
                "errores": cuerpo.get("errores") if r.status_code >= 400 else None,
            }
        )
    return salida
