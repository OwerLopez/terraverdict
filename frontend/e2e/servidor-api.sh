#!/usr/bin/env sh
# Backend aislado para la prueba E2E: base SQLite temporal, datos reales del repositorio y un admin.
# Lo arranca Playwright (playwright.config.ts → webServer). Usa backend/.venv si existe.
set -eu
cd "$(dirname "$0")/../../backend"
PY=python
[ -x .venv/bin/python ] && PY=.venv/bin/python
DB="${TMPDIR:-/tmp}/terraverdict-e2e-$$.db"
export TV_DATABASE_URL="sqlite:///$DB" TV_ENTORNO=pruebas TV_LOG_NIVEL=WARNING
export TV_ADMIN_PASSWORD="${E2E_CONTRASENA:-contrasena-e2e-segura}"
"$PY" -m app.cli migrar >/dev/null 2>&1
"$PY" -m app.cli importar >/dev/null
"$PY" -m app.cli crear-admin --email "${E2E_EMAIL:-e2e@terraverdict.pe}" --nombre "Prueba E2E" >/dev/null
exec "$PY" -m uvicorn app.main:app --host 127.0.0.1 --port "${E2E_PUERTO_API:-8799}" --no-access-log
