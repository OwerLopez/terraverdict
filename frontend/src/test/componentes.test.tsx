import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { Esquemas } from "../api/cliente";
import { BarraEstados, LineaTiempo } from "../componentes/graficos/Evidencia";
import { MapaCalor } from "../componentes/graficos/MapaCalor";
import { ChipEstado, VEREDICTOS } from "../componentes/ui";

const MATRIZ_VACIA: Esquemas["MatrizRelevancia"] = {
  estado: "vacia",
  mensaje: "Todavía no hay resultados de relevancia publicados por el pipeline.",
  problemas: [
    { id: "P1", nombre: "Lluvia extrema", objetivo: "Días ≥ p99", candidatas: ["indice_oni"], muestras: "~10 000", viabilidad: "alta", dominio_entrenamiento: "andes_sur_entrenamiento" },
  ],
  variables: [
    { id: "indice_oni", nombre: "Índice ONI", simbolo: "ONI", unidad: "Cel", grupo: "atmosfera", descripcion: "", relacion: null },
    { id: "ndvi", nombre: "NDVI", simbolo: "NDVI", unidad: "1", grupo: "superficie", descripcion: "", relacion: null },
  ],
  celdas: [],
  expedientes: [],
};

describe("componentes", () => {
  it("la matriz vacía no inventa valores y lo explica", () => {
    render(<MapaCalor matriz={MATRIZ_VACIA} />);
    expect(screen.getByText("Todavía no hay resultados de relevancia")).toBeInTheDocument();
    expect(screen.getByTitle("Índice ONI: candidata de P1, sin resultado publicado")).toBeInTheDocument();
    expect(screen.queryAllByRole("button")).toHaveLength(0);
  });

  it("los estados llevan texto además de color", () => {
    render(<ChipEstado mapa={VEREDICTOS} valor="preliminar" />);
    expect(screen.getByText("Preliminar")).toBeInTheDocument();
  });

  it("la barra de estados muestra conteos con etiqueta", () => {
    render(<BarraEstados conteos={{ verificado: 28, parcial: 2, sin_evidencia: 4 }} />);
    expect(screen.getByText("Verificado")).toBeInTheDocument();
    expect(screen.getByText("28")).toBeInTheDocument();
  });

  it("la crónica cita la fuente de cada evento", () => {
    render(
      <LineaTiempo
        eventos={[
          {
            id: "e1",
            fecha: "2025-02-01",
            precision: "mes",
            categoria: "turbidez",
            titulo: "Turbidez en la captación",
            descripcion: "Descripción",
            cifras: [
              { valor: 5000, unidad: "NTU", descripcion: "Turbidez", cota: "exacta" },
              { valor: 70, unidad: "%", descripcion: "Población afectada", cota: "minima" },
            ],
            fuentes: [{ titulo: "Nota", url: "https://example.org/nota", medio: "Medio" }],
          },
        ]}
      />,
    );
    expect(screen.getByText("feb 2025")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Medio: Nota/ })).toHaveAttribute("href", "https://example.org/nota");
    // Una cota de la fuente ("más del 70 %") no se muestra como valor exacto.
    expect(screen.getByText("> 70 %")).toBeInTheDocument();
    expect(screen.getByText(/5\s?000 NTU/)).toBeInTheDocument();
  });
});
