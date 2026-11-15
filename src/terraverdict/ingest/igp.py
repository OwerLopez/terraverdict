"""Sismos reportados por el IGP (Centro Sismológico Nacional) desde su API pública por año.

Fuente: https://ultimosismo.igp.gob.pe/api/ultimo-sismo/ajaxb/{año}. Es la lista de sismos que el
IGP reporta (no su catálogo completo de detección), disponible desde 2012. Las fechas vienen en
hora local de Perú (UTC−5), sin horario de verano. Cada año se guarda crudo con su SHA-256.
Hasta 2018 los registros no traen `codigo`; el identificador estable es `idlistasismos`.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

from .http import sesion
from .manifest import guardar_crudo

URL = "https://ultimosismo.igp.gob.pe/api/ultimo-sismo/ajaxb/{anio}"
PRODUCTO = "IGP_SISMOS_REPORTADOS"
UTC_LOCAL = dt.timedelta(hours=-5)


def descargar(desde: int, hasta: int, raw: str | Path) -> list[dict[str, Any]]:
    s = sesion()
    entradas = []
    for anio in range(desde, hasta + 1):
        r = s.get(URL.format(anio=anio), timeout=120)
        r.raise_for_status()
        if not isinstance(r.json(), list):  # años sin datos: {"error": "No se encontraron sismos..."}
            continue
        entradas.append(guardar_crudo(raw, f"igp_{anio}.json", r.content, url=r.url, producto=PRODUCTO))
    if not entradas:
        raise RuntimeError(f"El IGP no devolvió sismos entre {desde} y {hasta}")
    return entradas


def cargar(carpeta: str | Path) -> list[dict[str, Any]]:
    """Eventos con tiempo en UTC (ISO), lat, lon, profundidad (km) y magnitud; sin duplicados."""
    eventos: dict[str, dict[str, Any]] = {}
    for f in sorted(Path(carpeta).glob("igp_*.json")):
        for e in json.loads(f.read_text()):
            try:
                fecha = dt.date.fromisoformat(e["fecha_local"][:10])
                hora = dt.time.fromisoformat(e["hora_local"][11:19])
                utc = dt.datetime.combine(fecha, hora) - UTC_LOCAL
                ident = str(e.get("codigo") or f"igp-{e['idlistasismos']}")  # 'codigo' existe desde 2019
                eventos[ident] = {
                    "id": ident,
                    "tiempo": utc.isoformat(),
                    "lat": float(e["latitud"]),
                    "lon": float(e["longitud"]),
                    "profundidad_km": float(e["profundidad"]),
                    "magnitud": float(e["magnitud"]),
                    "tipo_magnitud": e.get("tipomagnitud") or None,
                    "referencia": e.get("referencia"),
                }
            except (KeyError, TypeError, ValueError):
                continue
    return sorted(eventos.values(), key=lambda e: e["tiempo"])
