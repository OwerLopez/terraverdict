"""Diagnóstico de dinámica (caos, no linealidad, ruido) en series reales de los fenómenos.

Series evaluadas y su preparación (siempre anomalías respecto del ciclo anual del entrenamiento,
para no confundir la estacionalidad con dinámica):
- Lluvia en la cabecera: totales de 5 días (péntadas) de log(1+P), anomalía. Se usan péntadas
  porque la serie diaria tiene muchos ceros empatados, que sesgan los métodos ordinales. Se evalúa
  con POWER y con CHIRPS: un veredicto que cambia con el producto no describe a la lluvia.
- Temperatura diaria en la cabecera: anomalía.
- SPI-3 mensual en la cabecera.
- ONI mensual (1950–presente).
- Sismos independientes M ≥ Mc: conteo mensual y logaritmo de los intervalos entre eventos.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..caos.diagnostico import diagnosticar
from ..senales.procesamiento import climatologia_diaria, escalas
from . import datos_reales as D
from .sequia import preparar as preparar_sequia


def series(
    cfg: dict[str, Any], raw: Path, sismos: dict[str, Any] | None, omitidas: dict[str, str] | None = None
) -> dict[str, tuple[pd.Series, str, str, float]]:
    """Series fechadas (índice temporal) para el diagnóstico global y para el historial en ventanas.

    Una fuente sin crudos locales (p. ej. CHIRPS cuando ClimateSERV no es accesible) se omite y su
    motivo queda en `omitidas`, en vez de detener el resto del diagnóstico."""
    hasta = cfg["particion_temporal"]["entrenamiento"][1]
    df, _ = D.power_diario(raw, "cabecera")

    def pentadas(diaria: pd.Series) -> pd.Series:
        p = np.log1p(diaria).resample("5D").sum(min_count=5)
        return p - p.groupby(p.index.dayofyear // 5).transform(lambda s: s[s.index <= pd.Timestamp(hasta)].mean())

    anom_lluvia = pentadas(df["PRECTOTCORR"])
    t = df["T2M"]
    anom_t = t - climatologia_diaria(t, hasta=hasta)
    X, _ = preparar_sequia(raw, hasta)
    salida = {
        "lluvia_pentadas_cabecera": (
            anom_lluvia.dropna(),
            "péntada",
            "NASA POWER (MERRA-2) PRECTOTCORR, celda de cabecera",
            5.0,
        ),
        "temperatura_diaria_cabecera": (
            anom_t.dropna(),
            "día",
            "NASA POWER (MERRA-2) T2M, celda de cabecera",
            1.0,
        ),
        "spi3_mensual_cabecera": (X["spi3"].dropna(), "mes", "SPI-3 derivado de NASA POWER", 30.4),
        "oni_mensual": (D.oni_mensual(raw).astype(float), "mes", "NOAA CPC ONI", 30.4),
    }
    try:
        salida["lluvia_pentadas_cabecera_chirps"] = (
            pentadas(D.chirps_diario(raw, "cabecera_local")).dropna(),
            "péntada",
            "CHIRPS v2.0 (ClimateSERV), caja de 0,1° en la cabecera",
            5.0,
        )
    except FileNotFoundError as e:
        if omitidas is not None:
            omitidas["lluvia_pentadas_cabecera_chirps"] = str(e)
    if sismos is not None:
        salida["sismos_conteo_mensual"] = (
            sismos["_series"]["mensual_independiente"].astype(float),
            "mes",
            "USGS ComCat desagrupado (Gardner-Knopoff)",
            30.4,
        )
        salida["sismos_intereventos_log"] = (
            pd.Series(sismos["_series"]["intereventos_log"], index=sismos["_series"]["intereventos_tiempos"]),
            "evento",
            "USGS ComCat desagrupado: log de días entre sismos",
            float("nan"),
        )
    return salida


def ejecutar(cfg: dict[str, Any], raw: Path, sismos: dict[str, Any] | None = None, registro=print) -> dict[str, Any]:
    resultados = {}
    omitidas: dict[str, str] = {}
    for nombre, (serie, unidad, fuente, dias) in series(cfg, raw, sismos, omitidas).items():
        x = serie.to_numpy(float)
        r = diagnosticar(x, nombre=nombre, unidad_tiempo=unidad)
        r["fuente"] = fuente
        tau = (r.get("embedding") or {}).get("tau") or 1
        z = (x - np.mean(x)) / (np.std(x) or 1.0)
        paso = max(1, (len(z) - tau) // 1500)  # submuestra para el gráfico del espacio de fases
        r["espacio_fases"] = np.round(np.column_stack([z[:-tau:paso], z[tau::paso]]), 3).tolist()
        if np.isfinite(dias) and len(x) > 64:
            r["escalas"] = escalas(x, paso_dias=dias)
        resultados[nombre] = r
        registro(f"caos {nombre}: n={r['n']} → {r['veredicto']}")
    conteo: dict[str, int] = {}
    for r in resultados.values():
        conteo[r["veredicto"]] = conteo.get(r["veredicto"], 0) + 1
    return {
        "fenomeno": "dinamica",
        "tarea": "diagnostico_caos",
        "series": resultados,
        "resumen_veredictos": conteo,
        "series_omitidas": omitidas,
        "lectura": (
            "Un veredicto 'compatible_con_caos_baja_dimension' exigiría no linealidad, determinismo, D2 "
            "saturado bajo, λ > 0 y K > 0,8 a la vez. Los métodos se validaron antes con Lorenz, Hénon, "
            "el mapa logístico, AR(1), ruido y un seno (tests/caos)."
        ),
    }
