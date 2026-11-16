"""INGEMMET · GEOCATMIN: inventario nacional de peligros geológicos (ArcGIS REST, capa de puntos).

Servicio oficial: https://geocatmin.ingemmet.gob.pe/arcgis/rest/services/SERV_PELIGROS_GEOLOGICOS/MapServer/0
El servidor entrega solo el certificado hoja (sin el intermedio Sectigo OV R36), por lo que la
verificación TLS falla con el almacén de certifi. NO se desactiva la verificación: se añade el
intermedio publicado por la propia CA (URL "CA Issuers" del certificado, AIA) en
config/certificados/, y la cadena se valida hasta la raíz Sectigo R46 que ya está en certifi.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import certifi

from .http import sesion
from .manifest import guardar_crudo

SERVICIO = "https://geocatmin.ingemmet.gob.pe/arcgis/rest/services/SERV_PELIGROS_GEOLOGICOS/MapServer/0"
PRODUCTO = "INGEMMET_PELIGROS_GEOLOGICOS"
INTERMEDIO = Path(__file__).resolve().parents[3] / "config" / "certificados" / "sectigo_public_server_auth_ca_ov_r36.pem"
# Huella SHA-256 (DER) del intermedio, comprobada contra http://crt.sectigo.com/SectigoPublicServerAuthenticationCAOVR36.crt
HUELLA_INTERMEDIO = "6542d176bed50f193c0ce297ae44ecd8a0a86bec2ede682769344059b4e78530"
CAMPOS = "OBJECTID,COD_INV,NM_DPTO,NM_PROV,NM_DIST,FECHA,TIP_PELIGRO,NOM_PELIGRO,ALTURA,FUENTE,TIESTU_ANO"
PAGINA = 2000
# Dominio codificado del campo TIP_PELIGRO publicado por el propio servicio (capa 0: movimientos en masa).
TIPOS = {
    "1000|1100": "Caída",
    "1000|1200": "Vuelco",
    "1000|1300": "Deslizamiento",
    "1000|1400": "Desplazamiento lateral",
    "1000|1500": "Flujo",
    "1000|1600": "Movimiento complejo",
    "1000|1700": "Reptación",
}


def huella_pem(pem: str) -> str:
    import base64

    cuerpo = "".join(linea for linea in pem.strip().splitlines() if not linea.startswith("-----"))
    return hashlib.sha256(base64.b64decode(cuerpo)).hexdigest()


@contextmanager
def almacen_con_intermedio(intermedio: Path = INTERMEDIO) -> Generator[str]:
    """Archivo temporal = raíces de certifi + intermedio verificado por huella. La verificación sigue activa."""
    pem = intermedio.read_text(encoding="utf-8")
    if huella_pem(pem) != HUELLA_INTERMEDIO:
        raise ValueError(f"El intermedio {intermedio.name} no coincide con la huella registrada")
    f = tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False, encoding="utf-8", newline="\n")
    try:
        f.write(Path(certifi.where()).read_text(encoding="utf-8") + "\n" + pem)
        f.close()
        yield f.name
    finally:
        os.unlink(f.name)


def descargar(raw: str | Path) -> dict[str, Any]:
    s = sesion()
    with almacen_con_intermedio() as ca:
        s.verify = ca
        total = s.get(f"{SERVICIO}/query", params={"f": "json", "where": "1=1", "returnCountOnly": "true"}, timeout=120)
        total.raise_for_status()
        esperado = int(total.json()["count"])
        # El servicio no admite paginación por desplazamiento: se recorre por rangos de OBJECTID.
        ids = s.get(f"{SERVICIO}/query", params={"f": "json", "where": "1=1", "returnIdsOnly": "true"}, timeout=180)
        ids.raise_for_status()
        todos = sorted(ids.json()["objectIds"])
        rasgos: list[dict[str, Any]] = []
        for i in range(0, len(todos), PAGINA):
            lote_ids = todos[i : i + PAGINA]
            r = s.get(
                f"{SERVICIO}/query",
                params={
                    "f": "json",
                    "where": f"OBJECTID >= {lote_ids[0]} AND OBJECTID <= {lote_ids[-1]}",
                    "outFields": CAMPOS,
                    "outSR": "4326",
                },
                timeout=180,
            )
            r.raise_for_status()
            cuerpo = r.json()
            if "error" in cuerpo:
                raise RuntimeError(f"ArcGIS: {cuerpo['error']}")
            rasgos.extend(cuerpo.get("features", []))
    if len(rasgos) != esperado:
        raise RuntimeError(f"INGEMMET: se esperaban {esperado} registros y llegaron {len(rasgos)}")
    contenido = json.dumps({"servicio": SERVICIO, "total": esperado, "features": rasgos}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return guardar_crudo(raw, "peligros_geologicos.json", contenido, url=SERVICIO, producto=PRODUCTO, extra={"registros": esperado})


def cargar(carpeta: str | Path) -> list[dict[str, Any]]:
    datos = json.loads((Path(carpeta) / "peligros_geologicos.json").read_text(encoding="utf-8"))
    salida = []
    for f in datos["features"]:
        a, g = f.get("attributes") or {}, f.get("geometry") or {}
        if g.get("x") is None or g.get("y") is None:
            continue
        salida.append(
            {
                "id": a.get("COD_INV") or a.get("OBJECTID"),
                "lat": float(g["y"]),
                "lon": float(g["x"]),
                "departamento": (a.get("NM_DPTO") or "").strip(),
                "tipo": TIPOS.get((a.get("TIP_PELIGRO") or "").strip(), "Otro"),
                "peligro": (a.get("NOM_PELIGRO") or "").strip(),
                "fecha_ms": a.get("FECHA"),
            }
        )
    return salida
