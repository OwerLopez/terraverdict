# ADR-018 · Sello como tabla de decisión determinista; una prueba pendiente impide 'robusta'

**Estado:** Aceptada (implementada en `trends/sello.py`)

## Contexto
El README exige que el Sello no sea subjetivo y que, con una sola familia de datos, nada califique como robusto.

## Decisión
`decidir()` recibe los resultados y el preregistro y devuelve 🟢/🟡/⚪/🔵 más `fallan` y `pendientes`. Pruebas: ventanas, ENSO (HAC), sensor **por producto**, **palanca de los últimos años** (nueva, por el salto de 2023–24), independencia por familias (`config/familias.yaml`) y detectabilidad. Pruebas no evaluadas (`None`) → máximo 🟡.

## Consecuencias
+ Auditable y testeable (`tests/unit/test_sello.py`). − Umbrales `u_ventanas`, `tol_sensor`, `alpha` son *propuestos* y deben congelarse en `preregistro.yaml` antes de S1.
