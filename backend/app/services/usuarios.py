"""Usuarios, autenticación y claves API."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import security
from app.core.errors import Conflicto
from app.db.models import ClaveApi, Usuario
from app.domain.vocabulario import Rol
from app.schemas.auth import ClaveCrear, UsuarioActualizar, UsuarioCrear
from app.services.comun import obtener_o_404


def crear_usuario(sesion: Session, datos: UsuarioCrear) -> Usuario:
    if sesion.scalar(select(Usuario).where(func.lower(Usuario.email) == datos.email.lower())):
        raise Conflicto(f"Ya existe un usuario con el correo {datos.email}.")
    usuario = Usuario(
        email=datos.email.lower(),
        nombre=datos.nombre,
        hash_contrasena=security.hashear_contrasena(datos.contrasena),
        rol=datos.rol.value,
    )
    sesion.add(usuario)
    sesion.commit()
    return usuario


def autenticar(sesion: Session, email: str, contrasena: str) -> Usuario | None:
    usuario = sesion.scalar(select(Usuario).where(func.lower(Usuario.email) == email.strip().lower()))
    if usuario is None:
        security.hashear_contrasena(contrasena)  # tiempo constante aproximado: no revela si el correo existe
        return None
    if not usuario.activo or not security.verificar_contrasena(usuario.hash_contrasena, contrasena):
        return None
    if security.necesita_rehash(usuario.hash_contrasena):
        usuario.hash_contrasena = security.hashear_contrasena(contrasena)
        sesion.commit()
    return usuario


def actualizar_usuario(sesion: Session, usuario_id: str, datos: UsuarioActualizar) -> Usuario:
    usuario = obtener_o_404(sesion, Usuario, usuario_id, "Usuario")
    if datos.nombre is not None:
        usuario.nombre = datos.nombre
    if datos.rol is not None:
        usuario.rol = datos.rol.value
    if datos.activo is not None:
        usuario.activo = datos.activo
    sesion.commit()
    return usuario


def asegurar_admin(sesion: Session, email: str, contrasena: str, nombre: str = "Administración") -> bool:
    """Crea el administrador inicial si no existe. Devuelve True si lo creó."""
    if sesion.scalar(select(Usuario).where(func.lower(Usuario.email) == email.lower())):
        return False
    crear_usuario(sesion, UsuarioCrear(email=email, nombre=nombre, contrasena=contrasena, rol=Rol.admin))
    return True


def crear_clave(sesion: Session, datos: ClaveCrear, creado_por: str | None) -> tuple[ClaveApi, str]:
    clave, prefijo, hash_ = security.generar_clave_api()
    registro = ClaveApi(
        nombre=datos.nombre,
        prefijo=prefijo,
        hash_clave=hash_,
        alcances=sorted({a.value for a in datos.alcances}),
        creado_por=creado_por,
    )
    sesion.add(registro)
    sesion.commit()
    return registro, clave


def resolver_clave(sesion: Session, clave: str) -> ClaveApi | None:
    if not clave.startswith(security.PREFIJO_CLAVE) or len(clave) < 20:
        return None
    registro = sesion.scalar(
        select(ClaveApi).where(ClaveApi.prefijo == clave[: security.LARGO_PREFIJO_BUSQUEDA])
    )
    if registro is None or not registro.activa:
        return None
    if not security.claves_iguales(registro.hash_clave, security.hash_clave(clave)):
        return None
    registro.ultimo_uso = datetime.now(UTC)
    sesion.commit()
    return registro


def revocar_clave(sesion: Session, clave_id: str) -> None:
    registro = obtener_o_404(sesion, ClaveApi, clave_id, "Clave API")
    registro.activa = False
    sesion.commit()
