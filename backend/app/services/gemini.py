"""Cliente mínimo de la API de Google Gemini (``generateContent``), solo con la biblioteca estándar.

Decisiones:
- La clave viaja únicamente en la cabecera ``X-goog-api-key`` (nunca en la URL, para que no quede
  en registros de proxies) y se lee de ``TV_GEMINI_API_KEY`` en el servidor. El frontend nunca la ve.
- Cadena de modelos: primero ``gemini-flash-latest``; si responde 429/5xx o no responde a tiempo,
  se intenta el siguiente (``gemini-flash-lite-latest``). Un 400/401/403 no se reintenta: es un
  error de la petición o de la clave y repetir no lo arregla.
- Los mensajes de error nunca incluyen la clave ni el cuerpo completo de la respuesta.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

URL_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
REINTENTABLES = frozenset({408, 429, 500, 502, 503, 504})


class ErrorGemini(RuntimeError):
    """Fallo al consultar Gemini. ``reintentable`` indica si otro modelo podría responder."""

    def __init__(self, mensaje: str, *, estado: int | None = None, reintentable: bool = False) -> None:
        super().__init__(mensaje)
        self.estado = estado
        self.reintentable = reintentable


@dataclass(frozen=True)
class RespuestaGemini:
    texto: str
    modelo: str
    tokens_entrada: int | None
    tokens_salida: int | None
    latencia_s: float


Transporte = Callable[[urllib.request.Request, float], tuple[int, bytes]]


def _transporte_http(peticion: urllib.request.Request, timeout: float) -> tuple[int, bytes]:
    try:
        with urllib.request.urlopen(peticion, timeout=timeout) as r:  # noqa: S310 (URL fija https)
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


class ClienteGemini:
    def __init__(
        self,
        clave: str,
        modelos: Sequence[str],
        *,
        timeout_s: float = 20.0,
        transporte: Transporte = _transporte_http,
    ) -> None:
        if not clave:
            raise ValueError("Falta la clave de Gemini")
        if not modelos:
            raise ValueError("Se necesita al menos un modelo")
        self._clave = clave
        self.modelos = tuple(modelos)
        self.timeout_s = timeout_s
        self._transporte = transporte

    def generar(
        self,
        sistema: str,
        mensaje: str,
        *,
        temperatura: float = 0.2,
        max_tokens: int = 1024,
    ) -> RespuestaGemini:
        cuerpo: dict[str, Any] = {
            "systemInstruction": {"parts": [{"text": sistema}]},
            "contents": [{"role": "user", "parts": [{"text": mensaje}]}],
            "generationConfig": {"temperature": temperatura, "maxOutputTokens": max_tokens},
        }
        ultimo: ErrorGemini | None = None
        for modelo in self.modelos:
            try:
                return self._llamar(modelo, cuerpo)
            except ErrorGemini as e:
                ultimo = e
                if not e.reintentable:
                    raise
        raise ultimo or ErrorGemini("sin modelos configurados")

    def _llamar(self, modelo: str, cuerpo: dict[str, Any]) -> RespuestaGemini:
        peticion = urllib.request.Request(  # noqa: S310 (URL https fija, modelo validado por patrón)
            f"{URL_BASE}/{modelo}:generateContent",
            data=json.dumps(cuerpo).encode("utf-8"),
            headers={"Content-Type": "application/json", "X-goog-api-key": self._clave},
            method="POST",
        )
        inicio = time.monotonic()
        try:
            estado, datos = self._transporte(peticion, self.timeout_s)
        except TimeoutError as e:
            raise ErrorGemini(f"{modelo}: sin respuesta en {self.timeout_s:.0f} s", reintentable=True) from e
        except urllib.error.URLError as e:
            raise ErrorGemini(f"{modelo}: error de red ({type(e.reason).__name__})", reintentable=True) from e
        latencia = time.monotonic() - inicio
        if estado != 200:
            raise ErrorGemini(
                f"{modelo}: HTTP {estado} ({_mensaje_error(datos)})",
                estado=estado,
                reintentable=estado in REINTENTABLES,
            )
        try:
            j = json.loads(datos)
            candidato = j["candidates"][0]
            texto = "".join(p.get("text", "") for p in candidato["content"]["parts"] if not p.get("thought"))
        except (ValueError, KeyError, IndexError, TypeError) as e:
            motivo = _motivo_bloqueo(datos)
            raise ErrorGemini(f"{modelo}: respuesta sin texto ({motivo})", reintentable=False) from e
        if not texto.strip():
            raise ErrorGemini(
                f"{modelo}: respuesta vacía ({candidato.get('finishReason')})", reintentable=True
            )
        uso = j.get("usageMetadata", {})
        return RespuestaGemini(
            texto=texto.strip(),
            modelo=str(j.get("modelVersion") or modelo),
            tokens_entrada=uso.get("promptTokenCount"),
            tokens_salida=uso.get("candidatesTokenCount"),
            latencia_s=round(latencia, 2),
        )


def _mensaje_error(datos: bytes) -> str:
    try:
        return str(json.loads(datos)["error"].get("status", "error"))
    except (ValueError, KeyError, TypeError, AttributeError):
        return "respuesta no JSON"


def _motivo_bloqueo(datos: bytes) -> str:
    try:
        j = json.loads(datos)
        return str(j.get("promptFeedback", {}).get("blockReason") or j["candidates"][0].get("finishReason"))
    except (ValueError, KeyError, IndexError, TypeError, AttributeError):
        return "formato inesperado"
