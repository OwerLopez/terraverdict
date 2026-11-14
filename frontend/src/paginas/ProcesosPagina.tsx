import { clsx } from "clsx";
import { Ban, Play, TerminalSquare, Workflow } from "lucide-react";
import { useState, type FormEvent } from "react";
import type { Esquemas } from "../api/cliente";
import { ErrorApi } from "../api/cliente";
import { useCancelarProceso, useEventosProceso, useProcesos, useResumen, useSeries, useSolicitarProceso } from "../api/consultas";
import { Boton, ChipEstado, ESTADOS_PROCESO, Encabezado, Esqueleto, EstadoVacio, ErrorCarga, Insignia, Tarjeta } from "../componentes/ui";
import { fechaHora, haceCuanto } from "../lib/formato";
import { useSesion } from "../lib/sesion";

type Proceso = Esquemas["ProcesoSalida"];

function Bitacora({ proceso }: { proceso: Proceso }) {
  const activo = proceso.estado === "pendiente" || proceso.estado === "en_curso";
  const eventos = useEventosProceso(proceso.id, activo);
  const cancelar = useCancelarProceso();
  const { puede } = useSesion();
  const color = { debug: "var(--ink-3)", info: "var(--accent)", aviso: "var(--warning)", error: "var(--critical)" } as const;
  return (
    <Tarjeta
      titulo={<span className="flex items-center gap-2"><TerminalSquare className="h-4 w-4 text-accent" /> Bitácora del proceso</span>}
      subtitulo={<span className="font-mono text-[11.5px]">{proceso.id}</span>}
      acciones={
        activo && puede("analista") && (
          <Boton tamano="sm" icono={Ban} onClick={() => cancelar.mutate(proceso.id)} disabled={cancelar.isPending}>Cancelar</Boton>
        )
      }
    >
      <div className="rounded-xl bg-[#0d0d0d] p-4 font-mono text-[12px] leading-relaxed text-[#c3c2b7]">
        {eventos.isLoading ? (
          <p>Cargando…</p>
        ) : (
          (eventos.data ?? []).map((e) => (
            <p key={e.id} className="flex gap-3">
              <span className="shrink-0 text-[#898781]">{new Date(e.t).toLocaleTimeString("es-PE")}</span>
              <span className="w-12 shrink-0 uppercase" style={{ color: color[e.nivel as keyof typeof color] }}>{e.nivel}</span>
              <span className="text-[#f0efec]">{e.mensaje}</span>
            </p>
          ))
        )}
        {activo && <p className="mt-1 animate-pulso text-[#898781]">▍ esperando eventos del trabajador…</p>}
      </div>
      {proceso.error && <p className="mt-3 text-[13px]" style={{ color: "var(--critical)" }}>Error: {proceso.error.mensaje}</p>}
    </Tarjeta>
  );
}

function Solicitar() {
  const series = useSeries({});
  const solicitar = useSolicitarProceso();
  const [error, setError] = useState<string | null>(null);
  const enviar = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const serie = String(new FormData(e.currentTarget).get("serie"));
    setError(null);
    solicitar.mutate(
      { tipo: "tendencia", parametros: { serie_id: serie }, prioridad: 5 },
      { onError: (err) => setError(err instanceof ErrorApi ? err.message : "No se pudo solicitar.") },
    );
  };
  const largas = (series.data?.items ?? []).filter((s) => s.n_observaciones >= 10);
  return (
    <form onSubmit={enviar} className="flex flex-col gap-3 sm:flex-row sm:items-end">
      <label className="flex-1 text-[12px] text-ink-2">
        Recalcular tendencia y sello para la serie
        <select name="serie" className="mt-1 h-9 w-full rounded-lg border border-line bg-surface-2 px-2.5 text-[13px] text-ink">
          {largas.map((s) => <option key={s.id} value={s.id}>{s.id}</option>)}
        </select>
      </label>
      <Boton type="submit" variante="primario" icono={Play} disabled={solicitar.isPending || largas.length === 0}>Solicitar</Boton>
      {error && <p role="alert" className="text-[13px]" style={{ color: "var(--critical)" }}>{error}</p>}
    </form>
  );
}

export function ProcesosPagina() {
  const procesos = useProcesos();
  const resumen = useResumen();
  const { puede, identidad } = useSesion();
  const [seleccion, setSeleccion] = useState<string | null>(null);
  const lista = procesos.data?.items ?? [];
  const activo = lista.find((p) => p.id === seleccion) ?? lista[0];
  const trabajadores = resumen.data?.trabajadores_activos ?? 0;

  return (
    <div className="space-y-6">
      <Encabezado
        eyebrow="Integración con ciencia de datos"
        titulo="Procesos científicos"
        descripcion="Las personas solicitan cálculos; los trabajadores del pipeline los reclaman, informan su avance en la bitácora y publican un expediente. La API no calcula ciencia: coordina."
        acciones={
          <Insignia tono={trabajadores > 0 ? "good" : "neutral"} icono={Workflow}>
            {trabajadores > 0 ? `${trabajadores} trabajador(es) activo(s)` : "Ningún trabajador conectado"}
          </Insignia>
        }
      />

      <Tarjeta titulo="Solicitar un proceso" subtitulo={puede("analista") ? "Quedará pendiente hasta que un trabajador lo reclame." : undefined}>
        {puede("analista") ? (
          <Solicitar />
        ) : (
          <p className="text-[13px] text-ink-2">
            {identidad ? "Su rol no permite solicitar procesos (se requiere analista)." : "Inicie sesión con rol analista para solicitar procesos."}
          </p>
        )}
      </Tarjeta>

      {procesos.isLoading ? (
        <Esqueleto className="h-60" />
      ) : procesos.error ? (
        <ErrorCarga error={procesos.error} />
      ) : lista.length === 0 ? (
        <EstadoVacio icono={Workflow} titulo="Todavía no hay procesos">
          Cuando un analista solicite un cálculo aparecerá aquí, con su estado y su bitácora en vivo. Contrato para trabajadores:
          <code className="mx-1 font-mono">POST /api/v1/procesos/reclamar</code>.
        </EstadoVacio>
      ) : (
        <div className="grid gap-6 xl:grid-cols-[1fr_1.1fr]">
          <Tarjeta titulo="Cola" sinPadding>
            <ul className="divide-y divide-line">
              {lista.map((p) => (
                <li key={p.id}>
                  <button
                    type="button"
                    onClick={() => setSeleccion(p.id)}
                    className={clsx("flex w-full items-center justify-between gap-3 px-5 py-3 text-left", p.id === activo?.id ? "bg-accent-soft" : "hover:bg-surface-2")}
                  >
                    <span className="min-w-0">
                      <span className="block text-[13.5px] font-medium capitalize text-ink">{p.tipo}</span>
                      <span className="block truncate font-mono text-[11px] text-ink-3">{JSON.stringify(p.parametros)}</span>
                      <span className="block text-[11.5px] text-ink-3">{haceCuanto(p.creado_en)} · {p.solicitado_por}</span>
                    </span>
                    <span className="flex shrink-0 flex-col items-end gap-1">
                      <ChipEstado mapa={ESTADOS_PROCESO} valor={p.estado} />
                      {p.progreso !== null && p.progreso !== undefined && (
                        <span className="h-1 w-20 overflow-hidden rounded-full bg-surface-3">
                          <span className="block h-full rounded-full bg-accent" style={{ width: `${p.progreso * 100}%` }} />
                        </span>
                      )}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </Tarjeta>
          {activo && (
            <div className="space-y-3">
              <Bitacora proceso={activo} />
              <p className="text-[12px] text-ink-3">
                Creado {fechaHora(activo.creado_en)}
                {activo.trabajador && ` · trabajador ${activo.trabajador}`}
                {activo.expediente_id && ` · expediente ${activo.expediente_id}`}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
