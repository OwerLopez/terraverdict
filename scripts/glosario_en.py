"""Genera el glosario español → inglés de los textos de datos que muestra la web.

Fuentes: catálogos de la API (fenómenos, variables, problemas, métricas, fuentes, dominios, eventos) y
los textos de los expedientes publicados. Traducción con Google Gemini en lotes y **validación
automática**: una traducción solo se acepta si conserva exactamente la misma secuencia de dígitos que
el original (ningún número puede cambiar); si no, el texto queda en español. Los textos ya traducidos
se reutilizan, así que volver a correrlo solo traduce lo nuevo.

Uso (con la API corriendo en local y TV_GEMINI_API_KEY en .env):
    python scripts/glosario_en.py --api http://127.0.0.1:8000 --salida frontend/src/lib/glosario-en.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))

from app.services.gemini import ClienteGemini  # noqa: E402

RUTAS = [
    "fenomenos", "variables", "problemas", "metricas", "metricas/mapas", "historial", "fuentes?limite=500", "dominios",
    "eventos", "expedientes?limite=500", "series?limite=500", "capas/sismos", "capas/volcanes", "nacional",
    "relevancia/matriz", "verificacion",
]
OMITIR = {
    "id", "url", "doi", "fuente_id", "variable_id", "problema_id", "coleccion", "version", "unidad", "unidad_id",
    "codigo", "acceso", "fecha", "fecha_publicacion", "familia", "licencia", "hash_contenido", "creado_en",
    "titulo_en", "descripcion_en", "dominio_id", "serie_id", "medio", "commit", "repositorio", "script",
}
INSTRUCCIONES = (
    "Translate each Spanish string of this JSON object to natural, concise English for a scientific web app about "
    "natural hazards and water in Arequipa, Peru. Rules: keep every number, unit, symbol, acronym, code, model name "
    "and proper noun (places, rivers, reservoirs, institutions such as SENAMHI, AUTODEMA, SEDAPAR) exactly; write "
    "decimals with a point instead of a comma; keep any text inside backticks unchanged; do not add or drop "
    "information. Return ONLY a JSON object with the same keys and the English strings as values."
)


def obtener(api: str, ruta: str) -> object:
    with urllib.request.urlopen(f"{api}/api/v1/{ruta}", timeout=120) as r:
        return json.load(r)


def textos(o: object, salida: set[str]) -> None:
    if isinstance(o, dict):
        for k, v in o.items():
            if k not in OMITIR:
                textos(v, salida)
    elif isinstance(o, list):
        for v in o:
            textos(v, salida)
    elif isinstance(o, str):
        prosa = len(o) > 2 and re.search(r"[a-záéíóúñ]", o) and not re.fullmatch(r"[a-z0-9_\-./:]+", o)
        if prosa and len(o) <= 600 and not o.startswith("http"):
            salida.add(o)


def digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--api", default="http://127.0.0.1:8000")
    p.add_argument("--salida", type=Path, default=RAIZ / "frontend" / "src" / "lib" / "glosario-en.json")
    p.add_argument("--lote", type=int, default=40)
    a = p.parse_args()

    clave = next(
        linea.split("=", 1)[1].strip()
        for linea in (RAIZ / ".env").read_text(encoding="utf-8").splitlines()
        if linea.startswith("TV_GEMINI_API_KEY=")
    )
    gemini = ClienteGemini(clave, ["gemini-flash-lite-latest", "gemini-flash-latest"], timeout_s=60)
    previo: dict[str, str] = json.loads(a.salida.read_text(encoding="utf-8")) if a.salida.exists() else {}

    pendientes: set[str] = set()
    for ruta in RUTAS:
        try:
            textos(obtener(a.api, ruta), pendientes)
        except Exception as e:  # noqa: BLE001 (una ruta opcional no debe detener el glosario)
            print(f"{ruta}: {e}")
    # El detalle de cada expediente (métodos, tareas, abstenciones) también se muestra en la web.
    for e in obtener(a.api, "expedientes?limite=500")["items"]:  # type: ignore[index]
        textos(obtener(a.api, f"expedientes/{e['id']}"), pendientes)
    vigentes = sorted(pendientes)
    faltan = [t for t in vigentes if t not in previo]
    print(f"{len(vigentes)} textos; {len(faltan)} por traducir")

    nuevo = {t: previo[t] for t in vigentes if t in previo}
    rechazados = 0
    for i in range(0, len(faltan), a.lote):
        lote = {str(j): t for j, t in enumerate(faltan[i : i + a.lote])}
        r = gemini.generar(INSTRUCCIONES, json.dumps(lote, ensure_ascii=False), temperatura=0.0, max_tokens=8192)
        crudo = re.sub(r"^```(?:json)?|```$", "", r.texto.strip(), flags=re.M).strip()
        try:
            traducido = json.loads(crudo)
        except json.JSONDecodeError:
            print(f"lote {i}: respuesta no JSON; se reintenta en la próxima corrida")
            continue
        for j, es in lote.items():
            en = str(traducido.get(j, "")).strip()
            if en and digitos(en) == digitos(es):
                nuevo[es] = en
            else:
                rechazados += 1
        print(f"lote {i // a.lote + 1}: {len(lote)} textos")
    a.salida.write_text(json.dumps(dict(sorted(nuevo.items())), ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"glosario: {len(nuevo)} entradas; {rechazados} rechazadas por cambiar dígitos (quedan en español)")


if __name__ == "__main__":
    main()
