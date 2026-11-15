import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AvisoNoOficial } from "../componentes/Marco";
import { TablaDatos } from "../componentes/fenomenos/TablaDatos";
import { VEREDICTOS_DINAMICA } from "../paginas/CaosPagina";

describe("fenómenos naturales", () => {
  it("el aviso permanente dice que no son alertas oficiales y nombra a las instituciones", () => {
    render(<AvisoNoOficial />);
    const aviso = screen.getByRole("note");
    expect(aviso).toHaveTextContent("Resultados experimentales. No son alertas oficiales");
    for (const institucion of ["SENAMHI", "IGP", "INGEMMET", "INDECI"]) expect(aviso).toHaveTextContent(institucion);
  });

  it("cada gráfico tiene su tabla de datos accesible", () => {
    render(<TablaDatos titulo="Sismos por año" columnas={["Año", "Sismos"]} filas={[["2001", 120], ["2002", 98]]} />);
    expect(screen.getByText("Ver datos en tabla (2 filas)")).toBeInTheDocument();
    const tabla = screen.getByRole("table", { name: "Sismos por año" });
    expect(tabla).toBeInTheDocument();
    expect(screen.getAllByRole("columnheader").map((c) => c.textContent)).toEqual(["Año", "Sismos"]);
    expect(screen.getByText("98")).toBeInTheDocument();
  });

  it("la tabla avisa cuando recorta filas", () => {
    render(<TablaDatos titulo="Puntos" columnas={["x"]} filas={[[1], [2], [3]]} maxFilas={2} />);
    expect(screen.getByText("Se muestran 2 de 3 filas.")).toBeInTheDocument();
  });

  it("todos los veredictos de dinámica tienen texto, no solo color", () => {
    for (const v of ["lineal_estocastica", "no_lineal_sin_caos_demostrado", "compatible_con_caos_baja_dimension", "regular", "insuficiente"]) {
      expect(VEREDICTOS_DINAMICA[v]?.texto.length).toBeGreaterThan(3);
    }
  });
});
