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
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view
from scipy.optimize import Bounds, LinearConstraint, minimize
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, PoissonRegressor, Ridge

from ..config import cargar_yaml
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


@dataclass
class Tarea:
    """Definición reutilizable de una tarea de pronóstico.

    La comparten el experimento principal y el historial por origen móvil, para que ambos usen
    exactamente los mismos datos, el mismo objetivo y las mismas referencias.
    `referencias(hasta)` devuelve el constructor de referencias ajustado solo con datos ≤ `hasta`.
    """

    nombre: str
    tipo: str  # clasificacion | regresion | conteo
    X: pd.DataFrame
    objetivo: pd.Series
    horizonte: pd.Timedelta | pd.DateOffset
    referencias: Callable[[str], Callable[[Datos], dict[str, dict[str, np.ndarray]]]]
    fechas: pd.DatetimeIndex | None = None
    epocas: int = 60
    bloque_bootstrap: int = 10
    horizonte_pasos: int = 1  # pasos de tiempo del pronóstico (Diebold-Mariano con corrección HLN)


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


RUTA_MODELOS = Path(__file__).resolve().parents[3] / "config" / "modelos.yaml"


def parametros(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    """Hiperparámetros y reglas de `config/modelos.yaml` (o los que trae `cfg["modelos"]`)."""
    if cfg is not None and cfg.get("modelos"):
        return cfg["modelos"]
    return _modelos_por_defecto()


@lru_cache(maxsize=1)
def _modelos_por_defecto() -> dict[str, Any]:
    return cargar_yaml(RUTA_MODELOS)


def _clasicos(tipo: str, semilla: int, cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    c = parametros(cfg)["clasicos"]
    if tipo == "clasificacion":
        return {
            "logistica": LogisticRegression(**c["logistica"]),
            "gbm": HistGradientBoostingClassifier(**c["gbm_clasificacion"], random_state=semilla),
        }
    if tipo == "conteo":
        return {
            "poisson_glm": PoissonRegressor(**c["poisson_glm"]),
            "gbm": HistGradientBoostingRegressor(loss="poisson", **c["gbm_conteo"], random_state=semilla),
        }
    return {
        "ridge": Ridge(**c["ridge"]),
        "gbm": HistGradientBoostingRegressor(**c["gbm_regresion"], random_state=semilla),
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


def pliegues_contiguos(n: int, k: int) -> list[np.ndarray]:
    """Bloques contiguos (en el tiempo) de la validación, para ajustar y evaluar sin solaparse."""
    k = max(2, min(k, n // 2)) if n >= 4 else 1
    return [b for b in np.array_split(np.arange(n), k) if len(b)]


def calibrar_cruzado(pva: np.ndarray, yva: np.ndarray, pliegues: list[np.ndarray]) -> np.ndarray:
    """Probabilidades de validación calibradas FUERA DE PLIEGUE: cada bloque se calibra con los demás.

    Con ellas se calcula el puntaje de validación. La calibración que se aplica a la prueba se ajusta
    con toda la validación. Si un pliegue deja una sola clase en el resto, ese bloque usa la tasa del resto.
    """
    salida = np.empty(len(pva))
    if len(pliegues) < 2:
        return CalibradorIsotonico().ajustar(pva, yva).transformar(pva)
    for idx in pliegues:
        resto = np.setdiff1d(np.arange(len(pva)), idx)
        if len(np.unique(yva[resto])) < 2:
            salida[idx] = np.clip(float(yva[resto].mean()), 1e-4, 1 - 1e-4)
        else:
            salida[idx] = CalibradorIsotonico().ajustar(pva[resto], yva[resto]).transformar(pva[idx])
    return salida


def _perdida_media(tipo: str, y: np.ndarray, p: np.ndarray) -> float:
    return float(np.mean(_perdidas(tipo, y, np.clip(p, 1e-9, None) if tipo == "conteo" else p)))


def pesos_validacion(tipo: str, y: np.ndarray, P: np.ndarray) -> np.ndarray:
    """Pesos ≥ 0 que suman 1 y minimizan la pérdida de la tarea (Brier, ECM o Poisson) sobre `P`
    (n × miembros). Apilamiento restringido (Breiman, 1996). Se ajustan SOLO con validación."""
    m = P.shape[1]
    if m == 1:
        return np.ones(1)
    restriccion = LinearConstraint(np.ones((1, m)), 1.0, 1.0)
    res = minimize(  # type: ignore[call-overload]  # stubs de scipy: options es un TypedDict
        lambda w: _perdida_media(tipo, y, P @ w),
        np.full(m, 1.0 / m),
        method="SLSQP",
        bounds=Bounds(np.zeros(m), np.ones(m)),
        constraints=restriccion,
        options={"maxiter": 200, "ftol": 1e-10},
    )
    w = np.clip(res.x if res.success else np.full(m, 1.0 / m), 0.0, None)
    return w / w.sum() if w.sum() > 0 else np.full(m, 1.0 / m)


def _combinar(variante: str, tipo: str, y: np.ndarray, Pva: np.ndarray) -> np.ndarray:
    return np.full(Pva.shape[1], 1.0 / Pva.shape[1]) if variante == "promedio" else pesos_validacion(tipo, y, Pva)


def evaluar_zoo(
    d: Datos,
    tipo: str,
    referencias: dict[str, dict[str, np.ndarray]],
    *,
    redes: list[str] | None = None,
    semillas: tuple[int, ...] = (0, 1),
    epocas: int = 60,
    bloque_bootstrap: int = 10,
    horizonte_pasos: int = 1,
    cfg: dict[str, Any] | None = None,
    registro: Callable[[str], None] = print,
) -> dict[str, Any]:
    """Entrena y evalúa referencias, modelos clásicos, redes y ensambles.

    `referencias[parte][nombre]` son predicciones de referencia (climatología obligatoria)
    alineadas con d.y[parte]. Reglas (docs/auditoria-metricas.md):
    - el modelo publicado es el de mejor `puntaje_validacion`; la prueba no interviene;
    - la calibración y los ensambles se puntúan FUERA DE PLIEGUE dentro de la validación;
    - la parada temprana de las redes usa el tramo final del entrenamiento, no la validación;
    - el IC90 usa bootstrap de bloques con el bloque mayor entre el de la tarea y el de
      Politis-White; Diebold-Mariano usa el horizonte del pronóstico.
    """
    P = parametros(cfg)
    redes = REDES if redes is None else redes
    ytr, yva, yte = d.y["entrenamiento"], d.y["validacion"], d.y["prueba"]
    ev = P["evaluacion"]
    pliegues = pliegues_contiguos(len(yva), int(P["calibracion"]["pliegues_validacion"]))
    resultados: dict[str, Any] = {}
    predicciones: dict[str, dict[str, np.ndarray]] = {}
    clim_va, clim_te = referencias["validacion"]["climatologia"], referencias["prueba"]["climatologia"]

    def fn(yy: np.ndarray, pp: np.ndarray, rr: np.ndarray) -> float:
        return puntaje_validacion(tipo, yy, pp, rr)

    def registrar(
        nombre: str,
        familia: str,
        pva: np.ndarray,
        pte: np.ndarray,
        extra: dict[str, Any],
        pva_oof: np.ndarray | None = None,
    ) -> None:
        """`pva_oof`: predicciones de validación fuera de pliegue (ensambles); si falta, se calculan."""
        crudo_va = pva
        umbral = q = None
        if tipo == "clasificacion":
            if familia not in ("referencia", "ensamble"):  # las referencias se evalúan tal cual
                cal = CalibradorIsotonico().ajustar(pva, yva)
                pva_oof = calibrar_cruzado(pva, yva, pliegues)
                pte = cal.transformar(pte)
            umbral = M.mejor_umbral_csi(yva, pva if pva_oof is None else pva_oof)
        va_puntaje = pva if pva_oof is None else pva_oof
        if tipo == "regresion":
            # Residuos de validación fuera de pliegue en los ensambles (sus pesos salen de la validación)
            q = cuantil_conformal(yva - va_puntaje, float(ev["nivel_ic"]))
        val = puntaje_validacion(tipo, yva, va_puntaje, clim_va)
        prueba = _metricas(tipo, yte, pte, referencias["prueba"], umbral, q)
        principal = (
            "bss_climatologia"
            if tipo == "clasificacion"
            else ("ganancia_informacion_bits" if tipo == "conteo" else "habilidad_climatologia")
        )
        dif = _perdidas(tipo, yte, pte) - _perdidas(tipo, yte, clim_te)
        bloque = max(int(bloque_bootstrap), M.bloque_politis_white(dif))
        ic = M.bootstrap_bloques(
            fn,
            yte,
            pte,
            clim_te,
            bloque=bloque,
            n=int(ev["bootstrap_repeticiones"]),
            semilla=int(ev["bootstrap_semilla"]),
            nivel=float(ev["nivel_ic"]),
        )
        dm = M.diebold_mariano(_perdidas(tipo, yte, pte), _perdidas(tipo, yte, clim_te), horizonte=horizonte_pasos)
        resultados[nombre] = {
            "familia": familia,
            "puntaje_validacion": val,
            "prueba": prueba,
            "metrica_principal": principal,
            "ic90_prueba": list(ic),
            "bloque_bootstrap": bloque,
            "diebold_mariano_vs_climatologia": dm,
            "umbral_decision": umbral,
            "q_conformal_90": q,
            **extra,
        }
        predicciones[nombre] = {
            "validacion": va_puntaje,
            "prueba": pte,
            "validacion_cruda": crudo_va,
        }

    for nombre, ref in referencias["validacion"].items():
        registrar(f"ref_{nombre}", "referencia", ref, referencias["prueba"][nombre], {"descripcion": nombre})

    for nombre, modelo in _clasicos(tipo, 0, cfg).items():
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
    pr = P["redes"]
    # Parada temprana con el tramo final del entrenamiento (temporal): la validación queda intacta
    # para elegir el modelo.
    n_pt = max(1, round(len(ytr) * float(pr["fraccion_parada_temprana"])))
    Xaj, yaj = d.X["entrenamiento"][:-n_pt], ytr[:-n_pt]
    Xpt, ypt = d.X["entrenamiento"][-n_pt:], ytr[-n_pt:]
    for red in redes:
        pva_s, pte_s, puntajes, info = [], [], [], []
        for s in semillas:
            fijar_semilla(s)  # la inicialización de los pesos también depende de la semilla
            modelo = ARQUITECTURAS[red](d.L, len(d.nombres), 1)
            modelo, h = entrenar(
                modelo,
                Xaj,
                yaj,
                Xpt,
                ypt,
                tarea=tipo,
                epocas=epocas,
                lote=int(pr["lote"]),
                lr=float(pr["tasa_aprendizaje"]),
                paciencia=int(pr["paciencia"]),
                decaimiento=float(pr["decaimiento_pesos"]),
                peso_positivo=peso,
                semilla=s,
            )
            pva, pte = predecir(modelo, d.X["validacion"], tipo), predecir(modelo, d.X["prueba"], tipo)
            pva_s.append(pva)
            pte_s.append(pte)
            puntajes.append(puntaje_validacion(tipo, yva, pva, clim_va))
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
                "parada_temprana": f"último {float(pr['fraccion_parada_temprana']):.0%} del entrenamiento ({n_pt} ventanas)",
                "puntaje_validacion_por_semilla": [float(v) for v in puntajes],
                "dispersion_semillas": float(np.std(puntajes)),
            },
        )
        registro(f"  {red}: validación {resultados[red]['puntaje_validacion']:.4f} ± {np.std(puntajes):.4f}")

    candidatos = [k for k, v in resultados.items() if v["familia"] != "referencia"]
    pe = P["ensamble"]
    k_miembros = int(pe["miembros"])
    ensambles = []
    for variante in pe["variantes"]:
        nombre_e = "ensamble_top3" if variante == "promedio" else "ensamble_ponderado"
        # Puntaje de validación fuera de pliegue: en cada bloque, miembros y pesos salen de los demás bloques
        oof = np.empty(len(yva))
        for idx in pliegues:
            resto = np.setdiff1d(np.arange(len(yva)), idx)
            top_r = sorted(
                candidatos,
                key=lambda k: (
                    -puntaje_validacion(tipo, yva[resto], predicciones[k]["validacion"][resto], clim_va[resto])
                ),
            )[:k_miembros]
            Pr = np.column_stack([predicciones[k]["validacion"][resto] for k in top_r])
            w_r = _combinar(variante, tipo, yva[resto], Pr)
            oof[idx] = np.column_stack([predicciones[k]["validacion"][idx] for k in top_r]) @ w_r
        # Para la prueba: miembros y pesos con toda la validación
        top = sorted(candidatos, key=lambda k: -resultados[k]["puntaje_validacion"])[:k_miembros]
        Pva = np.column_stack([predicciones[k]["validacion"] for k in top])
        w = _combinar(variante, tipo, yva, Pva)
        pte = np.column_stack([predicciones[k]["prueba"] for k in top]) @ w
        registrar(
            nombre_e,
            "ensamble",
            Pva @ w,
            pte,
            {
                "miembros": top,
                "pesos": [round(float(x), 4) for x in w],
                "variante": variante,
                "nota": (
                    "Promedio simple" if variante == "promedio" else "Pesos ≥ 0 que suman 1, ajustados en validación"
                )
                + f" de los {k_miembros} mejores en validación; puntaje de validación fuera de pliegue ({len(pliegues)} bloques)",
            },
            pva_oof=oof,
        )
        ensambles.append(nombre_e)
    todos = [*candidatos, *ensambles]
    mejor = max(todos, key=lambda k: resultados[k]["puntaje_validacion"])
    return {
        "modelos": resultados,
        "mejor_validacion": mejor,
        "ranking_validacion": sorted(todos, key=lambda k: -resultados[k]["puntaje_validacion"]),
        "protocolo": {
            "seleccion": "mayor puntaje de validación (la prueba no interviene)",
            "calibracion": f"isotónica; puntaje de validación fuera de pliegue ({len(pliegues)} bloques contiguos)",
            "parada_temprana": f"último {float(pr['fraccion_parada_temprana']):.0%} del entrenamiento",
            "ensambles": list(pe["variantes"]),
            "horizonte_diebold_mariano": horizonte_pasos,
            "bloque_bootstrap_minimo": int(bloque_bootstrap),
        },
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
