"""Experimento: SPI-3 en la cabecera del Chili a 1 y 3 meses de anticipación.

SPI con parámetros gamma ajustados solo con el periodo de entrenamiento (sin fuga de datos).
Predictores: SPI-3, SPI-6, anomalías de temperatura y humedad, ONI disponible (rezago de
publicación de 2 meses) y estación del año.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..evaluacion import metricas as M
from ..evaluacion.incertidumbre import decidir_abstencion, deriva
from ..senales.procesamiento import regimenes, spi, ventana_adaptativa
from . import datos_reales as D
from .comun import Particion, construir, evaluar_zoo, explicar, limpiar, serie_prueba


def preparar(raw: Path, hasta_entrenamiento: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    m, qc = D.power_mensual(raw)
    dias = m.index.days_in_month
    lluvia = m["PRECTOTCORR"] * dias  # mm/día → mm/mes
    oni = D.oni_mensual(raw)
    ent = m.index <= pd.Timestamp(hasta_entrenamiento)
    clim_t = m["T2M"][ent].groupby(m.index[ent].month).mean()
    clim_q = m["QV2M"][ent].groupby(m.index[ent].month).mean()
    mes = 2 * np.pi * m.index.month / 12
    X = pd.DataFrame(
        {
            "spi3": spi(lluvia, 3, hasta_entrenamiento),
            "spi6": spi(lluvia, 6, hasta_entrenamiento),
            "spi1": spi(lluvia, 1, hasta_entrenamiento),
            "anomalia_temperatura": m["T2M"] - clim_t.reindex(m.index.month).to_numpy(),
            "anomalia_humedad": m["QV2M"] - clim_q.reindex(m.index.month).to_numpy(),
            "oni": oni.reindex(m.index - pd.DateOffset(months=2)).to_numpy(),
            "mes_seno": np.sin(mes),
            "mes_coseno": np.cos(mes),
        },
        index=m.index,
    )
    return X, {**qc, "lluvia_anual_media_mm": float(lluvia.groupby(lluvia.index.year).sum().mean())}


def ejecutar(
    cfg: dict[str, Any],
    raw: Path,
    registro=print,
    redes: list[str] | None = None,
    semillas: tuple[int, ...] = (0, 1, 2),
) -> dict[str, Any]:
    pt = cfg["particion_temporal"]
    particion = Particion(tuple(pt["entrenamiento"]), tuple(pt["validacion"]), ("2021-01-01", "2025-12-31"))
    X, qc = preparar(raw, pt["entrenamiento"][1])
    columnas = list(X.columns)
    salida: dict[str, Any] = {
        "fenomeno": "sequia",
        "tarea": "regresion",
        "calidad": qc,
        "regimenes_spi3": regimenes(X["spi3"].dropna(), tamano_minimo=36),
        "horizontes": {},
    }
    for h in (1, 3):
        objetivo = X["spi3"].shift(-h)

        def referencias(d: Any) -> dict[str, dict[str, np.ndarray]]:
            return {
                p: {"climatologia": np.zeros(len(d.y[p])), "persistencia": X["spi3"].reindex(d.fechas[p]).to_numpy()}
                for p in ("validacion", "prueba")
            }

        def evaluar_L(L: int, objetivo: pd.Series = objetivo, h: int = h) -> float:
            from sklearn.linear_model import Ridge

            d = construir(X[columnas], objetivo, L, particion, None, pd.DateOffset(months=h))
            mdl = Ridge(alpha=3.0).fit(
                d.X["entrenamiento"].reshape(len(d.y["entrenamiento"]), -1), d.y["entrenamiento"]
            )
            p = mdl.predict(d.X["validacion"].reshape(len(d.y["validacion"]), -1))
            return M.habilidad_mse(d.y["validacion"], p, np.zeros(len(p)))

        ventana = ventana_adaptativa([3, 6, 12, 24], evaluar_L, {"memoria_spi": 3 + h})
        L = ventana["elegida"]
        d = construir(X[columnas], objetivo, L, particion, None, pd.DateOffset(months=h))
        refs = referencias(d)
        registro(f"sequía h={h}: ventana {L} meses, n={ {k: len(v) for k, v in d.y.items()} }")
        zoo = evaluar_zoo(
            d, "regresion", refs, redes=redes, semillas=semillas, epocas=150, bloque_bootstrap=6, registro=registro
        )
        mejor = zoo["mejor_validacion"]
        p = zoo["_predicciones"][mejor]["prueba"]
        sequia_obs, sequia_pred = d.y["prueba"] <= -1, p <= -1
        contingencia = M.tabla_contingencia(sequia_obs.astype(float), sequia_pred.astype(float), 0.5)
        abst = decidir_abstencion(
            habilidad_validacion=zoo["modelos"][mejor]["puntaje_validacion"],
            minimo=cfg["abstencion"]["skill_minimo_validacion"],
        )
        salida["horizontes"][f"h{h}"] = {
            "definicion": {
                "objetivo": f"SPI-3 dentro de {h} mes(es)",
                "ventana_meses": L,
                "n": {k: len(v) for k, v in d.y.items()},
            },
            "ventana": ventana,
            "zoo": limpiar(zoo),
            "categoria_sequia_spi_menor_1": contingencia,
            "explicabilidad": explicar(d, "regresion", refs["validacion"]["climatologia"]),
            "deriva": deriva(
                {c: X.loc[X.index <= particion.entrenamiento[1], c].dropna().to_numpy() for c in columnas},
                {c: X.loc[X.index >= particion.prueba[0], c].dropna().to_numpy() for c in columnas},
            ),
            "abstencion": abst,
            "serie_prueba": serie_prueba(d, zoo, mejor, refs["prueba"]["climatologia"]),
        }
    return salida
