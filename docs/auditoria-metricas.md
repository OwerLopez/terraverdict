# Auditoría de métricas y pesos

**Fecha:** 2026-11-15 · **Autor:** MaxsForocca (con asistencia de Claude) · **Commits:** ver `git log` desde `8a63d55`.

**Objetivo.** Demostrar con evidencia que:
- cada métrica se calcula y se usa como dice su definición;
- cada peso o elección sale del entrenamiento, de la validación o de una regla escrita antes;
- ningún número que se muestra se escribió a mano ni se fijó al azar.

**Las tres categorías de la auditoría:**

| Categoría | Qué es | Criterio |
|---|---|---|
| **(a) Resultado** | Una cifra que produce el pipeline | Debe salir de `resultados/*.json` con su procedencia. Si falta, se ve vacía, nunca rellenada |
| **(b) Parámetro de método** | Una decisión de diseño | Es legítima solo si está justificada, documentada (`config/`, `preregistro.yaml` o `docs/metodologia.md`) y **no se ajustó mirando la prueba** |
| **(c) Valor escrito a mano mostrado como resultado** | Un defecto | Se elimina o se deriva del pipeline |

Todas las pruebas citadas se ejecutan con `pytest` (paquete científico), `cd backend && pytest` y `cd frontend && npm test`.

---

## 1. Hallazgos y correcciones

| # | Hallazgo | Tipo | Efecto | Corrección | Prueba |
|---|---|---|---|---|---|
| H1 | El historial (README, bitácora, `/metricas` e informe) destacaba en cada tarea el modelo con **mejor cifra en la prueba**. Ejemplos: "Ridge 0,711" en la sequía a 1 mes, cuando la red congelada era N-BEATS; "ensamble 0,087" en la lluvia | (c) Selección con la prueba | Cifra fuera de muestra optimista | Nueva lectura principal `seleccion_validacion`: en cada año, el modelo que eligió la validación de ese corte. La web y el informe la ponen primero y ordenan el resto de forma fija | `test_lectura_principal_es_el_modelo_elegido_en_validacion_de_cada_anio` |
| H2 | La web elegía el "mejor clásico" del gráfico del historial por su cifra **fuera de muestra**; el informe, el "mejor clásico" de cada año por su cifra de prueba; la tabla agregada se ordenaba por cifra de prueba | (c) | Igual que H1 | El clásico de comparación se elige por validación; orden fijo | Revisión de código; `npm test` |
| H3 | La calibración isotónica se ajustaba con la validación y el **puntaje de validación** se medía sobre las mismas probabilidades calibradas | Fuga en la selección | Favorecía a los modelos calibrados al elegir | El puntaje usa calibración fuera de pliegue (5 bloques contiguos). La prueba sigue usando el calibrador ajustado con toda la validación | `test_calibracion_fuera_de_pliegue_no_es_optimista` |
| H4 | El ensamble se armaba con los 3 mejores en validación y luego se puntuaba **en esa misma validación** | Fuga en la selección | El ensamble competía con ventaja: en sismos fue el "elegido" | Puntaje fuera de pliegue: en cada bloque, miembros y pesos salen de los demás | `test_seleccion_por_validacion_con_ensambles_fuera_de_pliegue` |
| H5 | La parada temprana de las redes usaba la **validación**, la misma que después elegía el modelo | Fuga en la selección | Puntaje de validación optimista de las redes frente a los clásicos | Parada temprana con el último 15 % del entrenamiento | `test_parada_temprana_no_usa_la_validacion` |
| H6 | La Mc de sismos, que define el objetivo, se calculaba con **todo** el catálogo, prueba incluida | Fuga en el preprocesamiento | Ninguno en las cifras: la Mc del entrenamiento también es 4,4 y manda el piso de 4,5 (`sismos.json`, `completitud`). Era una fuga latente: con otro catálogo habría cambiado el objetivo | Mc solo con el entrenamiento (≤ 2015) y piso de `config/modelos.yaml` | `test_mc_de_sismos_solo_con_el_entrenamiento` |
| H7 | Diebold-Mariano usaba siempre h = 1, también en la sequía a 3 meses, cuyos errores se solapan | Método | p algo optimista en h = 3 | DM con el horizonte de la tarea (corrección de Harvey-Leybourne-Newbold) | `test_diebold_mariano_series_cortas_y_horizonte` |
| H8 | El bloque del bootstrap era fijo (10 días; 6 meses) y no se comprobaba contra la autocorrelación, tampoco en el agregado del historial, que concatena años | Método | IC90 posiblemente estrecho | Bloque = máx(fijo, Politis-White del diferencial de pérdidas); se guarda en el resultado | `test_bloque_politis_white_crece_con_la_autocorrelacion`, `test_bloque_del_historial_respeta_la_autocorrelacion_al_concatenar_anios` |
| H9 | El ECE de un pronóstico **constante** salía 0: los bordes de los bins colapsaban y no quedaba ningún bin | Defecto de métrica | Un pronóstico constante mal calibrado aparecía perfecto | Un solo bin cuando todos los valores son iguales | `test_ece_cero_si_lo_pronosticado_es_la_frecuencia_observada` |
| H10 | Caos en ventanas: el orden de la entropía de permutación cambiaba entre ventanas de una misma serie (intereventos: 4 y 5), y cada p se leía como "significativo" sin corrección por comparaciones múltiples | Método | Valores no comparables; conteos sin corregir presentados como prueba | Un orden por serie; p de Holm y q de BH por serie; la web y el informe muestran los tres conteos y rotulan el sin corregir como descriptivo | `test_caos_en_ventanas_usa_un_solo_orden_y_corrige_por_comparaciones_multiples` |
| H11 | La web rotulaba "mínimo posible" del p el mínimo **observado** | (c) | Etiqueta falsa | Lee `resumen.p_minimo_posible` = 1/(sustitutos + 1); sin él, rotula "mínimo observado" | `npm test` |
| H12 | Cifras escritas a mano en la web: "25 departamentos" y "Lima y Callao comparten celda" (`/peru`), "1981–2025", "< 200 mm/año", "10 redes neuronales" (`/modelos`) y "350 km" (`/sismos`) | (c) | Se mostrarían aunque cambiaran los datos | Se derivan del expediente (`departamentos`, `comparte_celda_con`, `serie_anios`, `umbral_spi_mm`, `radio_km`), o se quitan | `npm test` (E2E) |
| H13 | Verificador numérico: la web advertía con más de **1000** valores de respaldo, un número sin derivación; además repetía la tolerancia 0,005 del backend | (b) sin justificar | La advertencia no medía el riesgo real | El backend calcula, para cada cifra respaldada, la probabilidad de que una cifra **inventada** con el mismo formato coincida por azar; advierte si supera 0,05. La tolerancia vive solo en el backend | `test_probabilidad_de_coincidir_por_azar` |
| H14 | `experimentos/lluvia.py` tenía un diccionario `prior` escrito a mano. Sus valores coincidían con el catálogo, pero con identificadores distintos (`temperatura` frente a `temperatura_aire_2m`), y solo una entrada se leía del catálogo | (b) duplicado | Riesgo de deriva entre código y catálogo | Mapa explícito columna → id del catálogo; falla si falta una relevancia | `test_prior_fisico_de_lluvia_sale_del_catalogo` |
| H15 | Hiperparámetros escritos en el código (C = 0,5, alpha = 3, GBM, épocas, semillas, ventanas candidatas, ventana de sismos, piso de Mc, umbral del SPI) | (b) sin documentar | No auditables | `config/modelos.yaml` con la justificación de cada valor; su SHA-256 va en la procedencia | `test_hiperparametros_salen_de_la_configuracion` |
| H16 | El cuantil conformal de los ensambles usaba residuos de validación con pesos ajustados en esa validación | Fuga menor | Intervalo algo estrecho | Residuos fuera de pliegue | `test_seleccion_por_validacion_con_ensambles_fuera_de_pliegue` |
| H17 | La regla de evidencia (DM < 0,10) estaba escrita en tres lugares (informe, `lib/modelos.ts` y `ModelosPagina.tsx`) | (b) duplicado | Riesgo de deriva | Una fuente: `config/modelos.yaml`. El informe la lee; la web usa una constante que una prueba compara con la configuración | `test_regla_de_evidencia_igual_en_config_informe_y_web` |
| H18 | Los crudos locales de esta máquina no coincidían con los manifiestos del repositorio (24 alterados: POWER, celdas POWER y GVP). La cadena de custodia bloqueó la corrida, como debía | Proceso | Ninguno: no se entrenó con ellos | Se volvieron a descargar **solo** esos crudos de su fuente oficial; los manifiestos registran los nuevos SHA-256 | `tv verificar-integridad` |
| H19 | El experimento `fuentes` fallaba con una descarga de MODIS a medias (solo la banda diurna) | Robustez | Corrida interrumpida | MODIS se usa solo si están todas sus bandas | Revisión de código |

---

## 2. Métricas

| Métrica | Dónde se define | Fórmula verificada | De dónde sale | Riesgo de fuga | Acción |
|---|---|---|---|---|---|
| Brier | `evaluacion/metricas.py::brier` | media de (p − y)² | Calculada en prueba | Ninguno | Prueba contra la fórmula |
| BSS frente a la climatología | `habilidad_brier` | 1 − Brier/Brier_ref; NaN si Brier_ref = 0 | Prueba; la climatología se ajusta con el entrenamiento (≤ Y−2 en el historial) | Referencia sin datos de prueba | Prueba contra la fórmula y el caso Brier_ref = 0 |
| Habilidad ECM | `habilidad_mse` | 1 − ECM/ECM_ref; NaN si ECM_ref = 0 | Prueba | Ninguno | Prueba contra la fórmula y el caso límite |
| AUC | `auc` | `roc_auc_score`; NaN con una sola clase | Prueba | Ninguno | Prueba contra scikit-learn, todo ceros y todo unos |
| ECE | `confiabilidad` | Σ (n_b/n)·\|p̄_b − ȳ_b\| con bins de igual frecuencia | Prueba | Ninguno | **H9 corregido** |
| POD, FAR, CSI, HSS | `tabla_contingencia` | Wilks (2011); NaN si el denominador es 0 | Prueba, con el umbral elegido en validación | Ninguno | Prueba de casos límite |
| Umbral de máximo CSI | `mejor_umbral_csi` | Máximo CSI entre cuantiles 0,5–0,995 | **Validación** (probabilidades fuera de pliegue) | Ninguno | Revisado |
| Ganancia de información (bits) | `_metricas` (conteo) | (LL − LL_ref)/ln 2 | Prueba; tasa de referencia ≤ fin del entrenamiento | Ninguno | Prueba contra `scipy.stats.poisson` |
| MAE, RMSE, r | `mae`, `rmse`, `correlacion` | Definiciones estándar; r = NaN si la varianza es 0 | Prueba | Ninguno | Prueba |
| IC90 | `bootstrap_bloques` | Percentiles 5 y 95 de 500 réplicas por bloques móviles | Prueba | Bloque mal elegido: IC estrecho | **H8**: bloque ≥ Politis-White; NaN si n < 2 |
| Diebold-Mariano | `diebold_mariano` | HAC de Bartlett con rezagos = máx(h−1, ⌊n^⅓⌋) y corrección HLN; NaN si n < 3 o varianza 0 | Prueba, frente a la climatología | Horizonte mal fijado | **H7**: horizonte por tarea |
| Cobertura conformal 90 % | `cuantil_conformal`, `cobertura` | Cuantil ⌈(n+1)·0,9⌉/n de \|residuos\| | Cuantil en validación; cobertura en prueba | Ensambles: **H16** | Residuos fuera de pliegue |
| PSI y KS (deriva) | `incertidumbre.py::psi`, `deriva` | Σ (a − r)·ln(a/r) con bins del entrenamiento | Entrenamiento frente a prueba (solo advierte) | Ninguno: no decide nada | Umbral 0,25 de `config/fenomenos.yaml` (Siddiqi, 2006) |
| Importancia por permutación | `explicabilidad.py` | Aumento de la pérdida al permutar una variable completa | GBM ajustado en entrenamiento; permuta en validación | Ninguno | Revisado |
| Puntaje de validación | `comun.py::puntaje_validacion` | La métrica principal de la tarea frente a la climatología | Validación; calibración y ensambles **fuera de pliegue** | **H3, H4, H5** | Corregidos |

---

## 3. Parámetros

Columna "Origen": **E** aprendido en entrenamiento · **V** elegido o aprendido en validación · **P** preregistrado o regla fijada antes de la prueba · **F** fijado a priori (decisión de diseño documentada).

| Parámetro | Valor | Dónde se define | Origen | Justificación | Riesgo de fuga | Acción |
|---|---|---|---|---|---|---|
| Partición temporal | 1981–2015 / 2016–2020 / 2021–2026-10 | `config/fenomenos.yaml` | P | Congelada el 2026-11-15; una prueba falla si cambia | Ninguno | Revisado |
| Normalización (media y desviación) | — | `comun.py::construir` | E | Solo filas del entrenamiento | Ninguno | `test_normalizacion_solo_con_entrenamiento` |
| Parámetros gamma del SPI; climatologías de anomalías | — | `senales/procesamiento.py::spi`, `sequia.py` | E | Solo hasta el fin del entrenamiento | En el historial, el corte 2016 valida en 2015, año que entró en el ajuste | Documentado; afecta solo al régimen optimista |
| Umbral p90 de lluvia | p90 de dic–mar | `lluvia.py::tarea` | E | Entrenamiento congelado | Igual que el SPI | Documentado |
| Mc de sismos | máx(Mc del entrenamiento, 4,5) | `sismos.py::preparar`, `config/modelos.yaml` | E + F | Máxima curvatura + 0,2 (Woessner y Wiemer, 2005); piso conservador | Antes usaba la prueba (**H6**) | Corregido |
| Climatología y persistencia de referencia | — | `Tarea.referencias(hasta)` | E | Solo datos ≤ fin del entrenamiento (≤ Y−2 en el historial) | Ninguno | `test_origen_movil_regimenes_referencias_y_agregado` |
| Calibración isotónica | — | `comun.py::evaluar_zoo` | V | Ajustada en validación y aplicada a la prueba | Puntaje optimista (**H3**) | Corregido |
| Cuantil conformal | — | `evaluar_zoo` | V | Split conformal (Angelopoulos y Bates, 2021) | Ensambles (**H16**) | Corregido |
| Umbral de decisión (máximo CSI) | — | `evaluar_zoo` | V | Elegido en validación | Ninguno | Revisado |
| Ventana L de lluvia | candidatos 3, 7, 14, 30 días + sugeridas | `config/modelos.yaml` → `ventana_adaptativa` | V (entre candidatos F) | Escalas sinóptica a mensual | La validación elige L y luego el modelo: doble uso leve | Documentado |
| Ventana L de sequía | candidatos 3, 6, 12, 24 meses + sugeridas | ídem | V | Escalas estándar del SPI (McKee et al., 1993) | Igual que arriba | Documentado |
| Ventana de sismos | 12 meses | `config/modelos.yaml`; se guarda en `sismos.json` (`ventana_meses`) | F | Un ciclo anual de conteos | Ninguno | Antes era una constante leída por el historial; ahora el historial la lee del resultado |
| Variables de lluvia | mRMR | `seleccion/variables.py` | E | Solo con el entrenamiento | Ninguno | Revisado |
| Pesos del prior físico | alta 1,0 · media 0,8 · baja 0,6 | `config/modelos.yaml` | F | Prior del catálogo; ablación con pesos iguales en cada resultado | Ninguno | Ver §4 |
| Umbral nulo de mRMR | máximo de 50 permutaciones (≈ p98) | `config/modelos.yaml` | F | El estimador KSG es positivo con ruido; su nulo tiene cola larga | Ninguno | Revisado |
| Logística C, Ridge alpha, GLM alpha | 0,5 · 3 · 1 | `config/modelos.yaml` | F | Regularización moderada sobre entradas estandarizadas y muy correlacionadas (ventanas aplanadas) | Ninguno: no se ajustaron con la prueba | Movido a la configuración |
| GBM (iteraciones, tasa, hojas, L2) | 300 / 0,05 / 15 / 1 (conteo: 200 / 0,05 / 15) | `config/modelos.yaml` | F | Más conservador que el valor por defecto de scikit-learn para series cortas | Ninguno | Movido |
| Épocas máximas de las redes | 60 (lluvia), 150 (mensuales) | `config/modelos.yaml` | F | Son un tope; la parada temprana decide | Ninguno | Movido |
| Parada temprana | último 15 % del entrenamiento, paciencia 10 | `config/modelos.yaml` | E | Separar el ajuste de la red de la selección del modelo | Antes usaba la validación (**H5**) | Corregido |
| Semillas | lluvia 0, 1; sequía y sismos 0, 1, 2 | `config/modelos.yaml` | F | Presupuesto de cómputo; se informa la dispersión entre semillas | Ninguno | Movido |
| Peso de la clase positiva | √(negativos/positivos) | `evaluar_zoo` | E | Desbalance del entrenamiento; la raíz evita sobrecorregir | Ninguno | Revisado |
| Miembros y pesos del ensamble | 3 mejores; pesos iguales o aprendidos | `config/modelos.yaml`, `evaluar_zoo` | V | Ver §5 | Antes con ventaja (**H4**) | Corregido |
| Bloque del bootstrap | máx(10 d o 6 meses, Politis-White) | `config/modelos.yaml`, `metricas.py` | F + datos | Politis y White (2004); Patton et al. (2009) | Ninguno | **H8** |
| Réplicas y semilla del bootstrap | 500; 0 | `config/modelos.yaml` | F | Suficientes para percentiles 5–95 | Ninguno | Movido |
| Regla de evidencia | IC90 inferior > 0 y DM p < 0,10 | `config/modelos.yaml` | P | Dos pruebas complementarias; α = 0,10 igual que el preregistro de tendencias | Ninguno | **H17** |
| Abstención | habilidad de validación > 0; ≥ 30 eventos | `config/fenomenos.yaml` | P | Si no supera a la climatología en validación, no se publica | Ninguno | Revisado |
| Umbral del SPI nacional | 200 mm/año | `config/modelos.yaml` | F | El SPI no se interpreta en climas hiperáridos (OMM-N.° 1090, 2012) | Ninguno | Movido; viaja en el expediente (`umbral_spi_mm`) |
| α del caos en ventanas | 0,05; 39 sustitutos | `config/modelos.yaml`, `config/historial.yaml` | F | p mínimo 0,025 | Comparaciones múltiples (**H10**) | Corregido |
| Ventanas de caos (años por serie) | 15, 5, 25, 30, 20, 20 | `config/historial.yaml` | F | ≥ 240 puntos y n ≥ 5·d! con d ≥ 4 (Riedl et al., 2013) | Ninguno | Verificado con los n de cada ventana (§7) |
| Tolerancia del verificador | 0,5 % relativa + media unidad del último decimal | `backend/app/services/verificador.py` | F | Redondeo del tercer dígito significativo | — | Una sola fuente (**H13**) |
| Umbral de coincidencia por azar | 0,05 | ídem (`ALFA_COINCIDENCIA`) | F | Nivel convencional de una prueba | — | Reemplaza al tope de 1000 valores |

---

## 4. Selección de variables: ¿el prior cambia algo?

`mrmr` multiplica la información mutua por el peso del prior. Cada resultado de lluvia guarda ahora la selección con los pesos del catálogo y una ablación con pesos iguales (`seleccion_variables.ablacion_prior`).

**Cómo pesa el prior.** El prior solo cambia el **orden** en que entran las candidatas: el peso multiplica el puntaje, pero el criterio de parada compara la información mutua descontada, sin peso, con el nulo de permutaciones. Una variable sin señal no entra aunque su prior sea "alta".

**Ablación en la corrida auditada** (`resultados/lluvia_extrema.json`, `seleccion_variables`):

| Variable | Prior (catálogo) | IM (nats) | Umbral nulo | Resultado |
|---|---|---|---|---|
| lluvia (log) | alta | 0,0468 | — | fija |
| ONI | media | 0,0374 | — | elegida (redundancia 0,07) |
| humedad relativa | media | 0,0368 | — | elegida (redundancia 0,53) |
| radiación | media | 0,0175 | — | elegida (redundancia 0,61) |
| humedad específica | **alta** | 0,0261 | 0,0046 | descartada: redundante |
| amplitud térmica | media | 0,0203 | 0,0073 | descartada: redundante |
| temperatura | media | 0,0040 | 0,0110 | descartada: sin señal |
| presión | baja | 0,0043 | 0,0062 | descartada: sin señal |
| viento | baja | 0,0000 | 0,0065 | descartada: sin señal |

Con pesos iguales la selección es **la misma** (`ablacion_prior.cambia_la_seleccion = false`). En esta tarea el prior físico no decide nada: la selección la deciden los datos del entrenamiento. Una variable con prior "alta" (humedad específica) quedó fuera por redundante con la humedad relativa y el ONI. Las informaciones mutuas coinciden con las de la corrida anterior a la auditoría: la nueva descarga de POWER (H18) no cambió los datos del entrenamiento.

---

## 5. Pesos del ensamble

Antes había un solo ensamble: el promedio simple de los 3 mejores en validación, con pesos iguales no aprendidos, puntuado sobre la misma validación con que se eligió. Ahora compiten dos variantes, ambas puntuadas fuera de pliegue:
- `ensamble_top3`: promedio simple;
- `ensamble_ponderado`: pesos ≥ 0 que suman 1 y minimizan la pérdida en validación (apilamiento restringido; Breiman, 1996).

El modelo publicado sigue siendo el de mejor puntaje de validación. La prueba no interviene.

**Resultado de la corrida auditada** (puntaje de validación fuera de pliegue; `resultados/*.json`, `zoo.modelos`):

| Tarea | Elegido en validación | Promedio (val · prueba) | Ponderado (val · prueba) | Pesos aprendidos |
|---|---|---|---|---|
| Lluvia · POWER | **ensamble ponderado** | 0,177 · 0,096 | 0,177 · 0,092 | SSM 0,54 · iTransformer 0,42 · GRU 0,04 |
| Lluvia · CHIRPS | GRU | 0,019 · 0,058 | 0,025 · 0,069 | GRU 0,68 · logística 0 · iTransformer 0,32 |
| Sequía h1 · POWER | Ridge | 0,609 · 0,664 | 0,592 · 0,678 | Ridge 0,64 · TCN 0,36 · N-BEATS 0 |
| Sequía h3 · POWER | iTransformer | 0,169 · 0,124 | 0,078 · 0,122 | iTransformer 0,72 · GBM 0,28 · DLinear 0 |
| Sequía h1 · CHIRPS | Ridge | 0,570 · 0,498 | 0,639 · 0,568 | Ridge 0,89 · GBM 0,11 · N-BEATS 0 |
| Sequía h3 · CHIRPS | DLinear | 0,011 · −0,011 | 0,053 · 0,083 | DLinear 1 |
| Sismos | LSTM | 0,210 · 0,222 | 0,270 · 0,257 | LSTM 1 |

**Lectura.**
- Aprender los pesos **no garantiza** mejorar: en la sequía a 3 meses (POWER) los pesos de validación dan un puntaje fuera de pliegue menor (0,078) que el promedio (0,169). Con 60 meses de validación, ajustar pesos sobreajusta.
- A menudo los pesos se concentran en un solo miembro (sismos, sequía h3 con CHIRPS). En esos casos el ensamble ponderado equivale al mejor modelo individual, y el puntaje fuera de pliegue lo refleja.
- **Decisión:** se mantienen las dos variantes como candidatas y decide la validación, igual que con cualquier otro modelo. Solo en la lluvia (POWER) ganó el ponderado. La columna de prueba es informativa: no participó en ninguna decisión.

---

## 6. Historial (M8)

- **Referencias hasta Y−2:** verificado (`test_origen_movil_regimenes_referencias_y_agregado`).
- **Diseño congelado leído de los JSON:** variables, ventana y red salen de `resultados/<fenómeno>.json`. La ventana de sismos ahora se guarda en `sismos.json` (`pronostico_conteos.ventana_meses`); si falta, el historial se detiene y pide repetir el experimento.
- **Tamaño de muestra:** 12 meses por año en sequía y sismos. La web y el informe destacan el agregado por régimen; la tabla por año es contexto.
- **Lectura principal:** `seleccion_validacion` (**H1**).
- **Bloque del bootstrap del agregado:** el bloque usado es el mayor entre el de la tarea y el de Politis-White, y se guarda en `agregado.<régimen>.<modelo>.bloque_bootstrap`. En la lluvia, Politis-White lo sube a 18 días (SSM, fuera de muestra) y a 25 (GBM, validación del diseño). En las tareas mensuales manda el bloque de 6 meses. Los años se concatenan en orden, así que un bloque que cruza de diciembre a enero respeta la dependencia real. Prueba: `test_bloque_del_historial_respeta_la_autocorrelacion_al_concatenar_anios`.

---

## 7. Caos en ventanas

**Ventanas por serie** (`config/historial.yaml`; n de la corrida auditada):

| Serie | Años por ventana | n por ventana | Orden de permutación (uno por serie) | p ≤ 0,05 sin corregir | Tras Holm | Tras BH |
|---|---|---|---|---|---|---|
| Lluvia por péntadas (POWER) | 15 | 1083–1096 | 5 | 10 de 32 | 0 | 0 |
| Lluvia por péntadas (CHIRPS) | 15 | 1076–1096 | 5 | 4 de 32 | 0 | 0 |
| Temperatura diaria | 5 | 1765–1827 | 5 | 9 de 42 | 0 | 0 |
| SPI-3 mensual | 25 | 298–300 | 4 | 2 de 21 | 0 | 0 |
| ONI mensual | 30 | 357–360 | 4 | 23 de 48 | 0 | 0 |
| Conteo sísmico mensual | 20 | 240 | 4 | 0 de 34 | 0 | 0 |
| Intereventos sísmicos (log) | 20 | 366–606 | 4 (antes 4 y 5 según la ventana) | 0 de 35 | 0 | 0 |

- Todas las ventanas cumplen ≥ 240 puntos y n ≥ 5·d! con su orden: 5·4! = 120 y 5·5! = 600.
- **Conclusión de la auditoría:** ninguna ventana sostiene no linealidad después de corregir por comparaciones múltiples. Los conteos sin corregir (p. ej., el ONI en 23 de 48) son **descriptivos**: muestran en qué periodos la asimetría temporal fue mayor, no prueban no linealidad en ellos. El veredicto global de cada serie (`resultados/caos.json`, 99 sustitutos y Holm entre dos pruebas) no cambia.

---

## 8. Interfaz y API

Recorrido de `frontend/src` y `backend/app` buscando cifras escritas a mano que se muestren como resultado:
- **Corregidos:** H2, H11, H12 y H13 (ver la tabla del §1).
- **Textos de método, no resultados:** "máxima curvatura + 0,2", "IC 90 %", "nominal 90 %", "p ≤ 0,05" y "±0,05 hm³" de AUTODEMA. Este último es el control que hace `backend/app/importacion.py` al importar el reporte. Cada uno coincide con su fuente en la configuración o en el código.
- **API:** los endpoints de métricas (`/metricas`, `/metricas/mapas`, `/historial`) reorganizan expedientes publicados y no calculan cifras. El backend valida que `mejor_validacion` sea el máximo del puntaje de validación (`ResultadoComparacionModelos._reglas`) y ahora también que los pesos del ensamble sumen 1.

---

## 9. Reproducibilidad

Se corrió `tv experimentos` **tres veces** con las mismas semillas sobre los mismos crudos:
1. corrida 1, sola, con el commit `8a63d55`;
2. corrida final, con el commit `98846df`, en `resultados/`;
3. corrida de reproducibilidad con el mismo commit, en otra carpeta y **en paralelo** con la 2.

Comparación de todos los valores numéricos de los JSON (sin la procedencia ni los tiempos):

| Comparación | Valores comparados | Distintos |
|---|---|---|
| Final frente a reproducibilidad (mismo código, en paralelo; 11 experimentos) | 163 856 | **0** |
| Corrida 1 frente a final (código distinto solo en el conformal de los ensambles; 10 experimentos sin `fuentes`, que la corrida 1 no ejecutó) | 163 655 | 40, todos `q_conformal_90`, `ancho_intervalo_90` o `cobertura_90` de ensambles de regresión (H16) |

**Determinismo de torch en CPU.** Con torch 2.15 (CPU), semillas fijadas antes de crear cada red (`fijar_semilla`), barajado con un `torch.Generator` propio y `torch.set_num_threads(≤ 4)`, los resultados fueron **idénticos bit a bit**, también con dos corridas compitiendo por los núcleos. Para conservarlo, no hay que cambiar el número de hilos de torch: las sumas en coma flotante pueden cambiar de orden con otro número de hilos. Tampoco hay que mezclar versiones de torch, NumPy o scikit-learn (quedan en `procedencia.versiones`). No se activó `torch.use_deterministic_algorithms`, porque no hizo falta en CPU.

---

## 10. Qué cambió en los resultados y por qué

Los crudos de entrenamiento no cambiaron (las informaciones mutuas de la selección de variables y las cifras de Ridge, que no depende de la parada temprana ni de la calibración, son idénticas antes y después). Los cambios vienen del **protocolo de evaluación**.

**Experimento principal (prueba 2021–2026).**

| Tarea | Antes: elegido · val · prueba [IC90] · p DM | Ahora: elegido · val · prueba [IC90] · p DM | Lectura | Por qué cambió |
|---|---|---|---|---|
| Lluvia · POWER | SSM · 0,235 · 0,080 [0,003; 0,151] · 0,152 | Ensamble ponderado · 0,177 · 0,092 [0,021; 0,166] · 0,096 | indicio → **confirmada** | Calibración fuera de pliegue (H3): el puntaje de validación de todos los modelos calibrados baja (logística de 0,207 a 0,141; SSM de 0,235 a 0,173), y la validación elige otro candidato |
| Lluvia · CHIRPS | Ensamble · 0,109 · 0,046 [−0,007; 0,090] · 0,165 | GRU · 0,046 · 0,051 [0,013; 0,086] · 0,050 | no confirmada → **confirmada** | H3 y H4: el ensamble ya no compite con ventaja |
| Sequía h1 · POWER | N-BEATS · 0,740 · 0,776 [0,675; 0,843] · 0,017 | Ridge · 0,634 · 0,680 [0,539; 0,780] · 0,022 | confirmada (igual) | H5: sin parada temprana en la validación, el puntaje de N-BEATS baja de 0,740 a 0,610 y gana Ridge, que es idéntico antes y después. La cifra de prueba baja porque la red ya no se elige con información de la validación |
| Sequía h3 · POWER | iTransformer · 0,362 · 0,198 [0,119; 0,263] · 0,013 | iTransformer · 0,267 · 0,141 [0,094; 0,191] · 0,006 | confirmada (igual) | H5: la red entrena con el 85 % y para con el tramo final del entrenamiento; su puntaje de validación era optimista. El p de DM ya usa h = 3 (H7) |
| Sequía h1 · CHIRPS | Ensamble · 0,727 · 0,616 [0,491; 0,770] · 0,015 | Ridge · 0,658 · 0,576 [0,474; 0,670] · 0,008 | confirmada (igual) | H4 y H5 |
| Sequía h3 · CHIRPS | DLinear · 0,057 · 0,087 [0,048; 0,114] · 0,003 | DLinear · 0,053 · 0,083 [0,046; 0,109] · 0,006 | confirmada (igual) | H5 y H7 (cambio menor) |
| Sismos | Ensamble · 0,289 · 0,253 bits [0,066; 0,492] · 0,074 | LSTM · 0,287 · 0,257 bits [0,057; 0,495] · 0,073 | confirmada (igual) | H4: el puntaje fuera de pliegue del ensamble baja de 0,289 a 0,210 |

**Historial, fuera de muestra (2021 en adelante).** Antes se destacaba la mejor cifra de prueba de cada tarea; ahora, el modelo que eligió la validación de cada año (H1).

| Tarea | Antes (cifra destacada) | Ahora: elegido en validación año a año [IC90] · p DM | Lectura |
|---|---|---|---|
| Lluvia a 1 día | ensamble 0,087, "indicio" | 0,031 [−0,040; 0,090] · 0,461 | **no confirmada** |
| Sequía a 1 mes | Ridge 0,711, "confirmada" | 0,658 [0,531; 0,743] · 0,021 | confirmada |
| Sequía a 3 meses | ensamble 0,248, "confirmada" | 0,232 [0,073; 0,375] · 0,089 | confirmada |
| Sismos por mes | PatchTST 0,256 bits, "confirmada" | 0,149 bits [−0,029; 0,395] · 0,281 | **no confirmada** (la red congelada, ahora LSTM, da 0,214 [0,037; 0,438] · 0,105: indicio) |

**Qué significa.**
- La sequía a 1 y 3 meses sigue confirmada fuera de muestra con el procedimiento completo.
- La lluvia a 1 día y el conteo sísmico **ya no** se pueden presentar como habilidad confirmada fuera de muestra. En el periodo de prueba congelado (2021–2026) sí quedan confirmadas, pero el historial año a año, que cambia de modelo cada año según la validación, no sostiene la señal.
- Las cifras anteriores del README, la bitácora y los pendientes ("Ridge 0,711", "PatchTST 0,256") se reemplazaron por estas.

---

## 11. Riesgos que quedan (declarados, no corregidos)

1. **Completitud sísmica.** La Mc por década llega a 4,9–5,1 antes del año 2000, por encima de la Mc usada (4,5). Los conteos de esos años están incompletos y la tasa aparente crece con el tiempo. Corregirlo con una Mc variable cambiaría la tarea; queda como decisión del equipo.
2. **Doble uso de la validación.** Elige la ventana L con un modelo lineal y después elige el modelo. Es un uso secuencial habitual; el historial fuera de muestra mide su efecto.
3. **Hiperparámetros fijados a priori.** No se ajustaron con validación, a propósito: hacerlo gastaría la validación en más elecciones. Están documentados con su justificación.
4. **Primer corte del historial (2016).** El SPI y el umbral de lluvia se ajustaron hasta 2015, el año que en ese corte sirve de validación. Solo afecta al régimen "validación del diseño", que ya se lee como optimista.
5. **39 sustitutos por ventana.** Bastan para el diagnóstico descriptivo, no para sobrevivir a Holm con decenas de ventanas. Subirlos a 999 multiplicaría el tiempo por 25.
6. **Redes con el 85 % del entrenamiento.** La parada temprana honesta reserva el 15 % final; los clásicos usan el 100 %. Es una desventaja declarada de las redes, no una fuga.
