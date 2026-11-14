from __future__ import annotations

import datetime as dt
import subprocess
from pathlib import Path

import numpy as np

from ..config import Preregistro
from ..contracts.expediente import Expediente, Procedencia
from .hash import sha256_json


def _commit() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return None


def construir_expediente(*, id: str, objeto: dict, variable: str, anios, valores, resultado: dict,
                         productos: list[dict], pre: Preregistro,
                         advertencias: list[str] | None = None) -> Expediente:
    entradas = {"variable": variable, "anios": np.asarray(anios), "valores": np.asarray(valores),
                "preregistro": pre.sha256}
    adv = list(advertencias or [])
    if (resultado.get("independencia") is None):
        adv.append("Una sola familia de datos: la prueba de independencia no se evaluó.")
    return Expediente(
        id=id, tipo="tendencia", objeto={**objeto, "variable": variable},
        periodo={"desde": resultado["periodo"][0], "hasta": resultado["periodo"][1], "n": resultado["n"]},
        resultado=resultado, serie={str(int(a)): float(v) for a, v in zip(anios, valores)}, veredicto=resultado["sello"]["codigo"], advertencias=adv,
        procedencia=Procedencia(productos=productos, preregistro_sha256=pre.sha256,
                                codigo_commit=_commit(), entradas_sha256=sha256_json(entradas),
                                generado_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")))


def guardar(exp: Expediente, carpeta: str | Path) -> Path:
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"{exp.id}.json"
    ruta.write_text(exp.model_dump_json(indent=1), encoding="utf-8")
    return ruta
