# Qué falta para terminar TerraVerdict al 100 %

> Actualizado: **15-11-2026**. Lo hecho y su evidencia está en [`bitacora.md`](bitacora.md).
> Regla para cerrar una tarea: código + pruebas que pasan + entrada en la bitácora + commit en `main`.
> Nada se da por terminado sin evidencia ejecutada.

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
| ✅ Docker | `backend/Dockerfile`: migrar, importar y uvicorn. `frontend/Dockerfile`: build con nginx y proxy de `/api`. `docker-compose.yml` con perfil PostgreSQL. `.env.example`. **Hecho:** 15-11-2026; `docker compose config` válido. Las imágenes no se construyeron en este entorno (sin daemon de Docker): verificar con `docker compose up --build` |
| Extremo a extremo | Playwright: iniciar sesión, ver el panel, abrir un expediente y comprobar que el verificador marca una cifra sin respaldo |
| ✅ `docs/api/README.md` | Endpoints, autenticación y códigos de error con anclas `#errores-<codigo>`. Las URL `type` de los errores ya apuntan ahí. **Hecho:** 15-11-2026; una prueba del backend exige un ancla por cada código de error |
| ✅ `docs/integracion-ciencia-datos.md` | Contratos de series, expedientes y procesos; protocolo del trabajador; unidades e identificadores. `backend/app/main.py` ya lo enlaza. **Hecho:** 15-11-2026; incluye la tabla resultados → expedientes de `tv publicar` |
| ✅ `backend/README.md` | Instalación, variables `TV_*` y comandos. `backend/pyproject.toml` lo declara. **Hecho:** 15-11-2026 |
| ✅ `docs/arquitectura.md` | Vista completa: ciencia → API → web, con diagramas mermaid y flujos. **Hecho:** 15-11-2026 |
| ✅ `docs/metodologia.md` | Métodos estadísticos y de caos con bibliografía verificable. Las referencias ya están en los docstrings de cada módulo. **Hecho:** 15-11-2026; cada método con su módulo y su DOI o arXiv |
| Matriz de trazabilidad | Requisito → código → prueba → resultado |
| Presentación ejecutiva | Valor tecnológico, científico y económico. Usar solo cifras citadas (p. ej. MERESE US$ 1,5 M, población afectada > 70 %); sin proyecciones inventadas |

## Bloqueos externos (no dependen del código)

| Bloqueo | Qué se necesita | Quién |
|---|---|---|
| IMERG, MODIS, SMAP y HLS por Earthdata | Cuenta y token de Earthdata (gratis) en el entorno, nunca en el repositorio | Integrante con la cuenta |
| SENAMHI, IGP/OVS, INGEMMET, ANA, CENEPRED, SINIA | Sin API accesible (ver `auditoria-repositorio.md`): convenio o descarga manual verificada | Equipo / docentes |
| Serie de volumen de las represas | AUTODEMA publica reportes aislados en PDF: transcribir más reportes con su fuente | Equipo |
| Deslizamientos | Solo 28 eventos por lluvia en el GLC: el sistema se abstiene de estimar umbrales hasta tener ≥ 30 (inventario INGEMMET) | Integración nacional |

## Decisiones pendientes del equipo

- [ ] ¿Retirar `web/`? Está superado por `frontend/` (ADR-016, paso 2). Por ahora se conserva.
- [ ] ¿Borrar la rama remota `feat/architecture`? Su aporte ya está en `main` (`c3722cc`). Por ahora se conserva.
- [x] Congelar `preregistro.yaml` (2026-11-15, `estado: congelado`).
- [x] Confirmar las particiones temporales de `config/fenomenos.yaml` (congeladas el 2026-11-15).
