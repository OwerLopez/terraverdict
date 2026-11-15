"""Genera tests/fixtures/raw_reducido/ recortando los crudos REALES de data/raw.

Los fixtures son un subconjunto exacto de los datos descargados (nunca sintéticos ni editados):
- POWER diario (ciudad y cabecera) y GHCN Arequipa: 2008-01-01 a 2020-12-31.
- POWER mensual, ONI y GVP: completos (son pequeños).
- USGS: eventos desde 2008, solo las columnas que usa el cargador.
- GLC: solo filas de Perú; POWER por celda: solo las celdas de esos eventos, 2006–2018.
Guarda el SHA-256 de cada crudo original en ``origen.json`` para trazar de dónde salió cada recorte.

Uso: python scripts/generar_fixtures_experimentos.py
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
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


def main() -> None:
    if DESTINO.exists():
        shutil.rmtree(DESTINO)
    origen: dict[str, str] = {}
    for sub in ("power", "noaa", "ghcn", "usgs", "gvp", "glc", "power_celdas"):
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

    (DESTINO / "origen.json").write_text(json.dumps(origen, indent=1, sort_keys=True) + "\n")
    total = sum(p.stat().st_size for p in DESTINO.rglob("*") if p.is_file())
    print(f"{DESTINO.relative_to(RAIZ)}: {total / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
