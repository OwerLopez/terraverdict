/**
 * Títulos de los expedientes en inglés. El pipeline los publica en español con un conjunto cerrado de
 * patrones (`src/terraverdict/publicar/convertir.py`); aquí se traducen esos patrones. Un título que no
 * coincide con ninguno se muestra tal cual (nunca se inventa una traducción).
 */
import { idiomaActual } from "./i18n";

const REGLAS: [RegExp, string][] = [
  [/^Sequía: SPI-3 a (\d+) mes\(es\) en la cabecera del Chili/, "Drought: SPI-3 $1 month(s) ahead in the Chili headwaters"],
  [/^Lluvia fuerte a 1 día en la cabecera del Chili/, "Heavy rain 1 day ahead in the Chili headwaters"],
  [/^Conteo sísmico mensual frente a Poisson/, "Monthly earthquake counts vs. Poisson"],
  [/^Sismicidad a (\d+) km de Arequipa/, "Seismicity within $1 km of Arequipa"],
  [/^Recurrencia histórica de erupciones en el sur del Perú/, "Historical eruption recurrence in southern Peru"],
  [/^Deslizamientos detonados por lluvia en el sur del Perú/, "Rain-triggered landslides in southern Peru"],
  [/^Dinámica de las series reales: caos, no linealidad o ruido/, "Dynamics of real series: chaos, nonlinearity or noise"],
  [/^Historial de métricas: habilidad año a año y dinámica en ventanas/, "Metrics history: year-by-year skill and windowed dynamics"],
  [/^Panorama nacional: clima, sequía y sismicidad de los (\d+) departamentos/, "National overview: climate, drought and seismicity of Peru's $1 regions"],
  [/^Lluvia de diciembre a marzo en la cabecera del Chili/, "December–March rainfall in the Chili headwaters"],
  [/^Temperatura media anual en la cabecera del Chili/, "Mean annual temperature in the Chili headwaters"],
  [/^Tendencia de lluvia dic mar/, "December–March rainfall trend"],
  [/^Tendencia de t2m media anual/, "Mean annual 2 m air temperature trend"],
  [/^Relevancia de variables · Lluvia extrema en la cabecera/, "Variable relevance · Extreme rain in the headwaters"],
  [/^Lluvia extrema en la cabecera/, "Extreme rain in the headwaters"],
  [/^Degradación de bofedales/, "Wetland (bofedal) degradation"],
  [/^Déficit de las represas/, "Reservoir deficit"],
  [/^Turbidez en la captación/, "Turbidity at the water intake"],
];

/** Título en el idioma de la interfaz (los paréntesis finales, p. ej. la fuente o el periodo, se conservan). */
export function traducirTitulo(titulo: string): string {
  if (idiomaActual() !== "en") return titulo;
  for (const [patron, ingles] of REGLAS) {
    if (patron.test(titulo)) return titulo.replace(patron, ingles);
  }
  return titulo;
}

/** Texto bilingüe de los datos: usa la versión en inglés del dato si existe (nunca una traducción inventada). */
export function bilingueDato(es: string, en?: string | null): string {
  return idiomaActual() === "en" && en ? en : es;
}
