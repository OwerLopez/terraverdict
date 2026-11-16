# Despliegue

> Actualizado: 15-11-2026 (noche). Aquí se distingue lo **verificado** de lo que **requiere una acción de una persona**.

**Producción: <https://terraverdict.vercel.app>** (proyecto `terraverdict` en la cuenta de Vercel de
Ower Frank, enlazado a [`OwerLopez/terraverdict`](https://github.com/OwerLopez/terraverdict): cada `push` a
`main` despliega solo).

TerraVerdict tiene tres formas de desplegarse. Todas sirven los mismos resultados científicos: la API importa al arrancar el contrato `resultados/contrato/expedientes.json`, que exporta el pipeline. El servidor no necesita el paquete científico ni los crudos.

| Opción | Para qué | Persistencia | Estado |
|---|---|---|---|
| **A. Vercel** (estáticos + función Python) | Demostración pública con URL | Solo lectura: cada instancia arma su SQLite en `/tmp` | ✅ Publicado y verificado en producción (15-11-2026) |
| **B. Docker Compose** | Servidor propio o máquina del equipo | Volumen SQLite, o PostgreSQL con el perfil `postgres` | ✅ Verificado por el equipo (`docker compose up --build`, E2E 2 de 2) |
| **C. Vercel + PostgreSQL** | Producción con usuarios y claves persistentes | PostgreSQL gestionado | ⏳ Igual que A, más `TV_DATABASE_URL` |

## A. Vercel

### Qué hay en el repositorio
- `vercel.json`:
  - construye el frontend (`frontend/dist`);
  - define la función `api/index.py` (60 s como máximo);
  - redirige `/api/*` a la función y el resto a `index.html` (rutas de la SPA);
  - cabeceras de seguridad del frontend: CSP estricta (scripts solo propios y el script de tema por su
    hash; imágenes y conexiones solo a NASA GIBS y a los teselados de elevación; `frame-ancestors 'none'`),
    `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy` y COOP. La API añade las
    suyas (CSP `default-src 'none'`, HSTS). Una prueba exige que el hash de la CSP coincida con `index.html`;
  - caché inmutable para `/assets/`.
- `.vercelignore`: Vercel detecta el `pyproject.toml` de la raíz (paquete científico con torch) y lo
  instalaría en la función. Se excluye junto con todo lo que la API no lee; la función usa
  `api/requirements.txt`.
- `api/index.py`: importa la API de `backend/app` mediante `backend/app/serverless.py`. En cada arranque en frío:
  1. migra;
  2. importa catálogos, eventos y el contrato científico;
  3. crea el administrador si existen `TV_ADMIN_EMAIL` y `TV_ADMIN_PASSWORD` (y hay sesiones).
- Ajustes del proyecto en Vercel: *framework* "Other" (con "FastAPI" Vercel ignoraba `vercel.json` e
  instalaba el paquete científico), Node 22 y protección de Vercel solo en las vistas previas (la
  producción es pública).

### Variables de entorno
| Variable | Valor | Efecto si falta |
|---|---|---|
| `TV_GEMINI_API_KEY` | Clave de Google AI Studio | El asistente responde 503 y la web lo muestra "No configurado"; todo lo demás funciona |
| `TV_JWT_SECRETO` | `python -c "import secrets; print(secrets.token_urlsafe(48))"` | **Modo solo lectura**: la API no emite ni acepta tokens (falla cerrada); la consulta pública sigue disponible |
| `TV_ADMIN_EMAIL`, `TV_ADMIN_PASSWORD` | Administrador de la demostración (12 o más caracteres) | No se crea administrador |
| `TV_DATABASE_URL` | `postgresql+psycopg://…` (opción C; agregar `psycopg[binary]` a `api/requirements.txt`) | SQLite efímero en `/tmp` |

`TV_ENTORNO=produccion` ya viene por defecto en `api/index.py`. Los secretos se cargan en *Settings →
Environment Variables* del proyecto (por ejemplo, con **Import .env**); nunca en git. Después hay que
volver a desplegar (*Deployments → Redeploy*) para que la función los lea.

### Verificación en producción (15-11-2026)
- Compilación real en Vercel: correcta en 1 min 19 s (2 núcleos), sin instalar el paquete científico.
- `GET /api/v1/salud/lista` → `{"mensaje":"lista"}`; `/api/v1/expedientes` → 17 expedientes;
  `/api/v1/nacional` (25 departamentos) y `/api/v1/fenomenos` → 200; rutas de la SPA (`/`, `/metricas`) → 200.
- HSTS en todas las respuestas.

Para repetirla:
```bash
curl -s https://terraverdict.vercel.app/api/v1/salud/lista
```
```bash
cd frontend && E2E_BASE_URL=https://terraverdict.vercel.app npm run e2e -- --trace off
```

### Límites de la opción A
- La base vive en `/tmp` de cada instancia. Los usuarios, las claves de API y los expedientes creados por la API **no persisten** entre instancias ni entre despliegues. Para eso está la opción C.
- El límite de intentos de inicio de sesión se cuenta por instancia.

## B. Docker Compose

Ver [`arquitectura.md`](arquitectura.md) y [`../backend/README.md`](../backend/README.md).

```bash
docker compose up --build
```

- La imagen de la API copia el contrato científico (`resultados/contrato/`). `.dockerignore` deja pasar solo esa carpeta de `resultados/`.
- Verificado el 15-11: el contexto de compilación incluye `expedientes.json` con el mismo SHA-256 que el repositorio.
- En este entorno de trabajo no se pudo compilar la imagen completa: el proxy de red usa una CA propia que el contenedor no reconoce, y `pip install` falla. No es un defecto del `Dockerfile`; el equipo ya lo había compilado en su máquina.
