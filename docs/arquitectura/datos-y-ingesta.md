# Datos e ingesta

## Cómo se descarga cada fuente

| Fuente | Método | Volumen / cuidado | Estado |
|---|---|---|---|
| NASA POWER (T2M, PRECTOTCORR) | `ingest/power.py` (REST por punto) | KB | ✅ |
| ONI / RONI (NOAA CPC) | `ingest/noaa.py` (texto plano) | KB | ✅ (RONI pendiente) |
| IMERG Final mensual (333 gránulos) | `earthaccess.search_data("GPM_3IMERGM", version="07", bounding_box=…)` | Pequeño | Pendiente |
| IMERG Final diaria (10 135 gránulos) | Subset por bbox (OPeNDAP/Harmony) | **Decenas de GB si se baja entera**: probar un año | Pendiente |
| CHIRPS v3 mensual | HTTP directo `data.chc.ucsb.edu/products/CHIRPS/v3.0/monthly/latam/` | Moderado | Pendiente (responde) |
| MERRA-2 por bbox (M2TMNXSLV) | `earthaccess` | Moderado | Pendiente |
| MODIS / VIIRS / HLS / SMAP / NASADEM | AppEEARS por polígono (POST `/task`, sondear, descargar) | Colas: lanzar en la hora 0 | Pendiente |
| SWOT LakeSP | `earthaccess` + filtro por ID de lago (PLD) | Primero cruzar represas con la PLD | Pendiente |
| AUTODEMA | PDF + `pdftotext`; parser determinista `ingest/autodema_pdf.py` | Un PDF (13-03-2024); archivo histórico pendiente | Esqueleto |
| Giovanni · FIRMS · data rods | Reintentar con backoff; FIRMS pide MAP_KEY | Secundarios: `earthaccess` ya cubre casi todo | ⚠️ |

## Reglas

1. **Crudo con hash:** `guardar_crudo()` escribe el archivo y su entrada en `manifiesto.json` (URL, producto, versión, fecha UTC, SHA-256).
2. **Offline:** una vez descargado, `tv trends` no usa red.
3. **Credenciales:** `EARTHDATA_USER`, `EARTHDATA_PASS` (o `~/.netrc`), token de AppEEARS, cuenta USGS; solo por entorno o secretos de CI. Archivo `.env` en `.gitignore`.
4. **Disponibilidad ≠ HTTP 200:** un servicio es `ok` solo con 2xx/3xx; con reintentos y *backoff* (`ingest/http.py`).
5. **Licencias:** PISCOp (CC BY-NC-ND) solo validación interna y nada derivado publicado; Copernicus exige la atribución *"Contains modified Copernicus Sentinel data [año]"*.
6. **Entrega entre integrantes:** quien tenga las credenciales descarga y publica `data/raw` comprimido con su manifiesto; el resto trabaja offline.

## Familias para la prueba de independencia

Definidas en [`config/familias.yaml`](../../config/familias.yaml). Decisión pendiente: MODIS/VIIRS LST miden temperatura de *superficie*, no del aire. Propuesta: cuentan como **corroboración física** (se reportan aparte) y no como segunda familia de T2M; la segunda familia real sería ERA5 (no verificado) o SENAMHI.
