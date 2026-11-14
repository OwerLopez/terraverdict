import type { Expediente } from "../types";
const TITULO: Record<string, string> = { robusta: "Robusta", fragil: "Frágil", no_decidible: "No decidible", sin_tendencia: "Sin tendencia detectable" };
export default function SelloCard({ e }: { e: Expediente }) {
  const s = e.resultado.sello;
  return (
    <section style={{ border: "2px solid #888", borderRadius: 12, padding: 16 }}>
      <h2 style={{ margin: 0 }}>{s.emoji} {TITULO[s.codigo]}</h2>
      {s.fallan.length > 0 && <p><b>Falla:</b> {s.fallan.join(", ")}</p>}
      {s.pendientes.length > 0 && <p><b>Sin evaluar:</b> {s.pendientes.join(", ")}</p>}
      {s.nota && <p>{s.nota}</p>}
    </section>
  );
}
