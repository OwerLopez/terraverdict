import type { Esquemas } from "../api/cliente";

type Departamento = Esquemas["DepartamentoNacional"];
export type Metrica = "temperatura" | "lluvia" | "tendencia_lluvia";

/** Valor mostrado (unidades reales) y valor de color (escala log para la lluvia media, muy asimétrica). */
export function valores(d: Departamento, metrica: Metrica): { real: number; color: number } {
  if (metrica === "temperatura") return { real: d.tendencia_temperatura.sen_por_decada, color: d.tendencia_temperatura.sen_por_decada };
  if (metrica === "lluvia") return { real: d.lluvia_anual_media_mm, color: Math.log10(1 + d.lluvia_anual_media_mm) };
  return { real: d.tendencia_lluvia.sen_por_decada, color: d.tendencia_lluvia.sen_por_decada };
}

export function escala(deps: Departamento[], metrica: Metrica) {
  const vals = deps.map((d) => valores(d, metrica).color);
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  return (v: number) => (max > min ? (v - min) / (max - min) : 0.5);
}

/** Clave de unión: minúsculas sin tildes. Natural Earth separa "Lima Province" (Lima Metropolitana) de "Lima". */
export function claveDepartamento(nombre: string): string {
  const c = nombre.normalize("NFKD").replace(/\p{M}/gu, "").toLowerCase().trim();
  return c === "lima province" ? "lima" : c;
}

/** Polígonos de departamentos con el valor de la celda POWER de su capital (no un promedio areal). */
export function areasDepartamentos(geo: GeoJSON.FeatureCollection | undefined, deps: Departamento[], metrica: Metrica): GeoJSON.Feature[] | undefined {
  if (!geo || !deps.length) return undefined;
  const norm = escala(deps, metrica);
  const porClave = new Map(deps.map((d) => [claveDepartamento(d.nombre), d]));
  return geo.features.flatMap((f) => {
    const d = porClave.get(claveDepartamento(String(f.properties?.nombre ?? "")));
    if (!d) return [];
    const v = valores(d, metrica);
    return [{ ...f, properties: { nombre: d.nombre, valor: norm(v.color), original: v.real } }];
  });
}
