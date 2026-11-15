"""Fenómenos naturales (M6): catálogo científico y capas GeoJSON para el mapa.

Las capas no tienen datos propios: salen del expediente vigente (no retirado) más reciente de su
tipo, de modo que cada punto del mapa conserva su procedencia. Sin expediente, la capa está vacía
y lo dice (`expediente_id = null`), en lugar de mostrar datos de otro origen.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import ConfigDep, SesionDep
from app.core.errors import NoEncontrado
from app.db.models import Expediente
from app.domain.vocabulario import EstadoExpediente, TipoExpediente
from app.schemas.comun import errores
from app.schemas.fenomenos import CapaGeoJSON, CatalogoFenomenos, FenomenoSalida, VariableFenomeno
from app.schemas.geo import Feature, Geometria

router = APIRouter(tags=["Fenómenos naturales"])

AVISO = "Resultados experimentales. No son alertas oficiales (SENAMHI, IGP, INGEMMET, INDECI)."
CAMPOS_VARIABLE = {"id", "nombre", "unidad", "rol", "relevancia", "fuente", "justificacion", "limitaciones"}


@lru_cache(maxsize=4)
def _leer_catalogo(ruta: Path, _marca: float) -> dict[str, Any]:
    datos: dict[str, Any] = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    return datos


def catalogo(raiz: Path) -> dict[str, Any]:
    ruta = raiz / "config" / "fenomenos.yaml"
    if not ruta.exists():
        raise NoEncontrado("No se encontró config/fenomenos.yaml en la raíz de datos.")
    return _leer_catalogo(ruta, ruta.stat().st_mtime)


def _fenomeno(clave: str, f: dict[str, Any]) -> FenomenoSalida:
    return FenomenoSalida(
        id=clave,
        nombre=f["nombre"],
        procesos=" ".join(f["procesos"].split()),
        objetivo=f.get("objetivo", {}),
        variables=[
            VariableFenomeno(
                **{k: v for k, v in var.items() if k in CAMPOS_VARIABLE},
                detalles={k: v for k, v in var.items() if k not in CAMPOS_VARIABLE},
            )
            for var in f.get("variables", [])
        ],
        metricas=f.get("metricas", []),
        dominio_bbox=f.get("dominio_bbox"),
    )


@router.get(
    "/fenomenos",
    response_model=CatalogoFenomenos,
    summary="Catálogo de fenómenos naturales",
    description="Variables con su justificación física, fuente y limitaciones; partición temporal y reglas de abstención.",
)
def listar_fenomenos(config: ConfigDep) -> CatalogoFenomenos:
    c = catalogo(config.raiz_datos)
    return CatalogoFenomenos(
        version=c["version"],
        verificado=str(c["verificado"]),
        particion_temporal=c["particion_temporal"],
        abstencion=c["abstencion"],
        fenomenos=[_fenomeno(k, v) for k, v in c["fenomenos"].items()],
        acceso_fuentes_nacionales={
            k: {kk: str(vv) for kk, vv in v.items()}
            for k, v in c.get("acceso_fuentes_nacionales", {}).items()
            if isinstance(v, dict)
        },
        via_integracion_nacional=" ".join(
            str(c.get("acceso_fuentes_nacionales", {}).get("via_integracion", "")).split()
        )
        or None,
        aviso=AVISO,
    )


@router.get(
    "/fenomenos/{fenomeno_id}",
    response_model=FenomenoSalida,
    summary="Detalle de un fenómeno",
    responses=errores(404),
)
def obtener_fenomeno(fenomeno_id: str, config: ConfigDep) -> FenomenoSalida:
    fenomenos = catalogo(config.raiz_datos)["fenomenos"]
    if fenomeno_id not in fenomenos:
        raise NoEncontrado(f"El fenómeno '{fenomeno_id}' no existe.")
    return _fenomeno(fenomeno_id, fenomenos[fenomeno_id])


def _vigente(sesion: SesionDep, tipo: TipoExpediente) -> Expediente | None:
    return sesion.scalar(
        select(Expediente)
        .where(Expediente.tipo == tipo.value, Expediente.estado != EstadoExpediente.retirado.value)
        .order_by(Expediente.creado_en.desc(), Expediente.id)
        .limit(1)
    )


def _punto(lon: float, lat: float) -> Geometria:
    return Geometria(type="Point", coordinates=[lon, lat])


def _capa(e: Expediente | None, features: list[Feature], nota: str | None = None) -> CapaGeoJSON:
    if e is None:
        return CapaGeoJSON(features=[], nota="Aún no hay un expediente publicado para esta capa.")
    return CapaGeoJSON(
        features=features,
        expediente_id=e.id,
        generado_utc=e.procedencia.get("generado_utc"),
        fuente=e.resultado.get("fuente"),
        nota=nota,
    )


@router.get(
    "/capas/sismos",
    response_model=CapaGeoJSON,
    summary="Sismos como GeoJSON (del expediente de sismicidad vigente)",
)
def capa_sismos(
    sesion: SesionDep, magnitud_min: float = Query(5.0, ge=0, le=10, description="Magnitud mínima.")
) -> CapaGeoJSON:
    e = _vigente(sesion, TipoExpediente.sismicidad)
    eventos = [] if e is None else [s for s in e.resultado.get("mapa", []) if s["magnitud"] >= magnitud_min]
    return _capa(
        e,
        [
            Feature(
                id=f"sismo-{i}",
                geometry=_punto(s["lon"], s["lat"]),
                properties={
                    "fecha": s["fecha"],
                    "magnitud": s["magnitud"],
                    "profundidad_km": s.get("profundidad_km"),
                },
            )
            for i, s in enumerate(eventos)
        ],
        nota="Catálogo sísmico histórico. No es un pronóstico de sismos.",
    )


@router.get(
    "/capas/volcanes",
    response_model=CapaGeoJSON,
    summary="Volcanes con su recurrencia histórica (del expediente vigente)",
)
def capa_volcanes(sesion: SesionDep) -> CapaGeoJSON:
    e = _vigente(sesion, TipoExpediente.recurrencia)
    volcanes = [] if e is None else e.resultado.get("volcanes", [])
    return _capa(
        e,
        [
            Feature(
                id=f"volcan-{v['numero_gvp']}",
                geometry=_punto(v["lon"], v["lat"]),
                properties={
                    "nombre": v["nombre"],
                    "erupciones": v["erupciones"],
                    "probabilidad_anual": v["probabilidad_anual"],
                    "intervalo": v["intervalo"],
                    "distancia_km": v["distancia_km"],
                    "ultima_erupcion": v.get("ultima_erupcion"),
                },
            )
            for v in volcanes
        ],
        nota="Frecuencia histórica de erupciones; el estado actual de cada volcán lo informa el OVS-IGP.",
    )


@router.get(
    "/capas/deslizamientos",
    response_model=CapaGeoJSON,
    summary="Deslizamientos inventariados (del expediente de inventario vigente)",
)
def capa_deslizamientos(sesion: SesionDep) -> CapaGeoJSON:
    e = _vigente(sesion, TipoExpediente.inventario)
    eventos = [] if e is None else e.resultado.get("eventos", [])
    return _capa(
        e,
        [
            Feature(
                id=f"deslizamiento-{ev['id']}",
                geometry=_punto(ev["lon"], ev["lat"]),
                properties={
                    k: ev.get(k)
                    for k in ("fecha", "lugar", "categoria", "detonante", "lluvia_mm", "percentiles")
                },
            )
            for ev in eventos
        ],
    )
