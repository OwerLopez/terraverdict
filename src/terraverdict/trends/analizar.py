"""Orquesta las pruebas sobre UNA serie anual. Entrada pura -> salida JSON-serializable."""

from __future__ import annotations

import numpy as np

from ..config import Preregistro
from .detectabilidad import detectabilidad
from .enso import filtro_enso
from .independencia import familias_mismo_signo
from .mk import mk_conservador
from .palanca import palanca_final
from .sello import decidir
from .sen import sen_por_decada
from .sensor import prueba_sensor
from .ventanas import ventanas


def analizar_serie(
    anios: np.ndarray,
    x: np.ndarray,
    pre: Preregistro,
    *,
    oni: dict[int, float] | None = None,
    otras_familias: list[dict] | None = None,
    productos: dict | None = None,
    producto_primario: str = "POWER_MERRA2",
    con_ventanas: bool = True,
) -> dict:
    anios, x = np.asarray(anios, float), np.asarray(x, float)
    sen = sen_por_decada(anios, x, pre.ic_nivel)
    res: dict = {"n": len(x), "periodo": [int(anios[0]), int(anios[-1])], "sen": sen, "mk": mk_conservador(x)}
    res["ventanas"] = ventanas(anios, x, np.sign(sen["pendiente"]), pre.L_min, pre.alpha) if con_ventanas else None
    res["enso"] = filtro_enso(anios, x, oni) if oni else None
    q = pre.quiebres(producto_primario)
    res["sensor"] = prueba_sensor(anios, x, q)
    res["sensor"]["quiebres_declarados"] = q
    res["palanca"] = palanca_final(anios, x, pre.palanca_n, np.sign(sen["pendiente"]), pre.alpha)
    res["detectabilidad"] = detectabilidad(anios, x, sen["pendiente"], sen["ordenada"])
    if otras_familias is not None and productos is not None:
        res["independencia"] = familias_mismo_signo(
            [{"producto": producto_primario, "sen": sen["pendiente"]}, *otras_familias],
            productos,
            np.sign(sen["pendiente"]),
        )
    else:
        res["independencia"] = None
    v = decidir(res, pre)
    res["sello"] = {
        "codigo": v.codigo,
        "emoji": v.emoji,
        "fallan": v.fallan,
        "pendientes": v.pendientes,
        "nota": v.nota,
    }
    return res
