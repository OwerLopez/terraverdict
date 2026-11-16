# Qué falta para terminar TerraVerdict al 100 %

> Actualizado: **15-11-2026 (noche)**, al cierre. Lo hecho y su evidencia está en [`bitacora.md`](bitacora.md);
> cómo operar el proyecto, en [`traspaso.md`](traspaso.md).
> Regla para cerrar una tarea: código + pruebas que pasan + entrada en la bitácora + commit en `main`.

## Estado al cierre

### Lo que tenemos (verificado)
| Parte | Estado y evidencia |
|---|---|
| Aplicación publicada | ✅ <https://terraverdict.vercel.app> (Vercel, cuenta de Ower Frank; despliegue por `push` a `main`). API, SPA, CSP y cabeceras verificadas en producción |
| Repositorio | ✅ [`OwerLopez/terraverdict`](https://github.com/OwerLopez/terraverdict), historial completo con autores y fechas originales |
| Datos reales | ✅ Refrescados el 15-11: NASA POWER (Arequipa, celdas y 25 departamentos), **IMERG Final diaria 1998–2025-09 completa**, NASA GLC, NASA GIBS (mapa), USGS ComCat (hasta el 15-11-2026), Smithsonian GVP, NOAA ONI y GHCN, CHIRPS, IGP y MODIS LST. Todo con SHA-256 en `data/raw/*/manifiesto.json` |
| Modelos | ✅ 10 redes + clásicos, referencias y dos ensambles; IC90 por bootstrap de bloques, Diebold-Mariano, calibración, conformal y abstención. Protocolo auditado (`auditoria-metricas.md`) |
| M1 · Matriz de Relevancia | ✅ P1 (lluvia extrema en la cabecera, objetivo IMERG): dos modelos, permutación por bloques, estabilidad, significancia condicional con FDR y evaluación única en 2021–2025 (`resultados/relevancia.json`, vista `/relevancia`) |
| Historial (M8) | ✅ Origen móvil 2016–2026 con el modelo elegido en la validación de cada año. Cifras vigentes en [`experimentos.md`](experimentos.md) |
| Teoría del caos | ✅ Validada con sistemas de referencia; 7 series reales, global y en ventanas |
| Asistente | ✅ Google Gemini anclado en expedientes, con citas y verificación numérica de cada cifra; explicación en lenguaje claro en cada expediente |
| Procesos | ✅ Ejecuciones reales del pipeline (descargas y corridas) en `/procesos` |
| Seguridad | ✅ Claves solo en el servidor; límites por IP y global en el asistente; modo solo lectura sin secreto JWT; CSP estricta, HSTS, `nosniff`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`; cadena de custodia SHA-256 |
| Calidad | ✅ Pruebas de ciencia, backend, frontend y E2E (cifras en la bitácora); CI en GitHub Actions; portabilidad a Windows probada |
| Licencias | ✅ MIT + atribución de cada fuente + inventario de dependencias |

### Lo que falta
| Tarea | Quién | Detalle |
|---|---|---|
| Fuentes nacionales | Equipo / docentes | SENAMHI, IGP (catálogo completo), INGEMMET y ANA no tienen API abierta: convenio o descarga manual verificada |
| M1 para P2–P4 | Equipo | P2 (bofedales) necesita NDVI de HLS/Landsat por AppEEARS; P3 (represas), la serie de volumen de AUTODEMA (hoy solo reportes aislados en PDF); P4 (turbidez), más de 3 eventos documentados |
| Persistencia en Vercel (opción C) | Opcional | PostgreSQL gestionado en `TV_DATABASE_URL` para usuarios y claves que sobrevivan entre instancias (`despliegue.md`) |
| Humedad del suelo en P1 | Opcional | Candidata de la plantilla sin dato medido (GLDAS/SMAP); hoy aparece como "sin resultado" en la matriz |
| Redes líquidas (LNN/CfC) | Opcional | No implementadas; la familia convolucional (TCN) sí está |
| Pitch y video | Equipo | `presentacion-ejecutiva.md` y `capturas/`, con las cifras de `experimentos.md` |

## Bloqueos externos (no dependen del código)

| Bloqueo | Qué se necesita |
|---|---|
| SENAMHI, IGP/OVS, INGEMMET, ANA, CENEPRED, SINIA | Sin API accesible (ver `auditoria-repositorio.md`): convenio o descarga manual verificada |
| Serie de volumen de las represas | AUTODEMA publica reportes aislados en PDF: transcribir más reportes con su fuente |
| Deslizamientos | Solo 28 eventos por lluvia en el GLC: el sistema se abstiene de estimar umbrales hasta tener ≥ 30 (inventario INGEMMET) |

## Decisiones del equipo

- [x] Mc sísmica: se mantiene 4,5 como limitación declarada (`auditoria-metricas.md` §12).
- [x] Sustitutos del caos en ventanas: 39, lectura descriptiva (§12).
- [x] Traslado a `OwerLopez/terraverdict` con el historial completo.
- [x] Congelar `preregistro.yaml` y la partición temporal (2026-11-15).
- [ ] ¿Retirar `web/`? Está superado por `frontend/` (ADR-016). Por ahora se conserva.
