"""Matriz de Relevancia (M1): se construye solo con expedientes de tipo ``relevancia``.

Si no hay expedientes, la matriz se devuelve con ``estado = "vacia"``: la interfaz muestra
las plantillas de problema y las variables candidatas, sin ninguna importancia inventada.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Expediente, Problema, Variable
from app.domain.vocabulario import EstadoExpediente, TipoExpediente
from app.schemas.catalogo import ProblemaSalida, VariableSalida
from app.schemas.otros import CeldaRelevancia, MatrizRelevancia


def construir_matriz(sesion: Session, dominio_id: str | None) -> MatrizRelevancia:
    problemas = list(sesion.scalars(select(Problema).order_by(Problema.id)))
    consulta = (
        select(Expediente)
        .where(
            Expediente.tipo == TipoExpediente.relevancia.value,
            Expediente.estado != EstadoExpediente.retirado.value,
        )
        .order_by(Expediente.creado_en.desc())
    )
    if dominio_id:
        consulta = consulta.where(Expediente.dominio_id == dominio_id)

    ultimo_por_problema: dict[str, Expediente] = {}
    for exp in sesion.scalars(consulta):
        ultimo_por_problema.setdefault(str(exp.resultado.get("problema_id")), exp)

    celdas: list[CeldaRelevancia] = []
    variables_usadas: set[str] = set()
    for problema_id, exp in ultimo_por_problema.items():
        for v in exp.resultado.get("variables", []):
            variables_usadas.add(v["variable_id"])
            celdas.append(
                CeldaRelevancia(
                    problema_id=problema_id,
                    variable_id=v["variable_id"],
                    importancia=v["importancia"],
                    estabilidad=v["estabilidad"],
                    p_ajustado=v.get("p_ajustado"),
                    direccion=v["direccion"],
                    expediente_id=exp.id,
                    publicable=bool(exp.resultado.get("publicable")),
                )
            )

    candidatas = {c for p in problemas for c in p.candidatas} | variables_usadas
    variables = list(
        sesion.scalars(select(Variable).where(Variable.id.in_(candidatas)).order_by(Variable.id))
    )
    vacia = not celdas
    return MatrizRelevancia(
        estado="vacia" if vacia else "disponible",
        mensaje=(
            "Todavía no hay resultados de relevancia publicados por el pipeline. Se muestran las "
            "plantillas de problema y sus variables candidatas."
            if vacia
            else f"Resultados de {len(ultimo_por_problema)} problema(s); se usa el expediente más reciente de cada uno."
        ),
        problemas=[ProblemaSalida.model_validate(p) for p in problemas],
        variables=[VariableSalida.model_validate(v) for v in variables],
        celdas=celdas,
        expedientes=[e.id for e in ultimo_por_problema.values()],
    )
