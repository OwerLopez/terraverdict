"""Escala nacional: los 25 departamentos del Perú con el mismo motor que la cuenca del Chili.

Por departamento (celda NASA POWER de su capital, 1981–2025):
- Tendencia de la temperatura media anual y de la lluvia anual con el Sello de Confianza del
  paquete (Sen, Mann-Kendall conservador, filtro ENSO-HAC, ventanas, sensor, palanca,
  detectabilidad). La independencia queda pendiente (una sola familia), así que el máximo
  posible es 'frágil': el sistema lo dice en lugar de sobrevender.
- Estado de sequía: SPI-3 y SPI-12 del último mes, con parámetros gamma ajustados solo con
  1981–2015 (misma partición congelada).
Sismicidad nacional (USGS ComCat, caja que contiene al Perú): Mc, valor b con bootstrap, grilla de
1° con conteos y magnitud máxima, y valor b por franja de latitud (norte, centro, sur).
Deslizamientos por departamento (NASA GLC) y volcanes del país (Smithsonian GVP).
"""

from __future__ import annotations

import hashlib
import unicodedata
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..config import cargar_preregistro, cargar_yaml
from ..ingest import glc, gvp, noaa, power, usgs
from ..senales.procesamiento import spi
from ..trends.analizar import analizar_serie
from .comun import parametros
from .sismos import magnitud_completitud, valor_b

RAIZ = Path(__file__).resolve().parents[3]
# Fijado a priori en config/modelos.yaml (nacional.umbral_spi_mm_anual), con su justificación.
UMBRAL_SPI_MM = float(parametros()["nacional"]["umbral_spi_mm_anual"])


def _normalizar(texto: str | None) -> str:
    t = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode().lower().strip()
    return t.replace(" ", "_")


def power_celda(d: dict[str, Any]) -> tuple[float, float]:
    return round(round(d["lon"] / 0.625) * 0.625, 3), round(round(d["lat"] / 0.5) * 0.5, 3)


def descargar(cfg: dict[str, Any], raw: Path) -> dict[str, Any]:
    """Descarga POWER mensual por capital y el catálogo sísmico nacional (con manifiesto SHA-256)."""
    a, b = cfg["periodo_power"]
    registro: dict[str, Any] = {}
    for d in cfg["departamentos"]:
        destino = raw / "power_nacional"
        if any(destino.glob(f"power_{d['lon']}_{d['lat']}_*.json")):
            registro[d["id"]] = {"ok": True, "cache": True}
            continue
        try:
            registro[d["id"]] = {
                "ok": True,
                **power.descargar(d["lon"], d["lat"], a, b, destino, parametros="T2M,PRECTOTCORR"),
            }
        except Exception as e:  # noqa: BLE001 — se registra y se sigue con los demás departamentos
            registro[d["id"]] = {"ok": False, "error": f"{type(e).__name__}: {e}"[:200]}
    s = cfg["sismos"]
    destino = raw / "usgs_nacional"
    if not any(destino.glob("usgs_*.csv")):
        try:
            usgs.descargar_caja(s["bbox"], s["desde"], s["hasta"], destino, mag_min=s["mag_min"])
            registro["usgs_nacional"] = {"ok": True}
        except Exception as e:  # noqa: BLE001
            registro["usgs_nacional"] = {"ok": False, "error": f"{type(e).__name__}: {e}"[:200]}
    return registro


def disponibles(cfg: dict[str, Any], raw: Path) -> dict[str, Any]:
    """Modo sin red: usa solo lo que ya está en `raw` (pruebas y corridas reproducibles offline)."""
    salida: dict[str, Any] = {}
    for d in cfg["departamentos"]:
        hay = any((raw / "power_nacional").glob(f"power_{d['lon']}_{d['lat']}_*.json"))
        salida[d["id"]] = {"ok": True, "cache": True} if hay else {"ok": False, "error": "sin datos locales"}
    salida["usgs_nacional"] = {"ok": any((raw / "usgs_nacional").glob("usgs_*.csv"))}
    return salida


def _resumen_tendencia(r: dict[str, Any]) -> dict[str, Any]:
    return {
        "sen_por_decada": r["sen"]["sen_por_decada"],
        "ic90_por_decada": r["sen"]["ic_por_decada"],
        "p_conservador": r["mk"]["p_conservador"],
        "veredicto": r["sello"]["codigo"],
        "fallan": r["sello"]["fallan"],
        "pendientes": r["sello"]["pendientes"],
        "nota": r["sello"]["nota"],
        "anios_necesarios": (r.get("detectabilidad") or {}).get("anios_necesarios"),
        "periodo": r["periodo"],
    }


def _departamento(d: dict[str, Any], raw: Path, cfg: dict[str, Any], pre: Any, oni: dict[int, float]) -> dict[str, Any]:
    archivo = max((raw / "power_nacional").glob(f"power_{d['lon']}_{d['lat']}_*.json"))
    par, meta = power.cargar(archivo)
    t = pd.Series(
        {pd.Timestamp(int(k[:4]), int(k[4:]), 1): v for k, v in par["T2M"].items() if int(k[4:]) <= 12 and v != -999}
    )
    p = pd.Series(
        {
            pd.Timestamp(int(k[:4]), int(k[4:]), 1): v
            for k, v in par["PRECTOTCORR"].items()
            if int(k[4:]) <= 12 and v != -999
        }
    )
    p_mes = p * p.index.days_in_month  # mm/día → mm/mes
    completos_t = t.groupby(t.index.year).filter(lambda s: len(s) == 12)
    completos_p = p_mes.groupby(p_mes.index.year).filter(lambda s: len(s) == 12)
    t_anual = completos_t.groupby(completos_t.index.year).mean()
    p_anual = completos_p.groupby(completos_p.index.year).sum()
    tend_t = analizar_serie(t_anual.index.to_numpy(float), t_anual.to_numpy(), pre, oni=oni)
    tend_p = analizar_serie(p_anual.index.to_numpy(float), p_anual.to_numpy(), pre, oni=oni)
    hasta = cfg["spi_hasta_entrenamiento"]
    spi3, spi12 = spi(p_mes, 3, hasta), spi(p_mes, 12, hasta)
    clim = p_mes[p_mes.index <= pd.Timestamp(hasta)]
    return {
        **{k: d[k] for k in ("id", "nombre", "capital", "lon", "lat")},
        "elevacion_celda_m": meta["elevacion_celda_m"],
        "temperatura_media_c": float(t_anual.mean()),
        "lluvia_anual_media_mm": float(p_anual.mean()),
        "mes_mas_lluvioso": int(clim.groupby(clim.index.month).mean().idxmax()),
        "tendencia_temperatura": _resumen_tendencia(tend_t),
        "tendencia_lluvia": _resumen_tendencia(tend_p),
        "spi": {
            "mes": str(spi3.dropna().index[-1].date()),
            "spi3": float(spi3.dropna().iloc[-1]),
            "spi12": float(spi12.dropna().iloc[-1]),
            # En climas hiperáridos el ajuste gamma sobre lluvias casi nulas da SPI extremos y poco
            # informativos (OMM, Guía del usuario del SPI, 2012): se marcan y no se interpretan como sequía/exceso.
            "confiable": bool(float(p_anual.mean()) >= UMBRAL_SPI_MM),
            "nota": None
            if float(p_anual.mean()) >= UMBRAL_SPI_MM
            else f"Lluvia media < {UMBRAL_SPI_MM:.0f} mm/año: SPI poco fiable en clima árido.",
        },
        "series_anuales": {
            "anios": [int(a) for a in t_anual.index],
            "temperatura_c": [round(float(v), 3) for v in t_anual],
            "lluvia_mm": [round(float(p_anual.get(a, np.nan)), 1) for a in t_anual.index],
        },
    }


def _sismicidad(cfg: dict[str, Any], raw: Path) -> dict[str, Any]:
    ev = pd.DataFrame(usgs.cargar(raw / "usgs_nacional"))
    ev["tiempo"] = pd.to_datetime(ev["tiempo"], utc=True).dt.tz_localize(None)
    m = ev["magnitud"].to_numpy()
    mc = max(magnitud_completitud(m), float(cfg["sismos"]["mag_min"]))
    completos = ev[ev["magnitud"] >= mc - 1e-9]
    paso = float(cfg["sismos"]["celda_grados"])
    completos = completos.assign(
        clon=np.floor(completos["lon"] / paso) * paso + paso / 2,
        clat=np.floor(completos["lat"] / paso) * paso + paso / 2,
    )
    anios = (ev["tiempo"].max() - ev["tiempo"].min()).days / 365.25
    grilla = (
        completos.groupby(["clon", "clat"])
        .agg(n=("magnitud", "size"), m_max=("magnitud", "max"), prof_media=("profundidad_km", "mean"))
        .reset_index()
    )
    franjas = {"norte (0° a −8°)": (-8, 0.1), "centro (−8° a −14°)": (-14, -8), "sur (−14° a −18,5°)": (-18.6, -14)}
    por_franja = {}
    for nombre, (lo, hi) in franjas.items():
        sub = completos[(completos["lat"] >= lo) & (completos["lat"] < hi)]["magnitud"].to_numpy()
        por_franja[nombre] = (
            valor_b(sub, mc)
            if len(sub) >= 50
            else {"n": len(sub), "b": None, "nota": "menos de 50 sismos: no se estima b"}
        )
    grandes = ev[ev["magnitud"] >= 7.0].sort_values("magnitud", ascending=False)
    return {
        "fuente": "USGS ComCat (FDSN)",
        "bbox": cfg["sismos"]["bbox"],
        "eventos": len(ev),
        "desde": str(ev["tiempo"].min().date()),
        "hasta": str(ev["tiempo"].max().date()),
        "mc": mc,
        "valor_b": valor_b(m, mc),
        "valor_b_por_franja": por_franja,
        "tasa_anual_m_mayor_mc": float(len(completos) / anios),
        "grilla": [
            {
                "lon": float(r.clon),
                "lat": float(r.clat),
                "n": int(r.n),
                "tasa_anual": float(r.n / anios),
                "m_max": float(r.m_max),
                "profundidad_media_km": None if pd.isna(r.prof_media) else float(r.prof_media),
            }
            for r in grilla.itertuples()
        ],
        "grandes_sismos": [
            {
                "fecha": str(r.tiempo.date()),
                "magnitud": float(r.magnitud),
                "lugar": r.lugar,
                "lat": float(r.lat),
                "lon": float(r.lon),
                "profundidad_km": None if pd.isna(r.profundidad_km) else float(r.profundidad_km),
            }
            for r in grandes.itertuples()
        ],
        "advertencia": "Tasas históricas del catálogo global; no son pronósticos. El IGP mantiene el catálogo nacional oficial.",
    }


def ejecutar(
    raw: Path, registro: Any = print, config: Path | None = None, descargar_faltantes: bool = True
) -> dict[str, Any]:
    ruta_cfg = config or RAIZ / "config" / "nacional.yaml"
    cfg = cargar_yaml(ruta_cfg)
    pre = cargar_preregistro(RAIZ / "preregistro.yaml")
    oni = noaa.cargar_oni(raw / "noaa" / "oni.ascii.txt")
    descargas = descargar(cfg, raw) if descargar_faltantes else disponibles(cfg, raw)
    departamentos = []
    for d in cfg["departamentos"]:
        if not descargas.get(d["id"], {}).get("ok"):
            departamentos.append(
                {
                    **{k: d[k] for k in ("id", "nombre", "capital", "lon", "lat")},
                    "error": descargas.get(d["id"], {}).get("error", "sin datos"),
                }
            )
            continue
        celda = power_celda(d)
        compartida = next((x for x in departamentos if power_celda(x) == celda and "error" not in x), None)
        if compartida is not None:  # misma celda POWER: mismo clima, no se duplica
            departamentos.append(
                {
                    **{k: d[k] for k in ("id", "nombre", "capital", "lon", "lat")},
                    "comparte_celda_con": compartida["id"],
                    **{k: v for k, v in compartida.items() if k not in ("id", "nombre", "capital", "lon", "lat")},
                }
            )
            continue
        departamentos.append(_departamento(d, raw, cfg, pre, oni))
        registro(f"nacional: {d['nombre']} listo")
    # Deslizamientos por departamento (NASA GLC: el campo admin_division_name es el departamento)
    eventos_glc = glc.cargar(raw / "glc")
    conteo = pd.Series([_normalizar(e["region"]) for e in eventos_glc]).value_counts().to_dict()
    for dep in departamentos:
        dep["deslizamientos_glc"] = int(conteo.get(dep["id"], 0))
    volcanes, erupciones = gvp.cargar(raw / "gvp")
    resumen_veredictos: dict[str, dict[str, int]] = {"temperatura": {}, "lluvia": {}}
    for dep in departamentos:
        for var, clave in (("temperatura", "tendencia_temperatura"), ("lluvia", "tendencia_lluvia")):
            if clave in dep and "comparte_celda_con" not in dep:
                v = dep[clave]["veredicto"]
                resumen_veredictos[var][v] = resumen_veredictos[var].get(v, 0) + 1
    sismicidad = _sismicidad(cfg, raw) if descargas.get("usgs_nacional", {"ok": True}).get("ok") else None
    return {
        "fenomeno": "nacional",
        "tarea": "panorama_nacional",
        "configuracion": {
            "archivo": "config/nacional.yaml",
            "sha256": hashlib.sha256(Path(ruta_cfg).read_bytes()).hexdigest(),
        },
        "fuente_clima": "NASA POWER (MERRA-2), celda de la capital de cada departamento",
        "umbral_spi_mm": UMBRAL_SPI_MM,
        "departamentos": departamentos,
        "resumen_veredictos": resumen_veredictos,
        "sismicidad": sismicidad,
        "deslizamientos": {
            "fuente": "NASA Global Landslide Catalog",
            "total_peru": len(eventos_glc),
            "advertencia": "Catálogo basado en noticias, cobertura principal 2007–2017: subregistra zonas rurales.",
        },
        "volcanes": {
            "fuente": "Smithsonian GVP",
            "total": len(volcanes),
            "erupciones_registradas": len(erupciones),
            "lista": [
                {
                    "nombre": v["Volcano_Name"],
                    "lat": v["Latitude"],
                    "lon": v["Longitude"],
                    "ultima_erupcion": v.get("Last_Eruption_Year"),
                }
                for v in volcanes
            ],
        },
        "descargas": descargas,
        "lectura": (
            "Mismo motor y mismas reglas en todo el país. Con una sola familia de datos (POWER) el Sello no "
            "puede dar 'robusta': la prueba de independencia queda pendiente y el veredicto máximo es 'frágil'."
        ),
    }
