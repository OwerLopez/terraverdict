"""Esquemas de autenticación, usuarios y claves API."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

from app.domain.vocabulario import Alcance, Rol
from app.schemas.comun import Esquema

Email = Annotated[
    str, StringConstraints(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=255, to_lower=True)
]


class Token(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"  # noqa: S105 (tipo de token OAuth2, no es un secreto)
    expira_en: int = Field(description="Segundos de validez del token.")
    rol: Rol


class Identidad(BaseModel):
    tipo: Literal["usuario", "servicio"]
    id: str
    nombre: str
    rol: Rol | None = None
    alcances: list[Alcance] = []


class UsuarioCrear(Esquema):
    email: Email
    nombre: Annotated[str, StringConstraints(min_length=2, max_length=120)]
    contrasena: Annotated[str, StringConstraints(min_length=12, max_length=256)]
    rol: Rol = Rol.lector


class UsuarioActualizar(Esquema):
    nombre: Annotated[str, StringConstraints(min_length=2, max_length=120)] | None = None
    rol: Rol | None = None
    activo: bool | None = None


class UsuarioSalida(Esquema):
    id: str
    email: str
    nombre: str
    rol: Rol
    activo: bool
    creado_en: datetime


class ClaveCrear(Esquema):
    nombre: Annotated[str, StringConstraints(min_length=3, max_length=120)]
    alcances: list[Alcance] = Field(min_length=1)


class ClaveSalida(Esquema):
    id: str
    nombre: str
    prefijo: str
    alcances: list[Alcance]
    activa: bool
    creado_en: datetime
    ultimo_uso: datetime | None = None


class ClaveCreada(ClaveSalida):
    clave: str = Field(description="Se muestra una sola vez. Guárdela en un gestor de secretos.")
