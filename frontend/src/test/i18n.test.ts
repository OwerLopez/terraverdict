/**
 * Cobertura de traducción: ningún texto visible de la interfaz puede quedar fuera de t("es", "en").
 * Revisa el texto JSX entre etiquetas y los atributos de texto visibles de todos los componentes.
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { idiomaActual, t } from "../lib/i18n";

const RAIZ = join(__dirname, "..");
const ATRIBUTOS = ["titulo", "subtitulo", "descripcion", "etiqueta", "nota", "eyebrow", "pie", "placeholder", "aria-label", "title"];
// Textos técnicos o nombres propios que son iguales en ambos idiomas.
const PERMITIDOS = new Set(["API", "JSON", "CSV", "Diebold-Mariano", "Lyapunov λ", "TerraVerdict", "ES", "EN", "Español", "English", "ENSO", "x(t + τ)"]);

function archivos(dir: string): string[] {
  return readdirSync(dir).flatMap((n) => {
    const ruta = join(dir, n);
    if (statSync(ruta).isDirectory()) return n === "test" ? [] : archivos(ruta);
    return ruta.endsWith(".tsx") ? [ruta] : [];
  });
}

function sinTraducir(original: string): string[] {
  const hallados: string[] = [];
  // Lo que ya está dentro de t("…", "…") o t(`…`, `…`) está traducido: se retira antes de buscar.
  const fuente = original
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/^\s*\/\/.*$/gm, "")
    .replace(/\bt\((?:"(?:[^"\\]|\\.)*"|`[^`]*`)\s*,\s*(?:"(?:[^"\\]|\\.)*"|`[^`]*`)\s*\)/g, "t()");
  // Texto JSX: entre ">" y "<", sin llaves, con al menos dos palabras con letras.
  for (const m of fuente.matchAll(/>\s*([^<>{}]*[A-Za-zÁÉÍÓÚáéíóúñÑ]{2,}[^<>{}]*)\s*</g)) {
    const texto = (m[1] ?? "").trim();
    const esCodigo = /[;(){}[\]=?&|*+]|=>|^[):]|^(tv |POST |GET |new )|et al\./.test(texto);
    if (!esCodigo && texto.split(/\s+/).length >= 2 && !PERMITIDOS.has(texto)) hallados.push(texto);
  }
  for (const a of ATRIBUTOS) {
    for (const m of fuente.matchAll(new RegExp(`\\s${a}="([^"]*[a-záéíóúñ][^"]*)"`, "g"))) {
      const texto = m[1] ?? "";
      if (texto.split(/\s+/).length >= 2 && !PERMITIDOS.has(texto)) hallados.push(`${a}="${texto}"`);
    }
  }
  return hallados;
}

describe("i18n", () => {
  it("t() devuelve el texto del idioma vigente", () => {
    expect(t("Expedientes", "Case files")).toBe(idiomaActual() === "en" ? "Case files" : "Expedientes");
  });

  it("no queda texto visible sin traducir en los componentes", () => {
    const faltan = archivos(RAIZ).flatMap((ruta) => sinTraducir(readFileSync(ruta, "utf-8")).map((s) => `${ruta.replace(RAIZ, "src")}: ${s}`));
    expect(faltan).toEqual([]);
  });
});

describe("formato en inglés", () => {
  it("usa punto decimal, meses en inglés y unidades traducidas", async () => {
    const { fijarIdioma } = await import("../lib/i18n");
    const { numero, fecha, valorP, simboloUnidad, haceCuanto, etiquetaMetrica } = await import("../lib/formato");
    fijarIdioma("en");
    try {
      expect(numero(0.2257, 2, { signo: true })).toBe("+0.23");
      expect(fecha("2025-02-01", "mes")).toBe("Feb 2025");
      expect(fecha("2024-03-13")).toBe("Mar 13, 2024");
      expect(valorP(0)).toBe("< 0.001");
      expect(simboloUnidad("Cel/decada")).toBe("°C/decade");
      expect(etiquetaMetrica("anios_necesarios")).toBe("Years needed");
      expect(haceCuanto(new Date(Date.now() - 5 * 60000).toISOString())).toBe("5 min ago");
    } finally {
      fijarIdioma("es");
    }
  });

  it("el verificador recibe siempre números en formato español", async () => {
    const { fijarIdioma } = await import("../lib/i18n");
    const { numeroEs } = await import("../lib/formato");
    fijarIdioma("en");
    try {
      expect(numeroEs(-0.345, 3)).toBe("−0,345");
    } finally {
      fijarIdioma("es");
    }
  });
});
