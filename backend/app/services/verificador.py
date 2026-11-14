"""Verificador numérico determinista: ninguna cifra sin respaldo llega al usuario.

Extrae las cifras de un texto en español (``0,23``, ``−0,345``, ``1.234,5``, ``39 %``,
``10 135``) y comprueba que cada una coincida, con el redondeo que usa el texto, con algún
valor permitido (los valores numéricos de los expedientes consultados). Los años (1900–2100
sin decimales) se omiten porque son metadatos del periodo, no resultados.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

_PATRON = re.compile(
    r"(?<![\w.,])"
    r"(?P<signo>[−\-+])?"
    r"(?P<num>\d{1,3}(?:[.   ]\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?)"
    r"(?P<pct>\s?%)?"
    r"(?![\w])"
)


@dataclass(frozen=True)
class Cifra:
    texto: str
    valor: float
    decimales: int
    porcentaje: bool


def _a_numero(crudo: str) -> tuple[float, int]:
    limpio = crudo.replace(" ", " ").replace(" ", " ")
    if re.fullmatch(r"\d{1,3}(?:[. ]\d{3})+(?:,\d+)?", limpio):
        limpio = limpio.replace(".", "").replace(" ", "")
    decimales = (
        len(limpio.split(",")[1]) if "," in limpio else (len(limpio.split(".")[1]) if "." in limpio else 0)
    )
    return float(limpio.replace(",", ".")), decimales


def extraer_cifras(texto: str, *, ignorar_anios: bool = True) -> list[Cifra]:
    cifras: list[Cifra] = []
    for m in _PATRON.finditer(texto):
        valor, decimales = _a_numero(m.group("num"))
        if m.group("signo") in ("-", "−"):
            valor = -valor
        porcentaje = bool(m.group("pct"))
        if ignorar_anios and decimales == 0 and not porcentaje and 1900 <= valor <= 2100:
            continue
        cifras.append(Cifra(m.group(0).strip(), valor, decimales, porcentaje))
    return cifras


def valores_numericos(objeto: Any) -> list[float]:
    """Todos los números finitos dentro de una estructura JSON (excluye booleanos)."""
    salida: list[float] = []
    if isinstance(objeto, bool):
        return salida
    if isinstance(objeto, int | float):
        if math.isfinite(objeto):
            salida.append(float(objeto))
    elif isinstance(objeto, dict):
        for v in objeto.values():
            salida.extend(valores_numericos(v))
    elif isinstance(objeto, list | tuple):
        for v in objeto:
            salida.extend(valores_numericos(v))
    return salida


def _coincide(cifra: Cifra, valor: float, tolerancia_relativa: float) -> bool:
    """La cifra coincide si es un redondeo válido del valor (± media unidad del último decimal
    escrito) o si difiere menos que la tolerancia relativa."""
    candidatos = [valor, valor * 100] if cifra.porcentaje else [valor]
    media_unidad = 0.5 * 10 ** (-cifra.decimales) + 1e-9
    return any(
        abs(c - cifra.valor) <= media_unidad
        or abs(c - cifra.valor) <= tolerancia_relativa * max(abs(c), 1e-12)
        for c in candidatos
    )


@dataclass(frozen=True)
class Resultado:
    aprobado: bool
    cifras: list[tuple[Cifra, float | None]]

    @property
    def no_trazables(self) -> list[str]:
        return [c.texto for c, v in self.cifras if v is None]


def verificar(texto: str, permitidos: Iterable[float], tolerancia_relativa: float = 0.005) -> Resultado:
    valores = list(permitidos)
    evaluadas: list[tuple[Cifra, float | None]] = []
    for cifra in extraer_cifras(texto):
        match = next((v for v in valores if _coincide(cifra, v, tolerancia_relativa)), None)
        evaluadas.append((cifra, match))
    return Resultado(aprobado=all(v is not None for _, v in evaluadas), cifras=evaluadas)
