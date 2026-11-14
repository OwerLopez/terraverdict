"""Autenticación (OAuth2 con contraseña → JWT), usuarios y claves API de servicio."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.api.deps import Admin, ConfigDep, PrincipalDep, SesionDep
from app.core.errors import NoAutenticado
from app.core.security import LimitadorVentana, crear_token
from app.db.models import ClaveApi, Usuario
from app.domain.vocabulario import Rol
from app.schemas.auth import (
    ClaveCreada,
    ClaveCrear,
    ClaveSalida,
    Identidad,
    Token,
    UsuarioActualizar,
    UsuarioCrear,
    UsuarioSalida,
)
from app.schemas.comun import errores
from app.services import usuarios as servicio

router = APIRouter(tags=["Autenticación y acceso"])


@router.post(
    "/auth/token",
    response_model=Token,
    summary="Iniciar sesión (OAuth2, flujo de contraseña)",
    description="Envíe `username` (correo) y `password` como formulario. Devuelve un JWT Bearer.",
    responses=errores(401, 429),
)
def iniciar_sesion(
    request: Request,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    sesion: SesionDep,
    settings: ConfigDep,
) -> Token:
    limitador: LimitadorVentana = request.app.state.limitador_login
    limitador.verificar(request.client.host if request.client else "desconocido")
    usuario = servicio.autenticar(sesion, form.username, form.password)
    if usuario is None:
        raise NoAutenticado("Correo o contraseña incorrectos.")
    token, segundos = crear_token(settings, sujeto=usuario.id, rol=usuario.rol)
    return Token(access_token=token, expira_en=segundos, rol=Rol(usuario.rol))


@router.get("/auth/yo", response_model=Identidad, summary="Identidad autenticada", responses=errores(401))
def yo(principal: PrincipalDep) -> Identidad:
    return Identidad(
        tipo=principal.tipo,
        id=principal.id,
        nombre=principal.nombre,
        rol=principal.rol,
        alcances=sorted(principal.alcances),
    )


@router.get(
    "/usuarios", response_model=list[UsuarioSalida], summary="Listar usuarios", responses=errores(401, 403)
)
def listar_usuarios(_: Admin, sesion: SesionDep) -> list[Usuario]:
    return list(sesion.scalars(select(Usuario).order_by(Usuario.creado_en)))


@router.post(
    "/usuarios",
    response_model=UsuarioSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario",
    responses=errores(401, 403, 409, 422),
)
def crear_usuario(datos: UsuarioCrear, _: Admin, sesion: SesionDep) -> Usuario:
    return servicio.crear_usuario(sesion, datos)


@router.patch(
    "/usuarios/{usuario_id}",
    response_model=UsuarioSalida,
    summary="Actualizar rol, nombre o estado de un usuario",
    responses=errores(401, 403, 404, 422),
)
def actualizar_usuario(usuario_id: str, datos: UsuarioActualizar, _: Admin, sesion: SesionDep) -> Usuario:
    return servicio.actualizar_usuario(sesion, usuario_id, datos)


@router.get(
    "/claves", response_model=list[ClaveSalida], summary="Listar claves API", responses=errores(401, 403)
)
def listar_claves(_: Admin, sesion: SesionDep) -> list[ClaveApi]:
    return list(sesion.scalars(select(ClaveApi).order_by(ClaveApi.creado_en)))


@router.post(
    "/claves",
    response_model=ClaveCreada,
    status_code=status.HTTP_201_CREATED,
    summary="Crear clave API para una cuenta de servicio",
    description="La clave en claro se devuelve **una sola vez**. Alcances: `ingesta`, `trabajador`.",
    responses=errores(401, 403, 422),
)
def crear_clave(datos: ClaveCrear, admin: Admin, sesion: SesionDep) -> ClaveCreada:
    registro, clave = servicio.crear_clave(sesion, datos, admin.id)
    return ClaveCreada(**ClaveSalida.model_validate(registro).model_dump(), clave=clave)


@router.delete(
    "/claves/{clave_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revocar una clave API",
    responses=errores(401, 403, 404),
)
def revocar_clave(clave_id: str, _: Admin, sesion: SesionDep) -> Response:
    servicio.revocar_clave(sesion, clave_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
