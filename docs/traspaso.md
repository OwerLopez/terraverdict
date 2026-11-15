# Traspaso de TerraVerdict · después de la auditoría de métricas (15-11-2026)

Este documento es para el siguiente integrante que continúe el trabajo. Tiene dos partes:
1. el estado y los pasos de cada tarea pendiente;
2. un **prompt de traspaso** listo para pegar en un asistente de código (§3).

Reglas del proyecto que no cambian:
- Solo datos reales y trazables a fuentes oficiales: NASA, NOAA, USGS y Smithsonian.
- Toda cifra mostrada sale de `resultados/*.json`.
- Nada se da por terminado sin evidencia ejecutada.
- Los resultados no son alertas oficiales.
- Cada avance lleva código, pruebas, bitácora, pendientes y commit en `main` con tu propio usuario.

---

## 1. Dónde quedó la sesión del 15-11

Último trabajo: **auditoría de métricas y pesos** (MaxsForocca). Commits `8a63d55`, `98846df` y `783e08d`, más el de este traspaso.
- **Informe completo:** [`auditoria-metricas.md`](auditoria-metricas.md). Tiene 19 hallazgos corregidos, la tabla por métrica y por parámetro, qué cambió en las cifras y los riesgos que quedan (§11).
- **Hiperparámetros y reglas de método:** [`config/modelos.yaml`](../config/modelos.yaml), con la justificación de cada valor.
- **Bitácora:** entrada "Auditoría de métricas y pesos" en [`bitacora.md`](bitacora.md).

**Cifras vigentes del historial fuera de muestra** (modelo elegido en la validación de cada año):

| Tarea | Habilidad | Lectura |
|---|---|---|
| Sequía a 1 mes | 0,658 | confirmada |
| Sequía a 3 meses | 0,232 | confirmada |
| Lluvia a 1 día | 0,031 | no confirmada |
| Sismos | 0,149 bits | no confirmado |

No vuelvas a usar las cifras viejas ("Ridge 0,711", "PatchTST 0,256"): se habían elegido mirando la prueba.

**Estado verificado al cerrar:**
- **Pruebas:** ciencia 135 pasan y 2 se omiten; backend 73; frontend 33; E2E 2 de 2.
- **`tv verificar-integridad`:** 0 crudos alterados y 11 resultados sellados.
- **Reproducibilidad:** dos corridas completas de `tv experimentos` dieron resultados idénticos bit a bit.

---

## 2. Tareas pendientes

### 2.1 Publicar en Vercel · **solo el owner del repositorio (DiegoNiS)**
MaxsForocca no tiene permisos de administración sobre `DiegoNiS/terraverdict`; quien los tenga debe hacer esto. Pasos completos en [`despliegue.md`](despliegue.md) §A.1:
1. Instalar la integración de GitHub de Vercel para el repositorio e importarlo en Vercel.
2. Definir `TV_JWT_SECRETO`: 32 caracteres o más, por ejemplo `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Opcionalmente, `TV_ADMIN_EMAIL` y `TV_ADMIN_PASSWORD`.
3. Desplegar y verificar:
   ```bash
   curl -s https://<sitio>/api/v1/salud/lista
   cd frontend && E2E_BASE_URL=https://<sitio> npm run e2e -- --trace off
   ```
4. Registrar la URL y la evidencia en `docs/despliegue.md`, `docs/bitacora.md` y `docs/pendientes.md`.

### 2.2 Completar IMERG (2002–2025) · cualquier integrante con cuenta Earthdata
**Estado:** 1998–2001 descargados y verificados (`data/raw/imerg/manifiesto.json`, 0 días faltantes). La descarga se detuvo a propósito al cerrar la sesión.

**Velocidad observada:** unos 45 minutos por año con 4 hilos, o sea unas 18 horas para 2002–2025. GES DISC cortó la conexión una vez (`ConnectionError`); la orden termina con código 1 y se relanza.

**Pasos:**
1. Poner tu token en `.env`: `EARTHDATA_TOKEN=...`. Va solo en `.env`, nunca en git. Tu cuenta debe haber aceptado la EULA de GES DISC.
2. Relanzar hasta que termine. Retoma el primer año que falte y no repite los ya guardados:
   ```bash
   tv ingest-fenomenos --solo-adicionales --fuentes imerg
   ```
   No subas los hilos por encima de 4: con 12, GES DISC respondió 401 por límite de tasa. Puedes dejarlo en un bucle (`until tv ingest-fenomenos --solo-adicionales --fuentes imerg; do sleep 60; done`) en una máquina que no se suspenda.
3. Cuando el manifiesto llegue a 2025 (hasta 2025-09-30, el rango V07 Final):
   ```bash
   tv verificar-integridad
   tv experimentos --solo fuentes
   tv informe
   tv publicar --exportar resultados/contrato/expedientes.json
   pytest tests/integridad tests/experimentos/test_informe.py
   ```
4. Commit de `data/raw/imerg/manifiesto.json`, `data/raw/registro_descarga.json`, `resultados/`, `docs/experimentos.md`, más la entrada en la bitácora y en pendientes.

IMERG solo alimenta el contraste de fuentes (`resultados/fuentes.json`). Ningún modelo depende de él, así que no hace falta repetir los demás experimentos.

### 2.3 Si tus crudos no coinciden con los manifiestos
Los crudos (`data/raw/*/*`) no están en git; solo sus manifiestos. Si `tv verificar-integridad` muestra crudos **alterados** o **faltantes** en tu máquina:
- **Faltantes:** `tv ingest-fenomenos`. Los nacionales también los descarga `tv experimentos --solo nacional`.
- **Alterados:** vuelve a descargar solo esas fuentes. POWER y USGS se actualizan y su SHA-256 cambia con cada descarga.
- Después repite `tv experimentos` completo, porque los manifiestos nuevos cambian la procedencia, y haz commit de los manifiestos junto con los resultados. Así se hizo el 15-11 (ver la bitácora, H18).

### 2.4 Decisiones del equipo que dejó abiertas la auditoría (§11 de `auditoria-metricas.md`)
1. **Completitud sísmica.** La Mc por década llega a 4,9–5,1 antes de 2000, por encima de la Mc usada (4,5). Opciones:
   - Mc variable por periodo;
   - empezar la serie de conteos en 2000;
   - dejarlo como limitación declarada.

   Cualquier cambio exige repetir `tv experimentos` y documentarlo.
2. **Sustitutos del caos en ventanas.** Con 39 por ventana, ningún p puede sobrevivir a Holm. Si se quiere una prueba por ventana con corrección, subir `n_sustitutos` en `config/historial.yaml`; 999 multiplica el tiempo por unas 25 veces.

### 2.5 Opcionales
- **Asistente conversacional:** necesita una clave de API del proveedor; el verificador numérico ya funciona sin ella.
- **Redes líquidas (LNN/CfC):** no están implementadas. Si se agregan, se registran en `modelos/redes.py` y se repite `tv experimentos`.
- **Pitch y video:** usar `docs/presentacion-ejecutiva.md` y `docs/capturas/`, con las cifras vigentes (§1), no las anteriores a la auditoría.
- **Fuentes nacionales** (SENAMHI, IGP, INGEMMET, ANA): requieren convenio o descarga manual verificada.

### 2.6 Nota de entorno
Con Node 26, `npm test` necesita `NODE_OPTIONS=--no-experimental-webstorage`, porque Node trae su propio `localStorage` y tapa el de jsdom. CI usa Node 22 y no lo necesita.

---

## 3. Prompt de traspaso (para pegar en el asistente)

```text
# Traspaso de TerraVerdict: tareas pendientes después de la auditoría de métricas

## Contexto
- Proyecto TerraVerdict, NASA Space Apps 2026, reto "Be An Earth System Trend Detective!", sede
  Arequipa. Uso no comercial (hackatón). Repositorio DiegoNiS/terraverdict; se trabaja solo en `main`.
- Equipo: Ower Frank, MaxsForocca y DiegoNiS.
- Reglas que no se negocian:
  1. Solo datos reales, verificables y trazables a fuentes oficiales (NASA, NOAA, USGS, Smithsonian).
  2. Toda cifra mostrada sale de `resultados/*.json`, generados por el pipeline con procedencia y SHA-256.
     Ninguna elección (modelo, cifra destacada) puede hacerse mirando la prueba.
  3. Distinguir implementado, verificado, pendiente y lo que requiere validación experimental.
     Nada se declara terminado sin evidencia ejecutada.
  4. Los resultados no son alertas oficiales (SENAMHI, IGP, INGEMMET, INDECI).
  5. Cada avance: código, pruebas que pasan, entrada en docs/bitacora.md, actualización de
     docs/pendientes.md y commit en `main` con mi propio usuario de GitHub.
  6. Los secretos (EARTHDATA_TOKEN, TV_JWT_SECRETO) solo en `.env` o en el panel de Vercel, nunca en git.

## 1. Ponerse al día
git fetch origin && git checkout main && git pull --ff-only origin main
Lee en este orden: docs/traspaso.md (este traspaso, con los pasos detallados),
docs/auditoria-metricas.md, docs/pendientes.md, la primera entrada de docs/bitacora.md,
docs/metodologia.md y config/modelos.yaml.

Entornos y pruebas (resultado esperado: ciencia 135 pasan y 2 se omiten; backend 73; frontend 33; E2E 2 de 2):
python -m venv .venv && . .venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -e ".[dev,ml]" && pip install -e "backend[dev]"
pytest && tv verificar-integridad
cd backend && python -m venv .venv && .venv/bin/pip install -e ".[dev]" && .venv/bin/pytest && cd ..
cd frontend && npm ci && npm run typecheck && npm run lint && npm test && npm run build && npm run e2e -- --trace off
(Con Node 26: anteponer NODE_OPTIONS=--no-experimental-webstorage a npm test.)
Si `tv verificar-integridad` muestra crudos alterados o faltantes, sigue docs/traspaso.md §2.3 antes
de correr experimentos.

## 2. Cifras vigentes (no uses las anteriores a la auditoría)
Historial fuera de muestra, con el modelo que eligió la validación de cada año:
sequía a 1 mes 0,658 y a 3 meses 0,232 (confirmadas); lluvia a 1 día 0,031 y sismos 0,149 bits
(no confirmados). "Ridge 0,711" y "PatchTST 0,256" eran cifras elegidas con la prueba: no usarlas.

## 3. Tareas pendientes (detalle en docs/traspaso.md §2)
1. Vercel (solo si tengo permisos de owner del repositorio): integración de GitHub, importar el
   repositorio, TV_JWT_SECRETO (≥ 32 caracteres), verificar /api/v1/salud/lista y la E2E con
   E2E_BASE_URL apuntando al sitio publicado. Si no tengo permisos, no tocar y dejarlo para DiegoNiS.
2. IMERG 2002–2025: EARTHDATA_TOKEN en .env; repetir `tv ingest-fenomenos --solo-adicionales
   --fuentes imerg` hasta llegar a 2025 (≈ 45 min por año, 4 hilos como máximo, se reanuda solo).
   Después: tv verificar-integridad, tv experimentos --solo fuentes, tv informe,
   tv publicar --exportar resultados/contrato/expedientes.json, pruebas, bitácora, pendientes y commit.
3. Proponer al equipo (sin decidir solo) qué hacer con la completitud sísmica previa a 2000
   (docs/auditoria-metricas.md §11, riesgo 1). Si se cambia, repetir tv experimentos, informar las
   cifras nuevas y explicar por qué cambiaron.
4. Opcionales: asistente conversacional (necesita clave de API), redes líquidas LNN/CfC, pitch y
   video con las cifras vigentes.

## 4. Al cambiar el backend o los esquemas
cd backend && .venv/bin/python -m app.cli exportar-openapi --salida ../docs/api/openapi.json
cd frontend && npm run api:tipos

## 5. Antes de cerrar la sesión
Pruebas completas, tv verificar-integridad (código 0), entrada en docs/bitacora.md, docs/pendientes.md
actualizado, commit en main y push. Si algo queda a medias (una descarga larga), detenlo, deja el
manifiesto consistente y actualiza docs/traspaso.md.
```
