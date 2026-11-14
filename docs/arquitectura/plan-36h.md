# Plan de 36 horas

Objetivo: **un corte vertical con datos reales** (ADR-012). Los bloques asumen 4 frentes: **A** ingesta y credenciales · **B** estadística y Sello · **C** teledetección e hidrología · **D** web y comunicación. Ajustar nombres.

| Horas | A · Ingesta | B · Estadística | C · Hidrología | D · Web / relato | Hito |
|---|---|---|---|---|---|
| 0–2 | Probar login Earthdata; **lanzar tareas AppEEARS** (HLS, SMAP, MOD13Q1, NASADEM) y descargar IMERG mensual y CHIRPS v3 | Congelar `preregistro.yaml` (aprobar valores *propuestos*); correr `make test` | Cruzar represas con la PLD de SWOT; decidir si el gemelo es viable | Crear `web/`, `npm install`, leer expedientes de ejemplo | Repo corre; preregistro con hash |
| 2–8 | Publicar `data/raw` + manifiesto; MERRA-2 por bbox; extender POWER a 2025 | `zonal.py` (agregación por subcuenca ponderada por área) y series anuales IMERG/CHIRPS | Parser AUTODEMA (línea base) | `SelloCard` y `SerieChart` con los expedientes actuales | IMERG/CHIRPS/MERRA-2 anuales por subcuenca |
| 8–16 | Reintentar Giovanni/data rods/FIRMS (secundarios) | **Prueba de independencia** con 3 familias; persistir ONI; expedientes lluvia y T | Si hay cruce SWOT: serie del espejo de agua de Aguada Blanca (HLS) | `PruebasTable`, advertencias, grafo del proceso | **Expediente real con familias independientes** |
| 16–24 | Apoyo a B y C; AppEEARS descargado | Monte Carlo E4; investigar el hallazgo 2; sensibilidades de T (sin 2023–24, vs MODIS/VIIRS LST) | Tendencia del espejo de agua con Sello | Mapa 2D si alcanza; pulir mensajes de incertidumbre | E4 cerrado; demo navegable |
| 24–32 | — | Matriz P1 (si hay tiempo): bloques de años, estabilidad, nulo | GR2M + `generar_gr2m.R` (solo si el espejo de agua salió) | Guion del pitch, capturas, README final | Demo con datos reales |
| 32–36 | Congelar `data/raw` y expedientes | Revisión de cifras: README ↔ JSON | Revisión | Ensayo del pitch, video de respaldo | **Entrega** |

## Orden de recorte (si hay retraso de 3 h)

1. 3D → 2. chat y verificador → 3. MERESE → 4. ESP → 5. gemelo → 6. Matriz P1.
**No se recorta:** datos reales, Sello, "no decidible", preregistro.

## Decisiones que bloquean

| Decisión | Quién | Cuándo |
|---|---|---|
| Valores de `alpha`, `u_ventanas`, `tol_sensor` | B + arquitectura | Hora 0–2 |
| ¿LST cuenta como familia de T2M o solo corroboración? | B | Hora 2 |
| ¿El README mantiene "lluvia frágil" o pasa a "sin tendencia marginal"? (ADR-013) | Equipo | Hora 8 |
| Gemelo sí/no (según PLD de SWOT) | C | Hora 2 |
