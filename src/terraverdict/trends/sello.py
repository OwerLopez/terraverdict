"""Sello de Confianza: tabla de decisión DETERMINISTA y auditable.

Pruebas no evaluadas (None) impiden el veredicto 'robusta': con una sola familia de datos
el máximo posible es 'fragil' y lo dice (principio del proyecto).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..config import Preregistro

EMOJI = {"robusta": "🟢", "fragil": "🟡", "no_decidible": "⚪", "sin_tendencia": "🔵"}


@dataclass
class Veredicto:
    codigo: str
    fallan: list[str] = field(default_factory=list)
    pendientes: list[str] = field(default_factory=list)
    nota: str = ""

    @property
    def emoji(self) -> str:
        return EMOJI[self.codigo]


def decidir(r: dict, pre: Preregistro) -> Veredicto:
    """r: salida de analizar_serie (claves: mk, sen, ventanas, enso, sensor, independencia, detectabilidad)."""
    p = r["mk"]["p_conservador"]
    signo = (r["sen"]["pendiente"] > 0) - (r["sen"]["pendiente"] < 0)
    if p > pre.alpha:
        n_nec = (r.get("detectabilidad") or {}).get("anios_necesarios")
        n_disp = (r.get("detectabilidad") or {}).get("anios_disponibles")
        if n_nec is not None and n_disp is not None and n_nec > n_disp:
            return Veredicto("no_decidible", nota=f"faltan ~{n_nec - n_disp:.0f} años para detectarla")
        marginal = " (marginal: p ≤ 2·alpha, revisar con otra familia)" if p <= 2 * pre.alpha else ""
        return Veredicto("sin_tendencia", nota="p conservador > alpha y hay años suficientes" + marginal)

    fallan, pend = [], []
    v = r.get("ventanas")
    if not v or v.get("pct_mismo_signo") is None:
        pend.append("ventanas")
    elif v["pct_mismo_signo"] / 100 < pre.u_ventanas:
        fallan.append("ventanas")

    e = r.get("enso")
    if not e or not e.get("evaluada"):
        pend.append("enso")
    elif not (e["pendiente_sin_enso_por_decada"] * signo > 0 and e["p_pendiente_sin_enso_hac"] <= pre.alpha):
        fallan.append("enso")

    s = r.get("sensor")
    if not s:
        pend.append("sensor")
    else:
        for q in s["quiebres"].values():
            if q.get("aplicable") and (q["cambia_signo"] or (q["cambio_relativo_b"] or 0) > pre.tol_sensor):
                fallan.append("sensor")
                break

    pl = r.get("palanca")
    if pl and pl.get("evaluada") and not pl["sobrevive"]:
        fallan.append("palanca")

    i = r.get("independencia")
    if not i:
        pend.append("independencia")
    elif i["n_familias_mismo_signo"] < pre.min_familias:
        fallan.append("independencia")

    if fallan or pend:
        return Veredicto("fragil", sorted(set(fallan)), pend,
                         "pruebas pendientes impiden 'robusta'" if pend and not fallan else "")
    return Veredicto("robusta")
