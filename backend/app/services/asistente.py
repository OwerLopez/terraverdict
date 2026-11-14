"""Contrato del asistente conversacional (módulo M6).

El asistente todavía no está conectado. Este módulo define la interfaz que debe cumplir
cualquier proveedor (por ejemplo, un modelo de lenguaje con herramientas que solo leen
expedientes) y la garantía que la API impone siempre: el texto generado pasa por el
verificador numérico antes de llegar al usuario.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from app.core.config import Settings
from app.core.errors import ServicioNoDisponible


@dataclass(frozen=True)
class RespuestaAsistente:
    texto: str
    expedientes_citados: list[str]
    herramientas_usadas: list[str] = field(default_factory=list)


class ProveedorAsistente(Protocol):
    """Interfaz para conectar el asistente sin cambiar la API.

    Una implementación debe: (1) consultar solo herramientas de lectura del núcleo,
    (2) devolver los IDs de los expedientes que respaldan cada cifra, y (3) no calcular
    resultados científicos. La API verificará las cifras con ``services.verificador``.
    """

    def responder(self, pregunta: str, expediente_ids: list[str]) -> RespuestaAsistente: ...


class AsistenteNoConectado:
    def responder(self, pregunta: str, expediente_ids: list[str]) -> RespuestaAsistente:
        raise ServicioNoDisponible(
            "El asistente conversacional todavía no está conectado. El contrato está en "
            "docs/integracion-ciencia-datos.md; mientras tanto, POST /asistente/verificar ya "
            "aplica la garantía del verificador numérico."
        )


def obtener_proveedor(settings: Settings) -> ProveedorAsistente:
    """Punto único de conexión. Hoy siempre devuelve el estado 'no conectado'."""
    del settings  # la clave del proveedor se leerá aquí cuando se integre el módulo
    return AsistenteNoConectado()


def asistente_conectado(settings: Settings) -> bool:
    return not isinstance(obtener_proveedor(settings), AsistenteNoConectado)
