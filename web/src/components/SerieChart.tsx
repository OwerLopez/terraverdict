// Serie + recta de Sen. Los años vienen del periodo; los valores, del expediente (ver nota en App).
import type { Expediente } from "../types";
export default function SerieChart({ e, valores }: { e: Expediente; valores: number[] }) {
  const W = 640, H = 260, m = 36, [a0, a1] = e.resultado.periodo;
  const ys = valores, lo = Math.min(...ys), hi = Math.max(...ys);
  const X = (a: number) => m + ((a - a0) / (a1 - a0)) * (W - 2 * m);
  const Y = (v: number) => H - m - ((v - lo) / (hi - lo || 1)) * (H - 2 * m);
  const { pendiente, ordenada } = e.resultado.sen;
  const pts = ys.map((v, i) => `${X(a0 + i)},${Y(v)}`).join(" ");
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Serie anual con pendiente de Theil-Sen">
      <polyline points={pts} fill="none" stroke="#3b6ea5" strokeWidth={2} />
      <line x1={X(a0)} y1={Y(ordenada + pendiente * a0)} x2={X(a1)} y2={Y(ordenada + pendiente * a1)} stroke="#c0392b" strokeDasharray="6 4" />
      <text x={m} y={14} fontSize={12}>{a0}–{a1} · Sen {e.resultado.sen.sen_por_decada.toFixed(3)} / década</text>
    </svg>
  );
}
