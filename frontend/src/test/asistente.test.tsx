import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import type { Esquemas } from "../api/cliente";
import { SelloRespuesta, TextoConCitas } from "../componentes/RespuestaAsistente";

const ID = "TV-CMP-C7137FFC877E";

const respuesta = (aprobado: boolean): Esquemas["RespuestaAsistenteSalida"] => ({
  texto: `La habilidad es 0,576 [${ID}].`,
  expedientes_citados: [ID],
  expedientes_consultados: [{ id: ID, tipo: "comparacion_modelos", titulo: "Sequía: SPI-3 a 1 mes" }],
  verificacion: {
    aprobado,
    cifras: [{ texto: "0,576", valor: 0.576, trazable: aprobado, coincide_con: aprobado ? 0.576 : null, probabilidad_azar: null }],
    no_trazables: aprobado ? [] : ["0,576"],
    valores_permitidos: 120,
    alfa_coincidencia: 0.05,
    coincidencias_debiles: [],
  },
  modelo: "gemini-flash-latest",
  intentos: 1,
  latencia_s: 2.2,
});

describe("asistente", () => {
  it("convierte cada cita en un enlace al expediente", () => {
    render(<MemoryRouter><TextoConCitas texto={`Dato 0,576 [${ID}] y otro [${ID}, TV-SIS-33D497675B71].`} /></MemoryRouter>);
    const enlaces = screen.getAllByRole("link");
    expect(enlaces).toHaveLength(3);
    expect(enlaces[0]).toHaveAttribute("href", `/expedientes/${ID}`);
    expect(enlaces[2]).toHaveAttribute("href", "/expedientes/TV-SIS-33D497675B71");
  });

  it("muestra el sello de verificación y no oculta una cifra sin respaldo", () => {
    const { rerender } = render(<MemoryRouter><SelloRespuesta r={respuesta(true)} /></MemoryRouter>);
    expect(screen.getByText(/1\/1/)).toBeInTheDocument();
    expect(screen.getByText(/gemini-flash-latest/)).toBeInTheDocument();
    rerender(<MemoryRouter><SelloRespuesta r={respuesta(false)} /></MemoryRouter>);
    expect(screen.getAllByText(/Sin respaldo: 0,576|Unbacked: 0,576/).length).toBeGreaterThan(0);
  });
});
