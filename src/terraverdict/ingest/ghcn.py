"""NOAA GHCN-Daily por estación (Menne et al., 2012, doi:10.1175/JTECH-D-11-00103.1).

Valores en décimas (PRCP en décimas de mm, TMAX/TMIN en décimas de °C). Las observaciones con
bandera de calidad (QFLAG) no vacía se descartan, como recomienda la documentación de GHCN.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any

from .http import sesion
from .manifest import guardar_crudo

URL = "https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/{estacion}.csv"
PRODUCTO = "NOAA_GHCN_DAILY"


def descargar(estacion: str, raw: str | Path) -> dict[str, Any]:
    url = URL.format(estacion=estacion)
    r = sesion().get(url, timeout=180)
    r.raise_for_status()
    return guardar_crudo(raw, f"ghcn_{estacion}.csv", r.content, url=url, producto=PRODUCTO)


def cargar(carpeta: str | Path, estacion: str) -> dict[str, dict[str, float]]:
    """Devuelve {variable: {fecha_iso: valor}} con PRCP en mm y temperaturas en °C."""
    texto = (Path(carpeta) / f"ghcn_{estacion}.csv").read_text(encoding="utf-8")
    salida: dict[str, dict[str, float]] = {"PRCP": {}, "TMAX": {}, "TMIN": {}}
    for fila in csv.DictReader(io.StringIO(texto)):
        for var, valores in salida.items():
            valor = (fila.get(var) or "").strip()
            atributos = (fila.get(f"{var}_ATTRIBUTES") or "").split(",")
            qflag = atributos[1].strip() if len(atributos) > 1 else ""
            if valor and not qflag:
                valores[fila["DATE"]] = int(valor) / 10.0
    return salida
