#!/usr/bin/env python3
"""Revisión de todos los enlaces del reto y de la guía de la sede.

Para cada enlace: código HTTP, URL final y título de la página. Para las fuentes
con datos, además consulta qué hay disponible sobre la cuenca del Chili.
Guarda la evidencia en JSON.

Cada fallo de red o 5xx se reintenta una vez. Con ``--anterior`` se conserva el historial de
corridas previas: la red del entorno corta conexiones de forma intermitente, y un enlace que
respondió HTTP 200 en alguna corrida existe aunque en otra fallara.

Uso: python scripts/revisar_enlaces.py --anterior docs/verificacion/enlaces.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

import requests

PUNTO = "POINT(-71.35 -16.2)"  # cabecera del Chili (aprox.)
UA = {"User-Agent": "Mozilla/5.0 (terraverdict-revision-enlaces/1.0)"}

ENLACES = [
    # (grupo, nombre, url)
    ("Reto", "Página oficial del reto", "https://www.spaceappschallenge.org/2026/challenges/earth-system-trend-detective/"),
    ("Reto", "Giovanni", "https://giovanni.gsfc.nasa.gov/"),
    ("Reto", "Hydrology Time Series", "https://disc.gsfc.nasa.gov/information/tools?title=Hydrology%20Time%20Series"),
    ("Reto", "AppEEARS", "https://appeears.earthdatacloud.nasa.gov/"),
    ("Reto", "Climate Data Online (NOAA)", "https://www.ncei.noaa.gov/cdo-web/"),
    ("Reto", "Artículo SeaWiFS (Acker et al., 2009)", "https://ntrs.nasa.gov/api/citations/20090042747/downloads/20090042747.pdf"),
    ("Reto", "KNMI Climate Explorer", "https://climexp.knmi.nl/"),
    ("Reto", "Artículo: pruebas de tendencia (Medium)", "https://medium.com/@snp.kriss/statistical-test-methods-to-detect-trends-in-time-series-data-b361a0ec530b"),
    ("Reto", "Guía de significancia (Statsig)", "https://www.statsig.com/perspectives/a-comprehensive-guide-to-statistical-significance"),
    ("Reto", "RADARSAT Constellation Mission (CSA)", "https://donnees-data.asc-csa.gc.ca/en/dataset/rcm"),
    ("Reto", "Geo.ca", "https://geo.ca/"),
    ("Reto", "SWOT (CSA)", "https://www.asc-csa.gc.ca/eng/satellites/swot/"),
    ("Reto", "Ecosistemas desde el espacio (CSA)", "https://www.asc-csa.gc.ca/eng/satellites/everyday-lives/monitoring-and-protecting-our-ecosystems-from-space.asp"),
    ("Reto", "Tutorial SAR en Python (CSA)", "https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial"),
    ("Guía 1", "data.nasa.gov", "https://data.nasa.gov"),
    ("Guía 1", "api.nasa.gov", "https://api.nasa.gov"),
    ("Guía 1", "Earthdata", "https://earthdata.nasa.gov"),
    ("Guía 1", "Cuenta Earthdata (URS)", "https://urs.earthdata.nasa.gov"),
    ("Guía 1", "Earthdata Search", "https://search.earthdata.nasa.gov"),
    ("Guía 1", "Worldview", "https://worldview.earthdata.nasa.gov"),
    ("Guía 1", "NASA Images", "https://images.nasa.gov"),
    ("Guía 1", "Retos Space Apps 2026", "https://www.spaceappschallenge.org/2026/challenges/"),
    ("Guía 2", "R02 ASF Search (NISAR)", "https://search.asf.alaska.edu"),
    ("Guía 2", "R02 NISAR (JPL)", "https://nisar.jpl.nasa.gov"),
    ("Guía 2", "R03 NASA POWER", "https://power.larc.nasa.gov"),
    ("Guía 2", "R03 SMAP (JPL)", "https://smap.jpl.nasa.gov"),
    ("Guía 2", "R04 FIRMS", "https://firms.modaps.eosdis.nasa.gov"),
    ("Guía 2", "R05 Sonificación (Chandra)", "https://chandra.si.edu/sound/"),
    ("Guía 3", "Moon/Mars Trek", "https://trek.nasa.gov"),
    ("Guía 3", "Planetary Data System", "https://pds.nasa.gov"),
    ("Guía 3", "HiRISE", "https://hirise.lpl.arizona.edu"),
    ("Guía 3", "NSSDC", "https://nssdc.gsfc.nasa.gov"),
    ("Guía 3", "EarthExplorer (USGS)", "https://earthexplorer.usgs.gov"),
    ("Guía 4", "R12 PSI (Estación Espacial)", "https://psi.nasa.gov"),
    ("Guía 4", "R13 OSDR", "https://osdr.nasa.gov"),
    ("Guía 4", "R13 Human Research Program", "https://www.nasa.gov/hrp"),
    ("Guía 4", "R14 IRSA (SPHEREx)", "https://irsa.ipac.caltech.edu"),
    ("Guía 5", "Copernicus Data Space", "https://dataspace.copernicus.eu"),
    ("Guía 5", "JAXA G-Portal", "https://gportal.jaxa.jp"),
    ("Guía 5", "CSA", "https://www.asc-csa.gc.ca"),
]


def revisar(s: requests.Session, url: str) -> dict[str, Any]:
    r = s.get(url, timeout=60, allow_redirects=True)
    titulo = None
    if "html" in (r.headers.get("content-type") or ""):
        m = re.search(r"<title[^>]*>(.*?)</title>", r.text, re.S | re.I)
        titulo = re.sub(r"\s+", " ", m.group(1)).strip()[:120] if m else None
    return {"http": r.status_code, "url_final": r.url, "tipo": r.headers.get("content-type", "")[:40],
            "titulo": titulo, "bytes": len(r.content)}


def revisar_con_reintento(s: requests.Session, url: str, intentos: int = 2) -> dict[str, Any]:
    """Un fallo de red o un 5xx se reintenta una vez; se registra cuántos intentos hicieron falta."""
    d: dict[str, Any] = {}
    for n in range(1, intentos + 1):
        try:
            d = {"ok": True, **revisar(s, url)}
        except Exception as ex:
            d = {"ok": False, "error": f"{type(ex).__name__}: {ex}"[:200]}
        d["intentos"] = n
        if d["ok"] and d["http"] < 500:
            break
    return d


_CAMPOS_HISTORIAL = ("http", "error", "intentos")


def fusionar_historial(anteriores: list[dict[str, Any]], actual: dict[str, Any]) -> None:
    """Agrega a cada enlace el historial de corridas anteriores (misma URL), sin duplicar corridas.

    La red del entorno de verificación corta conexiones de forma intermitente: un enlace que
    respondió HTTP 200 en alguna corrida existe, aunque en otra fallara. El historial conserva
    todas las respuestas para que esa conclusión sea auditable.
    """
    previas: dict[str, list[dict[str, Any]]] = {}
    for previo in anteriores:
        for e in previo.get("enlaces", []):
            entradas = e.get("historial") or [
                {"utc": previo["generado_utc"], **{k: e[k] for k in _CAMPOS_HISTORIAL if k in e}}
            ]
            previas.setdefault(e["url"], []).extend(entradas)
    for e in actual["enlaces"]:
        propia = {"utc": actual["generado_utc"], **{k: e[k] for k in _CAMPOS_HISTORIAL if k in e}}
        por_corrida = {h["utc"]: h for h in [*previas.get(e["url"], []), propia]}
        e["historial"] = sorted(por_corrida.values(), key=lambda h: h["utc"])
        e["corridas_con_200"] = sum(1 for h in e["historial"] if h.get("http") == 200)


def sondas(s: requests.Session) -> dict[str, Callable[[], Any]]:
    def reto_texto():
        html = s.get(ENLACES[0][2], timeout=60).text
        txt = re.sub(r"<[^>]+>", " ", html)
        txt = re.sub(r"\s+", " ", txt)
        claves = ["Objectives", "Potential Considerations", "Background", "significant"]
        return {"menciona": {k: (k.lower() in txt.lower()) for k in claves}, "extracto": txt[:3000]}

    def asf_nisar():
        out = {}
        for plat in ("NISAR", "SENTINEL-1"):
            r = s.get("https://api.daac.asf.alaska.edu/services/search/param",
                      params={"platform": plat, "intersectsWith": PUNTO, "output": "count"}, timeout=90)
            out[plat] = r.text.strip()[:40]
        return out

    def imagenes_nasa():
        r = s.get("https://images-api.nasa.gov/search", params={"q": "Arequipa"}, timeout=60).json()
        items = r["collection"]["items"]
        return {"resultados": r["collection"]["metadata"]["total_hits"],
                "ejemplos": [i["data"][0]["title"][:70] for i in items[:5]]}

    def data_nasa():
        r = s.get("https://data.nasa.gov/api/3/action/package_search", params={"q": "IMERG precipitation", "rows": 3}, timeout=60)
        return {"http": r.status_code, "inicio_respuesta": r.text[:300]}

    def api_nasa():
        r = s.get("https://api.nasa.gov/planetary/apod", params={"api_key": "DEMO_KEY"}, timeout=60)
        return {"apod_http": r.status_code}

    def ntrs_metodos():
        pdf = s.get(ENLACES[5][2], timeout=120).content
        if not shutil.which("pdftotext"):
            return {"bytes": len(pdf)}
        with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
            f.write(pdf); f.flush()
            t = subprocess.run(["pdftotext", f.name, "-"], capture_output=True, text=True).stdout
        terminos = ["Giovanni", "Mann-Kendall", "Seasonal Kendall", "Sen", "linear regression",
                    "least squares", "deseasonal", "anomal", "autocorrelation", "significan", "SeaWiFS"]
        return {"paginas_aprox": t.count("\f") + 1,
                "menciona": {k: len(re.findall(re.escape(k), t, re.I)) for k in terminos}}

    def medium_statsig():
        out = {}
        for nombre, url in ((ENLACES[7][1], ENLACES[7][2]), (ENLACES[8][1], ENLACES[8][2])):
            t = re.sub(r"<[^>]+>", " ", s.get(url, timeout=60).text)
            out[nombre] = {k: len(re.findall(k, t, re.I)) for k in
                           ["Mann-Kendall", "Sen", "Spearman", "Cox-Stuart", "p-value", "multiple", "power"]}
        return out

    def rcm_ckan():
        r = s.get("https://data.asc-csa.gc.ca/api/3/action/package_search", params={"q": "RCM", "rows": 3}, timeout=60)
        j = r.json() if r.ok else {}
        res = j.get("result", {}).get("results", [])
        return {"http": r.status_code, "conjuntos": [(d.get("title"), d.get("license_title"),
                                                      len(d.get("resources", []))) for d in res]}

    def giovanni_rods():
        g = s.get("https://giovanni.gsfc.nasa.gov/giovanni/", timeout=60).status_code
        d = s.get("https://hydro1.gesdisc.eosdis.nasa.gov/daac-bin/access/timeseries.cgi",
                  params={"variable": "GLDAS2:GLDAS_NOAH025_3H_v2.1:SoilMoi0_10cm_inst",
                          "location": "GEOM:POINT(-71.25, -15.95)", "startDate": "2020-01-01T00",
                          "endDate": "2020-01-02T00", "type": "asc2"}, timeout=60)
        return {"giovanni_http": g, "data_rods_http": d.status_code, "data_rods_inicio": d.text[:200]}

    return {"reto_texto": reto_texto, "asf_conteos": asf_nisar, "nasa_images_arequipa": imagenes_nasa,
            "data_nasa_api": data_nasa, "api_nasa_apod": api_nasa, "ntrs_metodos": ntrs_metodos,
            "medium_statsig_contenido": medium_statsig, "rcm_catalogo": rcm_ckan,
            "giovanni_y_data_rods": giovanni_rods}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default="docs/verificacion/enlaces.json")
    ap.add_argument("--anterior", nargs="*", default=[],
                    help="Evidencias previas cuyo historial se conserva (p. ej. la misma salida).")
    a = ap.parse_args()
    anteriores = [json.loads(Path(f).read_text()) for f in a.anterior if Path(f).exists()]
    s = requests.Session(); s.headers.update(UA)
    ev: dict[str, Any] = {"generado_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                          "enlaces": [], "sondas": {}}
    for grupo, nombre, url in ENLACES:
        d = revisar_con_reintento(s, url)
        ev["enlaces"].append({"grupo": grupo, "nombre": nombre, "url": url, **d})
        print(f"[{d.get('http', 'ERR')}] {nombre}", file=sys.stderr)
    for k, f in sondas(s).items():
        try:
            ev["sondas"][k] = {"ok": True, "datos": f()}
        except Exception as ex:
            ev["sondas"][k] = {"ok": False, "error": f"{type(ex).__name__}: {ex}"[:200]}
        print(f"[{'OK ' if ev['sondas'][k]['ok'] else 'ERR'}] sonda {k}", file=sys.stderr)
    fusionar_historial(anteriores, ev)
    abiertos = sum(1 for e in ev["enlaces"] if e["corridas_con_200"] > 0)
    print(f"{abiertos}/{len(ev['enlaces'])} enlaces con HTTP 200 en al menos una corrida", file=sys.stderr)
    Path(a.salida).write_text(json.dumps(ev, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
