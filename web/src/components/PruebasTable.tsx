import type { Expediente } from "../types";
const icono = (ok: boolean | null) => (ok === null ? "⏳" : ok ? "✅" : "❌");
export default function PruebasTable({ e }: { e: Expediente }) {
  const r = e.resultado, s = r.sello;
  const estado = (k: string) => (s.pendientes.includes(k) ? null : !s.fallan.includes(k));
  const filas: [string, string, string][] = [
    ["Tendencia (p conservador)", icono(r.mk.p_conservador <= 0.1), `${r.mk.p_conservador.toPrecision(3)} (${r.mk.variante_limitante})`],
    ["Ventanas", icono(estado("ventanas")), r.ventanas?.pct_mismo_signo != null ? `${r.ventanas.pct_mismo_signo.toFixed(0)} % mismo signo` : "—"],
    ["ENSO (HAC)", icono(estado("enso")), r.enso?.evaluada ? "evaluada" : "falta ONI"],
    ["Sensor", icono(estado("sensor")), "por producto"],
    ["Palanca de los últimos años", icono(estado("palanca")), r.palanca?.evaluada ? `Sen sin últimos ${r.palanca.quitados}: ${r.palanca.sen_por_decada?.toFixed(3)}` : "—"],
    ["Independencia", icono(estado("independencia")), r.independencia ? `${r.independencia.n_familias_mismo_signo} familias` : "pendiente"],
    ["Detectabilidad", "ℹ️", `${r.detectabilidad.anios_necesarios?.toFixed(1) ?? "—"} años necesarios / ${r.detectabilidad.anios_disponibles}`],
  ];
  return (
    <table style={{ borderCollapse: "collapse", width: "100%" }}>
      <tbody>{filas.map(([n, i, d]) => (<tr key={n}><td style={{ padding: 4 }}>{n}</td><td>{i}</td><td>{d}</td></tr>))}</tbody>
    </table>
  );
}
