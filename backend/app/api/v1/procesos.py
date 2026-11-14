"""Procesos científicos: solicitud, cola de trabajo, bitácora y estado."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.api.deps import Analista, PaginacionDep, PrincipalDep, SesionDep, Trabajador
from app.core.errors import Prohibido
from app.db.models import Proceso
from app.domain.vocabulario import Alcance, EstadoProceso, Rol, TipoProceso
from app.schemas.comun import Pagina, errores
from app.schemas.procesos import (
    EventoProcesoCrear,
    EventoProcesoSalida,
    ProcesoActualizar,
    ProcesoCrear,
    ProcesoSalida,
    ReclamoProceso,
)
from app.services import procesos as servicio
from app.services.comun import obtener_o_404

router = APIRouter(prefix="/procesos", tags=["Procesos"])


@router.get("", response_model=Pagina[ProcesoSalida], summary="Listar procesos")
def listar(
    sesion: SesionDep,
    pagina: PaginacionDep,
    estado: EstadoProceso | None = None,
    tipo: TipoProceso | None = None,
) -> Pagina[ProcesoSalida]:
    limite, desplazamiento = pagina
    items, total = servicio.listar(
        sesion, estado=estado, tipo=tipo, limite=limite, desplazamiento=desplazamiento
    )
    return Pagina(
        items=[ProcesoSalida.model_validate(p) for p in items],
        total=total,
        limite=limite,
        desplazamiento=desplazamiento,
    )


@router.post(
    "",
    response_model=ProcesoSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Solicitar un proceso científico",
    description="Queda `pendiente` hasta que un trabajador de ciencia de datos lo reclame.",
    responses=errores(400, 401, 403, 422),
)
def solicitar(datos: ProcesoCrear, analista: Analista, sesion: SesionDep) -> Proceso:
    return servicio.solicitar(sesion, datos, analista.etiqueta)


@router.post(
    "/reclamar",
    response_model=ProcesoSalida,
    summary="Reclamar el siguiente proceso pendiente (trabajador)",
    responses={**errores(401, 403, 422), 204: {"description": "No hay procesos pendientes de esos tipos."}},
)
def reclamar(datos: ReclamoProceso, principal: Trabajador, sesion: SesionDep) -> Proceso | Response:
    proceso = servicio.reclamar(sesion, datos.trabajador, datos.tipos, principal.id)
    if proceso is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return proceso


@router.get(
    "/{proceso_id}", response_model=ProcesoSalida, summary="Detalle de un proceso", responses=errores(404)
)
def obtener(proceso_id: str, sesion: SesionDep) -> Proceso:
    return obtener_o_404(sesion, Proceso, proceso_id, "Proceso")


@router.patch(
    "/{proceso_id}",
    response_model=ProcesoSalida,
    summary="Actualizar estado o progreso",
    description=(
        "Trabajador: progreso, `completado` (con `expediente_id`) o `fallido` (con `error`). "
        "Personas con rol analista: solo `cancelado`."
    ),
    responses=errores(400, 401, 403, 404, 409, 422),
)
def actualizar(
    proceso_id: str, datos: ProcesoActualizar, principal: PrincipalDep, sesion: SesionDep
) -> Proceso:
    if Alcance.trabajador in principal.alcances:
        return servicio.actualizar(sesion, proceso_id, datos, actor=principal.etiqueta, clave_id=principal.id)
    if not principal.tiene_rol(Rol.analista):
        raise Prohibido("Se requiere el rol 'analista' o una clave con alcance 'trabajador'.")
    return servicio.actualizar(sesion, proceso_id, datos, actor=principal.etiqueta, clave_id=None)


@router.get(
    "/{proceso_id}/eventos",
    response_model=list[EventoProcesoSalida],
    summary="Bitácora del proceso",
    description="Use `desde_id` para pedir solo los eventos nuevos (sondeo incremental).",
    responses=errores(404),
)
def eventos(
    proceso_id: str,
    sesion: SesionDep,
    desde_id: Annotated[int | None, Query(ge=0)] = None,
) -> list[EventoProcesoSalida]:
    return [EventoProcesoSalida.model_validate(e) for e in servicio.eventos(sesion, proceso_id, desde_id)]


@router.post(
    "/{proceso_id}/eventos",
    response_model=EventoProcesoSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un evento en la bitácora (trabajador)",
    responses=errores(401, 403, 404, 422),
)
def registrar_evento(
    proceso_id: str, datos: EventoProcesoCrear, principal: Trabajador, sesion: SesionDep
) -> EventoProcesoSalida:
    return EventoProcesoSalida.model_validate(
        servicio.registrar_evento(sesion, proceso_id, datos, principal.id)
    )
