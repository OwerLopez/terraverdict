# ADR-016 · Frontend React en dos pasos: visor estático primero, 3D después

**Estado:** Aceptada (equipo eligió React)

## Contexto
El diferenciador es el Sello y la honestidad estadística, no el terreno 3D.

## Decisión
**Paso 1 (S3):** React + Vite + TypeScript que lee `expedientes/*.json` estáticos: tarjeta de Sello, serie con Sen y banda IC, tabla de pruebas (✅/❌/⏳), grafo del proceso y advertencias. Sin API obligatoria. **Paso 2:** FastAPI de solo lectura, mapa MapLibre 2D y, solo con tiempo, 3D con NASADEM. Tipos TypeScript generados desde el JSON Schema del expediente.

## Consecuencias
+ La demo funciona con archivos estáticos. − Hay que mantener sincronizados el esquema del expediente (pydantic) y los tipos de la web: se genera `schema.json` desde pydantic.
