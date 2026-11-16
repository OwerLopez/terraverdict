"""Elige, mes a mes, la mejor imagen HLS de 30 m sobre la represa Aguada Blanca (NASA GIBS).

Por qué: el time-lapse y la comparación tipo cortina del mapa deben mostrar imágenes reales, no fechas al
azar (un día cualquiera puede no tener pasada del satélite o estar nublado). Para cada mes se prueban todas
las fechas que GIBS declara para las capas HLS S30 (Sentinel-2) y L30 (Landsat 8/9), se descarga la tesela
z12 que contiene el embalse y se mide, **dentro de la caja del embalse**:

- cobertura: fracción de píxeles con dato (no transparentes);
- nubosidad aproximada: fracción de píxeles muy brillantes y poco saturados (nube o nieve).

Se elige la fecha con cobertura ≥ 0,98 y menor nubosidad; si ninguna cumple nubosidad ≤ 0,10, el mes queda
"sin observación válida" (no se interpola ni se rellena). Cada elección guarda la URL exacta de la tesela y
su SHA-256, así que cualquiera puede comprobarla.

Caja del embalse: OpenStreetMap, way 23815221 ("Represa de Aguada Blanca"), consultada el 16-11-2026.
HLS es un producto conjunto NASA/USGS; S30 usa imágenes Sentinel-2 de la ESA (Copernicus) armonizadas por
NASA, por eso se atribuye a ESA/Copernicus y NASA, no solo a NASA.

Uso (requiere Pillow):
    python scripts/timelapse_hls.py --desde 2020-01 --hasta 2026-11 \
        --salida frontend/src/datos/timelapse_aguada_blanca.json
"""

from __future__ import annotations

import argparse
import calendar
import hashlib
import io
import json
import math
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from PIL import Image

GIBS = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best"
CAPACIDADES = f"{GIBS}/1.0.0/WMTSCapabilities.xml"
CAPAS = {
    "HLS_S30_Nadir_BRDF_Adjusted_Reflectance": "Sentinel-2 (HLS S30)",
    "HLS_L30_Nadir_BRDF_Adjusted_Reflectance": "Landsat 8/9 (HLS L30)",
}
ZOOM = 12
# OpenStreetMap way 23815221: lat −16,2481 a −16,2200; lon −71,3478 a −71,3306.
CAJA = {"lat_min": -16.2481438, "lat_max": -16.2200408, "lon_min": -71.3478139, "lon_max": -71.3306054}
UA = {"User-Agent": "terraverdict-open-research/1.0"}


def pixel_global(lat: float, lon: float, z: int = ZOOM) -> tuple[float, float]:
    """Coordenada de píxel global (Web Mercator, teselas de 256 px)."""
    n = 2**z * 256
    x = (lon + 180.0) / 360.0 * n
    phi = math.radians(lat)
    y = (1.0 - math.log(math.tan(phi) + 1.0 / math.cos(phi)) / math.pi) / 2.0 * n
    return x, y


def ventana() -> tuple[int, int, tuple[int, int, int, int]]:
    """Tesela (x, y) y ventana de píxeles (x0, y0, x1, y1) del embalse dentro de ella."""
    x0, y0 = pixel_global(CAJA["lat_max"], CAJA["lon_min"])
    x1, y1 = pixel_global(CAJA["lat_min"], CAJA["lon_max"])
    tx, ty = int(x0 // 256), int(y0 // 256)
    if int(x1 // 256) != tx or int(y1 // 256) != ty:
        raise SystemExit("La caja del embalse cruza el borde de la tesela: ampliar a varias teselas.")
    return tx, ty, (int(x0 - tx * 256), int(y0 - ty * 256), int(math.ceil(x1 - tx * 256)), int(math.ceil(y1 - ty * 256)))


def fechas_declaradas(xml: str, capa: str) -> list[date]:
    i = xml.find(f"<ows:Identifier>{capa}</ows:Identifier>")
    if i < 0:
        raise SystemExit(f"GIBS no declara la capa {capa}")
    bloque = xml[i : xml.find("</Layer>", i)]
    dias: list[date] = []
    for valor in re.findall(r"<Value>([^<]+)</Value>", bloque):
        ini, fin, _ = valor.split("/")
        d, f = date.fromisoformat(ini), date.fromisoformat(fin)
        while d <= f:
            dias.append(d)
            d += timedelta(days=1)
    return dias


def url_tesela(capa: str, dia: date, tx: int, ty: int) -> str:
    return f"{GIBS}/{capa}/default/{dia.isoformat()}/GoogleMapsCompatible_Level{ZOOM}/{ZOOM}/{ty}/{tx}.png"


def medir(capa: str, dia: date, tx: int, ty: int, caja: tuple[int, int, int, int]) -> dict | None:
    url = url_tesela(capa, dia, tx, ty)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
            datos = r.read()
    except Exception:  # noqa: BLE001 - sin tesela para ese día (404) o error de red: no hay observación
        return None
    img = Image.open(io.BytesIO(datos)).convert("RGBA").crop(caja)
    crudo = img.tobytes()
    px = [tuple(crudo[i : i + 4]) for i in range(0, len(crudo), 4)]
    total = len(px)
    con_dato = [p for p in px if p[3] > 0]
    cobertura = len(con_dato) / total
    if not con_dato:
        return {"cobertura": 0.0}
    brillantes = sum(1 for (r, g, b, _) in con_dato if min(r, g, b) > 170 and max(r, g, b) - min(r, g, b) < 40)
    return {
        "fecha": dia.isoformat(),
        "capa": capa,
        "sensor": CAPAS[capa],
        "cobertura": round(cobertura, 4),
        "nubosidad": round(brillantes / len(con_dato), 4),
        "url": url,
        "sha256": hashlib.sha256(datos).hexdigest(),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--desde", default="2020-01")
    ap.add_argument("--hasta", default=date.today().strftime("%Y-%m"))
    ap.add_argument("--salida", type=Path, required=True)
    ap.add_argument("--max-nubosidad", type=float, default=0.10)
    ap.add_argument("--min-cobertura", type=float, default=0.98)
    a = ap.parse_args()

    with urllib.request.urlopen(urllib.request.Request(CAPACIDADES, headers=UA), timeout=120) as r:
        xml = r.read().decode("utf-8")
    tx, ty, caja = ventana()
    desde = date.fromisoformat(a.desde + "-01")
    y, m = map(int, a.hasta.split("-"))
    hasta = date(y, m, calendar.monthrange(y, m)[1])
    candidatos = [(c, d) for c in CAPAS for d in fechas_declaradas(xml, c) if desde <= d <= min(hasta, date.today())]
    print(f"tesela z{ZOOM}/{ty}/{tx}, ventana {caja}, {len(candidatos)} fechas a probar", file=sys.stderr)

    with ThreadPoolExecutor(max_workers=12) as ex:
        medidas = [m for m in ex.map(lambda cd: medir(cd[0], cd[1], tx, ty, caja), candidatos) if m and m.get("fecha")]

    meses = []
    d = desde
    while d <= hasta:
        clave = d.strftime("%Y-%m")
        del_mes = [x for x in medidas if x["fecha"].startswith(clave) and x["cobertura"] >= a.min_cobertura]
        validas = sorted((x for x in del_mes if x["nubosidad"] <= a.max_nubosidad), key=lambda x: (x["nubosidad"], x["fecha"]))
        meses.append(
            {
                "mes": clave,
                "imagenes_probadas": sum(1 for x in medidas if x["fecha"].startswith(clave)),
                "imagenes_completas": len(del_mes),
                "elegida": validas[0] if validas else None,
            }
        )
        d = date(d.year + (d.month == 12), d.month % 12 + 1, 1)

    salida = {
        "titulo": "Time-lapse HLS 30 m de la represa Aguada Blanca",
        "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fuente": "NASA GIBS · HLS S30 (Sentinel-2, ESA/Copernicus armonizado por NASA) y HLS L30 (Landsat 8/9, NASA/USGS)",
        "caja_embalse": {**CAJA, "origen": "OpenStreetMap way 23815221"},
        "tesela": {"z": ZOOM, "x": tx, "y": ty, "ventana_px": list(caja)},
        "criterio": {"min_cobertura": a.min_cobertura, "max_nubosidad": a.max_nubosidad, "nubosidad": "fracción de píxeles con min(R,G,B) > 170 y saturación < 40 dentro del embalse"},
        "meses": meses,
    }
    a.salida.parent.mkdir(parents=True, exist_ok=True)
    a.salida.write_text(json.dumps(salida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    con = sum(1 for x in meses if x["elegida"])
    print(f"{con}/{len(meses)} meses con imagen válida → {a.salida}", file=sys.stderr)


if __name__ == "__main__":
    main()
