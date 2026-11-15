"""Importación de datos reales y verificables del repositorio.

Todo lo que se carga aquí tiene una fuente rastreable:

* ``config/fuentes.yaml``, ``variables.yaml``, ``problemas.yaml``, ``dominios.yaml`` (catálogos).
* ``docs/verificacion/evidencia.json`` y ``enlaces.json`` (verificación ejecutada).
* ``datos/eventos/arequipa.json`` (eventos con citas).
* ``datos/autodema/reporte_2024-03-13.json`` (transcripción del PDF oficial).
* ``docs/verificacion/analisis_preliminar.json`` (análisis ejecutado con NASA POWER y NOAA).

La importación es idempotente y pasa por los mismos contratos y servicios que la API.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    Dominio,
    EventoDocumentado,
    Expediente,
    Fuente,
    InformeVerificacion,
    Problema,
    Serie,
    Unidad,
    Variable,
)
from app.domain.vocabulario import EstadoVerificacion
from app.schemas.catalogo import EventoDocumentadoSalida
from app.schemas.expedientes import ExpedienteCrear
from app.schemas.series import ObservacionesCarga, SerieCrear
from app.services import expedientes as servicio_expedientes
from app.services import series as servicio_series

log = logging.getLogger("terraverdict.importacion")
REPOSITORIO = "DiegoNiS/terraverdict"
IMPORTADOR = "servicio:importador-repositorio"

NOMBRES_FUENTES = {
    "imerg_final_mensual": "GPM IMERG Final · mensual",
    "imerg_final_diaria": "GPM IMERG Final · diaria",
    "imerg_early_30min": "GPM IMERG Early · 30 min",
    "imerg_late_30min": "GPM IMERG Late · 30 min",
    "chirps_v3_mensual": "CHIRPS v3 · mensual",
    "power_mensual": "NASA POWER · mensual por punto",
    "merra2_superficie_mensual": "MERRA-2 · superficie mensual",
    "merra2_flujos_mensual": "MERRA-2 · flujos mensuales",
    "gldas21_mensual": "GLDAS 2.1 Noah · mensual",
    "gldas20_mensual": "GLDAS 2.0 Noah · mensual (1948–2014)",
    "fldas_chirps_mensual": "FLDAS forzado con CHIRPS · mensual",
    "modis_lst_terra": "MODIS Terra · temperatura de superficie",
    "modis_lst_aqua": "MODIS Aqua · temperatura de superficie",
    "modis_ndvi": "MODIS Terra · NDVI 250 m",
    "modis_et": "MODIS · evapotranspiración",
    "modis_nieve": "MODIS Terra · nieve sin nubes",
    "viirs_ndvi": "VIIRS · NDVI",
    "viirs_fuegos": "VIIRS · fuegos activos 375 m",
    "area_quemada": "MODIS · área quemada",
    "smap_l3": "SMAP L3 · humedad del suelo 9 km",
    "smap_l4": "SMAP L4 · humedad superficial y de raíces",
    "nasadem": "NASADEM · terreno 30 m",
    "hls_landsat": "HLS Landsat · 30 m",
    "hls_sentinel2": "HLS Sentinel-2 · 30 m",
    "landsat_c2_l2": "Landsat Collection 2 · nivel 2",
    "sentinel1_grd": "Sentinel-1 · radar GRD",
    "swot_lagos": "SWOT · lagos y embalses",
    "icesat2_atl13": "ICESat-2 ATL13 · aguas interiores",
    "nisar_gcov": "NISAR · GCOV",
    "power_diaria": "NASA POWER · diaria por punto",
    "chirps_v2_diaria": "CHIRPS v2.0 · diaria (ClimateSERV)",
    "usgs_comcat": "USGS ComCat · catálogo sísmico",
    "igp_sismos_reportados": "IGP · sismos reportados",
    "gvp_volcanes": "Smithsonian GVP · volcanes y erupciones",
    "nasa_glc": "NASA · Global Landslide Catalog",
    "modis_lst_ornl": "MODIS MOD11A2 · LST por ORNL DAAC",
    "oni": "NOAA CPC · índice ONI",
    "roni": "NOAA CPC · índice RONI",
    "nino34_knmi": "KNMI · Niño3.4 (ERSST v5)",
    "ghcn_arequipa": "NOAA GHCN-Daily · estación Arequipa",
    "autodema_reportes": "AUTODEMA · reportes hídricos",
}

# Clave de cada fuente en docs/verificacion/evidencia.json
EVIDENCIA_POR_FUENTE = {
    "imerg_final_mensual": "cmr:imerg_final_mensual",
    "imerg_final_diaria": "cmr:imerg_final_diaria",
    "imerg_early_30min": "cmr:imerg_early_30min",
    "imerg_late_30min": "cmr:imerg_late_30min",
    "merra2_superficie_mensual": "cmr:merra2_superficie_mensual",
    "merra2_flujos_mensual": "cmr:merra2_flujos_mensual",
    "gldas21_mensual": "cmr:gldas21_noah_mensual",
    "gldas20_mensual": "cmr:gldas20_noah_mensual",
    "fldas_chirps_mensual": "cmr:fldas_chirps_mensual",
    "modis_lst_terra": "cmr:modis_lst_terra_8d",
    "modis_lst_aqua": "cmr:modis_lst_aqua_8d",
    "modis_ndvi": "cmr:modis_ndvi_terra_16d",
    "modis_et": "cmr:modis_et_8d",
    "modis_nieve": "cmr:modis_nieve_sin_nubes",
    "area_quemada": "cmr:modis_area_quemada",
    "viirs_ndvi": "cmr:viirs_ndvi_16d",
    "viirs_fuegos": "cmr:viirs_fuegos_375m",
    "smap_l3": "cmr:smap_l3_9km",
    "smap_l4": "cmr:smap_l4_9km_3h",
    "nasadem": "cmr:nasadem",
    "hls_landsat": "cmr:hls_landsat",
    "hls_sentinel2": "cmr:hls_sentinel2",
    "icesat2_atl13": "cmr:icesat2_aguas_interiores",
    "swot_lagos": "cmr:swot_lagos_obs",
    "nisar_gcov": "cmr:nisar_gcov",
    "power_mensual": "nasa_power",
    "oni": "enso",
    "roni": "enso",
    "nino34_knmi": "enso",
    "ghcn_arequipa": "ghcn_arequipa",
    "sentinel1_grd": "copernicus_sentinel",
    "autodema_reportes": "autodema_reporte",
    "chirps_v3_mensual": "chirps_v3_latam_mensual",
}

NOMBRES_REPRESAS = {
    "el_frayle": "Represa El Frayle",
    "el_pane": "Represa El Pañe",
    "pillones": "Represa Pillones",
    "aguada_blanca": "Represa Aguada Blanca",
    "chalhuanca": "Represa Chalhuanca",
    "bamputane": "Represa Bamputañe",
    "dique_espanoles": "Dique de los Españoles",
}


def _leer_yaml(ruta: Path) -> dict[str, Any]:
    with ruta.open(encoding="utf-8") as f:
        contenido: dict[str, Any] = yaml.safe_load(f)
    return contenido


def _leer_json(ruta: Path) -> dict[str, Any]:
    contenido: dict[str, Any] = json.loads(ruta.read_text(encoding="utf-8"))
    return contenido


def _sha256(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def _lista(valor: Any) -> list[str]:
    if valor is None:
        return []
    return [str(v) for v in valor] if isinstance(valor, list) else [str(valor)]


def importar_fuentes(sesion: Session, raiz: Path) -> int:
    fuentes = _leer_yaml(raiz / "config" / "fuentes.yaml")["fuentes"]
    ruta_evidencia = raiz / "docs" / "verificacion" / "evidencia.json"
    evidencia = _leer_json(ruta_evidencia) if ruta_evidencia.exists() else {"resultados": {}}
    generado = datetime.fromisoformat(evidencia["generado_utc"]) if "generado_utc" in evidencia else None
    for clave, datos in fuentes.items():
        resultado = evidencia["resultados"].get(EVIDENCIA_POR_FUENTE.get(clave, ""))
        por_confirmar = datos.get("por_confirmar")
        por_confirmar_txt = (
            por_confirmar if isinstance(por_confirmar, str) else ("sí" if por_confirmar else None)
        )
        if resultado is None:
            estado = EstadoVerificacion.sin_evidencia
        elif not resultado.get("ok"):
            estado = EstadoVerificacion.no_verificado
        else:
            estado = EstadoVerificacion.parcial if por_confirmar_txt else EstadoVerificacion.verificado
        conocidos = {
            "coleccion",
            "version",
            "acceso",
            "familia",
            "url",
            "licencia",
            "periodo",
            "resolucion",
            "uso",
            "advertencia",
            "por_confirmar",
        }
        sesion.merge(
            Fuente(
                id=clave,
                nombre=NOMBRES_FUENTES.get(clave, clave),
                coleccion=datos.get("coleccion"),
                version=str(datos["version"]) if datos.get("version") is not None else None,
                acceso=_lista(datos.get("acceso")),
                familia=datos.get("familia"),
                url=datos.get("url") or datos.get("url_ejemplo"),
                licencia=datos.get("licencia"),
                periodo=datos.get("periodo"),
                resolucion=datos.get("resolucion") if isinstance(datos.get("resolucion"), dict) else None,
                usos=_lista(datos.get("uso")),
                advertencia=datos.get("advertencia") or datos.get("nota"),
                por_confirmar=por_confirmar_txt,
                metadatos={k: v for k, v in datos.items() if k not in conocidos},
                estado_verificacion=estado.value,
                verificado_en=generado if resultado is not None else None,
                evidencia=resultado,
            )
        )
    sesion.commit()
    return len(fuentes)


def importar_catalogos(sesion: Session, raiz: Path) -> dict[str, int]:
    variables = _leer_yaml(raiz / "config" / "variables.yaml")["variables"]
    for clave, v in variables.items():
        sesion.merge(Variable(id=clave, **v))
    problemas = _leer_yaml(raiz / "config" / "problemas.yaml")["problemas"]
    for clave, p in problemas.items():
        sesion.merge(Problema(id=clave, **p))
    sesion.commit()
    return {"variables": len(variables), "problemas": len(problemas)}


def importar_dominios(sesion: Session, raiz: Path) -> int:
    dominios = _leer_yaml(raiz / "config" / "dominios.yaml")["dominios"]
    descripciones = {
        "chili_analisis": ("Cuenca regulada del Chili", "analisis"),
        "andes_sur_entrenamiento": ("Andes del sur (entrenamiento regional)", "entrenamiento"),
        "sur_peru_fenomenos": ("Sur del Perú (fenómenos regionales)", "analisis"),
    }
    for clave, d in dominios.items():
        nombre, tipo = descripciones.get(clave, (clave, "analisis"))
        sesion.merge(
            Dominio(
                id=clave,
                nombre=nombre,
                descripcion=d["descripcion"],
                tipo=tipo,
                bbox=[float(x) for x in d["bbox"]],
                geometria=None,
                aproximado=True,
                metadatos={k: v for k, v in d.items() if k not in {"descripcion", "bbox"}},
            )
        )
    sesion.commit()

    evidencia_path = raiz / "docs" / "verificacion" / "evidencia.json"
    evidencia = _leer_json(evidencia_path)["resultados"] if evidencia_path.exists() else {}
    power = evidencia.get("nasa_power", {}).get("datos", {})
    unidades: list[Unidad] = [
        Unidad(
            id="chili_analisis.sistema_regulado",
            dominio_id="chili_analisis",
            tipo="sistema",
            nombre="Sistema regulado del Chili",
            geometria=None,
            estado_geometria="pendiente",
            metadatos={"nota": "Polígono oficial pendiente (ANA + áreas de trasvase, etapa E1)."},
        ),
        Unidad(
            id="chili_analisis.cabecera_power",
            dominio_id="chili_analisis",
            tipo="punto",
            nombre="Celda NASA POWER de la cabecera",
            geometria={"type": "Point", "coordinates": [-71.25, -15.95]},
            estado_geometria="exacta",
            metadatos={
                "nota": "Punto consultado en el análisis preliminar (celda MERRA-2).",
                "elevacion_celda_m": power.get("elevacion_celda_m"),
            },
        ),
        Unidad(
            id="chili_analisis.captacion_la_tomilla",
            dominio_id="chili_analisis",
            tipo="captacion",
            nombre="Captación La Tomilla (SEDAPAR)",
            geometria=None,
            estado_geometria="pendiente",
            metadatos={},
        ),
    ]
    for estacion in evidencia.get("ghcn_arequipa", {}).get("datos", {}).get("estaciones_a_150km", []):
        completitud = evidencia["ghcn_arequipa"]["datos"]["completitud"].get(estacion["id"], {})
        unidades.append(
            Unidad(
                id=f"chili_analisis.estacion_{estacion['id'].lower()}",
                dominio_id="chili_analisis",
                tipo="estacion",
                nombre=f"Estación GHCN {estacion['id']} · {estacion['nombre'].title()}",
                geometria={"type": "Point", "coordinates": [estacion["lon"], estacion["lat"]]},
                estado_geometria="exacta",
                metadatos={
                    "elevacion_m": estacion["elev_m"],
                    "anios_lluvia_completos": len(completitud.get("PRCP", {}).get("anios_90pct", [])),
                    "anios_tmax_completos": len(completitud.get("TMAX", {}).get("anios_90pct", [])),
                },
            )
        )
    for represa, nombre in NOMBRES_REPRESAS.items():
        unidades.append(
            Unidad(
                id=f"chili_analisis.{represa}",
                dominio_id="chili_analisis",
                tipo="represa",
                nombre=nombre,
                geometria=None,
                estado_geometria="pendiente",
                metadatos={"operador": "AUTODEMA"},
            )
        )
    for u in unidades:
        sesion.merge(u)
    sesion.commit()
    return len(unidades)


def importar_verificacion(sesion: Session, raiz: Path) -> int:
    importados = 0
    archivos = {
        "fuentes": raiz / "docs" / "verificacion" / "evidencia.json",
        "enlaces": raiz / "docs" / "verificacion" / "enlaces.json",
    }
    for tipo, ruta in archivos.items():
        if not ruta.exists():
            continue
        datos = _leer_json(ruta)
        generado = datetime.fromisoformat(datos["generado_utc"])
        if tipo == "fuentes":
            total = len(datos["resultados"])
            correctas = sum(1 for r in datos["resultados"].values() if r.get("ok"))
        else:
            # Un enlace existe si respondió HTTP 200 en al menos una corrida: la red del entorno
            # de verificación corta conexiones de forma intermitente (historial en el JSON).
            total = len(datos["enlaces"])
            correctas = sum(
                1 for e in datos["enlaces"] if e.get("corridas_con_200", 1 if e.get("http") == 200 else 0) > 0
            )
        existente = sesion.scalar(
            select(InformeVerificacion).where(
                InformeVerificacion.tipo == tipo, InformeVerificacion.generado_utc == generado
            )
        )
        if existente is None:
            sesion.add(
                InformeVerificacion(
                    tipo=tipo, generado_utc=generado, total=total, correctas=correctas, datos=datos
                )
            )
            importados += 1
    sesion.commit()
    return importados


def importar_eventos(sesion: Session, raiz: Path) -> int:
    eventos = _leer_json(raiz / "datos" / "eventos" / "arequipa.json")["eventos"]
    for e in eventos:
        validado = EventoDocumentadoSalida.model_validate({**e, "fecha": date.fromisoformat(e["fecha"])})
        sesion.merge(
            EventoDocumentado(
                id=validado.id,
                fecha=validado.fecha,
                precision=validado.precision.value,
                categoria=validado.categoria.value,
                titulo=validado.titulo,
                descripcion=validado.descripcion,
                cifras=[c.model_dump() for c in validado.cifras],
                fuentes=[f.model_dump() for f in validado.fuentes],
                dominio_id="chili_analisis",
            )
        )
    sesion.commit()
    return len(eventos)


def _asegurar_serie(sesion: Session, datos: SerieCrear) -> None:
    if sesion.get(Serie, datos.id) is None:
        servicio_series.crear_serie(sesion, datos)


def importar_autodema(sesion: Session, raiz: Path) -> int:
    ruta = raiz / "datos" / "autodema" / "reporte_2024-03-13.json"
    reporte = _leer_json(ruta)
    suma = round(sum(r["volumen_util_hm3"] for r in reporte["represas"].values()), 2)
    if abs(suma - reporte["total_chili_volumen_util_hm3"]) > 0.05:
        raise ValueError(
            f"Transcripción inconsistente: suma {suma} ≠ total {reporte['total_chili_volumen_util_hm3']}"
        )
    evidencia = _leer_json(raiz / "docs" / "verificacion" / "evidencia.json")
    procedencia = {
        "fuentes": [
            {
                "fuente_id": "autodema_reportes",
                "url": reporte["url"],
                "consultado_utc": evidencia["generado_utc"],
            }
        ],
        "codigo": {"repositorio": REPOSITORIO, "script": "backend/app/importacion.py"},
        "hash_entradas": {"reporte_2024-03-13.json": _sha256(ruta)},
        "pasos": [
            {
                "id": "transcripcion",
                "nombre": "Transcripción del PDF oficial",
                "descripcion": reporte["transcripcion"],
                "metricas": {
                    "suma_represas_hm3": suma,
                    "total_reportado_hm3": reporte["total_chili_volumen_util_hm3"],
                },
            },
            {
                "id": "control_consistencia",
                "nombre": "Control: suma de represas = total reportado (±0,05 hm³)",
                "entradas": ["paso:transcripcion"],
                "metricas": {"diferencia_hm3": round(suma - reporte["total_chili_volumen_util_hm3"], 2)},
            },
        ],
        "generado_utc": evidencia["generado_utc"],
    }
    variables = {
        "volumen_util_hm3": ("volumen_util", "hm3", "Volumen útil"),
        "afluente_m3s": ("caudal_afluente", "m3/s", "Caudal afluente"),
        "descarga_m3s": ("descarga", "m3/s", "Descarga"),
        "precipitacion_mm": ("precipitacion", "mm", "Lluvia local"),
    }
    fecha = date.fromisoformat(reporte["fecha"])
    cargadas = 0
    filas: list[tuple[str, str, str, str, str, float]] = [
        (f"chili_analisis.{represa}", campo, *variables[campo], valor)
        for represa, datos in reporte["represas"].items()
        for campo, valor in datos.items()
        if valor is not None
    ]
    filas.append(
        (
            "chili_analisis.sistema_regulado",
            "volumen_util_hm3",
            *variables["volumen_util_hm3"],
            reporte["total_chili_volumen_util_hm3"],
        )
    )
    for unidad_id, _campo, variable_id, unidad, etiqueta, valor in filas:
        serie_id = f"{unidad_id}:{variable_id}:autodema_reportes:p1d"
        _asegurar_serie(
            sesion,
            SerieCrear.model_validate(
                {
                    "id": serie_id,
                    "dominio_id": "chili_analisis",
                    "unidad_id": unidad_id,
                    "variable_id": variable_id,
                    "fuente_id": "autodema_reportes",
                    "unidad": unidad,
                    "frecuencia": "P1D",
                    "agregacion": {"tipo": "valor_reportado", "hora_local": reporte["hora_local"]},
                    "descripcion": f"{etiqueta} según los reportes hídricos de AUTODEMA.",
                    "procedencia": procedencia,
                }
            ),
        )
        servicio_series.cargar_observaciones(
            sesion,
            serie_id,
            ObservacionesCarga.model_validate({"observaciones": [{"t": fecha, "valor": valor}]}),
        )
        cargadas += 1
    return cargadas


def _expediente_tendencia(
    datos: dict[str, Any],
    serie_id: str,
    variable_id: str,
    unidad_pendiente: str,
    procedencia: dict[str, Any],
    titulo: str,
    resumen: str,
) -> ExpedienteCrear:
    det = datos["detectabilidad"]
    return ExpedienteCrear.model_validate(
        {
            "estado": "preliminar",
            "dominio_id": "chili_analisis",
            "unidad_id": "chili_analisis.cabecera_power",
            "variable_id": variable_id,
            "serie_id": serie_id,
            "titulo": titulo,
            "resumen": resumen,
            "procedencia": procedencia,
            "resultado": {
                "tipo": "tendencia",
                "periodo": {"desde": str(datos["periodo"][0]), "hasta": str(datos["periodo"][1])},
                "n": datos["n"],
                "pendiente": {
                    "valor": datos["sen_por_decada"],
                    "intervalo": {
                        "lo": datos["ic90_por_decada"][0],
                        "hi": datos["ic90_por_decada"][1],
                        "nivel": 0.9,
                    },
                    "unidad": unidad_pendiente,
                },
                "significancia": {
                    "p_mann_kendall": datos["mk_p"],
                    "p_hamed_rao": datos["mk_hamed_rao_p"],
                    "p_conservador": datos["p_conservador"],
                    "alfa": 0.05,
                },
                "sello": {
                    "ventanas": {
                        "estado": "calculada",
                        "metricas": {**datos["ventanas"], "longitud_minima_anios": 20},
                        "nota": "Métricas calculadas; el umbral de aprobación se fijará en el preregistro.",
                    },
                    "enso": {
                        "estado": "calculada",
                        "metricas": datos["enso"],
                        "nota": "Regresión con el ONI de dic–feb (desfase 0).",
                    },
                    "sensor": {
                        "estado": "pendiente",
                        "nota": "Falta probar escalones en las transiciones documentadas.",
                    },
                    "independencia": {
                        "estado": "pendiente",
                        "nota": "Un solo producto (POWER/MERRA-2): falta una segunda familia independiente.",
                    },
                    "detectabilidad": {
                        "estado": "calculada",
                        "metricas": det,
                        "nota": "Weatherhead et al. (1998).",
                    },
                },
                "veredicto": "preliminar",
                "anios_para_decidir": round(max(0.0, det["anios_necesarios"] - det["anios_disponibles"]), 1),
            },
        }
    )


def importar_analisis_preliminar(sesion: Session, raiz: Path) -> dict[str, int]:
    ruta = raiz / "docs" / "verificacion" / "analisis_preliminar.json"
    analisis = _leer_json(ruta)
    generado = analisis["generado_utc"]
    hash_archivo = _sha256(ruta)
    fuentes_ref = [
        {
            "fuente_id": "power_mensual",
            "url": "https://power.larc.nasa.gov/api/temporal/monthly/point",
            "consultado_utc": generado,
        },
        {
            "fuente_id": "oni",
            "url": "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt",
            "consultado_utc": generado,
        },
    ]

    def procedencia(agregacion: dict[str, Any], datos: dict[str, Any]) -> dict[str, Any]:
        return {
            "fuentes": fuentes_ref,
            "codigo": {"repositorio": REPOSITORIO, "script": "scripts/analisis_preliminar.py"},
            "hash_entradas": {"analisis_preliminar.json": hash_archivo},
            "pasos": [
                {
                    "id": "descarga_power",
                    "nombre": "Descarga NASA POWER (MERRA-2)",
                    "salidas": ["serie mensual"],
                    "metricas": {
                        "lon": analisis["punto"]["lon"],
                        "lat": analisis["punto"]["lat"],
                        "elevacion_celda_m": analisis["fuente_power"]["elevacion_celda_m"],
                    },
                },
                {"id": "descarga_oni", "nombre": "Descarga del índice ONI (NOAA CPC)"},
                {
                    "id": "agregacion",
                    "nombre": agregacion["nombre"],
                    "entradas": ["paso:descarga_power"],
                    "metricas": {"n": datos["n"]},
                },
                {
                    "id": "theil_sen",
                    "nombre": "Pendiente de Theil-Sen (IC 90 %)",
                    "entradas": ["paso:agregacion"],
                    "metricas": {
                        "por_decada": datos["sen_por_decada"],
                        "ic90_lo": datos["ic90_por_decada"][0],
                        "ic90_hi": datos["ic90_por_decada"][1],
                    },
                },
                {
                    "id": "mann_kendall",
                    "nombre": "Mann-Kendall clásico y Hamed-Rao",
                    "entradas": ["paso:agregacion"],
                    "metricas": {
                        "p_clasico": datos["mk_p"],
                        "p_hamed_rao": datos["mk_hamed_rao_p"],
                        "p_conservador": datos["p_conservador"],
                    },
                },
                {
                    "id": "filtro_enso",
                    "nombre": "Filtro El Niño (regresión con ONI)",
                    "entradas": ["paso:agregacion", "paso:descarga_oni"],
                    "metricas": datos["enso"],
                },
                {
                    "id": "ventanas",
                    "nombre": "Ventanas de 20 años o más",
                    "entradas": ["paso:agregacion"],
                    "metricas": datos["ventanas"],
                },
                {
                    "id": "detectabilidad",
                    "nombre": "Detectabilidad (Weatherhead 1998)",
                    "entradas": ["paso:theil_sen"],
                    "metricas": datos["detectabilidad"],
                },
                {
                    "id": "veredicto",
                    "nombre": "Veredicto preliminar",
                    "descripcion": "Faltan las pruebas de sensor e independencia: el resultado no puede calificar como robusto.",
                    "entradas": [
                        "paso:mann_kendall",
                        "paso:filtro_enso",
                        "paso:ventanas",
                        "paso:detectabilidad",
                    ],
                },
            ],
            "generado_utc": generado,
        }

    t2m = analisis["temperatura_media_anual_C"]
    lluvia = analisis["lluvia_dic_mar_mm"]
    serie_t = "chili_analisis.cabecera_power:temperatura_aire_2m:power_mensual:p1y"
    serie_p = "chili_analisis.cabecera_power:precipitacion:power_mensual:p1y"
    proc_t = procedencia({"nombre": "Media anual de T2M"}, t2m)
    proc_p = procedencia({"nombre": "Suma dic–mar (mm/día × días del mes)"}, lluvia)

    _asegurar_serie(
        sesion,
        SerieCrear.model_validate(
            {
                "id": serie_t,
                "dominio_id": "chili_analisis",
                "unidad_id": "chili_analisis.cabecera_power",
                "variable_id": "temperatura_aire_2m",
                "fuente_id": "power_mensual",
                "unidad": "Cel",
                "frecuencia": "P1Y",
                "agregacion": {"tipo": "media_anual", "origen": "T2M mensual"},
                "descripcion": "Temperatura media anual del aire a 2 m en la celda de la cabecera (NASA POWER, fuente MERRA-2).",
                "procedencia": proc_t,
            }
        ),
    )
    servicio_series.cargar_observaciones(
        sesion,
        serie_t,
        ObservacionesCarga.model_validate(
            {"observaciones": [{"t": date(int(a), 1, 1), "valor": v} for a, v in t2m["serie"].items()]}
        ),
    )
    _asegurar_serie(
        sesion,
        SerieCrear.model_validate(
            {
                "id": serie_p,
                "dominio_id": "chili_analisis",
                "unidad_id": "chili_analisis.cabecera_power",
                "variable_id": "precipitacion",
                "fuente_id": "power_mensual",
                "unidad": "mm",
                "frecuencia": "P1Y",
                "agregacion": {
                    "tipo": "suma_temporada",
                    "meses": [12, 1, 2, 3],
                    "t": "Inicio de la temporada: 1 de diciembre del año anterior",
                },
                "descripcion": "Lluvia acumulada de diciembre a marzo en la celda de la cabecera (NASA POWER, PRECTOTCORR).",
                "procedencia": proc_p,
            }
        ),
    )
    servicio_series.cargar_observaciones(
        sesion,
        serie_p,
        ObservacionesCarga.model_validate(
            {
                "observaciones": [
                    {"t": date(int(a) - 1, 12, 1), "valor": v} for a, v in lluvia["serie"].items()
                ]
            }
        ),
    )

    exps = [
        _expediente_tendencia(
            t2m,
            serie_t,
            "temperatura_aire_2m",
            "Cel/decada",
            proc_t,
            "Temperatura media anual en la cabecera del Chili (1981–2024)",
            "Tendencia de Theil-Sen de la temperatura media anual en la celda de la cabecera, con filtro El Niño, "
            "ventanas y detectabilidad. Preliminar: un solo producto y sin prueba de sensor.",
        ),
        _expediente_tendencia(
            lluvia,
            serie_p,
            "precipitacion",
            "mm/decada",
            proc_p,
            "Lluvia de diciembre a marzo en la cabecera del Chili (1982–2024)",
            "Tendencia de la lluvia de la temporada húmeda en la celda de la cabecera, con su relación con El Niño. "
            "Preliminar: un solo producto y sin prueba de sensor.",
        ),
    ]
    creados = sum(1 for e in exps if servicio_expedientes.publicar(sesion, e, IMPORTADOR)[1])
    return {"series": 2, "expedientes_nuevos": creados}


def importar_expedientes_ciencia(sesion: Session, raiz: Path) -> dict[str, int]:
    """Publica los expedientes que exportó el pipeline científico (`tv publicar --exportar`).

    El archivo es el contrato: cada elemento se valida con `ExpedienteCrear` igual que si llegara por
    `POST /api/v1/expedientes`, y la publicación es idempotente por hash de contenido. Así un
    despliegue nuevo muestra los resultados sin depender del paquete científico.
    """
    ruta = raiz / "resultados" / "contrato" / "expedientes.json"
    if not ruta.exists():
        # No es un error (un despliegue puede no traer ciencia), pero no debe pasar inadvertido.
        log.warning("contrato_ciencia_ausente", extra={"ruta": str(ruta)})
        return {"leidos": 0, "nuevos": 0}
    lista = _leer_json(ruta)
    nuevos = 0
    for crudo in lista:
        datos = ExpedienteCrear.model_validate(crudo)
        nuevos += int(servicio_expedientes.publicar(sesion, datos, IMPORTADOR)[1])
    sesion.commit()
    return {"leidos": len(lista), "nuevos": nuevos}


def importar_todo(sesion: Session, raiz: Path, incluir_ciencia: bool = True) -> dict[str, Any]:
    resumen: dict[str, Any] = {}
    resumen["fuentes"] = importar_fuentes(sesion, raiz)
    resumen.update(importar_catalogos(sesion, raiz))
    resumen["unidades"] = importar_dominios(sesion, raiz)
    resumen["informes_verificacion_nuevos"] = importar_verificacion(sesion, raiz)
    resumen["eventos"] = importar_eventos(sesion, raiz)
    resumen["observaciones_autodema"] = importar_autodema(sesion, raiz)
    resumen["analisis_preliminar"] = importar_analisis_preliminar(sesion, raiz)
    if incluir_ciencia:
        resumen["expedientes_ciencia"] = importar_expedientes_ciencia(sesion, raiz)
    resumen["expedientes_total"] = len(sesion.scalars(select(Expediente.id)).all())
    log.info("importacion_completa", extra={"resumen": resumen})
    return resumen
