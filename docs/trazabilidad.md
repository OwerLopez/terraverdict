# Matriz de trazabilidad

Cada requisito del proyecto apunta al código que lo implementa, a la prueba automática que lo
verifica y al resultado o documento donde se ve. Una fila sin prueba no se considera cumplida.

| # | Requisito | Código | Prueba | Resultado / evidencia |
|---|---|---|---|---|
| R1 | Solo datos reales, con procedencia verificable de cada crudo | `src/terraverdict/ingest/*`, `ingest/manifest.py` | `tests/unit/test_ingesta_fuentes_nuevas.py`; humo sobre el recorte real con `origen.json` | `data/raw/*/manifiesto.json`, `data/raw/registro_descarga.json` |
| R2 | Todas las fuentes accesibles; los bloqueos se registran, no se ocultan | `ingest/fenomenos.py` (`_paso`, `registrar_desde_manifiestos`) | `test_ingesta_fuentes_nuevas.py` (formato real de cada API) | `registro_descarga.json` (IMERG con su evidencia); `config/fenomenos.yaml` → `acceso_fuentes_nacionales` |
| R3 | Reglas fijadas antes de evaluar (preregistro y partición congelados) | `preregistro.yaml`, `config/fenomenos.yaml` | `tests/unit/test_preregistro_congelado.py` | Hash en cada expediente y en cada `resultados/*.json` → `procedencia.preregistro_sha256` |
| R4 | Sin fuga de datos entre entrenamiento, validación y prueba | `experimentos/comun.py` (`construir`, `evaluar_zoo`), `senales/procesamiento.py` | `tests/motor/test_comun_modelos.py`, `test_seleccion_senales.py` (SPI y climatología sin fuga) | Particiones por fecha del objetivo en `docs/experimentos.md` |
| R5 | Habilidad siempre frente a referencias, con IC y prueba de significancia | `evaluacion/metricas.py` | `tests/motor/test_metricas.py` | Tablas por modelo en `docs/experimentos.md` |
| R6 | Incertidumbre calibrada y medida | `evaluacion/incertidumbre.py` | `tests/motor/test_incertidumbre.py` (cobertura conformal ≥ 90 %) | Cobertura en prueba (sequía) y ECE (lluvia) |
| R7 | Abstención explícita y motivada | `incertidumbre.decidir_abstencion`, `experimentos/deslizamientos.py`, `volcanes.py` | `test_incertidumbre.py::test_abstencion`; backend `test_fenomenos.py::test_abstencion_siempre_motivada` | Sección "Publicación" de cada fenómeno |
| R8 | Selección de variables con plausibilidad física | `seleccion/variables.py` | `test_seleccion_senales.py` (ruido, redundancia, escala) | Variables y descartadas por fenómeno |
| R9 | Zoológico de 10 redes reproducible | `modelos/redes.py`, `modelos/entrenamiento.py` | `test_comun_modelos.py` (forma, referencia y reproducibilidad) | Dispersión entre semillas en las tablas |
| R10 | Caos solo con evidencia completa | `caos/*` | `tests/caos/test_validacion_sistemas.py` (Lorenz, Hénon, logístico, AR(1), seno); backend `test_caos_exige_todas_las_condiciones` | `resultados/caos.json` |
| R11 | Sismos y volcanes sin pronósticos falsos | `experimentos/sismos.py`, `volcanes.py` | Humo `test_sismos`, `test_volcanes`; backend `es_pronostico: false` | `resultados/sismos.json`, `volcanes.json` |
| R12 | Resultados robustos a la fuente de datos | `experimentos/fuentes.py`; variantes `*_chirps` | `test_humo.py::test_contraste_de_fuentes`, `test_lluvia_con_chirps`, `test_sequia_con_chirps` | `resultados/fuentes.json` y la sección "Contraste entre fuentes" |
| R13 | Informe solo con cifras de los resultados | `experimentos/informe.py` (`tv informe`) | `tests/integracion/test_publicacion.py::test_informe_solo_con_cifras_de_los_json` | `docs/experimentos.md` |
| R14 | Publicación idempotente y con reglas científicas en el backend | `publicar/*`, `backend/app/schemas/expedientes.py` | `test_publicacion.py::test_publicacion_idempotente_en_el_backend`; backend `test_fenomenos.py` | `POST /api/v1/expedientes` (201/200/422) |
| R15 | Expedientes inmutables con procedencia completa | `backend/app/services/expedientes.py` | backend `test_expedientes.py` | `GET /api/v1/expedientes/{id}` |
| R16 | Catálogo de fenómenos y capas del mapa desde expedientes | `backend/app/api/v1/fenomenos.py` | backend `test_catalogo_de_fenomenos`, `test_capas_*` | `GET /fenomenos`, `/capas/*` |
| R17 | Contrato API versionado y tipos del frontend sincronizados | `docs/api/openapi.json`, `frontend/src/api/esquema.d.ts` | backend `test_openapi_versionado_coincide_con_el_codigo`; CI `git diff --exit-code` de los tipos | `docs/api/README.md` |
| R18 | Seguridad: roles, claves de servicio, límites, errores RFC 9457 | `backend/app/core/*`, `api/deps.py` | backend `test_sistema_y_seguridad.py` | `docs/api/README.md#errores` |
| R19 | Verificador: ninguna cifra sin respaldo | `backend/app/services/verificador.py` | backend `test_verificador.py` | `POST /asistente/verificar` |
| R20 | Aviso permanente de no oficialidad | `frontend/src/componentes/Marco.tsx` (`AvisoNoOficial`); `backend` (`aviso` del catálogo) | `frontend/src/test/fenomenos.test.tsx` | Todas las vistas |
| R21 | Accesibilidad de los gráficos | `frontend/src/componentes/fenomenos/TablaDatos.tsx` | `fenomenos.test.tsx` (tabla por gráfico, texto en los estados) | Vistas Sismos, Volcanes, Caos y Modelos |
| R22 | Tendencias con Sello de Confianza | `trends/*`, `expedientes/*` | `tests/unit/test_sello.py`, `test_golden_preliminar.py` | `expedientes/*.json` |
| R23 | Integración continua | `.github/workflows/ci.yml` | Los tres trabajos (backend, ciencia, frontend) | Pestaña Actions del repositorio |
