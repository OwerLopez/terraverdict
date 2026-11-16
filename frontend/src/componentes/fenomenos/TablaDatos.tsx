import { Download, Table2 } from "lucide-react";
import { isValidElement, useState, type ReactNode } from "react";
import { t } from "../../lib/i18n";
import { PanelLateral } from "../PanelLateral";

/** Texto plano de una celda para el CSV (los nodos de React se exportan por su contenido textual). */
function textoCelda(c: ReactNode): string {
  if (c === null || c === undefined || typeof c === "boolean") return "";
  if (typeof c === "string" || typeof c === "number") return String(c);
  if (Array.isArray(c)) return c.map(textoCelda).join("");
  if (isValidElement<{ children?: ReactNode }>(c)) return textoCelda(c.props.children);
  return "";
}

function csv(columnas: string[], filas: ReactNode[][]): string {
  const celda = (v: string) => (/[",\n;]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v);
  return [columnas, ...filas.map((f) => f.map(textoCelda))].map((f) => f.map(celda).join(",")).join("\n");
}

/**
 * Datos de un gráfico en un panel flotante lateral: se consultan sin abandonar la vista ni desplazar
 * la página, y se descargan en CSV. Son exactamente los mismos datos que dibuja el gráfico.
 */
export function TablaDatos({
  titulo,
  columnas,
  filas,
  maxFilas = 500,
}: {
  titulo: string;
  columnas: string[];
  filas: ReactNode[][];
  maxFilas?: number;
}) {
  const [abierto, setAbierto] = useState(false);
  const visibles = filas.slice(0, maxFilas);
  const descargar = () => {
    const url = URL.createObjectURL(new Blob([csv(columnas, filas)], { type: "text/csv;charset=utf-8" }));
    const a = Object.assign(document.createElement("a"), { href: url, download: `${titulo.replace(/[^\p{L}\p{N}]+/gu, "_")}.csv` });
    a.click();
    URL.revokeObjectURL(url);
  };
  return (
    <>
      <button
        type="button"
        onClick={() => setAbierto(true)}
        className="mt-3 inline-flex items-center gap-1.5 rounded-lg border border-line px-2.5 py-1 text-[12.5px] font-medium text-accent-ink hover:bg-surface-2"
      >
        <Table2 aria-hidden className="h-3.5 w-3.5" />
        {t(`Ver datos en tabla (${filas.length} filas)`, `Show data as table (${filas.length} rows)`)}
      </button>
      <PanelLateral abierto={abierto} alCerrar={() => setAbierto(false)} titulo={titulo}>
        <div className="flex items-center justify-between gap-3">
          <p className="text-[12.5px] text-ink-3">{t(`${filas.length} filas · los mismos datos del gráfico`, `${filas.length} rows · the same data as the chart`)}</p>
          <button type="button" onClick={descargar} className="inline-flex items-center gap-1.5 rounded-lg border border-line px-2.5 py-1 text-[12.5px] font-medium text-accent-ink hover:bg-surface-2">
            <Download aria-hidden className="h-3.5 w-3.5" /> CSV
          </button>
        </div>
        <div className="overflow-auto rounded-lg border border-line text-[12.5px]">
          <table className="w-full border-collapse text-left">
            <caption className="sr-only">{titulo}</caption>
            <thead className="sticky top-0 bg-surface-solida">
              <tr>
                {columnas.map((c) => (
                  <th key={c} scope="col" className="border-b border-line px-3 py-1.5 font-semibold text-ink-2">
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="cifra">
              {visibles.map((f, i) => (
                <tr key={i} className="odd:bg-surface-2">
                  {f.map((c, j) => (
                    <td key={j} className="px-3 py-1 text-ink">
                      {c}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {filas.length > maxFilas && (
            <p className="px-3 py-1.5 text-ink-3">{t(`Se muestran ${maxFilas} de ${filas.length} filas (el CSV las incluye todas).`, `Showing ${maxFilas} of ${filas.length} rows (the CSV includes all).`)}</p>
          )}
        </div>
      </PanelLateral>
    </>
  );
}
