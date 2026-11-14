# ADR-013 · p conservador = máximo de tres variantes de Mann-Kendall

**Estado:** Aceptada (implementada en `trends/mk.py`)

## Contexto
En lluvia dic–mar (n=43) las variantes dan p muy distintos: original 0,057, Hamed-Rao 0,0002, Yue-Wang ~5e-8, pre-blanqueo 0,109. Una corrección por autocorrelación no debería volver la tendencia *más* significativa; con autocorrelaciones negativas en algún lag, Hamed-Rao y Yue-Wang lo hacen. Además `pymannkendall` emite `sqrt` de varianza negativa en series sintéticas.

## Decisión
El p del Sello es el **máximo** entre `original`, `hamed_rao` y `prewhitening` (lista en `preregistro.yaml`). Se guardan todos los p y la variante limitante. Yue-Wang queda fuera. Las variantes con p = NaN se descartan y se registran en `p_invalidas`. El filtro ENSO usa errores HAC (Newey-West) en lugar de OLS.

## Consecuencias
+ El Sello no depende de una corrección inestable. − Es más conservador: la lluvia pasa de 'frágil' a 🔵 *sin tendencia* con p = 0,109 (marginal; el sello lo anota). Hay que decidir si el README mantiene la lectura 'frágil'. Verificación pendiente: Monte Carlo `tests/statistical` (E4) con más ruido y n distintos.
