# ADR-020 · Backend con base de datos y publicación por contrato; los crudos siguen en archivos con hash

**Estado:** Aceptada · **Reemplaza en parte a:** ADR-014 (solo la parte "sin base de datos")

## Contexto
El ADR-014 proponía servir todo desde archivos estáticos. El producto creció: varios usuarios con
roles, procesos de ciencia de datos que reportan avance, resultados que se retiran con motivo,
caché HTTP con ETag y un verificador numérico para la IA. Eso necesita estado transaccional.

## Decisión
- `data/raw/` mantiene lo decidido en el ADR-014: crudo con SHA-256 y manifiesto, fuera de git
  (en git solo los manifiestos y el registro de descarga).
- Los resultados científicos se publican en el backend (`POST /api/v1/expedientes`) con una clave
  de servicio de alcance `ingesta`. El ID del expediente se deriva del contenido: publicar dos
  veces lo mismo es idempotente.
- `resultados/*.json` del motor científico se versionan en git como evidencia reproducible y se
  importan al backend con el mismo contrato.
- SQLite en desarrollo y PostgreSQL en producción, con migraciones de Alembic.

## Consecuencias
+ Un solo contrato (OpenAPI) para frontend, pipeline y asistente; trazabilidad de quién publicó qué.
− El paquete científico necesita un adaptador de su `Expediente` al contrato del backend (tarea de integración).
