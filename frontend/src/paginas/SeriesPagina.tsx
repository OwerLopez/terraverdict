import { clsx } from "clsx";
import { Download, FileCheck2, LineChart } from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useExpedientes, useExpediente, useObservaciones, useSeries, useVariables } from "../api/consultas";
import { GraficoSerie } from "../componentes/graficos/GraficoSerie";
import { Boton, ChipEstado, Encabezado, Esqueleto, EstadoVacio, ErrorCarga, Insignia, Tarjeta, VEREDICTOS } from "../componentes/ui";
import { fecha, fechaHora, simboloUnidad } from "../lib/formato";

function descargarCsv(nombre: string, filas: { t: string; valor: number | null }[]) {
  const csv = ["t,valor", ...filas.map((f) => `${f.t},${f.valor ?? ""}`)].join("\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  const a = Object.assign(document.createElement("a"), { href: url, download: `${nombre}.csv` });
  a.click();
  URL.revokeObjectURL(url);
}

export function SeriesPagina() {
  const [params, setParams] = useSearchParams();
  const [variable, setVariable] = useState<string>("");
  const variables = useVariables();
  const series = useSeries(variable ? { variable_id: variable } : {});
  const lista = useMemo(
    () => (series.data?.items ?? []).slice().sort((a, b) => b.n_observaciones - a.n_observaciones),
    [series.data],
  );
  const seleccion = params.get("serie") ?? lista[0]?.id;
  const serie = lista.find((s) => s.id === seleccion) ?? lista[0];
  const obs = useObservaciones(serie?.id);
  const expedientes = useExpedientes(serie ? { serie_id: serie.id, tipo: "tendencia" } : {});
  const expediente = useExpediente(serie ? expedientes.data?.items[0]?.id : undefined);
  const r = expediente.data?.resultado;
  const tendencia = r && r.tipo === "tendencia" ? r : null;
  const nombreVariable = new Map((variables.data ?? []).map((v) => [v.id, v.nombre]));

  return (
    <div>
      <Encabezado
        eyebrow="Explorar"
        titulo="Series temporales"
        descripcion="Cada serie viene del pipeline con su fuente, su unidad y su procedencia. Si existe un expediente de tendencia, se dibujan la pendiente de Sen y su intervalo."
      />
      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <Tarjeta titulo="Catálogo" sinPadding>
          <div className="px-5 pb-3 pt-2">
            <label className="block text-[12px] text-ink-2">
              Variable
              <select
                value={variable}
                onChange={(e) => setVariable(e.target.value)}
                className="mt-1 h-9 w-full rounded-lg border border-line bg-surface-2 px-2.5 text-[13px] text-ink"
              >
                <option value="">Todas</option>
                {(variables.data ?? []).map((v) => <option key={v.id} value={v.id}>{v.nombre}</option>)}
              </select>
            </label>
          </div>
          {series.isLoading ? (
            <div className="space-y-2 px-5 pb-5">{[0, 1, 2, 3].map((i) => <Esqueleto key={i} className="h-12" />)}</div>
          ) : (
            <ul className="max-h-[560px] overflow-y-auto border-t border-line">
              {lista.map((s) => (
                <li key={s.id}>
                  <button
                    type="button"
                    onClick={() => setParams({ serie: s.id })}
                    className={clsx(
                      "w-full border-b border-line px-5 py-2.5 text-left transition-colors last:border-b-0",
                      s.id === serie?.id ? "bg-accent-soft" : "hover:bg-surface-2",
                    )}
                  >
                    <p className="text-[13px] font-medium text-ink">{nombreVariable.get(s.variable_id) ?? s.variable_id}</p>
                    <p className="truncate text-[11.5px] text-ink-3">{(s.unidad_id ?? s.dominio_id).replace("chili_analisis.", "")} · {s.fuente_id}</p>
                    <p className="cifra text-[11.5px] text-ink-3">{s.n_observaciones} obs. · {s.frecuencia}</p>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Tarjeta>

        <div className="space-y-6">
          {!serie ? (
            <EstadoVacio icono={LineChart} titulo="No hay series para este filtro">
              Las series aparecen cuando el pipeline las publica con <code className="font-mono">POST /api/v1/series</code>.
            </EstadoVacio>
          ) : (
            <>
              <Tarjeta
                titulo={nombreVariable.get(serie.variable_id) ?? serie.variable_id}
                subtitulo={serie.descripcion}
                acciones={
                  <>
                    {tendencia && <ChipEstado mapa={VEREDICTOS} valor={tendencia.veredicto} />}
                    <Boton tamano="sm" icono={Download} disabled={!obs.data} onClick={() => obs.data && descargarCsv(serie.id.replace(/[:.]/g, "_"), obs.data.observaciones)}>
                      CSV
                    </Boton>
                  </>
                }
                pie={<>Versión {serie.version} · actualizada {fechaHora(serie.actualizado_en)} · unidad {simboloUnidad(serie.unidad) || "adimensional"}</>}
              >
                {obs.isLoading ? (
                  <Esqueleto className="h-[340px]" />
                ) : obs.error ? (
                  <ErrorCarga error={obs.error} />
                ) : (obs.data?.observaciones.length ?? 0) < 2 ? (
                  <EstadoVacio titulo="Serie con un solo dato">
                    Valor del {fecha(obs.data?.observaciones[0]?.t)}: <strong className="cifra">{obs.data?.observaciones[0]?.valor ?? "—"} {simboloUnidad(serie.unidad)}</strong>.
                    Se graficará cuando el pipeline cargue más fechas.
                  </EstadoVacio>
                ) : (
                  <GraficoSerie
                    observaciones={obs.data?.observaciones ?? []}
                    unidad={serie.unidad}
                    agregacion={serie.agregacion}
                    pendiente={tendencia?.pendiente}
                    alto={340}
                    nombre={nombreVariable.get(serie.variable_id) ?? "Observado"}
                  />
                )}
              </Tarjeta>

              <Tarjeta titulo="Procedencia" subtitulo="De dónde viene cada valor">
                <dl className="grid gap-4 text-[13px] sm:grid-cols-2">
                  <div>
                    <dt className="etiqueta mb-1">Fuentes</dt>
                    <dd className="flex flex-wrap gap-1.5">
                      {serie.procedencia.fuentes.map((f) => <Insignia key={f.fuente_id}>{f.fuente_id}</Insignia>)}
                    </dd>
                  </div>
                  <div>
                    <dt className="etiqueta mb-1">Agregación</dt>
                    <dd className="font-mono text-[12px] text-ink-2">{JSON.stringify(serie.agregacion)}</dd>
                  </div>
                  <div>
                    <dt className="etiqueta mb-1">Código</dt>
                    <dd className="text-ink-2">{serie.procedencia.codigo?.script ?? "—"}</dd>
                  </div>
                  <div>
                    <dt className="etiqueta mb-1">Generado</dt>
                    <dd className="text-ink-2">{fechaHora(serie.procedencia.generado_utc)}</dd>
                  </div>
                </dl>
                {expediente.data && (
                  <Link to={`/expedientes/${expediente.data.id}`} className="mt-4 inline-flex items-center gap-1.5 text-[13px] font-medium text-accent-ink hover:underline">
                    <FileCheck2 className="h-4 w-4" /> Ver el expediente {expediente.data.id}
                  </Link>
                )}
              </Tarjeta>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
