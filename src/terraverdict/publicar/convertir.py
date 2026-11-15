"""Conversión de resultados/*.json y expedientes/*.json al contrato de expedientes del backend.

Reglas:
- Solo se copian cifras de los JSON de entrada; los títulos y resúmenes se arman con esas cifras.
- La procedencia conserva el commit, el preregistro, la configuración y el SHA-256 de cada crudo.
- Las reglas de publicación las valida el backend (422 si se violan); aquí no se "arreglan" datos
  para que pasen: si un resultado no cumple el contrato, la publicación falla y se informa.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

# Fuentes del catálogo (config/fuentes.yaml) y carpetas de data/raw que usa cada experimento.
FUENTES = {
    "volcanes": (["gvp_volcanes", "usgs_comcat"], ["gvp", "usgs"]),
    "deslizamientos": (["nasa_glc", "power_diaria"], ["glc", "power_celdas"]),
    "sismos": (["usgs_comcat"], ["usgs"]),
    "sequia": (["power_mensual", "oni"], ["power", "noaa"]),
    "sequia_chirps": (["chirps_v2_diaria", "power_mensual", "oni"], ["chirps", "power", "noaa"]),
    "lluvia_extrema": (["power_diaria", "oni", "ghcn_arequipa"], ["power", "noaa", "ghcn"]),
    "lluvia_extrema_chirps": (["chirps_v2_diaria", "power_diaria", "oni"], ["chirps", "power", "noaa"]),
    "caos": (
        ["power_diaria", "chirps_v2_diaria", "power_mensual", "oni", "usgs_comcat"],
        ["power", "chirps", "noaa", "usgs"],
    ),
}
DOMINIO = {"volcanes": "sur_peru_fenomenos", "deslizamientos": "sur_peru_fenomenos", "sismos": "sur_peru_fenomenos"}
REPOSITORIO = "DiegoNiS/terraverdict"


def _f(x: Any) -> float | None:
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) else None


def _texto(n: float | None, d: int = 3) -> str:
    return "—" if n is None else f"{n:.{d}f}".replace(".", ",")


def procedencia(experimento: str, proc: dict[str, Any], pasos: list[dict[str, Any]]) -> dict[str, Any]:
    fuentes, carpetas = FUENTES[experimento]
    hashes = {
        f"{c}/{e['archivo']}": e["sha256"] for c in carpetas for e in proc.get("crudos", {}).get(c, []) if "sha256" in e
    }
    return {
        "fuentes": [{"fuente_id": f} for f in fuentes],
        "codigo": {
            "repositorio": REPOSITORIO,
            "commit": proc.get("commit"),
            "script": f"tv experimentos ({experimento})",
        },
        "preregistro_sha256": proc.get("preregistro_sha256"),
        "hash_entradas": {**hashes, "config/fenomenos.yaml": proc["config_sha256"]},
        "pasos": pasos,
        "generado_utc": proc["generado_utc"],
    }


def _pasos(*nombres: tuple[str, str]) -> list[dict[str, Any]]:
    pasos, previo = [], None
    for ident, nombre in nombres:
        pasos.append({"id": ident, "nombre": nombre, "entradas": [f"paso:{previo}"] if previo else []})
        previo = ident
    return pasos


def abstencion(a: dict[str, Any]) -> dict[str, Any]:
    publicar = not a.get("abstencion") and bool(a.get("publicar", True))
    return {
        "publicar": publicar,
        "motivos": [] if publicar else list(a.get("motivos") or ["Abstención sin motivo registrado."]),
        "advertencias": list(a.get("advertencias", [])),
    }


def _intervalo(par: Any) -> dict[str, float] | None:
    if not par or len(par) != 2:
        return None
    lo, hi = _f(par[0]), _f(par[1])
    return {"lo": lo, "hi": hi, "nivel": 0.9} if lo is not None and hi is not None and lo <= hi else None


def comparacion(
    experimento: str,
    fenomeno: str,
    tarea: str,
    objetivo: str,
    horizonte: str,
    zoo: dict[str, Any],
    serie_prueba: dict[str, Any],
    abst: dict[str, Any],
    **extra: Any,
) -> dict[str, Any]:
    modelos = []
    for nombre, m in zoo["modelos"].items():
        dm = _f((m.get("diebold_mariano_vs_climatologia") or {}).get("p"))
        modelos.append(
            {
                "nombre": nombre,
                "familia": m["familia"],
                "puntaje_validacion": _f(m["puntaje_validacion"]),
                "puntaje_prueba": _f(m["prueba"].get(m["metrica_principal"])),
                "intervalo_prueba": _intervalo(m.get("ic90_prueba")),
                "p_diebold_mariano": dm,
                "dispersion_semillas": _f(m.get("dispersion_semillas")),
                "referencia": m.get("referencia"),
            }
        )
    fechas = serie_prueba["fechas"]
    return {
        "tipo": "comparacion_modelos",
        "fenomeno": fenomeno,
        "tarea": tarea,
        "objetivo": objetivo[:300],
        "horizonte": horizonte,
        "metrica_principal": next(iter(zoo["modelos"].values()))["metrica_principal"],
        "periodo_prueba": {"desde": fechas[0], "hasta": fechas[-1]},
        "modelos": modelos,
        "mejor_validacion": zoo["mejor_validacion"],
        "abstencion": abstencion(abst),
        **extra,
    }


def _importancia(explicabilidad: dict[str, Any] | None) -> list[dict[str, Any]]:
    return [
        {"variable": i["variable"], "importancia": i["importancia"], "desviacion": i["desviacion"]}
        for i in (explicabilidad or {}).get("importancias", [])
    ]


def _expediente(
    dominio: str, titulo: str, resumen: str, resultado: dict[str, Any], proc: dict[str, Any]
) -> dict[str, Any]:
    return {
        "estado": "preliminar",
        "dominio_id": dominio,
        "titulo": titulo[:200],
        "resumen": resumen[:2000],
        "resultado": resultado,
        "procedencia": proc,
    }


def de_lluvia(nombre: str, r: dict[str, Any]) -> list[dict[str, Any]]:
    zoo, d = r["zoo"], r["definicion"]
    m = zoo["modelos"][zoo["mejor_validacion"]]
    ablaciones = []
    for k, a in r["ablaciones"].items():
        mejor = max(a["modelos"], key=lambda x: a["modelos"][x]["puntaje_validacion"])
        ablaciones.append(
            {
                "nombre": k,
                "variables": a["variables"],
                "mejor_validacion": a["modelos"][mejor]["puntaje_validacion"],
                "mejor_prueba": _f(a["modelos"][mejor]["bss_prueba"]),
            }
        )
    resultado = comparacion(
        nombre,
        "lluvia_extrema",
        "clasificacion",
        d["objetivo"],
        f"{d['horizonte_dias']} día",
        zoo,
        r["serie_prueba"],
        r["abstencion"],
        variables_seleccionadas=r["seleccion_variables"]["seleccionadas"],
        ventana=r["ventana"]["elegida"],
        ablaciones=ablaciones,
        confiabilidad=[c for c in r["confiabilidad_mejor"]["curva"] if c["n"] >= 1],
        ece=_f(r["confiabilidad_mejor"]["ece"]),
        importancia=_importancia(r.get("explicabilidad")),
    )
    fuente = "CHIRPS" if nombre.endswith("chirps") else "NASA POWER"
    pasos = _pasos(
        ("descarga", "Descarga con SHA-256"),
        ("calidad", "Control de calidad y contraste con la estación"),
        ("seleccion", "Selección de variables (mRMR + prior físico)"),
        ("ventana", "Ventana adaptativa (validación)"),
        ("zoologico", "Entrenamiento del zoológico y calibración"),
        ("evaluacion", "Evaluación única en prueba con IC90 y Diebold-Mariano"),
    )
    return [
        _expediente(
            "chili_analisis",
            f"Lluvia fuerte a 1 día en la cabecera del Chili ({fuente})",
            f"Modelo elegido por validación: {zoo['mejor_validacion']}. Habilidad de Brier en prueba "
            f"{_texto(_f(m['prueba'].get('bss_climatologia')))} (IC90 {_texto((_intervalo(m.get('ic90_prueba')) or {}).get('lo'))} a "
            f"{_texto((_intervalo(m.get('ic90_prueba')) or {}).get('hi'))}). Resultado experimental, no una alerta oficial.",
            resultado,
            procedencia(nombre, r["procedencia"], pasos),
        )
    ]


def de_sequia(nombre: str, r: dict[str, Any]) -> list[dict[str, Any]]:
    salida = []
    fuente = "CHIRPS" if nombre.endswith("chirps") else "NASA POWER"
    for h, b in r["horizontes"].items():
        zoo = b["zoo"]
        m = zoo["modelos"][zoo["mejor_validacion"]]
        resultado = comparacion(
            nombre,
            "sequia",
            "regresion",
            b["definicion"]["objetivo"],
            f"{h[1:]} meses" if h != "h1" else "1 mes",
            zoo,
            b["serie_prueba"],
            b["abstencion"],
            ventana=b["definicion"]["ventana_meses"],
            cobertura_conformal_90=_f(m["prueba"].get("cobertura_90")),
            importancia=_importancia(b.get("explicabilidad")),
        )
        pasos = _pasos(
            ("descarga", "Descarga con SHA-256"),
            ("spi", "SPI con parámetros del entrenamiento"),
            ("ventana", "Ventana adaptativa (validación)"),
            ("zoologico", "Entrenamiento del zoológico"),
            ("evaluacion", "Evaluación única en prueba, IC90 e intervalo conformal"),
        )
        salida.append(
            _expediente(
                "chili_analisis",
                f"Sequía: SPI-3 a {h[1:]} mes(es) en la cabecera del Chili ({fuente})",
                f"Modelo elegido por validación: {zoo['mejor_validacion']}. Habilidad en prueba "
                f"{_texto(_f(m['prueba'].get('habilidad_climatologia')))}; cobertura conformal del 90 %: "
                f"{_texto(_f(m['prueba'].get('cobertura_90')))}.",
                resultado,
                procedencia(nombre, r["procedencia"], pasos),
            )
        )
    return salida


def de_sismos(r: dict[str, Any]) -> list[dict[str, Any]]:
    b = r["valor_b"]["todos"]
    sismicidad = {
        "tipo": "sismicidad",
        "fuente": r["catalogo"]["fuente"],
        "periodo": {"desde": r["catalogo"]["desde"], "hasta": r["catalogo"]["hasta"]},
        "radio_km": r["catalogo"]["radio_km"],
        "eventos": r["catalogo"]["eventos"],
        "mc": r["completitud"]["mc_usada"],
        "valor_b": b["b"],
        "intervalo_b": _intervalo(b["ic90_bootstrap"]),
        "independientes": r["desagrupamiento"]["independientes"],
        "cv_intereventos": _f(r["intereventos_independientes"]["cv"]),
        "tasa_anual_mc": r["tasa_anual_m_mayor_mc"],
        "conteos_anuales": r["conteos_anuales"],
        "mapa": [
            {"fecha": e["t"], "lat": e["lat"], "lon": e["lon"], "magnitud": e["m"], "profundidad_km": _f(e.get("z"))}
            for e in r["mapa"]
        ],
    }
    p = r["pronostico_conteos"]
    conteos = comparacion(
        "sismos", "sismos", "conteo", p["definicion"], "1 mes", p["zoo"], p["serie_prueba"], p["abstencion"]
    )
    pasos = _pasos(
        ("descarga", "Descarga USGS ComCat con SHA-256"),
        ("completitud", "Magnitud de completitud"),
        ("desagrupamiento", "Desagrupamiento de Gardner-Knopoff"),
        ("estadistica", "Valor b, tasas e intereventos"),
    )
    return [
        _expediente(
            "sur_peru_fenomenos",
            "Sismicidad a 350 km de Arequipa (USGS)",
            f"Mc = {_texto(sismicidad['mc'], 1)}; b = {_texto(b['b'], 2)} (IC90 {_texto(sismicidad['intervalo_b']['lo'], 2)} a "
            f"{_texto(sismicidad['intervalo_b']['hi'], 2)}). No es un pronóstico de sismos.",
            sismicidad,
            procedencia("sismos", r["procedencia"], pasos),
        ),
        _expediente(
            "sur_peru_fenomenos",
            "Conteo sísmico mensual frente a Poisson (USGS)",
            f"¿Hay estructura temporal más allá de un Poisson? Modelo elegido: {p['zoo']['mejor_validacion']}. "
            "No es un pronóstico de sismos.",
            conteos,
            procedencia(
                "sismos",
                r["procedencia"],
                [
                    *pasos,
                    {"id": "zoologico", "nombre": "Zoológico de modelos de conteo", "entradas": ["paso:estadistica"]},
                ],
            ),
        ),
    ]


def de_volcanes(r: dict[str, Any]) -> list[dict[str, Any]]:
    volcanes = [
        {
            "numero_gvp": v["numero_gvp"],
            "nombre": v["nombre"],
            "lat": v["lat"],
            "lon": v["lon"],
            "distancia_km": v["distancia_a_arequipa_km"],
            "erupciones": v["confirmadas_desde_1550"],
            "probabilidad_anual": v["probabilidad_anual_inicio"],
            "intervalo": _intervalo(v["ic90_probabilidad_anual"]),
            "intervalo_medio_anios": _f(v.get("intervalo_medio_anios")),
            "iev_maximo": v.get("iev_maximo_historico"),
            "ultima_erupcion": v.get("ultima_erupcion"),
            "inicios": sorted(
                e["inicio"]
                for e in v["erupciones"]
                if e["tipo"] == "Confirmed Eruption"
                and e["inicio"] is not None
                and e["inicio"] >= r["inicio_registro_historico"]
            ),
        }
        for v in r["volcanes"]
    ]
    resultado = {
        "tipo": "recurrencia",
        "fuente": r["fuente"],
        "inicio_registro": r["inicio_registro_historico"],
        "metodo": f"{r['metodo']['tasa']}; IC {r['metodo']['ic']}",
        "volcanes": volcanes,
        "abstencion": abstencion(r["abstencion"]),
    }
    top = max(volcanes, key=lambda v: v["erupciones"])
    return [
        _expediente(
            "sur_peru_fenomenos",
            "Recurrencia histórica de erupciones en el sur del Perú (GVP)",
            f"{len(volcanes)} volcanes. El más activo desde {r['inicio_registro_historico']}: {top['nombre']} "
            f"({top['erupciones']} erupciones). Frecuencias históricas, no pronósticos.",
            resultado,
            procedencia(
                "volcanes",
                r["procedencia"],
                _pasos(("descarga", "Descarga GVP"), ("recurrencia", "Poisson con IC exacto")),
            ),
        )
    ]


def de_deslizamientos(r: dict[str, Any], eventos_minimos: int) -> list[dict[str, Any]]:
    eventos = [
        {
            "id": str(e["id"]),
            "fecha": e["fecha"],
            "lat": e["lat"],
            "lon": e["lon"],
            "lugar": e.get("lugar"),
            "categoria": e.get("categoria"),
            "detonante": e.get("detonante"),
            "lluvia_mm": {k.split("_")[1]: _f(v) for k, v in e.items() if k.startswith("lluvia_")},
            "percentiles": {k.split("_")[1]: _f(v) for k, v in e.items() if k.startswith("percentil_")},
        }
        for e in r["eventos"]
    ]
    resultado = {
        "tipo": "inventario",
        "fenomeno": "deslizamientos",
        "fuente": r["fuente"],
        "eventos": eventos,
        "eventos_minimos_umbral": eventos_minimos,
        "umbral_estimado": False,
        "abstencion": abstencion(r["abstencion"]),
    }
    return [
        _expediente(
            "sur_peru_fenomenos",
            "Deslizamientos detonados por lluvia en el sur del Perú (NASA GLC)",
            f"{len(eventos)} eventos con serie de lluvia; se necesitan {eventos_minimos} para estimar un umbral.",
            resultado,
            procedencia(
                "deslizamientos",
                r["procedencia"],
                _pasos(("descarga", "Descarga GLC y POWER"), ("antecedente", "Lluvia antecedente y percentiles")),
            ),
        )
    ]


def de_caos(r: dict[str, Any]) -> list[dict[str, Any]]:
    series = []
    for nombre, s in r["series"].items():
        nl = s.get("no_linealidad") or {}
        sustitutos = [
            {
                "estadistico": k,
                "original": _f(v.get("original")),
                "sustitutos": [x for x in v.get("valores", []) if _f(x) is not None][:500],
                "p": _f(v.get("p")),
            }
            for k, v in (
                ("asimetria_temporal", nl.get("asimetria_temporal")),
                ("error_prediccion_analogos", nl.get("error_prediccion_analogos")),
            )
            if v and _f(v.get("original")) is not None and _f(v.get("p")) is not None
        ]
        d2 = s.get("dimension_correlacion") or {}
        series.append(
            {
                "serie_id": nombre,
                "fuente": s["fuente"],
                "n": s["n"],
                "unidad_tiempo": s["unidad_tiempo"],
                "veredicto": s["veredicto"],
                "condiciones": s.get("condiciones_caos", {}),
                "tau": (s.get("embedding") or {}).get("tau"),
                "m": (s.get("embedding") or {}).get("m"),
                "d2": _f(d2.get("d2_saturado")) if d2.get("satura") else None,
                "lyapunov": _f((s.get("lyapunov") or {}).get("lambda")),
                "k_01": _f((s.get("prueba_01") or {}).get("K")),
                "determinismo_rqa": _f((s.get("recurrencia") or {}).get("determinismo")),
                "espacio_fases": s.get("espacio_fases", []),
                "sustitutos": sustitutos,
                "recurrencia_miniatura": (s.get("recurrencia") or {}).get("miniatura", [])[:200],
            }
        )
    resultado = {"tipo": "caos", "series": series, "metodo": r["lectura"][:1000]}
    resumen = ", ".join(f"{k.replace('_', ' ')}: {v}" for k, v in r["resumen_veredictos"].items())
    return [
        _expediente(
            "chili_analisis",
            "Dinámica de las series reales: caos, no linealidad o ruido",
            f"{len(series)} series evaluadas con sustitutos IAAFT, D2, Lyapunov y prueba 0-1. Veredictos: {resumen}.",
            resultado,
            procedencia(
                "caos",
                r["procedencia"],
                _pasos(
                    ("descarga", "Descarga"),
                    ("anomalias", "Anomalías respecto del entrenamiento"),
                    ("diagnostico", "Diagnóstico integrado"),
                ),
            ),
        )
    ]


def de_resultados(carpeta: Path, eventos_minimos: int = 30) -> list[dict[str, Any]]:
    salida: list[dict[str, Any]] = []
    for ruta in sorted(carpeta.glob("*.json")):
        nombre = ruta.stem
        if nombre in ("indice", "fuentes"):
            continue
        r = json.loads(ruta.read_text())
        if nombre.startswith("lluvia_extrema"):
            salida += de_lluvia(nombre, r)
        elif nombre.startswith("sequia"):
            salida += de_sequia(nombre, r)
        elif nombre == "sismos":
            salida += de_sismos(r)
        elif nombre == "volcanes":
            salida += de_volcanes(r)
        elif nombre == "deslizamientos":
            salida += de_deslizamientos(r, eventos_minimos)
        elif nombre == "caos":
            salida += de_caos(r)
    return salida


def _estado_prueba(clave: str, sello: dict[str, Any], resultado: dict[str, Any]) -> dict[str, Any]:
    estado = "fallida" if clave in sello["fallan"] else ("pendiente" if clave in sello["pendientes"] else "aprobada")
    datos = resultado.get(clave) or {}
    metricas = (
        {k: v for k, v in datos.items() if isinstance(v, (int, float, str, bool)) and not isinstance(v, dict)}
        if isinstance(datos, dict)
        else {}
    )
    return {"estado": estado, "metricas": metricas}


def de_tendencia(e: dict[str, Any], alfa: float) -> dict[str, Any]:
    """Expediente de tendencia del paquete (Sello de Confianza) → contrato `tendencia` del backend.

    El paquete llama 'frágil' a una tendencia significativa con pruebas pendientes; el backend
    reserva 'fragil' para pruebas FALLIDAS y usa 'preliminar' para las pendientes. Se respeta
    el backend: con pruebas pendientes y ninguna fallida, el veredicto es 'preliminar'.
    """
    r, sello = e["resultado"], e["resultado"]["sello"]
    p = r["mk"]["p_variantes"]
    significativa = r["mk"]["p_conservador"] <= alfa
    if sello["fallan"] and significativa:
        veredicto = "fragil"
    elif sello["pendientes"]:
        veredicto = "preliminar" if significativa else "sin_tendencia"
    else:
        veredicto = "robusta" if significativa else "sin_tendencia"
    unidad = "Cel/decada" if e["objeto"]["variable"].startswith("t2m") else "mm/decada"
    claves = ("ventanas", "enso", "sensor", "independencia", "detectabilidad")
    resultado = {
        "tipo": "tendencia",
        "periodo": {"desde": str(e["periodo"]["desde"]), "hasta": str(e["periodo"]["hasta"])},
        "n": e["periodo"]["n"],
        "pendiente": {
            "valor": r["sen"]["sen_por_decada"],
            "intervalo": {"lo": r["sen"]["ic_por_decada"][0], "hi": r["sen"]["ic_por_decada"][1], "nivel": 0.9},
            "unidad": unidad,
        },
        "significancia": {
            "p_mann_kendall": p["original"],
            "p_hamed_rao": p.get("hamed_rao"),
            "p_conservador": r["mk"]["p_conservador"],
            "alfa": alfa,
        },
        "sello": {k: _estado_prueba(k, sello, r) for k in claves},
        "veredicto": veredicto,
        "anios_para_decidir": _f((r.get("detectabilidad") or {}).get("anios_necesarios")),
    }
    proc = e["procedencia"]
    return _expediente(
        "chili_analisis",
        f"Tendencia de {e['objeto']['variable'].replace('_', ' ')} ({e['periodo']['desde']}–{e['periodo']['hasta']})",
        f"Theil-Sen {_texto(r['sen']['sen_por_decada'])} {unidad.replace('Cel', '°C')}; p conservador "
        f"{_texto(r['mk']['p_conservador'], 4)}. Sello del paquete: {sello['codigo']} ({sello.get('nota') or 'sin nota'}).",
        resultado,
        {
            "fuentes": [{"fuente_id": "power_mensual"}],
            "codigo": {"repositorio": REPOSITORIO, "commit": proc.get("codigo_commit"), "script": "tv trends"},
            "preregistro_sha256": proc["preregistro_sha256"],
            "hash_entradas": {"entradas": proc["entradas_sha256"]},
            "pasos": _pasos(
                ("serie", "Serie anual"), ("mann_kendall", "Mann-Kendall conservador"), ("sello", "Sello de Confianza")
            ),
            "generado_utc": proc["generado_utc"],
        },
    )


def de_expedientes(carpeta: Path, alfa: float) -> list[dict[str, Any]]:
    return [de_tendencia(json.loads(p.read_text()), alfa) for p in sorted(carpeta.glob("TV-*.json"))]
