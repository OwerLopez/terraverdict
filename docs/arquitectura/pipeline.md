# Pipeline de datos y ciencia

## Etapas

| # | Etapa | Entrada | Salida | Validación | Estado |
|---|---|---|---|---|---|
| 1 | `ingest` | Catálogos, bbox, puntos | `data/raw/*` + `manifiesto.json` (SHA-256) | El archivo abre; variable y unidad esperadas | POWER y ONI listos; resto pendiente |
| 2 | `contract` | Raw | `Serie` (fecha, valor, unidad, producto, versión, DOI, familia, frac_valida) | pydantic: unidad controlada, sin centinelas, fechas únicas y ordenadas | `contracts/series.py` |
| 3 | `preprocess` | Serie mensual | Serie anual (T media; lluvia dic–mar por año hidrológico) | Años completos únicamente | `preprocess/anual.py` |
| 3b | `zonal` | Raster + polígono | Serie por subcuenca ponderada por área | `frac_valida` ≥ umbral | Pendiente (S1) |
| 4 | `trends` | Años, valores, ONI, otras familias | Sen+IC90, MK (3 variantes), ENSO-HAC, ventanas, sensor, palanca, independencia, n* | Sintéticos + golden | Listo |
| 5 | `sello` | Resultado de `trends` + preregistro | 🟢🟡⚪🔵 + `fallan` + `pendientes` | Tabla de decisión testeada | Listo |
| 6 | `expediente` | Todo lo anterior | JSON con hash de entradas, preregistro y commit | Esquema pydantic versionado | Listo |
| 7 | `report` | Expediente | `reports/<id>.md` | Toda cifra sale del JSON | Listo (básico) |

## Convenciones

- **Anual para el Sello, mensual para el gemelo** (hallazgo 8). Lluvia dic–mar = año hidrológico (dic del año previo + ene–mar).
- **Años completos:** IMERG Final llega a 2025-09, así que sus series anuales terminan en 2024.
- **Mezcla prohibida:** IMERG Early/Late nunca entran en una serie de tendencia.
- **Funciones puras:** `analizar_serie(anios, x, pre, ...) → dict`. Sin red, sin disco.
- **Caché:** `hash(entradas) + versión del código + hash del preregistro`. Cambiar el preregistro invalida todo.

## Lógica del Sello (resumen; ver ADR-018)

```
p_cons = max(MK_original, Hamed-Rao, pre-blanqueo)
si p_cons > alpha:  n* > n_disponible → ⚪ no decidible | si no → 🔵 sin tendencia (nota si es marginal)
si no, pruebas:  ventanas · ENSO (HAC) · sensor (por producto) · palanca · independencia (≥2 familias)
   alguna falla → 🟡 frágil (nombra cuáles)   |   alguna sin evaluar → 🟡 (pendientes)   |   todas pasan → 🟢
```

## Matriz de Relevancia (S4, plantilla P1)

1. Objetivo: día con IMERG Final diaria ≥ p99 de ese mes calendario (~100 eventos en ~10 000 días → clases muy desbalanceadas).
2. Candidatas (solo las de la plantilla): ONI (lag 0–3), agua precipitable, viento 500 hPa, humedad previa (GLDAS; SMAP desde 2015), T2M, mes.
3. Validación por **bloques de años** (dejar un año fuera); años finales apartados desde el inicio.
4. Línea base: climatología mensual del percentil. Métricas: **PR-AUC y Brier** (no accuracy).
5. Modelos: elastic-net y LightGBM de profundidad limitada; importancia por permutación en validación; estabilidad con 200 remuestreos por bloques; nulo por barajado en bloques; FDR.
6. Si la habilidad frente a la línea base no es > 0 con IC90 → *"no explicable con estas variables"*.

## Gemelo (S5, solo si pasa el cruce con la PLD de SWOT)

GR2M (airGR) con `X2 ∈ [0,2; 2,0]` (ampliado: con trasvases X2 > 1 es plausible; revisar si los parámetros se acumulan en el borde), calibración por hipercubo latino sobre ΔV, validación 2016–2025, regla **KGE_val < KGE_min → no se usa** (codificada, no solo documentada). Verificar si POWER ya corrige elevación antes de aplicar Γ·Δz (hallazgo 11).

## Comandos

```bash
make install                      # pip install -e ".[dev]"
make test                         # unit + reference (rápido, sin red)
make test-stat                    # Monte Carlo del Sello (@slow)
tv ingest-power && tv ingest-oni  # descarga a data/raw con hash
tv trends                         # sobre data/raw (offline)
tv trends --series tests/fixtures/preliminar_series.json   # sin red
tv report expedientes/<id>.json
```
