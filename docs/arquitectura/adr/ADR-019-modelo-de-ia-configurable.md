# ADR-019 · Modelo de lenguaje en configuración, fuera de la cadena de cálculo

**Estado:** Propuesta (matiza ADR-10)

## Contexto
El identificador de modelo, la beta de respaldo, `strict` y los precios citados en 7b no se pudieron contrastar con la documentación oficial.

## Decisión
El modelo vive en `configs/llm.yaml` (por ruta: extracción de PDF barato, chat más capaz). Antes de fijar parámetros de la API se consulta la documentación oficial. El verificador numérico determinista se implementa y prueba **antes** que cualquier llamada al modelo. Todo lo de IA va después del corte vertical.

## Consecuencias
+ Cambiar de modelo no toca el código. − Los números de costo del diseño quedan como estimación hasta medirlos.
