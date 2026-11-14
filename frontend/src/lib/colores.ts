import { useMemo } from "react";
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
export const RAMPA_AZUL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"];

/** Orden categórico fijo (nunca cíclico) para las categorías de eventos. */
export const CATEGORIAS_EVENTO: Record<string, { color: string; texto: string }> = {
  escasez: { color: "var(--serie-2)", texto: "Escasez" },
  turbidez: { color: "var(--serie-1)", texto: "Turbidez" },
  colmatacion: { color: "var(--serie-4)", texto: "Colmatación" },
  almacenamiento: { color: "var(--serie-3)", texto: "Almacenamiento" },
  degradacion: { color: "var(--serie-5)", texto: "Degradación" },
  clima: { color: "var(--serie-8)", texto: "Clima" },
  institucional: { color: "var(--serie-7)", texto: "Institucional" },
};
