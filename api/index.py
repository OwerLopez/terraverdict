"""Entrada de Vercel Functions: expone la API FastAPI del backend (`backend/app`).

El código de la API vive en `backend/`; aquí solo se ajusta la ruta de importación y la base por
defecto de un disco efímero. Ver `backend/app/serverless.py` y `docs/despliegue.md`.
"""

import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))

# /tmp es el único directorio escribible en Vercel Functions. Con TV_DATABASE_URL definida
# (PostgreSQL), se usa esa base y los datos persisten entre instancias.
os.environ.setdefault("TV_DATABASE_URL", "sqlite:////tmp/terraverdict.db")
os.environ.setdefault("TV_RAIZ_DATOS", str(RAIZ))
# Producción por defecto: sin TV_JWT_SECRETO (>= 32 caracteres) la función no arranca, en vez de
# firmar sesiones con el secreto de desarrollo.
os.environ.setdefault("TV_ENTORNO", "produccion")

from app.serverless import app  # noqa: E402

__all__ = ["app"]
