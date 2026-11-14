"""Carga del preregistro (con su hash) y de la configuración de cuenca."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Preregistro:
    datos: dict[str, Any]
    sha256: str

    @property
    def alpha(self) -> float:
        return float(self.datos["alpha"])

    @property
    def ic_nivel(self) -> float:
        return float(self.datos["ic_nivel"])

    @property
    def L_min(self) -> int:
        return int(self.datos["ventanas"]["L_min"])

    @property
    def u_ventanas(self) -> float:
        return float(self.datos["ventanas"]["u_ventanas"])

    @property
    def tol_sensor(self) -> float:
        return float(self.datos["sensor"]["tol_cambio_pendiente"])

    @property
    def min_familias(self) -> int:
        return int(self.datos["independencia"]["min_familias_mismo_signo"])

    def quiebres(self, producto: str) -> dict[str, float]:
        return dict(self.datos["sensor"]["quiebres_por_producto"].get(producto, {}))

    @property
    def palanca_n(self) -> int:
        return int(self.datos["palanca"]["quitar_ultimos_anios"])


def cargar_preregistro(ruta: str | Path = "preregistro.yaml") -> Preregistro:
    raw = Path(ruta).read_bytes()
    return Preregistro(yaml.safe_load(raw), hashlib.sha256(raw).hexdigest())


def cargar_yaml(ruta: str | Path) -> dict[str, Any]:
    return yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))
