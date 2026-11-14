import { describe, expect, it } from "vitest";
import { interpretarProblema } from "../api/cliente";
import { marcasAnio } from "../componentes/graficos/GraficoSerie";
import { colorCelda } from "../componentes/graficos/MapaCalor";
import {
  cifraCitada,
  conUnidad,
  decimalesDe,
  etiquetaMetrica,
  fecha,
  numero,
  simboloUnidad,
  valorMetrica,
  valorP,
} from "../lib/formato";
import { ubicar } from "../lib/grafo";
import { anioDecimal, banda, evaluarRecta, mediana, rectaSen } from "../lib/tendencia";

describe("formato en español", () => {
  it("usa coma decimal y signo menos tipográfico", () => {
    expect(numero(0.2257, 2, { signo: true })).toBe("+0,23");
    expect(numero(-0.345, 3)).toBe("−0,345");
    expect(numero(null)).toBe("—");
  });
  it("traduce unidades del vocabulario", () => {
    expect(conUnidad(373.3, "hm3", 1)).toBe("373,3 hm³");
    expect(conUnidad(60, "%", 0)).toBe("60 %");
    expect(simboloUnidad("Cel/decada")).toBe("°C/década");
  });
  it("respeta la precisión de las fechas", () => {
    expect(fecha("2025-02-01", "mes")).toBe("feb 2025");
    expect(fecha("2023-01-01", "anio")).toBe("2023");
    expect(fecha("2024-03-13")).toBe("13 mar 2024");
  });
  it("no muestra valores p como cero", () => {
    expect(valorP(0)).toBe("< 0,001");
    expect(valorP(0.0568)).toBe("0,057");
  });
});

describe("cifras citadas y métricas", () => {
  it("conserva la precisión con que la fuente escribió el número", () => {
    expect(decimalesDe(404.01)).toBe(2);
    expect(decimalesDe(373.3)).toBe(1);
    expect(decimalesDe(5000)).toBe(0);
    expect(cifraCitada({ valor: 404.01, unidad: "hm3", cota: "exacta" })).toBe("404,01 hm³");
  });
  it("muestra las cotas de la fuente con su signo", () => {
    expect(cifraCitada({ valor: 70, unidad: "%", cota: "minima" })).toBe("> 70 %");
    expect(cifraCitada({ valor: 5, unidad: "hm3", cota: "maxima" })).toBe("< 5 hm³");
    expect(cifraCitada({ valor: 22, unidad: "hm3", cota: "aproximada" })).toBe("≈ 22 hm³");
  });
  it("traduce las claves de métricas y no añade decimales a los enteros", () => {
    expect(etiquetaMetrica("anios_necesarios")).toBe("Años necesarios");
    expect(etiquetaMetrica("clave_nueva")).toBe("clave nueva");
    expect(valorMetrica(300)).toBe("300");
    expect(valorMetrica(-0.345)).toBe("−0,345");
    expect(valorMetrica(16.7971)).toBe("16,8");
  });
  it("marca el eje en años redondos", () => {
    expect(marcasAnio([1981.5, 2024.5])).toEqual([1990, 2000, 2010, 2020]);
    expect(marcasAnio([2001, 2024])).toEqual([2005, 2010, 2015, 2020]);
    expect(marcasAnio([])).toEqual([]);
  });
});

describe("recta de Sen", () => {
  it("usa la pendiente publicada y el intercepto de mediana", () => {
    const puntos = [2000, 2001, 2002, 2003, 2004].map((t, i) => ({ t, y: 10 + 0.5 * i }));
    const r = rectaSen(puntos, 5); // 5 por década = 0,5 por año
    expect(evaluarRecta(r, 2002)).toBeCloseTo(11, 9);
    expect(mediana([3, 1, 2])).toBe(2);
  });
  it("la banda contiene a la recta en el pivote", () => {
    const [lo, hi] = banda({ t: 2000, y: 5 }, 1, 3, 2010);
    expect(lo).toBeCloseTo(6);
    expect(hi).toBeCloseTo(8);
  });
  it("convierte fechas a año decimal", () => {
    expect(anioDecimal("1982-12-01")).toBeCloseTo(1982.9167, 3);
  });
});

describe("grafo del proceso", () => {
  it("ubica los pasos por capas según sus entradas", () => {
    const { nodos, aristas, capas } = ubicar([
      { id: "a", nombre: "A" },
      { id: "b", nombre: "B", entradas: ["paso:a"] },
      { id: "c", nombre: "C", entradas: ["paso:a"] },
      { id: "d", nombre: "D", entradas: ["paso:b", "paso:c"] },
    ]);
    expect(capas).toBe(3);
    expect(aristas).toHaveLength(4);
    expect(nodos.find((n) => n.paso.id === "d")?.capa).toBe(2);
    expect(nodos.find((n) => n.paso.id === "c")?.fila).toBe(1);
  });
});

describe("errores de la API", () => {
  it("interpreta problem+json", () => {
    const e = interpretarProblema(503, { codigo: "servicio_no_disponible", title: "Servicio no disponible", detail: "No conectado" });
    expect(e.status).toBe(503);
    expect(e.codigo).toBe("servicio_no_disponible");
    expect(e.message).toBe("No conectado");
  });
  it("tolera cuerpos que no son problem+json", () => {
    expect(interpretarProblema(500, "texto").codigo).toBe("error_http");
  });
});

describe("mapa de calor", () => {
  it("atenúa las celdas con baja estabilidad", () => {
    expect(colorCelda(0.9, 1).opacidad).toBeGreaterThan(colorCelda(0.9, 0.2).opacidad);
    expect(colorCelda(0.95, 1).texto).toBe("#ffffff");
    expect(colorCelda(0.05, 1).texto).toBe("#0b0b0b");
  });
});
