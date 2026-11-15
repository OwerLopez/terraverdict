# Qué falta para terminar TerraVerdict al 100 %

> Actualizado: **15-11-2026** (prioridades 1, 2 y 3 hechas, salvo lo marcado ⏳). Lo hecho y su evidencia está en [`bitacora.md`](bitacora.md).
> Regla para cerrar una tarea: código + pruebas que pasan + entrada en la bitácora + commit en `main`.
> Nada se da por terminado sin evidencia ejecutada.

## Estado al 15-11-2026 (cierre de la sesión)

### Lo que tenemos (verificado)
| Parte | Estado y evidencia |
|---|---|
| Datos reales | NASA POWER (Arequipa, celdas y 25 departamentos), NASA GLC, NASA GIBS (mapa), USGS ComCat, Smithsonian GVP, NOAA ONI y GHCN. Todo con SHA-256 en `data/raw/*/manifiesto.json`; `tv verificar-integridad`: 0 alterados |
| Modelos | 10 redes (MLP, DLinear, LSTM, GRU, TCN convolucional, N-BEATS, N-HiTS, PatchTST, iTransformer, SSM) + clásicos y referencias. Evidencia: IC90 + Diebold-Mariano. Calibración, conformal y abstención |
| Teoría del caos | Validada con Lorenz, Hénon y el mapa logístico. 7 series reales con veredicto global y ahora también **en ventanas deslizantes** (M8) |
| Historial (M8) | Origen móvil 2016–2026 con el diseño congelado. Fuera de muestra: sequía a 1 mes (Ridge 0,711), sequía a 3 meses (ensamble 0,248) y sismos (PatchTST 0,256 bits) **confirmados**; la lluvia a 1 día solo deja un **indicio** (ensamble 0,087) |
| Mapas de calor | `/metricas`: cada métrica (modelo × tarea), importancia de variables (también en `/relevancia`), historial modelo × año y caos serie × ventana. 24 fichas bilingües de métricas |
| Escala nacional | 25 departamentos (`/peru`) |
| Producto | API FastAPI (M1–M8), web React bilingüe ES/EN, accesible y sin desborde en móvil (16 rutas a 390 px) |
| Calidad | Pruebas: ciencia 117 (115 se ejecutan, 2 se omiten por diseño), backend 72, frontend 33, E2E 2 de 2 contra el despliegue emulado. CI en GitHub Actions |
| Despliegue | Docker Compose verificado por el equipo; Vercel listo y verificado en local (`docs/despliegue.md`) |
| Licencias | MIT + atribución de cada fuente + inventario de dependencias. Uso no comercial (hackatón): cubierto también por el Smithsonian GVP |

### Lo que falta
| Tarea | Quién | Detalle |
|---|---|---|
| Publicar en Vercel | DiegoNiS (propietario del repo) u Ower con permisos | Instalar la integración de GitHub de Vercel, importar el repositorio y definir `TV_JWT_SECRETO` (`docs/despliegue.md` §A.1) |
| IMERG completo | Integrante con cuenta Earthdata | `EARTHDATA_TOKEN` en `.env`, luego `tv ingest-fenomenos --solo-adicionales --fuentes imerg` (ver tabla de bloqueos) |
| Asistente conversacional | Equipo (opcional) | Necesita una clave de API del proveedor; el verificador numérico ya funciona sin ella |
| CHIRPS y MODIS | Cualquiera | ClimateSERV y ORNL no son accesibles desde el entorno de trabajo; correr desde otra máquina y repetir `tv experimentos` |
| Fuentes nacionales | Equipo / docentes | SENAMHI, IGP, INGEMMET, ANA: sin API abierta, requieren convenio o descarga manual verificada |
| Redes líquidas (LNN/CfC) | Opcional | No implementadas; la familia convolucional (TCN) sí está |
| Pitch y video de la hackatón | Equipo | Usar `docs/presentacion-ejecutiva.md` y las capturas de `docs/capturas/` |

## Prioridad 1 · Resultados científicos completos

### 1.1 Corrida completa de experimentos · ✅ hecho (15-11-2026, commit de código `41198fe`; ver bitácora)
**Qué falta**
- `tv experimentos` con las 10 redes y varias semillas: lluvia 2 semillas; sequía y sismos 3.
- Resultado esperado: `resultados/*.json` con la procedencia de cada experimento.
- Las cifras de la bitácora son de corridas de prueba con un zoológico reducido.

**Cómo**
```bash
python -m venv .venv && . .venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -e ".[dev,ml]"
tv ingest-fenomenos      # descarga real (unos minutos)
tv experimentos          # corrida completa (aprox. 30–60 min en CPU de 4 núcleos)
```

**Criterio de aceptación**
- `resultados/indice.json` lista seis experimentos: volcanes, deslizamientos, sismos, sequía, lluvia y caos.
- Cada uno con `procedencia.commit` y los hashes de los crudos.

### 1.2 Caos en series reales · ✅ hecho (15-11-2026; ver bitácora)
**Qué falta.** Está incluido en `tv experimentos`, salida `resultados/caos.json`. Series:
- lluvia por péntadas;
- temperatura diaria;
- SPI-3;
- ONI;
- conteo sísmico mensual;
- intereventos sísmicos.

**Criterio.** Cada serie tiene un veredicto (`lineal_estocastica`, `no_lineal_sin_caos_demostrado`, `compatible_con_caos_baja_dimension`, `regular` o `insuficiente`) con sus p-valores, D2, λ y K.

**Nota.** El método ya está validado: 14 pruebas con Lorenz, Hénon, logístico, AR(1) y seno.

### 1.3 Informe de experimentos · ✅ hecho (15-11-2026, `docs/experimentos.md`; ver bitácora)
**Qué falta.** `docs/experimentos.md` generado desde `resultados/*.json`, con:
- tabla por fenómeno: modelo, habilidad en validación, habilidad en prueba con IC90 y Diebold-Mariano;
- ablaciones, ventana elegida, variables seleccionadas, calibración y abstenciones;
- limitaciones.

**Regla.** Solo cifras que estén en los JSON.

### 1.4 Pruebas del motor · ✅ hecho (15-11-2026, ver bitácora)
**Qué falta.** Hoy hay pruebas de caos y de tendencias. Faltan pruebas unitarias de:
- `evaluacion/metricas.py`: habilidad = 0 frente a sí misma; Diebold-Mariano con pérdidas iguales;
- `incertidumbre.py`: cobertura conformal con datos intercambiables;
- `seleccion/variables.py`: descarta una variable de ruido;
- `senales/procesamiento.py`: SPI ≈ N(0,1) en el entrenamiento;
- `experimentos/comun.py`: sin fuga de datos entre particiones.

Y una prueba de humo de cada experimento con datos reducidos guardados en `tests/fixtures/`.

## Prioridad 2 · Integración con el producto

### 2.1 Backend · ✅ hecho (15-11-2026; ver bitácora)
1. Nuevos tipos de resultado en el contrato de expedientes:
   - `caos` (diagnóstico de dinámica);
   - `comparacion_modelos` (zoológico, ablaciones, calibración);
   - `recurrencia` (volcanes);
   - `sismicidad` (Mc, b, tasas);
   - `pronostico`, que ya existe: revisar que tenga intervalo conformal y abstención.
2. Adaptador `src/terraverdict/publicar/` que publique `resultados/*.json` con `POST /api/v1/expedientes` y una clave de servicio de alcance `ingesta`. Debe ser idempotente por hash de contenido (ADR-020).
3. Adaptador del `Expediente` de tendencias del paquete (`expedientes/*.json`) al contrato del backend.
4. Endpoints de lectura:
   - `GET /api/v1/fenomenos` (catálogo de `config/fenomenos.yaml`);
   - capas para el mapa: sismos M ≥ 5, volcanes y deslizamientos, en GeoJSON.
5. Pruebas, `python -m app.cli exportar-openapi`, prueba de deriva y `npm run api:tipos`.

### 2.2 Frontend: rediseño *glassmorphism* monocromático azul · ✅ hecho (15-11-2026; capturas en `docs/capturas/`)
1. Tokens monocromáticos azules con degradados.
2. Paneles de vidrio esmerilado: `backdrop-filter`, borde blanco translúcido y sombra suave.
3. Fondo con cintas azules difuminadas y líneas finas blancas.
4. Modo oscuro azul profundo.
5. Vistas nuevas:
   - **Fenómenos**: catálogo y variables con su justificación;
   - **Sismos**: mapa por magnitud y profundidad, b-value y tasas;
   - **Volcanes**: historia eruptiva y probabilidad anual con IC;
   - **Caos**: espacio de fases, gráfico de recurrencia y distribución de sustitutos;
   - **Modelos**: comparación con IC, confiabilidad, importancia de variables, intervalos e incertidumbre.
6. Aviso permanente: *"Resultados experimentales. No son alertas oficiales (SENAMHI, IGP, INGEMMET, INDECI)."*
7. Revisión visual con capturas en claro, oscuro y móvil.
8. Accesibilidad: contraste, foco, `aria` y tabla de datos de cada gráfico.

## Prioridad 3 · Calidad, despliegue y documentación

| Tarea | Detalle |
|---|---|
| ✅ CI | `.github/workflows/ci.yml` en tres trabajos. Backend: ruff, mypy y pytest. Ciencia: ruff, mypy y pytest. Frontend: typecheck, lint, test y build. **Hecho:** 15-11-2026; también verifica que los tipos del frontend coinciden con el OpenAPI |
| ✅ Docker | `backend/Dockerfile`: migrar, importar y uvicorn. `frontend/Dockerfile`: build con nginx y proxy de `/api`. `docker-compose.yml` con perfil PostgreSQL. `.env.example`. **Hecho y verificado (15-11-2026):** `docker compose up --build` con la API sana (healthcheck), nginx con proxy `/api` y rutas de la SPA, 13 expedientes publicados con `tv publicar --api http://localhost:8080`, persistencia tras reiniciar y E2E 2 de 2 contra el despliegue. Falta probar el perfil `postgres` |
| ✅ Extremo a extremo | Playwright: iniciar sesión, ver el panel, abrir un expediente y comprobar que el verificador marca una cifra sin respaldo. **Hecho (15-11-2026):** `frontend/e2e/recorrido.e2e.ts` (`npm run e2e`). Levanta su propio backend con SQLite temporal, o usa `E2E_BASE_URL` para probar otro despliegue; también pasa contra docker compose. Trabajo `e2e` en CI |
| ✅ `docs/api/README.md` | Endpoints, autenticación y códigos de error con anclas `#errores-<codigo>`. Las URL `type` de los errores ya apuntan ahí. **Hecho:** 15-11-2026; una prueba del backend exige un ancla por cada código de error |
| ✅ `docs/integracion-ciencia-datos.md` | Contratos de series, expedientes y procesos; protocolo del trabajador; unidades e identificadores. `backend/app/main.py` ya lo enlaza. **Hecho:** 15-11-2026; incluye la tabla resultados → expedientes de `tv publicar` |
| ✅ `backend/README.md` | Instalación, variables `TV_*` y comandos. `backend/pyproject.toml` lo declara. **Hecho:** 15-11-2026 |
| ✅ `docs/arquitectura.md` | Vista completa: ciencia → API → web, con diagramas mermaid y flujos. **Hecho:** 15-11-2026 |
| ✅ `docs/metodologia.md` | Métodos estadísticos y de caos con bibliografía verificable. Las referencias ya están en los docstrings de cada módulo. **Hecho:** 15-11-2026; cada método con su módulo y su DOI o arXiv |
| ✅ Matriz de trazabilidad | Requisito → código → prueba → resultado. **Hecho:** 15-11-2026, `docs/trazabilidad.md` (28 requisitos) |
| ✅ Métricas e historial (M8) | Mapas de calor por métrica, importancia de variables, historial año a año por origen móvil y caos en ventanas deslizantes, con 24 fichas de métricas. **Hecho:** 15-11-2026 (ver bitácora). Pendiente opcional: repetir el historial con CHIRPS cuando ClimateSERV sea accesible (`tv ingest-fenomenos` y `tv experimentos --solo historial`) |
| ✅ Licencias | `LICENSE` MIT; términos y cita de cada fuente en `docs/licencias-y-atribuciones.md`; inventario generado de las dependencias en `docs/licencias-terceros.md`; prueba que exige atribución para cada fuente de `data/raw`. **Hecho:** 15-11-2026. Queda ⚠️ confirmar el texto vigente de Mapzen Terrain Tiles y la licencia del IGP antes de usar sus datos |
| ✅ Presentación ejecutiva | Valor tecnológico, científico y económico. Usar solo cifras citadas (p. ej. MERESE US$ 1,5 M, población afectada > 70 %); sin proyecciones inventadas. **Hecho:** 15-11-2026, `docs/presentacion-ejecutiva.md` |

## Bloqueos externos (no dependen del código)

| Bloqueo | Qué se necesita | Quién |
|---|---|---|
| Despliegue en Vercel | El repositorio está listo y verificado en local (`docs/despliegue.md`). Falta que una cuenta con permisos sobre `DiegoNiS/terraverdict` instale la integración de GitHub de Vercel, importe el proyecto y defina `TV_JWT_SECRETO` | DiegoNiS (propietario del repositorio) u Ower con acceso |
| IMERG por Earthdata | Licencia aceptada y acceso verificado el 15-11. Rango V07 Final: 1998-01-01 a 2025-09-30. Estado: solo 1998 descargado; la corrida se detuvo con 401 de GES DISC (probable límite de tasa, no comprobado). El cliente ahora reintenta 401/429/5xx con espera exponencial, usa 4 hilos (antes 12) y el comando termina con código 1 si la descarga no se completa. Pasos: (1) comprobar acceso con una consulta usando `token_earthdata()`; (2) `tv ingest-fenomenos --solo-adicionales --fuentes imerg` (retoma desde 1999); (3) si el 401 persiste, bajar `hilos` en `descargar_imerg`; (4) `tv experimentos --solo fuentes`, `tv informe`, commit de `data/raw/imerg/manifiesto.json`, `resultados/` y `docs/experimentos.md`, y `tv publicar --exportar resultados/contrato/expedientes.json` | Integrante con `EARTHDATA_TOKEN=` en `.env` (nunca en git) |
| MODIS LST (ORNL DAAC) | **Para los próximos integrantes:** el 15-11, la API de subconjuntos de ORNL (`modis.ornl.gov/rst`) tardaba ~1 min por consulta y luego devolvió 502 sostenidos, incluso con 4 hilos. No es un problema del código ni de credenciales (no requiere cuenta). Antes de reintentar, probar `curl -s https://modis.ornl.gov/rst/api/v1/products`; si responde rápido, correr `tv ingest-fenomenos --solo-adicionales --fuentes modis` (4 hilos; no subirlos: con 20 el servidor respondió 502) y después `tv experimentos --solo fuentes` y `tv informe`. Alternativa sin ORNL: AppEEARS (LP DAAC), que exige usuario y contraseña de Earthdata, no solo el token. MODIS solo alimenta el contraste de fuentes (control de calidad); ningún modelo depende de él | Cualquiera, cuando ORNL responda |
| SENAMHI, IGP/OVS, INGEMMET, ANA, CENEPRED, SINIA | Sin API accesible (ver `auditoria-repositorio.md`): convenio o descarga manual verificada | Equipo / docentes |
| Serie de volumen de las represas | AUTODEMA publica reportes aislados en PDF: transcribir más reportes con su fuente | Equipo |
| Deslizamientos | Solo 28 eventos por lluvia en el GLC: el sistema se abstiene de estimar umbrales hasta tener ≥ 30 (inventario INGEMMET) | Integración nacional |

## Decisiones pendientes del equipo

- [ ] ¿Retirar `web/`? Está superado por `frontend/` (ADR-016, paso 2). Por ahora se conserva.
- [ ] ¿Borrar la rama remota `feat/architecture`? Su aporte ya está en `main` (`c3722cc`). Por ahora se conserva.
- [x] Congelar `preregistro.yaml` (2026-11-15, `estado: congelado`).
- [x] Confirmar las particiones temporales de `config/fenomenos.yaml` (congeladas el 2026-11-15).
