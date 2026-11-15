import { clsx } from "clsx";
import { ArrowDown, ArrowUp, Grid3x3, Minus, Waves } from "lucide-react";
import { useState } from "react";
import type { Esquemas } from "../../api/cliente";
import { RAMPA_AZUL } from "../../lib/colores";
import { numero, valorP } from "../../lib/formato";
import { EstadoVacio } from "../ui";
import { t } from "../../lib/i18n";

type Matriz = Esquemas["MatrizRelevancia"];
type Celda = Esquemas["CeldaRelevancia"];

/** Color por importancia (rampa secuencial). La confianza baja se atenúa hacia el gris neutro. */
export function colorCelda(importancia: number, estabilidad: number): { fondo: string; texto: string; opacidad: number } {
  const i = Math.min(RAMPA_AZUL.length - 1, Math.max(0, Math.floor(importancia * RAMPA_AZUL.length)));
  const fondo = RAMPA_AZUL[i] as string;
  return { fondo, texto: i >= 3 ? "#ffffff" : "#0b0b0b", opacidad: 0.35 + 0.65 * Math.max(0, Math.min(1, estabilidad)) };
}

const ICONO_DIRECCION = { positiva: ArrowUp, negativa: ArrowDown, no_monotona: Waves, indeterminada: Minus } as const;

export function MapaCalor({ matriz }: { matriz: Matriz }) {
  const [activa, setActiva] = useState<Celda | null>(null);
  const celdas = new Map(matriz.celdas.map((c) => [`${c.problema_id}|${c.variable_id}`, c]));
  const nombreVariable = new Map(matriz.variables.map((v) => [v.id, v.nombre]));
  const vacia = matriz.estado === "vacia";

  return (
    <div className="space-y-4">
      <div className="relative overflow-x-auto rounded-xl border border-line">
        <table className="w-full border-separate border-spacing-[3px] text-[12.5px]">
          <caption className="sr-only">{t("Matriz de relevancia: problemas por variables", "Relevance matrix: problems by variables")}</caption>
          <thead>
            <tr>
              <th className="sticky left-0 z-10 min-w-[220px] bg-surface px-3 py-2 text-left align-bottom font-medium text-ink-2">{t("Problema", "Problem")}</th>
              {matriz.variables.map((v) => (
                <th key={v.id} scope="col" className="h-[120px] min-w-[56px] align-bottom font-medium text-ink-2">
                  <div className="mx-auto w-5 whitespace-nowrap [writing-mode:vertical-rl] rotate-180 text-left">{v.nombre}</div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matriz.problemas.map((p) => (
              <tr key={p.id}>
                <th scope="row" className="sticky left-0 z-10 bg-surface px-3 py-2 text-left font-normal">
                  <span className="mr-2 font-mono text-[11px] text-ink-3">{p.id}</span>
                  <span className="font-medium text-ink">{p.nombre}</span>
                  <span className="block text-[11.5px] text-ink-3">{t("Viabilidad", "Feasibility")}: {p.viabilidad}</span>
                </th>
                {matriz.variables.map((v) => {
                  const celda = celdas.get(`${p.id}|${v.id}`);
                  const candidata = p.candidatas.includes(v.id);
                  if (celda) {
                    const col = colorCelda(celda.importancia, celda.estabilidad);
                    const Icono = ICONO_DIRECCION[celda.direccion as keyof typeof ICONO_DIRECCION] ?? Minus;
                    return (
                      <td key={v.id} className="p-0">
                        <button
                          type="button"
                          onMouseEnter={() => setActiva(celda)}
                          onFocus={() => setActiva(celda)}
                          className="grid h-12 w-full place-items-center rounded-md transition-transform hover:scale-[1.04]"
                          style={{ background: col.fondo, opacity: col.opacidad, color: col.texto }}
                          aria-label={t(`${p.nombre}, ${v.nombre}: importancia ${numero(celda.importancia, 2)}, estabilidad ${numero(celda.estabilidad, 2)}, dirección ${celda.direccion}`, `${p.nombre}, ${v.nombre}: importance ${numero(celda.importancia, 2)}, stability ${numero(celda.estabilidad, 2)}, direction ${celda.direccion}`)}
                        >
                          <Icono className="h-3.5 w-3.5" aria-hidden />
                        </button>
                      </td>
                    );
                  }
                  return (
                    <td key={v.id} className="p-0">
                      <div
                        className={clsx("grid h-12 place-items-center rounded-md", candidata ? "rayado border border-dashed border-line-strong" : "bg-surface-2")}
                        title={candidata ? t(`${v.nombre}: candidata de ${p.id}, sin resultado publicado`, `${v.nombre}: candidate for ${p.id}, no published result`) : t("No es candidata de este problema", "Not a candidate for this problem")}
                      >
                        {candidata && <span className="h-1.5 w-1.5 rounded-full bg-ink-3" aria-hidden />}
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
        {vacia && (
          <div className="pointer-events-none absolute inset-0 grid place-items-center bg-[var(--vidrio)] p-6">
            <EstadoVacio icono={Grid3x3} titulo={t("Todavía no hay resultados de relevancia", "No relevance results yet")} className="pointer-events-auto max-w-lg bg-surface">
              {matriz.mensaje} {t("Los puntos marcan las variables candidatas de cada plantilla. La matriz se llenará cuando el pipeline publique expedientes de tipo", "Dots mark each template's candidate variables. The matrix will fill when the pipeline publishes case files of type")} <code className="font-mono">relevancia</code>.
            </EstadoVacio>
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-start justify-between gap-6 text-[12px] text-ink-2">
        <div>
          <p className="etiqueta mb-1.5">{t("Importancia", "Importance")}</p>
          <div className="flex items-center gap-2">
            <span>0</span>
            <div className="flex">{RAMPA_AZUL.map((c) => <span key={c} className="h-3 w-6 first:rounded-l last:rounded-r" style={{ background: c }} />)}</div>
            <span>1</span>
          </div>
        </div>
        <div className="max-w-xs">
          <p className="etiqueta mb-1.5">{t("Confianza", "Confidence")}</p>
          <p>{t("Menor estabilidad entre remuestreos = color más tenue. Una importancia incierta nunca se ve intensa.", "Lower stability across resamples = fainter color. An uncertain importance never looks intense.")}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="rayado grid h-5 w-7 place-items-center rounded border border-dashed border-line-strong"><span className="h-1.5 w-1.5 rounded-full bg-ink-3" /></span>
          {t("Candidata sin resultado", "Candidate without result")}
        </div>
      </div>

      {activa && (
        <div className="rounded-xl border border-line bg-surface-2 p-3 text-[13px]" aria-live="polite">
          <p className="font-semibold text-ink">{activa.problema_id} · {nombreVariable.get(activa.variable_id) ?? activa.variable_id}</p>
          <p className="mt-1 text-ink-2">
            {t("Importancia", "Importance")} {numero(activa.importancia, 2)} · {t("estabilidad", "stability")} {numero(activa.estabilidad, 2)} · {t("p ajustado", "adjusted p")} {valorP(activa.p_ajustado)} ·{" "}
            {t("dirección", "direction")} {activa.direccion} · {activa.publicable ? t("publicable", "publishable") : t("no publicable", "not publishable")} · {t("expediente", "case file")}{" "}
            <span className="font-mono">{activa.expediente_id}</span>
          </p>
        </div>
      )}
    </div>
  );
}
