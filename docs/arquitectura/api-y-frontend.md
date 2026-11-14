# API y frontend

## Paso 1 · Visor estático (S3)

`web/` lee `public/expedientes/*.json` (copiados desde `expedientes/`). Sin API.

```
web/src/
  main.tsx · App.tsx
  types.ts                   # espejo del esquema del expediente (generar desde schema.json)
  components/
    SelloCard.tsx            # 🟢🟡⚪🔵 + qué falla + qué falta
    SerieChart.tsx           # serie, recta de Sen y banda IC90 (SVG propio)
    PruebasTable.tsx         # ✅ ❌ ⏳ por prueba, con el valor
    Advertencias.tsx         # "una sola familia de datos…"
```
Requisitos de comunicación (del diseño técnico, §8): **"no decidible" con el mismo peso visual que un resultado**, frescura de cada capa (fecha del último dato) y cada cifra enlazada a su expediente.

## Paso 2 · FastAPI de solo lectura (después de S3)

| Endpoint | Fuente | Nota |
|---|---|---|
| `GET /expedientes` | Carpeta `expedientes/` | Lista id, variable, veredicto |
| `GET /expedientes/{id}` | JSON | Mismo esquema que la web |
| `GET /cuencas/{id}/cadena` | Precalculado | Más adelante |
| `POST /verificar` | Verificador numérico | Solo con el módulo de IA |

Entradas validadas con pydantic y límite de tasa. Un solo esquema (`Expediente`) para web, API y MCP; `python -m terraverdict.contracts.expediente > web/src/schema.json` genera el JSON Schema.

## Paso 3 · Mapa y 3D

MapLibre 2D con veredictos por subcuenca; 3D con NASADEM solo si S1–S4 están sólidos.
