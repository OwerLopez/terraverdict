# Despliegue

> Actualizado: 15-11-2026. Aquí se distingue lo **verificado** de lo que **requiere una acción de una persona**.

TerraVerdict tiene tres formas de desplegarse. Todas sirven los mismos resultados científicos: la API importa al arrancar el contrato `resultados/contrato/expedientes.json`, que exporta el pipeline. El servidor no necesita el paquete científico ni los crudos.

| Opción | Para qué | Persistencia | Estado |
|---|---|---|---|
| **A. Vercel** (estáticos + función Python) | Demostración pública con URL | Solo lectura: cada instancia arma su SQLite en `/tmp` | ✅ Configuración en el repo y verificada en local · ⏳ falta conectar el repositorio a Vercel (ver §A.1) |
| **B. Docker Compose** | Servidor propio o máquina del equipo | Volumen SQLite, o PostgreSQL con el perfil `postgres` | ✅ Verificado por el equipo (`docker compose up --build`, E2E 2 de 2) |
| **C. Vercel + PostgreSQL** | Producción con usuarios y claves persistentes | PostgreSQL gestionado | ⏳ Igual que A, más `TV_DATABASE_URL` |

## A. Vercel

### Qué hay en el repositorio
- `vercel.json`:
  - construye el frontend (`frontend/dist`);
  - define la función `api/index.py`;
  - redirige `/api/*` a la función y el resto a `index.html` (rutas de la SPA);
  - marca los recursos con caché inmutable.
- `api/index.py`: importa la API de `backend/app` mediante `backend/app/serverless.py`. En cada arranque en frío:
  1. migra;
  2. importa catálogos, eventos y el contrato científico;
  3. crea el administrador si existen `TV_ADMIN_EMAIL` y `TV_ADMIN_PASSWORD`.
- `api/requirements.txt`: dependencias de la función, fijadas a las versiones con las que pasan las pruebas del backend (73 al 2026-11-15). Una prueba (`tests/integridad/test_despliegue.py`) exige que cubran todo `backend/pyproject.toml`.

### Verificación realizada (local, Python 3.12, el que usa Vercel por defecto)
- Entorno nuevo con solo `api/requirements.txt`, en modo producción, con `/tmp` vacío.
- Arranque en frío hasta la primera respuesta: **3,1 s**, incluidas la migración y la importación.
- Respuestas reales:
  - `/api/v1/nacional`: 25 departamentos;
  - capa de sismos: 625 eventos;
  - volcanes: 13;
  - deslizamientos: 28;
  - inicio de sesión del administrador definido por variables;
  - cabecera HSTS activa.
- Emulación del enrutado de `vercel.json` (estáticos, *fallback* de SPA y `/api`): **E2E de Playwright 2 de 2**.
- Sin `TV_JWT_SECRETO`, la función **no arranca** (falla la validación de producción), en vez de usar el secreto de desarrollo.

**No verificado todavía:** una compilación real en la infraestructura de Vercel.

### A.1 Acción pendiente de una persona
El 15-11, Vercel respondió *"To link a GitHub repository, you need to install the GitHub integration first"*. Una cuenta con permisos sobre el repositorio debe hacer lo siguiente:

1. En Vercel, **Add New → Project → Import Git Repository**. Autorizar la app de Vercel en GitHub para `DiegoNiS/terraverdict`. Como el repositorio es de DiegoNiS, la autorización la da esa cuenta o una organización que lo incluya.
2. Dejar la raíz del proyecto en la raíz del repositorio. `vercel.json` ya define la instalación, la compilación y la salida.
3. Definir las variables de entorno:

   | Variable | Valor | Obligatoria |
   |---|---|---|
   | `TV_JWT_SECRETO` | Resultado de `python -c "import secrets; print(secrets.token_urlsafe(48))"` (no se guarda en git) | Sí |
   | `TV_ADMIN_EMAIL`, `TV_ADMIN_PASSWORD` | Administrador de la demostración (contraseña de 12 o más caracteres) | No |
   | `TV_DATABASE_URL` | `postgresql+psycopg://…` para persistir (opción C; agregar `psycopg[binary]` a `api/requirements.txt`) | No |

   `TV_ENTORNO=produccion` ya viene por defecto en `api/index.py`.
4. Desplegar. Comprobar con:
   ```bash
   curl -s https://<proyecto>.vercel.app/api/v1/salud/lista
   ```
   ```bash
   E2E_BASE_URL=https://<proyecto>.vercel.app E2E_EMAIL=<admin> E2E_CONTRASENA=<clave> npm --prefix frontend run e2e -- --trace off
   ```

Después de conectar el repositorio, cada `push` a `main` despliega solo.

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
