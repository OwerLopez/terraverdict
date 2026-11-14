"""Diagnóstico integrado de la dinámica de una serie: ¿caos determinista, no linealidad o ruido?

Regla de decisión (conservadora; nunca fuerza conclusiones):
1. Con menos de ``n_minimo`` puntos el sistema se abstiene ("insuficiente").
2. Si ninguna prueba de no linealidad rechaza la hipótesis nula de los sustitutos IAAFT
   (asimetría temporal, error de predicción de análogos), la serie es compatible con un proceso
   lineal estocástico: "lineal_estocastica". Ninguna medida de caos se interpreta.
3. Si hay no linealidad pero no se cumplen TODAS las condiciones de caos de baja dimensión,
   la conclusión es "no_lineal_sin_caos_demostrado".
4. "compatible_con_caos_baja_dimension" exige a la vez: no linealidad significativa, determinismo
   (la serie se predice con análogos mejor que todos sus sustitutos), D2 que satura en un valor
   bajo (< 5), λ > 0 y K de la prueba 0-1 > 0,8. Aun así se informa como compatibilidad, no como
   demostración. La comparación de λ con los sustitutos se informa, pero no decide: en flujos
   continuos los sustitutos lineales también divergen en el espacio reconstruido (validado con
   Lorenz), por lo que el exponente no es por sí solo una prueba de caos (Kantz y Schreiber, 2004).
5. "regular" si la prueba 0-1 da K < 0,2 (dinámica periódica o cuasiperiódica).
"""

from __future__ import annotations

import datetime as dt
from typing import Any

import numpy as np

from .embedding import (
    dimension_embedding,
    embeber,
    falsos_vecinos,
    periodo_medio,
    retardo_optimo,
)
from .invariantes import (
    dimension_correlacion,
    entropia_muestral,
    entropia_permutacion,
    lyapunov_rosenstein,
    prueba_01,
)
from .recurrencia import rqa
from .surrogates import asimetria_temporal, error_prediccion_no_lineal, iaaft, prueba

VEREDICTOS = {
    "insuficiente": "Datos insuficientes para evaluar la dinámica: el sistema se abstiene.",
    "regular": "Dinámica regular (periódica o cuasiperiódica) según la prueba 0-1.",
    "lineal_estocastica": "Compatible con un proceso lineal estocástico: no hay evidencia de no linealidad ni de caos.",
    "no_lineal_sin_caos_demostrado": "Hay no linealidad significativa, pero no evidencia de caos determinista de baja dimensión.",
    "compatible_con_caos_baja_dimension": "Compatible con caos determinista de baja dimensión (compatibilidad, no demostración).",
}


def diagnosticar(
    x: np.ndarray,
    *,
    nombre: str,
    unidad_tiempo: str = "muestra",
    dt_tiempo: float = 1.0,
    n_minimo: int = 500,
    n_sustitutos: int = 99,
    n_sustitutos_costosos: int = 39,
    alpha: float = 0.05,
    max_puntos: int = 3000,
    semilla: int = 20261114,
) -> dict[str, Any]:
    rng = np.random.default_rng(semilla)
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    base: dict[str, Any] = {
        "serie": nombre,
        "n": len(x),
        "unidad_tiempo": unidad_tiempo,
        "semilla": semilla,
        "generado_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }
    if len(x) < n_minimo or np.std(x) == 0:
        return {**base, "veredicto": "insuficiente", "explicacion": VEREDICTOS["insuficiente"]}
    if len(x) > max_puntos:
        x = x[-max_puntos:]  # tramo más reciente y contiguo
        base["n_usado"] = max_puntos
    x = (x - x.mean()) / x.std()

    ret = retardo_optimo(x, max_lag=60)
    tau = int(ret["tau"])
    fnn = falsos_vecinos(x, tau, m_max=10)
    m = max(2, dimension_embedding(fnn))
    theiler = int(max(tau, round(periodo_medio(x))))
    theiler = min(theiler, len(x) // 20)

    # 1) No linealidad frente a sustitutos IAAFT
    tra = prueba(x, lambda s: asimetria_temporal(s, 1), n_sustitutos, "dos", rng)
    nlpe = prueba(x, lambda s: error_prediccion_no_lineal(s, m, tau), n_sustitutos, "menor", rng)
    # Dos pruebas sobre la misma hipótesis nula: corrección de Holm-Bonferroni (con dos pruebas,
    # rechazar si el p menor es <= alpha/2). Sin corrección, el error tipo I familiar sería ~10 %.
    alpha_holm = alpha / 2
    no_lineal = min(tra["p"], nlpe["p"]) <= alpha_holm

    # 2) Invariantes en la serie original
    m_valores = list(range(1, 11))
    d2 = dimension_correlacion(x, tau, m_valores, theiler)
    lyap = lyapunov_rosenstein(x, m, tau, theiler, dt=dt_tiempo)
    k01 = prueba_01(x[::tau], rng=rng)  # submuestreo por τ: evita el sobremuestreo de flujos
    pe = entropia_permutacion(x, orden=5, retardo=1)
    se = entropia_muestral(x)
    rq = rqa(embeber(x, m, tau), theiler=theiler)

    # 3) Invariantes costosos en sustitutos (¿se distinguen del ruido lineal con igual espectro?)
    lyap_s, det_s, pe_s = [], [], []
    for _ in range(n_sustitutos_costosos):
        s = iaaft(x, rng)
        lyap_s.append(lyapunov_rosenstein(s, m, tau, theiler, dt=dt_tiempo)["lambda"])
        det_s.append(rqa(embeber(s, m, tau), theiler=theiler, miniatura=1)["determinismo"])
        pe_s.append(entropia_permutacion(s, orden=5, retardo=1))
    lyap_s_arr, det_s_arr = np.array(lyap_s), np.array(det_s)
    p_lyap = (1 + int(np.sum(lyap_s_arr >= lyap["lambda"]))) / (len(lyap_s_arr) + 1)
    p_det = (1 + int(np.sum(det_s_arr >= rq["determinismo"]))) / (len(det_s_arr) + 1)

    condiciones = {
        "no_linealidad_significativa": bool(no_lineal),
        "determinismo_prediccion_analogos": bool(nlpe["p"] <= alpha_holm),
        "d2_satura_bajo": bool(d2["satura"] and d2["d2_saturado"] is not None and d2["d2_saturado"] < 5),
        "lyapunov_positivo": bool(np.isfinite(lyap["lambda"]) and lyap["lambda"] > 0),
        "prueba_01_caotica": bool(np.isfinite(k01["K"]) and k01["K"] > 0.8),
    }
    if np.isfinite(k01["K"]) and k01["K"] < 0.2:
        veredicto = "regular"
    elif not no_lineal:
        veredicto = "lineal_estocastica"
    elif all(condiciones.values()):
        veredicto = "compatible_con_caos_baja_dimension"
    else:
        veredicto = "no_lineal_sin_caos_demostrado"

    return {
        **base,
        "veredicto": veredicto,
        "explicacion": VEREDICTOS[veredicto],
        "condiciones_caos": condiciones,
        "embedding": {
            "tau": tau,
            "metodo_tau": ret["metodo"],
            "tau_ami": ret.get("tau_ami"),
            "tau_acf": ret.get("tau_acf"),
            "m": m,
            "theiler": theiler,
            "ami": [round(v, 4) for v in ret["ami"]],
            "fnn": [round(v, 4) for v in fnn],
        },
        "no_linealidad": {
            "asimetria_temporal": {k: v for k, v in tra.items()},
            "error_prediccion_analogos": {k: v for k, v in nlpe.items()},
            "alpha": alpha,
            "correccion": "Holm-Bonferroni (2 pruebas): rechazo si p mínimo <= alpha/2",
        },
        "dimension_correlacion": d2,
        "lyapunov": {
            **lyap,
            "unidad": f"1/{unidad_tiempo}",
            "p_frente_sustitutos": p_lyap,
            "sustitutos": [round(float(v), 4) for v in lyap_s_arr],
        },
        "prueba_01": k01,
        "entropia_permutacion": {"original": pe, "sustitutos_media": float(np.mean(pe_s)), "orden": 5},
        "entropia_muestral": se,
        "recurrencia": {
            **rq,
            "p_determinismo_frente_sustitutos": p_det,
            "determinismo_sustitutos_media": float(np.mean(det_s_arr)),
        },
        "metodo": {
            "sustitutos": f"IAAFT, {n_sustitutos} para pruebas rápidas y {n_sustitutos_costosos} para invariantes",
            "referencias": [
                "Takens 1981",
                "Fraser y Swinney 1986",
                "Kennel et al. 1992",
                "Grassberger y Procaccia 1983",
                "Rosenstein et al. 1993",
                "Theiler et al. 1992",
                "Schreiber y Schmitz 1996",
                "Marwan et al. 2007",
                "Bandt y Pompe 2002",
                "Richman y Moorman 2000",
                "Gottwald y Melbourne 2004, 2009",
            ],
        },
    }
