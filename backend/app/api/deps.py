"""Dependencias de la API: sesión, configuración, identidad y autorización (RBAC + alcances)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Annotated, Literal

from fastapi import Depends, Query, Request
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import NoAutenticado, Prohibido
from app.core.security import decodificar_token
from app.db.models import Usuario
from app.db.session import obtener_sesion
from app.domain.vocabulario import RANGO_ROL, Alcance, Rol
from app.services import usuarios as servicio_usuarios

oauth2 = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token", auto_error=False, description="Token JWT de usuario."
)
clave_api = APIKeyHeader(
    name="X-API-Key", auto_error=False, description="Clave de cuenta de servicio (pipeline y trabajadores)."
)

SesionDep = Annotated[Session, Depends(obtener_sesion)]


def obtener_config(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


ConfigDep = Annotated[Settings, Depends(obtener_config)]


@dataclass(frozen=True)
class Principal:
    tipo: Literal["usuario", "servicio"]
    id: str
    nombre: str
    rol: Rol | None = None
    alcances: frozenset[Alcance] = field(default_factory=frozenset)

    @property
    def etiqueta(self) -> str:
        return f"{self.tipo}:{self.nombre}"

    def tiene_rol(self, minimo: Rol) -> bool:
        return self.rol is not None and RANGO_ROL[self.rol] >= RANGO_ROL[minimo]


def principal_opcional(
    sesion: SesionDep,
    settings: ConfigDep,
    token: Annotated[str | None, Depends(oauth2)],
    clave: Annotated[str | None, Depends(clave_api)],
) -> Principal | None:
    if clave:
        registro = servicio_usuarios.resolver_clave(sesion, clave)
        if registro is None:
            raise NoAutenticado("Clave API inválida o revocada.")
        return Principal(
            "servicio", registro.id, registro.nombre, None, frozenset(Alcance(a) for a in registro.alcances)
        )
    if token:
        carga = decodificar_token(settings, token)
        usuario = sesion.get(Usuario, carga["sub"])
        if usuario is None or not usuario.activo:
            raise NoAutenticado("La cuenta no existe o está desactivada.")
        return Principal("usuario", usuario.id, usuario.email, Rol(usuario.rol))
    return None


PrincipalOpcional = Annotated[Principal | None, Depends(principal_opcional)]


def principal_requerido(principal: PrincipalOpcional) -> Principal:
    if principal is None:
        raise NoAutenticado("Se requiere un token Bearer o una clave X-API-Key.")
    return principal


PrincipalDep = Annotated[Principal, Depends(principal_requerido)]


def requiere_rol(minimo: Rol) -> Callable[[Principal], Principal]:
    def dependencia(principal: PrincipalDep) -> Principal:
        if not principal.tiene_rol(minimo):
            raise Prohibido(f"Se requiere el rol '{minimo.value}' o superior.")
        return principal

    return dependencia


def requiere_alcance(alcance: Alcance) -> Callable[[Principal], Principal]:
    """Permite cuentas de servicio con el alcance indicado o usuarios administradores."""

    def dependencia(principal: PrincipalDep) -> Principal:
        if alcance in principal.alcances or principal.tiene_rol(Rol.admin):
            return principal
        raise Prohibido(f"Se requiere el alcance '{alcance.value}' (clave API) o el rol 'admin'.")

    return dependencia


Admin = Annotated[Principal, Depends(requiere_rol(Rol.admin))]
Analista = Annotated[Principal, Depends(requiere_rol(Rol.analista))]
Ingesta = Annotated[Principal, Depends(requiere_alcance(Alcance.ingesta))]
Trabajador = Annotated[Principal, Depends(requiere_alcance(Alcance.trabajador))]


def paginacion(
    limite: Annotated[int, Query(ge=1, le=500, description="Elementos por página.")] = 50,
    desplazamiento: Annotated[int, Query(ge=0, description="Elementos a saltar.")] = 0,
) -> tuple[int, int]:
    return limite, desplazamiento


PaginacionDep = Annotated[tuple[int, int], Depends(paginacion)]
