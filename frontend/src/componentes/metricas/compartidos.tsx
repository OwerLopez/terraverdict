import { Sigma } from "lucide-react";
import { useMemo } from "react";
import type { Esquemas } from "../../api/cliente";
import { RAMPA_AZUL, colorSecuencial } from "../../lib/colores";
import { numero } from "../../lib/formato";
import { idiomaActual, t } from "../../lib/i18n";
import { evidencia, nombreVariable } from "../../lib/modelos";
import { LeyendaEscala, MatrizCalor } from "../graficos/MatrizCalor";
import { Insignia, Tarjeta } from "../ui";

type Ficha = Esquemas["FichaMetrica"];
type Mapas = Esquemas["MapasMetricas"];

/** Separa "Título (fuente)" en etiqueta y subtítulo, para que tareas con distinta fuente no se confundan. */
export function partesTitulo(titulo: string): { etiqueta: string; sub?: string } {
  const m = /^(.*?)\s*\(([^)]*)\)\s*$/.exec(titulo);
  return m ? { etiqueta: m[1] as string, sub: m[2] } : { etiqueta: titulo };
}

export const bilingue = (x: { es: string; en: string }) => (idiomaActual() === "en" ? x.en : x.es);

export const TEXTO_EVIDENCIA = {
  confirmada: () => t("confirmada", "confirmed"),
  indicio: () => t("indicio", "indication"),
  no_confirmada: () => t("no confirmada", "not confirmed"),
};

export function InsigniaEvidencia({ lo, p }: { lo: number | null | undefined; p: number | null | undefined }) {
  const e = evidencia(lo, p);
  return <Insignia tono={e === "confirmada" ? "good" : e === "indicio" ? "accent" : "neutral"}>{TEXTO_EVIDENCIA[e]()}</Insignia>;
}

/** Ficha de una métrica: qué mide, cómo leerla, si es mejor alta o baja y su referencia. */
export function FichaMetrica({ ficha, compacta = false }: { ficha: Ficha; compacta?: boolean }) {
  const mejor: Record<string, string> = {
    mayor: t("Mejor si es mayor", "Higher is better"),
    menor: t("Mejor si es menor", "Lower is better"),
    cercano_a_0_9: t("Mejor si está cerca de 0,90", "Best near 0.90"),
    informativa: t("Informativa: se lee junto con las demás", "Informative: read alongside the others"),
  };
  return (
    <article className={compacta ? "rounded-xl border border-line bg-surface-2 p-3" : "panel-vidrio rounded-2xl p-4"}>
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="text-[14px] font-semibold text-ink">{bilingue(ficha.nombre)}</h3>
        <span className="text-[11.5px] text-ink-3">{mejor[ficha.mejor] ?? ficha.mejor}</span>
      </header>
      <p className="mt-1.5 font-mono text-[11.5px] text-ink-2">{ficha.formula}</p>
      <dl className="mt-2 space-y-1.5 text-[12.5px] leading-snug">
        <div>
          <dt className="etiqueta">{t("Qué mide", "What it measures")}</dt>
          <dd className="text-ink-2">{bilingue(ficha.que_mide)}</dd>
        </div>
        <div>
          <dt className="etiqueta">{t("Cómo leerla", "How to read it")}</dt>
          <dd className="text-ink-2">{bilingue(ficha.como_leer)}</dd>
        </div>
      </dl>
      {!compacta && <p className="mt-2 text-[11.5px] text-ink-3">{t("Referencia", "Reference")}: {ficha.cita}</p>}
    </article>
  );
}

/** Mapa de calor tarea × variable con la importancia por permutación publicada en cada expediente. */
export function ImportanciaVariables({ mapas, ficha }: { mapas: Mapas; ficha?: Ficha }) {
  const indice = useMemo(() => new Map(mapas.importancia.map((i) => [`${i.expediente_id}|${i.variable}`, i])), [mapas]);
  const maximo = useMemo(() => {
    const m = new Map<string, number>();
    for (const i of mapas.importancia) m.set(i.expediente_id, Math.max(m.get(i.expediente_id) ?? 1e-12, i.importancia));
    return m;
  }, [mapas]);
  const tareas = mapas.tareas.filter((x) => maximo.has(x.expediente_id));
  if (!tareas.length) return null;
  return (
    <Tarjeta
      titulo={<span className="flex items-center gap-2"><Sigma className="h-4 w-4 text-accent" /> {t("Mapa de calor: importancia de cada variable", "Heatmap: importance of each variable")}</span>}
      subtitulo={t(
        "Importancia por permutación en validación (nunca en prueba), con un gradient boosting ajustado en entrenamiento. Cada fila se escala por su variable más importante.",
        "Permutation importance on validation (never on test), with gradient boosting fitted on training. Each row is scaled by its most important variable.",
      )}
    >
      <MatrizCalor
        titulo={t("Importancia de variables por tarea", "Variable importance by task")}
        etiquetaFilas={t("Tarea", "Task")}
        anchoFila={240}
        filas={tareas.map((x) => ({ id: x.expediente_id, ...partesTitulo(x.titulo) }))}
        columnas={mapas.variables.map((v) => ({ id: v, etiqueta: nombreVariable(v) }))}
        celda={(f, c) => {
          const i = indice.get(`${f.id}|${c.id}`);
          if (!i) return undefined;
          const fraccion = Math.max(0, i.importancia) / (maximo.get(f.id) ?? 1);
          return {
            texto: numero(fraccion, 2),
            color: i.importancia > 0 ? colorSecuencial(fraccion) : undefined,
            detalle: t(
              `${c.etiqueta} en ${f.etiqueta}: importancia ${numero(i.importancia, 4)} ± ${numero(i.desviacion, 4)} (relativa ${numero(fraccion, 2)})${i.importancia <= 0 ? ". El modelo no la necesita." : ""}`,
              `${c.etiqueta} in ${f.etiqueta}: importance ${numero(i.importancia, 4)} ± ${numero(i.desviacion, 4)} (relative ${numero(fraccion, 2)})${i.importancia <= 0 ? ". The model does not need it." : ""}`,
            ),
          };
        }}
        leyenda={<LeyendaEscala colores={[...RAMPA_AZUL]} izquierda={t("poco relevante", "low relevance")} derecha={t("la más relevante de la fila", "most relevant in the row")} nota={t("Una importancia alta no implica causalidad: indica de qué dependen las predicciones.", "High importance does not imply causality: it shows what the predictions rely on.")} />}
      />
      {ficha && <div className="mt-3"><FichaMetrica ficha={ficha} compacta /></div>}
    </Tarjeta>
  );
}

