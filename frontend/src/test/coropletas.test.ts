import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import type { Esquemas } from "../api/cliente";
import { areasDepartamentos, claveDepartamento } from "../lib/coropletas";

type Departamento = Esquemas["DepartamentoNacional"];

const geo = JSON.parse(readFileSync(resolve(process.cwd(), "public/datos/peru-departamentos.geojson"), "utf-8")) as GeoJSON.FeatureCollection;
const NOMBRES = ["Amazonas", "Áncash", "Apurímac", "Arequipa", "Ayacucho", "Cajamarca", "Callao", "Cusco", "Huancavelica", "Huánuco", "Ica", "Junín", "La Libertad", "Lambayeque", "Lima", "Loreto", "Madre de Dios", "Moquegua", "Pasco", "Piura", "Puno", "San Martín", "Tacna", "Tumbes", "Ucayali"];

const dep = (nombre: string, i: number) =>
  ({ id: nombre, nombre, lat: 0, lon: 0, lluvia_anual_media_mm: 10 * (i + 1), tendencia_temperatura: { sen_por_decada: i / 10 }, tendencia_lluvia: { sen_por_decada: -i } }) as unknown as Departamento;

describe("coropletas nacionales", () => {
  it("normaliza tildes y une Lima Metropolitana con Lima", () => {
    expect(claveDepartamento("Áncash")).toBe("ancash");
    expect(claveDepartamento("San Martín")).toBe("san martin");
    expect(claveDepartamento("Lima Province")).toBe("lima");
  });

  it("cada uno de los 25 departamentos publicados tiene su polígono", () => {
    const claves = new Set(geo.features.map((f) => claveDepartamento(String(f.properties?.nombre))));
    expect(NOMBRES.filter((n) => !claves.has(claveDepartamento(n)))).toEqual([]);
  });

  it("colorea con el valor real del departamento y escala 0–1", () => {
    const deps = NOMBRES.map(dep);
    const areas = areasDepartamentos(geo, deps, "temperatura") ?? [];
    expect(areas).toHaveLength(26); // Lima aparece dos veces (provincia y región) con el mismo valor
    const lima = areas.filter((a) => a.properties?.nombre === "Lima");
    expect(lima).toHaveLength(2);
    expect(lima.every((a) => a.properties?.original === 1.4)).toBe(true);
    const v = areas.map((a) => Number(a.properties?.valor));
    expect(Math.min(...v)).toBe(0);
    expect(Math.max(...v)).toBe(1);
  });
});
