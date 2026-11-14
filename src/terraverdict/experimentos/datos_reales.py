"""Carga de los datos reales descargados (data/raw) y control de calidad.

El control de calidad no corrige en silencio: cuenta y reporta. Los valores fuera de rango físico
se marcan como faltantes y quedan contados en el informe.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..ingest import ghcn

RANGOS = {  # límites físicos plausibles para la región (no climatológicos)
    "PRECTOTCORR": (0.0, 500.0),
    "T2M": (-40.0, 50.0),
    "T2M_MAX": (-40.0, 55.0),
    "T2M_MIN": (-50.0, 45.0),
    "RH2M": (0.0, 100.0),
    "QV2M": (0.0, 30.0),
    "WS2M": (0.0, 40.0),
    "PS": (50.0, 110.0),
    "ALLSKY_SFC_SW_DWN": (0.0, 45.0),
}


def _power_df(ruta: Path, diario: bool) -> tuple[pd.DataFrame, dict[str, Any]]:
    j = json.loads(ruta.read_text())
    par = j["properties"]["parameter"]
    df = pd.DataFrame(par)
    if diario:
        df.index = pd.to_datetime(df.index, format="%Y%m%d")
    else:
        df = df[[not k.endswith("13") for k in df.index]]
        df.index = pd.to_datetime(df.index, format="%Y%m")
    df = df.astype(float).sort_index()
    qc: dict[str, Any] = {
        "archivo": ruta.name,
        "n": len(df),
        "desde": str(df.index[0].date()),
        "hasta": str(df.index[-1].date()),
        "variables": {},
    }
    for c in df.columns:
        faltantes = int((df[c] == -999).sum())
        df.loc[df[c] == -999, c] = np.nan
        lo, hi = RANGOS.get(c, (-np.inf, np.inf))
        fuera = int(((df[c] < lo) | (df[c] > hi)).sum())
        df.loc[(df[c] < lo) | (df[c] > hi), c] = np.nan
        qc["variables"][c] = {
            "faltantes": faltantes,
            "fuera_de_rango": fuera,
            "fraccion_valida": float(df[c].notna().mean()),
        }
    qc["duplicados"] = int(df.index.duplicated().sum())
    qc["elevacion_celda_m"] = j["geometry"]["coordinates"][2]
    return df, qc


def power_diario(raw: Path, punto: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    return _power_df(raw / "power" / f"power_diario_{punto}.json", diario=True)


def power_mensual(raw: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    archivo = max((raw / "power").glob("power_-*_*.json"))
    return _power_df(archivo, diario=False)


def oni_mensual(raw: Path) -> pd.Series:
    """ONI por mes central de la estación de 3 meses (DJF → enero, …, NDJ → diciembre)."""
    centro = {
        "DJF": 1,
        "JFM": 2,
        "FMA": 3,
        "MAM": 4,
        "AMJ": 5,
        "MJJ": 6,
        "JJA": 7,
        "JAS": 8,
        "ASO": 9,
        "SON": 10,
        "OND": 11,
        "NDJ": 12,
    }
    filas = (raw / "noaa" / "oni.ascii.txt").read_text().strip().splitlines()[1:]
    datos = {}
    for linea in filas:
        p = linea.split()
        if len(p) >= 4 and p[0] in centro:
            datos[pd.Timestamp(int(p[1]), centro[p[0]], 1)] = float(p[3])
    return pd.Series(datos).sort_index()


def oni_disponible_diario(oni: pd.Series, indice: pd.DatetimeIndex) -> pd.Series:
    """ONI conocido en cada día: el CPC publica a inicios del mes M la estación centrada en M−2.

    Usar el ONI centrado en el mes actual filtraría información del futuro.
    """
    mes = indice.to_period("M").to_timestamp() - pd.DateOffset(months=2)
    return pd.Series(oni.reindex(mes).to_numpy(), index=indice)


def comparar_con_estacion(power: pd.DataFrame, raw: Path, estacion: str) -> dict[str, Any]:
    """Contraste POWER (celda de 0,5°) frente a la estación GHCN en los días comunes."""
    g = ghcn.cargar(raw / "ghcn", estacion)
    est = pd.Series({pd.Timestamp(k): v for k, v in g["PRCP"].items()}).sort_index()
    comun = power["PRECTOTCORR"].reindex(est.index).dropna()
    est = est.reindex(comun.index)
    mensual_p = comun.resample("MS").sum(min_count=25)
    mensual_e = est.resample("MS").sum(min_count=25)
    ok = mensual_p.notna() & mensual_e.notna()
    humedos = (comun >= 1) | (est >= 1)
    return {
        "estacion": estacion,
        "dias_comunes": len(comun),
        "desde": str(comun.index[0].date()),
        "hasta": str(comun.index[-1].date()),
        "r_diario": float(np.corrcoef(comun, est)[0, 1]),
        "r_diario_dias_humedos": float(np.corrcoef(comun[humedos], est[humedos])[0, 1]) if humedos.sum() > 30 else None,
        "meses_completos": int(ok.sum()),
        "r_mensual": float(np.corrcoef(mensual_p[ok], mensual_e[ok])[0, 1]) if ok.sum() > 12 else None,
        "razon_total_power_estacion": float(mensual_p[ok].sum() / mensual_e[ok].sum()) if ok.sum() > 12 else None,
        "p99_diario_power": float(comun.quantile(0.99)),
        "p99_diario_estacion": float(est.quantile(0.99)),
        "lectura": (
            "La celda de POWER suaviza la lluvia local: correlación y extremos menores que en la estación. "
            "Los resultados de lluvia extrema describen la escala regional de la celda, no tormentas puntuales."
        ),
    }
