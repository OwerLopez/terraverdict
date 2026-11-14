"""Descarga trazable de las fuentes de los cinco fenómenos (config/fenomenos.yaml).

Cada paso se registra con éxito o error explícito: nada falla en silencio. Los crudos quedan en
``data/raw/<fuente>/`` con su manifiesto SHA-256, de modo que el resto del pipeline corre offline.
"""

from __future__ import annotations

import datetime as dt
import json
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Any

from . import ghcn, glc, gvp, noaa, power, usgs
from .http import sesion


def _paso(registro: dict[str, Any], nombre: str, funcion: Callable[[], Any]) -> None:
    inicio = dt.datetime.now(dt.timezone.utc)
    try:
        salida = funcion()
        registro[nombre] = {"ok": True, "salida": salida}
    except Exception as e:  # noqa: BLE001 — se registra el motivo exacto; el paso siguiente continúa
        registro[nombre] = {"ok": False, "error": f"{type(e).__name__}: {e}"[:300]}
    registro[nombre]["segundos"] = round((dt.datetime.now(dt.timezone.utc) - inicio).total_seconds(), 1)


def descargar_todo(cfg: dict[str, Any], raw: str | Path = "data/raw") -> dict[str, Any]:
    raw = Path(raw)
    d = cfg["descarga"]
    reg: dict[str, Any] = {"inicio_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    for nombre, p in cfg["puntos"].items():
        _paso(
            reg,
            f"power_diario_{nombre}",
            partial(
                power.descargar_diario,
                p["lon"],
                p["lat"],
                d["power_diario"][0],
                d["power_diario"][1],
                raw / "power",
                nombre,
            ),
        )
    cab = cfg["puntos"]["cabecera"]
    _paso(
        reg,
        "power_mensual_cabecera",
        lambda: power.descargar(
            cab["lon"],
            cab["lat"],
            d["power_mensual"][0],
            d["power_mensual"][1],
            raw / "power",
            parametros="PRECTOTCORR,T2M,T2M_MAX,T2M_MIN,RH2M,QV2M",
        ),
    )
    _paso(reg, "oni", lambda: noaa.descargar_oni(raw / "noaa"))
    _paso(reg, "ghcn", lambda: ghcn.descargar(d["ghcn_estacion"], raw / "ghcn"))
    c = cfg["puntos"]["ciudad"]
    s = d["sismos"]
    _paso(
        reg,
        "usgs",
        lambda: usgs.descargar(
            c["lat"], c["lon"], s["radio_km"], s["desde"], s["hasta"], raw / "usgs", mag_min=s["mag_min"]
        ),
    )
    _paso(reg, "gvp", lambda: gvp.descargar(raw / "gvp", pais="Peru"))
    _paso(reg, "glc", lambda: glc.descargar(raw / "glc"))
    reg["fin_utc"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    return reg


def celdas_power(lon: float, lat: float) -> tuple[float, float]:
    """Centro aproximado de la celda MERRA-2 (0,5° lat × 0,625° lon) que contiene el punto."""
    return round(round(lon / 0.625) * 0.625, 4), round(round(lat / 0.5) * 0.5, 4)


def descargar_celdas_deslizamientos(
    eventos: list[dict[str, Any]], cfg: dict[str, Any], raw: str | Path = "data/raw"
) -> dict[str, Any]:
    """Serie diaria de lluvia POWER para cada celda con deslizamientos del dominio (no por evento)."""
    caja = cfg["fenomenos"]["deslizamientos"]["dominio_bbox"]
    d = cfg["descarga"]["power_diario"]
    celdas = sorted(
        {
            celdas_power(e["lon"], e["lat"])
            for e in eventos
            if caja[0] <= e["lon"] <= caja[2] and caja[1] <= e["lat"] <= caja[3]
        }
    )
    reg: dict[str, Any] = {}
    for lon, lat in celdas:
        nombre = f"celda_{lon}_{lat}"
        _paso(
            reg,
            nombre,
            partial(
                power.descargar_diario,
                lon,
                lat,
                d[0],
                d[1],
                Path(raw) / "power_celdas",
                nombre,
                parametros="PRECTOTCORR",
            ),
        )
    return reg


def verificar_fuentes_nacionales(fuentes: dict[str, str], timeout: int = 60) -> dict[str, Any]:
    """Prueba de acceso real a los portales nacionales; registra código HTTP o error exacto."""
    s = sesion(reintentos=1)
    salida: dict[str, Any] = {"generado_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    for nombre, url in fuentes.items():
        try:
            r = s.get(url, timeout=timeout, allow_redirects=True)
            salida[nombre] = {"url": url, "http": r.status_code, "url_final": r.url, "bytes": len(r.content)}
        except Exception as e:  # noqa: BLE001 — la evidencia registra cualquier fallo de acceso
            salida[nombre] = {"url": url, "error": f"{type(e).__name__}: {e}"[:300]}
    return salida


def guardar_registro(reg: dict[str, Any], ruta: str | Path) -> Path:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(reg, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return ruta
