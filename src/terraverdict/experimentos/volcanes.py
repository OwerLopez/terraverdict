"""Experimento: historia eruptiva y recurrencia de los volcanes del sur del Perú (GVP).

Probabilidad anual de inicio de erupción con un modelo de Poisson sobre el registro histórico
(desde 1550, inicio aproximado de los registros escritos coloniales en la región) e intervalo
exacto de Garwood (1936). Sin monitoreo continuo (OVS-IGP), el sistema NO pronostica erupciones:
describe frecuencias históricas y su incertidumbre.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

from ..ingest import gvp
from .sismos import catalogo

INICIO_HISTORICO = 1550


def _distancia_km(lat1: float, lon1: float, lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    dlat, dlon = np.radians(lat - lat1), np.radians(lon - lon1)
    a = np.sin(dlat / 2) ** 2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat)) * np.sin(dlon / 2) ** 2
    return 2 * 6371 * np.arcsin(np.sqrt(a))


def ejecutar(cfg: dict[str, Any], raw: Path, registro=print, anio_fin: int = 2026) -> dict[str, Any]:
    volcanes, erupciones = gvp.cargar(raw / "gvp")
    sismos = catalogo(raw)
    ciudad = cfg["puntos"]["ciudad"]
    salida = []
    for v in sorted(volcanes, key=lambda x: x["Volcano_Name"]):
        propias = [e for e in erupciones if e["Volcano_Number"] == v["Volcano_Number"]]
        confirmadas = sorted(
            [e for e in propias if e["Activity_Type"] == "Confirmed Eruption" and e["StartDateYear"] is not None],
            key=lambda e: e["StartDateYear"],
        )
        historicas = [e for e in confirmadas if e["StartDateYear"] >= INICIO_HISTORICO]
        T = anio_fin - INICIO_HISTORICO + 1
        n = len(historicas)
        lam = n / T
        lo = stats.chi2.ppf(0.05, 2 * n) / (2 * T) if n > 0 else 0.0
        hi = stats.chi2.ppf(0.95, 2 * n + 2) / (2 * T)
        anios = [e["StartDateYear"] for e in historicas]
        intervalos = np.diff(anios) if len(anios) > 1 else np.array([])
        lat, lon = v["Latitude"], v["Longitude"]
        d = _distancia_km(lat, lon, sismos["lat"].to_numpy(), sismos["lon"].to_numpy())
        cerca = sismos[(d <= 25) & (sismos["profundidad_km"].fillna(999) <= 30)]
        salida.append(
            {
                "numero_gvp": v["Volcano_Number"],
                "nombre": v["Volcano_Name"],
                "lat": lat,
                "lon": lon,
                "elevacion_m": v.get("Elevation"),
                "tipo": v.get("Primary_Volcano_Type"),
                "ultima_erupcion": v.get("Last_Eruption_Year"),
                "distancia_a_arequipa_km": float(
                    _distancia_km(ciudad["lat"], ciudad["lon"], np.array([lat]), np.array([lon]))[0]
                ),
                "erupciones_registradas": len(propias),
                "confirmadas_holoceno": len(confirmadas),
                "confirmadas_desde_1550": n,
                "tasa_anual": lam,
                "ic90_tasa": [float(lo), float(hi)],
                "probabilidad_anual_inicio": float(1 - np.exp(-lam)) if n else 0.0,
                "ic90_probabilidad_anual": [float(1 - np.exp(-lo)), float(1 - np.exp(-hi))],
                "intervalo_medio_anios": float(intervalos.mean()) if len(intervalos) else None,
                "cv_intervalos": float(intervalos.std() / intervalos.mean())
                if len(intervalos) > 2 and intervalos.mean() > 0
                else None,
                "iev_maximo_historico": max((e["ExplosivityIndexMax"] or 0) for e in historicas)
                if historicas
                else None,
                "erupciones": [
                    {
                        "inicio": e["StartDateYear"],
                        "fin": e.get("EndDateYear"),
                        "iev": e.get("ExplosivityIndexMax"),
                        "tipo": e["Activity_Type"],
                        "evidencia": e.get("StartEvidenceMethod"),
                    }
                    for e in sorted(
                        propias, key=lambda e: e["StartDateYear"] if e["StartDateYear"] is not None else -1e9
                    )
                ],
                "sismos_cercanos_usgs": {
                    "radio_km": 25,
                    "profundidad_max_km": 30,
                    "total": len(cerca),
                    "por_anio": {str(k): int(x) for k, x in cerca.groupby(cerca["tiempo"].dt.year).size().items()},
                },
            }
        )
    registro(f"volcanes: {len(salida)} volcanes, {len(erupciones)} registros de erupción")
    return {
        "fenomeno": "volcanes",
        "tarea": "recurrencia",
        "fuente": "Smithsonian GVP, Volcanoes of the World (WFS)",
        "inicio_registro_historico": INICIO_HISTORICO,
        "volcanes": sorted(salida, key=lambda x: -x["confirmadas_desde_1550"]),
        "abstencion": {
            "publicar": True,
            "abstencion": True,
            "motivos": [
                "Sin datos de monitoreo continuo (sismicidad volcánica, gases, deformación) no se pronostican erupciones."
            ],
            "advertencias": [
                "La probabilidad anual es una frecuencia histórica; el estado actual de cada volcán lo informa el OVS-IGP."
            ],
        },
        "metodo": {
            "tasa": "Poisson n/T con T desde 1550 hasta el año actual",
            "ic": "exacto de Garwood (chi-cuadrado), 90 %",
            "sismos_cercanos": "USGS ComCat; la red global no detecta la sismicidad volcánica pequeña",
        },
    }
