# Bitácora del proyecto TerraVerdict

Registro de cada avance importante, para que todo el equipo sepa **qué hay, cómo se comprobó y qué falta**.
La entrada más reciente va primero. Cada entrada corresponde a uno o más commits en `main` (búscalos con `git log --oneline`).

**Cómo agregar una entrada:** fecha · autor · qué se hizo · evidencia (pruebas, cifras, archivos) · decisiones y por qué · pendientes. Nunca escribir resultados que no se hayan ejecutado.

Lo que falta para terminar está en **[`pendientes.md`](pendientes.md)**.

---

## Estado al 15-11-2026 (resumen para el equipo)

| Parte | Estado | Evidencia | Cómo correrlo |
|---|---|---|---|
| Preregistro y partición temporal | ✅ Congelados el 15-11 | Prueba que falla ante cualquier cambio | `pytest tests/unit/test_preregistro_congelado.py` |
| Ingesta de fuentes reales | ✅ POWER (Arequipa, celdas y 25 departamentos), USGS (Arequipa y Perú), GVP, GLC, GHCN, ONI, CHIRPS, IGP y MODIS LST con SHA-256 · ⏳ IMERG (1998–2001; detenida al cerrar la sesión, se reanuda con `docs/traspaso.md`) | `data/raw/*/manifiesto.json` | `tv ingest-fenomenos` |
| Cadena de custodia | ✅ Crudos verificados contra su manifiesto antes de entrenar; resultados sellados; el publicador rechaza lo alterado | `tests/integridad/` | `tv verificar-integridad` |
| Motor (modelos, evaluación, incertidumbre, selección) | ✅ 10 redes, 2 ensambles, IC90, Diebold-Mariano, conformal y abstención; protocolo auditado (`docs/auditoria-metricas.md`) | `tests/motor/` | `pytest tests/motor` |
| Corrida completa de experimentos | ✅ 10 experimentos con procedencia, incluida la escala nacional | `resultados/*.json`, `resultados/indice.json` | `tv experimentos` |
| Escala nacional | ✅ 25 departamentos: Sello de temperatura y lluvia, SPI y sismicidad por celda | `resultados/nacional.json`, vista `/peru` | `tv experimentos --solo nacional` |
| Caos en series reales | ✅ 7 series, ninguna caótica | `resultados/caos.json` | (incluido en `tv experimentos`) |
| Informe de resultados | ✅ Solo cifras de los JSON | `docs/experimentos.md` | `tv informe` |
| Backend (API REST) | ✅ Tipos M6 y M7, capas, catálogo, importación del contrato | 67 pruebas; OpenAPI sin deriva | `cd backend && pytest` |
| Publicación ciencia → backend | ✅ Idempotente y por contrato (`resultados/contrato/expedientes.json`) | `tests/integracion/` | `tv publicar --exportar …` |
| Frontend | ✅ Glassmorphism azul, vistas de fenómenos y Perú; bilingüe español/inglés | 27 pruebas; `docs/capturas/` | `cd frontend && npm test` |
| Paquete científico | ✅ 108 pruebas pasan (2 omitidas por diseño) | `tests/` | `pytest` |
| CI, Docker y E2E | ✅ Docker verificado con `docker compose up`; E2E Playwright 2 de 2 | `.github/`, `docker-compose.yml`, `frontend/e2e/` | ver `pendientes.md` |
| Métricas e historial (M8) | ✅ Mapas de calor por métrica, importancia de variables, historial año a año (2016–2026) y caos en ventanas; 24 fichas de métricas | `resultados/historial.json`, vista `/metricas` | `tv experimentos --solo historial` |
| Licencias | ✅ Código MIT; cita y términos de cada fuente; inventario de dependencias | `LICENSE`, `docs/licencias-*.md`, `tests/integridad/test_licencias.py` | `python scripts/inventario_licencias.py …` |
| Despliegue público | ✅ Listo para Vercel y verificado en local (arranque en frío de 3,1 s, E2E 2 de 2) · ⏳ falta conectar el repositorio a Vercel (acción de cuenta) | `vercel.json`, `api/`, `docs/despliegue.md` | ver `despliegue.md` |

---|---|---|---|
| Preregistro y partición temporal | ✅ Congelados el 15-11 | Prueba que falla ante cualquier cambio | `pytest tests/unit/test_preregistro_congelado.py` |
| Ingesta de fuentes reales | ✅ POWER, CHIRPS, USGS, IGP, GVP, GLC, GHCN y ONI con SHA-256 · ⏳ IMERG (EULA de GES DISC) y MODIS (ORNL con 502) | `data/raw/registro_descarga.json` | `tv ingest-fenomenos` |
| Motor (modelos, evaluación, incertidumbre, selección) | ✅ 3 defectos corregidos al probarlo | `tests/motor/` | `pytest tests/motor` |
| Corrida completa de experimentos | ✅ 9 experimentos con procedencia | `resultados/*.json` | `tv experimentos` |
| Caos en series reales | ✅ 7 series, ninguna caótica | `resultados/caos.json` | (incluido en `tv experimentos`) |
| Informe de resultados | ✅ Solo cifras de los JSON | `docs/experimentos.md` | `tv informe` |
| Backend (API REST) | ✅ Tipos M6, capas y catálogo de fenómenos | 66 pruebas; OpenAPI sin deriva | `cd backend && pytest` |
| Publicación ciencia → backend | ✅ Idempotente; 13 expedientes reales | `tests/integracion/` | `tv publicar` |
| Frontend | ✅ Glassmorphism azul y 5 vistas nuevas | 23 pruebas; `docs/capturas/` | `cd frontend && npm test` |
| CI, Docker y documentación | ✅ · ⏳ falta construir las imágenes y ver la primera ejecución de CI | `.github/`, `docker-compose.yml`, `docs/` | ver `pendientes.md` |
| Prueba E2E (Playwright) | ⏳ Bloqueada: la descarga del navegador no fue autorizada en este entorno | — | ver `pendientes.md` |

---

## 2026-11-15 · Auditoría de métricas y pesos: validación honesta y cifras sin elegir con la prueba

**Autor:** MaxsForocca (con asistencia de Claude)

**Qué se hizo.** Se auditó, archivo por archivo, cómo se calcula y se usa cada métrica y de dónde sale cada peso o elección. Informe completo: [`auditoria-metricas.md`](auditoria-metricas.md), con 19 hallazgos (H1–H19), la tabla por métrica y por parámetro, y los riesgos que quedan.

**Defectos corregidos (los principales):**
- **H1–H2. Elección con la prueba.** El historial destacaba la mejor cifra de prueba de cada tarea ("Ridge 0,711", "PatchTST 0,256"), y la web elegía el "mejor clásico" por su cifra fuera de muestra. Ahora la lectura principal es `seleccion_validacion`: el modelo que eligió la validación de cada año.
- **H3–H5 y H16. Fugas en la selección.**
  - La calibración isotónica y los ensambles se puntuaban sobre la misma validación con que se ajustaban; ahora se puntúan fuera de pliegue (5 bloques contiguos).
  - La parada temprana de las redes usaba la validación; ahora usa el último 15 % del entrenamiento.
  - El cuantil conformal de los ensambles usa residuos fuera de pliegue.
- **H6.** La Mc de sismos usaba todo el catálogo; ahora solo el entrenamiento. No cambia la cifra: manda el piso de 4,5.
- **H7–H8.** Diebold-Mariano usa el horizonte (h = 3 en sequía). El bloque del bootstrap es el mayor entre el fijo y el de Politis-White, y se guarda en cada resultado.
- **H9.** El ECE de un pronóstico constante daba 0.
- **H10–H11.** Caos en ventanas:
  - ahora usa un orden de permutación por serie;
  - guarda p de Holm y q de BH; ninguna ventana sobrevive a la corrección, y el conteo sin corregir queda rotulado como descriptivo;
  - el "p mínimo posible" ya no es el mínimo observado.
- **H12.** Cifras escritas a mano en la web ("25 departamentos", "Lima y Callao", "1981–2025", "< 200 mm", "10 redes", "350 km"): ahora salen del expediente.
- **H13.** Verificador: el tope fijo de 1000 valores se reemplazó por la probabilidad de que una cifra inventada con el mismo formato coincida por azar (> 0,05 → coincidencia débil).
- **H14–H15, H17.** El prior de lluvia se lee del catálogo, con ablación. Los hiperparámetros pasan a `config/modelos.yaml` (con justificación y SHA-256 en la procedencia). La regla de evidencia tiene una sola fuente.
- **Ensamble con pesos aprendidos.** Se agregó `ensamble_ponderado` (pesos ≥ 0 que suman 1, ajustados en validación) como candidato junto al promedio. Solo gana en la lluvia (POWER). En la sequía a 3 meses sobreajusta: 0,078 frente a 0,169 del promedio, ambos fuera de pliegue.

**Datos (H18–H19).**
- En esta máquina, 24 crudos (POWER, celdas POWER y GVP) no coincidían con los manifiestos del repositorio y faltaban los 36 nacionales. La cadena de custodia bloqueó la corrida.
- Se volvieron a descargar **solo** esos crudos de su fuente oficial. Los nacionales los descargó el propio experimento. Los manifiestos tienen los nuevos SHA-256.
- Las informaciones mutuas y las cifras de Ridge coinciden con las de antes: los datos del entrenamiento no cambiaron.
- MODIS se completó (ciudad y cabecera, día y noche, tras reintentos por 502/503 de ORNL). IMERG quedó en 1998–2001 al cerrar la sesión: la descarga se detuvo a propósito y `fuentes` usa 1998–2000.
- `fuentes` ya no falla con una descarga de MODIS a medias, y dos ingestas en paralelo ya no se pisan el registro de descargas.

**Resultados nuevos** (todas las cifras de `resultados/*.json`; tabla completa en `auditoria-metricas.md` §10):

| Tarea | Antes | Ahora | Por qué |
|---|---|---|---|
| Lluvia t+1 (POWER), prueba | SSM 0,080, p DM 0,152: indicio | Ensamble ponderado 0,092 [0,021; 0,166], p 0,096: **confirmada** | Calibración fuera de pliegue |
| Sequía h1 (POWER), prueba | N-BEATS 0,776 | Ridge 0,680 [0,539; 0,780]: confirmada | Sin parada temprana en la validación, N-BEATS baja de 0,740 a 0,610 en validación |
| Sequía h3 (POWER), prueba | iTransformer 0,198 | iTransformer 0,141 [0,094; 0,191]: confirmada | Ídem |
| Sismos, prueba | Ensamble 0,253 bits | LSTM 0,257 bits [0,057; 0,495]: confirmada | El ensamble ya no compite con ventaja |
| Historial fuera de muestra: lluvia | "ensamble 0,087, indicio" | Elegido en validación 0,031 [−0,040; 0,090]: **no confirmada** | H1 |
| Historial fuera de muestra: sequía h1 / h3 | "Ridge 0,711" / "ensamble 0,248" | 0,658 [0,531; 0,743] / 0,232 [0,073; 0,375]: confirmadas | H1 |
| Historial fuera de muestra: sismos | "PatchTST 0,256, confirmada" | 0,149 bits [−0,029; 0,395]: **no confirmada** | H1 |

**Reproducibilidad.** Dos corridas completas con el mismo commit, una de ellas en paralelo con otra, dan 163 856 valores **idénticos bit a bit** (torch 2.15 en CPU, hilos ≤ 4). Después se repitió solo `fuentes`, con MODIS completo.

**Evidencia**
- Ciencia: 135 pruebas pasan y 2 se omiten (20 nuevas: `tests/motor/test_auditoria_metricas.py` y `tests/experimentos/test_historial.py`).
- Backend: 73 (1 nueva). Frontend: 33. E2E: 2 de 2.
- `tv verificar-integridad`: 116 crudos verificados, 0 alterados; 11 resultados sellados.
- Contrato: 15 expedientes (`tv publicar --exportar`). OpenAPI y tipos del frontend regenerados.
- En esta máquina, `npm test` exige `NODE_OPTIONS=--no-experimental-webstorage` porque Node 26 trae su propio `localStorage`. CI usa Node 22 y no lo necesita.

**Pendiente:**
- Vercel: solo el owner (DiegoNiS), porque MaxsForocca no tiene permisos.
- Terminar IMERG (2002–2025): pasos y prompt en [`traspaso.md`](traspaso.md).
- Decidir si la Mc debe variar por década (riesgo 1 de la auditoría).

---

## 2026-11-15 · M8: mapas de calor de métricas, historial año a año y caos en ventanas

**Autor:** Ower Frank

**Qué se hizo**
- **Historial del pronóstico** (`experimentos/historial.py`): origen móvil anual 2016–2026 con el diseño congelado de cada tarea.
  - Las tareas ahora son objetos `Tarea` compartidos con el experimento principal: mismos datos, objetivo y referencias.
  - Regímenes "validación del diseño" (≤ 2020) y "fuera de muestra".
  - Habilidad agregada por régimen con IC90 y Diebold-Mariano.
- **Historial de la dinámica:** invariantes de caos en ventanas deslizantes con los métodos ya validados (entropías, λ, determinismo, K y p de no linealidad con sustitutos IAAFT).
- **Mapas de calor (vista `/metricas`):**
  - modelo × tarea para cada métrica (habilidad en prueba y en validación, IC90 inferior, p de Diebold-Mariano, dispersión entre semillas);
  - importancia tarea × variable (también en `/relevancia`, que antes se veía vacía);
  - modelo × año del historial;
  - serie × ventana para cada invariante de caos.
- **Fichas de métricas:** `config/metricas.yaml` con 24 fichas bilingües (qué mide, cómo leerla, si es mejor alta o baja, referencia), servidas en `GET /api/v1/metricas`.
- **Backend:**
  - tipo de expediente `historial_metricas` (M8, `TV-HIS-…`) con validación estricta;
  - endpoints `GET /api/v1/historial` y `GET /api/v1/metricas/mapas`, que reorganizan expedientes publicados sin calcular cifras.
- **Correcciones encontradas en la revisión visual:**
  - en el móvil, cuatro vistas obligaban al navegador a alejar el zoom. Causas: textos `sr-only` con posición absoluta fuera del contenedor con scroll, tarjetas sin `min-w-0` dentro de grillas y un texto truncado sin `min-w-0`. Ahora las 16 rutas miden 390 px de ancho en un iPhone 13;
  - el panel mostraba "25 departamentos" escrito a mano: ahora cuenta expedientes, como las demás filas, y agrega la fila M8.
- **CHIRPS en el caos:** si faltan sus crudos (ClimateSERV bloqueado aquí), la serie se omite y el motivo queda registrado, en vez de detener el diagnóstico.

**Resultados reales del historial** (`resultados/historial.json`, sellado; `docs/experimentos.md`)

| Tarea | Fuera de muestra (2021–2026) | Lectura |
|---|---|---|
| Lluvia fuerte a 1 día | SSM congelado 0,036 (IC90 −0,081 a 0,138); ensamble 0,087 (IC90 0,009 a 0,166, p 0,119) | La red pierde la habilidad que tenía en validación (0,130): solo el ensamble deja un **indicio** |
| Sequía SPI-3 a 1 mes | Ridge 0,711 (IC90 0,572 a 0,811); N-BEATS 0,525 | Todos **confirmados**; el modelo lineal generaliza mejor que la red elegida |
| Sequía SPI-3 a 3 meses | Ensamble 0,248 (IC90 0,102 a 0,385, p 0,063) | **Confirmada** |
| Sismos por mes | PatchTST 0,256 bits (IC90 0,093 a 0,484, p 0,040) | **Confirmada**; refleja agrupamiento, no es pronóstico de sismos |

Dinámica: el ONI es no lineal (p ≤ 0,05) en 23 de 48 ventanas; la lluvia en 10 de 32; la temperatura en 9 de 42; los sismos en 0.

**Evidencia**
- Ciencia: 8 pruebas nuevas, entre ellas cortes sin fuga, referencias ajustadas solo hasta Y−2 y el método que distingue el mapa logístico del ruido en cada ventana.
- Backend: 5 pruebas nuevas, y la prueba de despliegue limpio exige el historial y los mapas.
- Frontend: 6 pruebas nuevas; E2E incluye `/metricas`.
- Contrato de despliegue: 15 expedientes; `tv verificar-integridad` con 11 resultados sellados y 0 alterados.

---

## 2026-11-15 · Despliegue en Vercel listo y verificador numérico endurecido

**Autor:** Ower Frank

**Qué se hizo**
- **Vercel:**
  - `vercel.json`: compila el frontend, define la función `api/index.py`, envía `/api/*` a la función y el resto a la SPA.
  - `backend/app/serverless.py`: en cada arranque en frío migra, importa el contrato científico y, si hay variables, crea el administrador.
  - `api/requirements.txt` fija las versiones probadas.
  - Producción por defecto: sin `TV_JWT_SECRETO` la función no arranca.
- **Defecto encontrado y corregido en el verificador numérico (el guardarraíl de la IA):**
  - La página marcaba por defecto **todos** los expedientes como respaldo. Desde que el backend importa los resultados científicos, eso son decenas de miles de valores, y con la tolerancia de 0,5 % una cifra inventada (987,65 mm) coincidía por azar. Lo detectó la E2E.
  - Ahora se verifica contra el expediente que cita el texto, y la página advierte cuando hay más de 1000 valores de respaldo.
- **Docker:** la imagen no copiaba `resultados/contrato/` y `.dockerignore` excluía `resultados`. Un despliegue con Docker habría arrancado sin las vistas M6 y M7. Corregido. Además, la importación ahora registra una advertencia si falta el contrato, en vez de ignorarlo en silencio.
- `docs/despliegue.md`: las tres opciones, qué está verificado y la acción pendiente.

**Evidencia**
- Función en Python 3.12 (el de Vercel), con un entorno nuevo creado solo con `api/requirements.txt`:
  - lista en 3,1 s;
  - `/nacional` con 25 departamentos; capas con 625 sismos, 13 volcanes y 28 deslizamientos;
  - inicio de sesión del administrador; HSTS activo.
- Emulación del enrutado de `vercel.json`: E2E de Playwright 2 de 2, después de la corrección. Antes, 1 de 2.
- Contexto Docker: `expedientes.json` entra con el mismo SHA-256.
- La imagen completa no compiló en este entorno porque el proxy usa una CA propia que el contenedor no reconoce. El equipo ya la había compilado en su máquina.
- `tests/integridad/test_despliegue.py`: `api/requirements.txt` cubre `backend/pyproject.toml` y la función no excluye los datos que importa la API.
- Paquete científico: 108 pruebas; backend: 67; frontend: 27.

**Pendiente (acción de una persona):** Vercel respondió que falta instalar su integración de GitHub para `DiegoNiS/terraverdict`. Pasos en `docs/despliegue.md` §A.1.

---

## 2026-11-15 · Licencias del código, de los datos y de las dependencias

**Autor:** Ower Frank

**Qué se hizo**
- `LICENSE` (MIT) en la raíz, coherente con lo que ya declaraban el backend y el OpenAPI. Deja explícito que no cambia la licencia de los datos de terceros.
- `license` declarada en `pyproject.toml` (ciencia) y en `frontend/package.json`.
- `docs/licencias-y-atribuciones.md`: términos y cita obligatoria de cada fuente que usa el sistema, con enlace a la fuente oficial de la verificación.
  - Lo no comprobado queda marcado ⚠️: el texto vigente de Mapzen Terrain Tiles, el IGP y AUTODEMA.
  - Hallazgo: el Smithsonian GVP permite el uso no comercial con cita; un uso comercial exige su permiso escrito o retirar el módulo de volcanes.
- `scripts/inventario_licencias.py` genera `docs/licencias-terceros.md` desde los metadatos de cada paquete instalado (no se escribe a mano).
  - Ciencia `[ml]`: 46 paquetes. Backend: 27. Frontend: 89.
  - Todos permisivos, salvo `certifi` (MPL-2.0, usado sin modificar, compatible con MIT).
- El mapa ahora atribuye el relieve como lo exige su fuente: *"Mapzen Terrain Tiles · 3DEP, SRTM, GMTED2010 (USGS), ETOPO1 (NOAA)"*.
- README: sección de equipo sin marcadores `[Nombre]`. Los aportes salen del historial de `git`.
- Corrección: `tests/integracion/test_publicacion.py` fallaba desde que el backend importa el contrato científico al iniciar (los expedientes ya existían). Ahora la prueba desactiva esa importación porque publica ella misma.

**Evidencia**
- `tests/integridad/test_licencias.py`: falla si aparece una carpeta en `data/raw` sin fila de licencia, o si `LICENSE` y los manifiestos de paquetes no coinciden.
- Paquete científico: 106 pruebas pasan (2 omitidas). Backend: 67 de 67. Frontend: 27 de 27 y `tsc` limpio.

---

## 2026-11-15 · Despliegue autosuficiente por contrato y cliente IMERG robusto
**Autor:** Ower Frank

**Qué se hizo**
- `tv publicar --exportar resultados/contrato/expedientes.json` escribe los expedientes ya en el formato del contrato de la API.
- Al arrancar, el backend los importa con `importar_expedientes_ciencia`, validando cada uno con `ExpedienteCrear` y de forma idempotente. Lo controla `TV_IMPORTAR_RESULTADOS_CIENCIA`, activa por defecto.
- Con esto, un despliegue nuevo (Docker o nube) muestra desde el primer arranque las vistas de sismos, volcanes, caos, modelos y Perú, sin depender del paquete científico. Antes quedaban vacías hasta correr `tv publicar` contra una API viva.
- Cliente IMERG:
  - reintentos acotados con espera exponencial ante 401/429/5xx (GES DISC limita la tasa); 403 no se reintenta, porque suele ser la licencia;
  - 4 hilos por defecto, en lugar de 12;
  - el error indica desde qué año retomar.
- `tv ingest-fenomenos` ahora termina con código 1 si falla una fuente pedida. Antes, la descarga de IMERG que se cortó en 1998 terminó con código 0. Para entornos sin acceso existe `--tolerar-fallos`.

**Evidencia**
- Backend: prueba de despliegue limpio con 14 expedientes científicos importados, segunda importación sin duplicados y `GET /api/v1/nacional` con 25 departamentos.
- `tests/unit/test_earthdata_reintentos.py` (3, sin red).
- Corrida real sin token: el comando imprime `ERR imerg` y sale con código 1.

---

## 2026-11-15 · Cadena de custodia del pipeline (integridad SHA-256 de punta a punta)
**Autor:** Ower Frank

**Qué se hizo**
- `src/terraverdict/integridad.py` añade tres capas:
  1. Antes de entrenar, cada crudo se compara con el SHA-256 de su manifiesto, y un archivo alterado detiene la corrida (`IntegridadComprometida`).
  2. El orquestador sella cada `resultados/*.json` con su SHA-256 en `indice.json`.
  3. El publicador se niega a publicar un resultado que no coincide con su sello.
- Nuevo comando `tv verificar-integridad`, que audita crudos y resultados y devuelve código 1 si algo no cuadra. La procedencia de cada resultado registra cuántos crudos se verificaron.

**Evidencia**
- `tests/integridad`: crudo alterado → la corrida se detiene; resultado alterado → no se publica; faltantes y archivos sin manifiesto se informan sin ser fatales.
- La verificación encontró un caso real. Los crudos locales de esta máquina (GVP, POWER) no coincidían con los manifiestos fusionados desde otra máquina del equipo. Se volvieron a descargar y se repitió la corrida nacional sobre la base verificada: 74 crudos verificados, 0 alterados, 10 resultados sellados.
- Los 36 crudos "faltantes" (CHIRPS, IGP e IMERG) solo existen donde los descargó MaxsForocca. Desde este entorno el proxy bloquea ClimateSERV, ultimosismo.igp.gob.pe y modis.ornl.gov, e IMERG requiere token. Sus resultados conservan su propia procedencia.

---

## 2026-11-15 · Interfaz bilingüe español/inglés y vista nacional
**Autor:** Ower Frank

**Qué se hizo**
- Traducción completa de la interfaz con `t("español", "English")`: los dos textos van juntos en el código, así que ninguno puede quedar sin traducir. Selector ES/EN persistente en la barra lateral. El idioma inicial sale del navegador.
- Formatos según el idioma: números (coma decimal en español, punto en inglés), meses, fechas relativas, unidades y etiquetas de métricas. El verificador numérico recibe siempre números en formato español, porque así lo exige el backend.
- Los datos citados (títulos de eventos, justificaciones del catálogo) se muestran en su idioma original, con aviso. Traducirlos alteraría la evidencia.
- Vista **Perú: escala nacional** (`/peru`):
  - mapa por departamento con la variable elegible;
  - tabla con el Sello de cada celda y el estado SPI (con ícono y texto, nunca solo color);
  - grilla sísmica nacional y valor b por franja.
- Se quitaron dos datos fijados a mano en el panel:
  - la etiqueta ENSO ahora se deriva del ONI citado con los umbrales de NOAA (±0,5 °C; fuerte ≥ 1,5 °C);
  - se agregaron los módulos M6 y M7 a la lista de estado.
- Los expedientes de tipo M6/M7 enlazan a su vista especializada; el JSON queda plegado.
- La página de modelos aplica la regla de evidencia unificada: confirmada, indicio o no confirmada.

**Evidencia**
- `src/test/i18n.test.ts`: recorre todos los componentes y falla si encuentra texto visible fuera de `t()`. Además verifica los formatos en inglés.
- 27 pruebas del frontend; tsc y eslint sin errores.

---

## 2026-11-15 · Escala nacional (25 departamentos) y regla de evidencia más estricta
**Autor:** Ower Frank

**Qué se hizo**
- `config/nacional.yaml` y `src/terraverdict/experimentos/nacional.py`: el **mismo motor** de la cuenca del Chili aplicado a los 25 departamentos (24 + Callao). Por cada celda NASA POWER de cada capital, 1981–2025:
  - tendencia de temperatura y lluvia con el Sello de Confianza del paquete;
  - SPI-3 y SPI-12 con parámetros gamma de 1981–2015.
- Sismicidad nacional: catálogo USGS en la caja que contiene al Perú (M ≥ 4,5, 1973–2026), con Mc, valor b con bootstrap, grilla de 1° y b por franja de latitud. También deslizamientos por departamento (NASA GLC) y los volcanes del país (GVP).
- Contrato del backend: tipo `panorama_nacional` (módulo M7, dominio `peru_nacional`) con validaciones, y endpoint `GET /api/v1/nacional`. El publicador añade el hash de `config/nacional.yaml` a la procedencia.
- Regla de evidencia unificada en el informe, la web y las pruebas. **Confirmada** exige IC90 > 0 **y** Diebold-Mariano p < 0,10; **indicio**, solo una de las dos.

**Evidencia**
- Corrida real en 69 s. 24 celdas climáticas distintas, porque Lima y Callao comparten celda y se informan una sola vez.
- Temperatura, en el vocabulario de la API: 15 preliminares, 4 frágiles, 3 sin tendencia y 2 no decidibles.
- Sismos: 5710 eventos; b = 1,035 (IC90 1,006–1,065). Por franja: norte 1,006, centro 1,070, sur 1,034.
- Pruebas `tests/nacional` (5), sin red y sobre un recorte real: celda compartida, nunca 'robusta' con una sola familia, SPI no interpretable en clima árido, sismicidad y contrato del backend.

**Decisiones**
- **SPI en clima árido.** Con lluvia media < 200 mm/año el SPI se marca como no interpretable: el ajuste gamma sobre lluvias casi nulas daba SPI-12 ≈ +4,7 en Lima, Callao e Ica (OMM, guía del SPI, 2012).
- **Lluvia fuerte a 1 día (POWER).** Pasa de "confirmada" a **indicio**: IC90 0,003–0,151 pero Diebold-Mariano p = 0,152.
- **Mismo vocabulario de veredictos en todo el sistema.** 'preliminar' es significativa con pruebas pendientes; 'frágil' tiene alguna prueba fallida.

---

## 2026-11-15 · IMERG desbloqueado: cliente reanudable (descarga en curso)
**Autor:** MaxsForocca · **Aportes:** Ower Frank

- Con la licencia de GES DISC aceptada, OPeNDAP devuelve datos con el token. El formato coincide con el lector (`precipitation.precipitation[0][i], …`).
- **Causa de los 401 de la prueba manual:** `.env` pasó al formato `EARTHDATA_TOKEN=…` y el comando de prueba leía el archivo completo como token. El código (`token_earthdata`) ya admitía ambos formatos.
- **Rango real en CMR:** IMERG V07 Final va de 1998-01-01 a 2025-09-30. `config/fenomenos.yaml` ahora usa ese rango.
- **Cliente:**
  - reanudable (salta los años completos según el manifiesto);
  - registra los días 404 en `dias_faltantes`, sin rellenarlos;
  - 12 hilos: con 24, GES DISC respondió 503.
- **Estado:** descarga en curso (~4 min por año, ~2 h en total). Los pasos para terminarla están en `pendientes.md` → bloqueos externos.

---

## 2026-11-15 · Revisión del despliegue con docker compose
**Autor:** MaxsForocca · **Aportes:** Ower Frank

**Verificado** (imágenes construidas por el equipo, contenedores levantados de nuevo)
- API `healthy`: migra e importa al arrancar. Interfaz en `:8080`: nginx sirve la SPA (`/sismos` → 200) y redirige `/api`, con las cabeceras de seguridad y `X-Request-ID`.
- Publicación de los resultados reales en el contenedor:
  1. `docker compose exec api python -m app.cli crear-clave --nombre pipeline --alcance ingesta`;
  2. `tv publicar --api http://localhost:8080` → 13 × 201; al repetir, 13 × 200 (idempotente).
- Persistencia: tras `docker compose restart api` siguen los 15 expedientes (13 + 2 importados); la reimportación no duplica.
- La prueba E2E pasa 2 de 2 contra este despliegue.

**Ajustes tras la revisión**
- `backend/Dockerfile`: uvicorn con `--no-access-log`. Cada solicitud se registraba dos veces (texto de uvicorn y JSON de la app), y el healthcheck llenaba el registro cada 30 s.
- `nginx.conf.template`: búferes de 4 MB para el cuerpo y para el proxy. El expediente de caos pesa ~1–2 MB y nginx lo escribía en archivos temporales, con advertencias. Tras el cambio, 0 advertencias.

**Pendiente.** Probar el perfil `--profile postgres` con `TV_DATABASE_URL=postgresql+psycopg://…`.

---

## 2026-11-15 · Prueba de punta a punta con Playwright
**Autor:** MaxsForocca · **Aportes:** Ower Frank

**Qué se hizo**
- `frontend/e2e/recorrido.e2e.ts` (`npm run e2e`), con dos pruebas:
  1. Panel con el aviso permanente → iniciar sesión → abrir un expediente y ver su procedencia (hash) → el verificador aprueba el texto respaldado y marca como **sin respaldo** una cifra inventada ("987,65").
  2. Las cinco vistas de fenómenos cargan con su título y el aviso, sin errores de JavaScript.
- `playwright.config.ts` levanta su propio backend (`e2e/servidor-api.sh`: SQLite temporal, datos reales importados y un admin) y el build del frontend.
  - Con `E2E_BASE_URL`, `E2E_EMAIL` y `E2E_CONTRASENA` prueba cualquier otro despliegue.
  - Navegador: `PLAYWRIGHT_CHROMIUM`, `/usr/bin/chromium` si existe, o el de Playwright.
- Trabajo `e2e` en CI, con el reporte HTML como artefacto si falla.

**Evidencia.** 2 de 2 pasan localmente (Chromium 156) y 2 de 2 contra el despliegue de docker compose (`E2E_BASE_URL=http://localhost:8080`).

---

## 2026-11-15 · Calidad, despliegue y documentación (prioridad 3)
**Autor:** MaxsForocca · **Aportes:** Ower Frank

**Qué se hizo** (un commit por tarea)
- **CI** (`.github/workflows/ci.yml`), en tres trabajos:
  - backend: ruff, mypy y pytest;
  - ciencia: ruff, mypy y pytest, con PyTorch CPU y el backend instalado para la integración;
  - frontend: tipos idénticos al OpenAPI, typecheck, lint, test y build.
- **Docker:**
  - API: migra, importa y sirve con uvicorn; usuario sin privilegios y healthcheck;
  - interfaz: Vite servido por nginx con proxy de `/api`;
  - `docker-compose.yml` con perfil `postgres`, y `.env.example`.
- **Documentación:**
  - `docs/api/README.md`, con una prueba de backend que exige un ancla por cada código de error;
  - `docs/integracion-ciencia-datos.md`, `backend/README.md`, `docs/arquitectura.md` y `docs/metodologia.md` (DOI o arXiv por método);
  - `docs/trazabilidad.md` (23 requisitos);
  - `docs/presentacion-ejecutiva.md`: solo cifras citadas o de los JSON, sin proyecciones.

**Evidencia**
- Ciencia: 92 pruebas pasan, 1 se omite (requiere R).
- Backend: 66 pruebas pasan.
- Frontend: 23 pruebas pasan; typecheck, lint y build limpios.
- `docker compose config` es válido.

**No verificado en este entorno (se dice, no se oculta)**
- **Imágenes de Docker:** sin daemon de Docker, no se construyeron.
- **Primera ejecución de CI:** sin `gh`, no se pudo ver la ejecución en GitHub Actions.
- **E2E con Playwright:** la descarga de Chromium no fue autorizada; la prueba queda pendiente.

---

## 2026-11-15 · Rediseño glassmorphism azul y vistas de fenómenos (pendiente 2.2)
**Autor:** MaxsForocca · **Aportes:** Ower Frank (frontend base)

**Qué se hizo**
- **Tokens monocromáticos azules** con degradados (`frontend/src/estilos/global.css`). Modo oscuro azul profundo, con pasos propios; no es una inversión automática.
- **Paneles de vidrio esmerilado** (`.panel-vidrio`): `backdrop-filter`, borde blanco translúcido y sombra suave. Si el navegador no tiene `backdrop-filter`, o el usuario pide más contraste o colores forzados, se usa una superficie sólida.
- **Fondo** de cintas azules difuminadas y líneas finas blancas, decorativo y sin interacción.
- **Colores de datos:** se mantiene la paleta validada de la guía de visualización. El azul monocromático aplica al cromo de la interfaz, porque una categoría distinguida solo por luminosidad no es legible.
- **Vistas nuevas:**

  | Vista | Contenido |
  |---|---|
  | **Fenómenos** (`/fenomenos`) | Catálogo con justificación, fuente y limitaciones de cada variable; partición; acceso a las fuentes nacionales |
  | **Sismos** (`/sismos`) | Mapa por magnitud (radio) y profundidad (rampa azul), valor b con IC, Mc, tasa, CV de intereventos y conteo anual |
  | **Volcanes** (`/volcanes`) | Probabilidad anual con IC90, historia eruptiva (año de cada inicio) y mapa |
  | **Caos** (`/caos`) | Espacio de fases, gráfico de recurrencia, distribución de sustitutos frente a la serie original y condiciones de caos |
  | **Modelos** (`/modelos`) | Habilidad en prueba con IC90 por modelo (el elegido por validación, resaltado), confiabilidad, importancia de variables, cobertura conformal, abstención y ablaciones |

- **Aviso permanente** en todas las vistas: *"Resultados experimentales. No son alertas oficiales (SENAMHI, IGP, INGEMMET, INDECI)."*
- **Accesibilidad:**
  - cada gráfico tiene `role="img"` con descripción y una tabla de datos (`TablaDatos`, con `caption`);
  - los renglones de los gráficos son enfocables con teclado;
  - los estados llevan texto y no solo color;
  - en móvil, los gráficos de renglones se desplazan dentro de su tarjeta.

**Revisión visual** (`docs/capturas/`)
- Capturas en claro, oscuro y móvil, tomadas con Firefox sin interfaz sobre el backend con los **13 expedientes reales** publicados.
- El mapa (MapLibre) sale en blanco en las capturas porque ese modo no tiene WebGL; en un navegador normal se dibuja.
- Ajustes hechos tras mirarlas:
  - formato de conteos ("4052" y no "4,052");
  - tildes en los nombres de los estadísticos;
  - barra de desplazamiento sobrante en escritorio;
  - última marca del eje recortada;
  - etiqueta "Validación".

**Evidencia.** `npm run typecheck`, `lint` y `build` sin errores. 23 pruebas de frontend pasan, 4 nuevas: aviso, tabla de datos y veredictos con texto.

**Pendiente.** La prueba E2E con Playwright (P3) no se pudo instalar: la descarga de Chromium no fue autorizada en este entorno.

---

## 2026-11-15 · Integración ciencia → backend (pendiente 2.1)
**Autor:** MaxsForocca · **Aportes:** Ower Frank (backend y contratos originales)

**Qué se hizo**
- **Nuevos tipos de expediente** (módulo M6), cada uno con sus reglas de publicación validadas en el esquema:

  | Tipo | Regla que el backend hace cumplir |
  |---|---|
  | `comparacion_modelos` | Exige una referencia. El elegido debe ser el **mejor en validación** (la prueba no elige). Solo se publica si supera a la referencia en validación |
  | `caos` | "Compatible con caos" exige las cinco condiciones, D2 < 5, λ > 0 y K > 0,8 |
  | `recurrencia` | P anual dentro de su IC; un año de inicio por erupción; `es_pronostico: false` |
  | `sismicidad` | b dentro de su IC; `es_pronostico: false` |
  | `inventario` | Sin umbral con menos eventos que el mínimo |
  | `pronostico` (revisado) | Admite intervalo conformal (debe contener la mediana) y abstención (impide publicar) |
  | Todos | Toda abstención lleva motivo |

- **Adaptador `src/terraverdict/publicar/` (`tv publicar`):**
  - convierte `resultados/*.json` (13 expedientes) y las tendencias de `expedientes/*.json` al contrato;
  - publica con una clave `ingesta`;
  - es idempotente por hash de contenido (ADR-020).
- En las tendencias, "frágil por pruebas **pendientes**" del paquete se publica como `preliminar`, porque el backend reserva `fragil` para pruebas **fallidas**.
- **Endpoints:**
  - `GET /api/v1/fenomenos[/{id}]`: catálogo de `config/fenomenos.yaml`;
  - `GET /api/v1/capas/{sismos,volcanes,deslizamientos}`: GeoJSON tomado del expediente vigente, sin datos propios.
- **Catálogo:** dominio `sur_peru_fenomenos` para los catálogos regionales; nombres de las fuentes nuevas.
- **Contrato:** OpenAPI exportado (`docs/api/openapi.json`) y tipos del frontend regenerados (`npm run api:tipos`).
- **Corrección de texto en el catálogo:** el objetivo de la lluvia decía "percentil 95 de los días con lluvia"; el experimento usa el **p90 de todos los días de dic–mar del entrenamiento**. Es solo descriptivo; los resultados guardan el hash de la configuración con la que se calcularon.

**Evidencia**
- Backend: 65 pruebas pasan, incluidas 14 nuevas de los tipos y endpoints de M6. La prueba de deriva del OpenAPI pasa.
- `tests/integracion/test_publicacion.py`, de punta a punta sobre el recorte real:
  - orquestador, informe, conversión y publicación en una instancia real del backend;
  - todo aceptado; la segunda publicación devuelve los mismos IDs; las capas salen de los expedientes.
- **Con los resultados reales:**
  - 13 expedientes publicados (201) y, al repetir, 13 × 200 con los mismos IDs;
  - capas: 625 sismos M ≥ 5, 13 volcanes y 28 deslizamientos.

---

## 2026-11-15 · Informe de experimentos generado desde los resultados (pendiente 1.3)
**Autor:** MaxsForocca · **Aportes:** Ower Frank

**Qué se hizo**
- `tv informe` (`experimentos/informe.py`) escribe `docs/experimentos.md` **solo** con cifras de `resultados/*.json`.
- **Contenido:**
  - procedencia de la corrida y resumen;
  - por fenómeno: modelos con validación, prueba, IC90, Diebold-Mariano y dispersión entre semillas;
  - variables elegidas y descartadas con su motivo, ventana, ablaciones, curva de confiabilidad, eventos documentados, deriva y abstención;
  - sismos, volcanes, deslizamientos, dinámica, contraste de fuentes y limitaciones.
- **Lecturas por reglas explícitas, no por redacción:**
  - "confirmada" solo si el IC90 completo es > 0;
  - en la dinámica, las medidas de caos no se interpretan si no hay no linealidad.
- **Limitaciones derivadas de los números:**
  - caída de habilidad de más de 0,05 entre validación y prueba;
  - Mc por década mayor que la usada;
  - deriva y abstenciones.

**Evidencia**
- `tests/experimentos/test_informe.py`: secciones de los 9 experimentos, commit de la procedencia, cifras iguales a las del JSON con el mismo redondeo, sin `None` ni `nan`, y celdas con `|` escapadas.
- El informe tiene unas 600 líneas.

---

## 2026-11-15 · Caos en series reales (pendiente 1.2)
**Autor:** MaxsForocca · **Aportes:** Ower Frank (método validado)

**Qué se hizo.** Se aplicó el diagnóstico integrado (`caos/diagnostico.py`, validado con Lorenz, Hénon, el mapa logístico, AR(1) y un seno) a 7 series reales: las 6 previstas más las péntadas de CHIRPS, para comprobar si el veredicto depende del producto. Las series son anomalías respecto del ciclo anual del entrenamiento. Salida: `resultados/caos.json` (misma corrida, código `41198fe`).

**Resultados.** Los p-valores salen de los sustitutos IAAFT (99); la regla es conservadora, con corrección de Holm.

| Serie | n | p asimetría temporal | p predicción por análogos | Veredicto |
|---|---|---|---|---|
| Lluvia por péntadas, POWER | 3 348 | 0,53 | 0,05 | Lineal estocástica |
| Lluvia por péntadas, CHIRPS | 3 341 | 0,72 | 0,09 | Lineal estocástica (el mismo veredicto con las dos fuentes) |
| Temperatura diaria, cabecera | 16 740 | 0,01 | 0,08 | No lineal, sin caos demostrado |
| SPI-3 mensual | 538 | 0,10 | 0,54 | Lineal estocástica |
| ONI mensual | 921 | 0,01 | 0,01 | No lineal, sin caos demostrado |
| Conteo sísmico mensual (desagrupado) | 646 | 0,86 | 0,71 | Lineal estocástica |
| Intereventos sísmicos (log) | 1 256 | 0,96 | 0,01 | No lineal, sin caos demostrado |

- **Ninguna serie es compatible con caos de baja dimensión.**
- En todas, la prueba 0-1 da K ≈ 1 (0,993–0,999). Es lo esperable en señales estocásticas: K no distingue caos de ruido, y por eso nunca decide sola.
- La no linealidad del ONI es coherente con la asimetría conocida entre El Niño y La Niña. La de la temperatura y los intereventos queda como hallazgo descriptivo, no como determinismo.

**Lectura para el producto.** Ninguna serie muestra caos determinista. La lluvia y el SPI se comportan como procesos lineales estocásticos, que es lo que justifica usar modelos probabilísticos y referencias climatológicas.

---

## 2026-11-15 · Corrida completa de experimentos (pendiente 1.1)
**Autor:** MaxsForocca · **Aportes:** Ower Frank

**Qué se hizo**
- Se corrió `tv experimentos` completo sobre los datos reales:
  - código `41198fe`; preregistro congelado `c40676fd…`;
  - 10 redes, con 2 semillas en lluvia y 3 en sequía y sismos;
  - 73 crudos con SHA-256 en la procedencia.
- `resultados/indice.json` lista 9 experimentos: volcanes, deslizamientos, sismos, fuentes, sequía (POWER y CHIRPS), lluvia extrema (POWER y CHIRPS) y caos.
- Tiempo total: unos 8 minutos en 20 núcleos.

**Resultados.** Todas las cifras salen de `resultados/*.json`; la prueba (2021–2026) se usó una sola vez.

| Tarea | Elegido en validación | Habilidad en prueba (IC90) | Diebold-Mariano | Lectura |
|---|---|---|---|---|
| Sequía, SPI-3 a 1 mes, POWER | N-BEATS | 0,776 (0,675–0,843) | p = 0,017 | Confirmada. Supera a la persistencia (0,587); cobertura conformal 90 % |
| Sequía, SPI-3 a 1 mes, CHIRPS | Ensamble | 0,616 (0,491–0,770) | — | Confirmada; cobertura 93 % |
| Sequía, SPI-3 a 3 meses, POWER | iTransformer | 0,198 (0,119–0,263) | p = 0,013 | Confirmada, pero menor que la persistencia frente a la climatología (0,386) |
| Sequía, SPI-3 a 3 meses, CHIRPS | DLinear | 0,087 (0,048–0,114) | — | Confirmada y pequeña |
| Lluvia fuerte a 1 día, POWER (≥ 3,22 mm) | SSM selectivo | 0,080 (0,003–0,151) | p = 0,15 | Apenas confirmada; no significativa por DM. Deriva PSI > 0,25 |
| Lluvia fuerte a 1 día, CHIRPS (≥ 8,33 mm) | Ensamble | 0,046 (−0,007 a 0,090) | p = 0,16 | **No confirmada** |
| Conteo sísmico mensual | Ensamble | 0,253 bits/mes (0,066–0,492) | p = 0,074 | Agrupamiento de réplicas, **no pronóstico de sismos** |

- **Selección de variables (lluvia):** con mRMR corregido se eligen la historia de lluvia, el ONI, la humedad (relativa en POWER, específica en CHIRPS) y la radiación. Antes se elegía solo la historia de lluvia.
- **Sismos (USGS, 4 052 eventos):**
  - Mc 4,5 y b = 0,997 (IC90 0,962–1,031).
  - Desagrupados con Gardner-Knopoff: 1 257 independientes y b = 0,900 (0,863–0,938).
  - CV de los intereventos: 1,07.
- **Volcanes** (frecuencia histórica desde 1550, % anual, IC90):
  - Ubinas 4,51 (3,07–6,37);
  - Sabancaya 1,87 (0,98–3,24);
  - Misti 0,84 (0,29–1,90), a 17,8 km de la ciudad.
- **Deslizamientos:** 28 detonados por lluvia en el sur (58 en Perú). **Abstención**, porque se necesitan 30. La mediana del percentil de lluvia de 3 días es 67,8.
- **Contraste de fuentes:**
  - Lluvia de dic–mar en la cabecera hasta la temporada 2025–26: POWER +21,2 mm/década (p = 0,036); CHIRPS en la celda de POWER +31,6 (p = 0,035); CHIRPS a 0,1° +21,2 (p = 0,117).
  - El signo coincide, pero la significancia depende del producto.
  - IGP frente a USGS: 1 097 sismos emparejados; M IGP − M USGS = −0,08 ± 0,26.

**Limitaciones que el informe hace explícitas**
- La Mc por década fue mayor que 4,5 antes de 2000 (4,9 en los 70, 5,1 en los 80, 4,6 en los 90): el conteo de esos años está incompleto. **No se cambió el método después de ver la prueba**; queda como limitación.
- La habilidad de la lluvia cae de la validación (0,23) a la prueba (0,08), con deriva de las entradas. Se informa, no se corrige mirando la prueba.

**Pendiente.** MODIS (ORNL saturado) e IMERG (EULA de GES DISC). Cuando lleguen, solo se vuelve a correr `fuentes`, que es control de calidad y no evalúa la prueba de ningún modelo.

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
