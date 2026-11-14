# ADR-012 · Corte vertical antes que amplitud

**Estado:** Propuesta

## Contexto
El diseño describe 6 módulos, API, MCP, 3D y chat; el código real son dos scripts. Quedan ~36 h.

## Decisión
Se construye **un flujo completo con datos reales de punta a punta** antes de abrir otro frente: `ingest → contrato → anual → trends/Sello → expediente → informe → vista web`. El orden de recorte es: 3D, chat, MERESE, ESP, gemelo. **Nunca se recortan** datos reales, Sello ni "no decidible" (regla del README).

## Consecuencias
+ Hay demo defendible aunque nada más llegue. − El gemelo y la Matriz quedan como diseño si el tiempo no alcanza, y así se declara (README, sección 0).
