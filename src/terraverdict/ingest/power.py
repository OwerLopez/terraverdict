from __future__ import annotations

import json
from pathlib import Path

from .http import sesion
from .manifest import guardar_crudo

URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"


def descargar(lon: float, lat: float, inicio: int, fin: int, raw: str | Path,
              parametros: str = "T2M,PRECTOTCORR") -> dict:
    params = {"parameters": parametros, "community": "AG", "longitude": lon, "latitude": lat,
              "start": inicio, "end": fin, "format": "JSON"}
    r = sesion().get(URL, params=params, timeout=180)
    r.raise_for_status()
    return guardar_crudo(raw, f"power_{lon}_{lat}_{inicio}_{fin}.json", r.content, url=r.url,
                         producto="NASA_POWER_MERRA2", extra={"parametros": parametros})


def cargar(archivo: str | Path) -> tuple[dict, dict]:
    j = json.loads(Path(archivo).read_text())
    return j["properties"]["parameter"], {"fuentes": j["header"].get("sources"),
                                         "elevacion_celda_m": j["geometry"]["coordinates"][2]}
