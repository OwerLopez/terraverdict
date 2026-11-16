from __future__ import annotations

from pathlib import Path

from .http import sesion
from .manifest import guardar_crudo

URL_ONI = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
# Índices mensuales de TSM (OISST v2.1, anomalías respecto de 1991–2020): Niño 1+2, 3, 4 y 3.4.
URL_NINO_MENSUAL = "https://www.cpc.ncep.noaa.gov/data/indices/sstoi.indices"
COLUMNAS_NINO = ("YR", "MON", "NINO1+2", "ANOM", "NINO3", "ANOM", "NINO4", "ANOM", "NINO3.4", "ANOM")


def descargar_oni(raw: str | Path) -> dict:
    r = sesion().get(URL_ONI, timeout=60)
    r.raise_for_status()
    return guardar_crudo(raw, "oni.ascii.txt", r.content, url=URL_ONI, producto="NOAA_CPC_ONI")


def validar_nino_mensual(contenido: bytes) -> int:
    """Comprueba la cabecera y que cada fila tenga año, mes y 8 valores numéricos; devuelve las filas.

    Así una página de error o un cambio de formato no entra en data/raw como si fuera el índice.
    """
    lineas = contenido.decode("utf-8").strip().splitlines()
    if not lineas or tuple(lineas[0].split()) != COLUMNAS_NINO:
        raise ValueError(f"Cabecera inesperada en sstoi.indices: {lineas[0] if lineas else '(vacío)'}")
    filas = 0
    for linea in lineas[1:]:
        p = linea.split()
        if len(p) != 10 or not (1950 <= int(p[0]) <= 2100 and 1 <= int(p[1]) <= 12):
            raise ValueError(f"Fila inválida en sstoi.indices: {linea}")
        [float(x) for x in p[2:]]
        filas += 1
    return filas


def descargar_nino_mensual(raw: str | Path) -> dict:
    """Anomalías mensuales de Niño 3.4 y Niño 1+2 (NOAA CPC, OISST v2.1): más recientes que el ONI."""
    r = sesion().get(URL_NINO_MENSUAL, timeout=60)
    r.raise_for_status()
    filas = validar_nino_mensual(r.content)
    return guardar_crudo(
        raw, "sstoi.indices", r.content, url=URL_NINO_MENSUAL, producto="NOAA_CPC_OISST_NINO", version="v2.1",
        extra={"filas": filas, "base_anomalias": "1991-2020"},
    )


def cargar_oni(archivo: str | Path) -> dict[int, float]:
    """ONI de DJF indexado por el año de enero-febrero (igual que el análisis preliminar)."""
    filas = Path(archivo).read_text(encoding="utf-8").strip().splitlines()[1:]
    return {int(p[1]): float(p[3]) for p in (linea.split() for linea in filas) if p[0] == "DJF"}


def clasificar_enso(oni_djf: float) -> str:
    return "nino_fuerte" if oni_djf >= 1.5 else "nino" if oni_djf >= 0.5 else "nina" if oni_djf <= -0.5 else "neutro"
