from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .http import sesion
from .manifest import guardar_crudo

URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"
URL_DIARIO = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMETROS_DIARIOS = "PRECTOTCORR,T2M,T2M_MAX,T2M_MIN,RH2M,QV2M,WS2M,PS,ALLSKY_SFC_SW_DWN"


def descargar(
    lon: float, lat: float, inicio: int, fin: int, raw: str | Path, parametros: str = "T2M,PRECTOTCORR"
) -> dict:
    params: dict[str, Any] = {
        "parameters": parametros,
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": inicio,
        "end": fin,
        "format": "JSON",
    }
    r = sesion().get(URL, params=params, timeout=180)
    r.raise_for_status()
    return guardar_crudo(
        raw,
        f"power_{lon}_{lat}_{inicio}_{fin}.json",
        r.content,
        url=r.url,
        producto="NASA_POWER_MERRA2",
        extra={"parametros": parametros},
    )


def cargar(archivo: str | Path) -> tuple[dict, dict]:
    j = json.loads(Path(archivo).read_text())
    return j["properties"]["parameter"], {
        "fuentes": j["header"].get("sources"),
        "elevacion_celda_m": j["geometry"]["coordinates"][2],
    }


def descargar_diario(
    lon: float, lat: float, inicio: str, fin: str, raw: str | Path, nombre: str, parametros: str = PARAMETROS_DIARIOS
) -> dict:
    """Serie diaria por punto (inicio/fin en AAAAMMDD). POWER marca los faltantes con -999."""
    params: dict[str, Any] = {
        "parameters": parametros,
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": inicio,
        "end": fin,
        "format": "JSON",
    }
    r = sesion().get(URL_DIARIO, params=params, timeout=300)
    r.raise_for_status()
    return guardar_crudo(
        raw,
        f"power_diario_{nombre}.json",
        r.content,
        url=r.url,
        producto="NASA_POWER_MERRA2",
        extra={"parametros": parametros, "punto": nombre},
    )
