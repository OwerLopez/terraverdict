# Backend de TerraVerdict (API REST)

API FastAPI que publica los resultados científicos del proyecto con su procedencia: catálogo de
fuentes verificadas, series, **expedientes inmutables** (con reglas de publicación validadas en el
esquema), procesos, capas del mapa y un verificador numérico para el asistente.
Contrato y errores: [`docs/api/README.md`](../docs/api/README.md) y [`openapi.json`](../docs/api/openapi.json).

## Instalación

Requiere Python ≥ 3.11.

```bash
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"            # agregar ",postgres" para usar PostgreSQL
python -m app.cli migrar           # crea o actualiza el esquema (Alembic)
python -m app.cli importar         # carga los datos reales del repositorio (idempotente)
TV_ADMIN_PASSWORD='…' python -m app.cli crear-admin --email admin@ejemplo.pe
uvicorn app.main:app --reload      # http://localhost:8000/api/docs
```

`importar` lee solo archivos versionados con fuente rastreable:
- catálogos de `config/` (fuentes, variables, problemas y dominios);
- evidencia de verificación de `docs/verificacion/`;
- eventos citados de `datos/eventos/`;
- reporte de AUTODEMA transcrito;
- análisis preliminar.

## Variables de entorno (`TV_*`)

Se leen del entorno o de `backend/.env` (no se versiona).

| Variable | Valor por defecto | Uso |
|---|---|---|
| `TV_ENTORNO` | `desarrollo` | `desarrollo`, `pruebas` o `produccion`. En producción se exige un secreto JWT de ≥ 32 caracteres y CORS sin `*` |
| `TV_DATABASE_URL` | `sqlite:///backend/terraverdict.db` | URL de SQLAlchemy, p. ej. `postgresql+psycopg://usuario:clave@host/terraverdict` |
| `TV_JWT_SECRETO` | valor solo para desarrollo | Firma de los tokens |
| `TV_JWT_ALGORITMO` | `HS256` | `HS256`, `HS384` o `HS512` |
| `TV_JWT_MINUTOS` | `60` | Vigencia del token (5–1440) |
| `TV_CORS_ORIGENES` | `["http://localhost:5173","http://127.0.0.1:5173"]` | Orígenes permitidos (lista JSON) |
| `TV_LOGIN_INTENTOS_POR_MINUTO` | `10` | Límite de inicios de sesión por IP |
| `TV_RAIZ_DATOS` | raíz del repositorio | De dónde se leen `config/`, `datos/` y `docs/verificacion/` |
| `TV_LOG_NIVEL` | `INFO` | Registros JSON con `request_id` |
| `TV_ANTHROPIC_API_KEY` | — | Habilita el asistente; sin ella responde 503 |
| `TV_ADMIN_PASSWORD` | — | Solo para `crear-admin` sin pedir la contraseña por consola |

El pipeline científico usa además `TV_CLAVE_INGESTA` (clave de alcance `ingesta`) para `tv publicar`.

## Comandos

| Comando | Qué hace |
|---|---|
| `python -m app.cli migrar` | Aplica las migraciones de Alembic |
| `python -m app.cli importar` | Importa los datos reales del repositorio |
| `python -m app.cli crear-admin --email …` | Crea el administrador inicial |
| `python -m app.cli crear-clave --nombre pipeline --alcance ingesta` | Crea una clave de servicio (se muestra una vez) |
| `python -m app.cli exportar-openapi` | Escribe `docs/api/openapi.json`; luego `cd frontend && npm run api:tipos` |

## Publicar los resultados científicos

```bash
python -m app.cli crear-clave --nombre pipeline --alcance ingesta   # copiar la clave
cd .. && TV_CLAVE_INGESTA='…' tv publicar --api http://localhost:8000
```

`tv publicar` convierte `resultados/*.json` y `expedientes/*.json` al contrato de expedientes.
Volver a publicar el mismo contenido devuelve los mismos IDs (respuesta 200).

## Calidad

```bash
ruff check app tests && mypy app && pytest
```

Las pruebas usan una base SQLite nueva por prueba, con los datos reales importados. Incluyen las
reglas científicas de cada tipo de expediente, la seguridad (roles, claves y límites) y la deriva
del OpenAPI versionado.
