import type { ReactNode } from "react";

/**
 * Vista de tabla de un gráfico (accesibilidad): los mismos datos que el gráfico, legibles por
 * lectores de pantalla y en impresión. Plegada por defecto para no duplicar ruido visual.
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
  const visibles = filas.slice(0, maxFilas);
  return (
    <details className="mt-3 text-[12.5px]">
      <summary className="cursor-pointer select-none font-medium text-accent-ink hover:underline">
        Ver datos en tabla ({filas.length} filas)
      </summary>
      <div className="mt-2 max-h-80 overflow-auto rounded-lg border border-line">
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
          <p className="px-3 py-1.5 text-ink-3">Se muestran {maxFilas} de {filas.length} filas.</p>
        )}
      </div>
    </details>
  );
}
