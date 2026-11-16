import { afterEach, describe, expect, it } from "vitest";
import { fijarIdioma } from "../lib/i18n";
import { traducirTitulo } from "../lib/titulos";

describe("títulos de expedientes", () => {
  afterEach(() => fijarIdioma("es"));

  it("se traducen al inglés conservando la fuente entre paréntesis", () => {
    fijarIdioma("en");
    expect(traducirTitulo("Sequía: SPI-3 a 3 mes(es) en la cabecera del Chili (CHIRPS)")).toBe(
      "Drought: SPI-3 3 month(s) ahead in the Chili headwaters (CHIRPS)",
    );
    expect(traducirTitulo("Sismicidad a 350 km de Arequipa (USGS)")).toBe("Seismicity within 350 km of Arequipa (USGS)");
    expect(traducirTitulo("Título desconocido")).toBe("Título desconocido");
  });

  it("en español quedan tal cual", () => {
    expect(traducirTitulo("Sismicidad a 350 km de Arequipa (USGS)")).toBe("Sismicidad a 350 km de Arequipa (USGS)");
  });
});

describe("traducción de los datos de la API", () => {
  it("traduce solo coincidencias exactas del glosario y no toca números ni identificadores", async () => {
    const { traducirDatos } = await import("../api/cliente");
    const datos = { id: "volumen_util", nombre: "Volumen almacenado", valor: 159, notas: ["texto sin traducción"], estado: "confirmada" };
    expect(traducirDatos(datos)).toEqual({ id: "volumen_util", nombre: "Stored volume", valor: 159, notas: ["texto sin traducción"], estado: "confirmada" });
  });
});
