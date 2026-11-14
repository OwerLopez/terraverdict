"""Salud del servicio, resumen del sistema y vocabularios."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from sqlalchemy import func, select, text

from app import __version__
from app.api.deps import ConfigDep, SesionDep
from app.core.errors import ServicioNoDisponible
from app.db.models import (
    Ejecucion,
    EventoDocumentado,
    Expediente,
    Fuente,
    InformeVerificacion,
    Observacion,
    Proceso,
    Serie,
)
from app.domain.unidades_medida import UNIDADES_MEDIDA
from app.schemas.catalogo import UnidadMedidaSalida
from app.schemas.comun import Mensaje, errores
from app.schemas.otros import ConteoPorClave, ConteoVerificacion, ResumenSistema
from app.services import asistente, procesos

router = APIRouter(tags=["Sistema"])


@router.get("/salud", response_model=Mensaje, summary="Vida del proceso (liveness)")
def salud() -> Mensaje:
    return Mensaje(mensaje="ok")


@router.get(
    "/salud/lista",
    response_model=Mensaje,
    summary="Preparación (readiness): base de datos accesible",
    responses=errores(503),
)
def salud_lista(sesion: SesionDep) -> Mensaje:
    try:
        sesion.execute(text("SELECT 1"))
    except Exception as exc:
        raise ServicioNoDisponible("La base de datos no responde.") from exc
    return Mensaje(mensaje="lista")


def _conteos(sesion: SesionDep, columna: Any) -> list[ConteoPorClave]:
    filas = sesion.execute(select(columna, func.count()).group_by(columna).order_by(columna)).all()
    return [ConteoPorClave(clave=str(clave), total=int(total)) for clave, total in filas]


def _informe(sesion: SesionDep, tipo: str) -> ConteoVerificacion | None:
    informe = sesion.scalar(
        select(InformeVerificacion)
        .where(InformeVerificacion.tipo == tipo)
        .order_by(InformeVerificacion.generado_utc.desc())
    )
    if informe is None:
        return None
    return ConteoVerificacion(
        generado_utc=informe.generado_utc, total=informe.total, correctas=informe.correctas
    )


@router.get("/resumen", response_model=ResumenSistema, summary="Estado agregado del sistema para el panel")
def resumen(sesion: SesionDep, settings: ConfigDep) -> ResumenSistema:
    return ResumenSistema(
        version_api=__version__,
        fuentes_total=sesion.scalar(select(func.count()).select_from(Fuente)) or 0,
        fuentes_por_estado=_conteos(sesion, Fuente.estado_verificacion),
        verificacion_fuentes=_informe(sesion, "fuentes"),
        verificacion_enlaces=_informe(sesion, "enlaces"),
        series_total=sesion.scalar(select(func.count()).select_from(Serie)) or 0,
        observaciones_total=sesion.scalar(select(func.count()).select_from(Observacion)) or 0,
        expedientes_por_tipo=_conteos(sesion, Expediente.tipo),
        procesos_por_estado=_conteos(sesion, Proceso.estado),
        eventos_documentados=sesion.scalar(select(func.count()).select_from(EventoDocumentado)) or 0,
        ultima_ejecucion=sesion.scalar(select(func.max(Ejecucion.registrado_en))),
        asistente_conectado=asistente.asistente_conectado(settings),
        trabajadores_activos=procesos.trabajadores_activos(sesion),
    )


@router.get(
    "/unidades-medida",
    response_model=list[UnidadMedidaSalida],
    summary="Vocabulario controlado de unidades de medida (compatible con UCUM)",
)
def unidades_medida() -> list[UnidadMedidaSalida]:
    return [UnidadMedidaSalida.model_validate(u, from_attributes=True) for u in UNIDADES_MEDIDA.values()]
