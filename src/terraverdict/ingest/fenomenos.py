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

from . import chirps, earthdata, ghcn, glc, gvp, igp, modis, noaa, power, usgs
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
    descargar_fuentes_adicionales(cfg, raw, reg)
    reg["fin_utc"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    return reg


ADICIONALES = ("chirps", "igp", "imerg", "modis")


def descargar_fuentes_adicionales(
    cfg: dict[str, Any], raw: Path, reg: dict[str, Any], fuentes: tuple[str, ...] = ADICIONALES
) -> dict[str, Any]:
    """CHIRPS (local 0,1° y celda de POWER), sismos del IGP, IMERG y MODIS LST para los dos puntos."""
    d = cfg["descarga"]
    ch = d["chirps"]
    for nombre, p in cfg["puntos"].items() if "chirps" in fuentes else ():
        lon_c, lat_c = celdas_power(p["lon"], p["lat"])
        for sufijo, geometria in (
            ("local", chirps.caja(p["lon"], p["lat"], ch["caja_local_grados"], ch["caja_local_grados"])),
            ("celda_power", chirps.caja(lon_c, lat_c, 0.625, 0.5)),
        ):
            _paso(
                reg,
                f"chirps_{nombre}_{sufijo}",
                partial(
                    chirps.descargar,
                    f"{nombre}_{sufijo}",
                    geometria,
                    ch["desde"],
                    ch["hasta"],
                    raw / "chirps",
                    hasta_fecha=ch["hasta_fecha"],
                ),
            )
    if "igp" in fuentes:
        _paso(reg, "igp", lambda: igp.descargar(d["igp"]["desde"], d["igp"]["hasta"], raw / "igp"))
    indices = [earthdata.indice_imerg(p["lon"], p["lat"]) for p in cfg["puntos"].values()]
    lon = (min(i[0] for i in indices), max(i[0] for i in indices))
    lat = (min(i[1] for i in indices), max(i[1] for i in indices))
    if "imerg" in fuentes:
        _paso(
            reg,
            "imerg",
            lambda: earthdata.descargar_imerg(
                lon,
                lat,
                dt.date.fromisoformat(d["imerg"]["desde"]),
                dt.date.fromisoformat(d["imerg"]["hasta"]),
                raw / "imerg",
            ),
        )
    for nombre, p in cfg["puntos"].items() if "modis" in fuentes else ():
        _paso(
            reg,
            f"modis_lst_{nombre}",
            partial(modis.descargar, nombre, p["lat"], p["lon"], raw / "modis", d["modis_lst"]["desde"]),
        )
    return reg


def registrar_desde_manifiestos(reg: dict[str, Any], raw: Path) -> dict[str, Any]:
    """Completa el registro con las fuentes adicionales ya descargadas en una corrida anterior que no
    llegó a escribir el registro (p. ej., interrumpida). La evidencia es su manifiesto SHA-256."""
    for carpeta in ("chirps", "igp"):
        man = raw / carpeta / "manifiesto.json"
        if not man.exists():
            continue
        for e in json.loads(man.read_text()):
            clave = carpeta if carpeta == "igp" else "_".join(e["archivo"].split("_")[:-2]).removesuffix(".json")
            if clave not in reg:
                reg[clave] = {"ok": True, "salida": [], "nota": "Tomado del manifiesto de una corrida anterior."}
            if reg[clave].get("nota") and e not in reg[clave]["salida"]:
                reg[clave]["salida"].append(e)
    # MODIS: un paso por punto, completo solo si su manifiesto tiene todas las bandas
    man = raw / "modis" / "manifiesto.json"
    if man.exists():
        entradas = json.loads(man.read_text())
        for punto in {e["archivo"].split("_")[1] for e in entradas}:
            propias = [e for e in entradas if e["archivo"].startswith(f"modis_{punto}_")]
            clave = f"modis_lst_{punto}"
            if len(propias) == 2 and not reg.get(clave, {}).get("ok"):
                reg[clave] = {"ok": True, "salida": propias, "nota": "Tomado del manifiesto (todas las bandas)."}
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
