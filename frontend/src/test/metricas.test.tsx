import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MatrizCalor } from "../componentes/graficos/MatrizCalor";
import { RAMPA_AZUL, RAMPA_NARANJA, colorDivergente, colorSecuencial } from "../lib/colores";
import { evidencia, nombreModelo, nombreVariable } from "../lib/modelos";
import { FichaMetrica } from "../componentes/metricas/compartidos";

describe("escalas de los mapas de calor", () => {
  it("la escala divergente usa azul para mejor, naranja para peor y neutro en el centro", () => {
    expect(RAMPA_AZUL).toContain(colorDivergente(0.4, 0.5).fondo);
    expect(RAMPA_NARANJA).toContain(colorDivergente(-0.4, 0.5).fondo);
    expect(colorDivergente(0.001, 0.5).fondo).toBe("var(--neutral-mid)");
    // Para un p-valor, menor es mejor: p = 0,01 frente a un umbral de 0,10 va al lado azul
    expect(RAMPA_AZUL).toContain(colorDivergente(0.01, 0.5, 0.1, false).fondo);
    expect(RAMPA_NARANJA).toContain(colorDivergente(0.6, 0.5, 0.1, false).fondo);
  });

  it("los pasos oscuros llevan texto claro para mantener el contraste", () => {
    expect(colorSecuencial(0.05).texto).toBe("#0b0b0b");
    expect(colorSecuencial(0.99).texto).toBe("#ffffff");
    expect(colorSecuencial(0.99).fondo).toBe(RAMPA_AZUL[RAMPA_AZUL.length - 1]);
  });
});

describe("mapa de calor accesible", () => {
  const filas = [{ id: "gru", etiqueta: "GRU" }, { id: "tcn", etiqueta: "TCN" }];
  const columnas = [{ id: "2021", etiqueta: "2021", grupo: "Fuera de muestra" }, { id: "2022", etiqueta: "2022", grupo: "Fuera de muestra" }];

  it("es una tabla con encabezados, valores escritos y detalle al enfocar", () => {
    render(
      <MatrizCalor
        titulo="Habilidad por año"
        etiquetaFilas="Modelo"
        filas={filas}
        columnas={columnas}
        celda={(f, c) =>
          c.id === "2022" && f.id === "tcn"
            ? { texto: "—", detalle: "TCN 2022: no evaluado", omitida: "pocos datos" }
            : { texto: f.id === "gru" ? "0,12" : "-0,05", detalle: `${f.etiqueta} ${c.etiqueta}: detalle`, marcada: f.id === "gru" }
        }
      />,
    );
    const tabla = screen.getByRole("table", { name: "Habilidad por año" });
    expect(within(tabla).getAllByRole("rowheader").map((h) => h.textContent)).toEqual(["GRU", "TCN"]);
    expect(within(tabla).getByRole("columnheader", { name: "Fuera de muestra" })).toHaveAttribute("colspan", "2");
    expect(within(tabla).getAllByText("0,12")).toHaveLength(2); // el valor se lee, no solo el color
    const omitida = screen.getByRole("button", { name: "TCN 2022: no evaluado" });
    expect(omitida).toHaveAttribute("title", "pocos datos");
    fireEvent.focus(screen.getAllByRole("button", { name: "GRU 2021: detalle" })[0] as HTMLElement);
    expect(screen.getByText("GRU 2021: detalle", { selector: "p" })).toBeInTheDocument();
  });
});

describe("fichas y nombres", () => {
  it("la ficha explica qué mide y cómo leer la métrica", () => {
    render(
      <FichaMetrica
        ficha={{
          id: "bss_climatologia",
          grupo: "pronostico",
          nombre: { es: "Habilidad de Brier frente a la climatología", en: "Brier skill vs climatology" },
          formula: "BSS = 1 − Brier(modelo) / Brier(climatología)",
          que_mide: { es: "Cuánto mejora la probabilidad.", en: "How much probability improves." },
          como_leer: { es: "0 = igual que la climatología.", en: "0 = same as climatology." },
          mejor: "mayor",
          valor_referencia: 0,
          cita: "Wilks (2011)",
        }}
      />,
    );
    expect(screen.getByRole("heading", { name: "Habilidad de Brier frente a la climatología" })).toBeInTheDocument();
    expect(screen.getByText("Mejor si es mayor")).toBeInTheDocument();
    expect(screen.getByText("0 = igual que la climatología.")).toBeInTheDocument();
    expect(screen.getByText(/Wilks \(2011\)/)).toBeInTheDocument();
  });

  it("la regla de evidencia exige IC90 > 0 y p < 0,10 para confirmar", () => {
    expect(evidencia(0.01, 0.05)).toBe("confirmada");
    expect(evidencia(0.01, 0.4)).toBe("indicio");
    expect(evidencia(-0.2, 0.05)).toBe("indicio");
    expect(evidencia(-0.2, 0.4)).toBe("no_confirmada");
    expect(evidencia(null, null)).toBe("no_confirmada");
  });

  it("los modelos y variables se nombran como en la literatura", () => {
    expect(nombreModelo("nbeats")).toBe("N-BEATS");
    expect(nombreModelo("tcn")).toBe("TCN (convolucional)");
    expect(nombreModelo("modelo_nuevo")).toBe("modelo nuevo");
    expect(nombreVariable("humedad_especifica")).toBe("Humedad específica");
  });
});
