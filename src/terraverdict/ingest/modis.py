"""Temperatura de superficie MODIS (MOD11A2 v061, compuestos de 8 días a 1 km) por la API pública
de subconjuntos de ORNL DAAC (https://modis.ornl.gov/data/modis_webservice.html). No requiere cuenta.

LST es temperatura de la superficie (piel), no del aire a 2 m: se usa como contraste independiente
de la temperatura de POWER, no como sustituto. La API admite como máximo 10 fechas por consulta.
Valores: entero × 0,02 = kelvin; 0 = sin dato (nubes o calidad insuficiente).
Cada consulta tarda cerca de 1 min en el servidor y la latencia no crece con consultas simultáneas
(medido el 2026-11-15: 8 en paralelo en 49 s), por eso se piden en paralelo, pero con pocos hilos:
con 20 simultáneas el servidor empezó a responder 502.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from .http import sesion
from .manifest import guardar_crudo

BASE = "https://modis.ornl.gov/rst/api/v1"
PRODUCTO = "MOD11A2"
BANDAS = ("LST_Day_1km", "LST_Night_1km")


def descargar(
    nombre: str, lat: float, lon: float, raw: str | Path, desde: str = "2000-01-01", hilos: int = 4
) -> dict[str, Any]:
    s = sesion()
    s.headers["Accept"] = "application/json"
    fechas = s.get(f"{BASE}/{PRODUCTO}/dates", params={"latitude": lat, "longitude": lon}, timeout=180)
    fechas.raise_for_status()
    modis = [f["modis_date"] for f in fechas.json()["dates"] if f["calendar_date"] >= desde]
    salida: dict[str, Any] = {}
    for banda in BANDAS:

        def tramo(i: int, banda: str = banda) -> list[dict[str, Any]]:
            r = s.get(
                f"{BASE}/{PRODUCTO}/subset",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "band": banda,
                    "startDate": modis[i],
                    "endDate": modis[min(i + 9, len(modis) - 1)],
                    "kmAboveBelow": 0,
                    "kmLeftRight": 0,
                },
                timeout=300,
            )
            r.raise_for_status()
            return list(r.json()["subset"])

        with ThreadPoolExecutor(hilos) as ex:
            tramos = [d for bloque in ex.map(tramo, range(0, len(modis), 10)) for d in bloque]
        contenido = json.dumps({"latitud": lat, "longitud": lon, "banda": banda, "subset": tramos}).encode()
        salida[banda] = guardar_crudo(
            raw,
            f"modis_{nombre}_{banda}.json",
            contenido,
            url=f"{BASE}/{PRODUCTO}/subset?latitude={lat}&longitude={lon}&band={banda}",
            producto=PRODUCTO,
            version="061",
            extra={"fechas": len(tramos)},
        )
    return salida


def cargar(carpeta: str | Path, nombre: str, banda: str) -> dict[str, float]:
    """{fecha_iso: °C} del compuesto de 8 días que empieza en esa fecha; sin los valores nulos."""
    j = json.loads((Path(carpeta) / f"modis_{nombre}_{banda}.json").read_text())
    return {
        d["calendar_date"]: round(d["data"][0] * 0.02 - 273.15, 2)
        for d in j["subset"]
        if d["data"] and d["data"][0] > 0
    }
