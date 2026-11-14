"""Asistente conversacional (no conectado todavía) y verificador numérico (activo)."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import ConfigDep, SesionDep
from app.db.models import Expediente
from app.schemas.comun import errores
from app.schemas.otros import (
    CifraDetectada,
    ConsultaAsistente,
    RespuestaAsistenteSalida,
    ResultadoVerificacionTexto,
    SolicitudVerificacion,
)
from app.services import asistente, verificador
from app.services.comun import exigir_existencia

router = APIRouter(prefix="/asistente", tags=["Asistente"])


@router.post(
    "/consultas",
    response_model=RespuestaAsistenteSalida,
    summary="Preguntar al asistente (módulo pendiente de conexión)",
    description=(
        "Hoy responde **503** con `codigo = servicio_no_disponible`: el proveedor todavía no está conectado. "
        "Cuando lo esté, cada respuesta pasará por el verificador numérico antes de devolverse."
    ),
    responses=errores(422, 503),
)
def consultar(datos: ConsultaAsistente, settings: ConfigDep) -> RespuestaAsistenteSalida:
    respuesta = asistente.obtener_proveedor(settings).responder(datos.pregunta, datos.expediente_ids)
    return RespuestaAsistenteSalida(texto=respuesta.texto, expedientes_citados=respuesta.expedientes_citados)


@router.post(
    "/verificar",
    response_model=ResultadoVerificacionTexto,
    summary="Verificar que cada cifra de un texto esté respaldada por expedientes",
    description=(
        "Extrae las cifras del texto (formato en español) y comprueba que cada una coincida, con su "
        "redondeo, con algún valor numérico de los expedientes indicados. Los años se omiten."
    ),
    responses=errores(404, 422),
)
def verificar(datos: SolicitudVerificacion, sesion: SesionDep) -> ResultadoVerificacionTexto:
    exigir_existencia(
        sesion, {f"expediente_ids[{i}]": (Expediente, e) for i, e in enumerate(datos.expediente_ids)}
    )
    expedientes = sesion.scalars(select(Expediente).where(Expediente.id.in_(datos.expediente_ids)))
    permitidos = [v for e in expedientes for v in verificador.valores_numericos(e.resultado)]
    resultado = verificador.verificar(datos.texto, permitidos, datos.tolerancia_relativa)
    return ResultadoVerificacionTexto(
        aprobado=resultado.aprobado,
        cifras=[
            CifraDetectada(texto=c.texto, valor=c.valor, trazable=v is not None, coincide_con=v)
            for c, v in resultado.cifras
        ],
        no_trazables=resultado.no_trazables,
        valores_permitidos=len(permitidos),
    )
