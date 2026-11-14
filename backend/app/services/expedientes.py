"""Expedientes: publicación inmutable con identificador derivado del contenido.

El ID es ``TV-<TIPO>-<12 hex del SHA-256>`` del contenido canónico. Publicar dos veces el
mismo contenido devuelve el mismo expediente (idempotencia), y cualquier cambio en datos,
parámetros o procedencia produce un expediente nuevo. Nada se edita: se reemplaza.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import Conflicto
from app.db.models import Dominio, Expediente, Fuente, Problema, Serie, Unidad, Variable
from app.domain.vocabulario import (
    ABREVIATURA_EXPEDIENTE,
    MODULO_POR_TIPO,
    EstadoExpediente,
    TipoExpediente,
)
from app.schemas.expedientes import ExpedienteCrear, ResultadoRelevancia
from app.services.comun import exigir_existencia, obtener_o_404, paginar


def contenido_canonico(datos: ExpedienteCrear) -> str:
    return json.dumps(
        datos.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def calcular_id(tipo: TipoExpediente, hash_contenido: str) -> str:
    return f"TV-{ABREVIATURA_EXPEDIENTE[tipo]}-{hash_contenido[:12].upper()}"


def publicar(sesion: Session, datos: ExpedienteCrear, creado_por: str) -> tuple[Expediente, bool]:
    """Devuelve ``(expediente, creado)``; ``creado`` es False si el contenido ya existía."""
    canonico = contenido_canonico(datos)
    hash_contenido = hashlib.sha256(canonico.encode()).hexdigest()
    existente = sesion.scalar(select(Expediente).where(Expediente.hash_contenido == hash_contenido))
    if existente is not None:
        return existente, False

    tipo = TipoExpediente(datos.resultado.tipo)
    referencias: dict[str, tuple[type[Any], Any]] = {
        "dominio_id": (Dominio, datos.dominio_id),
        "unidad_id": (Unidad, datos.unidad_id),
        "variable_id": (Variable, datos.variable_id),
        "serie_id": (Serie, datos.serie_id),
        "reemplaza_a": (Expediente, datos.reemplaza_a),
    }
    referencias.update(
        {f"procedencia.fuentes[{i}]": (Fuente, f.fuente_id) for i, f in enumerate(datos.procedencia.fuentes)}
    )
    if isinstance(datos.resultado, ResultadoRelevancia):
        referencias["resultado.problema_id"] = (Problema, datos.resultado.problema_id)
        referencias.update(
            {
                f"resultado.variables[{i}]": (Variable, v.variable_id)
                for i, v in enumerate(datos.resultado.variables)
            }
        )
    exigir_existencia(sesion, referencias)

    if datos.reemplaza_a:
        anterior = obtener_o_404(sesion, Expediente, datos.reemplaza_a, "Expediente")
        if anterior.tipo != tipo.value:
            raise Conflicto("Un expediente solo puede reemplazar a otro del mismo tipo.")
        anterior.estado = EstadoExpediente.retirado.value

    expediente = Expediente(
        id=calcular_id(tipo, hash_contenido),
        tipo=tipo.value,
        modulo=MODULO_POR_TIPO[tipo],
        estado=datos.estado,
        dominio_id=datos.dominio_id,
        unidad_id=datos.unidad_id,
        variable_id=datos.variable_id,
        serie_id=datos.serie_id,
        titulo=datos.titulo,
        resumen=datos.resumen,
        resultado=datos.resultado.model_dump(mode="json"),
        procedencia=datos.procedencia.model_dump(mode="json"),
        schema_version=datos.schema_version,
        hash_contenido=hash_contenido,
        reemplaza_a=datos.reemplaza_a,
        creado_por=creado_por,
    )
    sesion.add(expediente)
    sesion.commit()
    return expediente, True


def listar(
    sesion: Session,
    *,
    tipo: TipoExpediente | None,
    estado: EstadoExpediente | None,
    dominio_id: str | None,
    unidad_id: str | None,
    variable_id: str | None,
    serie_id: str | None,
    incluir_retirados: bool,
    limite: int,
    desplazamiento: int,
) -> tuple[list[Expediente], int]:
    consulta = select(Expediente).order_by(Expediente.creado_en.desc(), Expediente.id)
    filtros = {
        Expediente.tipo: tipo.value if tipo else None,
        Expediente.estado: estado.value if estado else None,
        Expediente.dominio_id: dominio_id,
        Expediente.unidad_id: unidad_id,
        Expediente.variable_id: variable_id,
        Expediente.serie_id: serie_id,
    }
    for columna, valor in filtros.items():
        if valor is not None:
            consulta = consulta.where(columna == valor)
    if not incluir_retirados and estado is None:
        consulta = consulta.where(Expediente.estado != EstadoExpediente.retirado.value)
    return paginar(sesion, consulta, limite, desplazamiento)


def retirar(sesion: Session, expediente_id: str, motivo: str, por: str) -> Expediente:
    """Retira un expediente (no se borra: se conserva con su motivo para la trazabilidad)."""
    expediente = obtener_o_404(sesion, Expediente, expediente_id, "Expediente")
    if expediente.estado == EstadoExpediente.retirado.value:
        raise Conflicto("El expediente ya está retirado.")
    expediente.estado = EstadoExpediente.retirado.value
    expediente.motivo_retiro = f"{motivo} (retirado por {por})"
    expediente.retirado_en = datetime.now(UTC)
    sesion.commit()
    return expediente
