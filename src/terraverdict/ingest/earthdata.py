"""Acceso a NASA Earthdata con token: IMERG Final diaria (GES DISC, OPeNDAP).

El token se lee de la variable de entorno ``EARTHDATA_TOKEN`` o del archivo ``.env`` de la raíz
(una línea ``EARTHDATA_TOKEN=...`` o solo el token). Nunca se escribe en crudos, manifiestos ni
registros. GES DISC exige además que la cuenta haya aceptado su licencia (EULA) una vez; si no,
responde 403 con la URL para aceptarla, y aquí se informa tal cual.

IMERG Final V07 diaria (Huffman et al., doi:10.5067/GPM/IMERGDF/DAY/07): rejilla de 0,1°,
``precipitation[time][lon][lat]`` en mm/día. Se pide una caja pequeña de celdas por día.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from .http import sesion
from .manifest import guardar_crudo

RAIZ = Path(__file__).resolve().parents[3]
OPENDAP = "https://gpm1.gesdisc.eosdis.nasa.gov/opendap/GPM_L3/GPM_3IMERGDF.07"
PRODUCTO = "GPM_3IMERGDF_V07"


def token_earthdata(ruta_env: Path = RAIZ / ".env") -> str:
    if os.environ.get("EARTHDATA_TOKEN"):
        return os.environ["EARTHDATA_TOKEN"].strip()
    if ruta_env.exists():
        texto = ruta_env.read_text().strip()
        for linea in texto.splitlines():
            if linea.startswith("EARTHDATA_TOKEN="):
                return linea.split("=", 1)[1].strip().strip("\"'")
        if "=" not in texto and len(texto.split()) == 1:
            return texto
    raise RuntimeError("Falta el token de Earthdata (EARTHDATA_TOKEN o .env)")


def indice_imerg(lon: float, lat: float) -> tuple[int, int]:
    """Índices (lon, lat) de la celda IMERG de 0,1° que contiene el punto."""
    return int((lon + 180) / 0.1 + 1e-9), int((lat + 90) / 0.1 + 1e-9)  # tolerancia: 73,6/0,1 = 735,999…


def _url_dia(d: dt.date, lon: tuple[int, int], lat: tuple[int, int]) -> str:
    v = "V07B"
    archivo = f"3B-DAY.MS.MRG.3IMERG.{d:%Y%m%d}-S000000-E235959.{v}.nc4"
    return (
        f"{OPENDAP}/{d:%Y}/{d:%m}/{archivo}.ascii?"
        f"precipitation.precipitation[0:0][{lon[0]}:{lon[1]}][{lat[0]}:{lat[1]}]"  # solo el arreglo, sin mapas
    )


REINTENTABLES = (401, 429, 500, 502, 503, 504)


def _verificar(r) -> None:
    if r.status_code in (401, 403):
        raise PermissionError(
            f"GES DISC respondió {r.status_code}: {r.text[:200]}. "
            "Si es 'EULA Acceptance Failure', el dueño de la cuenta debe aceptar la licencia en la URL indicada."
        )
    r.raise_for_status()


def pedir_con_reintentos(
    get: Callable[[str], Any],
    url: str,
    intentos: int = 4,
    espera: float = 2.0,
    dormir: Callable[[float], None] = time.sleep,
) -> Any:
    """GET con reintentos acotados y espera exponencial.

    GES DISC limita la tasa de consultas: bajo carga puede responder 401 o 429 a un token válido.
    Se reintenta 401/429/5xx (2, 4, 8 s…). Un 403 no se reintenta: suele ser la licencia (EULA) sin
    aceptar, y repetir no lo arregla. Si se agotan los intentos se devuelve la última respuesta.
    """
    r = get(url)
    for i in range(intentos - 1):
        if r.status_code not in REINTENTABLES:
            break
        dormir(espera * 2**i)
        r = get(url)
    return r


def descargar_imerg(
    lon: tuple[int, int],
    lat: tuple[int, int],
    desde: dt.date,
    hasta: dt.date,
    raw: str | Path,
    hilos: int = 4,
) -> list[dict[str, Any]]:
    """Una caja de celdas IMERG por día; se guarda un crudo por año (respuestas ASCII concatenadas).

    Reanudable: un año ya guardado y completo según el manifiesto no se vuelve a pedir. Un día que el
    servidor no tiene (404) se registra en `dias_faltantes` del manifiesto; no se rellena.
    """
    raw = Path(raw)
    s = sesion()
    s.headers["Authorization"] = f"Bearer {token_earthdata()}"

    def get(url: str) -> Any:
        return s.get(url, timeout=180)

    _verificar(pedir_con_reintentos(get, _url_dia(desde, lon, lat)))  # falla temprano si no hay acceso
    man = raw / "manifiesto.json"
    previos = {e["archivo"]: e for e in json.loads(man.read_text())} if man.exists() else {}
    entradas: list[dict[str, Any]] = []
    for anio in range(desde.year, hasta.year + 1):
        a, b = max(desde, dt.date(anio, 1, 1)), min(hasta, dt.date(anio, 12, 31))
        dias = [a + dt.timedelta(days=i) for i in range((b - a).days + 1)]
        nombre = f"imerg_diaria_{anio}.txt"
        previo = previos.get(nombre)
        if previo and previo.get("dias") == len(dias) and (raw / nombre).exists():
            entradas.append(previo)
            continue

        def bajar(d: dt.date) -> str | None:
            r = pedir_con_reintentos(get, _url_dia(d, lon, lat))
            if r.status_code == 404:
                return None
            _verificar(r)
            return f"### {d.isoformat()}\n{r.text}"

        try:
            with ThreadPoolExecutor(hilos) as ex:
                bloques = list(ex.map(bajar, dias))
        except PermissionError as e:
            # Los años anteriores ya quedaron guardados; el siguiente intento retoma desde este.
            raise PermissionError(f"Descarga de IMERG detenida en {anio} (años previos guardados): {e}") from e
        faltantes = [d.isoformat() for d, bl in zip(dias, bloques, strict=True) if bl is None]
        entradas.append(
            guardar_crudo(
                raw,
                nombre,
                "\n".join(bl for bl in bloques if bl is not None).encode(),
                url=_url_dia(a, lon, lat).split("?")[0].rsplit("/", 3)[0],
                producto=PRODUCTO,
                version="V07B",
                extra={
                    "indices_lon": list(lon),
                    "indices_lat": list(lat),
                    "dias": len(dias),
                    "dias_faltantes": faltantes,
                },
            )
        )
    return entradas


def cargar_imerg(carpeta: str | Path, lon: int, lat: int, lon0: int, lat0: int) -> dict[str, float]:
    """{fecha_iso: mm/día} de la celda (lon, lat) dentro de las cajas que empiezan en (lon0, lat0)."""
    salida: dict[str, float] = {}
    patron = re.compile(r"^precipitation\.precipitation\[0\]\[(\d+)\],\s*(.*)$")
    for f in sorted(Path(carpeta).glob("imerg_diaria_*.txt")):
        fecha = None
        for linea in f.read_text().splitlines():
            if linea.startswith("### "):
                fecha = linea[4:]
                continue
            m = patron.match(linea.strip())
            if fecha and m and int(m.group(1)) == lon - lon0:
                valores = [float(v) for v in m.group(2).split(",")]
                v = valores[lat - lat0]
                if v >= 0:
                    salida[fecha] = v
    return salida
