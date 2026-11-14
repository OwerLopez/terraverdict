"""Incertidumbre, calibración, deriva y abstención.

- Intervalos por predicción conformal partida (split conformal): cobertura marginal garantizada
  bajo intercambiabilidad (Vovk et al., 2005; Angelopoulos y Bates, 2021, arXiv:2107.07511).
  Con series temporales la garantía es aproximada: por eso se MIDE la cobertura en prueba.
- Calibración de probabilidades por regresión isotónica ajustada solo en validación.
- Deriva: índice de estabilidad poblacional (PSI) y prueba de Kolmogorov-Smirnov entre el
  periodo de entrenamiento y la ventana evaluada.
"""

from __future__ import annotations

import numpy as np
from scipy import stats
from sklearn.isotonic import IsotonicRegression


def cuantil_conformal(residuos_calibracion: np.ndarray, nivel: float = 0.90) -> float:
    r = np.sort(np.abs(np.asarray(residuos_calibracion, float)))
    n = len(r)
    k = int(np.ceil((n + 1) * nivel)) - 1
    return float(r[min(max(k, 0), n - 1)])


def intervalos_conformales(prediccion: np.ndarray, q: float) -> tuple[np.ndarray, np.ndarray]:
    return np.asarray(prediccion) - q, np.asarray(prediccion) + q


def cobertura(y: np.ndarray, inferior: np.ndarray, superior: np.ndarray) -> float:
    y = np.asarray(y)
    return float(np.mean((y >= inferior) & (y <= superior)))


class CalibradorIsotonico:
    def __init__(self) -> None:
        self._iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)

    def ajustar(self, p_validacion: np.ndarray, y_validacion: np.ndarray) -> CalibradorIsotonico:
        self._iso.fit(np.asarray(p_validacion, float), np.asarray(y_validacion, float))
        return self

    def transformar(self, p: np.ndarray) -> np.ndarray:
        return np.clip(self._iso.predict(np.asarray(p, float)), 1e-4, 1 - 1e-4)


def psi(referencia: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    """Índice de estabilidad poblacional: < 0,1 estable; 0,1–0,25 moderado; > 0,25 deriva fuerte."""
    referencia, actual = np.asarray(referencia, float), np.asarray(actual, float)
    bordes = np.unique(np.quantile(referencia, np.linspace(0, 1, bins + 1)))
    if len(bordes) < 3:
        return 0.0
    bordes[0], bordes[-1] = -np.inf, np.inf
    r = np.histogram(referencia, bordes)[0] / len(referencia)
    a = np.histogram(actual, bordes)[0] / len(actual)
    r, a = np.clip(r, 1e-6, None), np.clip(a, 1e-6, None)
    return float(np.sum((a - r) * np.log(a / r)))


def deriva(referencia: dict[str, np.ndarray], actual: dict[str, np.ndarray], umbral_psi: float = 0.25) -> dict:
    salida = {}
    for nombre, ref in referencia.items():
        valor = psi(ref, actual[nombre])
        ks = stats.ks_2samp(ref, actual[nombre])
        salida[nombre] = {"psi": round(valor, 4), "ks_p": float(ks.pvalue), "deriva": bool(valor > umbral_psi)}
    return salida


def decidir_abstencion(
    *,
    habilidad_validacion: float,
    minimo: float,
    n_eventos: int | None = None,
    eventos_minimos: int | None = None,
    deriva_detectada: bool = False,
) -> dict:
    """Regla de abstención global de una tarea. Devuelve si se publica y por qué."""
    motivos = []
    if not np.isfinite(habilidad_validacion) or habilidad_validacion <= minimo:
        motivos.append("No supera a la referencia climatológica en validación.")
    if n_eventos is not None and eventos_minimos is not None and n_eventos < eventos_minimos:
        motivos.append(f"Solo {n_eventos} eventos: se necesitan al menos {eventos_minimos}.")
    advertencias = ["Deriva de las entradas respecto del entrenamiento (PSI > 0,25)."] if deriva_detectada else []
    return {"publicar": not motivos, "abstencion": bool(motivos), "motivos": motivos, "advertencias": advertencias}
