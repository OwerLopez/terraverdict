"""Métricas: catálogo explicado, mapas de calor e historial (M8).

Todo sale de expedientes publicados por el pipeline (`comparacion_modelos`, `historial_metricas`) y
de `config/metricas.yaml`. Ninguna cifra se calcula ni se completa aquí: solo se reorganiza.
"""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import ConfigDep, SesionDep
from app.api.v1.fenomenos import AVISO, _leer_catalogo, _vigente
from app.core.errors import NoEncontrado
from app.db.models import Expediente
from app.domain.vocabulario import EstadoExpediente, TipoExpediente
from app.schemas.comun import errores
from app.schemas.fenomenos import (
    CatalogoMetricas,
    CeldaImportancia,
    CeldaMetricas,
    HistorialMetricas,
    MapasMetricas,
    ModeloMapa,
    TareaMapa,
)

router = APIRouter(tags=["Métricas e historial"])

ORDEN_FAMILIA = {"referencia": 0, "clasico": 1, "red_neuronal": 2, "ensamble": 3}


@router.get(
    "/metricas",
    response_model=CatalogoMetricas,
    summary="Catálogo de métricas con su explicación",
    description="Qué mide cada métrica, cómo leerla, si es mejor alta o baja y su referencia (config/metricas.yaml).",
    responses=errores(404),
)
def catalogo_metricas(config: ConfigDep) -> CatalogoMetricas:
    ruta = config.raiz_datos / "config" / "metricas.yaml"
    if not ruta.exists():
        raise NoEncontrado("No se encontró config/metricas.yaml en la raíz de datos.")
    return CatalogoMetricas.model_validate(_leer_catalogo(ruta, ruta.stat().st_mtime))


@router.get(
    "/metricas/mapas",
    response_model=MapasMetricas,
    summary="Mapas de calor de métricas e importancia de variables",
    description=(
        "Reorganiza los expedientes `comparacion_modelos` vigentes (el más reciente por título) en una matriz "
        "modelo × tarea con cada métrica publicada y una matriz tarea × variable con la importancia por "
        "permutación. Sin expedientes, las listas vienen vacías."
    ),
)
def mapas_metricas(sesion: SesionDep) -> MapasMetricas:
    expedientes = sesion.scalars(
        select(Expediente)
        .where(
            Expediente.tipo == TipoExpediente.comparacion_modelos.value,
            Expediente.estado != EstadoExpediente.retirado.value,
        )
        .order_by(Expediente.creado_en.desc(), Expediente.id)
    )
    vigentes: dict[str, Expediente] = {}
    for e in expedientes:
        vigentes.setdefault(e.titulo, e)
    tareas, celdas, importancia = [], [], []
    familias: dict[str, str] = {}
    for e in sorted(vigentes.values(), key=lambda x: x.titulo):
        r = e.resultado
        tareas.append(
            TareaMapa(
                expediente_id=e.id,
                titulo=e.titulo,
                fenomeno=r["fenomeno"],
                tarea=r["tarea"],
                horizonte=r["horizonte"],
                metrica_principal=r["metrica_principal"],
                mejor_validacion=r["mejor_validacion"],
            )
        )
        for m in r["modelos"]:
            familias.setdefault(m["nombre"], m["familia"])
            intervalo = m.get("intervalo_prueba") or {}
            celdas.append(
                CeldaMetricas(
                    expediente_id=e.id,
                    modelo=m["nombre"],
                    puntaje_validacion=m["puntaje_validacion"],
                    puntaje_prueba=m.get("puntaje_prueba"),
                    ic90_inferior=intervalo.get("lo"),
                    ic90_superior=intervalo.get("hi"),
                    p_diebold_mariano=m.get("p_diebold_mariano"),
                    dispersion_semillas=m.get("dispersion_semillas"),
                )
            )
        importancia += [
            CeldaImportancia(
                expediente_id=e.id,
                variable=i["variable"],
                importancia=i["importancia"],
                desviacion=i["desviacion"],
            )
            for i in r.get("importancia", [])
        ]
    return MapasMetricas(
        tareas=tareas,
        modelos=[
            ModeloMapa(nombre=n, familia=f)
            for n, f in sorted(familias.items(), key=lambda kv: (ORDEN_FAMILIA.get(kv[1], 9), kv[0]))
        ],
        celdas=celdas,
        variables=sorted({i.variable for i in importancia}),
        importancia=importancia,
        aviso=AVISO,
    )


@router.get(
    "/historial",
    response_model=HistorialMetricas,
    summary="Historial de métricas: año a año y dinámica en ventanas",
    description=(
        "Habilidad de cada modelo por año (origen móvil con el diseño congelado) y evolución de los "
        "invariantes de caos en ventanas deslizantes, del expediente `historial_metricas` vigente. "
        "Sin expediente publicado, `resultado` es null."
    ),
)
def historial_metricas(sesion: SesionDep) -> HistorialMetricas:
    e = _vigente(sesion, TipoExpediente.historial_metricas)
    if e is None:
        return HistorialMetricas(aviso=AVISO)
    return HistorialMetricas(
        expediente_id=e.id, generado_utc=e.procedencia.get("generado_utc"), resultado=e.resultado, aviso=AVISO
    )
