# Metodología

Métodos estadísticos, de aprendizaje automático y de sistemas dinámicos de TerraVerdict. Cada
método indica el módulo que lo implementa y su referencia (DOI o arXiv, verificables). Los
resultados están en [`experimentos.md`](experimentos.md); el registro de decisiones y defectos
corregidos, en [`bitacora.md`](bitacora.md).

## 1. Principios

1. **Datos reales con procedencia.** Cada crudo se guarda con su SHA-256, URL y fecha (`ingest/manifest.py`). Cada resultado guarda el commit, el hash del preregistro, el de la configuración y el de cada crudo (`experimentos/ejecutar.py`).
2. **Reglas fijadas antes de mirar la prueba.** `preregistro.yaml` y la partición temporal de `config/fenomenos.yaml` se congelaron el 2026-11-15, antes de la corrida completa. Una prueba automática falla si cambian.
3. **Partición temporal estricta.**
   - Entrenamiento: 1981–2015. Validación: 2016–2020. Prueba: 2021–2026-10.
   - Normalización, parámetros del SPI, climatologías, calibración, umbrales de decisión, ventana, variables y elección del modelo se ajustan con entrenamiento o validación. La prueba se evalúa **una vez**.
   - Las filas se asignan a una partición por la fecha del **objetivo** (t+h), para que ningún objetivo de entrenamiento caiga en validación. Pruebas: `tests/motor/test_comun_modelos.py`.
4. **Siempre frente a una referencia.** La habilidad se mide frente a la climatología y, cuando aplica, la persistencia (Wilks, 2011; Gneiting y Raftery, 2007, doi:10.1198/016214506000001437).
5. **Abstención explícita.** Si el modelo no supera a la climatología en validación, o hay menos eventos que el mínimo preregistrado, el sistema no publica y dice por qué. Ningún resultado es una alerta oficial.

## 2. Fuentes y control de calidad

| Fuente | Uso | Referencia |
|---|---|---|
| NASA POWER (MERRA-2), diaria y mensual | Lluvia, temperatura, humedad, viento, presión y radiación | power.larc.nasa.gov |
| CHIRPS v2.0, diaria (ClimateSERV) | Lluvia alternativa de 0,05° desde 1981 | Funk et al. (2015), doi:10.1038/sdata.2015.66 |
| IMERG Final V07, diaria | Lluvia satelital. Requiere aceptar la EULA de GES DISC; pendiente en la corrida del 2026-11-15 | Huffman et al., doi:10.5067/GPM/IMERGDF/DAY/07 |
| NOAA GHCN-Daily, Arequipa | Contraste puntual de lluvia y temperatura | Menne et al. (2012), doi:10.1175/JTECH-D-11-00103.1 |
| MODIS MOD11A2 v061 (ORNL DAAC) | Temperatura de superficie (contraste de anomalías y tendencias). En la corrida del 2026-11-15 no hubo acceso: ORNL respondía 502 (registrado) | modis.ornl.gov |
| NOAA CPC ONI | El Niño, con el rezago de publicación de 2 meses | cpc.ncep.noaa.gov |
| USGS ComCat | Sismos M ≥ 4 a 350 km de Arequipa desde 1973 | earthquake.usgs.gov/fdsnws |
| IGP, sismos reportados | Contraste nacional desde 2012 | ultimosismo.igp.gob.pe |
| Smithsonian GVP | Volcanes y erupciones del Holoceno | volcano.si.edu |
| NASA Global Landslide Catalog | Deslizamientos | Kirschbaum et al. (2010), doi:10.1007/s11069-009-9401-4; (2015), doi:10.1016/j.geomorph.2015.03.016 |

El control de calidad (`experimentos/datos_reales.py`) **cuenta, no corrige en silencio**:
- marca los faltantes (−999) y los valores fuera de rango físico;
- informa la fracción válida por variable.

El experimento `fuentes` (`experimentos/fuentes.py`) mide la concordancia entre productos:
- correlación diaria y mensual;
- razón de totales;
- extremos (p99) y frecuencia de días húmedos;
- tendencia de cada fuente.

Así se sabe cuánto depende un resultado del producto elegido. Por eso la lluvia extrema, la sequía y el caos se corren con POWER **y** con CHIRPS.

## 3. Señales y variables (`senales/`, `seleccion/`)

- **SPI-k:** McKee, Doesken y Kleist (1993). Usa una gamma por mes calendario con probabilidad de cero (Thom, 1958); los parámetros se ajustan **solo** con el entrenamiento.
- **Climatología diaria:** regresión armónica (3 armónicos) ajustada hasta el fin del entrenamiento.
- **Regímenes:** PELT con costo normal y penalización tipo BIC (Killick, Fearnhead y Eckley, 2012, doi:10.1080/01621459.2012.737745), implementado con ruptures (Truong, Oudre y Vayatis, 2020, doi:10.1016/j.sigpro.2019.107299).
- **Escalas:** varianza por nivel de la transformada wavelet discreta (Daubechies 4) y picos del periodograma.
- **Ventana adaptativa:** los candidatos fijos más los sugeridos por la señal (decorrelación de la autocorrelación, 4·τ de Takens) se comparan **en validación**.
- **Selección de variables (mRMR con prior físico):** Peng, Long y Ding (2005), doi:10.1109/TPAMI.2005.159.
  - Relevancia: información mutua por k vecinos (Kraskov, Stögbauer y Grassberger, 2004, doi:10.1103/PhysRevE.69.066138).
  - Redundancia: |ρ de Spearman| máxima con las variables ya elegidas.
  - Puntaje: peso físico (alta 1,0; media 0,8; baja 0,6) × IM × (1 − redundancia).
  - Una variable entra solo si su IM descontada supera la máxima de 50 permutaciones del objetivo (≈ p98 del nulo).
  - La forma multiplicativa reemplazó a la diferencia original porque, con un objetivo binario, la relevancia y la redundancia tenían escalas distintas (ver la bitácora del 2026-11-15).

## 4. Modelos (`modelos/`, `experimentos/comun.py`)

**Referencias** (no se recalibran):
- climatología por día del año (±15 días) o tasa media;
- persistencia de Markov o del último valor.

**Clásicos:** regresión logística, Ridge, GLM de Poisson y gradient boosting por histogramas.

**Redes** (PyTorch, CPU; entrada `(lote, L, F)`):

| Red | Referencia |
|---|---|
| MLP | Perceptrón multicapa |
| DLinear | Zeng et al. (2023), arXiv:2205.13504 |
| LSTM | Hochreiter y Schmidhuber (1997), doi:10.1162/neco.1997.9.8.1735 |
| GRU | Cho et al. (2014), arXiv:1406.1078 |
| TCN | Bai, Kolter y Koltun (2018), arXiv:1803.01271 |
| N-BEATS | Oreshkin et al. (2020), arXiv:1905.10437 |
| N-HiTS | Challu et al. (2023), arXiv:2201.12886 |
| PatchTST | Nie et al. (2023), arXiv:2211.14730 |
| iTransformer | Liu et al. (2024), arXiv:2310.06625 |
| SSM selectivo | Inspirado en Gu y Dao (2023), arXiv:2312.00752, y Gu et al. (2022), arXiv:2111.00396. Es una implementación de referencia, no el núcleo CUDA de Mamba |

**Entrenamiento:**
- AdamW con recorte de gradiente y parada temprana sobre la validación.
- Varias semillas: lluvia 2; sequía y sismos 3. Se informa la media y la dispersión entre semillas.
- La semilla se fija **antes** de crear la red, porque la inicialización también depende de ella.
- Ensamble: promedio de los 3 mejores en validación.

## 5. Evaluación e incertidumbre (`evaluacion/`)

- **Clasificación:**
  - habilidad de Brier frente a la climatología y a la persistencia;
  - AUC;
  - confiabilidad y ECE (bins de igual frecuencia);
  - tabla de contingencia (POD, FAR, CSI, HSS) con el umbral de máximo CSI **elegido en validación**.
- **Regresión:** habilidad = 1 − ECM/ECM de la referencia; MAE, RMSE, r.
- **Conteos:** ganancia de información en bits por mes frente a un Poisson de tasa constante.
- **Intervalos de confianza:** bootstrap de bloques móviles, que conserva la autocorrelación de los errores.
- **Diebold-Mariano:** frente a la climatología, con varianza HAC y corrección de Harvey, Leybourne y Newbold (Diebold y Mariano, 1995, doi:10.1080/07350015.1995.10524599).
- **Calibración isotónica:** ajustada solo en validación.
- **Intervalos conformales al 90 %:** predicción conformal partida (Vovk et al., 2005; Angelopoulos y Bates, 2021, arXiv:2107.07511). Con series temporales la garantía es aproximada: por eso se **mide** la cobertura en prueba.
- **Deriva:** PSI y Kolmogorov-Smirnov entre el entrenamiento y la prueba. Un PSI > 0,25 genera una advertencia.
- **Explicabilidad:** importancia por permutación de variables completas en toda la ventana (Breiman, 2001, doi:10.1023/A:1010933404324; Fisher, Rudin y Dominici, 2019).

**Lectura conservadora:** una habilidad está **confirmada** solo si su IC90 completo queda por encima de 0.

## 6. Fenómenos sin pronóstico posible con estos datos

- **Sismos** (`experimentos/sismos.py`):
  - Mc por máxima curvatura + 0,2 (Wiemer y Wyss, 2000, doi:10.1785/0119990114; Woessner y Wiemer, 2005, doi:10.1785/0120040007);
  - valor b de Aki (1965) con corrección de Utsu, incertidumbre de Shi y Bolt (1982) y bootstrap;
  - desagrupamiento de Gardner y Knopoff (1974);
  - el CV de los intereventos mide el agrupamiento.

  El conteo mensual se evalúa frente a un Poisson para medir estructura temporal. **No es un pronóstico de sismos.**
- **Volcanes** (`experimentos/volcanes.py`):
  - tasa de inicio de erupción por Poisson desde 1550, con IC exacto de Garwood (1936);
  - frecuencias históricas, no pronósticos: el estado actual lo informa el OVS-IGP.
- **Deslizamientos** (`experimentos/deslizamientos.py`):
  - lluvia antecedente de 1, 3, 10 y 30 días frente a la climatología de su celda y su mes;
  - el umbral empírico (Guzzetti et al., 2008, doi:10.1007/s10346-007-0112-1) solo se estima con ≥ 30 eventos.

## 7. Dinámica: caos, no linealidad o ruido (`caos/`)

| Paso | Método | Referencia |
|---|---|---|
| Retardo τ | Mínimo entre el primer mínimo de la información mutua promedio y el cruce de la autocorrelación por 1/e | Fraser y Swinney (1986), doi:10.1103/PhysRevA.33.1134 |
| Dimensión m | Falsos vecinos (< 1 %, con meseta), con ventana de Theiler | Kennel, Brown y Abarbanel (1992), doi:10.1103/PhysRevA.45.3403 |
| Dimensión de correlación D2 | Grassberger-Procaccia con cota de Eckmann-Ruelle | Grassberger y Procaccia (1983), doi:10.1016/0167-2789(83)90298-1 |
| Mayor exponente de Lyapunov | Rosenstein, con región lineal automática | Rosenstein, Collins y De Luca (1993), doi:10.1016/0167-2789(93)90009-P |
| Prueba 0-1 | Método de correlación (en flujos, con submuestreo por τ) | Gottwald y Melbourne (2004), doi:10.1098/rspa.2003.1183; (2009), doi:10.1137/080718851 |
| Entropías | De permutación; muestral | Bandt y Pompe (2002), doi:10.1103/PhysRevLett.88.174102; Richman y Moorman (2000), doi:10.1152/ajpheart.2000.278.6.H2039 |
| Recurrencias (RQA) | Tasa, determinismo, laminaridad, diagonales | Eckmann, Kamphorst y Ruelle (1987), doi:10.1209/0295-5075/4/9/004; Marwan et al. (2007), doi:10.1016/j.physrep.2006.11.001 |
| Sustitutos | IAAFT; asimetría temporal y predicción por análogos; corrección de Holm-Bonferroni | Theiler et al. (1992), doi:10.1016/0167-2789(92)90102-S; Schreiber y Schmitz (1996), doi:10.1103/PhysRevLett.77.635; (2000), doi:10.1016/S0167-2789(00)00043-9; Sugihara y May (1990), doi:10.1038/344734a0 |

**Regla de decisión** (`caos/diagnostico.py`). "Compatible con caos de baja dimensión" exige **a la vez**:
- no linealidad significativa;
- determinismo frente a todos los sustitutos;
- D2 que satura por debajo de 5;
- λ > 0;
- K > 0,8.

Si falta alguna condición, el veredicto es "no lineal sin caos demostrado" o "lineal estocástico". El método se validó antes con sistemas de referencia (Lorenz, Hénon, logístico, AR(1), ruido y seno; `tests/caos`). Las series reales se analizan como anomalías respecto del ciclo anual del entrenamiento, para no confundir la estacionalidad con dinámica.

## 8. Tendencias con Sello de Confianza (`trends/`)

- **Theil-Sen** con IC al 90 %.
- **Mann-Kendall con p conservador:** el máximo de las variantes original, Hamed-Rao y pre-blanqueo.
- **Cinco pruebas preregistradas:** ventanas móviles, ENSO, sensor, independencia de familias y detectabilidad.
- **Sensibilidad de palanca:** se quitan los últimos años y se comprueba si la tendencia sobrevive.

## 9. Reproducibilidad

```bash
tv ingest-fenomenos            # crudos con SHA-256
tv experimentos                # resultados/*.json con procedencia
tv informe                     # docs/experimentos.md (solo cifras de los JSON)
pytest                         # motor, caos, humo con un recorte real de los datos e integración con el backend
```
