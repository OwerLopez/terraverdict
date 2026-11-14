"""Matriz de Relevancia (M1) y registro de ejecuciones del pipeline."""

from __future__ import annotations

from fastapi import APIRouter, status
from sqlalchemy import select

from app.api.deps import Ingesta, PaginacionDep, SesionDep
from app.core.errors import Conflicto
from app.db.models import Ejecucion
from app.schemas.comun import Pagina, errores
from app.schemas.otros import EjecucionCrear, EjecucionSalida, MatrizRelevancia
from app.services.comun import paginar
from app.services.relevancia import construir_matriz

router = APIRouter(tags=["Ciencia de datos"])


@router.get(
    "/relevancia/matriz",
    response_model=MatrizRelevancia,
    summary="Matriz de Relevancia problema × variable",
    description=(
        "Se construye solo con expedientes de tipo `relevancia`. Si no hay ninguno, `estado = vacia` "
        "y `celdas = []`: la interfaz muestra las plantillas sin valores inventados."
    ),
)
def matriz(sesion: SesionDep, dominio_id: str | None = None) -> MatrizRelevancia:
    return construir_matriz(sesion, dominio_id)


@router.get(
    "/ejecuciones", response_model=Pagina[EjecucionSalida], summary="Ejecuciones registradas del pipeline"
)
def listar_ejecuciones(
    sesion: SesionDep, pagina: PaginacionDep, etapa: str | None = None
) -> Pagina[EjecucionSalida]:
    limite, desplazamiento = pagina
    consulta = select(Ejecucion).order_by(Ejecucion.iniciado.desc())
    if etapa:
        consulta = consulta.where(Ejecucion.etapa == etapa)
    items, total = paginar(sesion, consulta, limite, desplazamiento)
    return Pagina(
        items=[EjecucionSalida.model_validate(e) for e in items],
        total=total,
        limite=limite,
        desplazamiento=desplazamiento,
    )


@router.post(
    "/ejecuciones",
    response_model=EjecucionSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar el manifiesto de una ejecución del pipeline",
    responses=errores(401, 403, 409, 422),
)
def registrar_ejecucion(datos: EjecucionCrear, principal: Ingesta, sesion: SesionDep) -> EjecucionSalida:
    if sesion.get(Ejecucion, datos.id):
        raise Conflicto(f"La ejecución '{datos.id}' ya está registrada.")
    ejecucion = Ejecucion(**datos.model_dump(), registrado_por=principal.etiqueta)
    sesion.add(ejecucion)
    sesion.commit()
    return EjecucionSalida.model_validate(ejecucion)
