# `web/` · Visor estático (paso 1 del ADR-016) — superado

Este visor leía `public/expedientes/*.json` sin API. El paso 2 del mismo ADR ya está implementado:

- **Producto web:** [`../frontend/`](../frontend/) (React + TypeScript, tipos generados del OpenAPI, mapa MapLibre).
- **API:** [`../backend/`](../backend/) (FastAPI).

Se conserva hasta que el equipo confirme su retiro (ver [`../docs/auditoria-repositorio.md`](../docs/auditoria-repositorio.md)).
No agregar funcionalidades nuevas aquí.
