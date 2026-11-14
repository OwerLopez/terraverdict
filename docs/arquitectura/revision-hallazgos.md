# Hallazgos de la revisión y su estado

| # | Hallazgo | Estado |
|---|---|---|
| 1 | `p = 0.0` por redondeo a 4 decimales | ✅ El nuevo `trends` guarda el p completo (ver `expedientes/*.json`) |
| 2 | Hamed-Rao p = 0,0002 vs MK p = 0,057 en lluvia | ✅ Investigado: Yue-Wang 5e-8, pre-blanqueo 0,109 → ADR-013, p = máximo |
| 3 | Salto de T en 2023–24 con mucha palanca | ✅ Prueba `palanca` (sobrevive: Sen 0,19 °C/déc, p ≈ 3e-5); ⏳ contraste con MODIS/VIIRS y ERA5 |
| 4 | Análisis termina en 2024 | ⏳ `configs/chili.yaml` ya apunta a 2025; reejecutar `tv ingest-power` |
| 5 | 1983 = 5,2 mm sospechoso | ⏳ Contrastar con CHIRPS v3 |
| 6 | Cifras del README (98/171/144 mm) no están en el JSON | ⏳ `noaa.clasificar_enso` existe; falta persistir ONI y el promedio por clase en el expediente |
| 7 | Ventanas solapadas ≠ evidencia independiente | ✅ El informe lo rotula como robustez ante el periodo |
| 8 | Anomalías mensuales vs medias anuales | ✅ Convención en `pipeline.md`: anual para el Sello, mensual para el gemelo |
| 9 | `estado_http` marcaba ok un 403/404 | ✅ `ingest/http.py::estado_ok`; ⏳ migrar `verificar_fuentes.py` |
| 10 | Rango de X2 | ✅ `preregistro.yaml`: [0,2; 2,0]; ⏳ comprobar acumulación en el borde |
| 11 | ¿POWER ya corrige elevación? | ⏳ Verificar antes de aplicar Γ·Δz |
| 12 | Referencias cruzadas rotas (R7 → sección 11; `recursos-guia` con Copernicus DEM) | ⏳ Editar `diseno-tecnico.md` (R7 → sección 13) y `recursos-guia.md` |
| 13 | Detalles de la API de IA no confirmados (beta, `strict`, precios, `tool_choice`) | ⏳ ADR-019: contrastar con la documentación oficial |
