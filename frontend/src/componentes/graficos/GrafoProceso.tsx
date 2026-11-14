import { clsx } from "clsx";
import { useMemo, useState } from "react";
import type { Esquemas } from "../../api/cliente";
import { etiquetaMetrica, valorMetrica } from "../../lib/formato";
import { ubicar } from "../../lib/grafo";

type Paso = Esquemas["Paso"];

const ANCHO = 178;
const ALTO = 58;
const SEP_X = 56;
const SEP_Y = 18;

/** "Cómo llegué a esto": los pasos reales que produjeron el resultado, encendidos en orden. */
export function GrafoProceso({ pasos }: { pasos: Paso[] }) {
  const { nodos, aristas, capas } = useMemo(() => ubicar(pasos), [pasos]);
  const [seleccion, setSeleccion] = useState<string | null>(pasos.at(-1)?.id ?? null);

  const filasPorCapa = new Map<number, number>();
  nodos.forEach((n) => filasPorCapa.set(n.capa, Math.max(filasPorCapa.get(n.capa) ?? 0, n.fila + 1)));
  const maxFilas = Math.max(1, ...filasPorCapa.values());
  const alto = maxFilas * ALTO + (maxFilas - 1) * SEP_Y;
  const ancho = capas * ANCHO + (capas - 1) * SEP_X;

  const posicion = new Map(
    nodos.map((n) => {
      const filas = filasPorCapa.get(n.capa) ?? 1;
      const desplazamiento = (alto - (filas * ALTO + (filas - 1) * SEP_Y)) / 2;
      return [n.paso.id, { x: n.capa * (ANCHO + SEP_X), y: desplazamiento + n.fila * (ALTO + SEP_Y) }];
    }),
  );
  const pasoActivo = pasos.find((p) => p.id === seleccion);

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto pb-2">
        <div className="relative" style={{ width: ancho, height: alto }}>
          <svg className="absolute inset-0" width={ancho} height={alto} aria-hidden>
            {aristas.map((a) => {
              const d = posicion.get(a.desde);
              const h = posicion.get(a.hasta);
              if (!d || !h) return null;
              const x1 = d.x + ANCHO;
              const y1 = d.y + ALTO / 2;
              const x2 = h.x;
              const y2 = h.y + ALTO / 2;
              const resaltada = seleccion === a.hasta || seleccion === a.desde;
              return (
                <path
                  key={`${a.desde}-${a.hasta}`}
                  d={`M${x1},${y1} C${x1 + SEP_X / 2},${y1} ${x2 - SEP_X / 2},${y2} ${x2},${y2}`}
                  fill="none"
                  stroke={resaltada ? "var(--accent)" : "var(--axis)"}
                  strokeWidth={resaltada ? 2 : 1.5}
                />
              );
            })}
          </svg>
          {nodos.map((n) => {
            const p = posicion.get(n.paso.id);
            if (!p) return null;
            const activo = seleccion === n.paso.id;
            return (
              <button
                key={n.paso.id}
                type="button"
                onClick={() => setSeleccion(n.paso.id)}
                className={clsx(
                  "absolute flex flex-col justify-center rounded-xl border px-3 text-left transition-all animate-aparecer",
                  activo ? "border-accent bg-accent-soft shadow-flotante" : "border-line bg-surface hover:border-line-strong",
                )}
                style={{ left: p.x, top: p.y, width: ANCHO, height: ALTO, animationDelay: `${n.capa * 110}ms` }}
                aria-pressed={activo}
              >
                <span className="font-mono text-[10.5px] text-ink-3">{String(nodos.indexOf(n) + 1).padStart(2, "0")} · {n.paso.id}</span>
                <span className="line-clamp-2 text-[12.5px] font-medium leading-snug text-ink">{n.paso.nombre}</span>
              </button>
            );
          })}
        </div>
      </div>
      {pasoActivo && (
        <div className="rounded-xl border border-line bg-surface-2 p-4 text-[13px]" aria-live="polite">
          <p className="font-semibold text-ink">{pasoActivo.nombre}</p>
          {pasoActivo.descripcion && <p className="mt-1 text-ink-2">{pasoActivo.descripcion}</p>}
          {pasoActivo.metricas && Object.keys(pasoActivo.metricas).length > 0 ? (
            <dl className="mt-3 grid grid-cols-2 gap-x-6 gap-y-1.5 sm:grid-cols-3">
              {Object.entries(pasoActivo.metricas).map(([k, v]) => (
                <div key={k} className="min-w-0">
                  <dt className="truncate text-[11.5px] text-ink-3">{etiquetaMetrica(k)}</dt>
                  <dd className="cifra font-medium text-ink">{valorMetrica(v)}</dd>
                </div>
              ))}
            </dl>
          ) : (
            <p className="mt-2 text-ink-3">Este paso no registró métricas.</p>
          )}
        </div>
      )}
    </div>
  );
}
