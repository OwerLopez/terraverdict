import { BrainCircuit, CheckCircle2, ShieldAlert } from "lucide-react";
import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import type { Esquemas } from "../api/cliente";
import { useExpedienteVigente, useExpedientes } from "../api/consultas";
import { TablaDatos } from "../componentes/fenomenos/TablaDatos";
import { Dato, Encabezado, ErrorCarga, EstadoVacio, Esqueleto, Insignia, Tarjeta } from "../componentes/ui";
import { numero, valorP } from "../lib/formato";
import { t } from "../lib/i18n";
import { UMBRAL_P_DM, evidencia as reglaEvidencia } from "../lib/modelos";

type Comparacion = Esquemas["ResultadoComparacionModelos"];
type Modelo = Esquemas["ModeloEvaluado"];

const METRICAS: Record<string, [string, string]> = {
  bss_climatologia: ["Habilidad de Brier frente a la climatología", "Brier skill versus climatology"],
  habilidad_climatologia: ["Habilidad (1 − ECM / ECM climatológico)", "Skill (1 − MSE / climatological MSE)"],
  ganancia_informacion_bits: ["Ganancia de información frente a Poisson (bits/mes)", "Information gain versus Poisson (bits/month)"],
};
const FAMILIAS_ES_EN: Record<string, [string, string]> = { referencia: ["Referencia", "Reference"], clasico: ["Clásico", "Classical"], red_neuronal: ["Red neuronal", "Neural network"], ensamble: ["Ensamble", "Ensemble"] };
const familia = (f: string) => (FAMILIAS_ES_EN[f] ? t(...(FAMILIAS_ES_EN[f] as [string, string])) : f);

/**
 * Nivel de evidencia de la habilidad en prueba (regla del proyecto, docs/metodologia.md):
 * confirmada = IC90 por bootstrap > 0 Y Diebold-Mariano p < UMBRAL_P_DM; indicio = solo una de las dos.
 */
export function nivelEvidencia(m: { intervalo_prueba?: { lo: number } | null; p_diebold_mariano?: number | null }): "confirmada" | "indicio" | "no_confirmada" {
  return reglaEvidencia(m.intervalo_prueba?.lo, m.p_diebold_mariano);
}

/** Habilidad en prueba con IC90, un renglón por modelo; el elegido por validación va resaltado. */
function GraficoModelos({ modelos, elegido }: { modelos: Modelo[]; elegido: string }) {
  const [activo, setActivo] = useState<string | null>(null);
  const filas = [...modelos].sort((a, b) => b.puntaje_validacion - a.puntaje_validacion);
  const valores = filas.flatMap((m) => [m.puntaje_prueba ?? 0, m.intervalo_prueba?.lo ?? 0, m.intervalo_prueba?.hi ?? 0, 0]);
  const min = Math.min(...valores);
  const max = Math.max(...valores);
  const holgura = (max - min || 1) * 0.08;
  const ancho = 660;
  const izq = 180;
  const fila = 26;
  const alto = filas.length * fila + 30;
  const x = (v: number) => izq + ((v - (min - holgura)) / (max - min + 2 * holgura)) * (ancho - izq - 16);
  return (
    <svg viewBox={`0 0 ${ancho} ${alto}`} className="w-full" role="img" aria-label={t("Habilidad de cada modelo en el periodo de prueba con su intervalo de confianza del 90 %; la línea vertical marca la referencia (0)", "Each model's test-period skill with its 90 % confidence interval; the vertical line marks the reference (0)")}>
      <line x1={x(0)} x2={x(0)} y1={2} y2={alto - 24} stroke="var(--ink-3)" strokeDasharray="3 3" />
      <text x={x(0)} y={alto - 8} textAnchor="middle" fontSize={11} fill="var(--ink-3)">{t("0 = referencia", "0 = reference")}</text>
      {filas.map((m, i) => {
        const y = 4 + i * fila + fila / 2;
        const esElegido = m.nombre === elegido;
        const p = m.puntaje_prueba;
        return (
          <g
            key={m.nombre}
            tabIndex={0}
            className="outline-none"
            onMouseEnter={() => setActivo(m.nombre)}
            onMouseLeave={() => setActivo(null)}
            onFocus={() => setActivo(m.nombre)}
            onBlur={() => setActivo(null)}
            aria-label={`${m.nombre}: ${t("validación", "validation")} ${numero(m.puntaje_validacion, 3)}, ${t("prueba", "test")} ${numero(p, 3)}${m.intervalo_prueba ? `, ${t("IC90", "90 % CI")} ${numero(m.intervalo_prueba.lo, 3)} – ${numero(m.intervalo_prueba.hi, 3)}` : ""}`}
          >
            <rect x={0} y={y - fila / 2} width={ancho} height={fila} rx={6} fill={activo === m.nombre ? "var(--accent-soft)" : "transparent"} />
            <text x={izq - 10} y={y + 4} textAnchor="end" fontSize={12} fontWeight={esElegido ? 700 : 400} fill={m.familia === "referencia" ? "var(--ink-3)" : "var(--ink)"}>
              {m.nombre.replace(/_/g, " ")}
            </text>
            {m.intervalo_prueba && (
              <line x1={x(m.intervalo_prueba.lo)} x2={x(m.intervalo_prueba.hi)} y1={y} y2={y} stroke={esElegido ? "var(--accent)" : "var(--serie-1)"} strokeOpacity={esElegido ? 1 : 0.55} strokeWidth={2} strokeLinecap="round" />
            )}
            {p != null && (
              <circle cx={x(p)} cy={y} r={esElegido ? 6 : 4.5} fill={esElegido ? "var(--accent)" : m.familia === "referencia" ? "var(--ink-3)" : "var(--serie-1)"} stroke="var(--surface-solida)" strokeWidth={2} />
            )}
            {activo === m.nombre && p != null && (
              <text x={ancho - 8} y={y + 4} textAnchor="end" fontSize={11.5} fill="var(--ink-2)" className="cifra">
                {numero(p, 3)}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}

function Confiabilidad({ puntos, ece }: { puntos: Esquemas["PuntoConfiabilidad"][]; ece: number | null | undefined }) {
  const lado = 280;
  const m = 30;
  const maximo = Math.max(0.05, ...puntos.flatMap((p) => [p.pronosticada, p.observada])) * 1.1;
  const e = (v: number) => m + (v / maximo) * (lado - 2 * m);
  return (
    <svg viewBox={`0 0 ${lado} ${lado}`} className="mx-auto w-full max-w-[320px]" role="img" aria-label={t(`Diagrama de confiabilidad con ${puntos.length} grupos; error de calibración esperado ${numero(ece, 3)}`, `Reliability diagram with ${puntos.length} bins; expected calibration error ${numero(ece, 3)}`)}>
      <rect x={m} y={m} width={lado - 2 * m} height={lado - 2 * m} fill="none" stroke="var(--border-strong)" rx={6} />
      <line x1={e(0)} y1={lado - e(0)} x2={e(maximo)} y2={lado - e(maximo)} stroke="var(--ink-3)" strokeDasharray="4 3" />
      <polyline points={puntos.map((p) => `${e(p.pronosticada)},${lado - e(p.observada)}`).join(" ")} fill="none" stroke="var(--serie-1)" strokeWidth={2} />
      {puntos.map((p, i) => (
        <circle key={i} cx={e(p.pronosticada)} cy={lado - e(p.observada)} r={4.5} fill="var(--serie-1)" stroke="var(--surface-solida)" strokeWidth={2}>
          <title>{t(`Pronosticada ${numero(p.pronosticada, 3)} · observada ${numero(p.observada, 3)} · n = ${p.n}`, `Forecast ${numero(p.pronosticada, 3)} · observed ${numero(p.observada, 3)} · n = ${p.n}`)}</title>
        </circle>
      ))}
      <text x={lado / 2} y={lado - 8} textAnchor="middle" fontSize={11} fill="var(--ink-3)">{t("Probabilidad pronosticada", "Forecast probability")}</text>
      <text x={12} y={lado / 2} textAnchor="middle" fontSize={11} fill="var(--ink-3)" transform={`rotate(-90 12 ${lado / 2})`}>{t("Frecuencia observada", "Observed frequency")}</text>
    </svg>
  );
}

function Importancia({ datos }: { datos: Esquemas["ImportanciaVariable"][] }) {
  const max = Math.max(...datos.map((d) => Math.abs(d.importancia)), 1e-12);
  return (
    <ul className="space-y-2" aria-label={t("Importancia por permutación (aumento de la pérdida al permutar cada variable)", "Permutation importance (loss increase when permuting each variable)")}>
      {datos.map((d) => (
        <li key={d.variable} className="grid grid-cols-[150px_1fr_70px] items-center gap-3 text-[12.5px]">
          <span className="truncate text-ink-2" title={d.variable}>{d.variable.replace(/_/g, " ")}</span>
          <span className="h-2.5 rounded-full bg-surface-3">
            <span className="block h-full rounded-full" style={{ width: `${Math.max(0, d.importancia / max) * 100}%`, background: "var(--serie-1)" }} />
          </span>
          <span className="cifra text-right text-ink">{numero(d.importancia, 4)}</span>
        </li>
      ))}
    </ul>
  );
}

export function ModelosPagina() {
  const [params, setParams] = useSearchParams();
  const lista = useExpedientes({ tipo: "comparacion_modelos" });
  const { detalle, elegido } = useExpedienteVigente("comparacion_modelos", params.get("id") ?? undefined);
  const r = detalle.data?.resultado.tipo === "comparacion_modelos" ? (detalle.data.resultado as Comparacion) : undefined;
  const mejor = r?.modelos.find((m) => m.nombre === r.mejor_validacion);
  const evidencia = mejor ? nivelEvidencia(mejor) : "no_confirmada";

  return (
    <>
      <Encabezado
        eyebrow={t("Fenómenos naturales", "Natural hazards")}
        titulo={t("Comparación de modelos", "Model comparison")}
        descripcion={t("Referencias, modelos clásicos, redes neuronales y ensambles. Todo se elige en validación (calibración y ensambles puntuados fuera de pliegue); el periodo de prueba se usa una sola vez y solo informa.", "References, classical models, neural networks and ensembles. Everything is chosen on validation (calibration and ensembles scored out of fold); the test period is used once and only reports.")}
      />
      {lista.isError && <ErrorCarga error={lista.error} className="mb-4" />}
      {lista.isLoading && <Esqueleto className="h-12" />}
      {lista.data && lista.data.items.length === 0 && <EstadoVacio icono={BrainCircuit} titulo={t("Sin comparaciones publicadas", "No published comparisons")}>{t("Publique los resultados con", "Publish the results with")} <code>tv publicar</code>.</EstadoVacio>}
      {lista.data && lista.data.items.length > 0 && (
        <label className="mb-5 block max-w-xl text-[13px] font-medium text-ink-2">
          {t("Tarea", "Task")}
          <select
            value={elegido ?? ""}
            onChange={(e) => setParams({ id: e.target.value })}
            className="panel-vidrio mt-1 block h-10 w-full rounded-xl px-3 text-[14px] text-ink outline-none focus:ring-2 focus:ring-accent"
          >
            {lista.data.items.map((e) => (
              <option key={e.id} value={e.id}>{e.titulo}</option>
            ))}
          </select>
        </label>
      )}
      {detalle.isLoading && elegido && <Esqueleto className="h-80" />}
      {r && mejor && (
        <>
          <div className="mb-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Dato etiqueta={t("Modelo elegido (validación)", "Chosen model (validation)")} valor={<span className="text-[20px]">{mejor.nombre.replace(/_/g, " ")}</span>} nota={familia(mejor.familia)} icono={BrainCircuit} />
            <Dato etiqueta={t("Habilidad en prueba", "Test skill")} valor={numero(mejor.puntaje_prueba, 3)} nota={mejor.intervalo_prueba ? `${t("IC90", "90 % CI")} ${numero(mejor.intervalo_prueba.lo, 3)} – ${numero(mejor.intervalo_prueba.hi, 3)}` : t("sin IC", "no CI")} />
            <Dato etiqueta="Diebold-Mariano" valor={valorP(mejor.p_diebold_mariano)} nota={t("p frente a la climatología en prueba", "p versus climatology on test")} />
            <Dato
              etiqueta={t("Publicación", "Publication")}
              valor={<span className="text-[18px]">{r.abstencion.publicar ? t("Se publica", "Published") : t("Abstención", "Abstention")}</span>}
              nota={evidencia === "confirmada" ? t(`Habilidad confirmada: IC90 > 0 y Diebold-Mariano p < ${numero(UMBRAL_P_DM, 2)}`, `Skill confirmed: 90 % CI > 0 and Diebold-Mariano p < ${numero(UMBRAL_P_DM, 2)}`) : evidencia === "indicio" ? t(`Solo indicio: cumple una de las dos pruebas (IC90 > 0 o DM p < ${numero(UMBRAL_P_DM, 2)})`, `Indication only: meets one of the two tests (90 % CI > 0 or DM p < ${numero(UMBRAL_P_DM, 2)})`) : t("Habilidad no confirmada en prueba", "Skill not confirmed on test")}
              icono={r.abstencion.publicar ? CheckCircle2 : ShieldAlert}
              tono={r.abstencion.publicar ? "good" : "warning"}
            />
          </div>
          <div className="grid gap-5 xl:grid-cols-[1.5fr_1fr]">
            <Tarjeta
              titulo={METRICAS[r.metrica_principal] ? t(...(METRICAS[r.metrica_principal] as [string, string])) : r.metrica_principal}
              subtitulo={t(`${r.objetivo}. Horizonte: ${r.horizonte}. Prueba (fechas de emisión): ${r.periodo_prueba.desde} a ${r.periodo_prueba.hasta}. Ordenados por validación.`, `${r.objetivo}. Horizon: ${r.horizonte}. Test (issue dates): ${r.periodo_prueba.desde} to ${r.periodo_prueba.hasta}. Sorted by validation.`)}
              pie={<>{t("Fuente: expediente", "Source: case file")} <Link className="font-mono text-accent-ink hover:underline" to={`/expedientes/${detalle.data?.id}`}>{detalle.data?.id}</Link></>}
            >
              <div className="overflow-x-auto">
                <div className="min-w-[560px] sm:min-w-0">
                  <GraficoModelos modelos={r.modelos} elegido={r.mejor_validacion} />
                </div>
              </div>
              <TablaDatos
                titulo={t("Modelos evaluados", "Evaluated models")}
                columnas={[t("Modelo", "Model"), t("Familia", "Family"), t("Validación", "Validation"), t("Prueba", "Test"), t("IC90 prueba", "Test 90 % CI"), t("p DM", "DM p"), t("Dispersión entre semillas", "Spread across seeds")]}
                filas={[...r.modelos]
                  .sort((a, b) => b.puntaje_validacion - a.puntaje_validacion)
                  .map((m) => [
                    m.nombre,
                    familia(m.familia),
                    numero(m.puntaje_validacion, 3),
                    numero(m.puntaje_prueba, 3),
                    m.intervalo_prueba ? `${numero(m.intervalo_prueba.lo, 3)} – ${numero(m.intervalo_prueba.hi, 3)}` : "—",
                    valorP(m.p_diebold_mariano),
                    numero(m.dispersion_semillas, 4),
                  ])}
              />
            </Tarjeta>
            <div className="space-y-5">
              {r.confiabilidad && r.confiabilidad.length > 0 && (
                <Tarjeta titulo={t("Confiabilidad (prueba)", "Reliability (test)")} subtitulo={t(`Sobre la diagonal, las probabilidades significan lo que dicen. ECE = ${numero(r.ece, 3)}.`, `On the diagonal, probabilities mean what they say. ECE = ${numero(r.ece, 3)}.`)}>
                  <Confiabilidad puntos={r.confiabilidad} ece={r.ece} />
                  <TablaDatos titulo={t("Curva de confiabilidad", "Reliability curve")} columnas={[t("Pronosticada", "Forecast"), t("Observada", "Observed"), "n"]} filas={r.confiabilidad.map((p) => [numero(p.pronosticada, 3), numero(p.observada, 3), p.n])} />
                </Tarjeta>
              )}
              {r.cobertura_conformal_90 != null && (
                <Tarjeta titulo={t("Incertidumbre", "Uncertainty")} subtitulo={t("Intervalo conformal del 90 % calibrado en validación.", "90 % conformal interval calibrated on validation.")}>
                  <p className="text-[13px] text-ink-2">
                    {t("Cobertura medida en prueba", "Measured test coverage")}: <span className="cifra text-[20px] font-semibold text-ink">{numero(r.cobertura_conformal_90 * 100, 1)} %</span>{" "}
                    {t("(nominal 90 %). Con series temporales la garantía es aproximada; por eso se mide.", "(nominal 90 %). With time series the guarantee is approximate; that is why it is measured.")}
                  </p>
                </Tarjeta>
              )}
              {r.importancia && r.importancia.length > 0 && (
                <Tarjeta titulo={t("Importancia de variables", "Variable importance")} subtitulo={t("Permutación en validación (gradient boosting).", "Permutation on validation (gradient boosting).")}>
                  <Importancia datos={r.importancia} />
                </Tarjeta>
              )}
              <Tarjeta titulo={t("Decisión de publicación", "Publication decision")}>
                <ul className="space-y-1.5 text-[13px] text-ink-2">
                  {(r.abstencion.motivos ?? []).map((m) => (
                    <li key={m} className="flex gap-2"><Insignia tono="warning">{t("Motivo", "Reason")}</Insignia>{m}</li>
                  ))}
                  {(r.abstencion.advertencias ?? []).map((m) => (
                    <li key={m} className="flex gap-2"><Insignia tono="neutral">{t("Advertencia", "Warning")}</Insignia>{m}</li>
                  ))}
                  {r.abstencion.publicar && (r.abstencion.advertencias ?? []).length === 0 && <li>{t("Supera a la referencia en validación; sin advertencias.", "Beats the reference on validation; no warnings.")}</li>}
                </ul>
                {r.variables_seleccionadas && r.variables_seleccionadas.length > 0 && (
                  <p className="mt-3 text-[12.5px] text-ink-3">
                    {t("Variables (mRMR)", "Variables (mRMR)")}: {r.variables_seleccionadas.join(", ")} · {t("ventana", "window")} {r.ventana}
                  </p>
                )}
              </Tarjeta>
            </div>
          </div>
          {r.ablaciones && r.ablaciones.length > 0 && (
            <Tarjeta titulo={t("Ablaciones", "Ablations")} subtitulo={t("Mejor modelo de cada conjunto de variables (misma ventana).", "Best model for each variable set (same window).")} className="mt-5">
              <TablaDatos
                titulo={t("Ablaciones", "Ablations")}
                columnas={[t("Conjunto", "Set"), t("Variables", "Variables"), t("Validación", "Validation"), t("Prueba", "Test")]}
                filas={r.ablaciones.map((a) => [a.nombre.replace(/_/g, " "), a.variables.join(", "), numero(a.mejor_validacion, 3), numero(a.mejor_prueba, 3)])}
              />
            </Tarjeta>
          )}
        </>
      )}
    </>
  );
}
