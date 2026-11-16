"""Indicadores de estado actual para la portada: ENSO, sequía en la cabecera, sequía según ENSO y altitud.

Todo se calcula desde los crudos de ``data/raw`` (con su SHA-256) y se exporta a
``resultados/contrato/indicadores.json``, que el backend sirve en ``/api/v1/portada``. Nada se escribe a
mano en la interfaz.

Decisiones fijadas antes de mirar los valores recientes:

- **ENSO.** ONI de NOAA CPC (ERSSTv5, media móvil de 3 meses, bases climatológicas móviles de 30 años) y
  anomalías mensuales de Niño 3.4 y Niño 1+2 de ``sstoi.indices`` (OISST v2.1, base 1991–2020). El ONI es
  el índice oficial para declarar episodios (5 trimestres seguidos ≥ +0,5 °C) y llega con 1–2 meses de
  retraso; Niño 3.4 mensual es más reciente pero más ruidoso, y su base es distinta: no se comparan cifra a
  cifra. Niño 1+2 es la región costera que más afecta al Perú. La intensidad (≥ 1,5 °C "fuerte") es una
  convención usual, no una categoría oficial de NOAA.
- **SPI-3 actual.** Lluvia mensual de NASA POWER diaria (meses completos) en la celda de la cabecera; SPI con
  parámetros gamma ajustados solo con el entrenamiento (≤ 2015-12-31), igual que los experimentos. En la
  estación seca la lluvia de 3 meses es casi nula y el SPI pierde sentido: se marca "no confiable" si la
  media climatológica del acumulado de 3 meses de ese mes es < 10 mm.
- **Sequía según ENSO.** Para cada temporada de lluvias se toma el SPI-3 de febrero (acumulado dic–feb) y el
  ONI DJF del mismo año; se cuenta la frecuencia de SPI-3 ≤ −1 por categoría ENSO con intervalo de Wilson
  del 90 % y la prueba exacta de Fisher (El Niño frente al resto). Es una frecuencia histórica condicional
  (descriptiva), no un pronóstico.
- **Altitud.** Temperatura media 1991–2020 de la estación NOAA GHCN de Arequipa y de las celdas POWER, con
  su elevación; el gradiente observado se compara con la referencia de la atmósfera estándar (6,5 °C/km),
  que es una referencia física y no una corrección aplicada a los datos.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import math
from pathlib import Path

import pandas as pd
from scipy import stats

from ..senales.procesamiento import spi

FIN_ENTRENAMIENTO = "2015-12-31"
MIN_MM_SPI3 = 10.0
UMBRAL_SEQUIA = -1.0
GRADIENTE_REFERENCIA_C_KM = 6.5
PERIODO_NORMAL = ("1991-01-01", "2020-12-31")


def _sha256(archivo: Path) -> str:
    return hashlib.sha256(archivo.read_bytes()).hexdigest()


def _origen(archivo: Path, raiz: Path) -> dict:
    return {"archivo": archivo.relative_to(raiz).as_posix(), "sha256": _sha256(archivo)}


# --- ENSO ---------------------------------------------------------------------------------------------

TRIMESTRES = ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]


def oni_trimestral(archivo: Path) -> list[dict]:
    filas = Path(archivo).read_text(encoding="utf-8").strip().splitlines()[1:]
    return [{"trimestre": p[0], "anio": int(p[1]), "valor": float(p[3])} for p in (f.split() for f in filas) if len(p) >= 4]


def nino_mensual(archivo: Path) -> list[dict]:
    """``sstoi.indices``: YR MON NINO1+2 ANOM NINO3 ANOM NINO4 ANOM NINO3.4 ANOM."""
    filas = Path(archivo).read_text(encoding="utf-8").strip().splitlines()[1:]
    salida = []
    for f in filas:
        p = f.split()
        if len(p) < 10:
            continue
        salida.append({"anio": int(p[0]), "mes": int(p[1]), "nino12_anom": float(p[3]), "nino34_anom": float(p[9])})
    return salida


def intensidad(valor: float) -> str:
    if valor >= 1.5:
        return "nino_fuerte"
    if valor >= 0.5:
        return "nino"
    if valor <= -1.5:
        return "nina_fuerte"
    if valor <= -0.5:
        return "nina"
    return "neutro"


def enso(oni: list[dict], nino: list[dict] | None) -> dict:
    ultimo = oni[-1]
    consecutivos = 0
    for r in reversed(oni):
        if r["valor"] >= 0.5:
            consecutivos += 1
        else:
            break
    consecutivos_nina = 0
    for r in reversed(oni):
        if r["valor"] <= -0.5:
            consecutivos_nina += 1
        else:
            break
    episodio = "el_nino" if consecutivos >= 5 else "la_nina" if consecutivos_nina >= 5 else "sin_episodio"
    salida = {
        "oni": {
            "valor": ultimo["valor"],
            "trimestre": ultimo["trimestre"],
            "anio": ultimo["anio"],
            "intensidad": intensidad(ultimo["valor"]),
            "trimestres_consecutivos_nino": consecutivos,
            "trimestres_consecutivos_nina": consecutivos_nina,
            "episodio_noaa": episodio,
            "ultimos": oni[-12:],
        },
        "criterio_episodio": "NOAA CPC: 5 trimestres móviles seguidos con ONI ≥ +0,5 °C (El Niño) o ≤ −0,5 °C (La Niña)",
        "criterio_intensidad": "convención usual (no oficial de NOAA): ≥ 1,5 °C fuerte; 0,5–1,4 °C débil a moderado",
    }
    if nino:
        u = nino[-1]
        salida["nino_mensual"] = {
            "anio": u["anio"],
            "mes": u["mes"],
            "nino34_anom": u["nino34_anom"],
            "nino12_anom": u["nino12_anom"],
            "ultimos": nino[-12:],
            "base": "OISST v2.1, anomalías respecto de 1991–2020",
        }
    return salida


# --- Lluvia mensual y SPI-3 ---------------------------------------------------------------------------


def power_diario(archivo: Path, parametro: str) -> pd.Series:
    j = json.loads(Path(archivo).read_text(encoding="utf-8"))
    datos = j["properties"]["parameter"][parametro]
    s = pd.Series({pd.Timestamp(k): (v if v > -900 else float("nan")) for k, v in datos.items()}).sort_index()
    return s


def mensual_completo(diaria: pd.Series) -> pd.Series:
    """Suma mensual solo de meses con todos sus días presentes (un mes incompleto no se usa)."""
    grupos = diaria.groupby(diaria.index.to_period("M"))
    dias = grupos.count()
    esperados = pd.Series({p: p.days_in_month for p in dias.index})
    suma = grupos.sum()[dias == esperados]
    suma.index = suma.index.to_timestamp()
    return suma


def spi3_actual(mensual: pd.Series, meses: int = 12) -> dict:
    s3 = spi(mensual, 3, FIN_ENTRENAMIENTO)
    acum = mensual.rolling(3, min_periods=3).sum()
    entrenamiento = acum[acum.index <= pd.Timestamp(FIN_ENTRENAMIENTO)]
    clim = entrenamiento.groupby(entrenamiento.index.month).mean()
    filas = []
    for fecha in s3.dropna().index[-meses:]:
        media = float(clim.get(fecha.month, float("nan")))
        filas.append(
            {
                "mes": fecha.strftime("%Y-%m"),
                "spi3": round(float(s3[fecha]), 3),
                "acumulado_3m_mm": round(float(acum[fecha]), 1),
                "media_climatologica_3m_mm": round(media, 1),
                "confiable": bool(media >= MIN_MM_SPI3),
            }
        )
    confiables = [f for f in filas if f["confiable"]]
    return {
        "serie": filas,
        "ultimo": filas[-1] if filas else None,
        "ultimo_confiable": confiables[-1] if confiables else None,
        "categoria_ultimo_confiable": categoria_spi(confiables[-1]["spi3"]) if confiables else None,
        "criterio_confiable": f"media climatológica del acumulado de 3 meses ≥ {MIN_MM_SPI3:g} mm (entrenamiento ≤ {FIN_ENTRENAMIENTO})",
    }


def categoria_spi(v: float) -> str:
    """Categorías de McKee et al. (1993)."""
    if v <= -2:
        return "extremadamente_seco"
    if v <= -1.5:
        return "severamente_seco"
    if v <= -1:
        return "moderadamente_seco"
    if v < 1:
        return "cercano_a_lo_normal"
    if v < 1.5:
        return "moderadamente_humedo"
    if v < 2:
        return "muy_humedo"
    return "extremadamente_humedo"


def wilson(k: int, n: int, nivel: float = 0.9) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    z = float(stats.norm.ppf(0.5 + nivel / 2))
    p = k / n
    centro = (p + z * z / (2 * n)) / (1 + z * z / n)
    medio = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centro - medio), min(1.0, centro + medio))


def sequia_por_enso(mensual: pd.Series, oni: list[dict]) -> dict:
    s3 = spi(mensual, 3, FIN_ENTRENAMIENTO)
    djf = {r["anio"]: r["valor"] for r in oni if r["trimestre"] == "DJF"}
    temporadas = []
    for fecha, valor in s3.dropna().items():
        if fecha.month == 2 and fecha.year in djf:
            temporadas.append({"anio": fecha.year, "spi3_feb": round(float(valor), 3), "oni_djf": djf[fecha.year]})
    categorias = {
        "nina": ("La Niña (ONI DJF ≤ −0,5)", lambda o: o <= -0.5),
        "neutro": ("Neutro (−0,5 < ONI DJF < +0,5)", lambda o: -0.5 < o < 0.5),
        "nino": ("El Niño débil a moderado (+0,5 ≤ ONI DJF < +1,5)", lambda o: 0.5 <= o < 1.5),
        "nino_fuerte": ("El Niño fuerte (ONI DJF ≥ +1,5)", lambda o: o >= 1.5),
    }
    filas = []
    for clave, (nombre, cond) in categorias.items():
        sel = [t for t in temporadas if cond(t["oni_djf"])]
        k = sum(1 for t in sel if t["spi3_feb"] <= UMBRAL_SEQUIA)
        lo, hi = wilson(k, len(sel))
        filas.append(
            {
                "categoria": clave,
                "nombre": nombre,
                "n": len(sel),
                "con_sequia": k,
                "frecuencia": round(k / len(sel), 4) if sel else None,
                "ic90": [round(lo, 4), round(hi, 4)],
                "anios_con_sequia": [t["anio"] for t in sel if t["spi3_feb"] <= UMBRAL_SEQUIA],
            }
        )
    nino = [t for t in temporadas if t["oni_djf"] >= 0.5]
    resto = [t for t in temporadas if t["oni_djf"] < 0.5]
    a = sum(1 for t in nino if t["spi3_feb"] <= UMBRAL_SEQUIA)
    c = sum(1 for t in resto if t["spi3_feb"] <= UMBRAL_SEQUIA)
    _, p = stats.fisher_exact([[a, len(nino) - a], [c, len(resto) - c]], alternative="greater")
    return {
        "definicion": "SPI-3 de febrero (lluvia dic–feb) ≤ −1 en la celda POWER de la cabecera, por categoría del ONI DJF",
        "periodo": [temporadas[0]["anio"], temporadas[-1]["anio"]] if temporadas else None,
        "categorias": filas,
        "fisher_nino_vs_resto": {"p_unilateral": round(float(p), 4), "nino": [a, len(nino)], "resto": [c, len(resto)]},
        "temporadas": temporadas,
        "lectura": "Frecuencia histórica condicional (descriptiva), no un pronóstico calibrado; pocas temporadas por categoría.",
    }


# --- Altitud ------------------------------------------------------------------------------------------


def ghcn_media(archivo: Path) -> dict:
    filas = list(csv.DictReader(Path(archivo).open(encoding="utf-8")))
    a, b = PERIODO_NORMAL
    v = [float(f["TAVG"]) / 10 for f in filas if f.get("TAVG", "").strip() and a <= f["DATE"] <= b]
    dias = (pd.Timestamp(b) - pd.Timestamp(a)).days + 1
    return {
        "estacion": filas[0]["STATION"],
        "nombre": filas[0]["NAME"],
        "elevacion_m": float(filas[0]["ELEVATION"]),
        "temperatura_media_c": round(sum(v) / len(v), 2),
        "cobertura": round(len(v) / dias, 3),
    }


def power_media(archivo: Path) -> dict:
    j = json.loads(Path(archivo).read_text(encoding="utf-8"))
    t = power_diario(archivo, "T2M")
    a, b = PERIODO_NORMAL
    t = t[(t.index >= pd.Timestamp(a)) & (t.index <= pd.Timestamp(b))].dropna()
    lon, lat, z = j["geometry"]["coordinates"]
    return {"lon": lon, "lat": lat, "elevacion_celda_m": round(float(z), 1), "temperatura_media_c": round(float(t.mean()), 2)}


def altitud(ghcn: dict, cabecera: dict, ciudad: dict) -> dict:
    dz = (cabecera["elevacion_celda_m"] - ghcn["elevacion_m"]) / 1000
    dt_ = ghcn["temperatura_media_c"] - cabecera["temperatura_media_c"]
    return {
        "periodo": list(PERIODO_NORMAL),
        "estacion_ciudad": ghcn,
        "celda_cabecera": cabecera,
        "celda_ciudad_power": ciudad,
        "diferencia_c": round(dt_, 2),
        "desnivel_m": round(dz * 1000, 1),
        "gradiente_observado_c_km": round(dt_ / dz, 2),
        "gradiente_referencia_c_km": GRADIENTE_REFERENCIA_C_KM,
        "esperado_con_referencia_c": round(GRADIENTE_REFERENCIA_C_KM * dz, 2),
        "lectura": (
            "La atmósfera se enfría con la altura; 6,5 °C/km es la referencia de la atmósfera estándar, no una "
            "corrección aplicada a las observaciones. La celda POWER de la 'ciudad' (0,5°) promedia terreno a "
            "~3300 m, por eso es más fría que la estación del aeropuerto."
        ),
    }


# --- Resultados ya sellados -------------------------------------------------------------------------


def predicciones(resultados: Path) -> dict:
    """Series de prueba (observado, pronóstico e intervalo conformal del 90 %) de la sequía a 1 y 3 meses y
    desempeño de la lluvia extrema en los meses de eventos documentados. Se copian de resultados/*.json,
    cuyo SHA-256 está sellado en resultados/indice.json."""
    salida: dict = {"sequia": {}, "lluvia_eventos_documentados": []}
    seq = resultados / "sequia.json"
    if seq.exists():
        r = json.loads(seq.read_text(encoding="utf-8"))
        for h, d in r.get("horizontes", {}).items():
            sp = d.get("serie_prueba") or {}
            zoo = d.get("zoo", {})
            modelo = zoo.get("modelos", {}).get(sp.get("modelo"), {})
            salida["sequia"][h] = {
                "objetivo": d.get("definicion", {}).get("objetivo"),
                "modelo": sp.get("modelo"),
                "familia": modelo.get("familia"),
                "fechas": sp.get("fechas", []),
                "observado": sp.get("observado", []),
                "pronostico": sp.get("pronostico", []),
                "referencia": sp.get("referencia", []),
                "intervalo_90": sp.get("intervalo_90", []),
                "prueba": modelo.get("prueba"),
                "puntaje_validacion": modelo.get("puntaje_validacion"),
            }
        salida["sequia_origen"] = _origen(seq, resultados.parent)
    ll = resultados / "lluvia_extrema.json"
    if ll.exists():
        r = json.loads(ll.read_text(encoding="utf-8"))
        salida["lluvia_eventos_documentados"] = r.get("eventos_documentados", [])
        salida["lluvia_fuente"] = r.get("fuente_lluvia")
        salida["lluvia_umbral_mm"] = r.get("definicion", {}).get("umbral_mm")
        salida["lluvia_origen"] = _origen(ll, resultados.parent)
    return salida


# --- Conjunto -----------------------------------------------------------------------------------------


def generar(raw: Path, resultados: Path | None = None, particion: dict | None = None) -> dict:
    """Indicadores completos. `particion` es la partición temporal congelada de config/fenomenos.yaml."""
    raw = Path(raw)
    raiz = raw.parent.parent if raw.name == "raw" else raw
    oni_f = raw / "noaa" / "oni.ascii.txt"
    nino_f = raw / "noaa" / "sstoi.indices"
    cab_f = raw / "power" / "power_diario_cabecera.json"
    ciu_f = raw / "power" / "power_diario_ciudad.json"
    ghcn_f = next((raw / "ghcn").glob("ghcn_*.csv"))
    oni = oni_trimestral(oni_f)
    nino = nino_mensual(nino_f) if nino_f.exists() else None
    lluvia = mensual_completo(power_diario(cab_f, "PRECTOTCORR"))
    origen = [oni_f, cab_f, ciu_f, ghcn_f] + ([nino_f] if nino_f.exists() else [])
    return {
        "generado_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "enso": enso(oni, nino),
        "sequia_actual": {
            "punto": "celda NASA POWER de la cabecera del Chili",
            "lluvia_ultimo_mes": lluvia.index[-1].strftime("%Y-%m"),
            **spi3_actual(lluvia),
        },
        "sequia_por_enso": sequia_por_enso(lluvia, oni),
        "altitud": altitud(ghcn_media(ghcn_f), power_media(cab_f), power_media(ciu_f)),
        "predicciones": predicciones(Path(resultados)) if resultados else None,
        "particion_temporal": particion,
        "crudos": [_origen(f, raiz) for f in origen],
    }
