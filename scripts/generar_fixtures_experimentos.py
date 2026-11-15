"""Genera tests/fixtures/raw_reducido/ recortando los crudos REALES de data/raw.

Los fixtures son un subconjunto exacto de los datos descargados (nunca sintéticos ni editados):
- POWER diario (ciudad y cabecera) y GHCN Arequipa: 2008-01-01 a 2020-12-31.
- POWER mensual, ONI y GVP: completos (son pequeños).
- USGS: eventos desde 2008, solo las columnas que usa el cargador.
- GLC: solo filas de Perú; POWER por celda: solo las celdas de esos eventos, 2006–2018.
- CHIRPS (ClimateSERV) y MODIS LST: 2008-01-01 a 2020-12-31 (CHIRPS de la cabecera desde 1981, para que
  el SPI tenga ≥ 10 años por mes en el entrenamiento), solo los campos que leen los cargadores.
- IGP: años 2012–2020, sismos a menos de 400 km de Arequipa.
Guarda el SHA-256 de cada crudo original en ``origen.json`` para trazar de dónde salió cada recorte.

Uso: python scripts/generar_fixtures_experimentos.py
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
RAW = RAIZ / "data" / "raw"
DESTINO = RAIZ / "tests" / "fixtures" / "raw_reducido"
COLUMNAS_USGS = ["time", "latitude", "longitude", "depth", "mag", "magType", "net", "id", "place", "type", "status"]


def sha(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def recortar_power(origen: Path, destino: Path, desde: str, hasta: str) -> None:
    j = json.loads(origen.read_text())
    for var, serie in j["properties"]["parameter"].items():
        j["properties"]["parameter"][var] = {k: v for k, v in serie.items() if desde <= k <= hasta}
    j.pop("header", None)
    j.pop("messages", None)
    destino.write_text(json.dumps(j, separators=(",", ":")))


def recortar_csv(origen: Path, destino: Path, filtro, columnas: list[str] | None = None) -> None:
    filas = list(csv.DictReader(io.StringIO(origen.read_text(encoding="utf-8", errors="replace"))))
    filas = [f for f in filas if filtro(f)]
    campos = columnas or list(filas[0].keys())
    with destino.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)


def _km(lat: float, lon: float, lat0: float = -16.4, lon0: float = -71.535) -> float:
    a = math.sin(math.radians(lat - lat0) / 2) ** 2 + math.cos(math.radians(lat0)) * math.cos(
        math.radians(lat)
    ) * math.sin(math.radians(lon - lon0) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(a))


def main() -> None:
    if DESTINO.exists():
        shutil.rmtree(DESTINO)
    origen: dict[str, str] = {}
    for sub in ("power", "noaa", "ghcn", "usgs", "gvp", "glc", "power_celdas", "chirps", "igp", "modis"):
        (DESTINO / sub).mkdir(parents=True)

    for punto in ("ciudad", "cabecera"):
        f = RAW / "power" / f"power_diario_{punto}.json"
        recortar_power(f, DESTINO / "power" / f.name, "20080101", "20201231")
        origen[f"power/{f.name}"] = sha(f)
    for f in [*RAW.joinpath("power").glob("power_-*_*.json"), RAW / "noaa" / "oni.ascii.txt"]:
        shutil.copy(f, DESTINO / f.parent.name / f.name)
        origen[f"{f.parent.name}/{f.name}"] = sha(f)
    for f in RAW.joinpath("gvp").glob("*.geojson"):
        shutil.copy(f, DESTINO / "gvp" / f.name)
        origen[f"gvp/{f.name}"] = sha(f)

    for f in RAW.joinpath("ghcn").glob("ghcn_*.csv"):
        recortar_csv(f, DESTINO / "ghcn" / f.name, lambda r: "2008-01-01" <= r["DATE"] <= "2020-12-31")
        origen[f"ghcn/{f.name}"] = sha(f)
    for f in sorted(RAW.joinpath("usgs").glob("usgs_*.csv")):
        if int(f.stem.split("_")[2]) < 2008:
            continue
        recortar_csv(f, DESTINO / "usgs" / f.name, lambda r: r["time"] >= "2008", COLUMNAS_USGS)
        origen[f"usgs/{f.name}"] = sha(f)

    glc = RAW / "glc" / "glc.csv"
    recortar_csv(glc, DESTINO / "glc" / "glc.csv", lambda r: r.get("country_name") == "Peru")
    origen["glc/glc.csv"] = sha(glc)
    for f in RAW.joinpath("power_celdas").glob("power_diario_celda_*.json"):
        recortar_power(f, DESTINO / "power_celdas" / f.name, "20060101", "20181231")
        origen[f"power_celdas/{f.name}"] = sha(f)

    for f in sorted(RAW.joinpath("chirps").glob("chirps_*.json")):
        datos = [
            {"date": d["date"], "raw_value": d["raw_value"]}
            for d in json.loads(f.read_text())["data"]
            if ("1981" if "cabecera_local" in f.name else "2008") <= d["date"][6:10] <= "2020"
        ]
        if datos:
            (DESTINO / "chirps" / f.name).write_text(json.dumps({"data": datos}, separators=(",", ":")))
            origen[f"chirps/{f.name}"] = sha(f)
    for f in sorted(RAW.joinpath("igp").glob("igp_*.json")):
        if int(f.stem.split("_")[1]) > 2020:
            continue
        cerca = [
            {k: e.get(k) for k in ("codigo", "idlistasismos", "fecha_local", "hora_local", "latitud", "longitud", "magnitud", "profundidad", "tipomagnitud")}
            for e in json.loads(f.read_text())
            if _km(float(e["latitud"]), float(e["longitud"])) <= 400
        ]
        (DESTINO / "igp" / f.name).write_text(json.dumps(cerca, separators=(",", ":")))
        origen[f"igp/{f.name}"] = sha(f)
    for f in sorted(RAW.joinpath("modis").glob("modis_*.json")):
        j = json.loads(f.read_text())
        j["subset"] = [
            {"calendar_date": d["calendar_date"], "data": d["data"]}
            for d in j["subset"]
            if "2008-01-01" <= d["calendar_date"] <= "2020-12-31"
        ]
        (DESTINO / "modis" / f.name).write_text(json.dumps(j, separators=(",", ":")))
        origen[f"modis/{f.name}"] = sha(f)

    (DESTINO / "origen.json").write_text(json.dumps(origen, indent=1, sort_keys=True) + "\n")
    total = sum(p.stat().st_size for p in DESTINO.rglob("*") if p.is_file())
    print(f"{DESTINO.relative_to(RAIZ)}: {total / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
