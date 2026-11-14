"""Línea base DETERMINISTA para los reportes hídricos de AUTODEMA (sin LLM).

ESTADO: esqueleto. No se vio el layout exacto del PDF (solo que contiene 'Total Cuenca Chili'
y 6 líneas con 'Volumen Útil'). El primer paso en local es:
    pdftotext -layout REPORTE-HIDRICO.pdf - | less
y ajustar RE_FILA. Después este parser sirve de 'golden' contra el que se compara
el digitalizador con LLM (docs/diseno-tecnico.md, 7b.4).
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

NUM = r"-?\d{1,3}(?:[.,]\d+)?"
RE_FILA = re.compile(rf"^\s*(?P<represa>[A-Za-zÁÉÍÓÚÑáéíóúñ .]+?)\s+(?P<nums>(?:{NUM}\s+){{2,}}{NUM})\s*$")


def texto_pdf(pdf: str | Path) -> str:
    if not shutil.which("pdftotext"):
        raise RuntimeError("Falta pdftotext (poppler-utils)")
    return subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True,
                          text=True, check=True).stdout


def a_float(s: str) -> float:
    return float(s.replace(",", "."))


def parsear(texto: str) -> list[dict]:
    filas = []
    for linea in texto.splitlines():
        m = RE_FILA.match(linea)
        if m:
            filas.append({"represa": m["represa"].strip(), "valores": [a_float(n) for n in m["nums"].split()],
                          "linea": linea.strip()})
    return filas


def chequear_suma(filas: list[dict], idx_volumen: int, total_reportado: float, tol: float = 0.05) -> dict:
    """La suma de volúmenes útiles por represa debe igualar el total reportado (373,30 hm³ el 13-03-2024)."""
    suma = sum(f["valores"][idx_volumen] for f in filas if "total" not in f["represa"].lower())
    return {"suma": suma, "total_reportado": total_reportado, "ok": abs(suma - total_reportado) <= tol}
