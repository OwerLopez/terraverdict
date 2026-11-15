"""Informe de experimentos (docs/experimentos.md) generado SOLO desde resultados/*.json.

Regla: ninguna cifra se escribe a mano. Cada número del informe se lee de un JSON con procedencia
(commit, hashes de los crudos, configuración). El texto fijo describe métodos y cómo leer las
tablas; las conclusiones por fenómeno se derivan de reglas explícitas sobre esos números
(p. ej., "IC90 por encima de 0" o "abstención"), no de la redacción.
Uso: ``tv informe``.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from ..publicar.convertir import veredicto_backend
from .comun import parametros

# Regla de lectura de config/modelos.yaml (la misma que usa la web)
P_DM = float(parametros()["evaluacion"]["p_diebold_mariano"])
P_DM_TEXTO = f"{P_DM:.2f}".replace(".", ",")

NOMBRES = {
    "ref_climatologia": "Climatología (referencia)",
    "ref_persistencia": "Persistencia (referencia)",
    "logistica": "Regresión logística",
    "ridge": "Ridge",
    "poisson_glm": "GLM de Poisson",
    "gbm": "Gradient boosting",
    "mlp": "MLP",
    "dlinear": "DLinear",
    "lstm": "LSTM",
    "gru": "GRU",
    "tcn": "TCN",
    "nbeats": "N-BEATS",
    "nhits": "N-HiTS",
    "patchtst": "PatchTST",
    "itransformer": "iTransformer",
    "ssm_selectivo": "SSM selectivo",
    "ensamble_top3": "Ensamble (3 mejores en validación)",
    "ensamble_ponderado": "Ensamble ponderado (pesos de validación)",
    "seleccion_validacion": "Elegido en validación (año a año)",
}
VEREDICTOS = {
    "lineal_estocastica": "lineal estocástica",
    "no_lineal_sin_caos_demostrado": "no lineal, sin caos demostrado",
    "compatible_con_caos_baja_dimension": "compatible con caos de baja dimensión",
    "regular": "regular",
    "insuficiente": "datos insuficientes",
}
METRICA = {
    "bss_climatologia": "habilidad de Brier frente a la climatología",
    "habilidad_climatologia": "habilidad (1 − ECM/ECM de la climatología)",
    "ganancia_informacion_bits": "ganancia de información frente a Poisson de tasa constante (bits/mes)",
}


def n(x: Any, d: int = 3) -> str:
    """Número con coma decimal; '—' si falta."""
    if x is None:
        return "—"
    if isinstance(x, bool):
        return "sí" if x else "no"
    if isinstance(x, int):
        return f"{x:,}".replace(",", " ")
    if isinstance(x, float):
        texto = f"{x:.{d}f}"
        return ("0" + texto[2:] if texto.startswith("-0") and float(texto) == 0 else texto).replace(".", ",")
    return str(x)


def ic(par: list[float | None] | None, d: int = 3) -> str:
    if not par or par[0] is None or par[1] is None:
        return "—"
    return f"{n(par[0], d)} a {n(par[1], d)}"


def tabla(cabecera: list[str], filas: Iterable[list[Any]]) -> str:
    lineas = ["| " + " | ".join(cabecera) + " |", "|" + "|".join("---" for _ in cabecera) + "|"]
    lineas += ["| " + " | ".join(str(c).replace("|", "\\|") for c in f) + " |" for f in filas]
    return "\n".join(lineas)


def nivel_evidencia(m: dict[str, Any]) -> str:
    """Regla del proyecto (la misma que muestra la web): 'confirmada' exige IC90 por bootstrap de
    bloques > 0 Y Diebold-Mariano p < 0,10; 'indicio' cumple solo una; si no, 'no_confirmada'.

    Son dos pruebas complementarias: el bootstrap mide la incertidumbre de la habilidad y DM prueba
    que la diferencia de pérdidas no es azar con errores autocorrelacionados (varianza HAC).
    """
    lo = (m.get("ic90_prueba") or [None])[0]
    p = (m.get("diebold_mariano_vs_climatologia") or {}).get("p")
    ic = lo is not None and lo > 0
    dm = p is not None and p < P_DM
    return "confirmada" if ic and dm else ("indicio" if ic or dm else "no_confirmada")


def lectura_habilidad(m: dict[str, Any]) -> str:
    if (m.get("ic90_prueba") or [None])[0] is None:
        return "sin IC"
    return {
        "confirmada": f"confirmada (IC90 > 0 y DM p < {P_DM_TEXTO})",
        "indicio": f"indicio (solo una de las dos pruebas: IC90 > 0 o DM p < {P_DM_TEXTO})",
        "no_confirmada": f"no confirmada (IC90 incluye 0 y DM p ≥ {P_DM_TEXTO})",
    }[nivel_evidencia(m)]


def tabla_zoo(zoo: dict[str, Any]) -> str:
    modelos = zoo["modelos"]
    orden = [k for k in modelos if modelos[k]["familia"] == "referencia"] + zoo["ranking_validacion"]
    principal = next(iter(modelos.values()))["metrica_principal"]
    filas = []
    for k in orden:
        m = modelos[k]
        dm = m.get("diebold_mariano_vs_climatologia") or {}
        filas.append(
            [
                ("**" + NOMBRES.get(k, k) + "**") if k == zoo["mejor_validacion"] else NOMBRES.get(k, k),
                m["familia"].replace("_", " "),
                n(m.get("puntaje_validacion")),
                n(m["prueba"].get(principal)),
                ic(m.get("ic90_prueba")),
                n(dm.get("p")),
                n(m.get("dispersion_semillas")) if m["familia"] == "red_neuronal" else "",
            ]
        )
    return (
        f"Métrica principal: {METRICA.get(principal, principal)}. En **negrita**, el modelo elegido "
        "por validación (la prueba no participa en la elección).\n\n"
        + tabla(
            [
                "Modelo",
                "Familia",
                "Validación",
                "Prueba",
                "IC90 prueba",
                "p Diebold-Mariano",
                "Dispersión entre semillas",
            ],
            filas,
        )
    )


def bloque_abstencion(a: dict[str, Any]) -> str:
    estado = "**Se publica**" if a.get("publicar") and not a.get("abstencion") else "**Abstención**"
    lineas = [f"- Decisión: {estado}."]
    lineas += [f"- Motivo: {m}" for m in a.get("motivos", [])]
    lineas += [f"- Advertencia: {m}" for m in a.get("advertencias", [])]
    return "\n".join(lineas)


def bloque_deriva(deriva: dict[str, Any]) -> str:
    filas = [[k, n(v["psi"]), n(v["ks_p"], 4), "sí" if v["deriva"] else "no"] for k, v in deriva.items()]
    return tabla(["Variable", "PSI (entrenamiento → prueba)", "p KS", "Deriva (PSI > 0,25)"], filas)


def seccion_lluvia(r: dict[str, Any], titulo: str) -> str:
    d, zoo = r["definicion"], r["zoo"]
    mejor = zoo["modelos"][zoo["mejor_validacion"]]
    sel = r["seleccion_variables"]
    partes = [
        f"## {titulo}",
        f"**Fuente de la lluvia:** {r.get('fuente_lluvia', 'NASA POWER')}.  \n**Objetivo:** {d['objetivo']}; "
        f"horizonte {d['horizonte_dias']} día; meses {', '.join(str(m) for m in d['meses_evaluados'])}.",
        tabla(
            ["Partición", "Días", "Eventos"],
            [[k, n(v), n(d["eventos"][k])] for k, v in d["n"].items()],
        ),
        f"Tasa base en entrenamiento: {n(d['tasa_base_entrenamiento'])}.",
        "### Modelos",
        tabla_zoo(zoo),
        f"Lectura (regla IC90): habilidad del modelo elegido {lectura_habilidad(mejor)}.",
        "### Variables seleccionadas (mRMR con prior físico, solo entrenamiento)",
        "Redundancia = |ρ de Spearman| máxima con las ya elegidas; puntaje = peso × IM × (1 − redundancia). "
        "Las variables de estación del año (seno y coseno) se añaden siempre.",
        tabla(
            ["Variable", "Información mutua", "Redundancia", "Peso físico", "Puntaje"],
            [
                [
                    s["variable"] + (" (fija)" if s.get("fija") else ""),
                    n(s["informacion_mutua"], 4),
                    n(s["redundancia"], 4),
                    n(s["peso_fisico"], 1),
                    n(s["puntaje"], 4),
                ]
                for s in sel["detalle"]
            ],
        ),
        "Descartadas: "
        + (
            "; ".join(
                f"{s['variable']} (IM {n(s['informacion_mutua'], 4)}"
                + (f", umbral nulo {n(s['umbral_nulo'], 4)}" if "umbral_nulo" in s else "")
                + (f", {s['motivo']}" if "motivo" in s else "")
                + ")"
                for s in sel["descartadas"]
            )
            or "ninguna"
        )
        + ".",
        "### Ventana",
        f"Elegida: **{r['ventana']['elegida']} días** (mejor en validación). Sugeridas por la señal: "
        + ", ".join(f"{k} = {v}" for k, v in r["ventana"]["sugeridas_por_la_senal"].items())
        + ".",
        tabla(
            ["Ventana (días)", "Habilidad de Brier en validación"],
            [[k, n(v)] for k, v in r["ventana"]["puntuacion_validacion"].items()],
        ),
        "### Ablaciones (habilidad de Brier; validación / prueba)",
        tabla(
            ["Conjunto de variables", *sorted({m for a in r["ablaciones"].values() for m in a["modelos"]})],
            [
                [
                    nombre.replace("_", " "),
                    *[
                        f"{n(a['modelos'][m]['puntaje_validacion'])} / {n(a['modelos'][m]['bss_prueba'])}"
                        if m in a["modelos"]
                        else "—"
                        for m in sorted({m for a in r["ablaciones"].values() for m in a["modelos"]})
                    ],
                ]
                for nombre, a in r["ablaciones"].items()
            ],
        ),
        "### Calibración del modelo elegido (prueba)",
        f"ECE = {n(r['confiabilidad_mejor']['ece'])}.",
        tabla(
            ["Probabilidad pronosticada", "Frecuencia observada", "n"],
            [[n(c["pronosticada"]), n(c["observada"]), n(c["n"])] for c in r["confiabilidad_mejor"]["curva"]],
        ),
        "### Eventos documentados en el periodo de prueba",
        tabla(
            ["Evento", "Mes", "Días con lluvia fuerte", "P media del modelo esos días", "P climatológica esos días"],
            [
                [
                    e["titulo"],
                    e["mes"],
                    n(e["dias_lluvia_fuerte_observados"]),
                    n(e["probabilidad_media_modelo_en_dias_fuertes"]),
                    n(e["probabilidad_media_climatologia_en_dias_fuertes"]),
                ]
                for e in r["eventos_documentados"]
            ],
        )
        if r["eventos_documentados"]
        else "Ningún evento documentado cae en el periodo de prueba.",
        "### Deriva de las entradas",
        bloque_deriva(r["deriva"]),
        "### Publicación",
        bloque_abstencion(r["abstencion"]),
    ]
    c = r["calidad"].get("contraste_ciudad_vs_estacion")
    if c:
        partes += [
            "### Control de calidad: celda POWER de la ciudad frente a la estación GHCN",
            tabla(
                ["Días comunes", "r diario", "r mensual", "p99 POWER (mm)", "p99 estación (mm)"],
                [
                    [
                        n(c["dias_comunes"]),
                        n(c["r_diario"]),
                        n(c["r_mensual"]),
                        n(c["p99_diario_power"], 1),
                        n(c["p99_diario_estacion"], 1),
                    ]
                ],
            ),
        ]
    return "\n\n".join(partes)


def seccion_sequia(r: dict[str, Any], titulo: str) -> str:
    partes = [
        f"## {titulo}",
        f"Fuente de la lluvia para el SPI: **{r['calidad'].get('fuente_lluvia', 'power').upper()}**.",
    ]
    reg = r["regimenes_spi3"]
    partes.append(
        f"Regímenes del SPI-3 (PELT): {len(reg['puntos_cambio'])} puntos de cambio"
        + (f" ({', '.join(reg['puntos_cambio'])})" if reg["puntos_cambio"] else "")
        + "."
    )
    for b in r["horizontes"].values():
        zoo = b["zoo"]
        mejor = zoo["modelos"][zoo["mejor_validacion"]]
        c = b["categoria_sequia_spi_menor_1"]
        partes += [
            f"### {b['definicion']['objetivo']} (ventana {b['definicion']['ventana_meses']} meses)",
            tabla(["Partición", "Meses"], [[k, n(v)] for k, v in b["definicion"]["n"].items()]),
            tabla_zoo(zoo),
            f"Lectura (regla IC90): habilidad del modelo elegido {lectura_habilidad(mejor)}. Habilidad frente a "
            f"persistencia en prueba: {n(mejor['prueba'].get('habilidad_persistencia'))}. Cobertura del intervalo "
            f"conformal del 90 % en prueba: {n(mejor['prueba'].get('cobertura_90'))} (ancho {n(mejor['prueba'].get('ancho_intervalo_90'))}).",
            f"Categoría sequía (SPI-3 ≤ −1) en prueba: aciertos {c['aciertos']}, falsas alarmas {c['falsas_alarmas']}, "
            f"fallos {c['fallos']}; POD {n(c['pod'])}, FAR {n(c['far'])}, CSI {n(c['csi'])}.",
            bloque_abstencion(b["abstencion"]),
        ]
    return "\n\n".join(partes)


def seccion_sismos(r: dict[str, Any]) -> str:
    cat, b, p = r["catalogo"], r["valor_b"], r["pronostico_conteos"]
    zoo = p["zoo"]
    mejor = zoo["modelos"][zoo["mejor_validacion"]]
    return "\n\n".join(
        [
            "## Sismos (USGS ComCat)",
            f"Catálogo: {n(cat['eventos'])} eventos a menos de {cat['radio_km']} km de Arequipa, {cat['desde']} a {cat['hasta']}.",
            tabla(
                ["Magnitud", "Valor"],
                [
                    ["Mc por máxima curvatura", n(r["completitud"]["mc_maxima_curvatura"], 1)],
                    ["Mc usada (conservadora)", n(r["completitud"]["mc_usada"], 1)],
                    [
                        "b (todos, M ≥ Mc)",
                        f"{n(b['todos']['b'])} (IC90 {ic(b['todos']['ic90_bootstrap'])}), n = {n(b['todos']['n'])}",
                    ],
                    [
                        "b (desagrupados)",
                        f"{n(b['desagrupados']['b'])} (IC90 {ic(b['desagrupados']['ic90_bootstrap'])}), n = {n(b['desagrupados']['n'])}",
                    ],
                    [
                        "Independientes / dependientes (Gardner-Knopoff)",
                        f"{n(r['desagrupamiento']['independientes'])} / {n(r['desagrupamiento']['dependientes'])}",
                    ],
                    ["CV de intereventos independientes", n(r["intereventos_independientes"]["cv"])],
                    ["Tasa anual M ≥ Mc", n(r["tasa_anual_m_mayor_mc"], 2)],
                ],
            ),
            "CV ≈ 1 es lo esperado en un proceso de Poisson; > 1, agrupamiento; < 1, cuasiperiodicidad.",
            f"### Conteo mensual del mes siguiente ({p['definicion']})",
            tabla_zoo(zoo),
            f"Lectura (regla IC90): {lectura_habilidad(mejor)}. {r['advertencia']}",
            bloque_abstencion(p["abstencion"]),
            "### Sismos de M ≥ 6,5",
            tabla(
                ["Fecha (UTC)", "M", "Profundidad (km)", "Lugar"],
                [
                    [g["tiempo"][:10], n(g["magnitud"], 1), n(g["profundidad_km"], 0), g["lugar"]]
                    for g in r["grandes_sismos"]
                ],
            ),
        ]
    )


def seccion_volcanes(r: dict[str, Any]) -> str:
    filas = [
        [
            v["nombre"],
            n(v["distancia_a_arequipa_km"], 1),
            n(v["confirmadas_desde_1550"]),
            n(100 * v["probabilidad_anual_inicio"], 2),
            ic([100 * x for x in v["ic90_probabilidad_anual"]], 2),
            n(v["intervalo_medio_anios"], 1),
            n(v["iev_maximo_historico"]),
        ]
        for v in r["volcanes"]
        if v["confirmadas_holoceno"] > 0
    ]
    return "\n\n".join(
        [
            "## Volcanes (Smithsonian GVP)",
            f"Frecuencia histórica de inicio de erupción desde {r['inicio_registro_historico']} ({r['metodo']['tasa']}; IC {r['metodo']['ic']}).",
            tabla(
                [
                    "Volcán",
                    "Distancia a Arequipa (km)",
                    "Erupciones desde 1550",
                    "P anual (%)",
                    "IC90 (%)",
                    "Intervalo medio (años)",
                    "IEV máximo",
                ],
                filas,
            ),
            bloque_abstencion(r["abstencion"]),
        ]
    )


def seccion_deslizamientos(r: dict[str, Any]) -> str:
    return "\n\n".join(
        [
            "## Deslizamientos (NASA GLC + POWER)",
            f"{n(r['eventos_peru'])} deslizamientos en Perú en el catálogo; {n(r['eventos_dominio'])} en el dominio sur; "
            f"{n(r['eventos_por_lluvia_analizados'])} detonados por lluvia con serie de lluvia.",
            tabla(
                ["Acumulado", "Mediana del percentil del mismo mes", "Fracción sobre p75"],
                [
                    [k, n(v["mediana_percentil"], 1), n(v["fraccion_sobre_p75"])]
                    for k, v in r["resumen_percentiles"].items()
                ],
            ),
            bloque_abstencion(r["abstencion"]),
        ]
    )


def seccion_caos(r: dict[str, Any]) -> str:
    filas = []
    for nombre, s in r["series"].items():
        nl = s.get("no_linealidad", {})
        p_tra = (nl.get("asimetria_temporal") or {}).get("p")
        p_nlpe = (nl.get("error_prediccion_analogos") or {}).get("p")
        d2 = s.get("dimension_correlacion") or {}
        filas.append(
            [
                nombre.replace("_", " "),
                n(s["n"]),
                f"**{VEREDICTOS.get(s['veredicto'], s['veredicto'])}**",
                n(p_tra),
                n(p_nlpe),
                n(d2.get("d2_saturado")) if d2.get("satura") else "no satura",
                n((s.get("lyapunov") or {}).get("lambda")),
                n((s.get("prueba_01") or {}).get("K")),
            ]
        )
    resumen = ", ".join(f"{VEREDICTOS.get(k, k)}: {v}" for k, v in r["resumen_veredictos"].items())
    return "\n\n".join(
        [
            "## Dinámica: caos, no linealidad o ruido",
            r["lectura"],
            tabla(
                ["Serie", "n", "Veredicto", "p asimetría temporal", "p predicción por análogos", "D2", "λ", "K (0-1)"],
                filas,
            ),
            f"Resumen: {resumen}.",
            "En las series sin no linealidad significativa, D2, λ y K se informan pero **no se interpretan**: un "
            "proceso lineal estocástico también puede dar un D2 bajo o un K ≈ 1. La prueba 0-1 no distingue caos de ruido.",
        ]
    )


def seccion_fuentes(r: dict[str, Any]) -> str:
    ll, te = r["lluvia"], r["temperatura"]
    partes = [
        "## Contraste entre fuentes",
        "### Lluvia en la ciudad frente a la estación GHCN (ordenado por r mensual)",
        tabla(
            [
                "Fuente",
                "Días comunes",
                "r diario",
                "r días húmedos",
                "r mensual",
                "Totales fuente/estación",
                "p99 fuente / estación (mm)",
            ],
            [
                [
                    c["a"],
                    n(c["dias_comunes"]),
                    n(c["r_diario"]),
                    n(c["r_diario_dias_humedos"]),
                    n(c["r_mensual"]),
                    n(c["razon_totales_a_b"], 2),
                    f"{n(c['p99_diario_mm'][c['a']], 1)} / {n(c['p99_diario_mm'][c['b']], 1)}",
                ]
                for c in ll["ciudad_frente_a_estacion"]
            ],
        ),
        "### Lluvia en la cabecera entre productos",
        tabla(
            ["Par", "Días", "r diario", "r mensual", "Media anual (mm)", "Días ≥ 1 mm"],
            [
                [
                    f"{c['a']} · {c['b']}",
                    n(c["dias_comunes"]),
                    n(c["r_diario"]),
                    n(c["r_mensual"]),
                    f"{n(c['media_anual_mm'][c['a']], 0)} / {n(c['media_anual_mm'][c['b']], 0)}",
                    f"{n(c['fraccion_dias_humedos_1mm'][c['a']])} / {n(c['fraccion_dias_humedos_1mm'][c['b']])}",
                ]
                for c in ll["cabecera_entre_fuentes"]
            ],
        ),
        "### Tendencia de la lluvia de dic–mar por fuente (Theil-Sen; p conservador de Mann-Kendall)",
        tabla(
            ["Fuente", "Periodo", "Media (mm)", "Sen (mm/década)", "IC90", "p"],
            [
                [
                    t["fuente"],
                    f"{t['desde']}–{t['hasta']}",
                    n(t["media"], 0),
                    n(t["sen_por_decada"], 1),
                    ic(t["ic90_por_decada"], 1),
                    n(t["p_mk_conservador"]),
                ]
                for t in ll["tendencia_dic_mar"]
            ],
        ),
    ]
    if ll.get("nota_imerg"):
        partes.append(f"Nota: {ll['nota_imerg']}")
    partes += [
        "### Temperatura",
        tabla(
            ["Variable de la estación GHCN", "Días", "Sesgo POWER − estación (°C)", "r de anomalías diarias"],
            [
                [k, n(v["dias_comunes"]), n(v["sesgo_power_menos_estacion_C"], 2), n(v["r_anomalias_diarias"])]
                for k, v in te["estacion_frente_a_power"].items()
            ],
        ),
        tabla(
            ["Punto", "Banda MODIS", "Frente a", "Compuestos", "r de anomalías", "Media LST / POWER (°C)"],
            [
                [
                    p,
                    b,
                    v["frente_a"],
                    n(v["compuestos"]),
                    n(v["r_anomalias"]),
                    f"{n(v['media_lst_C'], 1)} / {n(v['media_power_C'], 1)}",
                ]
                for p, bandas in te["modis_frente_a_power"].items()
                for b, v in bandas.items()
            ],
        )
        if te["modis_frente_a_power"]
        else "MODIS no disponible en esta corrida.",
        tabla(
            ["Fuente", "Periodo", "Media (°C)", "Sen (°C/década)", "IC90", "p"],
            [
                [
                    t["fuente"],
                    f"{t['desde']}–{t['hasta']}",
                    n(t["media"], 2),
                    n(t["sen_por_decada"], 3),
                    ic(t["ic90_por_decada"], 3),
                    n(t["p_mk_conservador"]),
                ]
                for t in te["tendencias_media_anual"]
            ],
        ),
        te["nota"],
    ]
    s = r.get("sismos_usgs_frente_a_igp")
    if s:
        dm = s["diferencia_magnitud_igp_menos_usgs"] or {}
        partes += [
            "### Sismos: USGS frente a IGP",
            tabla(
                ["Magnitud", "Valor"],
                [
                    ["Periodo", f"{s['periodo'][0]} a {s['periodo'][1]}"],
                    ["Reportados por el IGP (radio)", n(s["igp_reportados"])],
                    ["USGS M ≥ 4 (mismo periodo)", n(s["usgs_m_mayor_4"])],
                    ["Emparejados", f"{n(s['emparejados'])} ({s['criterio_emparejamiento']})"],
                    ["Fracción de USGS M ≥ 4,5 con reporte IGP", n(s["fraccion_usgs_m45_con_reporte_igp"])],
                    ["M IGP − M USGS (media ± desviación)", f"{n(dm.get('media'), 2)} ± {n(dm.get('desviacion'), 2)}"],
                    ["Distancia epicentral mediana (km)", n(s["distancia_epicentral_km_mediana"], 1)],
                    ["Mc del IGP (máxima curvatura)", n(s["mc_igp_maxima_curvatura"], 1)],
                ],
            ),
            s["nota"],
        ]
    partes += [
        "### Fuentes no usadas y por qué",
        "\n".join(f"- **{k}**: {v}" for k, v in r["fuentes_no_usadas"].items()),
    ]
    return "\n\n".join(partes)


def _conteo_veredictos(deps: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    salida: dict[str, dict[str, int]] = {"temperatura": {}, "lluvia": {}}
    for d in deps:
        if d.get("comparte_celda_con"):
            continue
        for var, clave in (("temperatura", "tendencia_temperatura"), ("lluvia", "tendencia_lluvia")):
            v = veredicto_backend(d[clave], 0.10)
            salida[var][v] = salida[var].get(v, 0) + 1
    return salida


def periodo_nacional(r: dict[str, Any]) -> str:
    """Años de las series anuales de los departamentos (de los datos, no escrito a mano)."""
    anios = [a for d in r["departamentos"] for a in (d.get("series_anuales") or {}).get("anios", [])]
    return f"{min(anios)}–{max(anios)}" if anios else "del periodo disponible"


def seccion_nacional(r: dict[str, Any]) -> str:
    deps = [d for d in r["departamentos"] if "error" not in d]
    filas = []
    for d in deps:
        tt, tl, sp = d["tendencia_temperatura"], d["tendencia_lluvia"], d["spi"]
        filas.append(
            [
                d["nombre"] + (f" (misma celda que {d['comparte_celda_con']})" if d.get("comparte_celda_con") else ""),
                n(d["temperatura_media_c"], 1),
                f"{n(tt['sen_por_decada'], 2)} [{ic(tt['ic90_por_decada'], 2)}] · {veredicto_backend(tt, 0.10)}",
                n(d["lluvia_anual_media_mm"], 0),
                f"{n(tl['sen_por_decada'], 1)} · {veredicto_backend(tl, 0.10)}",
                f"{n(sp['spi12'], 2)}" + ("" if sp["confiable"] else " (no interpretable: clima árido)"),
                d.get("deslizamientos_glc", 0),
            ]
        )
    s = r.get("sismicidad")
    partes = [
        f"## Escala nacional · {len(r['departamentos'])} departamentos",
        f"**Clima:** {r['fuente_clima']}. Tendencias {periodo_nacional(r)} con el Sello de Confianza del paquete; "
        "SPI con parámetros gamma del entrenamiento (último mes disponible). Con una sola familia de datos el Sello "
        "no puede dar 'robusta': la independencia queda pendiente.",
        tabla(
            [
                "Departamento",
                "T media (°C)",
                "Tendencia T (°C/década) [IC90] · Sello",
                "Lluvia anual (mm)",
                "Tendencia lluvia (mm/década) · Sello",
                "SPI-12",
                "Deslizamientos GLC",
            ],
            filas,
        ),
        "Veredictos (mismo vocabulario que la API: 'preliminar' = significativa con pruebas pendientes) por celda "
        "climática distinta: "
        + "; ".join(
            f"{var} " + ", ".join(f"{k} {c}" for k, c in sorted(conteo.items()))
            for var, conteo in _conteo_veredictos(deps).items()
        )
        + ".",
    ]
    if s:
        partes += [
            f"**Sismicidad nacional:** {s['fuente']}, caja {s['bbox']}, {s['desde']} a {s['hasta']}: "
            f"{n(s['eventos'], 0)} sismos M ≥ 4,5; Mc = {n(s['mc'], 1)}; b = {n(s['valor_b']['b'], 3)} "
            f"(IC90 {ic(s['valor_b']['ic90_bootstrap'], 3)}); tasa anual M ≥ Mc = {n(s['tasa_anual_m_mayor_mc'], 1)}.",
            tabla(
                ["Franja", "b", "n"], [[k, n(v.get("b"), 3), v.get("n")] for k, v in s["valor_b_por_franja"].items()]
            ),
            s["advertencia"],
        ]
    return "\n\n".join(partes)


def resumen(res: dict[str, dict[str, Any]]) -> str:
    filas = []

    def fila(nombre: str, zoo: dict[str, Any], abst: dict[str, Any], nota: str = "") -> None:
        m = zoo["modelos"][zoo["mejor_validacion"]]
        filas.append(
            [
                nombre,
                NOMBRES.get(zoo["mejor_validacion"], zoo["mejor_validacion"]),
                n(m["prueba"].get(m["metrica_principal"])),
                ic(m.get("ic90_prueba")),
                n((m.get("diebold_mariano_vs_climatologia") or {}).get("p")),
                lectura_habilidad(m) + nota,
                "abstención" if abst.get("abstencion") else "publica",
            ]
        )

    for clave, titulo in (
        ("lluvia_extrema", "Lluvia fuerte t+1 · POWER"),
        ("lluvia_extrema_chirps", "Lluvia fuerte t+1 · CHIRPS"),
    ):
        if clave in res:
            fila(titulo, res[clave]["zoo"], res[clave]["abstencion"])
    for clave, fuente in (("sequia", "POWER"), ("sequia_chirps", "CHIRPS")):
        for h, b in res.get(clave, {}).get("horizontes", {}).items():
            fila(f"SPI-3 a {h[1:]} mes(es) · {fuente}", b["zoo"], b["abstencion"])
    if "sismos" in res:
        fila(
            "Conteo sísmico mensual",
            res["sismos"]["pronostico_conteos"]["zoo"],
            res["sismos"]["pronostico_conteos"]["abstencion"],
            "; refleja agrupamiento de réplicas, no es pronóstico de sismos",
        )
    return tabla(
        ["Tarea", "Modelo elegido (validación)", "Habilidad en prueba", "IC90", "p DM", "Lectura", "Publicación"], filas
    )


def limitaciones(res: dict[str, dict[str, Any]]) -> str:
    items = []
    for clave, r in sorted(res.items()):
        for a in (
            [r.get("abstencion")]
            + [b.get("abstencion") for b in r.get("horizontes", {}).values()]
            + [(r.get("pronostico_conteos") or {}).get("abstencion")]
        ):
            if a:
                items += [f"- **{clave}**: {m}" for m in a.get("motivos", []) + a.get("advertencias", [])]
    zoos = [(k, r["zoo"]) for k, r in res.items() if "zoo" in r] + [
        (f"{k} {h}", b["zoo"]) for k, r in res.items() for h, b in r.get("horizontes", {}).items()
    ]
    for clave, zoo in sorted(zoos):
        m = zoo["modelos"][zoo["mejor_validacion"]]
        val, prueba = m.get("puntaje_validacion"), m["prueba"].get(m["metrica_principal"])
        if val is not None and prueba is not None and val - prueba > 0.05:
            items.append(
                f"- **{clave}**: la habilidad del modelo elegido cae de {n(val)} en validación a {n(prueba)} en prueba; "
                "se informa tal cual (la prueba no se usa para reajustar)."
            )
    s = res.get("sismos")
    if s:
        mc = s["completitud"]["mc_usada"]
        altas = {d: v for d, v in s["completitud"]["mc_por_decada"].items() if v > mc}
        if altas:
            items.append(
                f"- **sismos**: la Mc por década supera a la Mc usada ({n(mc, 1)}) en "
                + ", ".join(f"{d} ({n(v, 1)})" for d, v in altas.items())
                + ": el conteo de esos años está incompleto y la tasa aparente crece con el tiempo."
            )
        items.append(
            "- **sismos**: el conteo mensual incluye réplicas; una ganancia frente a Poisson refleja agrupamiento "
            "(réplicas), no capacidad de pronosticar sismos."
        )
    items.append(
        "- Los resultados son experimentales y describen la escala de cada producto (celdas de 0,05° a 0,5°), no puntos."
    )
    items.append("- Ningún resultado es una alerta oficial: las emiten SENAMHI, IGP, INGEMMET e INDECI.")
    return "\n".join(dict.fromkeys(items))


REGIMEN = {"validacion_del_diseno": "validación del diseño", "fuera_de_muestra": "fuera de muestra"}


def seccion_historial(r: dict[str, Any]) -> str:
    m = r["metodo"]
    partes = [
        "## Historial de métricas · origen móvil y dinámica en ventanas",
        f"Para cada año Y desde {m['anio_inicial']}: entrenamiento con datos ≤ Y−2, validación en Y−1 y prueba en Y, "
        "con el **diseño congelado** del experimento principal (variables, ventana y red). Los años hasta "
        f"{m['frontera_diseno']} se usaron para elegir ese diseño (lectura optimista); los posteriores son "
        f"**fuera de muestra**. Semillas por corte: {', '.join(str(s) for s in m['semillas'])}. Por año la muestra "
        "es pequeña; la lectura principal es la habilidad agregada por régimen.",
    ]
    for nombre, t in r["pronostico"].items():
        if "omitido" in t:
            partes.append(f"### {nombre}\n\nNo evaluado: {t['omitido']}.")
            continue
        red = t["diseno"]["red"]
        partes.append(
            f"### {t['descripcion']}\n\nMétrica: {METRICA.get(t['metrica_principal'], t['metrica_principal'])}. "
            f"Red congelada: {NOMBRES.get(red, red)}, ventana {t['diseno']['ventana']}."
        )
        filas = []
        for a in t["anios"]:
            if a.get("omitido"):
                filas.append([a["anio"], REGIMEN[a["regimen"]], "—", "—", "—", f"omitido: {a['omitido']}"])
                continue
            mm = a["modelos"]
            elegido = a.get("elegido_en_validacion")
            # Clásico de referencia elegido por VALIDACIÓN del corte (nunca por la cifra de prueba)
            clasicos = [k for k, v in mm.items() if v["familia"] == "clasico"]
            clasico = max(clasicos, key=lambda k: mm[k]["validacion"] if mm[k]["validacion"] is not None else -1e9)
            filas.append(
                [
                    a["anio"],
                    REGIMEN[a["regimen"]],
                    n(a["n"]["prueba"]),
                    f"{NOMBRES.get(elegido, elegido)} {n(mm.get(elegido, {}).get('prueba'))}" if elegido else "—",
                    f"{n(mm[red]['prueba'])} [{ic(mm[red]['ic90'])}]",
                    f"{NOMBRES.get(clasico, clasico)} {n(mm[clasico]['prueba'])}",
                    n(mm.get("ref_persistencia", {}).get("prueba")),
                ]
            )
        partes.append(
            tabla(
                [
                    "Año",
                    "Régimen",
                    "n",
                    "Elegido en validación",
                    f"{NOMBRES.get(red, red)} [IC90]",
                    "Clásico elegido en validación",
                    "Persistencia",
                ],
                filas,
            )
        )
        filas = []
        principal_agr = t.get("lectura_principal")
        familias = {k: v["familia"] for a in t["anios"] for k, v in (a.get("modelos") or {}).items()}
        orden_familia = {"referencia": 4, "clasico": 2, "red_neuronal": 1, "ensamble": 3}

        # Orden fijo, independiente de las cifras de prueba: primero la lectura principal y la red congelada
        primeros = [k for k in (principal_agr, red) if k]
        for regimen in ("fuera_de_muestra", "validacion_del_diseno"):
            claves = t.get("agregado", {}).get(regimen, {})
            resto = sorted(
                (k for k in claves if k not in primeros), key=lambda k: (orden_familia.get(familias.get(k, ""), 5), k)
            )
            for modelo in [*(k for k in primeros if k in claves), *resto]:
                v = t["agregado"][regimen][modelo]
                filas.append(
                    [
                        REGIMEN[regimen],
                        ("**" + NOMBRES.get(modelo, modelo) + "**")
                        if modelo == principal_agr
                        else NOMBRES.get(modelo, modelo),
                        n(v["valor"]),
                        ic(v["ic90"]),
                        n(v["p_diebold_mariano"]),
                        lectura_habilidad(
                            {"ic90_prueba": v["ic90"], "diebold_mariano_vs_climatologia": {"p": v["p_diebold_mariano"]}}
                        ),
                        v.get("bloque_bootstrap", "—"),
                        v["anios"],
                    ]
                )
        if filas:
            partes.append(
                "Agregado por régimen (predicciones concatenadas). En **negrita**, la lectura principal: el modelo "
                "que eligió la validación de cada año (el procedimiento completo, sin mirar la prueba). Las demás "
                "filas son comparaciones: elegir entre ellas la de mejor cifra en la prueba sería sesgo de selección."
            )
            partes.append(tabla(["Régimen", "Modelo", "Habilidad", "IC90", "p DM", "Lectura", "Bloque", "Años"], filas))
    if r.get("caos"):
        partes.append("### Dinámica en ventanas deslizantes")
        filas = []
        for nombre, c in r["caos"].items():
            ok = [f for f in c["ventanas"] if not f.get("omitido")]
            if not ok:
                continue
            pe = [f["entropia_permutacion"] for f in ok if f.get("entropia_permutacion") is not None]
            ordenes = sorted({f["orden_permutacion"] for f in ok if f.get("orden_permutacion") is not None})
            nl = sum(1 for f in ok if f.get("p_no_linealidad") is not None and f["p_no_linealidad"] <= 0.05)
            holm = sum(1 for f in ok if f.get("p_holm") is not None and f["p_holm"] <= 0.05)
            bh = sum(1 for f in ok if f.get("q_bh") is not None and f["q_bh"] <= 0.05)
            filas.append(
                [
                    nombre.replace("_", " "),
                    f"{c['ventana_anios']} años",
                    f"{ok[0]['fin']}–{ok[-1]['fin']}",
                    len(ok),
                    (f"{n(min(pe))} a {n(max(pe))}" if pe else "—")
                    + (f" (orden {', '.join(map(str, ordenes))})" if ordenes else ""),
                    f"{nl} de {len(ok)}",
                    f"{holm} · {bh}",
                ]
            )
        partes.append(
            tabla(
                [
                    "Serie",
                    "Ventana",
                    "Fin de ventana",
                    "Ventanas",
                    "Entropía de permutación",
                    "p ≤ 0,05 sin corregir",
                    "Tras corregir (Holm · BH)",
                ],
                filas,
            )
        )
        partes.append(
            "Cada p de ventana se lee por separado y las ventanas se solapan: el conteo sin corregir es "
            "descriptivo. Con 39 sustitutos el p mínimo posible es 0,025, así que con decenas de ventanas "
            "ninguna puede superar Holm; Benjamini-Hochberg solo las retiene si muchas ventanas llegan al mínimo."
        )
        if r.get("series_omitidas"):
            partes.append(
                "Series sin crudos locales: " + "; ".join(f"{k} ({v})" for k, v in r["series_omitidas"].items()) + "."
            )
    return "\n\n".join(partes)


def generar(resultados: Path) -> str:
    indice = json.loads((resultados / "indice.json").read_text())
    res = {p.stem: json.loads(p.read_text()) for p in sorted(resultados.glob("*.json")) if p.stem != "indice"}
    proc = next(iter(res.values()))["procedencia"]
    partes = [
        "# Resultados de los experimentos",
        "> Generado automáticamente por `tv informe` desde `resultados/*.json`. No editar a mano: cada cifra "
        "sale de esos archivos, que guardan su procedencia completa.",
        tabla(
            ["Campo", "Valor"],
            [
                ["Generado (UTC)", indice["generado_utc"]],
                ["Commit del código", f"`{indice['commit']}`"],
                ["Modo", proc["modo"]],
                ["Configuración (SHA-256)", f"`{proc['config_sha256'][:16]}…`"],
                ["Versiones", ", ".join(f"{k} {v}" for k, v in proc["versiones"].items())],
                ["Crudos con hash", n(sum(len(v) for v in proc["crudos"].values()))],
                [
                    "Tiempo por experimento (s)",
                    ", ".join(f"{k} {n(float(v), 0)}" for k, v in indice["tiempos_segundos"].items()),
                ],
            ],
        ),
        "**Cómo leer.** La partición es temporal y está congelada (entrenamiento 1981–2015, validación 2016–2020, "
        "prueba 2021–2026). Todo se elige con validación; la prueba se usa una vez. Una habilidad está **confirmada** "
        "solo si su IC90 por bootstrap de bloques queda por encima de 0 **y** la prueba de Diebold-Mariano frente a la "
        f"climatología da p < {P_DM_TEXTO}; si solo se cumple una de las dos, es un **indicio**. "
        "Las reglas de método y los hiperparámetros están en `config/modelos.yaml`; su auditoría, en "
        "`docs/auditoria-metricas.md`.",
        "## Resumen",
        resumen(res),
    ]
    for clave, f in (
        ("lluvia_extrema", lambda r: seccion_lluvia(r, "Lluvia fuerte a 1 día · NASA POWER")),
        ("lluvia_extrema_chirps", lambda r: seccion_lluvia(r, "Lluvia fuerte a 1 día · CHIRPS")),
        ("sequia", lambda r: seccion_sequia(r, "Sequía (SPI-3) · NASA POWER")),
        ("sequia_chirps", lambda r: seccion_sequia(r, "Sequía (SPI-3) · CHIRPS")),
        ("sismos", seccion_sismos),
        ("volcanes", seccion_volcanes),
        ("deslizamientos", seccion_deslizamientos),
        ("caos", seccion_caos),
        ("fuentes", seccion_fuentes),
        ("nacional", seccion_nacional),
        ("historial", seccion_historial),
    ):
        if clave in res:
            partes.append(f(res[clave]))
    partes += ["## Limitaciones", limitaciones(res)]
    return "\n\n".join(partes) + "\n"
