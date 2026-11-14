"""Expedientes: resultados científicos inmutables con procedencia completa."""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.api.deps import Admin, Ingesta, PaginacionDep, SesionDep
from app.db.models import Expediente
from app.domain.vocabulario import EstadoExpediente, TipoExpediente
from app.schemas.comun import Pagina, errores
from app.schemas.expedientes import (
    ExpedienteCrear,
    ExpedienteResumen,
    ExpedienteRetirar,
    ExpedienteSalida,
    extraer_veredicto,
)
from app.services import expedientes as servicio
from app.services.comun import obtener_o_404

router = APIRouter(prefix="/expedientes", tags=["Expedientes"])


def _resumen(e: Expediente) -> ExpedienteResumen:
    return ExpedienteResumen.model_validate(
        {
            **{c: getattr(e, c) for c in ExpedienteResumen.model_fields if c != "veredicto"},
            "veredicto": extraer_veredicto(e.resultado),
        }
    )


def _salida(e: Expediente) -> ExpedienteSalida:
    return ExpedienteSalida.model_validate(
        {
            **{c: getattr(e, c) for c in ExpedienteSalida.model_fields if c != "veredicto"},
            "veredicto": extraer_veredicto(e.resultado),
        }
    )


@router.get("", response_model=Pagina[ExpedienteResumen], summary="Listar expedientes")
def listar(
    sesion: SesionDep,
    pagina: PaginacionDep,
    tipo: TipoExpediente | None = None,
    estado: EstadoExpediente | None = None,
    dominio_id: str | None = None,
    unidad_id: str | None = None,
    variable_id: str | None = None,
    serie_id: str | None = None,
    incluir_retirados: bool = False,
) -> Pagina[ExpedienteResumen]:
    limite, desplazamiento = pagina
    items, total = servicio.listar(
        sesion,
        tipo=tipo,
        estado=estado,
        dominio_id=dominio_id,
        unidad_id=unidad_id,
        variable_id=variable_id,
        serie_id=serie_id,
        incluir_retirados=incluir_retirados,
        limite=limite,
        desplazamiento=desplazamiento,
    )
    return Pagina(
        items=[_resumen(e) for e in items], total=total, limite=limite, desplazamiento=desplazamiento
    )


@router.post(
    "",
    response_model=ExpedienteSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Publicar un expediente (pipeline)",
    description=(
        "El ID se deriva del contenido (`TV-<TIPO>-<hash>`). Publicar el mismo contenido devuelve "
        "**200** con el expediente existente (idempotente). Las reglas científicas de publicación "
        "se validan en el esquema y producen **422** si no se cumplen."
    ),
    responses={
        **errores(401, 403, 404, 409, 422),
        200: {"model": ExpedienteSalida, "description": "Ya existía."},
    },
)
def publicar(
    datos: ExpedienteCrear, principal: Ingesta, sesion: SesionDep, response: Response
) -> ExpedienteSalida:
    expediente, creado = servicio.publicar(sesion, datos, principal.etiqueta)
    response.status_code = status.HTTP_201_CREATED if creado else status.HTTP_200_OK
    response.headers["Location"] = f"/api/v1/expedientes/{expediente.id}"
    return _salida(expediente)


@router.get(
    "/{expediente_id}",
    response_model=ExpedienteSalida,
    summary="Detalle de un expediente",
    responses=errores(404),
)
def obtener(expediente_id: str, sesion: SesionDep) -> ExpedienteSalida:
    return _salida(obtener_o_404(sesion, Expediente, expediente_id, "Expediente"))


@router.post(
    "/{expediente_id}/retirar",
    response_model=ExpedienteSalida,
    summary="Retirar un expediente (se conserva por trazabilidad)",
    responses=errores(401, 403, 404, 409, 422),
)
def retirar(
    expediente_id: str, datos: ExpedienteRetirar, admin: Admin, sesion: SesionDep
) -> ExpedienteSalida:
    return _salida(servicio.retirar(sesion, expediente_id, datos.motivo, admin.etiqueta))
