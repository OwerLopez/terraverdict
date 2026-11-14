# ADR-017 · Ingesta: `earthaccess` + AppEEARS + HTTP directo, credenciales solo por entorno

**Estado:** Propuesta

## Contexto
Una persona tiene las credenciales (Earthdata, AppEEARS, USGS). Descargar IMERG diaria completa son decenas de GB.

## Decisión
| Fuente | Herramienta |
|---|---|
| IMERG mensual, MERRA-2, GLDAS, FLDAS | `earthaccess` (CMR + HTTPS) |
| IMERG diaria | Subset (OPeNDAP o Harmony) por bbox, probando primero un año |
| MODIS, VIIRS, HLS, SMAP, NASADEM | AppEEARS por polígono: tarea asíncrona, sondeo y descarga |
| POWER, ONI, CHIRPS v3, Copernicus OData | HTTP con reintentos (`ingest/http.py`) |
| SWOT | `earthaccess` + filtro por ID de lago de la PLD |
Credenciales: variables de entorno (`EARTHDATA_USER/PASS` o `~/.netrc`), nunca en el repo. Un servicio se marca `ok` **solo con 2xx/3xx**.

## Consecuencias
+ Reduce volumen y bloqueos. − Las tareas de AppEEARS tienen colas: lanzarlas en la hora 0 (`ingest/appeears.py` aún no existe).
