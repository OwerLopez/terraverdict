# Resultados de los experimentos

> Generado automáticamente por `tv informe` desde `resultados/*.json`. No editar a mano: cada cifra sale de esos archivos, que guardan su procedencia completa.

| Campo | Valor |
|---|---|
| Generado (UTC) | 2026-11-15T10:06:56+00:00 |
| Commit del código | `eec6c5cc8532ca0e7ecb1c616630c17a1cf75673` |
| Modo | completo |
| Configuración (SHA-256) | `3cbb05a406bb35a4…` |
| Versiones | python 3.13.15, numpy 2.5.4, torch 2.15.0+cpu, scikit_learn 1.9.1 |
| Crudos con hash | 73 |
| Tiempo por experimento (s) | volcanes 0, deslizamientos 0, sismos 14, fuentes 1, sequia 56, sequia_chirps 27, lluvia_extrema 173, lluvia_extrema_chirps 159, caos 55, nacional 53 |

**Cómo leer.** La partición es temporal y está congelada (entrenamiento 1981–2015, validación 2016–2020, prueba 2021–2026). Todo se elige con validación; la prueba se usa una vez. Una habilidad está **confirmada** solo si su IC90 por bootstrap de bloques queda por encima de 0 **y** la prueba de Diebold-Mariano frente a la climatología da p < 0,10; si solo se cumple una de las dos, es un **indicio**.

## Resumen

| Tarea | Modelo elegido (validación) | Habilidad en prueba | IC90 | p DM | Lectura | Publicación |
|---|---|---|---|---|---|---|
| Lluvia fuerte t+1 · POWER | SSM selectivo | 0,080 | 0,003 a 0,151 | 0,152 | indicio (solo una de las dos pruebas: IC90 > 0 o DM p < 0,10) | publica |
| Lluvia fuerte t+1 · CHIRPS | Ensamble (3 mejores en validación) | 0,046 | -0,007 a 0,090 | 0,165 | no confirmada (IC90 incluye 0 y DM p ≥ 0,10) | publica |
| SPI-3 a 1 mes(es) · POWER | N-BEATS | 0,776 | 0,675 a 0,843 | 0,017 | confirmada (IC90 > 0 y DM p < 0,10) | publica |
| SPI-3 a 3 mes(es) · POWER | iTransformer | 0,198 | 0,119 a 0,263 | 0,013 | confirmada (IC90 > 0 y DM p < 0,10) | publica |
| SPI-3 a 1 mes(es) · CHIRPS | Ensamble (3 mejores en validación) | 0,616 | 0,491 a 0,770 | 0,015 | confirmada (IC90 > 0 y DM p < 0,10) | publica |
| SPI-3 a 3 mes(es) · CHIRPS | DLinear | 0,087 | 0,048 a 0,114 | 0,003 | confirmada (IC90 > 0 y DM p < 0,10) | publica |
| Conteo sísmico mensual | Ensamble (3 mejores en validación) | 0,253 | 0,066 a 0,492 | 0,074 | confirmada (IC90 > 0 y DM p < 0,10); refleja agrupamiento de réplicas, no es pronóstico de sismos | publica |

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
| **SSM selectivo** | red neuronal | 0,235 | 0,080 | 0,003 a 0,151 | 0,152 | 0,019 |
| Ensamble (3 mejores en validación) | ensamble | 0,230 | 0,099 | 0,028 a 0,168 | 0,068 |  |
| LSTM | red neuronal | 0,210 | 0,096 | 0,020 a 0,164 | 0,081 | 0,008 |
| Regresión logística | clasico | 0,207 | 0,072 | 0,001 a 0,145 | 0,163 |  |
| GRU | red neuronal | 0,207 | 0,084 | 0,019 a 0,147 | 0,105 | 0,061 |
| DLinear | red neuronal | 0,202 | 0,048 | -0,033 a 0,131 | 0,391 | 0,069 |
| iTransformer | red neuronal | 0,201 | 0,048 | -0,026 a 0,122 | 0,353 | 0,041 |
| N-BEATS | red neuronal | 0,193 | 0,117 | 0,052 a 0,176 | 0,021 | 0,034 |
| TCN | red neuronal | 0,188 | 0,113 | 0,045 a 0,180 | 0,036 | 0,055 |
| N-HiTS | red neuronal | 0,185 | 0,097 | 0,025 a 0,164 | 0,066 | 0,028 |
| MLP | red neuronal | 0,179 | 0,086 | 0,017 a 0,157 | 0,109 | 0,009 |
| Gradient boosting | clasico | 0,153 | 0,086 | 0,033 a 0,134 | 0,032 |  |
| PatchTST | red neuronal | 0,047 | 0,001 | -0,043 a 0,036 | 0,959 | 0,080 |

Lectura (regla IC90): habilidad del modelo elegido indicio (solo una de las dos pruebas: IC90 > 0 o DM p < 0,10).

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
| seleccion mrmr | 0,153 / 0,086 | 0,207 / 0,072 | 0,223 / 0,070 |
| solo historia lluvia | 0,142 / 0,031 | 0,198 / 0,084 | 0,209 / 0,088 |
| sin oni | 0,189 / 0,078 | 0,206 / 0,106 | 0,202 / 0,092 |
| todas las variables | 0,203 / 0,054 | 0,208 / 0,090 | 0,212 / 0,047 |

### Calibración del modelo elegido (prueba)

ECE = 0,032.

| Probabilidad pronosticada | Frecuencia observada | n |
|---|---|---|
| 0,000 | 0,022 | 91 |
| 0,007 | 0,024 | 127 |
| 0,051 | 0,025 | 157 |
| 0,082 | 0,083 | 228 |
| 0,158 | 0,107 | 178 |
| 0,370 | 0,306 | 245 |

### Eventos documentados en el periodo de prueba

| Evento | Mes | Días con lluvia fuerte | P media del modelo esos días | P climatológica esos días |
|---|---|---|---|---|
| Represas del sistema Chili con 159 de 409 hm³ útiles | 2023-11 | 3 | 0,097 | 0,015 |
| SEDAPAR paraliza sus dos plantas por huaicos y rebose de Aguada Blanca | 2024-03 | 4 | 0,258 | 0,089 |
| Turbidez de 5000 NTU detiene la producción de agua potable | 2025-02 | 9 | 0,513 | 0,151 |
| Segundo episodio de turbidez con el Chili a 50 m³/s | 2025-02 | 9 | 0,513 | 0,151 |

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
| **Ensamble (3 mejores en validación)** | ensamble | 0,109 | 0,046 | -0,007 a 0,090 | 0,165 |  |
| Regresión logística | clasico | 0,090 | -0,024 | -0,105 a 0,045 | 0,622 |  |
| GRU | red neuronal | 0,089 | 0,027 | -0,023 a 0,066 | 0,320 | 0,036 |
| SSM selectivo | red neuronal | 0,087 | 0,016 | -0,059 a 0,088 | 0,703 | 0,045 |
| Gradient boosting | clasico | 0,086 | 0,019 | -0,025 a 0,057 | 0,433 |  |
| N-BEATS | red neuronal | 0,085 | -0,016 | -0,086 a 0,043 | 0,694 | 0,060 |
| iTransformer | red neuronal | 0,083 | 0,075 | 0,014 a 0,127 | 0,043 | 0,080 |
| N-HiTS | red neuronal | 0,080 | -0,014 | -0,065 a 0,031 | 0,611 | 0,054 |
| MLP | red neuronal | 0,075 | -0,030 | -0,108 a 0,034 | 0,491 | 0,011 |
| LSTM | red neuronal | 0,073 | -0,001 | -0,047 a 0,040 | 0,975 | 0,061 |
| TCN | red neuronal | 0,064 | 0,062 | 0,024 a 0,097 | 0,025 | 0,164 |
| DLinear | red neuronal | 0,055 | 0,012 | -0,049 a 0,061 | 0,708 | 0,203 |
| PatchTST | red neuronal | 0,026 | -0,024 | -0,069 a 0,020 | 0,360 | 0,019 |

Lectura (regla IC90): habilidad del modelo elegido no confirmada (IC90 incluye 0 y DM p ≥ 0,10).

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
| seleccion mrmr | 0,086 / 0,019 | 0,089 / 0,038 | 0,090 / -0,024 |
| solo historia lluvia | 0,064 / 0,065 | 0,117 / 0,091 | 0,106 / 0,054 |
| sin oni | 0,068 / 0,075 | 0,100 / 0,082 | 0,086 / 0,058 |
| todas las variables | 0,071 / 0,054 | 0,100 / 0,070 | 0,085 / 0,069 |

### Calibración del modelo elegido (prueba)

ECE = 0,017.

| Probabilidad pronosticada | Frecuencia observada | n |
|---|---|---|
| 0,001 | 0,000 | 74 |
| 0,003 | 0,000 | 129 |
| 0,006 | 0,000 | 104 |
| 0,013 | 0,000 | 78 |
| 0,027 | 0,032 | 125 |
| 0,057 | 0,080 | 88 |
| 0,086 | 0,059 | 119 |
| 0,130 | 0,059 | 102 |
| 0,166 | 0,144 | 104 |
| 0,253 | 0,252 | 103 |

### Eventos documentados en el periodo de prueba

| Evento | Mes | Días con lluvia fuerte | P media del modelo esos días | P climatológica esos días |
|---|---|---|---|---|
| Represas del sistema Chili con 159 de 409 hm³ útiles | 2023-11 | 0 | — | — |
| SEDAPAR paraliza sus dos plantas por huaicos y rebose de Aguada Blanca | 2024-03 | 3 | 0,141 | 0,115 |
| Turbidez de 5000 NTU detiene la producción de agua potable | 2025-02 | 3 | 0,190 | 0,136 |
| Segundo episodio de turbidez con el Chili a 50 m³/s | 2025-02 | 3 | 0,190 | 0,136 |

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
| **N-BEATS** | red neuronal | 0,740 | 0,776 | 0,675 a 0,843 | 0,017 | 0,012 |
| N-HiTS | red neuronal | 0,740 | 0,776 | 0,675 a 0,843 | 0,017 | 0,012 |
| Ensamble (3 mejores en validación) | ensamble | 0,739 | 0,764 | 0,666 a 0,837 | 0,016 |  |
| TCN | red neuronal | 0,718 | 0,724 | 0,615 a 0,806 | 0,015 | 0,012 |
| MLP | red neuronal | 0,681 | 0,720 | 0,627 a 0,784 | 0,016 | 0,021 |
| GRU | red neuronal | 0,639 | 0,655 | 0,561 a 0,731 | 0,014 | 0,019 |
| Ridge | clasico | 0,634 | 0,680 | 0,539 a 0,780 | 0,022 |  |
| LSTM | red neuronal | 0,619 | 0,624 | 0,505 a 0,725 | 0,016 | 0,013 |
| Gradient boosting | clasico | 0,597 | 0,576 | 0,493 a 0,658 | 0,008 |  |
| iTransformer | red neuronal | 0,593 | 0,549 | 0,425 a 0,639 | 0,014 | 0,024 |
| PatchTST | red neuronal | 0,572 | 0,545 | 0,396 a 0,676 | 0,014 | 0,056 |
| SSM selectivo | red neuronal | 0,489 | 0,387 | 0,227 a 0,508 | 0,024 | 0,025 |
| DLinear | red neuronal | 0,306 | 0,275 | 0,203 a 0,337 | 0,014 | 0,253 |

Lectura (regla IC90): habilidad del modelo elegido confirmada (IC90 > 0 y DM p < 0,10). Habilidad frente a persistencia en prueba: 0,587. Cobertura del intervalo conformal del 90 % en prueba: 0,900 (ancho 2,531).

Categoría sequía (SPI-3 ≤ −1) en prueba: aciertos 2, falsas alarmas 0, fallos 1; POD 0,667, FAR 0,000, CSI 0,667.

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
| Persistencia (referencia) | referencia | -0,335 | -0,305 | -0,722 a 0,148 | 0,243 |  |
| **iTransformer** | red neuronal | 0,362 | 0,198 | 0,119 a 0,263 | 0,013 | 0,020 |
| Ensamble (3 mejores en validación) | ensamble | 0,330 | 0,205 | 0,090 a 0,285 | 0,031 |  |
| N-HiTS | red neuronal | 0,301 | 0,209 | 0,065 a 0,321 | 0,084 | 0,023 |
| DLinear | red neuronal | 0,291 | 0,181 | 0,066 a 0,268 | 0,043 | 0,058 |
| N-BEATS | red neuronal | 0,287 | 0,144 | 0,034 a 0,234 | 0,060 | 0,028 |
| GRU | red neuronal | 0,273 | 0,033 | -0,103 a 0,140 | 0,651 | 0,014 |
| MLP | red neuronal | 0,266 | 0,134 | 0,027 a 0,224 | 0,081 | 0,015 |
| LSTM | red neuronal | 0,266 | 0,139 | 0,025 a 0,219 | 0,071 | 0,023 |
| TCN | red neuronal | 0,249 | 0,167 | 0,002 a 0,308 | 0,173 | 0,052 |
| Gradient boosting | clasico | 0,236 | 0,040 | -0,125 a 0,124 | 0,532 |  |
| Ridge | clasico | 0,174 | -0,235 | -0,702 a 0,036 | 0,175 |  |
| SSM selectivo | red neuronal | 0,160 | 0,148 | 0,016 a 0,260 | 0,099 | 0,026 |
| PatchTST | red neuronal | 0,039 | 0,135 | 0,042 a 0,168 | 0,067 | 0,084 |

Lectura (regla IC90): habilidad del modelo elegido confirmada (IC90 > 0 y DM p < 0,10). Habilidad frente a persistencia en prueba: 0,386. Cobertura del intervalo conformal del 90 % en prueba: 0,817 (ancho 4,277).

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
| **Ensamble (3 mejores en validación)** | ensamble | 0,727 | 0,616 | 0,491 a 0,770 | 0,015 |  |
| N-BEATS | red neuronal | 0,727 | 0,600 | 0,471 a 0,758 | 0,018 | 0,019 |
| N-HiTS | red neuronal | 0,727 | 0,600 | 0,471 a 0,758 | 0,018 | 0,019 |
| MLP | red neuronal | 0,713 | 0,633 | 0,517 a 0,782 | 0,011 | 0,018 |
| TCN | red neuronal | 0,681 | 0,530 | 0,449 a 0,666 | 0,010 | 0,027 |
| Ridge | clasico | 0,658 | 0,576 | 0,474 a 0,670 | 0,008 |  |
| LSTM | red neuronal | 0,636 | 0,524 | 0,453 a 0,638 | 0,005 | 0,012 |
| GRU | red neuronal | 0,628 | 0,576 | 0,504 a 0,668 | 0,004 | 0,010 |
| Gradient boosting | clasico | 0,517 | 0,408 | 0,300 a 0,535 | 0,018 |  |
| DLinear | red neuronal | 0,490 | 0,461 | 0,397 a 0,560 | 0,000 | 0,169 |
| iTransformer | red neuronal | 0,459 | 0,533 | 0,436 a 0,625 | 0,002 | 0,075 |
| PatchTST | red neuronal | 0,301 | 0,281 | 0,213 a 0,363 | 0,000 | 0,163 |
| SSM selectivo | red neuronal | 0,276 | 0,249 | 0,151 a 0,402 | 0,005 | 0,033 |

Lectura (regla IC90): habilidad del modelo elegido confirmada (IC90 > 0 y DM p < 0,10). Habilidad frente a persistencia en prueba: 0,636. Cobertura del intervalo conformal del 90 % en prueba: 0,933 (ancho 2,467).

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
| Persistencia (referencia) | referencia | -0,621 | -0,498 | -1,104 a 0,055 | 0,102 |  |
| **DLinear** | red neuronal | 0,057 | 0,087 | 0,048 a 0,114 | 0,003 | 0,020 |
| Ensamble (3 mejores en validación) | ensamble | 0,051 | 0,072 | 0,031 a 0,112 | 0,007 |  |
| iTransformer | red neuronal | 0,049 | 0,021 | -0,058 a 0,102 | 0,613 | 0,015 |
| PatchTST | red neuronal | 0,038 | 0,097 | 0,056 a 0,141 | 0,004 | 0,024 |
| GRU | red neuronal | 0,015 | -0,057 | -0,113 a -0,005 | 0,112 | 0,041 |
| TCN | red neuronal | 0,010 | -0,107 | -0,245 a -0,003 | 0,114 | 0,003 |
| LSTM | red neuronal | -0,001 | -0,018 | -0,034 a -0,003 | 0,098 | 0,021 |
| SSM selectivo | red neuronal | -0,011 | -0,011 | -0,106 a 0,106 | 0,866 | 0,036 |
| N-BEATS | red neuronal | -0,015 | -0,152 | -0,314 a -0,010 | 0,114 | 0,033 |
| N-HiTS | red neuronal | -0,015 | -0,152 | -0,314 a -0,010 | 0,114 | 0,033 |
| MLP | red neuronal | -0,020 | -0,076 | -0,124 a -0,031 | 0,034 | 0,037 |
| Gradient boosting | clasico | -0,144 | -0,353 | -0,682 a -0,050 | 0,051 |  |
| Ridge | clasico | -0,167 | -0,381 | -0,626 a -0,166 | 0,019 |  |

Lectura (regla IC90): habilidad del modelo elegido confirmada (IC90 > 0 y DM p < 0,10). Habilidad frente a persistencia en prueba: 0,391. Cobertura del intervalo conformal del 90 % en prueba: 0,950 (ancho 4,022).

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
| **Ensamble (3 mejores en validación)** | ensamble | 0,289 | 0,253 | 0,066 a 0,492 | 0,074 |  |
| PatchTST | red neuronal | 0,275 | 0,234 | 0,021 a 0,474 | 0,113 | 0,026 |
| LSTM | red neuronal | 0,265 | 0,272 | 0,074 a 0,512 | 0,066 | 0,008 |
| iTransformer | red neuronal | 0,261 | 0,173 | 0,014 a 0,438 | 0,223 | 0,065 |
| GRU | red neuronal | 0,257 | 0,250 | 0,042 a 0,504 | 0,100 | 0,014 |
| TCN | red neuronal | 0,181 | 0,247 | 0,064 a 0,488 | 0,057 | 0,031 |
| N-HiTS | red neuronal | 0,167 | 0,213 | 0,007 a 0,479 | 0,153 | 0,032 |
| N-BEATS | red neuronal | 0,136 | 0,234 | 0,086 a 0,437 | 0,041 | 0,050 |
| DLinear | red neuronal | 0,128 | 0,157 | -0,023 a 0,433 | 0,286 | 0,047 |
| MLP | red neuronal | 0,128 | 0,181 | -0,002 a 0,435 | 0,200 | 0,075 |
| SSM selectivo | red neuronal | 0,089 | 0,033 | -0,149 a 0,214 | 0,779 | 0,053 |
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
| lluvia pentadas cabecera chirps | 3 341 | **lineal estocástica** | 0,720 | 0,090 | 1,428 | 0,125 | 0,998 |
| temperatura diaria cabecera | 16 740 | **no lineal, sin caos demostrado** | 0,010 | 0,080 | no satura | 0,021 | 0,997 |
| spi3 mensual cabecera | 538 | **lineal estocástica** | 0,100 | 0,540 | no satura | 0,048 | 0,993 |
| oni mensual | 921 | **no lineal, sin caos demostrado** | 0,010 | 0,010 | no satura | -0,002 | 0,999 |
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

### Lluvia en la cabecera entre productos

| Par | Días | r diario | r mensual | Media anual (mm) | Días ≥ 1 mm |
|---|---|---|---|---|---|
| power_cabecera · chirps_cabecera_celda_power | 16 709 | 0,318 | 0,800 | 198 / 470 | 0,132 / 0,270 |
| power_cabecera · chirps_cabecera_local | 16 709 | 0,290 | 0,781 | 198 / 448 | 0,132 / 0,241 |
| chirps_cabecera_celda_power · chirps_cabecera_local | 16 709 | 0,940 | 0,992 | 470 / 448 | 0,270 / 0,241 |

### Tendencia de la lluvia de dic–mar por fuente (Theil-Sen; p conservador de Mann-Kendall)

| Fuente | Periodo | Media (mm) | Sen (mm/década) | IC90 | p |
|---|---|---|---|---|---|
| power_cabecera | 1982–2026 | 151 | 21,2 | 7,0 a 32,7 | 0,036 |
| chirps_cabecera_celda_power | 1982–2026 | 395 | 31,6 | 10,2 a 51,3 | 0,035 |
| chirps_cabecera_local | 1982–2026 | 378 | 21,2 | 1,0 a 37,3 | 0,117 |

Nota: IMERG no se descargó: GES DISC exige que la cuenta Earthdata acepte su licencia (ver registro_descarga.json).

### Temperatura

| Variable de la estación GHCN | Días | Sesgo POWER − estación (°C) | r de anomalías diarias |
|---|---|---|---|
| TMAX | 8 578 | -3,19 | 0,401 |
| TMIN | 12 135 | -3,65 | 0,518 |

MODIS no disponible en esta corrida.

| Fuente | Periodo | Media (°C) | Sen (°C/década) | IC90 | p |
|---|---|---|---|---|---|
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

**Clima:** NASA POWER (MERRA-2), celda de la capital de cada departamento. Tendencias 1981–2025 con el Sello de Confianza del paquete; SPI con parámetros gamma de 1981–2015 (último mes disponible). Con una sola familia de datos el Sello no puede dar 'robusta': la independencia queda pendiente.

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

## Limitaciones

- **deslizamientos**: Solo 28 deslizamientos detonados por lluvia en el dominio: se necesitan al menos 30 para estimar un umbral de lluvia.
- **deslizamientos**: El catálogo GLC se basa en noticias: subregistra eventos rurales y su cobertura principal es 2007–2017.
- **lluvia_extrema**: Deriva de las entradas respecto del entrenamiento (PSI > 0,25).
- **lluvia_extrema_chirps**: Deriva de las entradas respecto del entrenamiento (PSI > 0,25).
- **volcanes**: Sin datos de monitoreo continuo (sismicidad volcánica, gases, deformación) no se pronostican erupciones.
- **volcanes**: La probabilidad anual es una frecuencia histórica; el estado actual de cada volcán lo informa el OVS-IGP.
- **lluvia_extrema**: la habilidad del modelo elegido cae de 0,235 en validación a 0,080 en prueba; se informa tal cual (la prueba no se usa para reajustar).
- **lluvia_extrema_chirps**: la habilidad del modelo elegido cae de 0,109 en validación a 0,046 en prueba; se informa tal cual (la prueba no se usa para reajustar).
- **sequia h3**: la habilidad del modelo elegido cae de 0,362 en validación a 0,198 en prueba; se informa tal cual (la prueba no se usa para reajustar).
- **sequia_chirps h1**: la habilidad del modelo elegido cae de 0,727 en validación a 0,616 en prueba; se informa tal cual (la prueba no se usa para reajustar).
- **sismos**: la Mc por década supera a la Mc usada (4,5) en 1970s (4,9), 1980s (5,1), 1990s (4,6): el conteo de esos años está incompleto y la tasa aparente crece con el tiempo.
- **sismos**: el conteo mensual incluye réplicas; una ganancia frente a Poisson refleja agrupamiento (réplicas), no capacidad de pronosticar sismos.
- Los resultados son experimentales y describen la escala de cada producto (celdas de 0,05° a 0,5°), no puntos.
- Ningún resultado es una alerta oficial: las emiten SENAMHI, IGP, INGEMMET e INDECI.
