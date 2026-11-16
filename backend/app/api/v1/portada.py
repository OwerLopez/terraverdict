"""Portada: "¿cómo estamos hoy?" y tabla maestra de veredictos, sin cifras escritas a mano.

- `indicadores` es el archivo `resultados/contrato/indicadores.json` que `tv publicar` genera desde los
  crudos (ENSO, SPI-3 actual de la cabecera, sequía según ENSO, gradiente altitudinal y series de prueba).
- Cada fila de la tabla sale del expediente vigente de su tipo y lleva su `expediente_id`.
- La anticipación usa siempre el modelo elegido en la **validación** (`mejor_validacion`): elegir la mejor
  cifra de la prueba sería sesgo de selección.
- Regla de evidencia (config/metricas.yaml): IC90 inferior > 0 y p de Diebold-Mariano < 0,10 = confirmada;
  solo una de las dos = indicio.
"""

from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import ConfigDep, SesionDep
from app.db.models import Expediente
from app.domain.vocabulario import EstadoExpediente, TipoExpediente
from app.schemas.portada import Anticipacion, FilaVeredicto, Portada, Tendencia

router = APIRouter(tags=["Portada"])

AVISO = "Resultados experimentales. No son alertas oficiales (SENAMHI, IGP, INGEMMET, INDECI, ENFEN)."
UMBRAL_P = 0.10
REGLA = "Regla de evidencia: IC90 inferior > 0 y p de Diebold-Mariano < 0,10 = confirmada; solo una de las dos = indicio."  # definida en config/metricas.yaml


@lru_cache(maxsize=4)
def _leer_json(ruta: Path, _marca: float) -> dict[str, Any]:
    datos: dict[str, Any] = json.loads(ruta.read_text(encoding="utf-8"))
    return datos


def indicadores(raiz: Path) -> dict[str, Any] | None:
    ruta = raiz / "resultados" / "contrato" / "indicadores.json"
    return _leer_json(ruta, ruta.stat().st_mtime) if ruta.exists() else None


def _vigentes(sesion: Session, tipo: TipoExpediente) -> list[Expediente]:
    return list(
        sesion.scalars(
            select(Expediente)
            .where(Expediente.tipo == tipo.value, Expediente.estado != EstadoExpediente.retirado.value)
            .order_by(Expediente.creado_en.desc(), Expediente.id)
        )
    )


def evidencia(lo: float | None, p: float | None) -> str:
    a = lo is not None and lo > 0
    b = p is not None and p < UMBRAL_P
    return "confirmada" if a and b else "indicio" if a or b else "sin_evidencia"


def _anticipacion(e: Expediente | None) -> Anticipacion | None:
    if e is None:
        return None
    r = e.resultado
    m = next((x for x in r.get("modelos", []) if x.get("nombre") == r.get("mejor_validacion")), None)
    if m is None:
        return None
    iv = m.get("intervalo_prueba") or {}
    lo, hi = iv.get("lo"), iv.get("hi")
    periodo = r.get("periodo_prueba") or {}
    return Anticipacion(
        metrica=r.get("metrica_principal", ""),
        valor=m.get("puntaje_prueba"),
        intervalo=[lo, hi] if lo is not None and hi is not None else None,
        p_diebold_mariano=m.get("p_diebold_mariano"),
        modelo=m["nombre"],
        familia=m.get("familia"),
        horizonte=r.get("horizonte"),
        periodo_prueba=f"{periodo.get('desde')} – {periodo.get('hasta')}" if periodo else None,
        evidencia=evidencia(lo, m.get("p_diebold_mariano")),  # type: ignore[arg-type]
        expediente_id=e.id,
    )


def _comparacion(lista: list[Expediente], fenomeno: str, horizonte: str | None = None) -> Expediente | None:
    """Comparación con NASA POWER (la principal); CHIRPS es la réplica de robustez."""
    for e in lista:
        r = e.resultado
        if r.get("fenomeno") == fenomeno and (horizonte is None or r.get("horizonte") == horizonte) and "CHIRPS" not in e.titulo:
            return e
    return None


def _tendencia(lista: list[Expediente], palabras: tuple[str, ...], variable: str) -> Tendencia | None:
    for e in lista:
        r = e.resultado
        if any(p in e.titulo.lower() for p in palabras) and "pendiente" in r:
            p = r["pendiente"]
            iv = p.get("intervalo") or {}
            per = r.get("periodo") or {}
            return Tendencia(
                tipo="pendiente",
                variable=variable,
                valor=p.get("valor"),
                intervalo=[iv["lo"], iv["hi"]] if "lo" in iv else None,
                unidad=p.get("unidad"),
                veredicto=r.get("veredicto"),
                periodo=f"{per.get('desde')}–{per.get('hasta')}" if per else None,
                expediente_id=e.id,
            )
    return None


def _veredicto_habilidad(a: Anticipacion | None) -> str:
    if a is None:
        return "abstencion"
    return {"confirmada": "habilidad_confirmada", "indicio": "habilidad_con_indicio"}.get(a.evidencia, "sin_habilidad")


def filas(sesion: Session) -> list[FilaVeredicto]:
    comparaciones = _vigentes(sesion, TipoExpediente.comparacion_modelos)
    tendencias = _vigentes(sesion, TipoExpediente.tendencia)
    salida: list[FilaVeredicto] = []

    lluvia = _anticipacion(_comparacion(comparaciones, "lluvia_extrema"))
    salida.append(
        FilaVeredicto(
            fenomeno="lluvia_extrema",
            fuentes=["NASA POWER (MERRA-2)", "CHIRPS", "NASA GPM IMERG (M1)"],
            tendencia=_tendencia(tendencias, ("lluvia",), "lluvia"),
            anticipacion=lluvia,
            veredicto=_veredicto_habilidad(lluvia),  # type: ignore[arg-type]
        )
    )

    sequia = _anticipacion(_comparacion(comparaciones, "sequia", "1 mes"))
    salida.append(
        FilaVeredicto(
            fenomeno="sequia",
            fuentes=["NASA POWER (MERRA-2)", "NOAA CPC (ONI)", "CHIRPS"],
            tendencia=_tendencia(tendencias, ("temperatura", "t2m"), "temperatura"),
            anticipacion=sequia,
            veredicto=_veredicto_habilidad(sequia),  # type: ignore[arg-type]
        )
    )

    sis = next(iter(_vigentes(sesion, TipoExpediente.sismicidad)), None)
    conteo = _anticipacion(_comparacion(comparaciones, "sismos"))
    tend_sis = None
    if sis is not None:
        r, iv = sis.resultado, sis.resultado.get("intervalo_b") or {}
        per = r.get("periodo") or {}
        tend_sis = Tendencia(
            tipo="valor_b",
            variable="Gutenberg-Richter",
            valor=r.get("valor_b"),
            intervalo=[iv["lo"], iv["hi"]] if "lo" in iv else None,
            periodo=f"{str(per.get('desde'))[:4]}–{str(per.get('hasta'))[:4]}" if per else None,
            expediente_id=sis.id,
        )
    salida.append(
        FilaVeredicto(
            fenomeno="sismos",
            fuentes=["USGS ComCat", "IGP"],
            tendencia=tend_sis,
            anticipacion=conteo,
            veredicto="descriptivo",
        )
    )

    rec = next(iter(_vigentes(sesion, TipoExpediente.recurrencia)), None)
    tend_vol, abst_vol = None, []
    if rec is not None:
        volcanes = rec.resultado.get("volcanes", [])
        # El volcán más cercano a la ciudad (no el de mayor cifra): Misti, a ~18 km.
        cercano = min(volcanes, key=lambda v: v.get("distancia_km", 1e9)) if volcanes else None
        if cercano:
            iv = cercano.get("intervalo") or {}
            tend_vol = Tendencia(
                tipo="probabilidad_anual",
                variable=cercano.get("nombre"),
                valor=cercano.get("probabilidad_anual"),
                intervalo=[iv["lo"], iv["hi"]] if "lo" in iv else None,
                periodo=f"{rec.resultado.get('inicio_registro')}–{date.today().year}",
                expediente_id=rec.id,
            )
        abst_vol = list((rec.resultado.get("abstencion") or {}).get("motivos", []))
    salida.append(
        FilaVeredicto(
            fenomeno="volcanes",
            fuentes=["Smithsonian GVP"],
            tendencia=tend_vol,
            abstencion=abst_vol,
            veredicto="recurrencia_historica",
        )
    )

    inv = next(iter(_vigentes(sesion, TipoExpediente.inventario)), None)
    tend_des, abst_des = None, []
    if inv is not None:
        tend_des = Tendencia(
            tipo="eventos",
            variable="deslizamientos detonados por lluvia",
            valor=float(len(inv.resultado.get("eventos", []))),
            unidad="eventos",
            expediente_id=inv.id,
        )
        abst = inv.resultado.get("abstencion") or {}
        abst_des = list(abst.get("motivos", [])) if not abst.get("publicar", True) else []
    salida.append(
        FilaVeredicto(
            fenomeno="deslizamientos",
            fuentes=["NASA Global Landslide Catalog", "INGEMMET"],
            tendencia=tend_des,
            abstencion=abst_des,
            veredicto="abstencion" if abst_des else "descriptivo",
        )
    )
    return salida


@router.get(
    "/portada",
    response_model=Portada,
    summary="Estado actual y tabla maestra de veredictos",
    description=(
        "Indicadores calculados desde los crudos (ENSO con ONI y Niño 3.4 / 1+2, SPI-3 actual en la cabecera, "
        "frecuencia de sequía según ENSO, gradiente altitudinal y series de prueba) y una fila por fenómeno con "
        "su tendencia, su habilidad fuera de muestra y su veredicto, cada una con el expediente de origen."
    ),
)
def portada(sesion: SesionDep, config: ConfigDep) -> Portada:
    ind = indicadores(config.raiz_datos)
    eventos = ((ind or {}).get("predicciones") or {}).get("lluvia_eventos_documentados", [])
    return Portada(indicadores=ind, filas=filas(sesion), lluvia_eventos_documentados=eventos, regla_evidencia=REGLA, aviso=AVISO)
