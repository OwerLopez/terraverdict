"""NASA Global Landslide Catalog (GLC), exportación pública en data.nasa.gov.

Kirschbaum, D. B. et al. (2010), Nat. Hazards 52, 561–575, doi:10.1007/s11069-009-9401-4;
Kirschbaum, D. B. et al. (2015), Geomorphology 249, 4–15, doi:10.1016/j.geomorph.2015.03.016.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any

from .http import sesion
from .manifest import guardar_crudo

URL = "https://data.nasa.gov/docs/legacy/Global_Landslide_Catalog_Export/Global_Landslide_Catalog_Export_rows.csv"
PRODUCTO = "NASA_GLC"


def descargar(raw: str | Path) -> dict[str, Any]:
    r = sesion().get(URL, timeout=300)
    r.raise_for_status()
    return guardar_crudo(raw, "glc.csv", r.content, url=URL, producto=PRODUCTO)


def cargar(carpeta: str | Path, pais: str = "Peru") -> list[dict[str, Any]]:
    texto = (Path(carpeta) / "glc.csv").read_text(encoding="utf-8", errors="replace")
    salida = []
    for fila in csv.DictReader(io.StringIO(texto)):
        if fila.get("country_name") != pais:
            continue
        try:
            salida.append(
                {
                    "id": fila.get("event_id"),
                    "fecha": fila.get("event_date"),
                    "lat": float(fila["latitude"]),
                    "lon": float(fila["longitude"]),
                    "region": fila.get("admin_division_name"),
                    "lugar": fila.get("location_description"),
                    "precision": fila.get("location_accuracy"),
                    "categoria": fila.get("landslide_category"),
                    "detonante": fila.get("landslide_trigger"),
                    "tamano": fila.get("landslide_size"),
                    "muertes": fila.get("fatality_count"),
                    "fuente": fila.get("source_name"),
                    "enlace": fila.get("source_link"),
                }
            )
        except (KeyError, ValueError):
            continue
    return sorted(salida, key=lambda e: e["fecha"] or "")
