# Bitácora del proyecto TerraVerdict

Registro de cada avance importante, para que todo el equipo sepa **qué hay, cómo se comprobó y qué falta**.
La entrada más reciente va primero. Cada entrada corresponde a uno o más commits en `main` (búscalos con `git log --oneline`).

**Cómo agregar una entrada:** fecha · autor · qué se hizo · evidencia (pruebas, cifras, archivos) · decisiones y por qué · pendientes. Nunca escribir resultados que no se hayan ejecutado.

Lo que falta para terminar está en **[`pendientes.md`](pendientes.md)**.

---

## Estado al 14-11-2026 (resumen para el equipo)

| Parte | Estado | Evidencia | Cómo correrlo |
|---|---|---|---|
| Propuesta y verificación de fuentes | ✅ Hecho | 37/40 consultas a catálogos; 35/40 enlaces con HTTP 200 | `docs/verificacion/` |
| Backend (API REST) | ✅ Hecho | 51 pruebas, ruff y mypy limpios, OpenAPI exportado | `cd backend && pytest` |
| Frontend (web) | ✅ Funcional · ⏳ falta el rediseño *glassmorphism* | tsc, eslint, 19 pruebas | `cd frontend && npm test` |
| Paquete científico de tendencias (Sello) | ✅ Integrado (aporte de MaxsForocca) | 14 pruebas | `pytest tests/unit` |
| Ingesta de cinco fenómenos | ✅ Descarga real con SHA-256 | `data/raw/registro_descarga.json` | `tv ingest-fenomenos` |
| Catálogo de variables y métricas por fenómeno | ✅ | `config/fenomenos.yaml` | — |
| Teoría del caos | ✅ Validada con sistemas de referencia · ⏳ falta correrla en series reales | 14 pruebas en `tests/caos` | `pytest tests/caos` |
| Modelos, evaluación e incertidumbre | ✅ Código y corridas de prueba · ⏳ falta la corrida completa | ver entrada del motor | `tv experimentos` |
| Integración ciencia → backend → frontend | ⏳ Pendiente | — | ver `pendientes.md` |

---

## 2026-11-15 · Más fuentes reales: CHIRPS, IGP, MODIS e IMERG, y experimentos multi-fuente
**Autor:** MaxsForocca · **Aportes:** Ower Frank

**Qué se hizo**
- **Clientes nuevos** en `src/terraverdict/ingest/`. Cada uno guarda el crudo con su SHA-256 y entra en `tv ingest-fenomenos` (y en `--solo-adicionales --fuentes …`):
  - `chirps.py`: CHIRPS v2.0 diario por la API pública de ClimateSERV, sin cuenta, en tramos de ≤ 20 años;
  - `igp.py`: sismos reportados por el IGP, API pública por año;
  - `earthdata.py`: IMERG Final V07 diaria por OPeNDAP con el token de Earthdata, leído del entorno o de `.env` y nunca escrito en crudos ni registros;
  - `modis.py`: MOD11A2 LST por la API de subconjuntos de ORNL DAAC.
- **Experimentos multi-fuente:**
  - lluvia extrema y sequía se repiten con CHIRPS (`lluvia_extrema_chirps`, `sequia_chirps`);
  - el diagnóstico de caos agrega las péntadas de CHIRPS;
  - el nuevo experimento `fuentes` contrasta lluvia (POWER, CHIRPS e IMERG frente a la estación GHCN), temperatura (POWER frente a GHCN y a MODIS LST, en anomalías y tendencias) y sismos (USGS frente a IGP, emparejados por tiempo y lugar).
- **Procedencia:** cada resultado guarda también el SHA-256 del preregistro.
- **Partición:** la de prueba de sequía y sismos sale de la configuración, recortada al último dato disponible. Con la configuración real es la misma de antes (2021-01 a 2025-12 y 2021-01 a 2026-10).
- **Catálogo:**
  - `config/fuentes.yaml` registra las fuentes nuevas;
  - `config/fenomenos.yaml` actualiza el acceso al IGP y a SENAMHI;
  - dos variables de validación que no tenían `justificacion` ahora la tienen (lo detectó el contrato del backend).
- **Fixtures:** `tests/fixtures/raw_reducido` suma recortes reales de CHIRPS (1981–2020 en la cabecera, para que el SPI tenga ≥ 10 años por mes) y del IGP (2012–2020, a 400 km).

**Evidencia** (`data/raw/registro_descarga.json`)
- CHIRPS: 4 series (cabecera y ciudad; caja de 0,1° y celda de POWER), 16 709 días cada una, de 1981-01-01 a 2026-09-30, sin huecos. 12 MB.
- IGP: 8 545 sismos reportados entre 2012-01-07 y 2026-11-15. Hasta 2018 los registros no traen `codigo`: se usa `idlistasismos`, y la prueba incluye un registro de 2013.
- Primeras lecturas del contraste (datos completos; cifras finales en `docs/experimentos.md`):
  - En la cabecera, CHIRPS da 448–470 mm/año y POWER 198 mm/año. r diario 0,29–0,32; r mensual 0,78–0,80.
  - En la ciudad, frente a la estación, ningún producto reproduce la lluvia diaria (r ≈ 0,19–0,20). POWER subestima los totales (razón 0,70) y CHIRPS los sobreestima (1,69–1,87).
  - Sismos IGP frente a USGS: 712 emparejados; M IGP − M USGS = −0,11 ± 0,27.
- `pytest`: 88 pruebas pasan, 1 se omite (requiere R). Incluye las pruebas de humo de `fuentes`, `lluvia_extrema_chirps` y `sequia_chirps`.

**Bloqueos (registrados, no ocultos)**
- **IMERG:**
  - El token es válido: LP DAAC y NSIDC responden 200.
  - GES DISC respondió `403 EULA Acceptance Failure` en el archivo de datos y `401` en OPeNDAP. Al final del día, el servidor no respondía.
  - Acción: el dueño de la cuenta debe aceptar una vez la licencia en https://urs.earthdata.nasa.gov/approve_app?client_id=e2WVk8Pw6weeLUKZYOxvTQ y correr `tv ingest-fenomenos --solo-adicionales --fuentes imerg`.
- **MODIS (ORNL):**
  - Cada consulta tarda cerca de 1 min y la latencia no crece con consultas simultáneas (8 en 49 s).
  - Con 20 simultáneas el servidor respondió 502. El cliente usa ahora 4 hilos y la descarga se reintenta aparte.
  - El contraste `fuentes` funciona con o sin MODIS.
- **SMAP y HLS:** el token tiene acceso, pero no se usan.
  - SMAP empieza en 2015, después del entrenamiento congelado, y solo se distribuye por gránulo global.
  - HLS es reflectancia a 30 m, sin relación directa con estos objetivos.

**Decisiones**
- Las fuentes se agregan **antes** de la corrida completa: así la prueba se usa una vez, con todas las fuentes disponibles.
- Los resultados con POWER y con CHIRPS se informan lado a lado. Un resultado que cambia con el producto no describe a la lluvia, sino al producto.

---

## 2026-11-15 · Corrección de escala en la selección de variables (mRMR)
**Autor:** MaxsForocca · **Aportes:** Ower Frank

**Defecto.** En clasificación (lluvia fuerte) la relevancia es la IM con un evento binario, acotada por la entropía del evento (≈ 0,26 nats con una tasa del 7 %). La redundancia era la IM entre variables continuas, que no tiene esa cota. Al restarlas, casi toda variable salía "redundante" por la diferencia de escala, no por falta de información.

Ejemplo con datos reales (recorte 2008–2020): la humedad específica tenía IM 0,032 frente a un nulo de 0,005 y aun así se descartaba. Esto explica por qué la corrida preliminar del 14-11 solo eligió la historia de lluvia.

**Corrección** (`seleccion/variables.py`)
- La redundancia pasa a ser la |ρ de Spearman| **máxima** con las variables ya elegidas, en [0, 1]. La media diluía la redundancia de una copia de una variable ya elegida.
- Puntaje = peso físico × IM × (1 − redundancia).
- Una variable solo entra si su IM descontada supera la máxima IM de 50 permutaciones del objetivo (≈ p98 del nulo). Con 300 permutaciones se comprobó que el nulo del estimador KSG tiene cola larga.

**Evidencia** (`tests/motor/test_seleccion_senales.py`)
- Con un evento al 9 % y una humedad correlacionada con la historia (ρ = 0,5) pero con señal propia, la humedad entra en **8 de 8** réplicas. Con el método anterior, en **1 de 8**.
- El ruido entra como máximo en 1 de 8.
- Una copia de una variable elegida se descarta.
- 39 pruebas del motor pasan.

---

## 2026-11-15 · Pruebas del motor y de humo de cada experimento (pendiente 1.4)
**Autor:** MaxsForocca · **Aportes:** Ower Frank (motor original)

**Qué se hizo**
- `tests/motor/`: 38 pruebas unitarias con datos sintéticos de respuesta conocida.
  - **Métricas.** Habilidad = 0 frente a sí misma. Diebold-Mariano: con pérdidas iguales no hay prueba (varianza nula); con pérdidas de igual distribución rechaza cerca del 10 % nominal; detecta un modelo mejor.
  - **Bootstrap, contingencia, ECE y Poisson.**
  - **Incertidumbre.** Cobertura conformal ≥ 90 % con datos intercambiables (50 réplicas, errores t de Student), corrección de muestra finita, calibración isotónica, PSI/KS y reglas de abstención.
  - **Selección y señales.** mRMR descarta ruido y redundancia. SPI ≈ N(0,1) en el entrenamiento y sin fuga del futuro. Climatología armónica sin fuga. PELT, wavelets y ventana adaptativa.
  - **Sin fuga entre particiones.** Particiones disjuntas por la fecha del objetivo; normalización solo con el entrenamiento; cambiar el objetivo de prueba no cambia ninguna decisión tomada con validación.
  - **Las 10 redes.** Forma de salida y referencia; entrenamiento reproducible.
- `tests/experimentos/test_humo.py`: los seis experimentos y el orquestador corren de punta a punta sobre `tests/fixtures/raw_reducido/` (unos 34 s).
  - Es un recorte **real** de `data/raw` (2008–2020, 3,7 MB) generado por `scripts/generar_fixtures_experimentos.py`.
  - `origen.json` guarda el SHA-256 de cada crudo original.
- `tv experimentos` acepta otro archivo de configuración (`config=`), para poder probar el orquestador.

**Defectos encontrados y corregidos al escribir las pruebas**
1. **Redes no reproducibles.** En `evaluar_zoo`, la red se creaba **antes** de fijar la semilla: los pesos iniciales dependían del estado previo del generador. Con las mismas entradas, el MLP daba 0,6371 en una corrida y 0,6325 en otra. Ahora se fija la semilla antes de crear cada red.
2. **mRMR admitía ruido.** El estimador KSG de información mutua es positivo incluso con ruido puro (0,0077 en la prueba), así que una variable de ruido entraba. Ahora una variable solo entra si su información mutua supera el percentil 95 del objetivo permutado (20 permutaciones). Las descartadas indican el motivo.

Ambos cambios afectan a las cifras preliminares del 14-11; la corrida completa (1.1) se hace ya con el código corregido.

**Evidencia.** `pytest`: 75 pruebas pasan y 1 se omite (requiere R). `ruff` y `mypy` limpios.

---

## 2026-11-15 · Preregistro y partición temporal congelados
**Autor:** MaxsForocca · **Aportes:** Ower Frank

**Qué se hizo**
- `preregistro.yaml` pasa a `estado: congelado` (2026-11-15). Los cinco valores que estaban *(propuesto)* quedan *(aprobado)* sin cambiar sus cifras.
- La partición temporal de `config/fenomenos.yaml` queda congelada: entrenamiento 1981–2015, validación 2016–2020, prueba 2021–2026-10.
- Se regeneraron los dos expedientes de tendencias: el hash del preregistro es parte de su procedencia.

**Evidencia**
- SHA-256 del preregistro congelado: `c40676fd76ab…d596`.
- `tests/unit/test_preregistro_congelado.py` falla si cambia un solo byte del preregistro o una fecha de la partición. 30 pruebas pasan.
- Los expedientes regenerados dan el mismo resultado que antes (T2M +0,226 °C/década, sello *frágil*; lluvia dic–mar sin tendencia). Solo cambian los hashes y la fecha.

**Decisiones**
- Se congela **antes** de la corrida completa, para que el periodo de prueba se use una sola vez con reglas fijadas de antemano.
- Cambiar un valor ahora exige subir `version` y anotar el motivo aquí.

---

## 2026-11-14 · Motor de pronóstico, evaluación e incertidumbre
**Autor:** Ower Frank

**Qué se hizo**
- `src/terraverdict/modelos/`: 10 arquitecturas en PyTorch (CPU) con su referencia: MLP, DLinear, LSTM, GRU, TCN, N-BEATS, N-HiTS, PatchTST, iTransformer y un SSM selectivo inspirado en Mamba (implementación de referencia, no el núcleo CUDA). Entrenamiento reproducible con semillas y parada temprana.
- `src/terraverdict/evaluacion/`: habilidad frente a climatología y persistencia, Brier, AUC, calibración (ECE), tabla de contingencia, Poisson, IC por *bootstrap* de bloques, prueba de Diebold-Mariano con varianza HAC, intervalos conformales al 90 %, calibración isotónica (solo con validación), deriva (PSI y KS), reglas de abstención e importancia por permutación.
- `src/terraverdict/senales/` y `seleccion/`: SPI con parámetros del entrenamiento, climatología armónica, regímenes con PELT, escalas con wavelets, ventana adaptativa (decorrelación, embedding de Takens y validación) y selección de variables mRMR con el prior físico del catálogo.
- `src/terraverdict/experimentos/`: lluvia fuerte, sequía (SPI-3), sismos, volcanes, deslizamientos y caos en series reales, con un orquestador que guarda la procedencia (hash de cada crudo, commit, configuración y versiones). Comando `tv experimentos`.

**Evidencia preliminar.** Son corridas de prueba con un zoológico reducido de redes y una sola semilla. **No son los resultados finales**; la corrida completa está en `pendientes.md`.

| Fenómeno | Resultado de prueba (periodo de prueba 2021–2026) | Lectura |
|---|---|---|
| Lluvia fuerte t+1 (celda de cabecera, ≥ p90 de dic–mar = 3,22 mm) | Logística: habilidad de Brier 0,112 (IC90 0,044–0,176), Diebold-Mariano p = 0,031 · GRU: 0,117 (0,046–0,178) · persistencia: 0,049 | Habilidad modesta pero significativa a un día |
| Sequía, SPI-3 a 1 mes | Ridge: habilidad 0,68 (IC90 0,54–0,78) frente a persistencia 0,46 | Parte es solapamiento de meses del SPI-3; los modelos superan a la persistencia |
| Sequía, SPI-3 a 3 meses | Habilidad en prueba ≈ 0,05, con un IC que incluye 0 | Sin habilidad confirmada |
| Sismos (USGS, 350 km) | Mc = 4,5; b = 0,997 (IC90 0,96–1,03); CV de intereventos desagrupados = 1,07 | Coherente con Poisson tras desagrupar (valida el método) |
| Conteos sísmicos mensuales | GRU: +0,23 bits/mes frente a Poisson (IC90 0,017–0,50), Diebold-Mariano p = 0,14 | No significativo: no hay pronóstico de sismos |
| Volcanes (GVP, desde 1550) | Ubinas: 4,5 %/año (IC90 3,1–6,4) · Sabancaya: 1,9 % · Misti (a 17,8 km de la ciudad): 0,8 % (0,3–1,9) | Frecuencias históricas, no pronósticos |
| Deslizamientos (NASA GLC) | 28 eventos por lluvia en el sur del Perú | **Abstención**: se necesitan ≥ 30 para un umbral |

**Control de calidad clave.** La celda de POWER de la ciudad frente a la estación GHCN de Arequipa tiene r diario = 0,20 y r mensual = 0,58; el p99 diario es 7,3 frente a 13,6 mm. Por eso la lluvia se modela en la celda de **cabecera** (donde nace el agua y la turbidez) y los resultados se describen a escala regional, no como tormentas puntuales de la ciudad.

**Decisiones**
- La selección automática (mRMR) se quedó solo con la historia de lluvia. La ablación lo respalda: con todas las variables la habilidad baja (logística 0,065 frente a 0,112).
- Las referencias no se recalibran: la climatología vale 0 frente a sí misma.
- La regla de abstención usa solo validación; el periodo de prueba se toca una vez.

---

## 2026-11-14 · Teoría del caos validada con sistemas de referencia
**Autor:** Ower Frank

**Qué se hizo.** `src/terraverdict/caos/` contiene:
- Embedding de Takens: τ con AMI y autocorrelación; m con falsos vecinos.
- Dimensión de correlación de Grassberger-Procaccia, con ventana de Theiler y cota de Eckmann-Ruelle.
- Exponente de Lyapunov de Rosenstein, con región lineal automática.
- Entropía de permutación y entropía muestral.
- Análisis de recurrencias (RQA).
- Sustitutos IAAFT con pruebas por rangos y corrección de Holm-Bonferroni.
- Prueba 0-1.
- Diagnóstico integrado con una regla conservadora: nunca afirma caos sin todas las condiciones.

**Evidencia** (`pytest tests/caos`: 14 pruebas, unos 40 s)

| Sistema de referencia | Valor teórico | Medido |
|---|---|---|
| Mapa logístico r = 4, λ | ln 2 = 0,693 | 0,695 |
| Hénon, D2 / λ | 1,21 / 0,42 | 1,22 / 0,416 |
| Lorenz, D2 / λ (por unidad de tiempo) | 2,05 / 0,906 | ≈ 1,9–2,0 / ≈ 0,86 |
| Prueba 0-1: seno / logístico | 0 / 1 | ≈ 0,00 / ≈ 1,00 |
| Diagnóstico: Hénon, Lorenz | compatible con caos | ✅ |
| Diagnóstico: AR(1), AR(1)³, ruido | lineal estocástico | ✅ |
| Diagnóstico: seno | regular | ✅ |

**Defectos encontrados y corregidos al validar** (por eso se valida antes de usar datos reales)
1. **τ en mapas.** El primer mínimo de la AMI daba τ = 10–18; ahora se toma el mínimo entre AMI y autocorrelación.
2. **Dimensión m.** Con el umbral de falsos vecinos del 5 %, Lorenz salía con m = 2; ahora se exige < 1 %, con meseta para datos ruidosos.
3. **Prueba 0-1 en flujos.** Necesitaba submuestreo por τ.
4. **Saturación falsa de D2.** Sin la cota de Eckmann-Ruelle, el AR(1) "saturaba" cerca de 7.
5. **λ frente a sustitutos.** No sirve como prueba en flujos continuos: daba falso negativo en Lorenz. Ahora decide la predicción por análogos.
6. **Falso positivo de no linealidad.** Dos pruebas sin corrección rechazaban en AR(1)³; se aplica Holm-Bonferroni.

---

## 2026-11-14 · Ingesta trazable de cinco fenómenos y catálogo científico
**Autor:** Ower Frank

**Qué se hizo**
- `config/fenomenos.yaml`: lluvia extrema, sequía, sismos, volcanes y deslizamientos. Cada variable lleva justificación física, fuente, resolución, cobertura, limitaciones y relevancia. Incluye métricas por fenómeno, reglas de abstención y la partición temporal: entrenamiento 1981–2015, validación 2016–2020, prueba 2021–2026.
- Nuevos clientes en `src/terraverdict/ingest/`: USGS ComCat (FDSN), Smithsonian GVP (WFS), NASA Global Landslide Catalog, NOAA GHCN-Daily y POWER diario. Usan el manifiesto SHA-256 que ya tenía el paquete del equipo.
- Orquestador con registro explícito de cada error y el comando `tv ingest-fenomenos`.

**Evidencia** (`data/raw/registro_descarga.json`: todos los pasos OK)
- POWER: 16 740 días por punto (1981-01-01 → 2026-10-31). Sin faltantes, salvo la radiación de 1981 a 1983.
- USGS: 4052 sismos M ≥ 4 a menos de 350 km de Arequipa (1973-01-08 → 2026-10-30), incluido el Mw 8,4 de 2001.
- GVP: 13 volcanes del Holoceno en Perú y 80 registros de erupción (Ubinas 28, Misti 22, Sabancaya 15).
- NASA GLC: 58 deslizamientos en Perú (2007–2009), 30 de ellos en el sur.
- GHCN Arequipa: lluvia con huecos (14 años casi completos, unos 140 mm/año).

**Fuentes nacionales** (consulta real, evidencia en `docs/verificacion/fuentes_fenomenos.json`)
- SENAMHI corta la conexión.
- IGP y OVS: el servidor de origen no responde.
- INGEMMET tiene una cadena SSL incompleta; no se desactivó la verificación.
- SINIA bloquea con un firewall.
- ANA y CENEPRED tienen portales sin API.

La vía de integración prevista es por convenio o descarga manual verificada, usando el contrato de series del backend.

**Decisiones**
- Los crudos (21 MB) no van a git: se versionan solo los manifiestos y el registro, y los datos se regeneran con un comando.
- Para estas fuentes se amplió la red del entorno de nube solo con los hosts exactos.

---

## 2026-11-14 · Auditoría del repositorio e integración del trabajo de `feat/architecture`
**Autor:** Ower Frank · **Aporte integrado:** MaxsForocca

**Qué se hizo**
- Se revisaron todas las ramas. Del trabajo de MaxsForocca se integró en `main` su commit con:
  - el paquete científico `src/terraverdict` (Sello de Confianza);
  - las pruebas;
  - los ADR-012 a ADR-019;
  - `preregistro.yaml`;
  - el visor `web/`.

  Se usó *cherry-pick* para **conservar su autoría**.
- `configs/` se unificó en `config/`.
- Se corrigieron los enlaces rotos del índice de ADR y el lint y los tipos del código integrado, sin cambiar su comportamiento.
- Se agregó el ADR-020 (backend con base de datos y publicación por contrato).

**Evidencia.** `ruff` y `mypy` limpios en 61 archivos; las pruebas del paquete pasan (1 se omite porque requiere R).

**Decisiones**
- No se fusionó la rama completa, porque reintroduciría el historial antiguo que el equipo pidió limpiar.
- `web/` se conserva marcado como superado por `frontend/` hasta que el equipo confirme su retiro.

Detalle completo en [`auditoria-repositorio.md`](auditoria-repositorio.md).

---

## 2026-11-14 · Backend y frontend con contratos para ciencia de datos (`43959a4`)
**Autor:** Ower Frank

**Backend** (`backend/`)
- API FastAPI versionada, con JWT, claves de servicio y RBAC.
- Errores RFC 9457, con `request_id` incluso en los 500.
- Expedientes inmutables direccionados por contenido.
- Series con ETag y cola de procesos.
- Verificador numérico para la IA.
- 51 pruebas.

**Frontend** (`frontend/`)
- React y TypeScript estricto, con tipos generados del OpenAPI.
- Mapa con NASA GIBS.
- Estados vacíos explícitos.
- Cifras citadas con su cota ("> 70 %").

**Verificación de enlaces**
- 35/40 con HTTP 200 en tres corridas, con su historial en `docs/verificacion/enlaces.json`.

---

## Historial anterior (resumen)

| Commit | Qué |
|---|---|
| `61330d0` | Especificación del pipeline de datos, catálogo de fuentes y dominios de entrenamiento |
| `a83c972` | Revisión de todos los enlaces del reto y de la guía con consultas reales |
| `6fe36e7` | Propuesta final integrada con verificación real de fuentes y primer análisis (temperatura +0,23 °C/década) |
| `5a31d6e` | IA generativa con garantías (verificador numérico) |
| `e23028c`, `380d159` | Planteamiento con datos reales de Arequipa y recursos oficiales del reto |
| `ed68a70`, `3ccdb45` | Gemelo digital y "Cadena del Agua de Arequipa" |
| `bcabb8c`, `1e01456` | Idea principal |
