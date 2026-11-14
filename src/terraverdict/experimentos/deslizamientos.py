"""Experimento: lluvia antecedente de los deslizamientos del sur del Perú (NASA GLC + POWER).

Para cada deslizamiento detonado por lluvia: lluvia acumulada de 1, 3, 10 y 30 días hasta el día
del evento en su celda POWER, y su percentil frente a todos los días del mismo mes en esa celda.
Un umbral empírico (Guzzetti et al., 2008, doi:10.1007/s10346-007-0112-1) solo se estima con al
menos `eventos_minimos_umbral` eventos; con menos, el sistema se abstiene y lo explica.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..ingest import glc
from ..ingest.fenomenos import celdas_power

DURACIONES = (1, 3, 10, 30)


def ejecutar(cfg: dict[str, Any], raw: Path, registro=print) -> dict[str, Any]:
    caja = cfg["fenomenos"]["deslizamientos"]["dominio_bbox"]
    minimo = cfg["abstencion"]["eventos_minimos_umbral"]
    todos = glc.cargar(raw / "glc")
    eventos = [e for e in todos if caja[0] <= e["lon"] <= caja[2] and caja[1] <= e["lat"] <= caja[3]]
    por_lluvia = [
        e for e in eventos if e["detonante"] in ("downpour", "rain", "continuous_rain", "monsoon", "tropical_cyclone")
    ]
    filas = []
    for e in por_lluvia:
        lon, lat = celdas_power(e["lon"], e["lat"])
        ruta = raw / "power_celdas" / f"power_diario_celda_{lon}_{lat}.json"
        if not ruta.exists():
            continue
        serie = pd.Series(json.loads(ruta.read_text())["properties"]["parameter"]["PRECTOTCORR"])
        serie.index = pd.to_datetime(serie.index, format="%Y%m%d")
        serie = serie.where(serie >= 0)
        fecha = pd.to_datetime(e["fecha"], format="%m/%d/%Y %I:%M:%S %p").normalize()
        fila: dict[str, Any] = {
            "id": e["id"],
            "fecha": str(fecha.date()),
            "lat": e["lat"],
            "lon": e["lon"],
            "region": e["region"],
            "lugar": e["lugar"],
            "precision_ubicacion": e["precision"],
            "detonante": e["detonante"],
            "categoria": e["categoria"],
            "muertes": e["muertes"],
        }
        for dias in DURACIONES:
            acumulada = serie.rolling(dias).sum()
            valor = acumulada.get(fecha, np.nan)
            mismo_mes = acumulada[acumulada.index.month == fecha.month].dropna()
            fila[f"lluvia_{dias}d_mm"] = None if not np.isfinite(valor) else float(valor)
            fila[f"percentil_{dias}d"] = None if not np.isfinite(valor) else float((mismo_mes < valor).mean() * 100)
        filas.append(fila)
    n = len(filas)
    resumen = {}
    for dias in DURACIONES:
        pct = np.array([f[f"percentil_{dias}d"] for f in filas if f[f"percentil_{dias}d"] is not None])
        resumen[f"{dias}d"] = {
            "mediana_percentil": float(np.median(pct)) if len(pct) else None,
            "fraccion_sobre_p75": float((pct > 75).mean()) if len(pct) else None,
        }
    abst = {
        "publicar": n >= minimo,
        "abstencion": n < minimo,
        "motivos": []
        if n >= minimo
        else [
            f"Solo {n} deslizamientos detonados por lluvia en el dominio: se necesitan al menos {minimo} para estimar un umbral de lluvia."
        ],
        "advertencias": [
            "El catálogo GLC se basa en noticias: subregistra eventos rurales y su cobertura principal es 2007–2017."
        ],
    }
    registro(
        f"deslizamientos: {len(eventos)} en el dominio, {n} por lluvia con serie de lluvia; abstención={abst['abstencion']}"
    )
    return {
        "fenomeno": "deslizamientos",
        "tarea": "lluvia_antecedente",
        "fuente": "NASA Global Landslide Catalog + NASA POWER",
        "dominio_bbox": caja,
        "eventos_peru": len(todos),
        "eventos_dominio": len(eventos),
        "eventos_por_lluvia_analizados": n,
        "regiones": pd.Series([e["region"] for e in eventos]).value_counts().to_dict(),
        "resumen_percentiles": resumen,
        "eventos": filas,
        "abstencion": abst,
        "umbral": None if n < minimo else "pendiente de implementar con n suficiente",
    }
