"""Sensibilidad a los últimos años (hallazgo 3: 2023-24 saltan +1.1 a +1.5 °C y tienen mucha palanca)."""
from __future__ import annotations

import numpy as np

from .mk import mk_conservador
from .sen import sen_por_decada


def palanca_final(anios: np.ndarray, x: np.ndarray, quitar: int, signo_ref: float, alpha: float) -> dict:
    if quitar <= 0 or len(x) - quitar < 15:
        return {"evaluada": False}
    s, m = sen_por_decada(anios[:-quitar], x[:-quitar]), mk_conservador(x[:-quitar])
    return {"evaluada": True, "quitados": quitar, "sen_por_decada": s["sen_por_decada"],
            "p_conservador": m["p_conservador"],
            "sobrevive": bool(np.sign(s["pendiente"]) == signo_ref and m["p_conservador"] <= alpha)}
