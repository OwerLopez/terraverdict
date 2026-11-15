"""Contraste entre fuentes independientes de la misma magnitud física.

Antes de creer un resultado hay que saber cuánto se parecen las fuentes que lo sustentan:
- Lluvia: NASA POWER (MERRA-2), CHIRPS v2.0 (satélite + estaciones), IMERG Final V07 (satélite)
  y la estación GHCN de Arequipa (aeropuerto). Se comparan días comunes, meses completos,
  extremos, frecuencia de días húmedos y la tendencia de la lluvia de dic–mar de cada fuente.
- Temperatura: POWER T2M frente a la estación GHCN (aire a 2 m) y a MODIS LST (superficie, MOD11A2).
  LST no es temperatura del aire: se comparan ANOMALÍAS y tendencias, no niveles.
- Sismos: USGS ComCat frente a los sismos reportados por el IGP (emparejados por tiempo y lugar).

Solo describe concordancia; no elige "la verdadera". Las tendencias usan Theil-Sen y el p
conservador de Mann-Kendall del paquete de tendencias.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..ingest import igp
from ..trends.mk import mk_conservador
from ..trends.sen import sen_por_decada
from . import datos_reales as D
from .sismos import catalogo, magnitud_completitud, valor_b
from .volcanes import _distancia_km


def comparar_lluvia(a: pd.Series, b: pd.Series, nombre_a: str, nombre_b: str) -> dict[str, Any] | None:
    comun = pd.concat([a, b], axis=1, keys=["a", "b"]).dropna()
    if len(comun) < 365:
        return None
    humedos = (comun["a"] >= 1) | (comun["b"] >= 1)
    dias_mes = comun["a"].resample("MS").count()
    mensual = comun.resample("MS").sum()[dias_mes >= 25]
    return {
        "a": nombre_a,
        "b": nombre_b,
        "dias_comunes": len(comun),
        "desde": str(comun.index[0].date()),
        "hasta": str(comun.index[-1].date()),
        "r_diario": float(comun["a"].corr(comun["b"])),
        "r_diario_dias_humedos": float(comun["a"][humedos].corr(comun["b"][humedos])),
        "r_spearman_diario": float(comun["a"].corr(comun["b"], method="spearman")),
        "meses_completos": len(mensual),
        "r_mensual": float(mensual["a"].corr(mensual["b"])) if len(mensual) > 12 else None,
        "razon_totales_a_b": float(comun["a"].sum() / comun["b"].sum()),
        "media_anual_mm": {nombre_a: float(comun["a"].mean() * 365.25), nombre_b: float(comun["b"].mean() * 365.25)},
        "p99_diario_mm": {nombre_a: float(comun["a"].quantile(0.99)), nombre_b: float(comun["b"].quantile(0.99))},
        "fraccion_dias_humedos_1mm": {
            nombre_a: float((comun["a"] >= 1).mean()),
            nombre_b: float((comun["b"] >= 1).mean()),
        },
    }


def tendencia_anual(serie: pd.Series, nombre: str, desde: int, hasta: int, unidad: str) -> dict[str, Any] | None:
    s = serie[(serie.index >= desde) & (serie.index <= hasta)].dropna()
    if len(s) < 15:
        return None
    anios, x = s.index.to_numpy(float), s.to_numpy(float)
    sen, mk = sen_por_decada(anios, x), mk_conservador(x)
    return {
        "fuente": nombre,
        "desde": int(anios[0]),
        "hasta": int(anios[-1]),
        "n_anios": len(s),
        "media": float(x.mean()),
        "unidad": unidad,
        "sen_por_decada": sen["sen_por_decada"],
        "ic90_por_decada": sen["ic_por_decada"],
        "p_mk_conservador": mk["p_conservador"],
    }


def _dic_mar(s: pd.Series) -> pd.Series:
    """Total de dic–mar asignado al año de enero; solo temporadas con ≥ 95 % de días."""
    anio = s.index.year + (s.index.month == 12)
    sel = s.index.month.isin([12, 1, 2, 3])
    g = s[sel].groupby(anio[sel])
    return g.sum()[g.count() >= 0.95 * 121]


def _media_anual(s: pd.Series, minimo: float) -> pd.Series:
    g = s.groupby(s.index.year)
    return g.mean()[g.count() >= minimo]


def _lluvia(cfg: dict[str, Any], raw: Path) -> dict[str, Any]:
    cab, ciu = cfg["puntos"]["cabecera"], cfg["puntos"]["ciudad"]
    p_cab = D.power_diario(raw, "cabecera")[0]["PRECTOTCORR"]
    p_ciu = D.power_diario(raw, "ciudad")[0]["PRECTOTCORR"]
    fuentes_cab = {
        "power_cabecera": p_cab,
        "chirps_cabecera_celda_power": D.chirps_diario(raw, "cabecera_celda_power"),
        "chirps_cabecera_local": D.chirps_diario(raw, "cabecera_local"),
    }
    fuentes_ciu = {
        "power_ciudad": p_ciu,
        "chirps_ciudad_celda_power": D.chirps_diario(raw, "ciudad_celda_power"),
        "chirps_ciudad_local": D.chirps_diario(raw, "ciudad_local"),
    }
    imerg = {
        "cabecera": D.imerg_diario(raw, cab["lon"], cab["lat"]),
        "ciudad": D.imerg_diario(raw, ciu["lon"], ciu["lat"]),
    }
    if imerg["cabecera"] is not None:
        fuentes_cab["imerg_cabecera"] = imerg["cabecera"]
    if imerg["ciudad"] is not None:
        fuentes_ciu["imerg_ciudad"] = imerg["ciudad"]
    estacion = D.ghcn_diario(raw, cfg["descarga"]["ghcn_estacion"])["PRCP"].dropna()

    pares_cab = []
    nombres = list(fuentes_cab)
    for i, a in enumerate(nombres):
        for b in nombres[i + 1 :]:
            c = comparar_lluvia(fuentes_cab[a], fuentes_cab[b], a, b)
            if c:
                pares_cab.append(c)
    frente_estacion = [
        c for n, s in fuentes_ciu.items() if (c := comparar_lluvia(s, estacion, n, "estacion_ghcn")) is not None
    ]
    ranking = sorted(frente_estacion, key=lambda c: -(c["r_mensual"] or -1))
    tendencias = [
        t
        for n, s in {**fuentes_cab, "estacion_ghcn_ciudad": estacion}.items()
        if (t := tendencia_anual(_dic_mar(s), n, 1982, 2026, "mm por temporada dic–mar")) is not None
    ]
    signos = {t["fuente"]: int(np.sign(t["sen_por_decada"])) for t in tendencias}
    return {
        "cabecera_entre_fuentes": pares_cab,
        "ciudad_frente_a_estacion": ranking,
        "mejor_concordancia_mensual_con_estacion": ranking[0]["a"] if ranking else None,
        "tendencia_dic_mar": tendencias,
        "signos_tendencia_dic_mar": signos,
        "imerg_disponible": imerg["cabecera"] is not None,
        "nota_imerg": None
        if imerg["cabecera"] is not None
        else "IMERG no se descargó: GES DISC exige que la cuenta Earthdata acepte su licencia (ver registro_descarga.json).",
    }


def _temperatura(cfg: dict[str, Any], raw: Path) -> dict[str, Any]:
    ciudad, _ = D.power_diario(raw, "ciudad")
    cabecera, _ = D.power_diario(raw, "cabecera")
    est = D.ghcn_diario(raw, cfg["descarga"]["ghcn_estacion"])
    salida: dict[str, Any] = {"estacion_frente_a_power": {}, "modis_frente_a_power": {}, "tendencias_media_anual": []}

    def anomalia(s: pd.Series) -> pd.Series:
        return s - s.groupby(s.index.dayofyear).transform("mean")

    for e, p in (("TMAX", "T2M_MAX"), ("TMIN", "T2M_MIN")):
        comun = pd.concat([est[e], ciudad[p]], axis=1, keys=["e", "p"]).dropna()
        if len(comun) > 365:
            salida["estacion_frente_a_power"][e] = {
                "dias_comunes": len(comun),
                "desde": str(comun.index[0].date()),
                "hasta": str(comun.index[-1].date()),
                "sesgo_power_menos_estacion_C": float((comun["p"] - comun["e"]).mean()),
                "r_anomalias_diarias": float(anomalia(comun["e"]).corr(anomalia(comun["p"]))),
            }
    for nombre, power_df in (("ciudad", ciudad), ("cabecera", cabecera)):
        lst = D.modis_lst(raw, nombre)
        if lst is None:
            continue
        bloque = {}
        for banda, var in (("LST_Day_1km", "T2M_MAX"), ("LST_Night_1km", "T2M_MIN")):
            s = lst[banda].dropna()
            # media de POWER en la misma ventana de 8 días que el compuesto MODIS
            p8 = pd.Series([power_df[var].loc[t : t + pd.Timedelta(days=7)].mean() for t in s.index], index=s.index)
            comun = pd.concat([s, p8], axis=1, keys=["m", "p"]).dropna()
            a_m = comun["m"] - comun["m"].groupby(comun.index.dayofyear).transform("mean")
            a_p = comun["p"] - comun["p"].groupby(comun.index.dayofyear).transform("mean")
            bloque[banda] = {
                "frente_a": var,
                "compuestos": len(comun),
                "fraccion_compuestos_validos": float(len(s) / len(lst)),
                "media_lst_C": float(comun["m"].mean()),
                "media_power_C": float(comun["p"].mean()),
                "r_anomalias": float(a_m.corr(a_p)),
            }
        salida["modis_frente_a_power"][nombre] = bloque
        media_lst = (lst["LST_Day_1km"] + lst["LST_Night_1km"]) / 2
        t_lst = tendencia_anual(_media_anual(media_lst.dropna(), 30), f"modis_lst_{nombre}", 2001, 2025, "°C")
        t_pow = tendencia_anual(_media_anual(power_df["T2M"], 360), f"power_t2m_{nombre}", 2001, 2025, "°C")
        salida["tendencias_media_anual"] += [t for t in (t_lst, t_pow) if t]
    t_est = tendencia_anual(
        _media_anual(((est["TMAX"] + est["TMIN"]) / 2).dropna(), 300), "estacion_ghcn_ciudad", 1981, 2025, "°C"
    )
    t_pow = tendencia_anual(_media_anual(ciudad["T2M"], 360), "power_t2m_ciudad", 1981, 2025, "°C")
    salida["tendencias_media_anual"] += [t for t in (t_est, t_pow) if t]
    salida["nota"] = (
        "MODIS LST mide la superficie, no el aire: los niveles difieren por construcción. "
        "Se comparan anomalías y tendencias en el mismo periodo (2001–2025)."
    )
    return salida


def _sismos(cfg: dict[str, Any], raw: Path) -> dict[str, Any] | None:
    if not (raw / "igp").exists():
        return None
    ciudad, radio = cfg["puntos"]["ciudad"], cfg["descarga"]["sismos"]["radio_km"]
    ig = pd.DataFrame(igp.cargar(raw / "igp"))
    ig["tiempo"] = pd.to_datetime(ig["tiempo"])
    ig = ig[_distancia_km(ciudad["lat"], ciudad["lon"], ig["lat"].to_numpy(), ig["lon"].to_numpy()) <= radio]
    us = catalogo(raw)
    us = us[us["tiempo"] >= ig["tiempo"].min()]
    t_us = us["tiempo"].to_numpy("datetime64[s]").astype(np.int64)
    pares = []
    for e in ig.itertuples():
        dt = np.abs(t_us - np.datetime64(e.tiempo, "s").astype(np.int64))
        cand = np.flatnonzero(dt <= 60)
        if len(cand) == 0:
            continue
        d = _distancia_km(e.lat, e.lon, us["lat"].to_numpy()[cand], us["lon"].to_numpy()[cand])
        k = int(np.argmin(d))
        if d[k] <= 100:
            u = us.iloc[cand[k]]
            pares.append(
                {
                    "dm": e.magnitud - u["magnitud"],
                    "dz": e.profundidad_km - u["profundidad_km"],
                    "dist": float(d[k]),
                    "dt": float(dt[cand[k]]),
                    "m_usgs": u["magnitud"],
                }
            )
    p = pd.DataFrame(pares)
    m_ig = ig["magnitud"].to_numpy()
    mc_ig = magnitud_completitud(m_ig)
    us45 = int((us["magnitud"] >= 4.5).sum())
    return {
        "periodo": [str(ig["tiempo"].min().date()), str(ig["tiempo"].max().date())],
        "radio_km": radio,
        "igp_reportados": len(ig),
        "igp_m_mayor_4": int((m_ig >= 4).sum()),
        "usgs_m_mayor_4": len(us),
        "emparejados": len(p),
        "criterio_emparejamiento": "|Δt| ≤ 60 s y distancia ≤ 100 km",
        "fraccion_usgs_m45_con_reporte_igp": float((p["m_usgs"] >= 4.5).sum() / us45) if us45 and len(p) else None,
        "diferencia_magnitud_igp_menos_usgs": {
            "media": float(p["dm"].mean()),
            "desviacion": float(p["dm"].std()),
            "mediana": float(p["dm"].median()),
        }
        if len(p)
        else None,
        "diferencia_profundidad_km_mediana": float(p["dz"].median()) if len(p) else None,
        "distancia_epicentral_km_mediana": float(p["dist"].median()) if len(p) else None,
        "mc_igp_maxima_curvatura": mc_ig,
        "valor_b_igp": valor_b(m_ig, mc_ig) if (m_ig >= mc_ig).sum() > 50 else None,
        "nota": "El IGP publica los sismos que reporta (percibidos o relevantes), no su catálogo completo de detección.",
    }


def ejecutar(cfg: dict[str, Any], raw: Path, registro=print) -> dict[str, Any]:
    lluvia = _lluvia(cfg, raw)
    registro(
        f"fuentes: lluvia, mejor concordancia con la estación = {lluvia['mejor_concordancia_mensual_con_estacion']}"
    )
    temperatura = _temperatura(cfg, raw)
    sismos = _sismos(cfg, raw)
    registro(f"fuentes: sismos IGP {'sí' if sismos else 'no'} disponibles")
    return {
        "fenomeno": "fuentes",
        "tarea": "contraste_de_fuentes",
        "lluvia": lluvia,
        "temperatura": temperatura,
        "sismos_usgs_frente_a_igp": sismos,
        "fuentes_no_usadas": {
            "SMAP (NSIDC)": "Acceso con token verificado, pero empieza en 2015 (después del entrenamiento) y solo se distribuye por gránulo global; no aporta a los experimentos con la partición congelada.",
            "HLS (LP DAAC)": "Acceso con token verificado; reflectancia a 30 m sin relación directa con las variables objetivo de estos experimentos.",
            "SENAMHI, ANA, CENEPRED, SINIA, INGEMMET": "Sin API pública de datos (ver docs/verificacion/fuentes_fenomenos.json); se integrarán por convenio o descarga manual verificada.",
        },
    }
