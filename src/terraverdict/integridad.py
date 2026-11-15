"""Integridad de punta a punta del pipeline (cadena de custodia de los datos).

1. Crudos: cada archivo de `data/raw/<fuente>/` se compara con el SHA-256 de su manifiesto,
   escrito en el momento de la descarga. Un archivo alterado detiene el entrenamiento.
2. Resultados: el orquestador sella cada `resultados/*.json` con su SHA-256 en `indice.json`.
3. Publicación: el publicador vuelve a calcular ese hash y se niega a publicar un resultado alterado.

Así una cifra mostrada en la web se puede rastrear hasta los bytes exactos que la produjeron.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class IntegridadComprometida(RuntimeError):
    """Un crudo o un resultado no coincide con el hash registrado."""


def sha256_archivo(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def verificar_crudos(raw: Path) -> dict[str, Any]:
    """Compara cada archivo presente con su manifiesto. Faltante ≠ alterado: solo lo segundo es fatal."""
    informe: dict[str, Any] = {"verificados": 0, "alterados": [], "faltantes": [], "sin_manifiesto": []}
    for manifiesto in sorted(raw.glob("*/manifiesto.json")):
        carpeta = manifiesto.parent
        registrados = set()
        for entrada in json.loads(manifiesto.read_text(encoding="utf-8")):
            ruta = carpeta / entrada["archivo"]
            registrados.add(entrada["archivo"])
            if not ruta.exists():
                informe["faltantes"].append(f"{carpeta.name}/{entrada['archivo']}")
            elif sha256_archivo(ruta) != entrada["sha256"]:
                informe["alterados"].append(f"{carpeta.name}/{entrada['archivo']}")
            else:
                informe["verificados"] += 1
        for archivo in sorted(carpeta.iterdir()):
            if archivo.name != "manifiesto.json" and archivo.is_file() and archivo.name not in registrados:
                informe["sin_manifiesto"].append(f"{carpeta.name}/{archivo.name}")
    informe["ok"] = not informe["alterados"]
    return informe


def exigir_crudos_integros(raw: Path) -> dict[str, Any]:
    informe = verificar_crudos(raw)
    if not informe["ok"]:
        raise IntegridadComprometida(
            "Crudos alterados respecto de su manifiesto (no se entrena sobre ellos): " + ", ".join(informe["alterados"])
        )
    return informe


def sellar_resultados(carpeta: Path) -> dict[str, str]:
    return {r.name: sha256_archivo(r) for r in sorted(carpeta.glob("*.json")) if r.name != "indice.json"}


def verificar_resultados(carpeta: Path) -> dict[str, Any]:
    indice = json.loads((carpeta / "indice.json").read_text(encoding="utf-8"))
    sellos: dict[str, str] = indice.get("sellos_sha256", {})
    alterados = [n for n, h in sellos.items() if (carpeta / n).exists() and sha256_archivo(carpeta / n) != h]
    sin_sello = [r.name for r in sorted(carpeta.glob("*.json")) if r.name != "indice.json" and r.name not in sellos]
    return {"ok": not alterados, "sellados": len(sellos), "alterados": alterados, "sin_sello": sin_sello}


def exigir_resultado_integro(ruta: Path) -> None:
    indice_ruta = ruta.parent / "indice.json"
    if not indice_ruta.exists():
        return
    sellos = json.loads(indice_ruta.read_text(encoding="utf-8")).get("sellos_sha256", {})
    if ruta.name in sellos and sha256_archivo(ruta) != sellos[ruta.name]:
        raise IntegridadComprometida(f"{ruta.name} no coincide con su sello en indice.json: no se publica.")
