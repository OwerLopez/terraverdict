import { ExternalLink, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { useFuentes, useVerificacion } from "../api/consultas";
import { BarraEstados, CoberturaFuentes } from "../componentes/graficos/Evidencia";
import { ChipEstado, Encabezado, Esqueleto, ErrorCarga, ESTADOS_VERIFICACION, Segmentado, Tarjeta } from "../componentes/ui";
import { fecha } from "../lib/formato";

type Filtro = "todas" | "verificado" | "parcial" | "sin_evidencia";

export function FuentesPagina() {
  const fuentes = useFuentes();
  const verificacion = useVerificacion();
  const [filtro, setFiltro] = useState<Filtro>("todas");
  const [texto, setTexto] = useState("");

  const lista = useMemo(() => {
    const q = texto.trim().toLowerCase();
    return (fuentes.data ?? []).filter(
      (f) =>
        (filtro === "todas" || f.estado_verificacion === filtro) &&
        (!q || `${f.nombre} ${f.coleccion ?? ""} ${f.familia ?? ""}`.toLowerCase().includes(q)),
    );
  }, [fuentes.data, filtro, texto]);

  const v = verificacion.data;
  return (
    <div className="space-y-6">
      <Encabezado
        eyebrow="Evidencia"
        titulo="Fuentes verificadas"
        descripcion="Cada fuente se comprobó con consultas reales a su catálogo oficial: que exista, su periodo publicado y que tenga datos sobre la cuenca. La verificación es reproducible con scripts/verificar_fuentes.py."
      />
      <div className="grid gap-6 lg:grid-cols-[1fr_1.4fr]">
        <Tarjeta
          titulo="Resultado de la verificación"
          subtitulo={v?.fuentes ? `${v.fuentes.correctas} de ${v.fuentes.total} comprobaciones correctas · ${fecha(v.fuentes.generado_utc)}` : undefined}
          pie={v?.enlaces ? `Enlaces del reto y la guía: ${v.enlaces.correctas} de ${v.enlaces.total} respondieron HTTP 200 en la ejecución registrada.` : undefined}
        >
          {v ? <BarraEstados conteos={v.estados_fuentes} /> : <Esqueleto className="h-16" />}
        </Tarjeta>
        <Tarjeta titulo="Cobertura temporal" subtitulo="Periodo publicado por cada colección, según su catálogo">
          {fuentes.data ? <CoberturaFuentes fuentes={fuentes.data} /> : <Esqueleto className="h-64" />}
        </Tarjeta>
      </div>

      <Tarjeta
        titulo="Catálogo"
        acciones={
          <Segmentado<Filtro>
            etiqueta="Filtrar por estado"
            valor={filtro}
            alCambiar={setFiltro}
            opciones={[
              { valor: "todas", texto: "Todas" },
              { valor: "verificado", texto: "Verificadas" },
              { valor: "parcial", texto: "Parciales" },
              { valor: "sin_evidencia", texto: "Sin evidencia" },
            ]}
          />
        }
        sinPadding
      >
        <div className="px-5 pb-3">
          <label className="relative block">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-3" />
            <span className="sr-only">Buscar fuente</span>
            <input value={texto} onChange={(e) => setTexto(e.target.value)} placeholder="Buscar por nombre, colección o familia" className="h-9 w-full rounded-lg border border-line bg-surface-2 pl-9 pr-3 text-[13px] text-ink" />
          </label>
        </div>
        {fuentes.error ? (
          <ErrorCarga error={fuentes.error} className="m-5" />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead className="border-y border-line bg-surface-2 text-left text-[12px] text-ink-2">
                <tr>
                  <th className="px-5 py-2 font-medium">Fuente</th>
                  <th className="px-3 py-2 font-medium">Colección</th>
                  <th className="px-3 py-2 font-medium">Periodo</th>
                  <th className="px-3 py-2 font-medium">Familia</th>
                  <th className="px-5 py-2 font-medium">Estado</th>
                </tr>
              </thead>
              <tbody>
                {lista.map((f) => (
                  <tr key={f.id} className="border-b border-line align-top last:border-b-0 hover:bg-surface-2">
                    <td className="px-5 py-2.5">
                      <p className="font-medium text-ink">{f.nombre}</p>
                      {f.advertencia && <p className="mt-0.5 max-w-sm text-[11.5px] leading-snug text-ink-3">{f.advertencia}</p>}
                      {f.por_confirmar && <p className="mt-0.5 max-w-sm text-[11.5px] leading-snug" style={{ color: "var(--serious)" }}>Por confirmar: {f.por_confirmar}</p>}
                    </td>
                    <td className="px-3 py-2.5">
                      <span className="font-mono text-[12px] text-ink-2">{f.coleccion ?? "—"}{f.version ? ` v${f.version}` : ""}</span>
                      {f.url && (
                        <a href={f.url} target="_blank" rel="noreferrer" className="mt-0.5 flex items-center gap-1 text-[11.5px] text-accent-ink hover:underline">
                          <ExternalLink className="h-3 w-3" /> acceso
                        </a>
                      )}
                    </td>
                    <td className="cifra px-3 py-2.5 text-ink-2">{f.periodo ? `${f.periodo[0] ?? "?"} → ${f.periodo[1] ?? "vigente"}` : "—"}</td>
                    <td className="px-3 py-2.5 font-mono text-[12px] text-ink-2">{f.familia ?? "—"}</td>
                    <td className="px-5 py-2.5"><ChipEstado mapa={ESTADOS_VERIFICACION} valor={f.estado_verificacion} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Tarjeta>
    </div>
  );
}
