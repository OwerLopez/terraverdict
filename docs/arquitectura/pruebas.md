# Estrategia de pruebas local

| Tipo | Qué prueba | Archivo | Corre en |
|---|---|---|---|
| **Golden** | `trends` reproduce `analisis_preliminar.json` desde series guardadas (tolerancia 1e-3 en IC y σ por el redondeo del JSON; Sen exacto) | `tests/unit/test_golden_preliminar.py` | `make test` |
| **Hallazgos como tests** | p conservador de la lluvia ≠ Hamed-Rao; la temperatura sobrevive sin 2023–24; una sola familia nunca da 🟢 | mismo archivo | `make test` |
| **Sello** | Cada falla se nombra; pendiente impide 🟢; ⚪ vs 🔵 | `tests/unit/test_sello.py` | `make test` |
| **Sintéticos** | Sen recupera pendiente conocida; ENSO separa tendencia de ONI; escalón de sensor detectado | `tests/unit/test_sintetico.py` | `make test` |
| **Calibración (E4)** | Falsos positivos AR(1) (φ = 0; 0,3; 0,6) ≤ alpha + 0,04 | `tests/statistical/` | `make test-stat` |
| **Expediente** | Hash estable y sensible; advierte independencia pendiente | `tests/unit/test_expediente.py` | `make test` |
| **Referencia GR2M** | Python vs airGR con 3 casos (incluye X2 > 1) | `tests/reference/` + `generar_gr2m.R` | tras `Rscript` local |
| **AUTODEMA** | Parser determinista vs lectura manual del PDF; suma = total reportado | por crear | local |

## Flujo con R (tu máquina)

```bash
Rscript tests/fixtures/airgr/generar_gr2m.R   # produce gr2m_ref.csv y gr2m_ref.meta.json; versionar ambos
```
Anotar la versión de airGR y forzar los mismos estados iniciales en la implementación Python.

## Flujo AUTODEMA (local)

1. `pdftotext -layout REPORTE-HIDRICO.pdf - | less` y ajustar `RE_FILA` en `ingest/autodema_pdf.py`.
2. Transcribir a mano 1–2 reportes a `tests/fixtures/autodema_manual.json`.
3. Test: parser == transcripción, y suma de volúmenes ≈ 373,30 hm³ (13-03-2024).
4. Ese parser es la **línea base** contra la que se compara luego el digitalizador con LLM.

## Calidad

`ruff`, `mypy`, `pytest` en CI (GitHub Actions) en cada PR. Los tests marcados `slow` y `red` no corren por defecto.
