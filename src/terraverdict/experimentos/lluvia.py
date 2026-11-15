"""Experimento: probabilidad de día de lluvia fuerte en la cabecera del Chili (t+1).

Objetivo: P(t+1) ≥ percentil 90 de los días de dic–mar del entrenamiento (celda POWER de la
cabecera). Se usa la cabecera porque ahí cae la lluvia que alimenta el Chili y su turbidez; el
control de calidad muestra que la celda de la ciudad no representa la lluvia local de la
estación (ver `calidad` en el resultado).

`fuente="chirps"` repite el experimento con la lluvia de CHIRPS v2.0 (caja de 0,1° en la cabecera)
como objetivo e historia; las demás variables siguen siendo de POWER. Sirve para saber si la
habilidad depende del producto de lluvia.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..caos.embedding import autocorrelacion, retardo_optimo
from ..evaluacion import metricas as M
from ..evaluacion.incertidumbre import decidir_abstencion, deriva
from ..seleccion.variables import mrmr
from ..senales.procesamiento import ventana_adaptativa
from . import datos_reales as D
from .comun import Particion, Tarea, construir, evaluar_zoo, explicar, limpiar, parametros, serie_prueba

MESES_HUMEDOS = [11, 12, 1, 2, 3, 4]
RAIZ = Path(__file__).resolve().parents[3]


# Columna del experimento → id de la variable en config/fenomenos.yaml (lluvia_extrema.variables).
# El prior físico (`relevancia`) se lee del catálogo con este mapa: no se escribe en el código.
VARIABLES_CATALOGO = {
    "lluvia_log": "lluvia_diaria",
    "humedad_especifica": "humedad_especifica",
    "humedad_relativa": "humedad_relativa",
    "temperatura": "temperatura_aire_2m",
    "amplitud_termica": "amplitud_termica",
    "presion": "presion_superficie",
    "viento": "viento_2m",
    "radiacion": "radiacion_onda_corta",
    "oni": "indice_oni",
}


def prior_catalogo(cfg: dict[str, Any], columnas: list[str]) -> dict[str, str]:
    """Relevancia física (alta, media o baja) de cada columna, tomada del catálogo de fenómenos."""
    catalogo = {v["id"]: v["relevancia"] for v in cfg["fenomenos"]["lluvia_extrema"]["variables"]}
    faltan = [c for c in columnas if VARIABLES_CATALOGO.get(c) not in catalogo]
    if faltan:
        raise KeyError(f"Variables sin relevancia en config/fenomenos.yaml: {faltan}")
    return {c: catalogo[VARIABLES_CATALOGO[c]] for c in columnas}


FUENTES_LLUVIA = {
    "power": "NASA POWER (MERRA-2) PRECTOTCORR, celda de la cabecera",
    "chirps": "CHIRPS v2.0 (ClimateSERV), promedio de una caja de 0,1° en la cabecera",
}


def preparar(raw: Path, fuente: str = "power") -> tuple[pd.DataFrame, pd.Series, dict[str, Any]]:
    df, qc = D.power_diario(raw, "cabecera")
    df = df[df.index >= "1984-01-01"]  # radiación disponible desde 1984
    if fuente == "chirps":
        lluvia = D.chirps_diario(raw, "cabecera_local").reindex(df.index)
        qc = {
            **qc,
            "lluvia_chirps": {
                "dias_validos": int(lluvia.notna().sum()),
                "hasta": str(lluvia.dropna().index[-1].date()),
            },
        }
    else:
        lluvia = df["PRECTOTCORR"]
    oni = D.oni_disponible_diario(D.oni_mensual(raw), df.index)
    doy = 2 * np.pi * df.index.dayofyear / 365.25
    X = pd.DataFrame(
        {
            "lluvia_log": np.log1p(lluvia),
            "humedad_especifica": df["QV2M"],
            "humedad_relativa": df["RH2M"],
            "temperatura": df["T2M"],
            "amplitud_termica": df["T2M_MAX"] - df["T2M_MIN"],
            "presion": df["PS"],
            "viento": df["WS2M"],
            "radiacion": df["ALLSKY_SFC_SW_DWN"],
            "oni": oni,
            "estacion_seno": np.sin(doy),
            "estacion_coseno": np.cos(doy),
        },
        index=df.index,
    )
    return X, lluvia, qc


def tarea(cfg: dict[str, Any], raw: Path, fuente: str = "power") -> tuple[Tarea, pd.Series, dict[str, Any], float]:
    """Lluvia fuerte al día siguiente. El umbral (p90 de dic–mar) se fija con el entrenamiento de la
    partición congelada; climatología y persistencia se ajustan con los datos ≤ `hasta`."""
    fin_entrenamiento = cfg["particion_temporal"]["entrenamiento"][1]
    X, lluvia, qc = preparar(raw, fuente)
    base = lluvia[(lluvia.index <= fin_entrenamiento) & lluvia.index.month.isin([12, 1, 2, 3])]
    umbral = float(base.quantile(0.90))
    evento = (lluvia >= umbral).astype(float)
    objetivo = evento.shift(-1)  # emitido en t, verifica t+1
    fechas = X.index[pd.DatetimeIndex(X.index + pd.Timedelta(days=1)).month.isin(MESES_HUMEDOS)]
    P = parametros(cfg)

    def referencias(hasta: str):
        # Climatología por día del año (±15 días) y persistencia de Markov, ajustadas con datos ≤ hasta
        ent = evento.index <= pd.Timestamp(hasta)
        doy = evento.index.dayofyear
        clim_doy = {d: float(evento[ent & (np.abs(((doy - d + 182) % 365) - 182) <= 15)].mean()) for d in range(1, 367)}
        hoy, manana = evento[ent].to_numpy()[:-1], evento[ent].to_numpy()[1:]
        p1, p0 = float(manana[hoy == 1].mean()), float(manana[hoy == 0].mean())

        def construir_refs(d) -> dict[str, dict[str, np.ndarray]]:
            salida = {}
            for parte in ("validacion", "prueba"):
                f = d.fechas[parte]
                salida[parte] = {
                    "climatologia": np.array([clim_doy[(x + pd.Timedelta(days=1)).dayofyear] for x in f]),
                    "persistencia": np.where(evento.reindex(f).to_numpy() == 1, p1, p0),
                }
            return salida

        return construir_refs

    t = Tarea(
        nombre=f"lluvia_extrema_{fuente}",
        tipo="clasificacion",
        X=X,
        objetivo=objetivo,
        horizonte=pd.Timedelta(days=1),
        referencias=referencias,
        fechas=fechas,
        epocas=int(P["redes"]["epocas"]["lluvia"]),
        bloque_bootstrap=int(P["evaluacion"]["bloque_bootstrap"]["lluvia"]),
        horizonte_pasos=1,
    )
    return t, lluvia, qc, umbral


def columnas_diseno(resultado: dict[str, Any]) -> list[str]:
    """Columnas con las que se entrenó el modelo publicado (selección mRMR + estación del año)."""
    return [*resultado["seleccion_variables"]["seleccionadas"], "estacion_seno", "estacion_coseno"]


def ejecutar(
    cfg: dict[str, Any],
    raw: Path,
    registro=print,
    redes: list[str] | None = None,
    semillas: tuple[int, ...] | None = None,
    fuente: str = "power",
) -> dict[str, Any]:
    P = parametros(cfg)
    semillas = tuple(P["redes"]["semillas"]["lluvia"]) if semillas is None else semillas
    pt = cfg["particion_temporal"]
    particion = Particion(tuple(pt["entrenamiento"]), tuple(pt["validacion"]), tuple(pt["prueba"]))
    t, _, qc, umbral = tarea(cfg, raw, fuente)
    X, objetivo, fechas = t.X, t.objetivo, t.fechas
    ciudad, _ = D.power_diario(raw, "ciudad")
    calidad = {
        "cabecera": qc,
        "contraste_ciudad_vs_estacion": D.comparar_con_estacion(ciudad, raw, cfg["descarga"]["ghcn_estacion"]),
    }
    referencias = t.referencias(particion.entrenamiento[1])

    # Selección de variables (solo entrenamiento): mRMR + prior físico del catálogo
    candidatas = [c for c in X.columns if not c.startswith("estacion")]
    prior = prior_catalogo(cfg, candidatas)
    ps = P["seleccion_variables"]
    tr = (X.index <= particion.entrenamiento[1]) & X.index.isin(fechas) & objetivo.notna()

    def seleccionar(pesos: dict[str, float]) -> dict[str, Any]:
        return mrmr(
            X.loc[tr, candidatas].to_numpy(),
            objetivo[tr].to_numpy().astype(int),
            candidatas,
            prior,
            clasificacion=True,
            siempre=["lluvia_log"],
            maximo=int(ps["maximo_lluvia"]),
            permutaciones=int(ps["permutaciones_nulo"]),
            pesos=pesos,
        )

    seleccion = seleccionar(ps["pesos_prior"])
    # Ablación del prior: la misma selección con pesos iguales. Mide si el prior físico cambia algo.
    sin_prior = seleccionar({k: 1.0 for k in ps["pesos_prior"]})
    seleccion["prior"] = prior
    seleccion["ablacion_prior"] = {
        "pesos_iguales": sin_prior["seleccionadas"],
        "cambia_la_seleccion": sin_prior["seleccionadas"] != seleccion["seleccionadas"],
    }
    columnas = seleccion["seleccionadas"] + ["estacion_seno", "estacion_coseno"]
    registro(f"lluvia: umbral {umbral:.2f} mm/d; variables {columnas}")

    # Ventana adaptativa: decorrelación y embedding de Takens sugieren; la validación decide
    serie = X["lluvia_log"].to_numpy()
    acf = autocorrelacion(serie - pd.Series(serie).rolling(31, center=True, min_periods=1).mean().to_numpy(), 60)
    l_acf = int(np.argmax(np.abs(acf[1:]) < 1 / np.e)) + 1
    tau = retardo_optimo(serie)["tau"]

    def evaluar_L(L: int) -> float:
        from sklearn.linear_model import LogisticRegression

        d = construir(X[columnas], objetivo, L, particion, fechas, pd.Timedelta(days=1))
        m = LogisticRegression(**P["clasicos"]["logistica"]).fit(
            d.X["entrenamiento"].reshape(len(d.X["entrenamiento"]), -1), d.y["entrenamiento"]
        )
        p = m.predict_proba(d.X["validacion"].reshape(len(d.X["validacion"]), -1))[:, 1]
        return M.habilidad_brier(d.y["validacion"], p, referencias(d)["validacion"]["climatologia"])

    ventana = ventana_adaptativa(
        list(P["ventanas"]["lluvia_dias"]), evaluar_L, {"decorrelacion_acf": l_acf, "embedding_takens": 4 * tau}
    )
    L = ventana["elegida"]
    registro(f"lluvia: ventana elegida {L} días")

    d = construir(X[columnas], objetivo, L, particion, fechas, pd.Timedelta(days=1))
    refs = referencias(d)
    zoo = evaluar_zoo(
        d,
        "clasificacion",
        refs,
        redes=redes,
        semillas=semillas,
        epocas=t.epocas,
        bloque_bootstrap=t.bloque_bootstrap,
        horizonte_pasos=t.horizonte_pasos,
        cfg=cfg,
        registro=registro,
    )
    mejor = zoo["mejor_validacion"]

    # Ablaciones: modelos clásicos + la mejor red (una semilla), misma ventana
    redes_zoo = [k for k, v in zoo["modelos"].items() if v["familia"] == "red_neuronal"]
    mejor_red = max(redes_zoo, key=lambda k: zoo["modelos"][k]["puntaje_validacion"]) if redes_zoo else None
    ablaciones = {}
    for nombre, cols in {
        "seleccion_mrmr": columnas,
        "solo_historia_lluvia": ["lluvia_log", "estacion_seno", "estacion_coseno"],
        "sin_oni": [c for c in [*candidatas, "estacion_seno", "estacion_coseno"] if c != "oni"],
        "todas_las_variables": [*candidatas, "estacion_seno", "estacion_coseno"],
    }.items():
        da = construir(X[cols], objetivo, L, particion, fechas, pd.Timedelta(days=1))
        za = evaluar_zoo(
            da,
            "clasificacion",
            referencias(da),
            redes=[mejor_red] if mejor_red else [],
            semillas=(0,),
            epocas=t.epocas,
            bloque_bootstrap=t.bloque_bootstrap,
            horizonte_pasos=t.horizonte_pasos,
            cfg=cfg,
            registro=lambda _: None,
        )
        ablaciones[nombre] = {
            "variables": cols,
            "modelos": {
                k: {"puntaje_validacion": v["puntaje_validacion"], "bss_prueba": v["prueba"]["bss_climatologia"]}
                for k, v in za["modelos"].items()
                if v["familia"] in ("clasico", "red_neuronal")
            },
        }

    # Eventos documentados en el periodo de prueba (datos/eventos/arequipa.json), por mes
    import json

    eventos_doc = json.loads((RAIZ / "datos" / "eventos" / "arequipa.json").read_text())["eventos"]
    p_mejor = zoo["_predicciones"][mejor]["prueba"]
    fechas_obj = d.fechas["prueba"] + pd.Timedelta(days=1)
    eventos = []
    for e in eventos_doc:
        if e["categoria"] not in ("turbidez", "escasez") and "huaico" not in e["id"]:
            continue
        mes = pd.Timestamp(e["fecha"]).to_period("M")
        sel = fechas_obj.to_period("M") == mes
        if not sel.any():
            continue
        fuertes = d.y["prueba"][sel] == 1
        eventos.append(
            {
                "evento": e["id"],
                "titulo": e["titulo"],
                "mes": str(mes),
                "dias_evaluados": int(sel.sum()),
                "dias_lluvia_fuerte_observados": int(fuertes.sum()),
                "probabilidad_media_modelo_en_dias_fuertes": float(p_mejor[sel][fuertes].mean())
                if fuertes.any()
                else None,
                "probabilidad_media_climatologia_en_dias_fuertes": float(
                    refs["prueba"]["climatologia"][sel][fuertes].mean()
                )
                if fuertes.any()
                else None,
                "probabilidad_media_modelo_resto": float(p_mejor[sel][~fuertes].mean()) if (~fuertes).any() else None,
            }
        )

    deriva_entradas = deriva(
        {c: X.loc[X.index <= particion.entrenamiento[1], c].dropna().to_numpy() for c in columnas},
        {c: X.loc[X.index >= particion.prueba[0], c].dropna().to_numpy() for c in columnas},
    )
    abst = decidir_abstencion(
        habilidad_validacion=zoo["modelos"][mejor]["puntaje_validacion"],
        minimo=cfg["abstencion"]["skill_minimo_validacion"],
        deriva_detectada=any(v["deriva"] for v in deriva_entradas.values()),
    )
    return {
        "fenomeno": "lluvia_extrema",
        "tarea": "clasificacion",
        "fuente_lluvia": FUENTES_LLUVIA[fuente],
        "definicion": {
            "objetivo": f"lluvia diaria en la cabecera ≥ {umbral:.2f} mm (p90 de dic–mar, entrenamiento; {fuente.upper()})",
            "horizonte_dias": 1,
            "meses_evaluados": MESES_HUMEDOS,
            "umbral_mm": umbral,
            "tasa_base_entrenamiento": float(d.y["entrenamiento"].mean()),
            "n": {k: len(v) for k, v in d.y.items()},
            "eventos": {k: int(v.sum()) for k, v in d.y.items()},
        },
        "calidad": calidad,
        "seleccion_variables": seleccion,
        "ventana": ventana,
        "zoo": limpiar(zoo),
        "ablaciones": ablaciones,
        "explicabilidad": explicar(d, "clasificacion", refs["validacion"]["climatologia"]),
        "eventos_documentados": eventos,
        "deriva": deriva_entradas,
        "abstencion": abst,
        "confiabilidad_mejor": M.confiabilidad(d.y["prueba"], p_mejor),
        "serie_prueba": serie_prueba(d, zoo, mejor, refs["prueba"]["climatologia"]),
    }
