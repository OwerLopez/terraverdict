/**
 * Imágenes HLS (30 m) elegidas mes a mes sobre la represa Aguada Blanca por `scripts/timelapse_hls.py`.
 * Cada mes guarda la fecha, el sensor, la cobertura y la nubosidad medidas píxel a píxel dentro del embalse,
 * la URL exacta de la tesela y su SHA-256. Un mes sin imagen válida se muestra como tal (sin interpolar).
 */
import datos from "../datos/timelapse_aguada_blanca.json";

export type ImagenMes = {
  fecha: string;
  capa: "HLS_S30_Nadir_BRDF_Adjusted_Reflectance" | "HLS_L30_Nadir_BRDF_Adjusted_Reflectance";
  sensor: string;
  cobertura: number;
  nubosidad: number;
  url: string;
  sha256: string;
};

export type MesLapso = { mes: string; imagenes_probadas: number; imagenes_completas: number; elegida: ImagenMes | null };

export const LAPSO = datos as unknown as {
  titulo: string;
  generado_utc: string;
  fuente: string;
  caja_embalse: { lat_min: number; lat_max: number; lon_min: number; lon_max: number; origen: string };
  criterio: { min_cobertura: number; max_nubosidad: number; nubosidad: string };
  meses: MesLapso[];
};

/** Centro del embalse (caja de OpenStreetMap, way 23815221). */
export const CENTRO_AGUADA_BLANCA: [number, number] = [
  (LAPSO.caja_embalse.lon_min + LAPSO.caja_embalse.lon_max) / 2,
  (LAPSO.caja_embalse.lat_min + LAPSO.caja_embalse.lat_max) / 2,
];

/** Imagen válida de un mes ("AAAA-MM"), o null si ese mes no tiene observación sin nubes. */
export function imagenDelMes(mes: string): ImagenMes | null {
  return LAPSO.meses.find((m) => m.mes === mes)?.elegida ?? null;
}
