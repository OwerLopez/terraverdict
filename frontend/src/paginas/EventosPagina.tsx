import { useMemo, useState } from "react";
import { useEventos } from "../api/consultas";
import { LineaTiempo } from "../componentes/graficos/Evidencia";
import { Encabezado, Esqueleto, ErrorCarga, Tarjeta } from "../componentes/ui";
import { CATEGORIAS_EVENTO } from "../lib/colores";

export function EventosPagina() {
  const eventos = useEventos();
  const [categoria, setCategoria] = useState<string | null>(null);
  const lista = useMemo(() => (eventos.data ?? []).filter((e) => !categoria || e.categoria === categoria), [eventos.data, categoria]);
  const presentes = useMemo(() => new Set<string>((eventos.data ?? []).map((e) => e.categoria)), [eventos.data]);

  return (
    <div className="space-y-6">
      <Encabezado
        eyebrow="Evidencia"
        titulo="Crónica de eventos"
        descripcion="Lo que pasó en el sistema hídrico de Arequipa, con cada cifra atribuida a su fuente. La precisión de la fecha se respeta: si la fuente solo indica el mes o el año, no se inventa el día."
      />
      <div className="flex flex-wrap gap-2" role="group" aria-label="Filtrar por categoría">
        <button type="button" onClick={() => setCategoria(null)} className={`rounded-full border px-3 py-1 text-[12.5px] ${categoria === null ? "border-accent bg-accent-soft text-accent-ink" : "border-line text-ink-2 hover:bg-surface-2"}`}>
          Todas
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
