"""Orquestador reproducible de todos los experimentos.

Escribe un JSON por experimento en ``resultados/`` con su procedencia completa: hash SHA-256 de
cada crudo usado (manifiestos de data/raw), commit del código, hash de la configuración,
versiones de las bibliotecas y tiempos. Uso: ``tv experimentos [--rapido]``.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import platform
import subprocess
import time
from pathlib import Path
from typing import Any

import numpy as np

from ..config import cargar_yaml
from . import caos_real, deslizamientos, lluvia, sequia, sismos, volcanes

RAIZ = Path(__file__).resolve().parents[3]


def _json(o: Any) -> Any:
    if isinstance(o, dict):
        return {str(k): _json(v) for k, v in o.items() if not str(k).startswith("_")}
    if isinstance(o, (list, tuple)):
        return [_json(v) for v in o]
    if isinstance(o, np.ndarray):
        return _json(o.tolist())
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else round(float(o), 6)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


def procedencia(raw: Path, config: Path) -> dict[str, Any]:
    import sklearn
    import torch

    manifiestos = {}
    for m in sorted(raw.glob("*/manifiesto.json")):
        manifiestos[m.parent.name] = [
            {k: e[k] for k in ("archivo", "sha256", "url", "descargado_utc") if k in e}
            for e in json.loads(m.read_text())
        ]
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True, cwd=RAIZ
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    return {
        "generado_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "commit": commit,
        "config_sha256": hashlib.sha256(config.read_bytes()).hexdigest(),
        "crudos": manifiestos,
        "versiones": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "torch": torch.__version__,
            "scikit_learn": sklearn.__version__,
        },
    }


def ejecutar(
    raw: Path = RAIZ / "data" / "raw",
    salida: Path = RAIZ / "resultados",
    rapido: bool = False,
    solo: list[str] | None = None,
) -> dict[str, Any]:
    config = RAIZ / "config" / "fenomenos.yaml"
    cfg = cargar_yaml(config)
    salida.mkdir(parents=True, exist_ok=True)
    proc = procedencia(raw, config)
    redes = ["gru", "tcn"] if rapido else None
    semillas = (0,) if rapido else None
    tiempos: dict[str, float] = {}
    hechos: dict[str, Any] = {}

    def correr(nombre: str, funcion) -> Any:
        if solo and nombre not in solo:
            return None
        t = time.perf_counter()
        print(f"== {nombre}")
        r = funcion()
        tiempos[nombre] = round(time.perf_counter() - t, 1)
        r["procedencia"] = {**proc, "segundos": tiempos[nombre], "modo": "rapido" if rapido else "completo"}
        (salida / f"{nombre}.json").write_text(json.dumps(_json(r), ensure_ascii=False, indent=1), encoding="utf-8")
        hechos[nombre] = r
        return r

    opciones: dict[str, Any] = {}
    if redes is not None:
        opciones["redes"] = redes
    if semillas is not None:
        opciones["semillas"] = semillas
    correr("volcanes", lambda: volcanes.ejecutar(cfg, raw))
    correr("deslizamientos", lambda: deslizamientos.ejecutar(cfg, raw))
    rs = correr("sismos", lambda: sismos.ejecutar(cfg, raw, **opciones))
    correr("sequia", lambda: sequia.ejecutar(cfg, raw, **opciones))
    correr("lluvia_extrema", lambda: lluvia.ejecutar(cfg, raw, **opciones))
    if rs is None and (not solo or "caos" in solo):
        rs = sismos.ejecutar(cfg, raw, redes=[], semillas=(0,))
    correr("caos", lambda: caos_real.ejecutar(cfg, raw, rs))
    indice = {
        "generado_utc": proc["generado_utc"],
        "commit": proc["commit"],
        "tiempos_segundos": tiempos,
        "experimentos": sorted(p.stem for p in salida.glob("*.json") if p.stem != "indice"),
    }
    (salida / "indice.json").write_text(json.dumps(indice, ensure_ascii=False, indent=1), encoding="utf-8")
    return indice
