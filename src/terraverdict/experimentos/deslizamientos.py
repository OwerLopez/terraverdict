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

from ..ingest import glc, ingemmet
from ..ingest.fenomenos import celdas_power

DURACIONES = (1, 3, 10, 30)
CELDA_DENSIDAD = 0.25  # grados


def _km(lat1, lon1, lat2, lon2):
    """Distancia del gran círculo (km) entre un punto y arreglos de puntos."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(a))


LIMITES = Path(__file__).resolve().parents[3] / "frontend" / "public" / "datos" / "peru-departamentos.geojson"


def _dentro(x: np.ndarray, y: np.ndarray, anillo: list[list[float]]) -> np.ndarray:
    """Punto en polígono (regla par-impar), vectorizado sobre los puntos."""
    a = np.asarray(anillo)
    xi, yi, xj, yj = a[:, 0], a[:, 1], np.roll(a[:, 0], 1), np.roll(a[:, 1], 1)
    cruza = ((yi[None, :] > y[:, None]) != (yj[None, :] > y[:, None])) & (
        x[:, None] < (xj - xi)[None, :] * (y[:, None] - yi[None, :]) / ((yj - yi)[None, :] + 1e-15) + xi[None, :]
    )
    return cruza.sum(axis=1) % 2 == 1


def puntos_al_azar_en_peru(caja: list[float], n: int, semilla: int = 0) -> np.ndarray:
    """Puntos uniformes dentro del territorio peruano de la caja (límites Natural Earth, dominio público)."""
    geo = json.loads(LIMITES.read_text(encoding="utf-8"))
    rng = np.random.default_rng(semilla)
    x = rng.uniform(caja[0], caja[2], n * 4)
    y = rng.uniform(caja[1], caja[3], n * 4)
    dentro = np.zeros(len(x), bool)
    for f in geo["features"]:
        for poli in f["geometry"]["coordinates"]:
            dentro |= _dentro(x, y, poli[0]) & ~np.any([_dentro(x, y, h) for h in poli[1:]] or [np.zeros(len(x), bool)], axis=0)
    return np.column_stack([y[dentro], x[dentro]])[:n]


def contraste_ingemmet(eventos_glc: list[dict[str, Any]], raw: Path, caja: list[float]) -> dict[str, Any] | None:
    """Segunda familia de evidencia: inventario de campo de INGEMMET frente al catálogo de noticias GLC.

    No es una comparación temporal (la fecha del inventario es la del levantamiento, no la del evento):
    mide si los deslizamientos reportados por GLC caen donde INGEMMET inventarió movimientos en masa.
    """
    if not (raw / "ingemmet" / "peligros_geologicos.json").exists():
        return None
    todos = ingemmet.cargar(raw / "ingemmet")
    dom = [p for p in todos if caja[0] <= p["lon"] <= caja[2] and caja[1] <= p["lat"] <= caja[3]]
    if not dom:
        return None
    lat = np.array([p["lat"] for p in dom])
    lon = np.array([p["lon"] for p in dom])
    distancias = np.array([float(_km(e["lat"], e["lon"], lat, lon).min()) for e in eventos_glc]) if eventos_glc else np.array([])
    # Línea base: la misma medida para lugares al azar del territorio peruano de la caja. Sin ella,
    # "80 % a menos de 5 km" no dice nada en una región con miles de puntos inventariados.
    azar = puntos_al_azar_en_peru(caja, 2000) if LIMITES.exists() else np.empty((0, 2))
    d_azar = np.array([float(_km(a, b, lat, lon).min()) for a, b in azar])
    p0 = float((d_azar < 5).mean()) if len(d_azar) else None
    k = int((distancias < 5).sum())
    from scipy.stats import binom

    p_valor = float(binom.sf(k - 1, len(distancias), p0)) if p0 is not None and len(distancias) else None
    celdas = pd.DataFrame(
        {"lat": np.floor(lat / CELDA_DENSIDAD) * CELDA_DENSIDAD + CELDA_DENSIDAD / 2, "lon": np.floor(lon / CELDA_DENSIDAD) * CELDA_DENSIDAD + CELDA_DENSIDAD / 2}
    ).value_counts().reset_index(name="n")
    return {
        "fuente": "INGEMMET · GEOCATMIN, inventario de peligros geológicos (movimientos en masa)",
        "servicio": ingemmet.SERVICIO,
        "registros_nacionales": len(todos),
        "registros_dominio": len(dom),
        "por_tipo_dominio": pd.Series([p["tipo"] for p in dom]).value_counts().to_dict(),
        "por_departamento_dominio": pd.Series([p["departamento"] for p in dom]).value_counts().to_dict(),
        "eventos_glc_comparados": len(distancias),
        "distancia_glc_a_ingemmet_km": {
            "mediana": float(np.median(distancias)) if len(distancias) else None,
            "fraccion_menor_5km": float((distancias < 5).mean()) if len(distancias) else None,
            "fraccion_menor_10km": float((distancias < 10).mean()) if len(distancias) else None,
        },
        "linea_base_azar": {
            "puntos": int(len(d_azar)),
            "mediana_km": float(np.median(d_azar)) if len(d_azar) else None,
            "fraccion_menor_5km": p0,
            "p_valor_binomial_5km": p_valor,
            "metodo": "2000 puntos uniformes dentro del Perú en la misma caja (semilla 0); p = P(Binom(n, p_azar) ≥ k).",
        },
        "densidad_celdas": {
            "tamano_grados": CELDA_DENSIDAD,
            "celdas": [{"lat": float(r.lat), "lon": float(r.lon), "n": int(r.n)} for r in celdas.itertuples()],
        },
        "nota": "La fecha del inventario es la del levantamiento de campo, no la del evento: no se compara en el tiempo. GLC (noticias) e INGEMMET (campo) son familias independientes de evidencia, pero ambas favorecen zonas accesibles (vías, poblados), lo que también acerca sus puntos.",
    }


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
        serie = pd.Series(json.loads(ruta.read_text(encoding="utf-8"))["properties"]["parameter"]["PRECTOTCORR"])
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
        "contraste_ingemmet": contraste_ingemmet(eventos, raw, caja),
    }
