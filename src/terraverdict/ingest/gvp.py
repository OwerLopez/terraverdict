"""Smithsonian Global Volcanism Program (GVP), base Volcanoes of the World, por su servicio WFS.

Capas usadas: volcanes del Holoceno y erupciones del Holoceno. Se filtran por país (Perú).
Cita: Global Volcanism Program (2024). Volcanoes of the World (v. 5.x). Smithsonian Institution.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .http import sesion
from .manifest import guardar_crudo

URL = "https://webservices.volcano.si.edu/geoserver/GVP-VOTW/ows"
PRODUCTO = "SMITHSONIAN_GVP_VOTW"
CAPAS = {
    "volcanes": "GVP-VOTW:Smithsonian_VOTW_Holocene_Volcanoes",
    "erupciones": "GVP-VOTW:Smithsonian_VOTW_Holocene_Eruptions",
}


def _obtener(s: Any, capa: str, filtro: str) -> tuple[bytes, str]:
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": capa,
        "outputFormat": "application/json",
        "CQL_FILTER": filtro,
    }
    r = s.get(URL, params=params, timeout=180)
    r.raise_for_status()
    json.loads(r.content)  # falla aquí si el servicio no devolvió GeoJSON
    return r.content, r.url


def descargar(raw: str | Path, pais: str = "Peru") -> list[dict[str, Any]]:
    """Descarga los volcanes del Holoceno de un país y todas sus erupciones registradas (GeoJSON)."""
    s = sesion()
    contenido, url = _obtener(s, CAPAS["volcanes"], f"Country='{pais}'")
    numeros = [f["properties"]["Volcano_Number"] for f in json.loads(contenido)["features"]]
    entradas = [
        guardar_crudo(
            raw,
            "gvp_volcanes.geojson",
            contenido,
            url=url,
            producto=PRODUCTO,
            extra={"capa": CAPAS["volcanes"], "pais": pais},
        )
    ]
    filtro = "Volcano_Number IN (" + ",".join(str(n) for n in numeros) + ")"
    contenido, url = _obtener(s, CAPAS["erupciones"], filtro)
    entradas.append(
        guardar_crudo(
            raw,
            "gvp_erupciones.geojson",
            contenido,
            url=url,
            producto=PRODUCTO,
            extra={"capa": CAPAS["erupciones"], "volcanes": numeros},
        )
    )
    return entradas


def cargar(carpeta: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    carpeta = Path(carpeta)
    volcanes = [
        f["properties"] | {"coordenadas": f["geometry"]["coordinates"] if f.get("geometry") else None}
        for f in json.loads((carpeta / "gvp_volcanes.geojson").read_text())["features"]
    ]
    erupciones = [f["properties"] for f in json.loads((carpeta / "gvp_erupciones.geojson").read_text())["features"]]
    return volcanes, erupciones
