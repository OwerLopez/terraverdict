import { t } from "./i18n";

/** Nombres de los modelos tal como se publican en la literatura (los mismos del informe). */
const NOMBRES: Record<string, [string, string]> = {
  ref_climatologia: ["Climatología (referencia)", "Climatology (reference)"],
  ref_persistencia: ["Persistencia (referencia)", "Persistence (reference)"],
  logistica: ["Regresión logística", "Logistic regression"],
  ridge: ["Ridge", "Ridge"],
  poisson_glm: ["GLM de Poisson", "Poisson GLM"],
  gbm: ["Gradient boosting", "Gradient boosting"],
  mlp: ["MLP", "MLP"],
  dlinear: ["DLinear", "DLinear"],
  lstm: ["LSTM", "LSTM"],
  gru: ["GRU", "GRU"],
  tcn: ["TCN (convolucional)", "TCN (convolutional)"],
  nbeats: ["N-BEATS", "N-BEATS"],
  nhits: ["N-HiTS", "N-HiTS"],
  patchtst: ["PatchTST", "PatchTST"],
  itransformer: ["iTransformer", "iTransformer"],
  ssm_selectivo: ["SSM selectivo", "Selective SSM"],
  ensamble_top3: ["Ensamble (3 mejores)", "Ensemble (top 3)"],
  ensamble_ponderado: ["Ensamble ponderado", "Weighted ensemble"],
  seleccion_validacion: ["Elegido en validación (año a año)", "Chosen on validation (each year)"],
};

const FAMILIAS: Record<string, [string, string]> = {
  referencia: ["Referencia", "Reference"],
  clasico: ["Clásico", "Classical"],
  red_neuronal: ["Red neuronal", "Neural network"],
  ensamble: ["Ensamble", "Ensemble"],
};

export const nombreModelo = (clave: string): string => {
  const par = NOMBRES[clave];
  return par ? t(par[0], par[1]) : clave.replace(/_/g, " ");
};

export const nombreFamilia = (clave: string): string => {
  const par = FAMILIAS[clave];
  return par ? t(par[0], par[1]) : clave;
};

/**
 * Umbral de Diebold-Mariano de la regla de evidencia. Debe coincidir con
 * config/modelos.yaml (evaluacion.p_diebold_mariano); una prueba del paquete científico lo exige.
 */
export const UMBRAL_P_DM = 0.1;

/** Regla del proyecto (docs/metodologia.md): confirmada = IC90 > 0 Y Diebold-Mariano p < UMBRAL_P_DM. */
export function evidencia(icInferior: number | null | undefined, p: number | null | undefined): "confirmada" | "indicio" | "no_confirmada" {
  const ic = (icInferior ?? -1) > 0;
  const dm = (p ?? 1) < UMBRAL_P_DM;
  return ic && dm ? "confirmada" : ic || dm ? "indicio" : "no_confirmada";
}

/** Variables de entrada de los modelos (claves de resultados/*.json) con nombre legible. */
const VARIABLES: Record<string, [string, string]> = {
  lluvia_log: ["Lluvia (log)", "Rainfall (log)"],
  humedad_especifica: ["Humedad específica", "Specific humidity"],
  humedad_relativa: ["Humedad relativa", "Relative humidity"],
  temperatura: ["Temperatura", "Temperature"],
  amplitud_termica: ["Amplitud térmica", "Diurnal range"],
  presion: ["Presión", "Pressure"],
  viento: ["Viento", "Wind"],
  radiacion: ["Radiación solar", "Solar radiation"],
  oni: ["ONI (El Niño)", "ONI (El Niño)"],
  estacion_seno: ["Estación (seno)", "Season (sine)"],
  estacion_coseno: ["Estación (coseno)", "Season (cosine)"],
  spi1: ["SPI-1", "SPI-1"],
  spi3: ["SPI-3", "SPI-3"],
  spi6: ["SPI-6", "SPI-6"],
  anomalia_temperatura: ["Anomalía de temperatura", "Temperature anomaly"],
  anomalia_humedad: ["Anomalía de humedad", "Humidity anomaly"],
  mes_seno: ["Mes (seno)", "Month (sine)"],
  mes_coseno: ["Mes (coseno)", "Month (cosine)"],
  conteo_log: ["Conteo sísmico (log)", "Earthquake count (log)"],
  conteo_independiente_log: ["Conteo independiente (log)", "Declustered count (log)"],
  magnitud_maxima: ["Magnitud máxima", "Maximum magnitude"],
};

export const nombreVariable = (clave: string): string => {
  const par = VARIABLES[clave];
  return par ? t(par[0], par[1]) : clave.replace(/_/g, " ");
};

/** Series del diagnóstico de dinámica. */
const SERIES: Record<string, [string, string]> = {
  lluvia_pentadas_cabecera: ["Lluvia por péntadas · POWER", "5-day rainfall · POWER"],
  lluvia_pentadas_cabecera_chirps: ["Lluvia por péntadas · CHIRPS", "5-day rainfall · CHIRPS"],
  temperatura_diaria_cabecera: ["Temperatura diaria · POWER", "Daily temperature · POWER"],
  spi3_mensual_cabecera: ["SPI-3 mensual", "Monthly SPI-3"],
  oni_mensual: ["ONI mensual (NOAA)", "Monthly ONI (NOAA)"],
  sismos_conteo_mensual: ["Sismos por mes (USGS)", "Earthquakes per month (USGS)"],
  sismos_intereventos_log: ["Intervalos entre sismos (log)", "Inter-event times (log)"],
};

export const nombreSerie = (clave: string): string => {
  const par = SERIES[clave];
  return par ? t(par[0], par[1]) : clave.replace(/_/g, " ");
};

/** Tareas del historial con un nombre corto para los selectores. */
const TAREAS: Record<string, [string, string]> = {
  lluvia_extrema_power: ["Lluvia fuerte · 1 día", "Heavy rain · 1 day"],
  lluvia_extrema_chirps: ["Lluvia fuerte · CHIRPS", "Heavy rain · CHIRPS"],
  sequia_h1_power: ["Sequía · 1 mes", "Drought · 1 month"],
  sequia_h3_power: ["Sequía · 3 meses", "Drought · 3 months"],
  sismos_conteo_mensual: ["Sismos por mes", "Earthquakes per month"],
};

export const nombreTarea = (clave: string): string => {
  const par = TAREAS[clave];
  return par ? t(par[0], par[1]) : clave.replace(/_/g, " ");
};
