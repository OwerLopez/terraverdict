"""Independencia por FAMILIA de procedencia: cuenta familias, no productos."""

from __future__ import annotations


def familias_mismo_signo(resultados: list[dict], productos: dict, signo_ref: float) -> dict:
    """resultados: [{'producto': 'IMERG_FINAL', 'sen': 0.4}, ...] (incluye el producto primario)."""
    por_familia: dict[str, list[float]] = {}
    for r in resultados:
        fam = productos.get(r["producto"], {}).get("familia", r["producto"])
        por_familia.setdefault(fam, []).append(r["sen"])
    coinciden = [f for f, v in por_familia.items() if sum((s > 0) - (s < 0) for s in v) * signo_ref > 0]
    return {
        "familias_evaluadas": sorted(por_familia),
        "familias_mismo_signo": sorted(coinciden),
        "n_familias_mismo_signo": len(coinciden),
    }
