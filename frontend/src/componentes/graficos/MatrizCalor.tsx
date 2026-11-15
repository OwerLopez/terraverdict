import { clsx } from "clsx";
import { type ReactNode, useState } from "react";
import type { ColorCelda } from "../../lib/colores";
import { t } from "../../lib/i18n";

export type FilaMatriz = { id: string; etiqueta: string; sub?: string };
export type ColumnaMatriz = { id: string; etiqueta: string; sub?: string; grupo?: string };
export type CeldaMatriz = {
  /** Texto visible en la celda: el valor nunca se comunica solo con color. */
  texto: string;
  color?: ColorCelda;
  /** Descripción completa para lectores de pantalla y el panel de detalle. */
  detalle: string;
  /** Resalta la celda (p. ej., el modelo elegido en validación). */
  marcada?: boolean;
  /** Motivo por el que no hay valor; la celda se dibuja rayada. */
  omitida?: string;
};

/**
 * Mapa de calor accesible como tabla: encabezados de fila y columna, valor escrito en cada celda,
 * foco por teclado con detalle anunciado y celdas sin dato rayadas con su motivo.
 */
export function MatrizCalor({
  titulo,
  etiquetaFilas,
  filas,
  columnas,
  celda,
  leyenda,
  anchoFila = 200,
}: {
  titulo: string;
  etiquetaFilas: string;
  filas: FilaMatriz[];
  columnas: ColumnaMatriz[];
  celda: (fila: FilaMatriz, columna: ColumnaMatriz) => CeldaMatriz | undefined;
  leyenda?: ReactNode;
  anchoFila?: number;
}) {
  const [activa, setActiva] = useState<string | null>(null);
  const grupos = columnas.reduce<{ grupo: string; n: number }[]>((acc, c) => {
    const g = c.grupo ?? "";
    const ultimo = acc[acc.length - 1];
    if (ultimo && ultimo.grupo === g) ultimo.n += 1;
    else acc.push({ grupo: g, n: 1 });
    return acc;
  }, []);
  const hayGrupos = grupos.some((g) => g.grupo);

  return (
    <div className="space-y-3">
      {/* relative: contiene los textos sr-only (posición absoluta) dentro del scroll, sin ensanchar la página */}
      <div className="relative overflow-x-auto rounded-xl border border-line">
        <table className="w-full border-separate border-spacing-[2px] text-[12px]">
          <caption className="sr-only">{titulo}</caption>
          <thead>
            {hayGrupos && (
              <tr>
                <td className="sticky left-0 z-10 bg-surface" />
                {grupos.map((g, i) => (
                  <th key={`${g.grupo}-${i}`} colSpan={g.n} scope="colgroup" className="border-b border-line px-1 pb-1 text-center text-[11px] font-medium text-ink-3">
                    {g.grupo}
                  </th>
                ))}
              </tr>
            )}
            <tr>
              <th scope="col" className="sticky left-0 z-10 bg-surface px-3 py-2 text-left align-bottom font-medium text-ink-2" style={{ minWidth: anchoFila }}>
                {etiquetaFilas}
              </th>
              {columnas.map((c) => (
                <th key={c.id} scope="col" className="min-w-[58px] px-1 pb-1 align-bottom text-center font-medium leading-tight text-ink-2">
                  <span className="block">{c.etiqueta}</span>
                  {c.sub && <span className="block text-[10.5px] font-normal text-ink-3">{c.sub}</span>}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filas.map((f) => (
              <tr key={f.id}>
                <th scope="row" className="sticky left-0 z-10 bg-surface px-3 py-1.5 text-left font-normal" style={{ minWidth: anchoFila }}>
                  <span className="font-medium text-ink">{f.etiqueta}</span>
                  {f.sub && <span className="block text-[11px] text-ink-3">{f.sub}</span>}
                </th>
                {columnas.map((c) => {
                  const d = celda(f, c);
                  const clave = `${f.id}|${c.id}`;
                  if (!d) {
                    return (
                      <td key={c.id} className="p-0">
                        <div className="grid h-9 place-items-center rounded-md bg-surface-2 text-ink-3" title={t("Sin dato", "No data")}>
                          <span aria-hidden>·</span>
                          <span className="sr-only">{t("Sin dato", "No data")}</span>
                        </div>
                      </td>
                    );
                  }
                  if (d.omitida) {
                    return (
                      <td key={c.id} className="p-0">
                        <button
                          type="button"
                          onMouseEnter={() => setActiva(`${d.detalle}`)}
                          onFocus={() => setActiva(`${d.detalle}`)}
                          className="rayado grid h-9 w-full place-items-center rounded-md border border-dashed border-line-strong text-[11px] text-ink-3"
                          aria-label={d.detalle}
                          title={d.omitida}
                        >
                          —
                        </button>
                      </td>
                    );
                  }
                  return (
                    <td key={c.id} className="p-0">
                      <button
                        type="button"
                        onMouseEnter={() => setActiva(d.detalle)}
                        onFocus={() => setActiva(d.detalle)}
                        aria-label={d.detalle}
                        data-celda={clave}
                        className={clsx(
                          "grid h-9 w-full place-items-center rounded-md px-1 font-mono text-[11.5px] tabular-nums transition-transform hover:scale-[1.04] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1",
                          d.marcada && "ring-2 ring-[var(--ink)] ring-offset-1 ring-offset-[var(--surface)]",
                        )}
                        style={{ background: d.color?.fondo ?? "var(--surface-2)", color: d.color?.texto ?? "var(--ink)" }}
                      >
                        {d.texto}
                      </button>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p aria-live="polite" className="min-h-[2.5em] rounded-lg bg-surface-2 px-3 py-2 text-[12.5px] leading-snug text-ink-2">
        {activa ?? t("Pase el cursor o enfoque una celda para ver su detalle.", "Hover or focus a cell to see its details.")}
      </p>
      {leyenda}
    </div>
  );
}

/** Leyenda de una escala: la rampa de colores con sus extremos rotulados. */
export function LeyendaEscala({ colores, izquierda, centro, derecha, nota }: { colores: string[]; izquierda: string; centro?: string; derecha: string; nota?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11.5px] text-ink-3">
      <div className="flex flex-wrap items-center gap-2">
        <span>{izquierda}</span>
        <span className="flex overflow-hidden rounded" aria-hidden>
          {colores.map((c, i) => (
            <span key={`${c}-${i}`} className="h-3 w-5" style={{ background: c }} />
          ))}
        </span>
        <span>{derecha}</span>
      </div>
      {centro && <span>{centro}</span>}
      {nota && <span className="basis-full">{nota}</span>}
    </div>
  );
}
