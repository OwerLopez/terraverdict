"""Procesamiento de señales: climatología, anomalías, SPI, regímenes, escalas y ventana adaptativa.

- SPI: McKee, Doesken y Kleist (1993); distribución gamma por mes calendario con probabilidad de
  cero (Thom, 1958). Los parámetros se ajustan SOLO con el periodo de entrenamiento.
- Cambios de régimen: PELT (Killick, Fearnhead y Eckley, 2012, doi:10.1080/01621459.2012.737745)
  con la implementación de ruptures (Truong, Oudre y Vayatis, 2020, doi:10.1016/j.sigpro.2019.107299).
- Escalas: periodograma y energía por nivel de la transformada wavelet discreta (Daubechies 4).
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd
import pywt
import ruptures as rpt
from scipy import signal, stats


def climatologia_diaria(serie: pd.Series, armonicos: int = 3, hasta: str | None = None) -> pd.Series:
    """Ciclo anual suave (regresión armónica) ajustado hasta la fecha `hasta` (sin fuga de datos)."""
    s = serie.dropna()
    ajuste = s[s.index <= pd.Timestamp(hasta)] if hasta else s

    def diseno(idx: pd.DatetimeIndex) -> np.ndarray:
        w = 2 * np.pi * idx.dayofyear.to_numpy() / 365.25
        cols = [np.ones(len(idx))]
        for k in range(1, armonicos + 1):
            cols += [np.cos(k * w), np.sin(k * w)]
        return np.column_stack(cols)

    beta, *_ = np.linalg.lstsq(diseno(ajuste.index), ajuste.to_numpy(), rcond=None)
    return pd.Series(diseno(serie.index) @ beta, index=serie.index)


def spi(lluvia_mensual: pd.Series, escala: int, hasta: str) -> pd.Series:
    """SPI-k con parámetros gamma por mes calendario ajustados hasta `hasta` (inclusive)."""
    acumulada = lluvia_mensual.rolling(escala, min_periods=escala).sum()
    salida = pd.Series(np.nan, index=acumulada.index)
    for mes in range(1, 13):
        sel = acumulada.index.month == mes
        ajuste = acumulada[sel & (acumulada.index <= pd.Timestamp(hasta))].dropna()
        positivos = ajuste[ajuste > 0]
        if len(positivos) < 10:
            continue
        q = float((ajuste == 0).mean())
        a, _, escala_g = stats.gamma.fit(positivos, floc=0)
        valores = acumulada[sel]
        cdf = q + (1 - q) * stats.gamma.cdf(valores.clip(lower=0), a, scale=escala_g)
        salida[sel] = stats.norm.ppf(np.clip(cdf, 1e-6, 1 - 1e-6))
    return salida


def regimenes(serie: pd.Series, tamano_minimo: int = 24, penalizacion: float | None = None) -> dict:
    """Puntos de cambio en media y varianza (PELT, costo normal) con penalización tipo BIC."""
    s = serie.dropna()
    x = ((s - s.mean()) / s.std()).to_numpy()[:, None]
    pen = penalizacion if penalizacion is not None else 3 * np.log(len(x))
    cortes = rpt.Pelt(model="normal", min_size=tamano_minimo).fit(x).predict(pen=pen)
    segmentos, inicio = [], 0
    for fin in cortes:
        tramo = s.iloc[inicio:fin]
        segmentos.append(
            {
                "desde": str(tramo.index[0].date()),
                "hasta": str(tramo.index[-1].date()),
                "media": float(tramo.mean()),
                "desviacion": float(tramo.std()),
                "n": len(tramo),
            }
        )
        inicio = fin
    return {
        "metodo": "PELT costo normal (ruptures)",
        "penalizacion": float(pen),
        "tamano_minimo": tamano_minimo,
        "puntos_cambio": [str(s.index[c].date()) for c in cortes[:-1]],
        "segmentos": segmentos,
    }


def escalas(x: np.ndarray, paso_dias: float = 1.0, wavelet: str = "db4") -> dict:
    """Varianza por escala (DWT) y picos del periodograma (periodos en días)."""
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    x = x - x.mean()
    niveles = min(pywt.dwt_max_level(len(x), pywt.Wavelet(wavelet).dec_len), 10)
    coef = pywt.wavedec(x, wavelet, level=niveles)
    energias = [float(np.sum(c**2)) for c in coef[1:]][::-1]  # nivel 1 (escala fina) … nivel J
    total = sum(energias) + float(np.sum(coef[0] ** 2))
    por_escala = [
        {
            "nivel": j + 1,
            "periodo_dias": [2 ** (j + 1) * paso_dias, 2 ** (j + 2) * paso_dias],
            "fraccion_varianza": e / total,
        }
        for j, e in enumerate(energias)
    ]
    f, pxx = signal.periodogram(x, detrend="linear")
    orden = np.argsort(pxx[1:])[::-1][:5] + 1
    picos = [
        {"periodo_dias": float(paso_dias / f[i]), "potencia_relativa": float(pxx[i] / pxx[1:].sum())}
        for i in orden
        if f[i] > 0
    ]
    return {"wavelet": wavelet, "por_escala": por_escala, "picos_periodograma": picos}


def ventana_adaptativa(candidatos: list[int], evaluar: Callable[[int], float], sugeridas: dict[str, int]) -> dict:
    """Elige la longitud de ventana con mejor desempeño en VALIDACIÓN entre candidatos fijos y las
    sugeridas por la señal (decorrelación, embedding de Takens). Devuelve todas las puntuaciones."""
    todas = sorted({int(c) for c in candidatos} | {int(v) for v in sugeridas.values() if v and v > 1})
    puntuaciones = {L: float(evaluar(L)) for L in todas}
    mejor = max(puntuaciones, key=lambda k: puntuaciones[k])
    return {"elegida": mejor, "puntuacion_validacion": puntuaciones, "sugeridas_por_la_senal": sugeridas}
