# ADR-014 · Archivos con hash, sin base de datos; todo corre offline sobre `data/raw`

**Estado:** Propuesta

## Contexto
Hosting estático, equipo pequeño, credenciales en manos de una sola persona, y servicios que fallan (Giovanni, FIRMS, data rods).

## Decisión
- `data/raw/` guarda el **crudo con SHA-256** y `manifiesto.json` (URL, producto, versión, fecha). Fuera de git.
- `data/interim/` y `data/processed/`: Parquet (series por unidad) y Zarr/NetCDF (cubos), consultables con DuckDB.
- `expedientes/*.json` **sí** van a git: son el producto final y alimentan web, API y MCP.
- Todo comando acepta modo offline; los tests usan fixtures guardados, nunca red.
- Caché por `hash(entradas) + versión del código + hash del preregistro`.

## Consecuencias
+ Reproducible y barato. − Sin DVC los crudos no se comparten por git: la persona con credenciales publica un `data/raw` comprimido (Drive/S3) con el manifiesto.
