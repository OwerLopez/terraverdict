# Resultados de los experimentos

> Generado automáticamente por `tv informe` desde `resultados/*.json`. No editar a mano: cada cifra sale de esos archivos, que guardan su procedencia completa.

| Campo | Valor |
|---|---|
| Generado (UTC) | 2026-11-15T21:28:43+00:00 |
| Commit del código | `98846dfe121502312b8e4386cc85c94020d52034` |
| Modo | completo |
| Configuración (SHA-256) | `0382c23985f0b0c0…` |
| Versiones | python 3.13.15, numpy 2.5.4, torch 2.15.0+cpu, scikit_learn 1.9.1 |
| Crudos con hash | 113 |
| Tiempo por experimento (s) | volcanes 0, deslizamientos 0, sismos 94, fuentes 1, sequia 605, sequia_chirps 671, lluvia_extrema 448, lluvia_extrema_chirps 1151, caos 60, nacional 30, historial 3333 |

**Cómo leer.** La partición es temporal y está congelada (entrenamiento 1981–2015, validación 2016–2020, prueba 2021–2026). Todo se elige con validación; la prueba se usa una vez. Una habilidad está **confirmada** solo si su IC90 por bootstrap de bloques queda por encima de 0 **y** la prueba de Diebold-Mariano frente a la climatología da p < 0,10; si solo se cumple una de las dos, es un **indicio**. Las reglas de método y los hiperparámetros están en `config/modelos.yaml`; su auditoría, en `docs/auditoria-metricas.md`.

## Resumen

| Tarea | Modelo elegido (validación) | Habilidad en prueba | IC90 | p DM | Lectura | Publicación |
|---|---|---|---|---|---|---|
| Lluvia fuerte t+1 · POWER | Ensamble ponderado (pesos de validación) | 0,092 | 0,021 a 0,166 | 0,096 | confirmada (IC90 > 0 y DM p < 0,10) | publica |
| Lluvia fuerte t+1 · CHIRPS | GRU | 0,051 | 0,013 a 0,086 | 0,050 | confirmada (IC90 > 0 y DM p < 0,10) | publica |
| SPI-3 a 1 mes(es) · POWER | Ridge | 0,680 | 0,539 a 0,780 | 0,022 | confirmada (IC90 > 0 y DM p < 0,10) | publica |
| SPI-3 a 3 mes(es) · POWER | iTransformer | 0,141 | 0,094 a 0,191 | 0,006 | confirmada (IC90 > 0 y DM p < 0,10) | publica |
| SPI-3 a 1 mes(es) · CHIRPS | Ridge | 0,576 | 0,474 a 0,670 | 0,008 | confirmada (IC90 > 0 y DM p < 0,10) | publica |
| SPI-3 a 3 mes(es) · CHIRPS | DLinear | 0,083 | 0,046 a 0,109 | 0,006 | confirmada (IC90 > 0 y DM p < 0,10) | publica |
| Conteo sísmico mensual | LSTM | 0,257 | 0,057 a 0,495 | 0,073 | confirmada (IC90 > 0 y DM p < 0,10); refleja agrupamiento de réplicas, no es pronóstico de sismos | publica |

## Lluvia fuerte a 1 día · NASA POWER

**Fuente de la lluvia:** NASA POWER (MERRA-2) PRECTOTCORR, celda de la cabecera.  
**Objetivo:** lluvia diaria en la cabecera ≥ 3.22 mm (p90 de dic–mar, entrenamiento; POWER); horizonte 1 día; meses 11, 12, 1, 2, 3, 4.

| Partición | Días | Eventos |
|---|---|---|
| entrenamiento | 5 786 | 409 |
| validacion | 907 | 120 |
| prueba | 1 026 | 122 |

Tasa base en entrenamiento: 0,071.

### Modelos

Métrica principal: habilidad de Brier frente a la climatología. En **negrita**, el modelo elegido por validación (la prueba no participa en la elección).

| Modelo | Familia | Validación | Prueba | IC90 prueba | p Diebold-Mariano | Dispersión entre semillas |
|---|---|---|---|---|---|---|
| Climatología (referencia) | referencia | 0,000 | 0,000 | 0,000 a 0,000 | — |  |
| Persistencia (referencia) | referencia | 0,041 | 0,020 | -0,028 a 0,070 | 0,525 |  |
| **Ensamble ponderado (pesos de validación)** | ensamble | 0,177 | 0,092 | 0,021 a 0,166 | 0,096 |  |
| Ensamble (3 mejores en validación) | ensamble | 0,177 | 0,096 | 0,028 a 0,168 | 0,077 |  |
| SSM selectivo | red neuronal | 0,173 | 0,071 | -0,010 a 0,140 | 0,199 | 0,022 |
| iTransformer | red neuronal | 0,164 | 0,055 | -0,020 a 0,139 | 0,323 | 0,062 |
| GRU | red neuronal | 0,148 | 0,076 | 0,011 a 0,146 | 0,135 | 0,010 |
| Regresión logística | clasico | 0,141 | 0,072 | 0,001 a 0,145 | 0,163 |  |
| DLinear | red neuronal | 0,119 | 0,020 | -0,063 a 0,109 | 0,721 | 0,057 |
| LSTM | red neuronal | 0,115 | 0,062 | -0,007 a 0,134 | 0,224 | 0,010 |
| TCN | red neuronal | 0,109 | 0,078 | 0,005 a 0,154 | 0,161 | 0,016 |
| N-HiTS | red neuronal | 0,107 | 0,062 | -0,006 a 0,125 | 0,200 | 0,050 |
| N-BEATS | red neuronal | 0,106 | 0,078 | 0,008 a 0,152 | 0,143 | 0,043 |
| MLP | red neuronal | 0,105 | 0,087 | 0,013 a 0,165 | 0,107 | 0,013 |
| Gradient boosting | clasico | 0,096 | 0,086 | 0,033 a 0,134 | 0,032 |  |
| PatchTST | red neuronal | -0,003 | -0,001 | -0,060 a 0,040 | 0,974 | 0,005 |

Lectura (regla IC90): habilidad del modelo elegido confirmada (IC90 > 0 y DM p < 0,10).

### Variables seleccionadas (mRMR con prior físico, solo entrenamiento)

Redundancia = |ρ de Spearman| máxima con las ya elegidas; puntaje = peso × IM × (1 − redundancia). Las variables de estación del año (seno y coseno) se añaden siempre.

| Variable | Información mutua | Redundancia | Peso físico | Puntaje |
|---|---|---|---|---|
| lluvia_log (fija) | 0,0468 | — | — | — |
| oni | 0,0374 | 0,0702 | 0,8 | 0,0278 |
| humedad_relativa | 0,0368 | 0,5277 | 0,8 | 0,0139 |
| radiacion | 0,0175 | 0,6133 | 0,8 | 0,0054 |

Descartadas: humedad_especifica (IM 0,0261, umbral nulo 0,0046, redundante o sin ganancia); temperatura (IM 0,0040, umbral nulo 0,0110, sin señal frente al objetivo permutado); amplitud_termica (IM 0,0203, umbral nulo 0,0073, redundante o sin ganancia); presion (IM 0,0043, umbral nulo 0,0062, sin señal frente al objetivo permutado); viento (IM 0,0000, umbral nulo 0,0065, sin señal frente al objetivo permutado).

### Ventana

Elegida: **14 días** (mejor en validación). Sugeridas por la señal: decorrelacion_acf = 1, embedding_takens = 16.

| Ventana (días) | Habilidad de Brier en validación |
|---|---|
| 3 | 0,149 |
| 7 | 0,148 |
| 14 | 0,153 |
| 16 | 0,148 |
| 30 | 0,143 |

### Ablaciones (habilidad de Brier; validación / prueba)

| Conjunto de variables | gbm | logistica | ssm_selectivo |
|---|---|---|---|
| seleccion mrmr | 0,096 / 0,086 | 0,141 / 0,072 | 0,166 / 0,055 |
| solo historia lluvia | 0,090 / 0,031 | 0,146 / 0,084 | 0,119 / 0,094 |
| sin oni | 0,145 / 0,078 | 0,152 / 0,106 | 0,167 / 0,077 |
| todas las variables | 0,159 / 0,054 | 0,152 / 0,090 | 0,121 / 0,089 |

### Calibración del modelo elegido (prueba)

ECE = 0,035.

| Probabilidad pronosticada | Frecuencia observada | n |
|---|---|---|
| 0,007 | 0,010 | 98 |
| 0,018 | 0,019 | 106 |
| 0,040 | 0,078 | 90 |
| 0,054 | 0,052 | 116 |
| 0,080 | 0,094 | 85 |
| 0,105 | 0,041 | 121 |
| 0,148 | 0,088 | 102 |
| 0,211 | 0,170 | 94 |
| 0,280 | 0,218 | 101 |
| 0,464 | 0,407 | 113 |

### Eventos documentados en el periodo de prueba

| Evento | Mes | Días con lluvia fuerte | P media del modelo esos días | P climatológica esos días |
|---|---|---|---|---|
| Represas del sistema Chili con 159 de 409 hm³ útiles | 2023-11 | 3 | 0,089 | 0,015 |
| SEDAPAR paraliza sus dos plantas por huaicos y rebose de Aguada Blanca | 2024-03 | 4 | 0,305 | 0,089 |
| Turbidez de 5000 NTU detiene la producción de agua potable | 2025-02 | 9 | 0,500 | 0,151 |
| Segundo episodio de turbidez con el Chili a 50 m³/s | 2025-02 | 9 | 0,500 | 0,151 |

### Deriva de las entradas

| Variable | PSI (entrenamiento → prueba) | p KS | Deriva (PSI > 0,25) |
|---|---|---|---|
| lluvia_log | 0,081 | 0,0000 | no |
| oni | 0,514 | 0,0000 | sí |
| humedad_relativa | 0,035 | 0,0000 | no |
| radiacion | 0,255 | 0,0000 | sí |
| estacion_seno | 0,001 | 0,8490 | no |
| estacion_coseno | 0,002 | 0,5077 | no |

### Publicación

- Decisión: **Se publica**.
- Advertencia: Deriva de las entradas respecto del entrenamiento (PSI > 0,25).

### Control de calidad: celda POWER de la ciudad frente a la estación GHCN

| Días comunes | r diario | r mensual | p99 POWER (mm) | p99 estación (mm) |
|---|---|---|---|---|
| 7 538 | 0,199 | 0,580 | 7,3 | 13,6 |

## Lluvia fuerte a 1 día · CHIRPS

**Fuente de la lluvia:** CHIRPS v2.0 (ClimateSERV), promedio de una caja de 0,1° en la cabecera.  
**Objetivo:** lluvia diaria en la cabecera ≥ 8.33 mm (p90 de dic–mar, entrenamiento; CHIRPS); horizonte 1 día; meses 11, 12, 1, 2, 3, 4.

| Partición | Días | Eventos |
|---|---|---|
| entrenamiento | 5 786 | 391 |
| validacion | 907 | 58 |
| prueba | 1 026 | 65 |

Tasa base en entrenamiento: 0,068.

### Modelos

Métrica principal: habilidad de Brier frente a la climatología. En **negrita**, el modelo elegido por validación (la prueba no participa en la elección).

| Modelo | Familia | Validación | Prueba | IC90 prueba | p Diebold-Mariano | Dispersión entre semillas |
|---|---|---|---|---|---|---|
| Climatología (referencia) | referencia | 0,000 | 0,000 | 0,000 a 0,000 | — |  |
| Persistencia (referencia) | referencia | 0,014 | 0,106 | 0,056 a 0,154 | 0,000 |  |
| **GRU** | red neuronal | 0,046 | 0,051 | 0,013 a 0,086 | 0,050 | 0,039 |
| Ensamble ponderado (pesos de validación) | ensamble | 0,025 | 0,069 | 0,025 a 0,106 | 0,010 |  |
| Regresión logística | clasico | 0,023 | -0,024 | -0,105 a 0,045 | 0,622 |  |
| Ensamble (3 mejores en validación) | ensamble | 0,019 | 0,058 | 0,013 a 0,098 | 0,048 |  |
| iTransformer | red neuronal | 0,016 | 0,069 | 0,022 a 0,115 | 0,032 | 0,076 |
| Gradient boosting | clasico | 0,014 | 0,019 | -0,025 a 0,057 | 0,433 |  |
| SSM selectivo | red neuronal | 0,010 | 0,041 | -0,046 a 0,118 | 0,449 | 0,004 |
| TCN | red neuronal | -0,008 | 0,052 | 0,023 a 0,077 | 0,012 | 0,022 |
| PatchTST | red neuronal | -0,010 | 0,005 | -0,021 a 0,032 | 0,757 | 0,005 |
| DLinear | red neuronal | -0,026 | 0,028 | -0,023 a 0,072 | 0,384 | 0,115 |
| N-HiTS | red neuronal | -0,026 | 0,029 | 0,001 a 0,053 | 0,095 | 0,072 |
| N-BEATS | red neuronal | -0,029 | 0,043 | 0,003 a 0,080 | 0,103 | 0,012 |
| LSTM | red neuronal | -0,029 | 0,027 | -0,012 a 0,060 | 0,282 | 0,053 |
| MLP | red neuronal | -0,055 | 0,039 | 0,010 a 0,065 | 0,041 | 0,009 |

Lectura (regla IC90): habilidad del modelo elegido confirmada (IC90 > 0 y DM p < 0,10).

### Variables seleccionadas (mRMR con prior físico, solo entrenamiento)

Redundancia = |ρ de Spearman| máxima con las ya elegidas; puntaje = peso × IM × (1 − redundancia). Las variables de estación del año (seno y coseno) se añaden siempre.

| Variable | Información mutua | Redundancia | Peso físico | Puntaje |
|---|---|---|---|---|
| lluvia_log (fija) | 0,0444 | — | — | — |
| oni | 0,0298 | 0,1129 | 0,8 | 0,0211 |
| humedad_especifica | 0,0266 | 0,5680 | 1,0 | 0,0115 |
| radiacion | 0,0166 | 0,5496 | 0,8 | 0,0060 |

Descartadas: humedad_relativa (IM 0,0279, umbral nulo 0,0066, redundante o sin ganancia); temperatura (IM 0,0002, umbral nulo 0,0067, sin señal frente al objetivo permutado); amplitud_termica (IM 0,0258, umbral nulo 0,0071, redundante o sin ganancia); presion (IM 0,0100, umbral nulo 0,0046, redundante o sin ganancia); viento (IM 0,0000, umbral nulo 0,0046, sin señal frente al objetivo permutado).

### Ventana

Elegida: **14 días** (mejor en validación). Sugeridas por la señal: decorrelacion_acf = 1, embedding_takens = 44.

| Ventana (días) | Habilidad de Brier en validación |
|---|---|
| 3 | 0,032 |
| 7 | 0,030 |
| 14 | 0,044 |
| 30 | 0,028 |
| 44 | 0,033 |

### Ablaciones (habilidad de Brier; validación / prueba)

| Conjunto de variables | gbm | gru | logistica |
|---|---|---|---|
| seleccion mrmr | 0,014 / 0,019 | 0,053 / 0,041 | 0,023 / -0,024 |
| solo historia lluvia | 0,006 / 0,065 | 0,046 / 0,085 | 0,049 / 0,054 |
| sin oni | 0,019 / 0,075 | 0,012 / 0,055 | 0,023 / 0,058 |
| todas las variables | 0,022 / 0,054 | 0,029 / 0,053 | 0,022 / 0,069 |

### Calibración del modelo elegido (prueba)

ECE = 0,016.

| Probabilidad pronosticada | Frecuencia observada | n |
|---|---|---|
| 0,000 | 0,000 | 257 |
| 0,015 | 0,023 | 177 |
| 0,030 | 0,010 | 104 |
| 0,067 | 0,072 | 152 |
| 0,115 | 0,039 | 128 |
| 0,202 | 0,211 | 208 |

### Eventos documentados en el periodo de prueba

| Evento | Mes | Días con lluvia fuerte | P media del modelo esos días | P climatológica esos días |
|---|---|---|---|---|
| Represas del sistema Chili con 159 de 409 hm³ útiles | 2023-11 | 0 | — | — |
| SEDAPAR paraliza sus dos plantas por huaicos y rebose de Aguada Blanca | 2024-03 | 3 | 0,125 | 0,115 |
| Turbidez de 5000 NTU detiene la producción de agua potable | 2025-02 | 3 | 0,157 | 0,136 |
| Segundo episodio de turbidez con el Chili a 50 m³/s | 2025-02 | 3 | 0,157 | 0,136 |

### Deriva de las entradas

| Variable | PSI (entrenamiento → prueba) | p KS | Deriva (PSI > 0,25) |
|---|---|---|---|
| lluvia_log | 0,002 | 0,0001 | no |
| oni | 0,514 | 0,0000 | sí |
| humedad_especifica | 0,134 | 0,0000 | no |
| radiacion | 0,255 | 0,0000 | sí |
| estacion_seno | 0,001 | 0,8490 | no |
| estacion_coseno | 0,002 | 0,5077 | no |

### Publicación

- Decisión: **Se publica**.
- Advertencia: Deriva de las entradas respecto del entrenamiento (PSI > 0,25).

### Control de calidad: celda POWER de la ciudad frente a la estación GHCN

| Días comunes | r diario | r mensual | p99 POWER (mm) | p99 estación (mm) |
|---|---|---|---|---|
| 7 538 | 0,199 | 0,580 | 7,3 | 13,6 |

## Sequía (SPI-3) · NASA POWER

Fuente de la lluvia para el SPI: **POWER**.

Regímenes del SPI-3 (PELT): 5 puntos de cambio (1987-06-01, 1997-01-01, 2003-04-01, 2011-03-01, 2018-09-01).

### SPI-3 dentro de 1 mes(es) (ventana 3 meses)

| Partición | Meses |
|---|---|
| entrenamiento | 412 |
| validacion | 60 |
| prueba | 60 |

Métrica principal: habilidad (1 − ECM/ECM de la climatología). En **negrita**, el modelo elegido por validación (la prueba no participa en la elección).

| Modelo | Familia | Validación | Prueba | IC90 prueba | p Diebold-Mariano | Dispersión entre semillas |
|---|---|---|---|---|---|---|
| Climatología (referencia) | referencia | 0,000 | 0,000 | 0,000 a 0,000 | — |  |
| Persistencia (referencia) | referencia | 0,393 | 0,456 | 0,130 a 0,671 | 0,114 |  |
| **Ridge** | clasico | 0,634 | 0,680 | 0,539 a 0,780 | 0,022 |  |
| TCN | red neuronal | 0,620 | 0,634 | 0,506 a 0,731 | 0,019 | 0,012 |
| N-BEATS | red neuronal | 0,610 | 0,643 | 0,510 a 0,737 | 0,019 | 0,008 |
| N-HiTS | red neuronal | 0,610 | 0,643 | 0,510 a 0,737 | 0,019 | 0,008 |
| Ensamble (3 mejores en validación) | ensamble | 0,609 | 0,664 | 0,530 a 0,760 | 0,018 |  |
| MLP | red neuronal | 0,606 | 0,657 | 0,525 a 0,750 | 0,020 | 0,017 |
| Gradient boosting | clasico | 0,597 | 0,576 | 0,493 a 0,658 | 0,008 |  |
| Ensamble ponderado (pesos de validación) | ensamble | 0,592 | 0,678 | 0,543 a 0,774 | 0,019 |  |
| GRU | red neuronal | 0,591 | 0,605 | 0,504 a 0,688 | 0,015 | 0,005 |
| iTransformer | red neuronal | 0,569 | 0,535 | 0,411 a 0,620 | 0,014 | 0,007 |
| PatchTST | red neuronal | 0,559 | 0,547 | 0,409 a 0,657 | 0,016 | 0,043 |
| LSTM | red neuronal | 0,555 | 0,555 | 0,414 a 0,675 | 0,020 | 0,001 |
| SSM selectivo | red neuronal | 0,456 | 0,352 | 0,218 a 0,455 | 0,021 | 0,021 |
| DLinear | red neuronal | 0,074 | 0,051 | 0,039 a 0,069 | 0,003 | 0,050 |

Lectura (regla IC90): habilidad del modelo elegido confirmada (IC90 > 0 y DM p < 0,10). Habilidad frente a persistencia en prueba: 0,412. Cobertura del intervalo conformal del 90 % en prueba: 0,900 (ancho 3,209).

Categoría sequía (SPI-3 ≤ −1) en prueba: aciertos 1, falsas alarmas 0, fallos 2; POD 0,333, FAR 0,000, CSI 0,333.

- Decisión: **Se publica**.

### SPI-3 dentro de 3 mes(es) (ventana 24 meses)

| Partición | Meses |
|---|---|
| entrenamiento | 389 |
| validacion | 60 |
| prueba | 60 |

Métrica principal: habilidad (1 − ECM/ECM de la climatología). En **negrita**, el modelo elegido por validación (la prueba no participa en la elección).

| Modelo | Familia | Validación | Prueba | IC90 prueba | p Diebold-Mariano | Dispersión entre semillas |
|---|---|---|---|---|---|---|
| Climatología (referencia) | referencia | 0,000 | 0,000 | 0,000 a 0,000 | — |  |
| Persistencia (referencia) | referencia | -0,335 | -0,305 | -0,722 a 0,148 | 0,259 |  |
| **iTransformer** | red neuronal | 0,267 | 0,141 | 0,094 a 0,191 | 0,006 | 0,010 |
| Gradient boosting | clasico | 0,236 | 0,040 | -0,125 a 0,124 | 0,545 |  |
| DLinear | red neuronal | 0,235 | 0,149 | 0,054 a 0,225 | 0,042 | 0,063 |
| N-HiTS | red neuronal | 0,223 | 0,122 | 0,025 a 0,179 | 0,105 | 0,021 |
| N-BEATS | red neuronal | 0,211 | 0,064 | -0,022 a 0,120 | 0,195 | 0,038 |
| MLP | red neuronal | 0,175 | 0,053 | -0,020 a 0,103 | 0,232 | 0,042 |
| Ridge | clasico | 0,174 | -0,235 | -0,702 a 0,036 | 0,190 |  |
| Ensamble (3 mejores en validación) | ensamble | 0,169 | 0,124 | 0,048 a 0,177 | 0,029 |  |
| TCN | red neuronal | 0,114 | -0,046 | -0,234 a 0,079 | 0,588 | 0,033 |
| LSTM | red neuronal | 0,103 | -0,013 | -0,079 a 0,037 | 0,735 | 0,044 |
| Ensamble ponderado (pesos de validación) | ensamble | 0,078 | 0,122 | 0,063 a 0,165 | 0,015 |  |
| GRU | red neuronal | 0,067 | -0,047 | -0,126 a -0,001 | 0,193 | 0,028 |
| SSM selectivo | red neuronal | 0,056 | 0,051 | -0,068 a 0,159 | 0,517 | 0,008 |
| PatchTST | red neuronal | -0,066 | -0,019 | -0,056 a 0,001 | 0,110 | 0,138 |

Lectura (regla IC90): habilidad del modelo elegido confirmada (IC90 > 0 y DM p < 0,10). Habilidad frente a persistencia en prueba: 0,342. Cobertura del intervalo conformal del 90 % en prueba: 0,833 (ancho 4,337).

Categoría sequía (SPI-3 ≤ −1) en prueba: aciertos 0, falsas alarmas 0, fallos 3; POD 0,000, FAR —, CSI 0,000.

- Decisión: **Se publica**.

## Sequía (SPI-3) · CHIRPS

Fuente de la lluvia para el SPI: **CHIRPS**.

Regímenes del SPI-3 (PELT): 2 puntos de cambio (2002-11-01, 2011-08-01).

### SPI-3 dentro de 1 mes(es) (ventana 4 meses)

| Partición | Meses |
|---|---|
| entrenamiento | 411 |
| validacion | 60 |
| prueba | 60 |

Métrica principal: habilidad (1 − ECM/ECM de la climatología). En **negrita**, el modelo elegido por validación (la prueba no participa en la elección).

| Modelo | Familia | Validación | Prueba | IC90 prueba | p Diebold-Mariano | Dispersión entre semillas |
|---|---|---|---|---|---|---|
| Climatología (referencia) | referencia | 0,000 | 0,000 | 0,000 a 0,000 | — |  |
| Persistencia (referencia) | referencia | -0,114 | -0,053 | -0,501 a 0,359 | 0,844 |  |
| **Ridge** | clasico | 0,658 | 0,576 | 0,474 a 0,670 | 0,008 |  |
| Ensamble ponderado (pesos de validación) | ensamble | 0,639 | 0,568 | 0,470 a 0,660 | 0,008 |  |
| Ensamble (3 mejores en validación) | ensamble | 0,570 | 0,498 | 0,419 a 0,604 | 0,008 |  |
| Gradient boosting | clasico | 0,517 | 0,408 | 0,300 a 0,535 | 0,018 |  |
| N-BEATS | red neuronal | 0,513 | 0,370 | 0,229 a 0,536 | 0,033 | 0,029 |
| N-HiTS | red neuronal | 0,513 | 0,370 | 0,229 a 0,536 | 0,033 | 0,029 |
| MLP | red neuronal | 0,486 | 0,380 | 0,248 a 0,540 | 0,027 | 0,106 |
| DLinear | red neuronal | 0,479 | 0,438 | 0,377 a 0,530 | 0,000 | 0,162 |
| GRU | red neuronal | 0,425 | 0,287 | 0,197 a 0,425 | 0,020 | 0,040 |
| TCN | red neuronal | 0,408 | 0,284 | 0,148 a 0,467 | 0,024 | 0,035 |
| LSTM | red neuronal | 0,379 | 0,210 | 0,106 a 0,371 | 0,043 | 0,034 |
| iTransformer | red neuronal | 0,329 | 0,428 | 0,330 a 0,551 | 0,003 | 0,022 |
| SSM selectivo | red neuronal | 0,190 | 0,215 | 0,100 a 0,397 | 0,009 | 0,062 |
| PatchTST | red neuronal | 0,125 | 0,125 | 0,075 a 0,181 | 0,005 | 0,048 |

Lectura (regla IC90): habilidad del modelo elegido confirmada (IC90 > 0 y DM p < 0,10). Habilidad frente a persistencia en prueba: 0,598. Cobertura del intervalo conformal del 90 % en prueba: 0,883 (ancho 2,354).

Categoría sequía (SPI-3 ≤ −1) en prueba: aciertos 1, falsas alarmas 1, fallos 1; POD 0,500, FAR 0,500, CSI 0,333.

- Decisión: **Se publica**.

### SPI-3 dentro de 3 mes(es) (ventana 3 meses)

| Partición | Meses |
|---|---|
| entrenamiento | 410 |
| validacion | 60 |
| prueba | 60 |

Métrica principal: habilidad (1 − ECM/ECM de la climatología). En **negrita**, el modelo elegido por validación (la prueba no participa en la elección).

| Modelo | Familia | Validación | Prueba | IC90 prueba | p Diebold-Mariano | Dispersión entre semillas |
|---|---|---|---|---|---|---|
| Climatología (referencia) | referencia | 0,000 | 0,000 | 0,000 a 0,000 | — |  |
| Persistencia (referencia) | referencia | -0,621 | -0,498 | -1,104 a 0,055 | 0,114 |  |
| **DLinear** | red neuronal | 0,053 | 0,083 | 0,046 a 0,109 | 0,006 | 0,025 |
| Ensamble ponderado (pesos de validación) | ensamble | 0,053 | 0,083 | 0,046 a 0,109 | 0,006 |  |
| Ensamble (3 mejores en validación) | ensamble | 0,011 | -0,011 | -0,024 a 0,001 | 0,160 |  |
| GRU | red neuronal | -0,011 | -0,099 | -0,157 a -0,045 | 0,014 | 0,065 |
| LSTM | red neuronal | -0,018 | -0,033 | -0,051 a -0,017 | 0,003 | 0,033 |
| MLP | red neuronal | -0,038 | -0,098 | -0,141 a -0,052 | 0,011 | 0,045 |
| PatchTST | red neuronal | -0,078 | -0,028 | -0,083 a 0,018 | 0,344 | 0,023 |
| TCN | red neuronal | -0,080 | -0,240 | -0,431 a -0,086 | 0,023 | 0,019 |
| iTransformer | red neuronal | -0,093 | -0,177 | -0,263 a -0,082 | 0,018 | 0,054 |
| N-BEATS | red neuronal | -0,141 | -0,339 | -0,525 a -0,150 | 0,012 | 0,056 |
| N-HiTS | red neuronal | -0,141 | -0,339 | -0,525 a -0,150 | 0,012 | 0,056 |
| Gradient boosting | clasico | -0,144 | -0,353 | -0,682 a -0,050 | 0,059 |  |
| SSM selectivo | red neuronal | -0,165 | -0,205 | -0,352 a -0,046 | 0,035 | 0,060 |
| Ridge | clasico | -0,167 | -0,381 | -0,626 a -0,166 | 0,023 |  |

Lectura (regla IC90): habilidad del modelo elegido confirmada (IC90 > 0 y DM p < 0,10). Habilidad frente a persistencia en prueba: 0,388. Cobertura del intervalo conformal del 90 % en prueba: 0,950 (ancho 4,006).

Categoría sequía (SPI-3 ≤ −1) en prueba: aciertos 0, falsas alarmas 0, fallos 2; POD 0,000, FAR —, CSI 0,000.

- Decisión: **Se publica**.

## Sismos (USGS ComCat)

Catálogo: 4 052 eventos a menos de 350 km de Arequipa, 1973-01-08 a 2026-10-30.

| Magnitud | Valor |
|---|---|
| Mc por máxima curvatura | 4,4 |
| Mc usada (conservadora) | 4,5 |
| b (todos, M ≥ Mc) | 0,997 (IC90 0,962 a 1,031), n = 2 029 |
| b (desagrupados) | 0,900 (IC90 0,863 a 0,938), n = 1 257 |
| Independientes / dependientes (Gardner-Knopoff) | 1 257 / 772 |
| CV de intereventos independientes | 1,071 |
| Tasa anual M ≥ Mc | 37,71 |

CV ≈ 1 es lo esperado en un proceso de Poisson; > 1, agrupamiento; < 1, cuasiperiodicidad.

### Conteo mensual del mes siguiente (conteo mensual de sismos M ≥ 4.5 del mes siguiente)

Métrica principal: ganancia de información frente a Poisson de tasa constante (bits/mes). En **negrita**, el modelo elegido por validación (la prueba no participa en la elección).

| Modelo | Familia | Validación | Prueba | IC90 prueba | p Diebold-Mariano | Dispersión entre semillas |
|---|---|---|---|---|---|---|
| Climatología (referencia) | referencia | 0,000 | 0,000 | 0,000 a 0,000 | — |  |
| Persistencia (referencia) | referencia | -0,759 | -0,804 | -1,223 a -0,259 | 0,009 |  |
| **LSTM** | red neuronal | 0,287 | 0,257 | 0,057 a 0,495 | 0,073 | 0,008 |
| Ensamble ponderado (pesos de validación) | ensamble | 0,270 | 0,257 | 0,057 a 0,495 | 0,073 |  |
| Ensamble (3 mejores en validación) | ensamble | 0,210 | 0,222 | 0,050 a 0,426 | 0,066 |  |
| PatchTST | red neuronal | 0,192 | 0,159 | -0,002 a 0,366 | 0,168 | 0,033 |
| GRU | red neuronal | 0,192 | 0,191 | 0,046 a 0,388 | 0,092 | 0,091 |
| N-HiTS | red neuronal | 0,182 | 0,215 | 0,026 a 0,442 | 0,096 | 0,035 |
| TCN | red neuronal | 0,160 | 0,223 | 0,071 a 0,432 | 0,041 | 0,037 |
| iTransformer | red neuronal | 0,142 | 0,020 | -0,120 a 0,276 | 0,882 | 0,060 |
| N-BEATS | red neuronal | 0,096 | 0,175 | 0,047 a 0,361 | 0,070 | 0,050 |
| DLinear | red neuronal | 0,041 | 0,059 | -0,090 a 0,303 | 0,651 | 0,105 |
| MLP | red neuronal | 0,022 | 0,080 | -0,103 a 0,316 | 0,569 | 0,077 |
| SSM selectivo | red neuronal | -0,121 | -0,113 | -0,302 a 0,056 | 0,324 | 0,106 |
| Gradient boosting | clasico | -0,238 | -0,074 | -0,544 a 0,306 | 0,775 |  |
| GLM de Poisson | clasico | -0,306 | -0,494 | -0,798 a -0,120 | 0,032 |  |

Lectura (regla IC90): confirmada (IC90 > 0 y DM p < 0,10). No es un pronóstico de sismos. Mide si hay estructura temporal (agrupamiento) más allá del azar.

- Decisión: **Se publica**.

### Sismos de M ≥ 6,5

| Fecha (UTC) | M | Profundidad (km) | Lugar |
|---|---|---|---|
| 1979-02-16 | 6,9 | 53 | 24 km NNE of El Cardo, Peru |
| 1983-02-25 | 6,9 | 146 | 77 km SE of Palca, Peru |
| 1984-06-18 | 6,5 | 117 | 7 km WNW of Uñon, Peru |
| 1987-08-08 | 7,2 | 70 | 68 km SSE of Arica, Chile |
| 1987-08-13 | 6,6 | 36 | 36 km SSW of Locumba, Peru |
| 1988-04-12 | 7,1 | 33 | 30 km SW of Islay (Matarani), Peru |
| 1991-05-24 | 6,8 | 128 | 13 km SSE of Chojata, Peru |
| 1999-04-03 | 6,8 | 87 | 6 km SE of Camaná, Peru |
| 2001-06-23 | 8,4 | 33 | 6 km SSW of Atico, Peru |
| 2001-06-26 | 6,7 | 24 | 34 km WSW of Pacocha, Peru |
| 2001-07-05 | 6,6 | 62 | 31 km S of Achanizo, Peru |
| 2001-07-07 | 7,6 | 33 | 51 km SW of Punta de Bombón, Peru |
| 2013-09-25 | 7,1 | 40 | 16 km WSW of Atiquipa, Peru |
| 2014-08-24 | 6,8 | 101 | 38 km NW of Aniso, Peru |
| 2018-01-14 | 7,1 | 39 | 37 km W of Atiquipa, Peru |
| 2019-03-01 | 7,0 | 267 | 22 km NNE of Azángaro, Peru |
| 2022-05-26 | 7,2 | 236 | 10 km W of Azángaro, Peru |
| 2024-06-28 | 7,2 | 24 | 10 km WSW of Atiquipa, Peru |
| 2026-08-20 | 6,7 | 99 | 35 km ENE of Tambo, Peru |

## Volcanes (Smithsonian GVP)

Frecuencia histórica de inicio de erupción desde 1550 (Poisson n/T con T desde 1550 hasta el año actual; IC exacto de Garwood (chi-cuadrado), 90 %).

| Volcán | Distancia a Arequipa (km) | Erupciones desde 1550 | P anual (%) | IC90 (%) | Intervalo medio (años) | IEV máximo |
|---|---|---|---|---|---|---|
| Ubinas | 68,3 | 22 | 4,51 | 3,07 a 6,37 | 22,6 | 3 |
| Sabancaya | 76,4 | 9 | 1,87 | 0,98 a 3,24 | 34,4 | 3 |
| Misti, El | 17,8 | 4 | 0,84 | 0,29 a 1,90 | 102,7 | 2 |
| Tutupaca | 142,1 | 2 | 0,42 | 0,07 a 1,31 | 15,0 | 4 |
| Huaynaputina | 76,4 | 1 | 0,21 | 0,01 a 0,99 | — | 6 |
| Ticsani | 107,5 | 1 | 0,21 | 0,01 a 0,99 | — | 0 |
| Andahua-Orcopampa | 138,2 | 0 | 0,00 | 0,00 a 0,63 | — | — |
| Huambo | 90,2 | 0 | 0,00 | 0,00 a 0,63 | — | — |
| Quimsachata-Oroscocha | 253,0 | 0 | 0,00 | 0,00 a 0,63 | — | — |
| Yucamane | 167,1 | 0 | 0,00 | 0,00 a 0,63 | — | — |

- Decisión: **Abstención**.
- Motivo: Sin datos de monitoreo continuo (sismicidad volcánica, gases, deformación) no se pronostican erupciones.
- Advertencia: La probabilidad anual es una frecuencia histórica; el estado actual de cada volcán lo informa el OVS-IGP.

## Deslizamientos (NASA GLC + POWER)

58 deslizamientos en Perú en el catálogo; 30 en el dominio sur; 28 detonados por lluvia con serie de lluvia.

| Acumulado | Mediana del percentil del mismo mes | Fracción sobre p75 |
|---|---|---|
| 1d | 60,0 | 0,250 |
| 3d | 67,8 | 0,464 |
| 10d | 60,6 | 0,357 |
| 30d | 64,6 | 0,321 |

- Decisión: **Abstención**.
- Motivo: Solo 28 deslizamientos detonados por lluvia en el dominio: se necesitan al menos 30 para estimar un umbral de lluvia.
- Advertencia: El catálogo GLC se basa en noticias: subregistra eventos rurales y su cobertura principal es 2007–2017.

## Dinámica: caos, no linealidad o ruido

Un veredicto 'compatible_con_caos_baja_dimension' exigiría no linealidad, determinismo, D2 saturado bajo, λ > 0 y K > 0,8 a la vez. Los métodos se validaron antes con Lorenz, Hénon, el mapa logístico, AR(1), ruido y un seno (tests/caos).

| Serie | n | Veredicto | p asimetría temporal | p predicción por análogos | D2 | λ | K (0-1) |
|---|---|---|---|---|---|---|---|
| lluvia pentadas cabecera | 3 348 | **lineal estocástica** | 0,530 | 0,050 | 1,488 | 0,271 | 0,997 |
| temperatura diaria cabecera | 16 740 | **no lineal, sin caos demostrado** | 0,010 | 0,080 | no satura | 0,021 | 0,997 |
| spi3 mensual cabecera | 538 | **lineal estocástica** | 0,100 | 0,540 | no satura | 0,048 | 0,993 |
| oni mensual | 921 | **no lineal, sin caos demostrado** | 0,010 | 0,010 | no satura | -0,002 | 0,999 |
| lluvia pentadas cabecera chirps | 3 341 | **lineal estocástica** | 0,720 | 0,090 | 1,428 | 0,125 | 0,998 |
| sismos conteo mensual | 646 | **lineal estocástica** | 0,860 | 0,710 | 0,000 | 0,062 | 0,997 |
| sismos intereventos log | 1 256 | **no lineal, sin caos demostrado** | 0,960 | 0,010 | no satura | 0,116 | 0,999 |

Resumen: lineal estocástica: 4, no lineal, sin caos demostrado: 3.

En las series sin no linealidad significativa, D2, λ y K se informan pero **no se interpretan**: un proceso lineal estocástico también puede dar un D2 bajo o un K ≈ 1. La prueba 0-1 no distingue caos de ruido.

## Contraste entre fuentes

### Lluvia en la ciudad frente a la estación GHCN (ordenado por r mensual)

| Fuente | Días comunes | r diario | r días húmedos | r mensual | Totales fuente/estación | p99 fuente / estación (mm) |
|---|---|---|---|---|---|---|
| power_ciudad | 7 538 | 0,199 | 0,015 | 0,580 | 0,70 | 7,3 / 13,6 |
| chirps_ciudad_celda_power | 7 538 | 0,200 | 0,035 | 0,441 | 1,87 | 12,3 / 13,6 |
| chirps_ciudad_local | 7 538 | 0,191 | -0,013 | 0,422 | 1,69 | 15,0 / 13,6 |
| imerg_ciudad | 464 | 0,277 | 0,130 | — | 0,69 | 10,4 / 18,5 |

### Lluvia en la cabecera entre productos

| Par | Días | r diario | r mensual | Media anual (mm) | Días ≥ 1 mm |
|---|---|---|---|---|---|
| power_cabecera · chirps_cabecera_celda_power | 16 709 | 0,318 | 0,800 | 198 / 470 | 0,132 / 0,270 |
| power_cabecera · chirps_cabecera_local | 16 709 | 0,290 | 0,781 | 198 / 448 | 0,132 / 0,241 |
| power_cabecera · imerg_cabecera | 1 096 | 0,234 | 0,880 | 207 / 419 | 0,149 / 0,242 |
| chirps_cabecera_celda_power · chirps_cabecera_local | 16 709 | 0,940 | 0,992 | 470 / 448 | 0,270 / 0,241 |
| chirps_cabecera_celda_power · imerg_cabecera | 1 096 | 0,610 | 0,982 | 490 / 419 | 0,272 / 0,242 |
| chirps_cabecera_local · imerg_cabecera | 1 096 | 0,584 | 0,982 | 475 / 419 | 0,254 / 0,242 |

### Tendencia de la lluvia de dic–mar por fuente (Theil-Sen; p conservador de Mann-Kendall)

| Fuente | Periodo | Media (mm) | Sen (mm/década) | IC90 | p |
|---|---|---|---|---|---|
| power_cabecera | 1982–2026 | 151 | 21,2 | 7,0 a 32,7 | 0,036 |
| chirps_cabecera_celda_power | 1982–2026 | 395 | 31,6 | 10,2 a 51,3 | 0,035 |
| chirps_cabecera_local | 1982–2026 | 378 | 21,2 | 1,0 a 37,3 | 0,117 |

### Temperatura

| Variable de la estación GHCN | Días | Sesgo POWER − estación (°C) | r de anomalías diarias |
|---|---|---|---|
| TMAX | 8 578 | -3,19 | 0,401 |
| TMIN | 12 135 | -3,65 | 0,518 |

| Punto | Banda MODIS | Frente a | Compuestos | r de anomalías | Media LST / POWER (°C) |
|---|---|---|---|---|---|
| ciudad | LST_Day_1km | T2M_MAX | 1 219 | 0,224 | 32,1 / 19,4 |
| ciudad | LST_Night_1km | T2M_MIN | 1 164 | 0,227 | 10,8 / 5,0 |
| cabecera | LST_Day_1km | T2M_MAX | 1 208 | 0,322 | 28,6 / 15,2 |
| cabecera | LST_Night_1km | T2M_MIN | 1 185 | 0,448 | -4,2 / -0,3 |

| Fuente | Periodo | Media (°C) | Sen (°C/década) | IC90 | p |
|---|---|---|---|---|---|
| modis_lst_ciudad | 2001–2025 | 21,60 | -0,472 | -0,777 a -0,150 | 0,107 |
| power_t2m_ciudad | 2001–2025 | 11,12 | 0,282 | 0,111 a 0,498 | 0,172 |
| modis_lst_cabecera | 2001–2025 | 12,51 | -0,044 | -0,403 a 0,289 | 0,907 |
| power_t2m_cabecera | 2001–2025 | 6,09 | 0,203 | 0,120 a 0,415 | 0,385 |
| power_t2m_ciudad | 1981–2025 | 10,84 | 0,274 | 0,202 a 0,342 | 0,011 |

MODIS LST mide la superficie, no el aire: los niveles difieren por construcción. Se comparan anomalías y tendencias en el mismo periodo (2001–2025).

### Sismos: USGS frente a IGP

| Magnitud | Valor |
|---|---|
| Periodo | 2012-01-07 a 2026-11-13 |
| Reportados por el IGP (radio) | 3 273 |
| USGS M ≥ 4 (mismo periodo) | 1 882 |
| Emparejados | 1 097 (\|Δt\| ≤ 60 s y distancia ≤ 100 km) |
| Fracción de USGS M ≥ 4,5 con reporte IGP | 0,719 |
| M IGP − M USGS (media ± desviación) | -0,08 ± 0,26 |
| Distancia epicentral mediana (km) | 17,4 |
| Mc del IGP (máxima curvatura) | 4,1 |

El IGP publica los sismos que reporta (percibidos o relevantes), no su catálogo completo de detección.

### Fuentes no usadas y por qué

- **SMAP (NSIDC)**: Acceso con token verificado, pero empieza en 2015 (después del entrenamiento) y solo se distribuye por gránulo global; no aporta a los experimentos con la partición congelada.
- **HLS (LP DAAC)**: Acceso con token verificado; reflectancia a 30 m sin relación directa con las variables objetivo de estos experimentos.
- **SENAMHI, ANA, CENEPRED, SINIA, INGEMMET**: Sin API pública de datos (ver docs/verificacion/fuentes_fenomenos.json); se integrarán por convenio o descarga manual verificada.

## Escala nacional · 25 departamentos

**Clima:** NASA POWER (MERRA-2), celda de la capital de cada departamento. Tendencias 1981–2025 con el Sello de Confianza del paquete; SPI con parámetros gamma del entrenamiento (último mes disponible). Con una sola familia de datos el Sello no puede dar 'robusta': la independencia queda pendiente.

| Departamento | T media (°C) | Tendencia T (°C/década) [IC90] · Sello | Lluvia anual (mm) | Tendencia lluvia (mm/década) · Sello | SPI-12 | Deslizamientos GLC |
|---|---|---|---|---|---|---|
| Amazonas | 17,0 | 0,29 [0,20 a 0,41] · preliminar | 550 | -58,2 · sin_tendencia | -0,38 | 0 |
| Áncash | 8,1 | 0,29 [0,18 a 0,38] · preliminar | 416 | -38,6 · no_decidible | 2,15 | 5 |
| Apurímac | 12,0 | 0,12 [0,03 a 0,23] · sin_tendencia | 672 | 37,4 · sin_tendencia | 0,83 | 3 |
| Arequipa | 10,8 | 0,27 [0,20 a 0,34] · preliminar | 136 | 23,9 · preliminar | 2,38 (no interpretable: clima árido) | 5 |
| Ayacucho | 9,2 | 0,09 [0,02 a 0,18] · fragil | 540 | 42,4 · fragil | 1,95 | 2 |
| Cajamarca | 14,2 | 0,22 [0,12 a 0,31] · preliminar | 467 | 18,1 · no_decidible | 1,37 | 0 |
| Callao | 18,2 | 0,15 [0,06 a 0,25] · preliminar | 30 | 2,5 · no_decidible | 4,74 (no interpretable: clima árido) | 0 |
| Cusco | 8,3 | 0,15 [0,06 a 0,23] · fragil | 698 | 31,3 · sin_tendencia | 0,73 | 15 |
| Huancavelica | 5,3 | 0,14 [0,06 a 0,23] · fragil | 345 | 16,0 · no_decidible | 1,98 | 2 |
| Huánuco | 9,7 | 0,22 [0,15 a 0,30] · preliminar | 611 | -8,7 · no_decidible | -0,05 | 4 |
| Ica | 18,6 | 0,18 [0,11 a 0,27] · preliminar | 82 | 22,4 · preliminar | 4,75 (no interpretable: clima árido) | 0 |
| Junín | 8,7 | 0,17 [0,09 a 0,24] · preliminar | 370 | 14,3 · no_decidible | 2,21 | 1 |
| La Libertad | 17,8 | 0,23 [0,14 a 0,30] · preliminar | 195 | 20,4 · fragil | 2,92 (no interpretable: clima árido) | 2 |
| Lambayeque | 20,5 | -0,01 [-0,17 a 0,13] · no_decidible | 90 | 13,7 · fragil | 1,90 (no interpretable: clima árido) | 0 |
| Lima (misma celda que callao) | 18,2 | 0,15 [0,06 a 0,25] · preliminar | 30 | 2,5 · no_decidible | 4,74 (no interpretable: clima árido) | 10 |
| Loreto | 25,7 | 0,09 [0,03 a 0,15] · fragil | 2657 | 294,6 · sin_tendencia | 0,10 | 0 |
| Madre de Dios | 25,3 | -0,03 [-0,20 a 0,12] · no_decidible | 2003 | 178,7 · preliminar | 1,50 | 0 |
| Moquegua | 7,1 | 0,28 [0,22 a 0,34] · preliminar | 129 | 7,2 · sin_tendencia | 1,81 (no interpretable: clima árido) | 0 |
| Pasco | 7,0 | 0,18 [0,10 a 0,24] · preliminar | 324 | 6,4 · no_decidible | 1,28 | 1 |
| Piura | 25,4 | 0,14 [0,02 a 0,25] · sin_tendencia | 202 | -21,7 · no_decidible | 0,58 | 0 |
| Puno | 7,9 | 0,21 [0,13 a 0,30] · preliminar | 423 | 26,6 · sin_tendencia | 1,57 | 4 |
| San Martín | 22,3 | 0,21 [0,04 a 0,36] · sin_tendencia | 987 | -0,3 · no_decidible | -0,56 | 3 |
| Tacna | 15,0 | 0,27 [0,22 a 0,36] · preliminar | 60 | -4,9 · no_decidible | 1,39 (no interpretable: clima árido) | 0 |
| Tumbes | 24,7 | 0,27 [0,16 a 0,38] · preliminar | 413 | 23,3 · no_decidible | 0,05 | 0 |
| Ucayali | 27,0 | 0,48 [0,30 a 0,66] · preliminar | 1349 | -82,9 · sin_tendencia | 0,13 | 0 |

Veredictos (mismo vocabulario que la API: 'preliminar' = significativa con pruebas pendientes) por celda climática distinta: temperatura fragil 4, no_decidible 2, preliminar 15, sin_tendencia 3; lluvia fragil 3, no_decidible 11, preliminar 3, sin_tendencia 7.

**Sismicidad nacional:** USGS ComCat (FDSN), caja [-81.5, -18.5, -68.5, 0.0], 1973-01-15 a 2026-11-13: 5 710 sismos M ≥ 4,5; Mc = 4,7; b = 1,035 (IC90 1,006 a 1,065); tasa anual M ≥ Mc = 69,8.

| Franja | b | n |
|---|---|---|
| norte (0° a −8°) | 1,006 | 1110 |
| centro (−8° a −14°) | 1,070 | 1071 |
| sur (−14° a −18,5°) | 1,034 | 1578 |

Tasas históricas del catálogo global; no son pronósticos. El IGP mantiene el catálogo nacional oficial.

## Historial de métricas · origen móvil y dinámica en ventanas

Para cada año Y desde 2016: entrenamiento con datos ≤ Y−2, validación en Y−1 y prueba en Y, con el **diseño congelado** del experimento principal (variables, ventana y red). Los años hasta 2020 se usaron para elegir ese diseño (lectura optimista); los posteriores son **fuera de muestra**. Semillas por corte: 0. Por año la muestra es pequeña; la lectura principal es la habilidad agregada por régimen.

### lluvia diaria en la cabecera ≥ 3.22 mm (p90 de dic–mar, entrenamiento; POWER)

Métrica: habilidad de Brier frente a la climatología. Red congelada: SSM selectivo, ventana 14.

| Año | Régimen | n | Elegido en validación | SSM selectivo [IC90] | Clásico elegido en validación | Persistencia |
|---|---|---|---|---|---|---|
| 2016 | validación del diseño | 182 | Ensamble ponderado (pesos de validación) 0,117 | 0,110 [0,019 a 0,197] | Gradient boosting 0,087 | 0,082 |
| 2017 | validación del diseño | 181 | Regresión logística 0,101 | 0,174 [0,044 a 0,315] | Regresión logística 0,101 | 0,117 |
| 2018 | validación del diseño | 181 | Ensamble (3 mejores en validación) 0,052 | 0,020 [-0,144 a 0,144] | Regresión logística 0,037 | -0,015 |
| 2019 | validación del diseño | 181 | Regresión logística -0,073 | 0,016 [-0,099 a 0,102] | Regresión logística -0,073 | -0,053 |
| 2020 | validación del diseño | 182 | Ensamble (3 mejores en validación) 0,264 | 0,271 [0,126 a 0,386] | Gradient boosting 0,153 | 0,033 |
| 2021 | fuera de muestra | 181 | Regresión logística -0,207 | -0,457 [-1,025 a -0,221] | Regresión logística -0,207 | -0,048 |
| 2022 | fuera de muestra | 181 | SSM selectivo -0,073 | -0,073 [-0,146 a -0,034] | Gradient boosting -0,029 | -0,117 |
| 2023 | fuera de muestra | 181 | Ensamble (3 mejores en validación) 0,064 | 0,051 [0,004 a 0,108] | Regresión logística 0,066 | 0,046 |
| 2024 | fuera de muestra | 182 | Ensamble (3 mejores en validación) 0,049 | 0,051 [-0,149 a 0,180] | Regresión logística -0,033 | 0,048 |
| 2025 | fuera de muestra | 181 | Gradient boosting 0,022 | 0,168 [-0,134 a 0,401] | Gradient boosting 0,022 | 0,027 |
| 2026 | fuera de muestra | 120 | Regresión logística 0,233 | 0,227 [-0,023 a 0,387] | Regresión logística 0,233 | 0,082 |

Agregado por régimen (predicciones concatenadas). En **negrita**, la lectura principal: el modelo que eligió la validación de cada año (el procedimiento completo, sin mirar la prueba). Las demás filas son comparaciones: elegir entre ellas la de mejor cifra en la prueba sería sesgo de selección.

| Régimen | Modelo | Habilidad | IC90 | p DM | Lectura | Bloque | Años |
|---|---|---|---|---|---|---|---|
| fuera de muestra | **Elegido en validación (año a año)** | 0,031 | -0,040 a 0,090 | 0,461 | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | 10 | 6 |
| fuera de muestra | SSM selectivo | 0,037 | -0,060 a 0,129 | 0,556 | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | 18 | 6 |
| fuera de muestra | Gradient boosting | 0,031 | -0,033 a 0,090 | 0,463 | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | 10 | 6 |
| fuera de muestra | Regresión logística | 0,019 | -0,059 a 0,090 | 0,696 | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | 10 | 6 |
| fuera de muestra | Ensamble ponderado (pesos de validación) | 0,048 | -0,023 a 0,107 | 0,292 | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | 10 | 6 |
| fuera de muestra | Ensamble (3 mejores en validación) | 0,072 | 0,001 a 0,140 | 0,149 | indicio (solo una de las dos pruebas: IC90 > 0 o DM p < 0,10) | 10 | 6 |
| fuera de muestra | Climatología (referencia) | 0,000 | 0,000 a 0,000 | — | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | 10 | 6 |
| fuera de muestra | Persistencia (referencia) | 0,015 | -0,032 a 0,066 | 0,614 | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | 10 | 6 |
| validación del diseño | **Elegido en validación (año a año)** | 0,112 | 0,028 a 0,164 | 0,021 | confirmada (IC90 > 0 y DM p < 0,10) | 10 | 5 |
| validación del diseño | SSM selectivo | 0,136 | 0,063 a 0,184 | 0,003 | confirmada (IC90 > 0 y DM p < 0,10) | 10 | 5 |
| validación del diseño | Gradient boosting | 0,048 | -0,018 a 0,106 | 0,305 | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | 25 | 5 |
| validación del diseño | Regresión logística | 0,111 | 0,024 a 0,168 | 0,028 | confirmada (IC90 > 0 y DM p < 0,10) | 10 | 5 |
| validación del diseño | Ensamble ponderado (pesos de validación) | 0,127 | 0,054 a 0,173 | 0,006 | confirmada (IC90 > 0 y DM p < 0,10) | 10 | 5 |
| validación del diseño | Ensamble (3 mejores en validación) | 0,135 | 0,065 a 0,179 | 0,004 | confirmada (IC90 > 0 y DM p < 0,10) | 10 | 5 |
| validación del diseño | Climatología (referencia) | 0,000 | 0,000 a 0,000 | — | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | 10 | 5 |
| validación del diseño | Persistencia (referencia) | 0,039 | -0,010 a 0,077 | 0,125 | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | 10 | 5 |

### SPI-3 dentro de 1 mes(es)

Métrica: habilidad (1 − ECM/ECM de la climatología). Red congelada: TCN, ventana 3.

| Año | Régimen | n | Elegido en validación | TCN [IC90] | Clásico elegido en validación | Persistencia |
|---|---|---|---|---|---|---|
| 2016 | validación del diseño | 12 | Ensamble (3 mejores en validación) 0,475 | 0,525 [0,466 a 0,628] | Gradient boosting 0,351 | 0,571 |
| 2017 | validación del diseño | 12 | TCN 0,619 | 0,619 [0,503 a 0,897] | Ridge 0,571 | 0,506 |
| 2018 | validación del diseño | 12 | Gradient boosting 0,525 | 0,635 [0,474 a 0,912] | Gradient boosting 0,525 | 0,627 |
| 2019 | validación del diseño | 12 | Ridge 0,782 | 0,675 [0,675 a 0,829] | Ridge 0,782 | -0,308 |
| 2020 | validación del diseño | 12 | Ensamble (3 mejores en validación) 0,531 | 0,475 [0,037 a 0,746] | Ridge 0,484 | 0,425 |
| 2021 | fuera de muestra | 12 | Ensamble (3 mejores en validación) 0,760 | 0,603 [0,112 a 0,623] | Gradient boosting 0,785 | 0,772 |
| 2022 | fuera de muestra | 12 | Ridge 0,131 | 0,260 [0,079 a 0,601] | Ridge 0,131 | -1,078 |
| 2023 | fuera de muestra | 12 | Gradient boosting 0,609 | 0,643 [0,312 a 0,654] | Gradient boosting 0,609 | 0,343 |
| 2024 | fuera de muestra | 12 | Ridge 0,345 | 0,545 [0,537 a 0,705] | Ridge 0,345 | -0,110 |
| 2025 | fuera de muestra | 12 | TCN 0,780 | 0,780 [0,742 a 0,820] | Ridge 0,834 | 0,742 |

Agregado por régimen (predicciones concatenadas). En **negrita**, la lectura principal: el modelo que eligió la validación de cada año (el procedimiento completo, sin mirar la prueba). Las demás filas son comparaciones: elegir entre ellas la de mejor cifra en la prueba sería sesgo de selección.

| Régimen | Modelo | Habilidad | IC90 | p DM | Lectura | Bloque | Años |
|---|---|---|---|---|---|---|---|
| fuera de muestra | **Elegido en validación (año a año)** | 0,658 | 0,531 a 0,743 | 0,021 | confirmada (IC90 > 0 y DM p < 0,10) | 6 | 5 |
| fuera de muestra | TCN | 0,667 | 0,547 a 0,745 | 0,019 | confirmada (IC90 > 0 y DM p < 0,10) | 6 | 5 |
| fuera de muestra | Gradient boosting | 0,660 | 0,548 a 0,734 | 0,017 | confirmada (IC90 > 0 y DM p < 0,10) | 6 | 5 |
| fuera de muestra | Ridge | 0,711 | 0,572 a 0,811 | 0,023 | confirmada (IC90 > 0 y DM p < 0,10) | 6 | 5 |
| fuera de muestra | Ensamble ponderado (pesos de validación) | 0,680 | 0,559 a 0,753 | 0,018 | confirmada (IC90 > 0 y DM p < 0,10) | 6 | 5 |
| fuera de muestra | Ensamble (3 mejores en validación) | 0,710 | 0,595 a 0,786 | 0,016 | confirmada (IC90 > 0 y DM p < 0,10) | 6 | 5 |
| fuera de muestra | Climatología (referencia) | 0,000 | 0,000 a 0,000 | — | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | 6 | 5 |
| fuera de muestra | Persistencia (referencia) | 0,456 | 0,130 a 0,671 | 0,114 | indicio (solo una de las dos pruebas: IC90 > 0 o DM p < 0,10) | 6 | 5 |
| validación del diseño | **Elegido en validación (año a año)** | 0,585 | 0,494 a 0,747 | 0,000 | confirmada (IC90 > 0 y DM p < 0,10) | 6 | 5 |
| validación del diseño | TCN | 0,605 | 0,529 a 0,704 | 0,001 | confirmada (IC90 > 0 y DM p < 0,10) | 6 | 5 |
| validación del diseño | Gradient boosting | 0,582 | 0,512 a 0,730 | 0,000 | confirmada (IC90 > 0 y DM p < 0,10) | 6 | 5 |
| validación del diseño | Ridge | 0,620 | 0,509 a 0,759 | 0,002 | confirmada (IC90 > 0 y DM p < 0,10) | 6 | 5 |
| validación del diseño | Ensamble ponderado (pesos de validación) | 0,579 | 0,489 a 0,733 | 0,000 | confirmada (IC90 > 0 y DM p < 0,10) | 6 | 5 |
| validación del diseño | Ensamble (3 mejores en validación) | 0,635 | 0,562 a 0,757 | 0,000 | confirmada (IC90 > 0 y DM p < 0,10) | 6 | 5 |
| validación del diseño | Climatología (referencia) | 0,000 | 0,000 a 0,000 | — | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | 6 | 5 |
| validación del diseño | Persistencia (referencia) | 0,393 | 0,242 a 0,618 | 0,034 | confirmada (IC90 > 0 y DM p < 0,10) | 6 | 5 |

### SPI-3 dentro de 3 mes(es)

Métrica: habilidad (1 − ECM/ECM de la climatología). Red congelada: iTransformer, ventana 24.

| Año | Régimen | n | Elegido en validación | iTransformer [IC90] | Clásico elegido en validación | Persistencia |
|---|---|---|---|---|---|---|
| 2016 | validación del diseño | 12 | iTransformer 0,294 | 0,294 [0,269 a 0,384] | Ridge -0,182 | -0,104 |
| 2017 | validación del diseño | 12 | iTransformer 0,421 | 0,421 [0,260 a 0,695] | Ridge 0,497 | 0,164 |
| 2018 | validación del diseño | 12 | Ensamble (3 mejores en validación) 0,438 | 0,315 [0,311 a 0,631] | Ridge 0,434 | 0,204 |
| 2019 | validación del diseño | 12 | Gradient boosting 0,363 | 0,282 [0,207 a 0,291] | Gradient boosting 0,363 | -1,720 |
| 2020 | validación del diseño | 12 | Gradient boosting -0,506 | -0,055 [-0,706 a 0,187] | Gradient boosting -0,506 | -0,705 |
| 2021 | fuera de muestra | 12 | iTransformer 0,154 | 0,154 [-0,954 a 0,200] | Gradient boosting 0,072 | -0,059 |
| 2022 | fuera de muestra | 12 | iTransformer -0,378 | -0,378 [-0,772 a 0,047] | Ridge -1,329 | -2,811 |
| 2023 | fuera de muestra | 12 | iTransformer 0,092 | 0,092 [0,023 a 0,120] | Gradient boosting 0,175 | -0,369 |
| 2024 | fuera de muestra | 12 | Gradient boosting 0,579 | 0,411 [0,145 a 0,673] | Gradient boosting 0,579 | -0,854 |
| 2025 | fuera de muestra | 12 | Ensamble (3 mejores en validación) 0,439 | 0,422 [0,342 a 0,466] | Gradient boosting 0,416 | 0,086 |

Agregado por régimen (predicciones concatenadas). En **negrita**, la lectura principal: el modelo que eligió la validación de cada año (el procedimiento completo, sin mirar la prueba). Las demás filas son comparaciones: elegir entre ellas la de mejor cifra en la prueba sería sesgo de selección.

| Régimen | Modelo | Habilidad | IC90 | p DM | Lectura | Bloque | Años |
|---|---|---|---|---|---|---|---|
| fuera de muestra | **Elegido en validación (año a año)** | 0,232 | 0,073 a 0,375 | 0,089 | confirmada (IC90 > 0 y DM p < 0,10) | 6 | 5 |
| fuera de muestra | iTransformer | 0,218 | 0,050 a 0,352 | 0,094 | confirmada (IC90 > 0 y DM p < 0,10) | 6 | 5 |
| fuera de muestra | Gradient boosting | 0,239 | 0,061 a 0,383 | 0,133 | indicio (solo una de las dos pruebas: IC90 > 0 o DM p < 0,10) | 6 | 5 |
| fuera de muestra | Ridge | 0,030 | -0,346 a 0,302 | 0,874 | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | 6 | 5 |
| fuera de muestra | Ensamble ponderado (pesos de validación) | 0,231 | 0,077 a 0,383 | 0,084 | confirmada (IC90 > 0 y DM p < 0,10) | 6 | 5 |
| fuera de muestra | Ensamble (3 mejores en validación) | 0,253 | 0,110 a 0,400 | 0,070 | confirmada (IC90 > 0 y DM p < 0,10) | 6 | 5 |
| fuera de muestra | Climatología (referencia) | 0,000 | 0,000 a 0,000 | — | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | 6 | 5 |
| fuera de muestra | Persistencia (referencia) | -0,305 | -0,722 a 0,148 | 0,259 | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | 6 | 5 |
| validación del diseño | **Elegido en validación (año a año)** | 0,265 | 0,040 a 0,458 | 0,135 | indicio (solo una de las dos pruebas: IC90 > 0 o DM p < 0,10) | 6 | 5 |
| validación del diseño | iTransformer | 0,269 | 0,155 a 0,384 | 0,006 | confirmada (IC90 > 0 y DM p < 0,10) | 6 | 5 |
| validación del diseño | Gradient boosting | 0,166 | -0,152 a 0,434 | 0,422 | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | 6 | 5 |
| validación del diseño | Ridge | 0,154 | -0,111 a 0,387 | 0,437 | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | 6 | 5 |
| validación del diseño | Ensamble ponderado (pesos de validación) | 0,307 | 0,105 a 0,470 | 0,070 | confirmada (IC90 > 0 y DM p < 0,10) | 6 | 5 |
| validación del diseño | Ensamble (3 mejores en validación) | 0,270 | 0,080 a 0,435 | 0,078 | confirmada (IC90 > 0 y DM p < 0,10) | 6 | 5 |
| validación del diseño | Climatología (referencia) | 0,000 | 0,000 a 0,000 | — | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | 6 | 5 |
| validación del diseño | Persistencia (referencia) | -0,335 | -0,731 a 0,143 | 0,267 | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | 6 | 5 |

### conteo mensual de sismos M ≥ 4.5 del mes siguiente

Métrica: ganancia de información frente a Poisson de tasa constante (bits/mes). Red congelada: LSTM, ventana 12.

| Año | Régimen | n | Elegido en validación | LSTM [IC90] | Clásico elegido en validación | Persistencia |
|---|---|---|---|---|---|---|
| 2016 | validación del diseño | 12 | LSTM 0,302 | 0,302 [-0,036 a 0,436] | Gradient boosting -0,091 | -0,581 |
| 2017 | validación del diseño | 12 | Ensamble ponderado (pesos de validación) 0,549 | 0,492 [0,280 a 0,658] | GLM de Poisson 0,277 | 0,026 |
| 2018 | validación del diseño | 12 | LSTM 0,220 | 0,220 [-0,206 a 0,307] | GLM de Poisson -0,045 | -0,100 |
| 2019 | validación del diseño | 12 | LSTM 0,237 | 0,237 [0,000 a 0,351] | GLM de Poisson -0,752 | -1,855 |
| 2020 | validación del diseño | 12 | LSTM 0,129 | 0,129 [-0,002 a 0,297] | Gradient boosting -0,560 | -1,348 |
| 2021 | fuera de muestra | 12 | LSTM 0,739 | 0,739 [0,739 a 1,562] | Gradient boosting 0,657 | -0,244 |
| 2022 | fuera de muestra | 12 | Ensamble ponderado (pesos de validación) 0,345 | 0,442 [0,442 a 0,691] | Gradient boosting -0,152 | -0,075 |
| 2023 | fuera de muestra | 12 | LSTM 0,007 | 0,007 [-0,245 a 0,322] | GLM de Poisson -1,272 | -2,073 |
| 2024 | fuera de muestra | 12 | LSTM 0,184 | 0,184 [-0,200 a 0,798] | Gradient boosting -0,392 | -0,180 |
| 2025 | fuera de muestra | 12 | LSTM -0,027 | -0,027 [-0,314 a 0,010] | Gradient boosting -0,473 | -1,025 |
| 2026 | fuera de muestra | 10 | Ensamble ponderado (pesos de validación) -0,454 | -0,120 [-0,122 a -0,057] | GLM de Poisson -0,803 | -1,716 |

Agregado por régimen (predicciones concatenadas). En **negrita**, la lectura principal: el modelo que eligió la validación de cada año (el procedimiento completo, sin mirar la prueba). Las demás filas son comparaciones: elegir entre ellas la de mejor cifra en la prueba sería sesgo de selección.

| Régimen | Modelo | Habilidad | IC90 | p DM | Lectura | Bloque | Años |
|---|---|---|---|---|---|---|---|
| fuera de muestra | **Elegido en validación (año a año)** | 0,149 | -0,029 a 0,395 | 0,281 | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | 6 | 6 |
| fuera de muestra | LSTM | 0,214 | 0,037 a 0,438 | 0,105 | indicio (solo una de las dos pruebas: IC90 > 0 o DM p < 0,10) | 6 | 6 |
| fuera de muestra | Gradient boosting | -0,263 | -0,604 a 0,003 | 0,180 | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | 6 | 6 |
| fuera de muestra | GLM de Poisson | -0,388 | -0,648 a -0,081 | 0,041 | indicio (solo una de las dos pruebas: IC90 > 0 o DM p < 0,10) | 6 | 6 |
| fuera de muestra | Ensamble ponderado (pesos de validación) | 0,124 | -0,053 a 0,378 | 0,374 | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | 6 | 6 |
| fuera de muestra | Ensamble (3 mejores en validación) | 0,016 | -0,202 a 0,242 | 0,910 | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | 6 | 6 |
| fuera de muestra | Climatología (referencia) | 0,000 | 0,000 a 0,000 | — | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | 6 | 6 |
| fuera de muestra | Persistencia (referencia) | -0,862 | -1,261 a -0,351 | 0,003 | indicio (solo una de las dos pruebas: IC90 > 0 o DM p < 0,10) | 6 | 6 |
| validación del diseño | **Elegido en validación (año a año)** | 0,288 | 0,071 a 0,461 | 0,024 | confirmada (IC90 > 0 y DM p < 0,10) | 6 | 5 |
| validación del diseño | LSTM | 0,276 | 0,072 a 0,449 | 0,025 | confirmada (IC90 > 0 y DM p < 0,10) | 6 | 5 |
| validación del diseño | Gradient boosting | -0,292 | -0,525 a -0,142 | 0,031 | indicio (solo una de las dos pruebas: IC90 > 0 o DM p < 0,10) | 6 | 5 |
| validación del diseño | GLM de Poisson | -0,310 | -0,698 a -0,018 | 0,175 | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | 6 | 5 |
| validación del diseño | Ensamble ponderado (pesos de validación) | 0,276 | 0,068 a 0,439 | 0,028 | confirmada (IC90 > 0 y DM p < 0,10) | 6 | 5 |
| validación del diseño | Ensamble (3 mejores en validación) | 0,073 | -0,149 a 0,247 | 0,572 | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | 6 | 5 |
| validación del diseño | Climatología (referencia) | 0,000 | 0,000 a 0,000 | — | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | 6 | 5 |
| validación del diseño | Persistencia (referencia) | -0,771 | -1,379 a -0,353 | 0,022 | indicio (solo una de las dos pruebas: IC90 > 0 o DM p < 0,10) | 6 | 5 |

### Dinámica en ventanas deslizantes

| Serie | Ventana | Fin de ventana | Ventanas | Entropía de permutación | p ≤ 0,05 sin corregir | Tras corregir (Holm · BH) |
|---|---|---|---|---|---|---|
| lluvia pentadas cabecera | 15 años | 1995–2026 | 32 | 0,971 a 0,982 (orden 5) | 10 de 32 | 0 · 0 |
| temperatura diaria cabecera | 5 años | 1985–2026 | 42 | 0,907 a 0,938 (orden 5) | 9 de 42 | 0 · 0 |
| spi3 mensual cabecera | 25 años | 2005–2025 | 21 | 0,909 a 0,949 (orden 4) | 2 de 21 | 0 · 0 |
| oni mensual | 30 años | 1979–2026 | 48 | 0,553 a 0,749 (orden 4) | 23 de 48 | 0 · 0 |
| lluvia pentadas cabecera chirps | 15 años | 1995–2026 | 32 | 0,963 a 0,972 (orden 5) | 4 de 32 | 0 · 0 |
| sismos conteo mensual | 20 años | 1992–2025 | 34 | 0,916 a 0,951 (orden 4) | 0 de 34 | 0 · 0 |
| sismos intereventos log | 20 años | 1992–2026 | 35 | 0,985 a 0,998 (orden 4) | 0 de 35 | 0 · 0 |

Cada p de ventana se lee por separado y las ventanas se solapan: el conteo sin corregir es descriptivo. Con 39 sustitutos el p mínimo posible es 0,025, así que con decenas de ventanas ninguna puede superar Holm; Benjamini-Hochberg solo las retiene si muchas ventanas llegan al mínimo.

## Limitaciones

- **deslizamientos**: Solo 28 deslizamientos detonados por lluvia en el dominio: se necesitan al menos 30 para estimar un umbral de lluvia.
- **deslizamientos**: El catálogo GLC se basa en noticias: subregistra eventos rurales y su cobertura principal es 2007–2017.
- **lluvia_extrema**: Deriva de las entradas respecto del entrenamiento (PSI > 0,25).
- **lluvia_extrema_chirps**: Deriva de las entradas respecto del entrenamiento (PSI > 0,25).
- **volcanes**: Sin datos de monitoreo continuo (sismicidad volcánica, gases, deformación) no se pronostican erupciones.
- **volcanes**: La probabilidad anual es una frecuencia histórica; el estado actual de cada volcán lo informa el OVS-IGP.
- **lluvia_extrema**: la habilidad del modelo elegido cae de 0,177 en validación a 0,092 en prueba; se informa tal cual (la prueba no se usa para reajustar).
- **sequia h3**: la habilidad del modelo elegido cae de 0,267 en validación a 0,141 en prueba; se informa tal cual (la prueba no se usa para reajustar).
- **sequia_chirps h1**: la habilidad del modelo elegido cae de 0,658 en validación a 0,576 en prueba; se informa tal cual (la prueba no se usa para reajustar).
- **sismos**: la Mc por década supera a la Mc usada (4,5) en 1970s (4,9), 1980s (5,1), 1990s (4,6): el conteo de esos años está incompleto y la tasa aparente crece con el tiempo.
- **sismos**: el conteo mensual incluye réplicas; una ganancia frente a Poisson refleja agrupamiento (réplicas), no capacidad de pronosticar sismos.
- Los resultados son experimentales y describen la escala de cada producto (celdas de 0,05° a 0,5°), no puntos.
- Ningún resultado es una alerta oficial: las emiten SENAMHI, IGP, INGEMMET e INDECI.
