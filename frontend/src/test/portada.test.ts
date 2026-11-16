import { afterEach, describe, expect, it } from "vitest";
import type { Esquemas } from "../api/cliente";
import { mesTexto } from "../componentes/portada/Estado";
import { categoriaEnso } from "../lib/indicadores";
import { fijarIdioma } from "../lib/i18n";
import { lecturaEce, lecturaHabilidad, lecturaP } from "../lib/lectura";
import { LAPSO, imagenDelMes } from "../lib/timelapse";
import { particionar, soloValidados } from "../paginas/RelevanciaPagina";

afterEach(() => fijarIdioma("es"));

describe("lectura en lenguaje claro de las métricas", () => {
  it("BSS 0,08 = 8 % menos error que la climatología (sin cambiar el significado)", () => {
    fijarIdioma("en");
    expect(lecturaHabilidad(0.08, "bss_climatologia")).toBe("Skill: 8 % less Brier error than climatology (historical average)");
    expect(lecturaHabilidad(-0.05, "habilidad_climatologia")).toContain("more squared error");
    expect(lecturaHabilidad(0.001, "bss_climatologia")).toContain("Same as climatology");
    expect(lecturaHabilidad(null, "bss_climatologia")).toBeNull();
  });

  it("p de Diebold-Mariano: 0,05 convencional y 0,10 preregistrado", () => {
    fijarIdioma("en");
    expect(lecturaP(0.04)).toContain("p < 0.05");
    expect(lecturaP(0.07)).toContain("preregistered threshold");
    expect(lecturaP(0.3)).toContain("No significant difference");
  });

  it("ECE en puntos porcentuales", () => {
    fijarIdioma("en");
    expect(lecturaEce(0.0349)).toContain("3.5 percentage points");
  });
});

describe("matriz de relevancia", () => {
  const matriz = {
    estado: "disponible",
    mensaje: "",
    expedientes: [],
    variables: [{ id: "a", nombre: "A" }, { id: "b", nombre: "B" }, { id: "c", nombre: "C" }],
    problemas: [
      { id: "P1", nombre: "Lluvia", objetivo: "", candidatas: ["a", "b"], muestras: "", viabilidad: "alta", dominio_entrenamiento: "" },
      { id: "P2", nombre: "Bofedales", objetivo: "", candidatas: ["c"], muestras: "", viabilidad: "alta", dominio_entrenamiento: "" },
    ],
    celdas: [{ problema_id: "P1", variable_id: "a", importancia: 0.5, estabilidad: 0.9, p_ajustado: 0.01, direccion: "positiva", expediente_id: "TV-REL-1", publicable: true }],
  } as unknown as Esquemas["MatrizRelevancia"];

  it("separa los problemas con resultados de los que esperan datos, sin rellenar celdas", () => {
    const { conResultados, enEspera } = particionar(matriz);
    expect(conResultados.map((p) => p.id)).toEqual(["P1"]);
    expect(enEspera.map((p) => p.id)).toEqual(["P2"]);
    const v = soloValidados(matriz);
    expect(v.problemas.map((p) => p.id)).toEqual(["P1"]);
    expect(v.variables.map((x) => x.id)).toEqual(["a", "b"]);
    expect(v.celdas).toHaveLength(1);
  });
});

describe("portada", () => {
  it("categoría ENSO con los mismos cortes que el cálculo", () => {
    expect(categoriaEnso(2.46)).toBe("nino_fuerte");
    expect(categoriaEnso(1.49)).toBe("nino");
    expect(categoriaEnso(0)).toBe("neutro");
    expect(categoriaEnso(-0.5)).toBe("nina");
  });

  it("formatea meses en ambos idiomas", () => {
    expect(mesTexto("2026-10")).toBe("oct 2026");
    fijarIdioma("en");
    expect(mesTexto("2026-10")).toBe("Oct 2026");
  });

  it("el time-lapse solo tiene imágenes verificadas con su hash, y los meses sin imagen quedan vacíos", () => {
    expect(LAPSO.meses.length).toBeGreaterThan(60);
    for (const m of LAPSO.meses) {
      if (!m.elegida) continue;
      expect(m.elegida.url).toMatch(/^https:\/\/gibs\.earthdata\.nasa\.gov\/wmts\/epsg3857\/best\/HLS_[LS]30_/);
      expect(m.elegida.url).toContain(m.elegida.fecha);
      expect(m.elegida.sha256).toMatch(/^[0-9a-f]{64}$/);
      expect(m.elegida.nubosidad).toBeLessThanOrEqual(LAPSO.criterio.max_nubosidad);
      expect(m.elegida.fecha.startsWith(m.mes)).toBe(true);
    }
    const vacio = LAPSO.meses.find((m) => !m.elegida);
    if (vacio) expect(imagenDelMes(vacio.mes)).toBeNull();
  });
});
