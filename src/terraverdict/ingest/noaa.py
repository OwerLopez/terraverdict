from __future__ import annotations

from pathlib import Path

from .http import sesion
from .manifest import guardar_crudo

URL_ONI = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"


def descargar_oni(raw: str | Path) -> dict:
    r = sesion().get(URL_ONI, timeout=60)
    r.raise_for_status()
    return guardar_crudo(raw, "oni.ascii.txt", r.content, url=URL_ONI, producto="NOAA_CPC_ONI")


def cargar_oni(archivo: str | Path) -> dict[int, float]:
    """ONI de DJF indexado por el año de enero-febrero (igual que el análisis preliminar)."""
    filas = Path(archivo).read_text().strip().splitlines()[1:]
    return {int(p[1]): float(p[3]) for p in (linea.split() for linea in filas) if p[0] == "DJF"}


def clasificar_enso(oni_djf: float) -> str:
    return "nino_fuerte" if oni_djf >= 1.5 else "nino" if oni_djf >= 0.5 else "nina" if oni_djf <= -0.5 else "neutro"
