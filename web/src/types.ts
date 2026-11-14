// Espejo del esquema del expediente. Generar el real con:
//   python -m terraverdict.contracts.expediente > src/schema.json
export interface Sello { codigo: "robusta" | "fragil" | "no_decidible" | "sin_tendencia"; emoji: string; fallan: string[]; pendientes: string[]; nota: string }
export interface Resultado {
  n: number; periodo: [number, number];
  sen: { sen_por_decada: number; ic_por_decada: [number, number]; pendiente: number; ordenada: number };
  mk: { p_variantes: Record<string, number>; p_conservador: number; variante_limitante: string };
  ventanas: { n_ventanas: number; pct_mismo_signo: number | null; pct_significativas: number | null } | null;
  enso: { evaluada: boolean; [k: string]: unknown } | null;
  palanca: { evaluada: boolean; sobrevive?: boolean; sen_por_decada?: number; quitados?: number } | null;
  detectabilidad: { anios_necesarios: number | null; anios_disponibles: number };
  independencia: { n_familias_mismo_signo: number } | null;
  sello: Sello;
}
export interface Expediente {
  id: string; tipo: string; serie: Record<string, number>; veredicto: string; advertencias: string[];
  objeto: Record<string, string>; periodo: { desde: number; hasta: number; n: number };
  resultado: Resultado;
  procedencia: { preregistro_sha256: string; entradas_sha256: string; generado_utc: string; codigo_commit: string | null };
}
