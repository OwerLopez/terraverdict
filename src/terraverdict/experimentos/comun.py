"""Marco común de experimentos: ventanas, particiones temporales, zoológico de modelos y métricas.

Reglas que este módulo hace cumplir (no son opcionales):
- Partición temporal estricta (config/fenomenos.yaml): la normalización, la calibración, el
  umbral de decisión y la selección del mejor modelo se ajustan con entrenamiento/validación;
  el periodo de prueba solo se usa para la evaluación final.
- Toda métrica de habilidad se compara con referencias explícitas (climatología, persistencia).
- Las redes se entrenan con varias semillas; se informa la media y la dispersión entre semillas.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, PoissonRegressor, Ridge

from ..evaluacion import metricas as M
from ..evaluacion.explicabilidad import importancia_permutacion
from ..evaluacion.incertidumbre import (
    CalibradorIsotonico,
    cobertura,
    cuantil_conformal,
    intervalos_conformales,
)
from ..modelos.entrenamiento import entrenar, fijar_semilla, predecir
from ..modelos.redes import ARQUITECTURAS, REFERENCIAS, contar_parametros

REDES = list(ARQUITECTURAS)


@dataclass
class Particion:
    entrenamiento: tuple[str, str]
    validacion: tuple[str, str]
    prueba: tuple[str, str]

    def etiquetas(self, fechas: pd.DatetimeIndex) -> np.ndarray:
        e = np.full(len(fechas), "", dtype=object)
        for nombre, (a, b) in (
            ("entrenamiento", self.entrenamiento),
            ("validacion", self.validacion),
            ("prueba", self.prueba),
        ):
            e[(fechas >= pd.Timestamp(a)) & (fechas <= pd.Timestamp(b))] = nombre
        return e


@dataclass
class Datos:
    X: dict[str, np.ndarray]
    y: dict[str, np.ndarray]
    fechas: dict[str, pd.DatetimeIndex]
    nombres: list[str]
    L: int
    normalizacion: dict[str, tuple[float, float]] = field(default_factory=dict)


def construir(
    df: pd.DataFrame,
    objetivo: pd.Series,
    L: int,
    particion: Particion,
    fechas_permitidas: pd.DatetimeIndex | None = None,
    horizonte_fecha: pd.Timedelta | None = None,
) -> Datos:
    """Ventanas [t−L+1, t] de todas las variables → objetivo emitido en t (ya desplazado a t+h).

    Las filas se asignan a una partición por la fecha del OBJETIVO (t+h) cuando se da
    `horizonte_fecha`, para que ningún objetivo de entrenamiento caiga en validación.
    """
    df = df.astype(float)
    entrenamiento = df[
        (df.index >= pd.Timestamp(particion.entrenamiento[0])) & (df.index <= pd.Timestamp(particion.entrenamiento[1]))
    ]
    norm = {c: (float(entrenamiento[c].mean()), float(entrenamiento[c].std() or 1.0)) for c in df.columns}
    z = (df - pd.Series({c: v[0] for c, v in norm.items()})) / pd.Series({c: v[1] for c, v in norm.items()})
    arr = z.to_numpy(np.float32)
    ventanas = sliding_window_view(arr, (L, arr.shape[1]))[:, 0]  # (N−L+1, L, F)
    fins = df.index[L - 1 :]
    y = objetivo.reindex(fins).to_numpy(float)
    ok = np.isfinite(y) & np.isfinite(ventanas).all(axis=(1, 2))
    if fechas_permitidas is not None:
        ok &= np.isin(fins, fechas_permitidas)
    fecha_objetivo = fins + (horizonte_fecha or pd.Timedelta(0))
    etiquetas = particion.etiquetas(pd.DatetimeIndex(fecha_objetivo))
    X, Y, F = {}, {}, {}
    for parte in ("entrenamiento", "validacion", "prueba"):
        sel = ok & (etiquetas == parte)
        X[parte], Y[parte], F[parte] = ventanas[sel].copy(), y[sel], fins[sel]
    return Datos(X, Y, F, list(df.columns), L, norm)


def _plano(X: np.ndarray) -> np.ndarray:
    return X.reshape(len(X), -1)


def _clasicos(tipo: str, semilla: int) -> dict[str, Any]:
    if tipo == "clasificacion":
        return {
            "logistica": LogisticRegression(C=0.5, max_iter=3000),
            "gbm": HistGradientBoostingClassifier(
                max_iter=300, learning_rate=0.05, max_leaf_nodes=15, l2_regularization=1.0, random_state=semilla
            ),
        }
    if tipo == "conteo":
        return {
            "poisson_glm": PoissonRegressor(alpha=1.0, max_iter=1000),
            "gbm": HistGradientBoostingRegressor(
                loss="poisson", max_iter=200, learning_rate=0.05, max_leaf_nodes=15, random_state=semilla
            ),
        }
    return {
        "ridge": Ridge(alpha=3.0),
        "gbm": HistGradientBoostingRegressor(
            max_iter=300, learning_rate=0.05, max_leaf_nodes=15, l2_regularization=1.0, random_state=semilla
        ),
    }


def _predecir_clasico(modelo: Any, X: np.ndarray, tipo: str) -> np.ndarray:
    return modelo.predict_proba(_plano(X))[:, 1] if tipo == "clasificacion" else modelo.predict(_plano(X))


def _metricas(
    tipo: str,
    y: np.ndarray,
    p: np.ndarray,
    ref: dict[str, np.ndarray],
    umbral: float | None = None,
    q_conformal: float | None = None,
) -> dict[str, Any]:
    if tipo == "clasificacion":
        salida = {
            "brier": M.brier(y, p),
            "bss_climatologia": M.habilidad_brier(y, p, ref["climatologia"]),
            "auc": M.auc(y, p),
            "ece": M.confiabilidad(y, p)["ece"],
        }
        if "persistencia" in ref:
            salida["bss_persistencia"] = M.habilidad_brier(y, p, ref["persistencia"])
        if umbral is not None:
            salida["contingencia"] = M.tabla_contingencia(y, p, umbral)
        return salida
    if tipo == "conteo":
        ll, ll0 = M.log_verosimilitud_poisson(y, p), M.log_verosimilitud_poisson(y, ref["climatologia"])
        return {
            "log_verosimilitud": ll,
            "ganancia_informacion_bits": (ll - ll0) / np.log(2),
            "mae": M.mae(y, p),
            "mae_climatologia": M.mae(y, ref["climatologia"]),
        }
    salida = {
        "mae": M.mae(y, p),
        "rmse": M.rmse(y, p),
        "r": M.correlacion(y, p),
        "habilidad_climatologia": M.habilidad_mse(y, p, ref["climatologia"]),
    }
    if "persistencia" in ref:
        salida["habilidad_persistencia"] = M.habilidad_mse(y, p, ref["persistencia"])
    if q_conformal is not None:
        lo, hi = intervalos_conformales(p, q_conformal)
        salida["cobertura_90"] = cobertura(y, lo, hi)
        salida["ancho_intervalo_90"] = 2 * q_conformal
    return salida


def puntaje_validacion(tipo: str, y: np.ndarray, p: np.ndarray, ref: np.ndarray) -> float:
    """Métrica única para elegir modelos (mayor es mejor)."""
    if tipo == "clasificacion":
        return M.habilidad_brier(y, p, ref)
    if tipo == "conteo":
        return (M.log_verosimilitud_poisson(y, p) - M.log_verosimilitud_poisson(y, ref)) / np.log(2)
    return M.habilidad_mse(y, p, ref)


def _perdidas(tipo: str, y: np.ndarray, p: np.ndarray) -> np.ndarray:
    if tipo == "conteo":
        from scipy import stats

        return -stats.poisson.logpmf(y.astype(int), np.clip(p, 1e-9, None))
    return (p - y) ** 2


def evaluar_zoo(
    d: Datos,
    tipo: str,
    referencias: dict[str, dict[str, np.ndarray]],
    *,
    redes: list[str] | None = None,
    semillas: tuple[int, ...] = (0, 1),
    epocas: int = 60,
    bloque_bootstrap: int = 10,
    registro: Callable[[str], None] = print,
) -> dict[str, Any]:
    """Entrena y evalúa referencias, modelos clásicos y redes. `referencias[parte][nombre]` son
    predicciones de referencia (climatología obligatoria) alineadas con d.y[parte]."""
    redes = REDES if redes is None else redes
    ytr, yva, yte = d.y["entrenamiento"], d.y["validacion"], d.y["prueba"]
    resultados: dict[str, Any] = {}
    predicciones: dict[str, dict[str, np.ndarray]] = {}

    def registrar(nombre: str, familia: str, pva: np.ndarray, pte: np.ndarray, extra: dict[str, Any]) -> None:
        crudo_va = pva
        umbral = q = None
        if tipo == "clasificacion":
            if familia not in ("referencia", "ensamble"):  # las referencias se evalúan tal cual
                cal = CalibradorIsotonico().ajustar(pva, yva)
                pva, pte = cal.transformar(pva), cal.transformar(pte)
            umbral = M.mejor_umbral_csi(yva, pva)
        elif tipo == "regresion":
            q = cuantil_conformal(yva - pva, 0.90)
        val = puntaje_validacion(tipo, yva, pva, referencias["validacion"]["climatologia"])
        prueba = _metricas(tipo, yte, pte, referencias["prueba"], umbral, q)
        principal = (
            "bss_climatologia"
            if tipo == "clasificacion"
            else ("ganancia_informacion_bits" if tipo == "conteo" else "habilidad_climatologia")
        )
        if tipo == "clasificacion":

            def fn(yy, pp, rr):
                return M.habilidad_brier(yy, pp, rr)
        elif tipo == "conteo":

            def fn(yy, pp, rr):
                return (M.log_verosimilitud_poisson(yy, pp) - M.log_verosimilitud_poisson(yy, rr)) / np.log(2)
        else:

            def fn(yy, pp, rr):
                return M.habilidad_mse(yy, pp, rr)

        ic = M.bootstrap_bloques(fn, yte, pte, referencias["prueba"]["climatologia"], bloque=bloque_bootstrap)
        dm = M.diebold_mariano(_perdidas(tipo, yte, pte), _perdidas(tipo, yte, referencias["prueba"]["climatologia"]))
        resultados[nombre] = {
            "familia": familia,
            "puntaje_validacion": val,
            "prueba": prueba,
            "metrica_principal": principal,
            "ic90_prueba": list(ic),
            "diebold_mariano_vs_climatologia": dm,
            "umbral_decision": umbral,
            "q_conformal_90": q,
            **extra,
        }
        predicciones[nombre] = {"validacion": pva, "prueba": pte, "validacion_cruda": crudo_va}

    for nombre, ref in referencias["validacion"].items():
        registrar(f"ref_{nombre}", "referencia", ref, referencias["prueba"][nombre], {"descripcion": nombre})

    for nombre, modelo in _clasicos(tipo, 0).items():
        t = time.perf_counter()
        modelo.fit(_plano(d.X["entrenamiento"]), ytr)
        registrar(
            nombre,
            "clasico",
            _predecir_clasico(modelo, d.X["validacion"], tipo),
            _predecir_clasico(modelo, d.X["prueba"], tipo),
            {"segundos": round(time.perf_counter() - t, 2)},
        )
        registro(f"  {nombre}: validación {resultados[nombre]['puntaje_validacion']:.4f}")

    peso = None
    if tipo == "clasificacion":
        pos = max(1.0, float(ytr.sum()))
        peso = float(np.sqrt((len(ytr) - pos) / pos))
    for red in redes:
        pva_s, pte_s, puntajes, info = [], [], [], []
        for s in semillas:
            fijar_semilla(s)  # la inicialización de los pesos también depende de la semilla
            modelo = ARQUITECTURAS[red](d.L, len(d.nombres), 1)
            modelo, h = entrenar(
                modelo,
                d.X["entrenamiento"],
                ytr,
                d.X["validacion"],
                yva,
                tarea=tipo,
                epocas=epocas,
                peso_positivo=peso,
                semilla=s,
            )
            pva, pte = predecir(modelo, d.X["validacion"], tipo), predecir(modelo, d.X["prueba"], tipo)
            pva_s.append(pva)
            pte_s.append(pte)
            puntajes.append(puntaje_validacion(tipo, yva, pva, referencias["validacion"]["climatologia"]))
            info.append(
                {
                    "semilla": s,
                    "epocas": len(h.perdida_validacion),
                    "mejor_epoca": h.mejor_epoca,
                    "segundos": round(h.segundos, 1),
                }
            )
        registrar(
            red,
            "red_neuronal",
            np.mean(pva_s, 0),
            np.mean(pte_s, 0),
            {
                "referencia": REFERENCIAS[red],
                "parametros": contar_parametros(modelo),
                "semillas": info,
                "puntaje_validacion_por_semilla": [float(v) for v in puntajes],
                "dispersion_semillas": float(np.std(puntajes)),
            },
        )
        registro(f"  {red}: validación {resultados[red]['puntaje_validacion']:.4f} ± {np.std(puntajes):.4f}")

    candidatos = [k for k, v in resultados.items() if v["familia"] != "referencia"]
    top = sorted(candidatos, key=lambda k: -resultados[k]["puntaje_validacion"])[:3]
    pva = np.mean([predicciones[k]["validacion"] for k in top], 0)
    pte = np.mean([predicciones[k]["prueba"] for k in top], 0)
    registrar("ensamble_top3", "ensamble", pva, pte, {"miembros": top})
    if tipo == "clasificacion":  # el ensamble ya promedia probabilidades calibradas
        resultados["ensamble_top3"]["nota"] = "Promedio de probabilidades calibradas de los 3 mejores en validación"
    mejor = max([*candidatos, "ensamble_top3"], key=lambda k: resultados[k]["puntaje_validacion"])
    return {
        "modelos": resultados,
        "mejor_validacion": mejor,
        "ranking_validacion": sorted(
            [*candidatos, "ensamble_top3"], key=lambda k: -resultados[k]["puntaje_validacion"]
        ),
        "_predicciones": predicciones,
    }


def explicar(d: Datos, tipo: str, referencia_validacion: np.ndarray, semilla: int = 0) -> dict[str, Any]:
    """Importancia por permutación con un GBM ajustado en entrenamiento y evaluado en validación."""
    modelo = _clasicos(tipo, semilla)["gbm"]
    modelo.fit(_plano(d.X["entrenamiento"]), d.y["entrenamiento"])
    if tipo == "clasificacion":
        perdida = M.brier
    elif tipo == "conteo":

        def perdida(y: np.ndarray, p: np.ndarray) -> float:
            return -M.log_verosimilitud_poisson(y, p)
    else:

        def perdida(y: np.ndarray, p: np.ndarray) -> float:
            return float(np.mean((y - p) ** 2))

    imp = importancia_permutacion(
        lambda X: _predecir_clasico(modelo, X, tipo),
        d.X["validacion"],
        d.y["validacion"],
        perdida,
        d.nombres,
        repeticiones=5,
        semilla=semilla,
    )
    return {"modelo": "gbm (ajustado en entrenamiento)", "conjunto": "validación", "importancias": imp}


def serie_prueba(
    d: Datos, zoo: dict[str, Any], modelo: str, referencia: np.ndarray, maximo: int = 2500
) -> dict[str, Any]:
    """Predicciones de prueba (para graficar) del modelo indicado frente a lo observado."""
    p = zoo["_predicciones"][modelo]["prueba"]
    q = zoo["modelos"][modelo].get("q_conformal_90")
    fechas = d.fechas["prueba"][-maximo:]
    n = len(fechas)
    salida = {
        "modelo": modelo,
        "fechas": [str(f.date()) for f in fechas],
        "observado": np.round(d.y["prueba"][-n:], 4).tolist(),
        "pronostico": np.round(p[-n:], 4).tolist(),
        "referencia": np.round(referencia[-n:], 4).tolist(),
    }
    if q is not None:
        salida["intervalo_90"] = [round(float(q), 4)]
    return salida


def limpiar(zoo: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in zoo.items() if not k.startswith("_")}
