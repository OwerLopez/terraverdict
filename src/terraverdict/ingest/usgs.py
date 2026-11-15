"""Catálogo sísmico USGS ComCat por el servicio FDSN (https://earthquake.usgs.gov/fdsnws/event/1/).

Se consulta por tramos de años porque el servicio limita cada respuesta a 20 000 eventos.
Cada tramo se guarda crudo (CSV) con su SHA-256 en el manifiesto.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any

from .http import sesion
from .manifest import guardar_crudo

URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
PRODUCTO = "USGS_COMCAT"


def descargar(
    lat: float,
    lon: float,
    radio_km: float,
    desde: int,
    hasta: int,
    raw: str | Path,
    mag_min: float = 4.0,
    tramo_anios: int = 5,
) -> list[dict[str, Any]]:
    """Descarga los eventos con magnitud >= mag_min a menos de radio_km del punto, de desde a hasta."""
    s = sesion()
    entradas = []
    for a in range(desde, hasta + 1, tramo_anios):
        b = min(a + tramo_anios - 1, hasta)
        params: dict[str, Any] = {
            "format": "csv",
            "starttime": f"{a}-01-01",
            "endtime": f"{b}-12-31T23:59:59",
            "latitude": lat,
            "longitude": lon,
            "maxradiuskm": radio_km,
            "minmagnitude": mag_min,
            "orderby": "time-asc",
        }
        r = s.get(URL, params=params, timeout=180)
        r.raise_for_status()
        entradas.append(
            guardar_crudo(
                raw,
                f"usgs_{a}_{b}.csv",
                r.content,
                url=r.url,
                producto=PRODUCTO,
                extra={"radio_km": radio_km, "mag_min": mag_min},
            )
        )
    return entradas


def descargar_caja(
    bbox: list[float], desde: int, hasta: int, raw: str | Path, mag_min: float = 4.5, tramo_anios: int = 5
) -> list[dict[str, Any]]:
    """Igual que `descargar`, pero por caja geográfica [lon_min, lat_min, lon_max, lat_max] (escala nacional)."""
    s = sesion()
    entradas = []
    for a in range(desde, hasta + 1, tramo_anios):
        b = min(a + tramo_anios - 1, hasta)
        params: dict[str, Any] = {
            "format": "csv",
            "starttime": f"{a}-01-01",
            "endtime": f"{b}-12-31T23:59:59",
            "minlongitude": bbox[0],
            "minlatitude": bbox[1],
            "maxlongitude": bbox[2],
            "maxlatitude": bbox[3],
            "minmagnitude": mag_min,
            "orderby": "time-asc",
        }
        r = s.get(URL, params=params, timeout=180)
        r.raise_for_status()
        entradas.append(
            guardar_crudo(
                raw,
                f"usgs_{a}_{b}.csv",
                r.content,
                url=r.url,
                producto=PRODUCTO,
                extra={"bbox": bbox, "mag_min": mag_min},
            )
        )
    return entradas


def cargar(carpeta: str | Path) -> list[dict[str, Any]]:
    """Une los tramos, elimina duplicados por id y ordena por tiempo."""
    eventos: dict[str, dict[str, Any]] = {}
    for f in sorted(Path(carpeta).glob("usgs_*.csv")):
        for fila in csv.DictReader(io.StringIO(f.read_text(encoding="utf-8"))):
            if fila.get("type") not in (None, "", "earthquake"):
                continue
            try:
                eventos[fila["id"]] = {
                    "id": fila["id"],
                    "tiempo": fila["time"],
                    "lat": float(fila["latitude"]),
                    "lon": float(fila["longitude"]),
                    "profundidad_km": float(fila["depth"] or "nan"),
                    "magnitud": float(fila["mag"]),
                    "tipo_magnitud": fila["magType"],
                    "red": fila["net"],
                    "lugar": fila["place"],
                    "estado": fila["status"],
                }
            except (KeyError, ValueError):
                continue
    return sorted(eventos.values(), key=lambda e: e["tiempo"])
