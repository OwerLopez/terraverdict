"""Cola de procesos científicos con máquina de estados explícita.

Protocolo para los trabajadores de ciencia de datos (cuenta de servicio con alcance
``trabajador``):

1. ``POST /procesos/reclamar`` con sus tipos → recibe el proceso pendiente más prioritario
   (pasa a ``en_curso`` de forma atómica) o 204 si no hay trabajo.
2. ``POST /procesos/{id}/eventos`` para registrar su bitácora (también actualiza el latido).
3. ``PATCH /procesos/{id}`` con ``progreso`` y, al final, ``estado=completado`` y
   ``expediente_id``, o ``estado=fallido`` y ``error``.

La implementación usa la base de datos como cola. Puede sustituirse por un broker
(Redis, RabbitMQ) sin cambiar este contrato HTTP.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.errors import ErrorDominio, Prohibido, TransicionInvalida
from app.db.models import EventoProceso, Expediente, Proceso
from app.domain.vocabulario import (
    PARAMETROS_REQUERIDOS,
    TRANSICIONES_PROCESO,
    EstadoProceso,
    TipoProceso,
)
from app.schemas.procesos import EventoProcesoCrear, ProcesoActualizar, ProcesoCrear
from app.services.comun import exigir_existencia, obtener_o_404, paginar

VENTANA_TRABAJADOR_ACTIVO = timedelta(minutes=5)


def solicitar(sesion: Session, datos: ProcesoCrear, solicitante: str) -> Proceso:
    faltan = sorted(PARAMETROS_REQUERIDOS[datos.tipo] - datos.parametros.keys())
    if faltan:
        raise ErrorDominio(
            f"Faltan parámetros para un proceso de tipo '{datos.tipo.value}'.",
            errores=[
                {"campo": f"parametros.{f}", "mensaje": "requerido", "tipo": "faltante"} for f in faltan
            ],
        )
    proceso = Proceso(
        tipo=datos.tipo.value,
        parametros=datos.parametros,
        prioridad=datos.prioridad,
        solicitado_por=solicitante,
    )
    sesion.add(proceso)
    sesion.flush()
    sesion.add(EventoProceso(proceso_id=proceso.id, nivel="info", mensaje=f"Solicitado por {solicitante}."))
    sesion.commit()
    return proceso


def reclamar(sesion: Session, trabajador: str, tipos: list[TipoProceso], clave_id: str) -> Proceso | None:
    """Asigna atómicamente el proceso pendiente más prioritario (seguro con varios trabajadores)."""
    candidatos = sesion.scalars(
        select(Proceso.id)
        .where(Proceso.estado == EstadoProceso.pendiente.value, Proceso.tipo.in_([t.value for t in tipos]))
        .order_by(Proceso.prioridad.desc(), Proceso.creado_en)
        .limit(10)
    ).all()
    ahora = datetime.now(UTC)
    for candidato in candidatos:
        resultado = sesion.execute(
            update(Proceso)
            .where(Proceso.id == candidato, Proceso.estado == EstadoProceso.pendiente.value)
            .values(
                estado=EstadoProceso.en_curso.value,
                trabajador=trabajador,
                reclamado_por=clave_id,
                iniciado_en=ahora,
                ultimo_latido=ahora,
            )
        )
        if resultado.rowcount == 1:  # type: ignore[attr-defined]
            sesion.add(
                EventoProceso(proceso_id=candidato, nivel="info", mensaje=f"Reclamado por {trabajador}.")
            )
            sesion.commit()
            return sesion.get(Proceso, candidato)
        sesion.rollback()
    return None


def _exigir_propietario(proceso: Proceso, clave_id: str) -> None:
    if proceso.reclamado_por is not None and proceso.reclamado_por != clave_id:
        raise Prohibido(f"El proceso está asignado a otro trabajador ('{proceso.trabajador}').")


def actualizar(
    sesion: Session, proceso_id: str, datos: ProcesoActualizar, *, actor: str, clave_id: str | None
) -> Proceso:
    """``clave_id`` es la clave API del trabajador; ``None`` si actúa una persona (solo puede cancelar)."""
    proceso = obtener_o_404(sesion, Proceso, proceso_id, "Proceso")
    actual = EstadoProceso(proceso.estado)
    ahora = datetime.now(UTC)
    es_trabajador = clave_id is not None

    if not es_trabajador and (
        datos.estado != EstadoProceso.cancelado or datos.progreso is not None or datos.expediente_id
    ):
        raise Prohibido(
            "Las personas usuarias solo pueden cancelar procesos; el resto lo actualiza el trabajador."
        )
    if clave_id is not None:
        _exigir_propietario(proceso, clave_id)

    if datos.estado is not None and datos.estado != actual:
        if datos.estado not in TRANSICIONES_PROCESO[actual]:
            raise TransicionInvalida(f"No se puede pasar de '{actual.value}' a '{datos.estado.value}'.")
        if datos.estado == EstadoProceso.completado:
            if not datos.expediente_id:
                raise ErrorDominio("Un proceso completado debe indicar el expediente_id que produjo.")
            exigir_existencia(sesion, {"expediente_id": (Expediente, datos.expediente_id)})
        if datos.estado == EstadoProceso.fallido and datos.error is None:
            raise ErrorDominio("Un proceso fallido debe incluir 'error'.")
        proceso.estado = datos.estado.value
        if datos.estado in (EstadoProceso.completado, EstadoProceso.fallido, EstadoProceso.cancelado):
            proceso.finalizado_en = ahora
        sesion.add(
            EventoProceso(
                proceso_id=proceso.id,
                nivel="error" if datos.estado == EstadoProceso.fallido else "info",
                mensaje=f"Estado: {actual.value} → {datos.estado.value} ({actor}).",
                datos=datos.error.model_dump() if datos.error else None,
            )
        )
    elif datos.estado is None and actual not in (EstadoProceso.en_curso,) and (datos.progreso is not None):
        raise TransicionInvalida("Solo se informa progreso de un proceso en curso.")

    if datos.progreso is not None:
        proceso.progreso = datos.progreso
    if datos.expediente_id is not None:
        proceso.expediente_id = datos.expediente_id
    if datos.error is not None:
        proceso.error = datos.error.model_dump()
    if es_trabajador:
        proceso.ultimo_latido = ahora
    sesion.commit()
    return proceso


def registrar_evento(
    sesion: Session, proceso_id: str, datos: EventoProcesoCrear, clave_id: str
) -> EventoProceso:
    proceso = obtener_o_404(sesion, Proceso, proceso_id, "Proceso")
    _exigir_propietario(proceso, clave_id)
    evento = EventoProceso(
        proceso_id=proceso_id, nivel=datos.nivel.value, mensaje=datos.mensaje, datos=datos.datos
    )
    proceso.ultimo_latido = datetime.now(UTC)
    sesion.add(evento)
    sesion.commit()
    return evento


def listar(
    sesion: Session,
    *,
    estado: EstadoProceso | None,
    tipo: TipoProceso | None,
    limite: int,
    desplazamiento: int,
) -> tuple[list[Proceso], int]:
    consulta = select(Proceso).order_by(Proceso.creado_en.desc())
    if estado:
        consulta = consulta.where(Proceso.estado == estado.value)
    if tipo:
        consulta = consulta.where(Proceso.tipo == tipo.value)
    return paginar(sesion, consulta, limite, desplazamiento)


def eventos(sesion: Session, proceso_id: str, desde_id: int | None) -> list[EventoProceso]:
    obtener_o_404(sesion, Proceso, proceso_id, "Proceso")
    consulta = select(EventoProceso).where(EventoProceso.proceso_id == proceso_id).order_by(EventoProceso.id)
    if desde_id is not None:
        consulta = consulta.where(EventoProceso.id > desde_id)
    return list(sesion.scalars(consulta))


def trabajadores_activos(sesion: Session) -> int:
    limite = datetime.now(UTC) - VENTANA_TRABAJADOR_ACTIVO
    valor: Any = sesion.scalar(
        select(func.count(func.distinct(Proceso.trabajador))).where(
            Proceso.trabajador.is_not(None), Proceso.ultimo_latido >= limite
        )
    )
    return int(valor or 0)
