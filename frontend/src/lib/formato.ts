/** Formato de números, fechas y unidades en español (Perú), con signo menos tipográfico. */

const SIMBOLOS: Record<string, string> = {
  mm: "mm",
  "mm/d": "mm/día",
  "mm/h": "mm/h",
  Cel: "°C",
  K: "K",
  "1": "",
  "%": "%",
  "m3/m3": "m³/m³",
  km2: "km²",
  ha: "ha",
  hm3: "hm³",
  "m3/s": "m³/s",
  m: "m",
  "m/s": "m/s",
  "MJ/m2/d": "MJ m⁻² día⁻¹",
  deg: "°",
  count: "",
  NTU: "NTU",
  MUSD: "M US$",
};

export function simboloUnidad(codigo: string): string {
  if (codigo in SIMBOLOS) return SIMBOLOS[codigo] ?? codigo;
  return codigo.replace("Cel/decada", "°C/década").replace("/decada", "/década");
}

export function numero(valor: number | null | undefined, decimales = 2, opciones: { signo?: boolean } = {}): string {
  if (valor === null || valor === undefined || !Number.isFinite(valor)) return "—";
  // "es" usa coma decimal (como la documentación y el verificador numérico); "es-PE" usaría punto.
  const texto = new Intl.NumberFormat("es", {
    minimumFractionDigits: decimales,
    maximumFractionDigits: decimales,
  }).format(Math.abs(valor));
  if (valor < 0) return `−${texto}`;
  return opciones.signo && valor > 0 ? `+${texto}` : texto;
}

export function conUnidad(valor: number | null | undefined, unidad: string, decimales = 2, signo = false): string {
  const simbolo = simboloUnidad(unidad);
  const n = numero(valor, decimales, { signo });
  if (!simbolo) return n;
  return simbolo === "%" ? `${n} %` : `${n} ${simbolo}`;
}

/** Valor p legible: "< 0,001" en lugar de 0,0000. */
export function valorP(p: number | null | undefined): string {
  if (p === null || p === undefined) return "—";
  if (p < 0.001) return "< 0,001";
  return numero(p, 3);
}

const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];

export function fecha(iso: string | null | undefined, precision: "dia" | "mes" | "anio" = "dia"): string {
  if (!iso) return "—";
  const [a, m, d] = iso.slice(0, 10).split("-").map(Number);
  if (!a) return iso;
  if (precision === "anio") return String(a);
  const mes = MESES[(m ?? 1) - 1] ?? "";
  return precision === "mes" ? `${mes} ${a}` : `${d} ${mes} ${a}`;
}

export function fechaHora(iso: string | null | undefined): string {
  if (!iso) return "—";
  const f = new Date(iso);
  if (Number.isNaN(f.getTime())) return iso;
  return new Intl.DateTimeFormat("es-PE", { dateStyle: "medium", timeStyle: "short" }).format(f);
}

export function haceCuanto(iso: string | null | undefined, ahora: Date = new Date()): string {
  if (!iso) return "—";
  const ms = ahora.getTime() - new Date(iso).getTime();
  const min = Math.round(ms / 60000);
  if (min < 1) return "hace instantes";
  if (min < 60) return `hace ${min} min`;
  const h = Math.round(min / 60);
  if (h < 48) return `hace ${h} h`;
  return `hace ${Math.round(h / 24)} días`;
}

export function anio(iso: string): number {
  return Number(iso.slice(0, 4));
}

/** Decimales con que la fuente escribió el número (404,01 → 2; 373,3 → 1; 5000 → 0), máximo 3. */
export function decimalesDe(valor: number): number {
  const texto = String(Math.abs(valor));
  if (texto.includes("e")) return 3;
  return Math.min(3, texto.split(".")[1]?.length ?? 0);
}

const PREFIJO_COTA: Record<string, string> = { minima: "> ", maxima: "< ", aproximada: "≈ " };
export const TEXTO_COTA: Record<string, string> = {
  minima: "Cota inferior: la fuente dice «más de»",
  maxima: "Cota superior: la fuente dice «menos de»",
  aproximada: "Valor aproximado según la fuente",
};

/** Cifra citada tal como la dio la fuente: misma precisión y, si es una cota, con su signo. */
export function cifraCitada(c: { valor: number; unidad: string; cota?: string }): string {
  return `${PREFIJO_COTA[c.cota ?? ""] ?? ""}${conUnidad(c.valor, c.unidad, decimalesDe(c.valor))}`;
}

const ETIQUETAS_METRICA: Record<string, string> = {
  n_ventanas: "Ventanas evaluadas",
  pct_mismo_signo: "% con el mismo signo",
  pct_significativas_p010: "% significativas (p < 0,10)",
  longitud_minima_anios: "Longitud mínima (años)",
  r_pearson_con_oni_djf: "r con ONI (dic–feb)",
  p_pearson: "p de la correlación",
  pendiente_sin_enso_por_decada: "Pendiente sin El Niño (por década)",
  p_pendiente_sin_enso: "p sin El Niño",
  coef_oni: "Coeficiente del ONI",
  sigma_ruido: "σ del ruido",
  phi_ar1: "φ autocorrelación AR(1)",
  anios_necesarios: "Años necesarios",
  anios_disponibles: "Años disponibles",
  elevacion_celda_m: "Elevación de la celda (m)",
  por_decada: "Pendiente por década",
  ic90_lo: "IC 90 % inferior",
  ic90_hi: "IC 90 % superior",
  p_clasico: "p Mann-Kendall clásico",
  p_hamed_rao: "p Hamed-Rao",
  p_conservador: "p conservador",
  suma_represas_hm3: "Suma de represas (hm³)",
  total_reportado_hm3: "Total reportado (hm³)",
  diferencia_hm3: "Diferencia (hm³)",
  lon: "Longitud",
  lat: "Latitud",
  n: "Observaciones",
};

export function etiquetaMetrica(clave: string): string {
  return ETIQUETAS_METRICA[clave] ?? clave.replaceAll("_", " ").replace("anios", "años").replace("pct", "%");
}

export function valorMetrica(v: unknown): string {
  if (typeof v === "number") {
    if (Number.isInteger(v)) return numero(v, 0);
    return numero(v, Math.abs(v) >= 10 ? 1 : 3);
  }
  if (typeof v === "boolean") return v ? "sí" : "no";
  return v === null || v === undefined ? "—" : String(v);
}
