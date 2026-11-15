import { useMemo } from "react";
import { t } from "./i18n";
import { colorToken, useTema } from "./tema";

/** Colores resueltos del tema actual para librerías que dibujan en SVG/Canvas (Recharts, MapLibre). */
export function useColores() {
  const { oscuro } = useTema();
  return useMemo(() => {
    void oscuro; // recalcula al cambiar de tema
    const t = (n: string, respaldo: string) => colorToken(n) || respaldo;
    return {
      superficie: t("--surface", "#fcfcfb"),
      tinta: t("--ink", "#0b0b0b"),
      tinta2: t("--ink-2", "#52514e"),
      tinta3: t("--ink-3", "#898781"),
      rejilla: t("--grid", "#e1e0d9"),
      eje: t("--axis", "#c3c2b7"),
      serie1: t("--serie-1", "#2a78d6"),
      serie2: t("--serie-2", "#eb6834"),
      banda: t("--banda", "rgba(42,120,214,0.14)"),
      neutro: t("--neutral-mid", "#f0efec"),
    };
  }, [oscuro]);
}

/** Rampa secuencial azul (100 → 700), validada en la guía de visualización. */
export const RAMPA_AZUL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"] as const;

/** Orden categórico fijo (nunca cíclico) para las categorías de eventos. */
function categoria(color: string, es: string, en: string): { color: string; readonly texto: string } {
  return {
    color,
    get texto() {
      return t(es, en);
    },
  };
}

export const CATEGORIAS_EVENTO: Record<string, { color: string; readonly texto: string }> = {
  escasez: categoria("var(--serie-2)", "Escasez", "Scarcity"),
  turbidez: categoria("var(--serie-1)", "Turbidez", "Turbidity"),
  colmatacion: categoria("var(--serie-4)", "Colmatación", "Siltation"),
  almacenamiento: categoria("var(--serie-3)", "Almacenamiento", "Storage"),
  degradacion: categoria("var(--serie-5)", "Degradación", "Degradation"),
  clima: categoria("var(--serie-8)", "Clima", "Climate"),
  institucional: categoria("var(--serie-7)", "Institucional", "Institutional"),
};
