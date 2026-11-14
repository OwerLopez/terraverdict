# ADR-015 · Escenarios del gemelo en FastAPI; el port a TypeScript se pospone (matiza ADR-3)

**Estado:** Propuesta

## Contexto
ADR-3 plantea Python + TypeScript con pruebas de paridad. Es la pieza más cara y la que menos aporta antes de tener un gemelo validado.

## Decisión
Los escenarios corren en el servidor con GR2M acelerado con numba (microsegundos por corrida). El port a TypeScript pasa a la hoja de ruta (Fase 1) y solo si se necesita modo sin conexión.

## Consecuencias
+ Un solo código del modelo, sin riesgo de divergencia. − La vista de escenarios requiere el contenedor de la API en la demo (o una grabación).
