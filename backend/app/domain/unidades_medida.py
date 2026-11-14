"""Vocabulario controlado de unidades de medida (códigos compatibles con UCUM).

Toda serie publicada declara su unidad con uno de estos códigos. La conversión de
unidades es responsabilidad del pipeline (etapa E3), nunca del cliente.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UnidadMedida:
    codigo: str
    simbolo: str
    nombre: str
    ucum: str


UNIDADES_MEDIDA: dict[str, UnidadMedida] = {
    u.codigo: u
    for u in (
        UnidadMedida("mm", "mm", "milímetros de lámina de agua", "mm"),
        UnidadMedida("mm/d", "mm/día", "milímetros por día", "mm/d"),
        UnidadMedida("mm/h", "mm/h", "milímetros por hora", "mm/h"),
        UnidadMedida("Cel", "°C", "grados Celsius", "Cel"),
        UnidadMedida("K", "K", "kelvin", "K"),
        UnidadMedida("1", "—", "adimensional", "1"),
        UnidadMedida("%", "%", "porcentaje", "%"),
        UnidadMedida("m3/m3", "m³/m³", "contenido volumétrico de agua", "m3/m3"),
        UnidadMedida("km2", "km²", "kilómetros cuadrados", "km2"),
        UnidadMedida("ha", "ha", "hectáreas", "har"),
        UnidadMedida("hm3", "hm³", "hectómetros cúbicos (millones de m³)", "hm3"),
        UnidadMedida("m3/s", "m³/s", "metros cúbicos por segundo", "m3/s"),
        UnidadMedida("m", "m", "metros", "m"),
        UnidadMedida("m/s", "m/s", "metros por segundo", "m/s"),
        UnidadMedida("MJ/m2/d", "MJ m⁻² día⁻¹", "megajulios por metro cuadrado por día", "MJ/m2/d"),
        UnidadMedida("deg", "°", "grados de ángulo", "deg"),
        UnidadMedida("count", "n", "conteo", "{count}"),
        UnidadMedida("NTU", "NTU", "unidades nefelométricas de turbidez", "[NTU]"),
        UnidadMedida("MUSD", "M US$", "millones de dólares estadounidenses", "[USD]"),
    )
}


def es_unidad_valida(codigo: str) -> bool:
    return codigo in UNIDADES_MEDIDA
