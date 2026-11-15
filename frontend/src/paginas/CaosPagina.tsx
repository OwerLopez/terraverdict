import { Orbit } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import type { Esquemas } from "../api/cliente";
import { useExpedienteVigente } from "../api/consultas";
import { TablaDatos } from "../componentes/fenomenos/TablaDatos";
import { Dato, Encabezado, ErrorCarga, EstadoVacio, Esqueleto, Insignia, Tarjeta, type Tono } from "../componentes/ui";
import { RAMPA_AZUL } from "../lib/colores";
import { numero } from "../lib/formato";

type Serie = Esquemas["SerieDinamica"];

export const VEREDICTOS_DINAMICA: Record<string, { texto: string; tono: Tono }> = {
  lineal_estocastica: { texto: "Lineal estocástica", tono: "neutral" },
  no_lineal_sin_caos_demostrado: { texto: "No lineal, sin caos demostrado", tono: "accent" },
  compatible_con_caos_baja_dimension: { texto: "Compatible con caos de baja dimensión", tono: "warning" },
  regular: { texto: "Regular", tono: "good" },
  insuficiente: { texto: "Datos insuficientes", tono: "neutral" },
};

const ESTADISTICOS: Record<string, string> = {
  asimetria_temporal: "Asimetría temporal",
  error_prediccion_analogos: "Error de predicción por análogos",
};
const nombreEstadistico = (e: string) => ESTADISTICOS[e] ?? e.replace(/_/g, " ");

const CONDICIONES: Record<string, string> = {
  no_linealidad_significativa: "No linealidad significativa (sustitutos IAAFT)",
  determinismo_prediccion_analogos: "Determinismo (predicción por análogos)",
  d2_satura_bajo: "D2 satura por debajo de 5",
  lyapunov_positivo: "Exponente de Lyapunov > 0",
  prueba_01_caotica: "Prueba 0-1: K > 0,8",
};

function EspacioFases({ puntos, tau }: { puntos: [number, number][]; tau: number | null | undefined }) {
  const lado = 320;
  const m = 28;
  const lim = Math.max(3, ...puntos.flatMap(([a, b]) => [Math.abs(a), Math.abs(b)]));
  const e = (v: number) => m + ((v + lim) / (2 * lim)) * (lado - 2 * m);
  return (
    <svg viewBox={`0 0 ${lado} ${lado}`} className="mx-auto w-full max-w-[360px]" role="img" aria-label={`Espacio de fases reconstruido: x(t) frente a x(t+τ) con τ = ${tau ?? "—"}, ${puntos.length} puntos`}>
      <rect x={m} y={m} width={lado - 2 * m} height={lado - 2 * m} fill="none" stroke="var(--border-strong)" rx={6} />
      <line x1={e(0)} x2={e(0)} y1={m} y2={lado - m} stroke="var(--grid)" />
      <line y1={lado - e(0)} y2={lado - e(0)} x1={m} x2={lado - m} stroke="var(--grid)" />
      {puntos.map(([a, b], i) => (
        <circle key={i} cx={e(a)} cy={lado - e(b)} r={1.6} fill="var(--serie-1)" fillOpacity={0.45} />
      ))}
      <text x={lado / 2} y={lado - 6} textAnchor="middle" fontSize={11} fill="var(--ink-3)">x(t), estandarizada</text>
      <text x={10} y={lado / 2} textAnchor="middle" fontSize={11} fill="var(--ink-3)" transform={`rotate(-90 10 ${lado / 2})`}>x(t + τ)</text>
    </svg>
  );
}

/** Gráfico de recurrencia: densidad de recurrencias por bloque, rampa azul secuencial. */
function Recurrencia({ matriz }: { matriz: number[][] }) {
  const lienzo = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const c = lienzo.current;
    const n = matriz.length;
    if (!c || n === 0) return;
    c.width = n;
    c.height = n;
    const ctx = c.getContext("2d");
    if (!ctx) return;
    const max = Math.max(...matriz.flat(), 1e-9);
    matriz.forEach((fila, i) =>
      fila.forEach((v, j) => {
        const paso = Math.min(RAMPA_AZUL.length - 1, Math.floor((v / max) * RAMPA_AZUL.length));
        ctx.fillStyle = v === 0 ? "rgba(0,0,0,0)" : (RAMPA_AZUL[paso] ?? RAMPA_AZUL[6]);
        ctx.fillRect(j, n - 1 - i, 1, 1);
      }),
    );
  }, [matriz]);
  return (
    <canvas
      ref={lienzo}
      role="img"
      aria-label={`Gráfico de recurrencia de ${matriz.length} × ${matriz.length} bloques; más oscuro = más recurrencias`}
      className="mx-auto aspect-square w-full max-w-[320px] rounded-lg border border-line"
      style={{ imageRendering: "pixelated" }}
    />
  );
}

/** Histograma del estadístico en los sustitutos, con el valor de la serie original. */
function Sustitutos({ d }: { d: Esquemas["DistribucionSustitutos"] }) {
  const ancho = 320;
  const alto = 150;
  const valores = [...d.sustitutos, d.original];
  const min = Math.min(...valores);
  const max = Math.max(...valores);
  const nb = 16;
  const paso = (max - min) / nb || 1;
  const conteos = Array.from({ length: nb }, (_, i) => d.sustitutos.filter((v) => v >= min + i * paso && (i === nb - 1 ? v <= max : v < min + (i + 1) * paso)).length);
  const cmax = Math.max(...conteos, 1);
  const x = (v: number) => 8 + ((v - min) / (max - min || 1)) * (ancho - 16);
  const anchoBarra = (ancho - 16) / nb;
  return (
    <svg viewBox={`0 0 ${ancho} ${alto + 18}`} className="w-full" role="img" aria-label={`Distribución de ${nombreEstadistico(d.estadistico).toLowerCase()} en ${d.sustitutos.length} sustitutos; la serie original vale ${numero(d.original, 3)} (p = ${numero(d.p, 3)})`}>
      {conteos.map((c, i) => (
        <rect key={i} x={8 + i * anchoBarra + 1} y={alto - (c / cmax) * (alto - 10)} width={anchoBarra - 2} height={(c / cmax) * (alto - 10)} rx={2} fill="var(--serie-1)" fillOpacity={0.55} />
      ))}
      <line x1={x(d.original)} x2={x(d.original)} y1={4} y2={alto} stroke="var(--ink)" strokeWidth={2} strokeDasharray="4 3" />
      <text x={Math.min(x(d.original) + 4, ancho - 60)} y={14} fontSize={11} fill="var(--ink)">original</text>
      <text x={8} y={alto + 14} fontSize={10.5} fill="var(--ink-3)">{numero(min, 3)}</text>
      <text x={ancho - 8} y={alto + 14} fontSize={10.5} fill="var(--ink-3)" textAnchor="end">{numero(max, 3)}</text>
    </svg>
  );
}

export function CaosPagina() {
  const { detalle } = useExpedienteVigente("caos");
  const r = detalle.data?.resultado.tipo === "caos" ? (detalle.data.resultado as Esquemas["ResultadoCaos"]) : undefined;
  const [elegida, setElegida] = useState<string | null>(null);
  const serie: Serie | undefined = useMemo(() => r?.series.find((s) => s.serie_id === elegida) ?? r?.series[0], [r, elegida]);
  const v = serie ? VEREDICTOS_DINAMICA[serie.veredicto] : undefined;

  return (
    <>
      <Encabezado
        eyebrow="Fenómenos naturales"
        titulo="Dinámica: ¿caos, no linealidad o ruido?"
        descripcion="Diagnóstico de cada serie real con sustitutos IAAFT, dimensión de correlación, exponente de Lyapunov, prueba 0-1 y recurrencias. Afirmar caos exige todas las condiciones a la vez."
      />
      {detalle.isError && <ErrorCarga error={detalle.error} className="mb-4" />}
      {detalle.isLoading && <Esqueleto className="h-80" />}
      {!detalle.isLoading && !r && <EstadoVacio icono={Orbit} titulo="Sin diagnóstico publicado">Publique los resultados con <code>tv publicar</code>.</EstadoVacio>}
      {r && serie && (
        <>
          <div className="mb-5 flex flex-wrap gap-2" role="tablist" aria-label="Series evaluadas">
            {r.series.map((s) => (
              <button
                key={s.serie_id}
                type="button"
                role="tab"
                aria-selected={s.serie_id === serie.serie_id}
                onClick={() => setElegida(s.serie_id)}
                className={
                  s.serie_id === serie.serie_id
                    ? "panel-vidrio rounded-full px-3.5 py-1.5 text-[13px] font-semibold text-accent-ink ring-2 ring-accent"
                    : "panel-vidrio rounded-full px-3.5 py-1.5 text-[13px] font-medium text-ink-2 hover:text-ink"
                }
              >
                {s.serie_id.replace(/_/g, " ")}
              </button>
            ))}
          </div>
          <div className="mb-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Dato etiqueta="Veredicto" valor={<span className="text-[18px]">{v?.texto ?? serie.veredicto}</span>} nota={`${serie.fuente} · n = ${numero(serie.n, 0)} (${serie.unidad_tiempo})`} />
            <Dato etiqueta="Dimensión D2" valor={serie.d2 != null ? numero(serie.d2, 2) : "no satura"} nota={`Embedding: τ = ${serie.tau ?? "—"}, m = ${serie.m ?? "—"}`} />
            <Dato etiqueta="Lyapunov λ" valor={numero(serie.lyapunov, 3)} nota={`por ${serie.unidad_tiempo}`} />
            <Dato etiqueta="Prueba 0-1 (K)" valor={numero(serie.k_01, 2)} nota="≈ 0 regular · ≈ 1 caótica o estocástica" />
          </div>
          <div className="grid gap-5 lg:grid-cols-3">
            <Tarjeta titulo="Espacio de fases" subtitulo="Reconstrucción de Takens (submuestra).">
              {serie.espacio_fases?.length ? <EspacioFases puntos={serie.espacio_fases as [number, number][]} tau={serie.tau} /> : <EstadoVacio titulo="Sin puntos" />}
              <TablaDatos titulo="Espacio de fases" columnas={["x(t)", "x(t+τ)"]} filas={(serie.espacio_fases ?? []).map(([a, b]) => [numero(a, 3), numero(b, 3)])} maxFilas={200} />
            </Tarjeta>
            <Tarjeta titulo="Gráfico de recurrencia" subtitulo="Densidad por bloque; diagonales largas indican determinismo.">
              {serie.recurrencia_miniatura?.length ? <Recurrencia matriz={serie.recurrencia_miniatura} /> : <EstadoVacio titulo="Sin datos de recurrencia" />}
              <p className="mt-2 text-center text-[12px] text-ink-3">Determinismo (RQA): {numero(serie.determinismo_rqa, 3)}</p>
            </Tarjeta>
            <Tarjeta titulo="Frente a los sustitutos" subtitulo="Si la serie original cae dentro de la nube de sustitutos lineales, no hay evidencia de no linealidad.">
              {serie.sustitutos?.length ? (
                <div className="space-y-4">
                  {serie.sustitutos.map((d) => (
                    <div key={d.estadistico}>
                      <p className="mb-1 text-[12.5px] font-medium text-ink-2">
                        {nombreEstadistico(d.estadistico)} · p = {numero(d.p, 3)}
                      </p>
                      <Sustitutos d={d} />
                    </div>
                  ))}
                </div>
              ) : (
                <EstadoVacio titulo="Sin sustitutos (serie insuficiente)" />
              )}
              <TablaDatos
                titulo="Estadísticos frente a sustitutos"
                columnas={["Estadístico", "Original", "Sustitutos (n)", "p"]}
                filas={(serie.sustitutos ?? []).map((d) => [nombreEstadistico(d.estadistico), numero(d.original, 4), d.sustitutos.length, numero(d.p, 3)])}
              />
            </Tarjeta>
          </div>
          <Tarjeta titulo="Condiciones para afirmar caos" className="mt-5" pie={<>Fuente: expediente <Link className="font-mono text-accent-ink hover:underline" to={`/expedientes/${detalle.data?.id}`}>{detalle.data?.id}</Link></>}>
            <ul className="grid gap-2 text-[13px] sm:grid-cols-2">
              {Object.entries(CONDICIONES).map(([k, texto]) => {
                const ok = serie.condiciones?.[k];
                return (
                  <li key={k} className="flex items-center gap-2">
                    <Insignia tono={ok ? "good" : "neutral"}>{ok ? "Se cumple" : ok === false ? "No se cumple" : "No evaluada"}</Insignia>
                    <span className="text-ink-2">{texto}</span>
                  </li>
                );
              })}
            </ul>
          </Tarjeta>
        </>
      )}
    </>
  );
}
