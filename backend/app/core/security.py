"""Contraseñas (Argon2id), tokens JWT y claves API para cuentas de servicio."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
import time
from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import Settings
from app.core.errors import DemasiadasSolicitudes, NoAutenticado

_hasher = PasswordHasher()
PREFIJO_CLAVE = "tv_"
LARGO_PREFIJO_BUSQUEDA = 12


def hashear_contrasena(contrasena: str) -> str:
    return _hasher.hash(contrasena)


def verificar_contrasena(hash_guardado: str, contrasena: str) -> bool:
    try:
        return _hasher.verify(hash_guardado, contrasena)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def necesita_rehash(hash_guardado: str) -> bool:
    return _hasher.check_needs_rehash(hash_guardado)


def crear_token(settings: Settings, *, sujeto: str, rol: str) -> tuple[str, int]:
    ahora = datetime.now(UTC)
    vence = ahora + timedelta(minutes=settings.jwt_minutos)
    carga = {"sub": sujeto, "rol": rol, "iat": ahora, "exp": vence, "iss": "terraverdict", "typ": "access"}
    token = jwt.encode(carga, settings.jwt_secreto.get_secret_value(), algorithm=settings.jwt_algoritmo)
    return token, settings.jwt_minutos * 60


def decodificar_token(settings: Settings, token: str) -> dict[str, Any]:
    try:
        carga: dict[str, Any] = jwt.decode(
            token,
            settings.jwt_secreto.get_secret_value(),
            algorithms=[settings.jwt_algoritmo],
            issuer="terraverdict",
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise NoAutenticado("El token expiró. Inicie sesión nuevamente.") from exc
    except jwt.PyJWTError as exc:
        raise NoAutenticado("Token inválido.") from exc
    if carga.get("typ") != "access":
        raise NoAutenticado("Tipo de token inválido.")
    return carga


def generar_clave_api() -> tuple[str, str, str]:
    """Devuelve ``(clave_en_claro, prefijo_busqueda, hash_sha256)``. La clave en claro se muestra una vez."""
    clave = PREFIJO_CLAVE + secrets.token_urlsafe(32)
    return clave, clave[:LARGO_PREFIJO_BUSQUEDA], hash_clave(clave)


def hash_clave(clave: str) -> str:
    return hashlib.sha256(clave.encode()).hexdigest()


def claves_iguales(hash_a: str, hash_b: str) -> bool:
    return hmac.compare_digest(hash_a, hash_b)


class LimitadorVentana:
    """Límite de intentos por clave en una ventana deslizante (memoria del proceso).

    Suficiente para una instancia. Con varias réplicas, el límite debe aplicarse en el
    proxy o con un almacén compartido (documentado en docs/arquitectura.md).
    """

    def __init__(self, maximo: int, ventana_s: float) -> None:
        self.maximo = maximo
        self.ventana_s = ventana_s
        self._registros: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def verificar(self, clave: str) -> None:
        ahora = time.monotonic()
        with self._lock:
            cola = self._registros[clave]
            while cola and ahora - cola[0] > self.ventana_s:
                cola.popleft()
            if len(cola) >= self.maximo:
                espera = int(self.ventana_s - (ahora - cola[0])) + 1
                raise DemasiadasSolicitudes(f"Demasiados intentos. Reintente en {espera} s.")
            cola.append(ahora)
