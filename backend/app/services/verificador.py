"""Verificador numérico determinista: ninguna cifra sin respaldo llega al usuario.

Extrae las cifras de un texto en español (``0,23``, ``−0,345``, ``1.234,5``, ``39 %``,
``10 135``) y comprueba que cada una coincida, con el redondeo que usa el texto, con algún
valor permitido (los valores numéricos de los expedientes consultados). Los años (1900–2100
sin decimales) se omiten porque son metadatos del periodo, no resultados.

Una coincidencia solo es evidencia si no es probable por azar. Para cada cifra respaldada se
calcula la probabilidad de que una cifra INVENTADA con el mismo formato (mismo signo, mismos
decimales y mismo orden de magnitud) caiga dentro de la tolerancia de algún valor permitido.
Si supera ``ALFA_COINCIDENCIA`` (0,05, el nivel convencional de una prueba), la coincidencia se
marca como débil. Esto reemplaza al antiguo tope fijo de 1000 valores de respaldo de la web, que
no tenía derivación (auditoría de métricas, 2026-11-15).
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


ALFA_COINCIDENCIA = 0.05
TOLERANCIA_RELATIVA = 0.005  # media unidad del tercer dígito significativo: 0,711 ≈ 0,7114


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


def _radio(valor: float, decimales: int, tolerancia_relativa: float) -> float:
    return max(0.5 * 10 ** (-decimales) + 1e-9, tolerancia_relativa * abs(valor))


def probabilidad_azar(cifra: Cifra, permitidos: Iterable[float], tolerancia_relativa: float) -> float:
    """Fracción del rango de cifras con el mismo formato que coincidiría con algún valor permitido.

    Rango: el orden de magnitud de la cifra, [10^e, 10^(e+1)), con su signo (o [0, 10·paso) si la
    cifra es menor que un paso del último decimal). Es la probabilidad de que un número inventado,
    uniforme en ese rango, pase el verificador.
    """
    paso = 10 ** (-cifra.decimales)
    magnitud = abs(cifra.valor)
    if magnitud < paso:
        lo, hi = 0.0, 10 * paso
    else:
        e = math.floor(math.log10(magnitud))
        lo, hi = 10.0**e, 10.0 ** (e + 1)
    signo = -1.0 if cifra.valor < 0 else 1.0
    intervalos = []
    for v in permitidos:
        for c in [v, v * 100] if cifra.porcentaje else [v]:
            if c * signo < 0 and c != 0:
                continue
            r = _radio(c, cifra.decimales, tolerancia_relativa)
            a, b = max(lo, abs(c) - r), min(hi, abs(c) + r)
            if b > a:
                intervalos.append((a, b))
    if not intervalos:
        return 0.0
    intervalos.sort()
    cubierto, inicio, fin = 0.0, intervalos[0][0], intervalos[0][1]
    for a, b in intervalos[1:]:
        if a > fin:
            cubierto += fin - inicio
            inicio, fin = a, b
        else:
            fin = max(fin, b)
    cubierto += fin - inicio
    return min(1.0, cubierto / (hi - lo))


@dataclass(frozen=True)
class Resultado:
    aprobado: bool
    cifras: list[tuple[Cifra, float | None]]
    azar: tuple[float | None, ...] = ()

    @property
    def no_trazables(self) -> list[str]:
        return [c.texto for c, v in self.cifras if v is None]

    @property
    def coincidencias_debiles(self) -> list[str]:
        """Cifras respaldadas cuya coincidencia sería probable por azar (p > ALFA_COINCIDENCIA)."""
        return [
            c.texto
            for (c, v), p in zip(self.cifras, self.azar, strict=False)
            if v is not None and p is not None and p > ALFA_COINCIDENCIA
        ]


def verificar(
    texto: str, permitidos: Iterable[float], tolerancia_relativa: float = TOLERANCIA_RELATIVA
) -> Resultado:
    valores = list(permitidos)
    evaluadas: list[tuple[Cifra, float | None]] = []
    azar: list[float | None] = []
    for cifra in extraer_cifras(texto):
        match = next((v for v in valores if _coincide(cifra, v, tolerancia_relativa)), None)
        evaluadas.append((cifra, match))
        azar.append(probabilidad_azar(cifra, valores, tolerancia_relativa) if match is not None else None)
    return Resultado(aprobado=all(v is not None for _, v in evaluadas), cifras=evaluadas, azar=tuple(azar))
