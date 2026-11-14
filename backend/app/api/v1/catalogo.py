"""Catálogo público: fuentes verificadas, variables, problemas, eventos documentados y verificación."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.api.deps import SesionDep
from app.db.models import EventoDocumentado, Fuente, InformeVerificacion, Problema, Variable
from app.domain.vocabulario import CategoriaEvento, EstadoVerificacion
from app.schemas.catalogo import (
    EventoDocumentadoSalida,
    FuenteSalida,
    InformeVerificacionSalida,
    ProblemaSalida,
    VariableSalida,
    VerificacionResumen,
)
from app.schemas.comun import errores
from app.services.comun import obtener_o_404

router = APIRouter(tags=["Catálogo"])


@router.get(
    "/fuentes", response_model=list[FuenteSalida], summary="Fuentes de datos y su estado de verificación"
)
def listar_fuentes(
    sesion: SesionDep,
    estado: Annotated[
        EstadoVerificacion | None, Query(description="Filtrar por estado de verificación.")
    ] = None,
    familia: Annotated[str | None, Query(description="Familia de procedencia.")] = None,
) -> list[Fuente]:
    consulta = select(Fuente).order_by(Fuente.id)
    if estado:
        consulta = consulta.where(Fuente.estado_verificacion == estado.value)
    if familia:
        consulta = consulta.where(Fuente.familia == familia)
    return list(sesion.scalars(consulta))


@router.get(
    "/fuentes/{fuente_id}",
    response_model=FuenteSalida,
    summary="Detalle de una fuente",
    responses=errores(404),
)
def obtener_fuente(fuente_id: str, sesion: SesionDep) -> Fuente:
    return obtener_o_404(sesion, Fuente, fuente_id, "Fuente")


@router.get("/variables", response_model=list[VariableSalida], summary="Catálogo de variables físicas")
def listar_variables(sesion: SesionDep, grupo: str | None = None) -> list[Variable]:
    consulta = select(Variable).order_by(Variable.grupo, Variable.id)
    if grupo:
        consulta = consulta.where(Variable.grupo == grupo)
    return list(sesion.scalars(consulta))


@router.get(
    "/variables/{variable_id}",
    response_model=VariableSalida,
    summary="Detalle de una variable",
    responses=errores(404),
)
def obtener_variable(variable_id: str, sesion: SesionDep) -> Variable:
    return obtener_o_404(sesion, Variable, variable_id, "Variable")


@router.get(
    "/problemas",
    response_model=list[ProblemaSalida],
    summary="Plantillas de problema de la Matriz de Relevancia",
)
def listar_problemas(sesion: SesionDep) -> list[Problema]:
    return list(sesion.scalars(select(Problema).order_by(Problema.id)))


@router.get(
    "/eventos",
    response_model=list[EventoDocumentadoSalida],
    summary="Eventos documentados con sus fuentes citadas",
)
def listar_eventos(sesion: SesionDep, categoria: CategoriaEvento | None = None) -> list[EventoDocumentado]:
    consulta = select(EventoDocumentado).order_by(EventoDocumentado.fecha.desc())
    if categoria:
        consulta = consulta.where(EventoDocumentado.categoria == categoria.value)
    return list(sesion.scalars(consulta))


@router.get(
    "/verificacion",
    response_model=VerificacionResumen,
    summary="Último informe de verificación de fuentes y enlaces",
)
def verificacion(sesion: SesionDep) -> VerificacionResumen:
    def ultimo(tipo: str) -> InformeVerificacionSalida | None:
        informe = sesion.scalar(
            select(InformeVerificacion)
            .where(InformeVerificacion.tipo == tipo)
            .order_by(InformeVerificacion.generado_utc.desc())
        )
        return InformeVerificacionSalida.model_validate(informe) if informe else None

    estados = dict(
        sesion.execute(
            select(Fuente.estado_verificacion, func.count()).group_by(Fuente.estado_verificacion)
        ).all()
    )
    return VerificacionResumen(
        fuentes=ultimo("fuentes"),
        enlaces=ultimo("enlaces"),
        estados_fuentes={k: int(v) for k, v in estados.items()},
    )
