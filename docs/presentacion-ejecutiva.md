# TerraVerdict · Presentación ejecutiva

> Cada cifra viene de una fuente citada (eventos con enlace en `datos/eventos/arequipa.json`) o de
> `resultados/*.json` (con commit, preregistro y hash de cada dato). No hay proyecciones ni cifras
> estimadas por el equipo.

---

## 1. El problema: el agua de Arequipa depende de lo que pasa río arriba

- **Febrero de 2025:** la turbidez llegó a **5000 NTU** y la potabilización se detuvo; **más del 70 %** de la población se quedó sin agua potable (El Búho).
- **Noviembre de 2023:** las represas del sistema Chili tenían **159 de 409 hm³** útiles (La República). Ese año se declararon en emergencia por déficit hídrico **70 distritos** (Andina).
- **Aguada Blanca:** su capacidad de diseño era de **43 hm³** y la actual se estima en cerca de **22 hm³**, por sedimentación (El Búho).
- **Bofedales** de la Reserva de Salinas y Aguada Blanca: **−8,7 %** de área entre 2000 y 2024 (Universidad Católica de Santa María).
- **Inversión en juego:** SEDAPAR comprometió **US$ 1,5 millones** en el MERESE para 2024–2026 (Forest Trends).

**La pregunta de quien decide:** ¿qué señales son reales, cuáles se pueden anticipar y con qué confianza?

---

## 2. La propuesta: respuestas con su evidencia y su nivel de confianza

TerraVerdict no da una respuesta sin decir de dónde sale ni cuánta confianza merece.

| Garantía | Cómo se cumple |
|---|---|
| Datos reales y trazables | 73 crudos con SHA-256: NASA POWER, CHIRPS, USGS, IGP, Smithsonian GVP, NASA GLC, NOAA |
| Reglas fijadas antes de mirar | Preregistro y partición temporal congelados; la prueba (2021–2026) se usa una sola vez |
| Siempre frente a una referencia | Cada modelo se compara con la climatología y la persistencia, con IC al 90 % |
| Abstención explícita | Si no hay habilidad o faltan datos, el sistema lo dice y no publica pronóstico |
| Robustez a la fuente | Lluvia y sequía se evalúan con dos productos independientes (POWER y CHIRPS) |
| No es una alerta oficial | Aviso permanente: las alertas las emiten SENAMHI, IGP, INGEMMET e INDECI |

---

## 3. Valor científico: qué sabemos y qué no

| Pregunta | Respuesta (prueba 2021–2026) |
|---|---|
| ¿Se anticipa la sequía a 1 mes (SPI-3)? | **Sí.** Habilidad 0,78 (IC90 0,67–0,84) con POWER y 0,62 (0,49–0,77) con CHIRPS; mejor que la persistencia |
| ¿Y a 3 meses? | **Poco.** 0,20 (0,12–0,26) con POWER y 0,09 (0,05–0,11) con CHIRPS |
| ¿Se anticipa la lluvia fuerte de mañana? | **Muy poco y depende del producto.** 0,08 (0,003–0,15) con POWER; con CHIRPS no se confirma (−0,01 a 0,09) |
| ¿Se pronostican sismos? | **No.** El conteo mensual solo refleja el agrupamiento de réplicas. La sismicidad se describe: b = 1,00 (0,96–1,03) |
| ¿Qué tan frecuentes son las erupciones? | Frecuencia histórica desde 1550: Ubinas 4,5 % al año, Sabancaya 1,9 %, Misti 0,8 % (a 17,8 km de la ciudad) |
| ¿Hay umbral de lluvia para deslizamientos? | **Todavía no:** hay 28 eventos y se necesitan 30. El sistema se abstiene |
| ¿La lluvia es caótica? | **No.** Se comporta como un proceso lineal estocástico, igual con POWER que con CHIRPS. Ninguna de las 7 series muestra caos |

Lo que el sistema **no** afirma vale tanto como lo que afirma.

---

## 4. Valor tecnológico: una cadena reproducible de punta a punta

```
Fuentes reales → ingesta con SHA-256 → experimentos (10 redes + modelos clásicos)
→ informe automático → API con reglas científicas → interfaz con vidrio azul
```

- **Reproducible:** `tv ingest-fenomenos && tv experimentos && tv informe` regenera todo; la corrida completa tarda unos 8 minutos en 20 núcleos.
- **Reglas en la API:** el backend **rechaza** con 422 un resultado que viole una regla. Por ejemplo, elegir un modelo por su desempeño en prueba, o afirmar caos sin todas las condiciones.
- **Calidad verificada:** 92 pruebas del paquete científico, 65 del backend y 23 del frontend, con integración continua en tres trabajos.
- **Fuentes nacionales:** la API del IGP ya está integrada. SENAMHI, ANA e INGEMMET entran por el contrato de series cuando haya convenio o descarga verificada, sin cambiar la arquitectura.

---

## 5. Valor económico: mejores decisiones con el dinero que ya existe

Sin cifras inventadas: el valor está en **orientar recursos que ya están comprometidos**.

- El MERESE de SEDAPAR invierte **US$ 1,5 millones** (2024–2026) en la cuenca. TerraVerdict aporta evidencia trazable sobre qué cambia y dónde, para priorizar ese gasto.
- La señal de **sequía a 1 mes** tiene habilidad confirmada. Es información útil para la operación de las represas, que en 2023 llegaron a **159 de 409 hm³**.
- Saber qué **no** se puede anticipar (lluvia fuerte diaria con un solo producto, sismos) evita invertir en alertas sin respaldo.

---

## 6. Siguientes pasos (dependen de terceros, no del código)

| Paso | Qué se necesita |
|---|---|
| IMERG (lluvia satelital diaria) | Aceptar una vez la licencia de GES DISC en la cuenta Earthdata del equipo |
| Umbral de deslizamientos | El inventario de INGEMMET (≥ 30 eventos) |
| Estaciones SENAMHI | Convenio o descarga verificada, que entra por el contrato de series |
| Piloto con usuarios | SEDAPAR o AUTODEMA: medir una decisión real tomada con la herramienta |

---

*Resultados experimentales. No son alertas oficiales (SENAMHI, IGP, INGEMMET, INDECI).*
