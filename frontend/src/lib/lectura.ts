/**
 * Lectura en lenguaje claro de las métricas técnicas, sin cambiar su significado matemático.
 *
 * - BSS y habilidad (ECM) frente a la climatología: `1 − error(modelo) / error(climatología)`. Un valor de
 *   0,08 significa exactamente "8 % menos error que la climatología" (el promedio histórico de ese día o mes).
 * - p de Diebold-Mariano: compara las pérdidas del modelo y de la climatología. El umbral preregistrado del
 *   proyecto es 0,10 (config/metricas.yaml); se informa además si cruza el convencional 0,05.
 * - ECE: diferencia media entre la probabilidad pronosticada y la frecuencia observada, en puntos porcentuales.
 */
import { numero } from "./formato";
import { t } from "./i18n";

export type MetricaHabilidad = "bss_climatologia" | "habilidad_climatologia" | "ganancia_informacion_bits" | string;

/** Umbral de p preregistrado (config/metricas.yaml, p_diebold_mariano.valor_referencia). */
export const UMBRAL_P_PREREGISTRADO = 0.1;

export function lecturaHabilidad(valor: number | null | undefined, metrica: MetricaHabilidad): string | null {
  if (valor === null || valor === undefined || !Number.isFinite(valor)) return null;
  if (metrica === "ganancia_informacion_bits") {
    return valor > 0
      ? t(`Aporta ${numero(valor, 3)} bits más que un proceso de Poisson sin memoria`, `Adds ${numero(valor, 3)} bits over a memoryless Poisson process`)
      : t("Sin información adicional frente a un proceso de Poisson", "No extra information over a Poisson process");
  }
  const pct = Math.abs(valor) * 100;
  const error = metrica === "bss_climatologia" ? t("error de Brier", "Brier error") : t("error cuadrático", "squared error");
  if (Math.abs(valor) < 0.005) return t("Igual que la climatología (promedio histórico)", "Same as climatology (historical average)");
  return valor > 0
    ? t(`Habilidad: ${numero(pct, 0)} % menos ${error} que la climatología (promedio histórico)`, `Skill: ${numero(pct, 0)} % less ${error} than climatology (historical average)`)
    : t(`${numero(pct, 0)} % más ${error} que la climatología: no supera al promedio histórico`, `${numero(pct, 0)} % more ${error} than climatology: does not beat the historical average`);
}

export function lecturaP(p: number | null | undefined): string | null {
  if (p === null || p === undefined || !Number.isFinite(p)) return null;
  if (p < 0.05) return t("Diferencia estadísticamente significativa frente a la climatología (p < 0,05)", "Statistically significant difference vs climatology (p < 0.05)");
  if (p < UMBRAL_P_PREREGISTRADO) return t("Indicio de diferencia (p < 0,10, umbral preregistrado; no llega a 0,05)", "Indication of a difference (p < 0.10, preregistered threshold; not below 0.05)");
  return t("Sin diferencia significativa frente a la climatología (p ≥ 0,10)", "No significant difference vs climatology (p ≥ 0.10)");
}

export function lecturaEce(ece: number | null | undefined): string | null {
  if (ece === null || ece === undefined || !Number.isFinite(ece)) return null;
  return t(
    `Las probabilidades se desvían en promedio ${numero(ece * 100, 1)} puntos porcentuales de lo observado`,
    `Forecast probabilities deviate from observed frequencies by ${numero(ece * 100, 1)} percentage points on average`,
  );
}
