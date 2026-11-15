"""Toda fuente de datos que el pipeline descarga debe tener su licencia y su cita documentadas.

Si se agrega una carpeta nueva en data/raw sin registrarla aquí y en
docs/licencias-y-atribuciones.md, la prueba falla: no se publica nada de una fuente sin atribución.
"""

from __future__ import annotations

import json
from pathlib import Path

import tomllib

RAIZ = Path(__file__).resolve().parents[2]
ATRIBUCIONES = RAIZ / "docs" / "licencias-y-atribuciones.md"

# Carpeta de data/raw -> texto con el que la fuente figura en la tabla de atribuciones.
FUENTE_POR_CARPETA = {
    "power": "NASA POWER",
    "power_celdas": "NASA POWER",
    "power_nacional": "NASA POWER",
    "imerg": "GPM IMERG Final V07",
    "glc": "NASA Global Landslide Catalog",
    "usgs": "USGS ComCat",
    "usgs_nacional": "USGS ComCat",
    "gvp": "Smithsonian GVP",
    "noaa": "NOAA CPC ONI",
    "ghcn": "GHCN-Daily",
    "chirps": "CHIRPS",
    "igp": "IGP",
    "modis": "MODIS LST",
}


def test_cada_fuente_descargada_tiene_atribucion() -> None:
    texto = ATRIBUCIONES.read_text(encoding="utf-8")
    carpetas = sorted(p.parent.name for p in (RAIZ / "data" / "raw").glob("*/manifiesto.json"))
    assert carpetas, "no hay manifiestos en data/raw"
    sin_registro = [c for c in carpetas if c not in FUENTE_POR_CARPETA]
    assert not sin_registro, f"fuentes sin licencia documentada: {sin_registro}"
    sin_fila = [c for c in carpetas if FUENTE_POR_CARPETA[c] not in texto]
    assert not sin_fila, f"fuentes sin fila en licencias-y-atribuciones.md: {sin_fila}"


def test_licencia_del_codigo_es_coherente() -> None:
    assert (RAIZ / "LICENSE").read_text(encoding="utf-8").startswith("MIT License")
    ciencia = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
    backend = tomllib.loads((RAIZ / "backend" / "pyproject.toml").read_text(encoding="utf-8"))
    frontend = json.loads((RAIZ / "frontend" / "package.json").read_text(encoding="utf-8"))
    assert ciencia["project"]["license"] == {"text": "MIT"}
    assert backend["project"]["license"] == {"text": "MIT"}
    assert frontend["license"] == "MIT"
