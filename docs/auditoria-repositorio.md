# Auditoría y consolidación del repositorio

> **Fecha:** 14 de noviembre de 2026 · **Alcance:** todas las ramas locales y remotas, módulos, datos, documentación, frontend y backend.
> **Regla aplicada:** no perder trabajo, no ejecutar operaciones destructivas sin justificación y dejar cada decisión registrada aquí y en la [bitácora](bitacora.md).

## 1. Ramas

| Rama | Último commit | Contenido | Decisión |
|---|---|---|---|
| `main` | ver `git log` | Propuesta, verificación de fuentes, backend FastAPI, frontend React, motor científico | Rama de trabajo única del equipo |
| `origin/feat/architecture` | `6664d9b` (MaxsForocca) | Construida sobre el historial **anterior** a la limpieza de autoría; aporta 1 commit nuevo: paquete científico `src/terraverdict`, pruebas, ADR-012 a ADR-019, `preregistro.yaml`, visor `web/` | **Integrada** en `main` con `cherry-pick` como `c3722cc`, con la autoría de MaxsForocca intacta. No se fusionó la rama completa porque reintroduciría los commits antiguos que el equipo pidió limpiar. La rama remota **se conserva** (borrarla es decisión del equipo) |
| `origin/ower/pensive-curie-ooom0o` | — | Referencia local obsoleta: ya no existe en el remoto | Ninguna acción |

## 2. Inventario de módulos

| Ruta | Qué es | Estado |
|---|---|---|
| `backend/` | API REST FastAPI: catálogo, series, expedientes inmutables, procesos, relevancia, asistente con verificador numérico, auth JWT y claves API | ✅ 51 pruebas |
| `frontend/` | Producto web React + TypeScript (tipos generados del OpenAPI) | ✅ tsc, eslint, 19 pruebas |
| `src/terraverdict/trends/` | Tendencias con Sello de Confianza (MK conservador, ENSO-HAC, sensor, palanca, detectabilidad, independencia) | ✅ pruebas del equipo |
| `src/terraverdict/caos/` | Teoría del caos: Takens, AMI, FNN, D2, Lyapunov, entropías, RQA, sustitutos IAAFT, prueba 0-1 | ✅ 14 pruebas de validación |
| `src/terraverdict/modelos/` | 10 redes (MLP, DLinear, LSTM, GRU, TCN, N-BEATS, N-HiTS, PatchTST, iTransformer, SSM selectivo) | ✅ verificadas en un proceso conocido |
| `src/terraverdict/evaluacion/` | Métricas de habilidad, Diebold-Mariano, bootstrap por bloques, conformal, calibración, deriva, abstención, explicabilidad | ✅ |
| `src/terraverdict/senales/`, `seleccion/` | SPI, climatología, regímenes (PELT), escalas (wavelet), ventana adaptativa, mRMR con prior físico | ✅ |
| `src/terraverdict/experimentos/` | Experimentos reproducibles por fenómeno | ⏳ corrida completa en curso |
| `src/terraverdict/ingest/` | Clientes con manifiesto SHA-256: POWER, ONI, GHCN, USGS, GVP, NASA GLC | ✅ descarga real del 14-11-2026 |
| `web/` | Visor estático del "paso 1" del ADR-016 | ⚠️ Superado por `frontend/` (ver §3) |
| `scripts/` | Análisis preliminar, verificación de fuentes y enlaces | ✅ |

## 3. Duplicaciones y deuda técnica

| Hallazgo | Decisión | Justificación |
|---|---|---|
| `configs/` (chili, familias) y `config/` (fuentes, variables, dominios) | Unificado en `config/` con `git mv`; referencias actualizadas | Una sola fuente de configuración |
| `web/` (visor estático) y `frontend/` (producto) | Se **conserva** `web/` marcado como superado | El ADR-016 preveía un paso 2 con FastAPI y MapLibre, que es lo que implementan `backend/` y `frontend/`. Se retira cuando el equipo lo confirme; su historial queda en git |
| `expedientes/*.json` y `web/public/expedientes/*.json` | Se mantienen | Son salidas del pipeline de tendencias; el adaptador al contrato del backend está en la tarea de integración |
| Contrato `Expediente` del paquete científico y contrato del backend | Pendiente: adaptador de publicación | El backend tiene el contrato tipado y validado; el paquete publicará por `POST /api/v1/expedientes` con clave de servicio |
| ADR-014 ("sin base de datos") y backend con base de datos | Resuelto en ADR-020 | Los crudos siguen en archivos con hash; los resultados se sirven desde la API |
| Lint y tipos del código integrado | Corregidos sin cambiar comportamiento | `ruff` y `mypy` limpios en 61 archivos |
| `datos/` (curados, versionados) y `data/` (espacio de trabajo del pipeline) | Se mantienen ambos, con roles distintos | `datos/` guarda insumos curados pequeños; `data/raw` guarda descargas regenerables (solo manifiestos en git) |

## 4. Acceso real a fuentes por fenómeno (14-11-2026)

Evidencia: [`verificacion/fuentes_fenomenos.json`](verificacion/fuentes_fenomenos.json) y `data/raw/registro_descarga.json`.

| Fuente | Resultado | Uso |
|---|---|---|
| NASA POWER (diario y mensual) | ✅ 16 740 días por punto, sin faltantes salvo radiación 1981–1983 | Lluvia, sequía, caos |
| NOAA CPC ONI | ✅ 1950–2026 | Predictor de gran escala |
| NOAA GHCN-Daily Arequipa | ✅ con huecos (14 años casi completos de lluvia) | Contraste de calidad |
| USGS ComCat (FDSN) | ✅ 4052 sismos M ≥ 4 a 350 km, 1973–2026 | Sismos |
| Smithsonian GVP (WFS) | ✅ 13 volcanes, 80 registros de erupción | Volcanes |
| NASA Global Landslide Catalog | ✅ 58 eventos en Perú (2007–2009) | Deslizamientos |
| SENAMHI | ❌ el servidor corta la conexión | Integración por convenio o descarga manual |
| IGP (sismos, OVS) | ❌ el origen no responde (502) | Ídem |
| INGEMMET GEOCATMIN | ❌ cadena de certificado SSL incompleta | Ídem; no se desactivó la verificación |
| ANA SNIRH, CENEPRED SIGRID | ⚠️ portales interactivos sin API | Ídem |
| SINIA | ❌ firewall (403) | Ídem |
