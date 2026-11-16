# Traspaso de TerraVerdict · cierre del 15-11-2026 (noche)

Documento para quien continúe el trabajo. Tiene dos partes: el estado verificado y cómo operarlo (§1–§4),
y un **prompt de traspaso** listo para pegar en un asistente de código (§5).

Reglas del proyecto que no cambian:
- Solo datos reales y trazables a fuentes oficiales: NASA, NOAA, USGS y Smithsonian.
- Toda cifra mostrada sale de `resultados/*.json`; ninguna elección se hace mirando la prueba.
- Nada se da por terminado sin evidencia ejecutada.
- Los resultados no son alertas oficiales (SENAMHI, IGP, INGEMMET, INDECI).
- Cada avance lleva código, pruebas, bitácora, pendientes y commit en `main`.

---

## 1. Dónde está todo

| Qué | Dónde |
|---|---|
| Repositorio (owner: Ower Frank) | <https://github.com/OwerLopez/terraverdict> · rama `main` |
| Repositorio original (solo lectura; la cuenta del owner dejó de estar disponible) | <https://github.com/DiegoNiS/terraverdict> · equivalencia de hashes en [`mapa-commits.md`](mapa-commits.md) |
| Aplicación publicada | <https://terraverdict.vercel.app> (proyecto `terraverdict` en la cuenta de Vercel de Ower Frank; cada `push` a `main` despliega) |
| Cifras vigentes | [`experimentos.md`](experimentos.md) (generado por `tv informe`) |
| Qué falta | [`pendientes.md`](pendientes.md) |
| Qué se hizo y cómo se verificó | [`bitacora.md`](bitacora.md) |

**Traslado del repositorio (15-11).** El historial de `main` se copió completo a `OwerLopez/terraverdict`
con sus autores, fechas y horas originales; solo se quitaron las líneas `Co-Authored-By` de herramientas de
IA de los mensajes (por eso cambian los hashes, ver `mapa-commits.md`). Los commits posteriores no llevan
firma de IA, por decisión del equipo.

## 2. Estado verificado al cerrar

- **Datos refrescados el 15-11** (todas las fuentes, hasta la fecha de descarga): POWER, ONI, GHCN, USGS
  (hasta el 15-11-2026), GVP, GLC, CHIRPS, IGP, MODIS LST e **IMERG Final diaria completa 1998–2025-09**
  (1998–2001 coinciden bit a bit con la descarga de MaxsForocca).
- **Experimentos regenerados** con una sola corrida y un solo commit (`resultados/indice.json`).
- **M1 · Matriz de Relevancia implementada** para P1 (lluvia extrema en la cabecera, objetivo IMERG).
- **Asistente "Terra" con Google Gemini**, flotante en todas las páginas y en español e inglés, anclado en
  expedientes y verificado cifra por cifra; "Explicación en lenguaje claro" en cada expediente.
- **Web bilingüe**: interfaz y textos de datos (glosario validado de `scripts/glosario_en.py`).
- **Procesos**: la API muestra las ejecuciones reales del pipeline (descargas y corridas).
- **Despliegue** en Vercel verificado en producción (API, SPA, cabeceras de seguridad y CSP).
- Pruebas, integridad y CI: ver la entrada de cierre de [`bitacora.md`](bitacora.md).

## 3. Cómo operarlo

### 3.1 Entorno (Windows o Linux)
```bash
python -m venv .venv && . .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -e ".[dev,ml]" && pip install -e "backend[dev]"
pytest && tv verificar-integridad
cd backend && python -m venv .venv && .venv/bin/pip install -e ".[dev]" && .venv/bin/pytest && cd ..
cd frontend && npm ci && npm run typecheck && npm run lint && npm test && npm run build && npm run e2e -- --trace off
```
- **Windows:** el repositorio trae `.gitattributes` (LF) y todo el código lee y escribe en UTF-8, así que
  ya no hace falta `PYTHONUTF8`. Si un clon antiguo marca resultados "alterados", es el CRLF: `git config
  core.autocrlf false` y `git checkout -- .` (el contenido es el mismo; lo comprueba el SHA-256).
- Con Node 26, `npm test` necesita `NODE_OPTIONS=--no-experimental-webstorage` (CI usa Node 22).

### 3.2 Secretos (solo en `.env` o en el panel de Vercel; nunca en git)
| Variable | Para qué | Dónde |
|---|---|---|
| `EARTHDATA_TOKEN` | Descargar IMERG (la cuenta acepta una vez la EULA de GES DISC) | `.env` |
| `TV_GEMINI_API_KEY` | Asistente con Gemini | `.env` (local) y Vercel |
| `TV_JWT_SECRETO` | Sesiones; sin él, producción queda en **modo solo lectura** | Vercel |
| `TV_ADMIN_EMAIL`, `TV_ADMIN_PASSWORD` | Administrador de la demostración | Vercel (opcional) |
| `TV_CLAVE_INGESTA` | `tv publicar --api …` contra una API viva | `.env` (opcional) |

En Vercel: *Settings → Environment Variables* (se puede importar un `.env`) y después *Redeploy*.

### 3.3 Refrescar datos y resultados
```bash
tv ingest-fenomenos                       # todas las fuentes (IMERG ≈ 3–5 min por año; se reanuda)
tv verificar-integridad
tv experimentos                           # ≈ 20 min con 20 núcleos
tv informe
tv publicar --exportar resultados/contrato/expedientes.json   # también escribe ejecuciones.json
pytest
# Con la API local corriendo sobre el contrato nuevo: traducir al inglés los textos nuevos de los datos
python scripts/glosario_en.py --api http://127.0.0.1:8000
```
Haz commit **antes** de `tv experimentos`: cada resultado registra el commit `HEAD` que lo produjo.

### 3.4 Al cambiar el backend o los esquemas
```bash
cd backend && .venv/bin/python -m app.cli exportar-openapi --salida ../docs/api/openapi.json
cd frontend && npm run api:tipos
```

## 4. Decisiones tomadas al cierre (con su porqué)
1. **Mc sísmica = 4,5 como limitación declarada** (no se cambia después de ver que el conteo no se
   confirma; el preregistro está congelado). Detalle: [`auditoria-metricas.md`](auditoria-metricas.md) §12.
2. **39 sustitutos por ventana** en el caos en ventanas: lectura descriptiva (§12 de la auditoría).
3. **M1 · significancia condicional por variable** en lugar de desplazar el objetivo: con el objetivo
   desplazado el modelo nulo era más débil y el ruido salía significativo (comprobado con datos sintéticos).
4. **IMERG diario completo** (no una muestra): con 4 hilos se descargó a ≈ 3–5 min por año, no 45.
5. **Producción sin `TV_JWT_SECRETO` = solo lectura** en lugar de no arrancar: la consulta pública sigue
   disponible y no se emite ni acepta ningún token.

---

## 5. Prompt de traspaso (para pegar en el asistente)

```text
# Traspaso de TerraVerdict (NASA Space Apps 2026, reto "Be An Earth System Trend Detective!", Arequipa)

## Contexto
- Repositorio: OwerLopez/terraverdict (owner Ower Frank); se trabaja en `main`. Publicado en
  https://terraverdict.vercel.app (cada push a main despliega). El repositorio original
  DiegoNiS/terraverdict es solo de lectura; equivalencia de hashes en docs/mapa-commits.md.
- Equipo: Ower Frank, MaxsForocca y DiegoNiS.
- Reglas: solo datos reales y trazables (NASA, NOAA, USGS, Smithsonian); toda cifra sale de
  resultados/*.json; nada se elige mirando la prueba; nada se declara terminado sin evidencia ejecutada;
  los resultados no son alertas oficiales; secretos solo en .env o en Vercel; commits sin firma de IA.

## 1. Ponerse al día
git pull --ff-only origin main
Lee: docs/traspaso.md, docs/pendientes.md, la primera entrada de docs/bitacora.md, docs/experimentos.md,
docs/auditoria-metricas.md (§11–12), docs/modulo-relevancia.md y config/modelos.yaml.
Entornos y pruebas: docs/traspaso.md §3.1. Integridad: tv verificar-integridad (código 0).

## 2. Qué hay
Ingesta trazable (SHA-256), 10 redes + clásicos + ensambles con IC90 y Diebold-Mariano, conformal y
abstención, caos validado, historial fuera de muestra 2016–2026, escala nacional (25 departamentos),
M1 (Matriz de Relevancia, P1 con IMERG), asistente Gemini con verificador numérico, API FastAPI y web
React bilingüe, procesos con las ejecuciones reales del pipeline, CSP y cabeceras de seguridad.

## 3. Qué falta (docs/pendientes.md)
Fuentes nacionales (SENAMHI, IGP, INGEMMET, ANA) por convenio; M1 para P2–P4 (requieren NDVI, volumen
de represas y eventos de turbidez); base PostgreSQL para usuarios persistentes en Vercel (opción C);
redes líquidas (opcional).

## 4. Antes de cerrar una sesión
Pruebas completas, tv verificar-integridad, entrada en docs/bitacora.md, docs/pendientes.md al día,
commit en main y push. Si algo queda a medias, detenlo, deja los manifiestos consistentes y actualiza
este traspaso.
```
