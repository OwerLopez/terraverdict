/**
 * Tipos de `resultados/contrato/indicadores.json` (generado por `tv publicar` desde los crudos; ver
 * src/terraverdict/publicar/indicadores.py). La API lo entrega sin tipar dentro de `/api/v1/portada`.
 */
export type FilaSpi = { mes: string; spi3: number; acumulado_3m_mm: number; media_climatologica_3m_mm: number; confiable: boolean };
export type Trimestre = { trimestre: string; anio: number; valor: number };
export type NinoMes = { anio: number; mes: number; nino12_anom: number; nino34_anom: number };
export type CategoriaEnso = { categoria: string; nombre: string; n: number; con_sequia: number; frecuencia: number | null; ic90: [number, number]; anios_con_sequia: number[] };
export type SeriePrueba = {
  objetivo: string | null;
  modelo: string | null;
  familia: string | null;
  fechas: string[];
  observado: (number | null)[];
  pronostico: (number | null)[];
  referencia: (number | null)[];
  intervalo_90: ([number, number] | null)[];
  prueba?: Record<string, number> | null;
  puntaje_validacion?: number | null;
};
export type EventoLluvia = {
  evento: string;
  titulo: string;
  mes: string;
  dias_evaluados: number;
  dias_lluvia_fuerte_observados: number;
  probabilidad_media_modelo_en_dias_fuertes: number | null;
  probabilidad_media_climatologia_en_dias_fuertes: number | null;
  probabilidad_media_modelo_resto: number | null;
};

export type Indicadores = {
  generado_utc: string;
  enso: {
    oni: { valor: number; trimestre: string; anio: number; intensidad: string; trimestres_consecutivos_nino: number; trimestres_consecutivos_nina: number; episodio_noaa: "el_nino" | "la_nina" | "sin_episodio"; ultimos: Trimestre[] };
    criterio_episodio: string;
    criterio_intensidad: string;
    nino_mensual?: { anio: number; mes: number; nino34_anom: number; nino12_anom: number; ultimos: NinoMes[]; base: string };
  };
  sequia_actual: { punto: string; lluvia_ultimo_mes: string; serie: FilaSpi[]; ultimo: FilaSpi | null; ultimo_confiable: FilaSpi | null; categoria_ultimo_confiable: string | null; criterio_confiable: string };
  sequia_por_enso: { definicion: string; periodo: [number, number] | null; categorias: CategoriaEnso[]; fisher_nino_vs_resto: { p_unilateral: number; nino: [number, number]; resto: [number, number] }; lectura: string };
  altitud: {
    periodo: [string, string];
    estacion_ciudad: { estacion: string; nombre: string; elevacion_m: number; temperatura_media_c: number; cobertura: number };
    celda_cabecera: { lon: number; lat: number; elevacion_celda_m: number; temperatura_media_c: number };
    celda_ciudad_power: { lon: number; lat: number; elevacion_celda_m: number; temperatura_media_c: number };
    diferencia_c: number;
    desnivel_m: number;
    gradiente_observado_c_km: number;
    gradiente_referencia_c_km: number;
    esperado_con_referencia_c: number;
  };
  predicciones: {
    sequia: Record<string, SeriePrueba>;
    lluvia_eventos_documentados: EventoLluvia[];
    lluvia_fuente?: string;
    lluvia_umbral_mm?: number;
  } | null;
  particion_temporal: Record<"entrenamiento" | "validacion" | "prueba", [string, string]> | null;
  crudos: { archivo: string; sha256: string }[];
};

export function comoIndicadores(x: unknown): Indicadores | null {
  return x && typeof x === "object" && "enso" in x ? (x as Indicadores) : null;
}

/** Categoría ENSO del simulador para un valor del ONI (mismos cortes que el cálculo). */
export function categoriaEnso(oni: number): string {
  if (oni >= 1.5) return "nino_fuerte";
  if (oni >= 0.5) return "nino";
  if (oni <= -0.5) return "nina";
  return "neutro";
}
