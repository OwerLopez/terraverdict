"""Toda descarga guarda el crudo + hash + manifiesto. Permite correr offline sobre data/raw."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def guardar_crudo(carpeta: str | Path, nombre: str, contenido: bytes, *, url: str,
                  producto: str, version: str | None = None, extra: dict | None = None) -> dict:
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / nombre).write_bytes(contenido)
    entrada = {"archivo": nombre, "sha256": sha256_bytes(contenido), "bytes": len(contenido), "url": url,
               "producto": producto, "version": version,
               "descargado_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), **(extra or {})}
    man = carpeta / "manifiesto.json"
    lista = json.loads(man.read_text()) if man.exists() else []
    lista = [e for e in lista if e["archivo"] != nombre] + [entrada]
    man.write_text(json.dumps(lista, indent=1, ensure_ascii=False))
    return entrada
