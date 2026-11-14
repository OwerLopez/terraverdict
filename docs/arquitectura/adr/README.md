# Registro de decisiones de arquitectura (continuación)

Continúa la tabla ADR-1…ADR-11 de [`../../diseno-tecnico.md`](../../diseno-tecnico.md#3-decisiones-de-arquitectura-adr). Cada decisión usa Contexto / Decisión / Consecuencias; cambiar una decisión = nuevo ADR que la reemplaza.

| ADR | Decisión | Estado |
|---|---|---|
| [ADR-012](adr/ADR-012-corte-vertical-primero.md) | Corte vertical antes que amplitud | Propuesta |
| [ADR-013](adr/ADR-013-p-conservador-mann-kendall.md) | p conservador = máximo de tres variantes de Mann-Kendall | Aceptada (implementada en `trends/mk.py`) |
| [ADR-014](adr/ADR-014-almacenamiento-y-offline.md) | Archivos con hash, sin base de datos; todo corre offline sobre `data/raw` | Propuesta |
| [ADR-015](adr/ADR-015-escenarios-en-servidor-no-en-navegador.md) | Escenarios del gemelo en FastAPI; el port a TypeScript se pospone (matiza ADR-3) | Propuesta |
| [ADR-016](adr/ADR-016-frontend-react-en-dos-pasos.md) | Frontend React en dos pasos: visor estático primero, 3D después | Aceptada (equipo eligió React) |
| [ADR-017](adr/ADR-017-ingesta-earthaccess-appeears.md) | Ingesta: `earthaccess` + AppEEARS + HTTP directo, credenciales solo por entorno | Propuesta |
| [ADR-018](adr/ADR-018-sello-determinista-pruebas-pendientes.md) | Sello como tabla de decisión determinista; una prueba pendiente impide 'robusta' | Aceptada (implementada en `trends/sello.py`) |
| [ADR-019](adr/ADR-019-modelo-de-ia-configurable.md) | Modelo de lenguaje en configuración, fuera de la cadena de cálculo | Propuesta (matiza ADR-10) |
