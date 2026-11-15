"""CHIRPS diario (Funk et al., 2015, doi:10.1038/sdata.2015.66) por la API pública de ClimateSERV.

ClimateSERV (NASA-USAID SERVIR, https://climateserv.servirglobal.net) devuelve el promedio areal
de CHIRPS (0,05°) sobre un polígono. No requiere cuenta. Cada consulta admite como máximo 20 años,
por eso se pide por tramos; cada tramo se guarda crudo (JSON) con su SHA-256 en el manifiesto.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .http import sesion
from .manifest import guardar_crudo

BASE = "https://climateserv.servirglobal.net/api"
PRODUCTO = "CHIRPS_DIARIO_CLIMATESERV"
DATATYPE_CHIRPS = 0
OPERACION_PROMEDIO = 5


def caja(lon: float, lat: float, ancho_lon: float, alto_lat: float) -> dict[str, Any]:
    o, e, s, n = lon - ancho_lon / 2, lon + ancho_lon / 2, lat - alto_lat / 2, lat + alto_lat / 2
    return {"type": "Polygon", "coordinates": [[[o, s], [e, s], [e, n], [o, n], [o, s]]]}


def _consultar(s, geometria: dict[str, Any], desde: str, hasta: str, espera_max: int = 900) -> tuple[bytes, str]:
    params = {
        "datatype": DATATYPE_CHIRPS,
        "begintime": desde,
        "endtime": hasta,
        "intervaltype": 0,
        "operationtype": OPERACION_PROMEDIO,
        "geometry": json.dumps(geometria),
    }
    r = s.get(f"{BASE}/submitDataRequest/", params=params, timeout=120)
    r.raise_for_status()
    respuesta = r.json()
    if not isinstance(respuesta, list) or not respuesta:
        raise RuntimeError(f"ClimateSERV rechazó la consulta: {str(respuesta)[:200]}")
    ident = str(respuesta[0])
    inicio = time.monotonic()
    while True:
        progreso = s.get(f"{BASE}/getDataRequestProgress/", params={"id": ident}, timeout=60).json()
        if progreso and float(progreso[0]) >= 100:
            break
        if progreso and float(progreso[0]) < 0:
            raise RuntimeError(f"ClimateSERV informó un error en la consulta {ident}")
        if time.monotonic() - inicio > espera_max:
            raise TimeoutError(f"ClimateSERV no terminó la consulta {ident} en {espera_max} s")
        time.sleep(5)
    datos = s.get(f"{BASE}/getDataFromRequest/", params={"id": ident}, timeout=300)
    datos.raise_for_status()
    if not datos.json().get("data"):
        raise RuntimeError(f"ClimateSERV devolvió una serie vacía para {desde}–{hasta}")
    return datos.content, r.url


def descargar(
    nombre: str,
    geometria: dict[str, Any],
    desde: int,
    hasta: int,
    raw: str | Path,
    tramo_anios: int = 10,
    hasta_fecha: str | None = None,
) -> list[dict[str, Any]]:
    """Serie diaria del promedio areal de CHIRPS sobre `geometria`, de `desde` a `hasta` (años)."""
    s = sesion()
    entradas = []
    for a in range(desde, hasta + 1, tramo_anios):
        b = min(a + tramo_anios - 1, hasta)
        fin = hasta_fecha if b == hasta and hasta_fecha else f"12/31/{b}"
        contenido, url = _consultar(s, geometria, f"01/01/{a}", fin)
        entradas.append(
            guardar_crudo(
                raw,
                f"chirps_{nombre}_{a}_{b}.json",
                contenido,
                url=url,
                producto=PRODUCTO,
                version="CHIRPS v2.0 (datatype 0 de ClimateSERV)",
                extra={"geometria": geometria, "operacion": "promedio areal"},
            )
        )
    return entradas


def cargar(carpeta: str | Path, nombre: str) -> dict[str, float]:
    """{fecha_iso: mm/día}. Los valores negativos (sin dato en ClimateSERV) se descartan."""
    salida: dict[str, float] = {}
    for f in sorted(Path(carpeta).glob(f"chirps_{nombre}_*.json")):
        for d in json.loads(f.read_text())["data"]:
            v = d.get("raw_value")
            if v is None or v < 0:
                continue
            m, dia, a = d["date"].split("/")
            salida[f"{a}-{m}-{dia}"] = float(v)
    return dict(sorted(salida.items()))
