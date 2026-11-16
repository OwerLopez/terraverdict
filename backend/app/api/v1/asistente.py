"""Asistente conversacional con Gemini (anclado en expedientes y verificado) y verificador numérico."""

from __future__ import annotations

from fastapi import APIRouter, Request
from sqlalchemy import select

from app.api.deps import ConfigDep, SesionDep
from app.core.security import LimitadorVentana, ip_cliente
from app.db.models import Expediente
from app.domain.vocabulario import EstadoExpediente
from app.schemas.comun import errores
from app.schemas.otros import (
    CifraDetectada,
    ConsultaAsistente,
    ExpedienteConsultado,
    RespuestaAsistenteSalida,
    ResultadoVerificacionTexto,
    SolicitudVerificacion,
)
from app.services import asistente, verificador
from app.services.comun import exigir_existencia

router = APIRouter(prefix="/asistente", tags=["Asistente"])


def _informe(resultado: verificador.Resultado, n_permitidos: int) -> ResultadoVerificacionTexto:
    return ResultadoVerificacionTexto(
        aprobado=resultado.aprobado,
        cifras=[
            CifraDetectada(
                texto=c.texto, valor=c.valor, trazable=v is not None, coincide_con=v, probabilidad_azar=p
            )
            for (c, v), p in zip(resultado.cifras, resultado.azar, strict=True)
        ],
        no_trazables=resultado.no_trazables,
        valores_permitidos=n_permitidos,
        alfa_coincidencia=verificador.ALFA_COINCIDENCIA,
        coincidencias_debiles=resultado.coincidencias_debiles,
    )


def _contexto(e: Expediente) -> asistente.ExpedienteContexto:
    return asistente.ExpedienteContexto(
        id=e.id, tipo=e.tipo, titulo=e.titulo, resumen=e.resumen, resultado=e.resultado
    )


@router.post(
    "/consultas",
    response_model=RespuestaAsistenteSalida,
    summary="Preguntar al asistente (Gemini, anclado en expedientes publicados y verificado)",
    description=(
        "Elige los expedientes publicados más pertinentes (o los indicados), pide a Google Gemini una "
        "respuesta que solo use esas cifras y cite sus IDs, y verifica cada cifra contra los expedientes "
        "citados. Si alguna no tiene respaldo, pide una reescritura. La respuesta incluye siempre el "
        "informe de verificación. **429** si se supera el límite por IP o global; **503** si el proveedor "
        "no está configurado o no responde."
    ),
    responses=errores(404, 422, 429, 503),
)
def consultar(
    datos: ConsultaAsistente, request: Request, sesion: SesionDep, settings: ConfigDep
) -> RespuestaAsistenteSalida:
    proveedor = asistente.obtener_proveedor(settings)
    por_ip: LimitadorVentana = request.app.state.limitador_asistente
    global_: LimitadorVentana = request.app.state.limitador_asistente_global
    por_ip.verificar(ip_cliente(request))
    global_.verificar("global")

    publicados = list(
        sesion.scalars(select(Expediente).where(Expediente.estado != EstadoExpediente.retirado))
    )
    if datos.expediente_ids:
        exigir_existencia(
            sesion, {f"expediente_ids[{i}]": (Expediente, e) for i, e in enumerate(datos.expediente_ids)}
        )
        pedidos = set(datos.expediente_ids)
        contexto = [_contexto(e) for e in publicados if e.id in pedidos]
    else:
        contexto = asistente.seleccionar(datos.pregunta, [_contexto(e) for e in publicados])
    elegidos = {c.id for c in contexto}
    catalogo = [f"{e.titulo} [{e.id}]" for e in publicados if e.id not in elegidos]

    r = proveedor.responder(datos.pregunta, contexto, catalogo)
    return RespuestaAsistenteSalida(
        texto=r.texto,
        expedientes_citados=r.expedientes_citados,
        expedientes_consultados=[
            ExpedienteConsultado(id=c.id, tipo=c.tipo, titulo=c.titulo) for c in r.expedientes_consultados
        ],
        verificacion=_informe(r.verificacion, r.valores_permitidos),
        modelo=r.modelo,
        intentos=r.intentos,
        latencia_s=r.latencia_s,
    )


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
    return _informe(resultado, len(permitidos))
