"""Series temporales: registro, carga idempotente de observaciones y consulta."""

from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.errors import Conflicto
from app.db.models import Dominio, Fuente, Observacion, Serie, Unidad, Variable
from app.schemas.series import ObservacionesCarga, ResultadoCarga, SerieCrear
from app.services.comun import exigir_existencia, obtener_o_404, paginar


def crear_serie(sesion: Session, datos: SerieCrear) -> Serie:
    if sesion.get(Serie, datos.id) is not None:
        raise Conflicto(
            f"La serie '{datos.id}' ya existe. Use PUT /series/{{id}}/observaciones para cargar datos."
        )
    exigir_existencia(
        sesion,
        {
            "dominio_id": (Dominio, datos.dominio_id),
            "unidad_id": (Unidad, datos.unidad_id),
            "variable_id": (Variable, datos.variable_id),
            "fuente_id": (Fuente, datos.fuente_id),
        },
    )
    exigir_existencia(
        sesion,
        {f"procedencia.fuentes.{f.fuente_id}": (Fuente, f.fuente_id) for f in datos.procedencia.fuentes},
    )
    serie = Serie(
        id=datos.id,
        dominio_id=datos.dominio_id,
        unidad_id=datos.unidad_id,
        variable_id=datos.variable_id,
        fuente_id=datos.fuente_id,
        unidad=datos.unidad,
        frecuencia=datos.frecuencia.value,
        agregacion=datos.agregacion,
        descripcion=datos.descripcion,
        procedencia=datos.procedencia.model_dump(mode="json"),
    )
    sesion.add(serie)
    sesion.commit()
    return serie


def cargar_observaciones(sesion: Session, serie_id: str, carga: ObservacionesCarga) -> ResultadoCarga:
    """Inserta o actualiza observaciones por fecha (idempotente) y versiona la serie."""
    serie = obtener_o_404(sesion, Serie, serie_id, "Serie")
    if carga.reemplazar:
        sesion.execute(delete(Observacion).where(Observacion.serie_id == serie_id))
        existentes: dict[date, Observacion] = {}
    else:
        fechas = [o.t for o in carga.observaciones]
        existentes = {
            o.t: o
            for o in sesion.scalars(
                select(Observacion).where(Observacion.serie_id == serie_id, Observacion.t.in_(fechas))
            )
        }
    insertadas = actualizadas = 0
    for obs in carga.observaciones:
        previa = existentes.get(obs.t)
        if previa is None:
            sesion.add(
                Observacion(
                    serie_id=serie_id,
                    t=obs.t,
                    valor=obs.valor,
                    frac_valida=obs.frac_valida,
                    calidad=obs.calidad,
                )
            )
            insertadas += 1
        elif (previa.valor, previa.frac_valida, previa.calidad) != (obs.valor, obs.frac_valida, obs.calidad):
            previa.valor, previa.frac_valida, previa.calidad = obs.valor, obs.frac_valida, obs.calidad
            actualizadas += 1
    sesion.flush()
    minimo, maximo, total = sesion.execute(
        select(func.min(Observacion.t), func.max(Observacion.t), func.count()).where(
            Observacion.serie_id == serie_id
        )
    ).one()
    if insertadas or actualizadas or carga.reemplazar:
        serie.version += 1
        serie.actualizado_en = datetime.now(UTC)
    serie.t_inicio, serie.t_fin, serie.n_observaciones = minimo, maximo, int(total)
    sesion.commit()
    return ResultadoCarga(
        serie_id=serie_id,
        insertadas=insertadas,
        actualizadas=actualizadas,
        version=serie.version,
        t_inicio=serie.t_inicio,
        t_fin=serie.t_fin,
        n_observaciones=serie.n_observaciones,
    )


def listar_series(
    sesion: Session,
    *,
    dominio_id: str | None,
    unidad_id: str | None,
    variable_id: str | None,
    fuente_id: str | None,
    limite: int,
    desplazamiento: int,
) -> tuple[list[Serie], int]:
    consulta = select(Serie).order_by(Serie.id)
    if dominio_id:
        consulta = consulta.where(Serie.dominio_id == dominio_id)
    if unidad_id:
        consulta = consulta.where(Serie.unidad_id == unidad_id)
    if variable_id:
        consulta = consulta.where(Serie.variable_id == variable_id)
    if fuente_id:
        consulta = consulta.where(Serie.fuente_id == fuente_id)
    return paginar(sesion, consulta, limite, desplazamiento)


def observaciones(
    sesion: Session, serie_id: str, desde: date | None, hasta: date | None
) -> tuple[Serie, list[Observacion]]:
    serie = obtener_o_404(sesion, Serie, serie_id, "Serie")
    consulta = select(Observacion).where(Observacion.serie_id == serie_id).order_by(Observacion.t)
    if desde:
        consulta = consulta.where(Observacion.t >= desde)
    if hasta:
        consulta = consulta.where(Observacion.t <= hasta)
    return serie, list(sesion.scalars(consulta))
