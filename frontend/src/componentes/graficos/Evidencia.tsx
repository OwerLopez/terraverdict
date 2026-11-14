import { ExternalLink } from "lucide-react";
import type { Esquemas } from "../../api/cliente";
import { CATEGORIAS_EVENTO } from "../../lib/colores";
import { TEXTO_COTA, cifraCitada, fecha } from "../../lib/formato";
import { ESTADOS_VERIFICACION, Insignia } from "../ui";

const ORDEN_ESTADOS = ["verificado", "parcial", "no_verificado", "sin_evidencia"];
const COLOR_ESTADO: Record<string, string> = {
  verificado: "var(--good)",
  parcial: "var(--warning)",
  no_verificado: "var(--critical)",
  sin_evidencia: "var(--ink-3)",
};

/** Barra apilada de estados de verificación (estado = color + ícono + texto). */
export function BarraEstados({ conteos }: { conteos: Record<string, number> }) {
  const total = Object.values(conteos).reduce((a, b) => a + b, 0) || 1;
  const presentes = ORDEN_ESTADOS.filter((e) => (conteos[e] ?? 0) > 0);
  return (
    <div>
      <div className="flex h-3 w-full gap-[2px]" role="img" aria-label="Distribución de estados de verificación">
        {presentes.map((e) => (
          <div
            key={e}
            className="h-full first:rounded-l-full last:rounded-r-full"
            style={{ width: `${((conteos[e] ?? 0) / total) * 100}%`, background: COLOR_ESTADO[e] }}
            title={`${ESTADOS_VERIFICACION[e]?.texto}: ${conteos[e]}`}
          />
        ))}
      </div>
      <ul className="mt-3 flex flex-wrap gap-x-4 gap-y-2">
        {presentes.map((e) => {
          const def = ESTADOS_VERIFICACION[e];
          return (
            <li key={e} className="flex items-center gap-1.5 text-[12.5px] text-ink-2">
              {def && <def.icono aria-hidden className="h-3.5 w-3.5" style={{ color: COLOR_ESTADO[e] }} />}
              {def?.texto} <span className="cifra font-semibold text-ink">{conteos[e]}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

/** Periodo publicado de cada fuente (barras horizontales sobre un eje de años). */
export function CoberturaFuentes({ fuentes, desde = 1945 }: { fuentes: Esquemas["FuenteSalida"][]; desde?: number }) {
  const hoy = new Date().getUTCFullYear() + new Date().getUTCMonth() / 12;
  const conPeriodo = fuentes
    .filter((f) => f.periodo?.[0])
    .map((f) => {
      const ini = Number(String(f.periodo?.[0]).slice(0, 4)) + (Number(String(f.periodo?.[0]).slice(5, 7) || 1) - 1) / 12;
      const finTxt = f.periodo?.[1];
      const fin = finTxt ? Number(String(finTxt).slice(0, 4)) + (Number(String(finTxt).slice(5, 7) || 12) - 1) / 12 : hoy;
      return { f, ini, fin, vigente: !finTxt };
    })
    .sort((a, b) => a.ini - b.ini);
  const escala = (x: number) => `${((Math.max(desde, x) - desde) / (hoy - desde)) * 100}%`;
  const marcas = [1950, 1970, 1990, 2010].filter((m) => m > desde);

  return (
    <div className="text-[12px]">
      <div className="relative ml-[180px] h-5 border-b border-line text-ink-3">
        {marcas.map((m) => (
          <span key={m} className="absolute -translate-x-1/2" style={{ left: escala(m) }}>{m}</span>
        ))}
        <span className="absolute right-0">hoy</span>
      </div>
      <ul className="mt-1.5 space-y-1">
        {conPeriodo.map(({ f, ini, fin, vigente }) => (
          <li key={f.id} className="flex items-center gap-2">
            <span className="w-[172px] shrink-0 truncate text-ink-2" title={f.nombre}>{f.nombre}</span>
            <div className="relative h-3 flex-1 rounded-full bg-surface-2">
              <div
                className="absolute inset-y-0 rounded-full"
                style={{ left: escala(ini), width: `calc(${escala(fin)} - ${escala(ini)})`, background: "var(--accent)", opacity: vigente ? 1 : 0.55 }}
                title={`${f.periodo?.[0]} → ${f.periodo?.[1] ?? "vigente"}`}
              />
            </div>
          </li>
        ))}
      </ul>
      <p className="mt-2 text-ink-3">Barra intensa: colección vigente. Barra tenue: colección cerrada.</p>
    </div>
  );
}

/** Crónica de eventos documentados, cada uno con su fuente citada. */
export function LineaTiempo({ eventos, limite }: { eventos: Esquemas["EventoDocumentadoSalida"][]; limite?: number }) {
  const lista = limite ? eventos.slice(0, limite) : eventos;
  return (
    <ol className="relative space-y-5 border-l border-line pl-6">
      {lista.map((e) => {
        const cat = CATEGORIAS_EVENTO[e.categoria];
        return (
          <li key={e.id} className="relative animate-aparecer">
            <span className="absolute -left-[31px] top-1 h-3 w-3 rounded-full border-2 border-surface" style={{ background: cat?.color ?? "var(--ink-3)" }} aria-hidden />
            <div className="flex flex-wrap items-center gap-2">
              <time className="cifra text-[12px] font-medium text-ink-3" dateTime={e.fecha}>{fecha(e.fecha, e.precision)}</time>
              <Insignia>{cat?.texto ?? e.categoria}</Insignia>
            </div>
            <p className="mt-1 font-semibold leading-snug text-ink">{e.titulo}</p>
            <p className="mt-0.5 text-[13px] leading-relaxed text-ink-2">{e.descripcion}</p>
            {e.cifras.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {e.cifras.map((c) => (
                  <span key={c.descripcion} className="rounded-lg border border-line bg-surface-2 px-2 py-1 text-[12px] text-ink-2" title={TEXTO_COTA[c.cota]}>
                    <span className="cifra font-semibold text-ink">{cifraCitada(c)}</span> · {c.descripcion}
                  </span>
                ))}
              </div>
            )}
            <ul className="mt-2 space-y-0.5">
              {e.fuentes.map((f) => (
                <li key={f.url}>
                  <a href={f.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-[12px] text-accent-ink hover:underline">
                    <ExternalLink className="h-3 w-3" aria-hidden />
                    {f.medio ? `${f.medio}: ` : ""}{f.titulo}
                  </a>
                </li>
              ))}
            </ul>
          </li>
        );
      })}
    </ol>
  );
}
