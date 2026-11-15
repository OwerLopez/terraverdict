"""El despliegue sin servidor (Vercel) debe instalar lo mismo que el backend y llevar sus datos."""

from __future__ import annotations

import json
import re
from pathlib import Path

import tomllib

RAIZ = Path(__file__).resolve().parents[2]


def _nombre(requisito: str) -> str:
    return re.split(r"[\s;<>=!~\[]", requisito, maxsplit=1)[0].lower().replace("_", "-")


def test_requisitos_de_la_funcion_cubren_al_backend() -> None:
    backend = tomllib.loads((RAIZ / "backend" / "pyproject.toml").read_text(encoding="utf-8"))
    necesarios = {_nombre(r) for r in backend["project"]["dependencies"]} - {"uvicorn"}  # Vercel trae su servidor
    lineas = (RAIZ / "api" / "requirements.txt").read_text(encoding="utf-8").splitlines()
    fijados = {_nombre(linea) for linea in lineas if linea.strip() and not linea.startswith("#")}
    assert necesarios <= fijados, f"faltan en api/requirements.txt: {sorted(necesarios - fijados)}"
    assert all("==" in linea for linea in lineas if linea.strip() and not linea.startswith("#")), "fijar versiones"


def test_la_funcion_no_excluye_los_datos_que_importa_la_api() -> None:
    config = json.loads((RAIZ / "vercel.json").read_text(encoding="utf-8"))
    excluidos = config["functions"]["api/index.py"]["excludeFiles"]
    for necesario in ("config/", "datos/", "docs/verificacion/", "resultados/contrato/"):
        assert not re.search(rf"[{{,]{re.escape(necesario)}\*\*", excluidos), f"{necesario} quedaría fuera de la función"
    assert (RAIZ / "resultados" / "contrato" / "expedientes.json").exists()
    destinos = {r["source"]: r["destination"] for r in config["rewrites"]}
    assert destinos["/api/(.*)"] == "/api/index"


def test_csp_del_frontend_autoriza_exactamente_el_script_en_linea() -> None:
    """La CSP de vercel.json permite el script en línea de index.html solo por su hash SHA-256."""
    import base64
    import hashlib
    import re

    raiz = Path(__file__).resolve().parents[2]
    html = (raiz / "frontend" / "index.html").read_text(encoding="utf-8")
    scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
    cabeceras = json.loads((raiz / "vercel.json").read_text(encoding="utf-8"))["headers"]
    csp = next(h["value"] for c in cabeceras for h in c["headers"] if h["key"] == "Content-Security-Policy")
    for s in scripts:
        huella = "sha256-" + base64.b64encode(hashlib.sha256(s.encode("utf-8")).digest()).decode()
        assert f"'{huella}'" in csp, "index.html cambió: actualizar el hash del script en la CSP de vercel.json"
    assert "'unsafe-inline'" not in csp.split("script-src", 1)[1].split(";", 1)[0]
    assert "frame-ancestors 'none'" in csp
