"""Métricas de verificación de pronósticos (Wilks, 2011; Gneiting y Raftery, 2007, doi:10.1198/016214506000001437).

Todas las métricas de habilidad se calculan frente a una referencia explícita (climatología o
persistencia): una métrica absoluta sin referencia no dice si el modelo sirve.
"""

from __future__ import annotations

import numpy as np
from scipy import stats
from sklearn.metrics import roc_auc_score


def mae(y: np.ndarray, p: np.ndarray) -> float:
    return float(np.mean(np.abs(np.asarray(y) - np.asarray(p))))


def rmse(y: np.ndarray, p: np.ndarray) -> float:
    return float(np.sqrt(np.mean((np.asarray(y) - np.asarray(p)) ** 2)))


def habilidad_mse(y: np.ndarray, p: np.ndarray, referencia: np.ndarray) -> float:
    """1 − MSE(modelo)/MSE(referencia): > 0 significa que el modelo mejora a la referencia."""
    ref = float(np.mean((np.asarray(y) - np.asarray(referencia)) ** 2))
    return float(1 - np.mean((np.asarray(y) - np.asarray(p)) ** 2) / ref) if ref > 0 else float("nan")


def brier(y: np.ndarray, p: np.ndarray) -> float:
    return float(np.mean((np.asarray(p) - np.asarray(y)) ** 2))


def habilidad_brier(y: np.ndarray, p: np.ndarray, p_referencia: np.ndarray) -> float:
    ref = brier(y, p_referencia)
    return float(1 - brier(y, p) / ref) if ref > 0 else float("nan")


def auc(y: np.ndarray, p: np.ndarray) -> float:
    y = np.asarray(y)
    return float(roc_auc_score(y, p)) if 0 < y.sum() < len(y) else float("nan")


def confiabilidad(y: np.ndarray, p: np.ndarray, bins: int = 10) -> dict:
    """Curva de confiabilidad y error de calibración esperado (ECE) con bins de igual frecuencia."""
    y, p = np.asarray(y, float), np.asarray(p, float)
    bordes = np.unique(np.quantile(p, np.linspace(0, 1, bins + 1)))
    idx = np.clip(np.searchsorted(bordes, p, side="right") - 1, 0, len(bordes) - 2)
    curva, ece = [], 0.0
    for b in range(len(bordes) - 1):
        sel = idx == b
        if sel.sum() == 0:
            continue
        pm, om = float(p[sel].mean()), float(y[sel].mean())
        curva.append({"pronosticada": round(pm, 4), "observada": round(om, 4), "n": int(sel.sum())})
        ece += sel.mean() * abs(pm - om)
    return {"ece": float(ece), "curva": curva}


def tabla_contingencia(y: np.ndarray, p: np.ndarray, umbral: float) -> dict:
    y = np.asarray(y).astype(bool)
    s = np.asarray(p) >= umbral
    a, b, c = int((s & y).sum()), int((s & ~y).sum()), int((~s & y).sum())
    d = int((~s & ~y).sum())
    pod = a / (a + c) if a + c else float("nan")
    far = b / (a + b) if a + b else float("nan")
    csi = a / (a + b + c) if a + b + c else float("nan")
    n = a + b + c + d
    esperado = ((a + b) * (a + c) + (c + d) * (b + d)) / n if n else float("nan")
    hss = (a + d - esperado) / (n - esperado) if n and n != esperado else float("nan")
    return {
        "umbral": float(umbral),
        "aciertos": a,
        "falsas_alarmas": b,
        "fallos": c,
        "correctos_negativos": d,
        "pod": pod,
        "far": far,
        "csi": csi,
        "hss": hss,
    }


def mejor_umbral_csi(y: np.ndarray, p: np.ndarray) -> float:
    """Umbral que maximiza el CSI. Se elige en VALIDACIÓN y se aplica sin cambios en prueba."""
    candidatos = np.unique(np.quantile(p, np.linspace(0.5, 0.995, 60)))
    return float(max(candidatos, key=lambda u: np.nan_to_num(tabla_contingencia(y, p, u)["csi"])))


def log_verosimilitud_poisson(y: np.ndarray, mu: np.ndarray) -> float:
    mu = np.clip(np.asarray(mu, float), 1e-9, None)
    return float(np.mean(stats.poisson.logpmf(np.asarray(y, int), mu)))


def correlacion(y: np.ndarray, p: np.ndarray) -> float:
    y, p = np.asarray(y, float), np.asarray(p, float)
    return float(np.corrcoef(y, p)[0, 1]) if np.std(p) > 0 and np.std(y) > 0 else float("nan")


def bootstrap_bloques(
    funcion, *arreglos: np.ndarray, bloque: int = 10, n: int = 500, semilla: int = 0, nivel: float = 0.90
) -> tuple[float, float]:
    """IC por bootstrap de bloques móviles (conserva la autocorrelación de los errores)."""
    rng = np.random.default_rng(semilla)
    N = len(arreglos[0])
    bloque = max(1, min(bloque, N // 2))
    valores = []
    for _ in range(n):
        inicios = rng.integers(0, N - bloque + 1, int(np.ceil(N / bloque)))
        idx = np.concatenate([np.arange(s, s + bloque) for s in inicios])[:N]
        v = funcion(*[a[idx] for a in arreglos])
        if np.isfinite(v):
            valores.append(v)
    if not valores:
        return float("nan"), float("nan")
    a = (1 - nivel) / 2
    return float(np.quantile(valores, a)), float(np.quantile(valores, 1 - a))


def diebold_mariano(perdida_a: np.ndarray, perdida_b: np.ndarray, horizonte: int = 1) -> dict:
    """Prueba de Diebold y Mariano (1995), doi:10.1080/07350015.1995.10524599, con varianza HAC.

    H0: igual pérdida esperada. Estadístico < 0 favorece al modelo A. Corrección de muestra
    pequeña de Harvey, Leybourne y Newbold (1997).
    """
    d = np.asarray(perdida_a, float) - np.asarray(perdida_b, float)
    n = len(d)
    dm = float(d.mean())
    rezagos = max(horizonte - 1, int(np.floor(n ** (1 / 3))))
    gamma0 = float(np.mean((d - dm) ** 2))
    var = gamma0 + 2 * sum(
        (1 - k / (rezagos + 1)) * float(np.mean((d[k:] - dm) * (d[:-k] - dm))) for k in range(1, rezagos + 1)
    )
    if var <= 0:
        return {"estadistico": float("nan"), "p": float("nan"), "diferencia_media": dm}
    est = dm / np.sqrt(var / n)
    correccion = np.sqrt((n + 1 - 2 * horizonte + horizonte * (horizonte - 1) / n) / n)
    est *= correccion
    p = float(2 * stats.t.sf(abs(est), df=n - 1))
    return {"estadistico": float(est), "p": p, "diferencia_media": dm, "rezagos_hac": rezagos}
