"""Inventario reproducible de licencias de las dependencias de terceros.

Recorre las dependencias de ejecución (transitivas) de cada componente y escribe una sección
Markdown con nombre, versión y licencia declarada por el propio paquete. No interpreta ni
inventa licencias: si un paquete no declara una, aparece como "no declarada" para revisión.

Uso (cada componente con el intérprete de su entorno, porque las versiones viven ahí):

    .venv/bin/python scripts/inventario_licencias.py python "terraverdict[ml]" > /tmp/ciencia.md
    backend/.venv/bin/python scripts/inventario_licencias.py python terraverdict-backend > /tmp/backend.md
    python scripts/inventario_licencias.py npm frontend > /tmp/frontend.md

`docs/licencias-terceros.md` se arma concatenando las tres salidas.
"""

from __future__ import annotations

import json
import re
import sys
from importlib import metadata
from pathlib import Path

# Licencias que obligan a revisar cómo se distribuye el producto (no prohíben el uso).
COPYLEFT = re.compile(r"\b(A?GPL|LGPL|MPL|EPL|CDDL|SSPL|CC-BY-SA|CC-BY-NC)", re.IGNORECASE)


def _licencia_python(dist: metadata.Distribution) -> str:
    meta = dist.metadata
    expresion = meta.get("License-Expression")
    if expresion:
        return expresion.strip()
    clasificadores = [c.split("::")[-1].strip() for c in meta.get_all("Classifier") or [] if c.startswith("License ::")]
    if clasificadores:
        return "; ".join(sorted(set(clasificadores)))
    texto = (meta.get("License") or "").strip()
    # Algunos paquetes pegan el texto completo de la licencia en este campo: se usa solo su primera línea.
    return texto.splitlines()[0][:80] if texto else "no declarada"


def _nombre(requisito: str, extras: frozenset[str] = frozenset()) -> str | None:
    marcado = re.search(r"extra\s*==\s*['\"]([^'\"]+)['\"]", requisito)
    if marcado and marcado.group(1) not in extras:  # opcional no pedido: no es de ejecución
        return None
    return re.split(r"[\s;<>=!~\[(]", requisito, maxsplit=1)[0]


def dependencias_python(raiz: str, extras: frozenset[str] = frozenset()) -> dict[str, metadata.Distribution]:
    vistos: dict[str, metadata.Distribution] = {}
    pendientes = [d for d in (_nombre(r, extras) for r in metadata.requires(raiz) or []) if d]
    while pendientes:
        nombre = pendientes.pop()
        clave = re.sub(r"[-_.]+", "-", nombre).lower()
        if clave in vistos:
            continue
        try:
            dist = metadata.distribution(nombre)
        except metadata.PackageNotFoundError:
            continue  # dependencia condicional de otra plataforma
        vistos[clave] = dist
        pendientes.extend(d for d in (_nombre(r) for r in dist.requires or []) if d)
    return vistos


def dependencias_npm(carpeta: Path) -> dict[str, tuple[str, str]]:
    paquete = json.loads((carpeta / "package.json").read_text(encoding="utf-8"))
    vistos: dict[str, tuple[str, str]] = {}
    pendientes = list(paquete.get("dependencies", {}))
    while pendientes:
        nombre = pendientes.pop()
        if nombre in vistos:
            continue
        ruta = carpeta / "node_modules" / nombre / "package.json"
        if not ruta.exists():
            continue  # dependencia opcional no instalada en esta plataforma
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        licencia = datos.get("license")
        if isinstance(licencia, dict):
            licencia = licencia.get("type")
        vistos[nombre] = (datos.get("version", "?"), licencia or "no declarada")
        pendientes.extend(datos.get("dependencies", {}))
    return vistos


def tabla(titulo: str, filas: list[tuple[str, str, str]]) -> str:
    revisar = [f for f in filas if COPYLEFT.search(f[2]) or f[2] == "no declarada"]
    lineas = [f"## {titulo}", "", f"{len(filas)} paquetes de ejecución (transitivos).", ""]
    if revisar:
        lineas += ["**Para revisar:** " + ", ".join(f"`{n}` ({lic})" for n, _, lic in revisar), ""]
    lineas += ["| Paquete | Versión | Licencia declarada |", "|---|---|---|"]
    lineas += [f"| {n} | {v} | {lic} |" for n, v, lic in sorted(filas, key=lambda f: f[0].lower())]
    return "\n".join(lineas) + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] not in {"python", "npm"}:
        print(__doc__, file=sys.stderr)
        return 2
    if argv[1] == "python":
        raiz, _, resto = argv[2].partition("[")
        extras = frozenset(e.strip() for e in resto.rstrip("]").split(",") if e.strip())
        deps = dependencias_python(raiz, extras)
        filas = [(d.metadata["Name"], d.version, _licencia_python(d)) for d in deps.values()]
        titulo = f"Python · `{argv[2]}`"
    else:
        npm = dependencias_npm(Path(argv[2]))
        filas = [(n, v, lic) for n, (v, lic) in npm.items()]
        titulo = f"npm · `{argv[2]}` (dependencias de producción)"
    sys.stdout.write(tabla(titulo, filas))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
