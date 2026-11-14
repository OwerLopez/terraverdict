"""Mann-Kendall con p CONSERVADOR.

Hallazgo de la revisión (lluvia dic-mar, n=43): MK p=0.057, Hamed-Rao p=0.0002,
Yue-Wang p~5e-8, pre-blanqueo p=0.109. Una corrección por autocorrelación no debe
hacer la tendencia MÁS significativa; con autocorrelaciones negativas en algún lag,
Hamed-Rao e Yue-Wang lo hacen. Regla: p conservador = máximo de las variantes
declaradas en el preregistro. Se guardan TODAS para auditoría.
"""

from __future__ import annotations

import numpy as np
import pymannkendall as pmk

_VARIANTES = {
    "original": pmk.original_test,
    "hamed_rao": pmk.hamed_rao_modification_test,
    "prewhitening": pmk.pre_whitening_modification_test,
}


def mk_conservador(x: np.ndarray, variantes: list[str] | None = None) -> dict:
    variantes = variantes or list(_VARIANTES)
    import warnings

    ps: dict[str, float] = {}
    invalidas: list[str] = []
    for v in variantes:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            p = float(_VARIANTES[v](x).p)
        if np.isfinite(p):
            ps[v] = p
        else:  # varianza negativa -> p = NaN: se registra como inválida
            invalidas.append(v)
    if not ps:
        raise ValueError("Ninguna variante de Mann-Kendall produjo un p válido")
    peor = max(ps, key=lambda k: ps[k])
    return {"p_variantes": ps, "p_invalidas": invalidas, "p_conservador": ps[peor], "variante_limitante": peor}
