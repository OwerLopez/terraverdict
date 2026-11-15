# API de TerraVerdict (v1)

Contrato completo y siempre actualizado: [`openapi.json`](openapi.json). Una prueba del backend
(`test_openapi_versionado_coincide_con_el_codigo`) falla si este archivo y el código difieren, y el
frontend genera sus tipos a partir de él (`npm run api:tipos`).
Con el servidor en marcha, la documentación interactiva está en `/api/docs` (Swagger) y `/api/redoc`.

- **Base:** `/api/v1`
- **Formato:** JSON (UTF-8). Las fechas siguen ISO 8601; las geometrías siguen GeoJSON (RFC 7946, EPSG:4326).
- **Errores:** RFC 9457 (`application/problem+json`), con un `codigo` estable y el `request_id`. Ver [Errores](#errores).

## Autenticación

| Mecanismo | Cabecera | Para quién | Cómo se obtiene |
|---|---|---|---|
| Token JWT (OAuth2, flujo de contraseña) | `Authorization: Bearer <token>` | Personas: `lector`, `analista`, `admin` | `POST /api/v1/auth/token` con `username` y `password` (formulario) |
| Clave de servicio | `X-API-Key: <clave>` | Pipeline (`ingesta`) y trabajadores (`trabajador`) | `python -m app.cli crear-clave --nombre … --alcance ingesta` o `POST /api/v1/claves` (admin) |

- Las lecturas son públicas. Las escrituras exigen el rol o el alcance que indica cada operación en el OpenAPI.
- El inicio de sesión está limitado por IP (`TV_LOGIN_INTENTOS_POR_MINUTO`).
- Una clave se muestra **una sola vez** al crearla; en la base solo se guarda su hash.

## Endpoints

| Grupo | Método y ruta | Uso | Permiso |
|---|---|---|---|
| Sistema | `GET /salud`, `GET /salud/lista` | Vida y preparación (base de datos accesible) | público |
| | `GET /resumen` | Estado agregado para el panel | público |
| | `GET /unidades-medida` | Vocabulario de unidades (compatible con UCUM) | público |
| Acceso | `POST /auth/token`, `GET /auth/yo` | Iniciar sesión e identidad | público / autenticado |
| | `GET, POST /usuarios`, `PATCH /usuarios/{id}` | Gestión de usuarios | admin |
| | `GET, POST /claves`, `DELETE /claves/{id}` | Claves de servicio | admin |
| Catálogo | `GET /fuentes[/{id}]` | Fuentes con su estado de verificación | público |
| | `GET /variables[/{id}]`, `GET /problemas` | Variables físicas y plantillas de problema | público |
| | `GET /eventos`, `GET /verificacion` | Eventos documentados con citas; último informe de verificación | público |
| Dominios | `GET /dominios[/{id}]`, `GET /dominios/{id}/unidades` | Zonas de estudio y unidades (GeoJSON) | público |
| | `POST /unidades`, `PUT /unidades/{id}/geometria` | Registro y geometría de unidades | `ingesta` |
| Series | `GET /series[/{id}]`, `GET /series/{id}/observaciones` | Series y observaciones (con `ETag` / `If-None-Match`) | público |
| | `POST /series`, `PUT /series/{id}/observaciones` | Registro y carga idempotente por fecha | `ingesta` |
| Expedientes | `GET /expedientes[/{id}]` | Resultados científicos inmutables con procedencia | público |
| | `POST /expedientes` | Publicar (idempotente por hash de contenido: 201 nuevo, 200 ya existía) | `ingesta` |
| | `POST /expedientes/{id}/retirar` | Retirar con motivo (se conserva) | admin |
| Fenómenos naturales | `GET /fenomenos[/{id}]` | Catálogo de `config/fenomenos.yaml`: variables con justificación, partición y abstención | público |
| | `GET /capas/sismos?magnitud_min=5`, `GET /capas/volcanes`, `GET /capas/deslizamientos` | Capas GeoJSON del mapa, tomadas del expediente vigente de cada tipo | público |
| | `GET /nacional` | Panorama nacional (M7): 25 departamentos del expediente `panorama_nacional` vigente | público |
| Métricas e historial | `GET /metricas` | Catálogo de métricas (`config/metricas.yaml`): qué mide cada una, cómo leerla y su referencia, en español e inglés | público |
| | `GET /metricas/mapas` | Matrices para los mapas de calor: modelo × tarea por métrica e importancia tarea × variable, de los expedientes `comparacion_modelos` vigentes | público |
| | `GET /historial` | Historial año a año por origen móvil y dinámica en ventanas (M8) del expediente `historial_metricas` vigente | público |
| Ciencia de datos | `GET /relevancia/matriz` | Matriz de Relevancia (solo con expedientes `relevancia`) | público |
| | `GET, POST /ejecuciones` | Manifiestos de ejecución del pipeline | público / `ingesta` |
| Procesos | `GET, POST /procesos`, `GET, PATCH /procesos/{id}` | Cola de procesos científicos | público / analista / `trabajador` |
| | `POST /procesos/reclamar`, `GET, POST /procesos/{id}/eventos` | Protocolo del trabajador y bitácora | `trabajador` |
| Asistente | `POST /asistente/consultas` | Asistente conversacional (pendiente de conexión: 503) | público |
| | `POST /asistente/verificar` | Marca cada cifra de un texto sin respaldo en expedientes | público |

### Tipos de expediente

El campo `resultado.tipo` decide el esquema y sus reglas de publicación, que el backend **valida**:
si un resultado viola una regla, la respuesta es 422.

| Tipo | Módulo | Prefijo del ID | Reglas que se validan |
|---|---|---|---|
| `tendencia` | M2 | `TV-TEN-` | `robusta` exige las cinco pruebas aprobadas; `fragil` exige una prueba fallida; el p conservador es el mayor de las variantes |
| `relevancia` | M1 | `TV-REL-` | Solo es publicable si supera la línea base con el IC por encima de 0 |
| `atribucion` | M3 | `TV-ATR-` | El gemelo debe superar su KGE de validación |
| `pronostico` | M4 | `TV-PRO-` | Publicable solo con CRPSS > 0 en todo el IC. Si hay intervalo conformal, debe contener la mediana. Una abstención impide publicar |
| `alerta` | M4 | `TV-ALE-` | Ventana de validez coherente |
| `colmatacion`, `priorizacion` | M5 | `TV-COL-`, `TV-PRI-` | Significancia conservadora; selección dentro del presupuesto |
| `comparacion_modelos` | M6 | `TV-CMP-` | Exige al menos una referencia. El modelo elegido debe ser el **mejor en validación** (la prueba no elige). Solo se publica si supera a la referencia en validación. Toda abstención lleva motivo |
| `caos` | M6 | `TV-CAO-` | `compatible_con_caos_baja_dimension` exige las cinco condiciones, D2 < 5, λ > 0 y K > 0,8 |
| `recurrencia` | M6 | `TV-REC-` | La probabilidad anual queda dentro de su IC. `es_pronostico` siempre es `false` |
| `sismicidad` | M6 | `TV-SIS-` | El valor b queda dentro de su IC. `es_pronostico` siempre es `false` |
| `inventario` | M6 | `TV-INV-` | No se estima un umbral con menos eventos que el mínimo preregistrado |

Los expedientes de los fenómenos se publican con `tv publicar` (paquete científico) usando una clave
`ingesta` en `TV_CLAVE_INGESTA`. Publicar dos veces el mismo contenido devuelve los mismos IDs.

## Errores

Todas las respuestas de error tienen esta forma:

```json
{
  "type": "https://github.com/DiegoNiS/terraverdict/blob/main/docs/api/README.md#errores-regla_cientifica",
  "title": "El resultado no cumple una regla de publicación",
  "status": 422,
  "detail": "…",
  "instance": "/api/v1/expedientes",
  "codigo": "regla_cientifica",
  "request_id": "0b74c068b7c0472085a740427de8b209",
  "errores": [{"campo": "resultado.mejor_validacion", "mensaje": "…", "tipo": "value_error"}]
}
```

Los clientes deben reaccionar al `codigo`, no al texto. El `request_id` también se envía en la
cabecera `X-Request-ID` y aparece en los registros del servidor, incluso en los errores 500.

### errores-solicitud_invalida
**400.** La solicitud está mal formada (p. ej., parámetros incompatibles).

### errores-no_autenticado
**401.** Falta el token o la clave, o no son válidos o vencieron. Incluye `WWW-Authenticate: Bearer`.

### errores-prohibido
**403.** La identidad no tiene el rol o el alcance que exige la operación (p. ej., publicar sin el alcance `ingesta`).

### errores-no_encontrado
**404.** El recurso no existe, o una referencia del cuerpo (fuente, dominio, variable o expediente) no está en el catálogo.

### errores-metodo_no_permitido
**405.** El método HTTP no está definido para esa ruta.

### errores-conflicto
**409.** El estado actual impide la operación: un ID ya existe, un expediente ya está retirado o se intenta reemplazar un expediente por otro de distinto tipo.

### errores-transicion_invalida
**409.** Transición de estado de un proceso no permitida (p. ej., `completado → en_curso`).

### errores-validacion
**422.** El cuerpo no cumple el contrato o una regla científica del esquema. `errores` indica el campo y el motivo de cada falla.

### errores-regla_cientifica
**422.** El resultado viola una regla de publicación evaluada en el servicio (fuera del esquema).

### errores-demasiadas_solicitudes
**429.** Se superó el límite de intentos de inicio de sesión. Reintentar más tarde.

### errores-servicio_no_disponible
**503.** El módulo todavía no está conectado (p. ej., el asistente sin clave de modelo).

### errores-error_interno
**500.** Error no controlado. El `request_id` permite encontrarlo en los registros.

### errores-error_http
Cualquier otro código HTTP sin código propio.
