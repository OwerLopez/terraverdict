import { useMemo, useState } from "react";
import { useEventos } from "../api/consultas";
import { LineaTiempo } from "../componentes/graficos/Evidencia";
import { Encabezado, Esqueleto, ErrorCarga, Tarjeta } from "../componentes/ui";
import { CATEGORIAS_EVENTO } from "../lib/colores";
import { t } from "../lib/i18n";

export function EventosPagina() {
  const eventos = useEventos();
  const [categoria, setCategoria] = useState<string | null>(null);
  const lista = useMemo(() => (eventos.data ?? []).filter((e) => !categoria || e.categoria === categoria), [eventos.data, categoria]);
  const presentes = useMemo(() => new Set<string>((eventos.data ?? []).map((e) => e.categoria)), [eventos.data]);

  return (
    <div className="space-y-6">
      <Encabezado
        eyebrow={t("Evidencia", "Evidence")}
        titulo={t("Crónica de eventos", "Event chronicle")}
        descripcion={t("Lo que pasó en el sistema hídrico de Arequipa, con cada cifra atribuida a su fuente. La precisión de la fecha se respeta: si la fuente solo indica el mes o el año, no se inventa el día. Los textos citados se muestran en su idioma original.", "What happened in Arequipa's water system, with every figure attributed to its source. Date precision is respected: if the source only gives the month or year, no day is invented. Cited texts are shown in their original language (Spanish).")}
      />
      <div className="flex flex-wrap gap-2" role="group" aria-label={t("Filtrar por categoría", "Filter by category")}>
        <button type="button" onClick={() => setCategoria(null)} className={`rounded-full border px-3 py-1 text-[12.5px] ${categoria === null ? "border-accent bg-accent-soft text-accent-ink" : "border-line text-ink-2 hover:bg-surface-2"}`}>
          {t("Todas", "All")}
        </button>
        {Object.entries(CATEGORIAS_EVENTO).filter(([k]) => presentes.has(k)).map(([k, c]) => (
          <button
            key={k}
            type="button"
            onClick={() => setCategoria(k)}
            aria-pressed={categoria === k}
            className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-[12.5px] ${categoria === k ? "border-accent bg-accent-soft text-accent-ink" : "border-line text-ink-2 hover:bg-surface-2"}`}
          >
            <span className="h-2 w-2 rounded-full" style={{ background: c.color }} /> {c.texto}
          </button>
        ))}
      </div>
      <Tarjeta>
        {eventos.isLoading ? <Esqueleto className="h-96" /> : eventos.error ? <ErrorCarga error={eventos.error} /> : <LineaTiempo eventos={lista} />}
      </Tarjeta>
    </div>
  );
}
