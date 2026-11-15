# API de TerraVerdict. Contexto de construcción: raíz del repositorio
#   docker build -f backend/Dockerfile -t terraverdict-api .
# Al arrancar: migra el esquema, importa los datos reales versionados (idempotente) y sirve con uvicorn.
# Sin access log de uvicorn: la app ya registra cada solicitud en JSON con su request_id.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TV_RAIZ_DATOS=/srv/terraverdict \
    TV_DATABASE_URL=sqlite:////datos/terraverdict.db

WORKDIR /srv/terraverdict/backend
COPY backend/pyproject.toml backend/README.md ./
COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./
RUN pip install ".[postgres]"

# Datos versionados que importa la API (catálogos, verificación, eventos y reportes citados)
COPY config /srv/terraverdict/config
COPY datos /srv/terraverdict/datos
COPY docs/verificacion /srv/terraverdict/docs/verificacion

RUN useradd --system --uid 10001 tv && mkdir -p /datos && chown tv /datos
USER tv
VOLUME ["/datos"]
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/v1/salud/lista').status == 200 else 1)"
CMD ["sh", "-c", "python -m app.cli migrar && python -m app.cli importar && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --no-access-log"]
