"""Módulo M1 · Matriz de Relevancia, problema P1: lluvia extrema en la cabecera del Chili.

Responde, con datos reales y sin mirar la prueba: **¿qué variables candidatas importan para anticipar
un día de lluvia extrema, en qué dirección y con cuánta confianza?** Sigue `docs/modulo-relevancia.md`:

1. Objetivo: día con lluvia IMERG Final ≥ percentil 99 del periodo de desarrollo (celda de 0,1° de la
   cabecera). Predictores: candidatas de `config/problemas.yaml` medidas el **día anterior** (POWER) y
   el ONI **conocido** ese día (el CPC publica con dos meses de retraso): no hay fuga del futuro.
2. Partición congelada (`config/fenomenos.yaml`): desarrollo = entrenamiento + validación; los años de
   prueba se apartan desde el inicio y se usan **una sola vez** al final.
3. Validación cruzada dejando un año fuera; línea base = climatología (tasa de eventos del pliegue).
4. Dos modelos: A = logística elastic-net; B = árboles con gradiente de profundidad limitada.
5. Importancia por permutación por bloques en el año apartado (aumento del Brier).
6. Estabilidad: frecuencia en el top-k entre remuestreos de años (Meinshausen y Bühlmann, 2010).
   Significancia condicional: cada variable se desplaza circularmente (≥ 365 días) y se reentrena;
   p = fracción de desplazamientos que no empeoran la pérdida → FDR (Benjamini-Hochberg).
7. k elegido por validación cruzada; se reentrena con el mejor modelo y se evalúa una vez en la prueba
   con IC90 por bootstrap de bloques. Publicable solo si la habilidad supera a la climatología con el
   IC90 por encima de 0.
8. Dirección: signo del coeficiente estandarizado de A contrastado con la dependencia parcial de B.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from ..evaluacion.metricas import ajuste_bh, bloque_politis_white, bootstrap_bloques, brier
from . import datos_reales as D

# Candidata del catálogo (config/variables.yaml) → columna de POWER diario (o "oni").
FUENTE_CANDIDATA = {
    "indice_oni": "oni",
    "temperatura_aire_2m": "T2M",
    "humedad_relativa": "RH2M",
    "viento_2m": "WS2M",
}


@dataclass(frozen=True)
class Parametros:
    percentil: float = 0.99
    C: float = 1.0
    l1_ratio: float = 0.5
    gbm: tuple[tuple[str, Any], ...] = (
        ("max_depth", 3),
        ("learning_rate", 0.05),
        ("max_iter", 150),
        ("min_samples_leaf", 40),
    )
    desplazamiento_minimo: int = 30
    remuestreos: int = 200
    nulos: int = 200
    alfa_fdr: float = 0.10
    k_maximo: int = 10

    @classmethod
    def desde_config(cls, c: dict[str, Any]) -> Parametros:
        return cls(
            percentil=c["percentil_objetivo"],
            C=c["elastic_net"]["C"],
            l1_ratio=c["elastic_net"]["l1_ratio"],
            gbm=tuple(sorted(c["gbm"].items())),
            desplazamiento_minimo=c["desplazamiento_minimo_dias"],
            remuestreos=c["remuestreos_estabilidad"],
            nulos=c["nulos"],
            alfa_fdr=c["alfa_fdr"],
            k_maximo=c["k_maximo"],
        )


# --- Modelos -------------------------------------------------------------------------------------


def _ajustar(modelo: str, X: np.ndarray, y: np.ndarray, p: Parametros, semilla: int) -> Any:
    if modelo == "A":
        escala = StandardScaler().fit(X)
        lr = LogisticRegression(solver="saga", C=p.C, l1_ratio=p.l1_ratio, max_iter=4000, random_state=semilla).fit(
            escala.transform(X), y
        )
        return ("A", escala, lr)
    gb = HistGradientBoostingClassifier(random_state=semilla, **dict(p.gbm)).fit(X, y)
    return ("B", None, gb)


def _predecir(m: Any, X: np.ndarray) -> np.ndarray:
    _, escala, est = m
    Z = escala.transform(X) if escala is not None else X
    return est.predict_proba(Z)[:, 1]


def bss(y: np.ndarray, prob: np.ndarray, base: float) -> float:
    """Habilidad de Brier frente a la climatología `base` (tasa de eventos del desarrollo)."""
    ref = brier(y, np.full(len(y), base))
    return float(1 - brier(y, prob) / ref) if ref > 0 else float("nan")


def _permutar_bloque(x: np.ndarray, rng: np.random.Generator, minimo: int) -> np.ndarray:
    n = len(x)
    if n <= 2 * minimo:
        return rng.permutation(x)
    return np.roll(x, int(rng.integers(minimo, n - minimo)))


# --- Validación cruzada dejando un año fuera ----------------------------------------------------


def validacion_cruzada(
    X: np.ndarray,
    y: np.ndarray,
    anios: np.ndarray,
    modelo: str,
    p: Parametros,
    semilla: int = 0,
    importancias: bool = True,
) -> dict[str, Any]:
    """Predicciones fuera de pliegue e importancia por permutación por bloques en cada año apartado."""
    rng = np.random.default_rng(semilla)
    oof = np.full(len(y), np.nan)
    aumento = np.zeros(X.shape[1])
    pesos = 0
    for a in np.unique(anios):
        prueba = anios == a
        if y[~prueba].sum() < 2:
            continue
        m = _ajustar(modelo, X[~prueba], y[~prueba], p, semilla)
        oof[prueba] = _predecir(m, X[prueba])
        if importancias and y[prueba].sum() > 0:
            base = brier(y[prueba], oof[prueba])
            for j in range(X.shape[1]):
                Xp = X[prueba].copy()
                Xp[:, j] = _permutar_bloque(Xp[:, j], rng, p.desplazamiento_minimo)
                aumento[j] += (brier(y[prueba], _predecir(m, Xp)) - base) * prueba.sum()
            pesos += prueba.sum()
    ok = ~np.isnan(oof)
    tasa = float(y.mean())
    return {
        "oof": oof,
        "bss": bss(y[ok], oof[ok], tasa),
        "importancia": aumento / max(pesos, 1),
    }


def _perdida_cv(X: np.ndarray, y: np.ndarray, anios: np.ndarray, p: Parametros, semilla: int) -> float:
    oof = validacion_cruzada(X, y, anios, "A", p, semilla, importancias=False)["oof"]
    ok = ~np.isnan(oof)
    return brier(y[ok], oof[ok])


def _perdida_desplazada(
    X: np.ndarray, y: np.ndarray, anios: np.ndarray, p: Parametros, j: int, desplazamiento: int, semilla: int
) -> float:
    Xn = X.copy()
    Xn[:, j] = np.roll(Xn[:, j], desplazamiento)
    return _perdida_cv(Xn, y, anios, p, semilla)


def _normalizar(v: np.ndarray) -> np.ndarray:
    v = np.clip(v, 0, None)
    return v / v.max() if v.max() > 0 else v


def direccion(X: np.ndarray, y: np.ndarray, p: Parametros) -> list[str]:
    """Signo del coeficiente estandarizado de A frente a la dependencia parcial de B."""
    _, _, lr = _ajustar("A", X, y, p, 0)
    coef = lr.coef_[0]
    gb = _ajustar("B", X, y, p, 0)
    salida = []
    for j in range(X.shape[1]):
        malla = np.quantile(X[:, j], np.linspace(0.05, 0.95, 9))
        pd_ = []
        for v in malla:
            Xg = X.copy()
            Xg[:, j] = v
            pd_.append(float(_predecir(gb, Xg).mean()))
        rho = float(pd.Series(pd_).corr(pd.Series(range(len(pd_))), method="spearman")) if np.ptp(pd_) > 0 else 0.0
        forma = "positiva" if rho >= 0.8 else "negativa" if rho <= -0.8 else "no_monotona"
        signo = "positiva" if coef[j] > 1e-6 else "negativa" if coef[j] < -1e-6 else "indeterminada"
        if forma == "no_monotona":
            salida.append("no_monotona")
        elif signo in ("indeterminada", forma):
            salida.append(forma)
        else:
            salida.append("indeterminada")  # los dos modelos discrepan: se muestra la discrepancia
    return salida


def relevancia(
    X: pd.DataFrame, y: pd.Series, anios_desarrollo: list[int], anios_prueba: list[int], p: Parametros, semilla: int = 0
) -> dict[str, Any]:
    """Núcleo del M1, independiente de la fuente de datos (se valida con datos sintéticos)."""
    nombres = list(X.columns)
    anio = X.index.year.to_numpy()
    dev = np.isin(anio, anios_desarrollo)
    te = np.isin(anio, anios_prueba)
    Xd, yd, ad = X.to_numpy()[dev], y.to_numpy()[dev].astype(int), anio[dev]
    Xt, yt = X.to_numpy()[te], y.to_numpy()[te].astype(int)

    cv = {m: validacion_cruzada(Xd, yd, ad, m, p, semilla) for m in ("A", "B")}
    imp = {m: _normalizar(cv[m]["importancia"]) for m in cv}
    combinada = (imp["A"] + imp["B"]) / 2
    orden = list(np.argsort(-combinada))

    # k por validación cruzada con el mejor modelo de la validación (tope k_maximo).
    elegido = max(cv, key=lambda m: cv[m]["bss"])
    puntajes_k = {}
    for k in range(1, min(p.k_maximo, len(nombres)) + 1):
        cols = orden[:k]
        puntajes_k[k] = validacion_cruzada(Xd[:, cols], yd, ad, elegido, p, semilla, importancias=False)["bss"]
    k = max(puntajes_k, key=lambda kk: (round(puntajes_k[kk], 6), -kk))
    top = set(orden[:k])

    # Estabilidad: remuestreo de años con reemplazo; importancia fuera de bolsa con el modelo A.
    rng = np.random.default_rng(semilla + 1)
    unicos = np.unique(ad)
    # Con k = número de variables el top-k las contendría a todas (estabilidad trivial de 1): la
    # frecuencia se mide en el top-k_e con k_e ≤ n − 1.
    k_estabilidad = max(1, min(k, len(nombres) - 1))
    en_top = np.zeros(len(nombres))
    aporta = np.zeros(len(nombres))
    validos = 0
    for r in range(p.remuestreos):
        bolsa = rng.choice(unicos, size=len(unicos), replace=True)
        fuera = np.setdiff1d(unicos, bolsa)
        if len(fuera) == 0:
            continue
        idx = np.concatenate([np.flatnonzero(ad == a) for a in bolsa])
        oob = np.isin(ad, fuera)
        if yd[idx].sum() < 2 or yd[oob].sum() < 1:
            continue
        m = _ajustar("A", Xd[idx], yd[idx], p, r)
        base = brier(yd[oob], _predecir(m, Xd[oob]))
        aum = []
        for j in range(len(nombres)):
            Xo = Xd[oob].copy()
            Xo[:, j] = _permutar_bloque(Xo[:, j], rng, p.desplazamiento_minimo)
            aum.append(brier(yd[oob], _predecir(m, Xo)) - base)
        en_top[np.argsort(-np.asarray(aum))[:k_estabilidad]] += 1
        aporta += np.asarray(aum) > 0
        validos += 1
    estabilidad = en_top / max(validos, 1)
    frecuencia_aporte = aporta / max(validos, 1)

    # Significancia condicional por variable: se desplaza circularmente SOLO esa variable (≥ 365 días),
    # se reentrena A en la misma validación cruzada y se compara la pérdida. Si la variable no aporta
    # nada dado el resto, desplazarla no cambia la pérdida (p ≈ 0,5); si aporta, la empeora.
    perdida_obs = _perdida_cv(Xd, yd, ad, p, semilla)
    tareas = [(j, int(rng.integers(365, len(yd) - 365)), r) for j in range(len(nombres)) for r in range(p.nulos)]
    perdidas = Parallel(n_jobs=-1)(delayed(_perdida_desplazada)(Xd, yd, ad, p, j, s, semilla + r) for j, s, r in tareas)
    mayores = np.zeros(len(nombres))
    for (j, _, _), perdida in zip(tareas, perdidas, strict=True):
        mayores[j] += perdida <= perdida_obs
    p_valor = (1 + mayores) / (1 + p.nulos)
    p_aj = ajuste_bh(list(p_valor))

    # Prueba: una sola vez, con el modelo y el k elegidos en validación.
    cols = orden[:k]
    final = _ajustar(elegido, Xd[:, cols], yd, p, semilla)
    prob = _predecir(final, Xt[:, cols])
    tasa = float(yd.mean())
    habilidad = bss(yt, prob, tasa)
    bloque = max(10, bloque_politis_white((prob - yt) ** 2 - (tasa - yt) ** 2))
    lo, hi = bootstrap_bloques(lambda a, b: bss(a, b, tasa), yt, prob, bloque=bloque, n=1000, semilla=semilla)
    publicable = bool(np.isfinite(habilidad) and habilidad > 0 and lo > 0)

    dirs = direccion(Xd, yd, p)
    variables = [
        {
            "variable_id": nombres[j],
            "importancia": round(float(combinada[j]), 6),
            "importancia_lineal": round(float(imp["A"][j]), 6),
            "importancia_no_lineal": round(float(imp["B"][j]), 6),
            "estabilidad": round(float(estabilidad[j]), 6),
            "frecuencia_aporte_fuera_de_bolsa": round(float(frecuencia_aporte[j]), 6),
            "p_valor": round(float(p_valor[j]), 6),
            "p_ajustado": round(float(p_aj[j]), 6) if p_aj[j] is not None else None,
            "significativa_fdr": bool(p_aj[j] is not None and p_aj[j] <= p.alfa_fdr),
            "direccion": dirs[j],
            "en_top_k": j in top,
        }
        for j in orden
    ]
    coinciden = set(np.argsort(-imp["A"])[:k]) == set(np.argsort(-imp["B"])[:k])
    return {
        "variables": variables,
        "k": k,
        "puntajes_k_validacion": {str(kk): round(float(v), 6) for kk, v in puntajes_k.items()},
        "modelos_validacion": {m: round(float(cv[m]["bss"]), 6) for m in cv},
        "modelo_elegido": {"A": "logistica_elastic_net", "B": "gradient_boosting"}[elegido],
        "coinciden_lineal_y_no_lineal": bool(coinciden),
        "remuestreos_validos": validos,
        "k_estabilidad": k_estabilidad,
        "nulos": p.nulos,
        "prueba": {
            "metrica": "BSS frente a la climatología",
            "valor": round(float(habilidad), 6),
            "ic90": [round(float(lo), 6), round(float(hi), 6)],
            "bloque_bootstrap": int(bloque),
            "dias": len(yt),
            "eventos": int(yt.sum()),
        },
        "publicable": publicable,
        "eventos_desarrollo": int(yd.sum()),
        "dias_desarrollo": len(yd),
        "tasa_climatologica": round(tasa, 6),
    }


# --- Datos reales del problema P1 ---------------------------------------------------------------


def datos_p1(cfg: dict[str, Any], raw: Path) -> tuple[pd.DataFrame, pd.Series, dict[str, Any]] | None:
    cab = cfg["puntos"]["cabecera"]
    lluvia = D.imerg_diario(raw, cab["lon"], cab["lat"])
    if lluvia is None:
        return None
    power, qc = D.power_diario(raw, "cabecera")
    oni = D.oni_disponible_diario(D.oni_mensual(raw), power.index)
    previo = power.shift(1)  # predictores del día anterior
    X = pd.DataFrame({cand: (oni if fuente == "oni" else previo[fuente]) for cand, fuente in FUENTE_CANDIDATA.items()})
    datos = pd.concat([X, lluvia.rename("lluvia")], axis=1).dropna()
    return datos[list(FUENTE_CANDIDATA)], datos["lluvia"], qc


def ejecutar(cfg: dict[str, Any], raw: Path, semilla: int = 0) -> dict[str, Any]:
    import yaml

    raiz = Path(__file__).resolve().parents[3]
    problemas = yaml.safe_load((raiz / "config" / "problemas.yaml").read_text(encoding="utf-8"))["problemas"]
    plantilla = problemas["P1"]
    p = Parametros.desde_config(cfg["modelos"]["relevancia"])
    cargados = datos_p1(cfg, raw)
    if cargados is None:
        return {"fenomeno": "relevancia", "problema_id": "P1", "estado": "sin_datos", "motivo": "IMERG no descargado"}
    X, lluvia, qc = cargados
    part = cfg["particion_temporal"]
    anio = X.index.year
    fin_dev = int(part["validacion"][1][:4])
    inicio_prueba = int(part["prueba"][0][:4])
    desarrollo = sorted({int(a) for a in anio if a <= fin_dev})
    prueba = sorted({int(a) for a in anio if a >= inicio_prueba})
    dev = np.isin(anio, desarrollo)
    umbral = float(lluvia[dev].quantile(p.percentil))  # solo con el desarrollo: la prueba no interviene
    y = (lluvia >= umbral).astype(int)
    r = relevancia(X, y, desarrollo, prueba, p, semilla)
    sin_dato = [c for c in plantilla["candidatas"] if c not in FUENTE_CANDIDATA]
    return {
        "fenomeno": "relevancia",
        "problema_id": "P1",
        "problema": plantilla["nombre"],
        "objetivo": f"día con lluvia IMERG Final ≥ {umbral:.2f} mm (percentil {p.percentil * 100:.0f} del desarrollo)",
        "umbral_mm": round(umbral, 4),
        "fuentes": {
            "objetivo": "NASA GPM IMERG Final V07 diaria (celda de 0,1° de la cabecera)",
            "predictores": "NASA POWER diario (día anterior) y NOAA CPC ONI (valor publicado a la fecha)",
        },
        "periodo": {"desde": str(X.index[0].date()), "hasta": str(X.index[-1].date())},
        "desarrollo": f"{desarrollo[0]}–{desarrollo[-1]}",
        "particion_prueba": f"{prueba[0]}–{prueba[-1]} (años apartados desde el inicio; evaluados una sola vez)",
        "candidatas_sin_dato": sin_dato,
        "calidad_predictores": {k: v for k, v in qc.items() if k in ("duplicados", "elevacion_celda_m")},
        **r,
        "lectura": (
            "La relevancia es predictiva, no causal: indica de qué depende la anticipación de un día extremo "
            "fuera de muestra. Celda pálida = importancia incierta (baja estabilidad o p ajustado alto)."
        ),
    }
