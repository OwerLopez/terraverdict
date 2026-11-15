/** Formato de números, fechas y unidades en el idioma vigente (es/en), con signo menos tipográfico. */
import { idiomaActual, locale, t } from "./i18n";

const SIMBOLOS: Record<string, string> = {
  mm: "mm",
  "mm/d": "mm/d",
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
  "MJ/m2/d": "MJ m⁻² d⁻¹",
  deg: "°",
  count: "",
  NTU: "NTU",
  MUSD: "M US$",
};

export function simboloUnidad(codigo: string): string {
  if (codigo in SIMBOLOS) return SIMBOLOS[codigo] ?? codigo;
  const decada = t("década", "decade");
  return codigo.replace("Cel/decada", `°C/${decada}`).replace("/decada", `/${decada}`);
}

export function numero(valor: number | null | undefined, decimales = 2, opciones: { signo?: boolean } = {}): string {
  if (valor === null || valor === undefined || !Number.isFinite(valor)) return "—";
  // "es" usa coma decimal (como la documentación y el verificador numérico); "en" usa punto.
  const texto = new Intl.NumberFormat(locale(), {
    minimumFractionDigits: decimales,
    maximumFractionDigits: decimales,
  }).format(Math.abs(valor));
  if (valor < 0) return `−${texto}`;
  return opciones.signo && valor > 0 ? `+${texto}` : texto;
}

/** Número siempre en formato español (coma decimal): lo exige el verificador numérico del backend. */
export function numeroEs(valor: number | null | undefined, decimales = 2, opciones: { signo?: boolean } = {}): string {
  if (valor === null || valor === undefined || !Number.isFinite(valor)) return "—";
  const texto = new Intl.NumberFormat("es", { minimumFractionDigits: decimales, maximumFractionDigits: decimales }).format(Math.abs(valor));
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
  if (p < 0.001) return `< ${numero(0.001, 3)}`;
  return numero(p, 3);
}

const MESES_ES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const MESES_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** Abreviatura del mes (1–12) en el idioma vigente. */
export function nombreMes(m: number): string {
  return (idiomaActual() === "en" ? MESES_EN : MESES_ES)[m - 1] ?? "";
}

export function fecha(iso: string | null | undefined, precision: "dia" | "mes" | "anio" = "dia"): string {
  if (!iso) return "—";
  const [a, m, d] = iso.slice(0, 10).split("-").map(Number);
  if (!a) return iso;
  if (precision === "anio") return String(a);
  const mes = nombreMes(m ?? 1);
  if (precision === "mes") return `${mes} ${a}`;
  return idiomaActual() === "en" ? `${mes} ${d}, ${a}` : `${d} ${mes} ${a}`;
}

export function fechaHora(iso: string | null | undefined): string {
  if (!iso) return "—";
  const f = new Date(iso);
  if (Number.isNaN(f.getTime())) return iso;
  return new Intl.DateTimeFormat(idiomaActual() === "en" ? "en-US" : "es-PE", { dateStyle: "medium", timeStyle: "short" }).format(f);
}

export function haceCuanto(iso: string | null | undefined, ahora: Date = new Date()): string {
  if (!iso) return "—";
  const ms = ahora.getTime() - new Date(iso).getTime();
  const min = Math.round(ms / 60000);
  if (min < 1) return t("hace instantes", "just now");
  if (min < 60) return t(`hace ${min} min`, `${min} min ago`);
  const h = Math.round(min / 60);
  if (h < 48) return t(`hace ${h} h`, `${h} h ago`);
  const dias = Math.round(h / 24);
  return t(`hace ${dias} días`, `${dias} days ago`);
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
export function textoCota(cota: string | undefined): string | undefined {
  if (cota === "minima") return t("Cota inferior: la fuente dice «más de»", "Lower bound: the source says “more than”");
  if (cota === "maxima") return t("Cota superior: la fuente dice «menos de»", "Upper bound: the source says “less than”");
  if (cota === "aproximada") return t("Valor aproximado según la fuente", "Approximate value per the source");
  return undefined;
}

/** Cifra citada tal como la dio la fuente: misma precisión y, si es una cota, con su signo. */
export function cifraCitada(c: { valor: number; unidad: string; cota?: string }): string {
  return `${PREFIJO_COTA[c.cota ?? ""] ?? ""}${conUnidad(c.valor, c.unidad, decimalesDe(c.valor))}`;
}

const ETIQUETAS_METRICA: Record<string, [string, string]> = {
  n_ventanas: ["Ventanas evaluadas", "Windows evaluated"],
  pct_mismo_signo: ["% con el mismo signo", "% with the same sign"],
  pct_significativas_p010: ["% significativas (p < 0,10)", "% significant (p < 0.10)"],
  longitud_minima_anios: ["Longitud mínima (años)", "Minimum length (years)"],
  r_pearson_con_oni_djf: ["r con ONI (dic–feb)", "r with ONI (Dec–Feb)"],
  p_pearson: ["p de la correlación", "Correlation p"],
  pendiente_sin_enso_por_decada: ["Pendiente sin El Niño (por década)", "Slope without El Niño (per decade)"],
  p_pendiente_sin_enso: ["p sin El Niño", "p without El Niño"],
  coef_oni: ["Coeficiente del ONI", "ONI coefficient"],
  sigma_ruido: ["σ del ruido", "Noise σ"],
  phi_ar1: ["φ autocorrelación AR(1)", "φ AR(1) autocorrelation"],
  anios_necesarios: ["Años necesarios", "Years needed"],
  anios_disponibles: ["Años disponibles", "Years available"],
  elevacion_celda_m: ["Elevación de la celda (m)", "Cell elevation (m)"],
  por_decada: ["Pendiente por década", "Slope per decade"],
  ic90_lo: ["IC 90 % inferior", "90 % CI lower"],
  ic90_hi: ["IC 90 % superior", "90 % CI upper"],
  p_clasico: ["p Mann-Kendall clásico", "Classic Mann-Kendall p"],
  p_hamed_rao: ["p Hamed-Rao", "Hamed-Rao p"],
  p_conservador: ["p conservador", "Conservative p"],
  suma_represas_hm3: ["Suma de represas (hm³)", "Sum of reservoirs (hm³)"],
  total_reportado_hm3: ["Total reportado (hm³)", "Reported total (hm³)"],
  diferencia_hm3: ["Diferencia (hm³)", "Difference (hm³)"],
  lon: ["Longitud", "Longitude"],
  lat: ["Latitud", "Latitude"],
  n: ["Observaciones", "Observations"],
};

export function etiquetaMetrica(clave: string): string {
  const par = ETIQUETAS_METRICA[clave];
  if (par) return t(par[0], par[1]);
  return clave.replaceAll("_", " ").replace("anios", t("años", "years")).replace("pct", "%");
}

export function valorMetrica(v: unknown): string {
  if (typeof v === "number") {
    if (Number.isInteger(v)) return numero(v, 0);
    return numero(v, Math.abs(v) >= 10 ? 1 : 3);
  }
  if (typeof v === "boolean") return v ? t("sí", "yes") : "no";
  return v === null || v === undefined ? "—" : String(v);
}
