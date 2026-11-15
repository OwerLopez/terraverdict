import { Layers3, ShieldAlert } from "lucide-react";
import { useFenomenos } from "../api/consultas";
import { Encabezado, ErrorCarga, Esqueleto, Insignia, Tarjeta, type Tono } from "../componentes/ui";
import { t } from "../lib/i18n";

const TONO_RELEVANCIA: Record<string, Tono> = { alta: "accent", media: "neutral", baja: "neutral" };
const PARTES: Record<string, [string, string]> = { entrenamiento: ["Entrenamiento", "Training"], validacion: ["Validación", "Validation"], prueba: ["Prueba", "Test"] };
const RELEVANCIA: Record<string, [string, string]> = { alta: ["alta", "high"], media: ["media", "medium"], baja: ["baja", "low"] };
const ESTADO_ACCESO: Record<string, { texto: [string, string]; tono: Tono }> = {
  api_publica: { texto: ["API pública", "Public API"], tono: "good" },
  portal: { texto: ["Portal sin API", "Portal without API"], tono: "warning" },
  no_accesible: { texto: ["No accesible", "Not accessible"], tono: "critical" },
};

export function FenomenosPagina() {
  const consulta = useFenomenos();
  const c = consulta.data;
  return (
    <>
      <Encabezado
        eyebrow={t("Fenómenos naturales", "Natural hazards")}
        titulo={t("Catálogo científico", "Scientific catalog")}
        descripcion={t("Cada variable entra con una razón física, su fuente y sus limitaciones. El sistema elige entre ellas con información mutua y este prior; no acumula datos sin criterio. Las justificaciones del catálogo están en español, su idioma de origen.", "Each variable enters with a physical reason, its source and its limitations. The system chooses among them with mutual information and this prior; it does not pile up data blindly. Catalog justifications are in Spanish, their original language.")}
      />
      {consulta.isError && <ErrorCarga error={consulta.error} />}
      {consulta.isLoading && <Esqueleto className="h-64" />}
      {c && (
        <div className="space-y-5">
          <Tarjeta titulo={t("Reglas comunes", "Common rules")} subtitulo={t(`Catálogo versión ${c.version}, verificado el ${c.verificado}.`, `Catalog version ${c.version}, verified on ${c.verificado}.`)}>
            <dl className="grid gap-3 text-[13px] sm:grid-cols-3">
              {Object.entries(c.particion_temporal).map(([parte, [desde, hasta]]) => (
                <div key={parte} className="rounded-xl bg-surface-2 p-3">
                  <dt className="etiqueta">{PARTES[parte] ? t(...(PARTES[parte] as [string, string])) : parte}</dt>
                  <dd className="cifra mt-1 font-medium text-ink">
                    {desde} → {hasta}
                  </dd>
                </div>
              ))}
            </dl>
            <p className="mt-3 text-[13px] text-ink-2">
              {t("La prueba se usa una sola vez. Mínimo de habilidad en validación para publicar:", "The test set is used only once. Minimum validation skill to publish:")}{" "}
              <span className="cifra font-medium">{c.abstencion.skill_minimo_validacion}</span>; {t("eventos mínimos para estimar un umbral:", "minimum events to estimate a threshold:")} <span className="cifra font-medium">{c.abstencion.eventos_minimos_umbral}</span>.
            </p>
          </Tarjeta>

          {c.fenomenos.map((f) => (
            <Tarjeta key={f.id} titulo={f.nombre} subtitulo={f.procesos}>
              <p className="mb-3 text-[13px] text-ink-2">
                <span className="font-semibold text-ink">{t("Objetivo", "Target")}: </span>
                {String(f.objetivo.tarea ?? "")}
                {f.objetivo.advertencia ? (
                  <span className="mt-1 flex items-start gap-1.5 text-ink">
                    <ShieldAlert aria-hidden className="mt-0.5 h-3.5 w-3.5 shrink-0" style={{ color: "var(--warning)" }} />
                    {String(f.objetivo.advertencia)}
                  </span>
                ) : null}
              </p>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[720px] border-collapse text-left text-[13px]">
                  <caption className="sr-only">{t("Variables de", "Variables of")} {f.nombre}</caption>
                  <thead>
                    <tr className="border-b border-line text-ink-3">
                      <th scope="col" className="py-2 pr-3 font-semibold">{t("Variable", "Variable")}</th>
                      <th scope="col" className="py-2 pr-3 font-semibold">{t("Relevancia", "Relevance")}</th>
                      <th scope="col" className="py-2 pr-3 font-semibold">{t("Fuente", "Source")}</th>
                      <th scope="col" className="py-2 pr-3 font-semibold">{t("Justificación física", "Physical justification")}</th>
                      <th scope="col" className="py-2 font-semibold">{t("Limitaciones", "Limitations")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {f.variables.map((v) => (
                      <tr key={v.id} className="border-b border-line align-top last:border-0">
                        <th scope="row" className="py-2 pr-3 font-medium text-ink">
                          {v.nombre}
                          {v.unidad && <span className="ml-1 font-normal text-ink-3">({v.unidad})</span>}
                        </th>
                        <td className="py-2 pr-3">
                          {v.relevancia ? <Insignia tono={TONO_RELEVANCIA[v.relevancia] ?? "neutral"}>{RELEVANCIA[v.relevancia] ? t(...(RELEVANCIA[v.relevancia] as [string, string])) : v.relevancia}</Insignia> : "—"}
                        </td>
                        <td className="py-2 pr-3 font-mono text-[12px] text-ink-2">{v.fuente ?? "—"}</td>
                        <td className="py-2 pr-3 text-ink-2">{v.justificacion}</td>
                        <td className="py-2 text-ink-3">{v.limitaciones ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="mt-3 text-[12px] text-ink-3">{t("Métricas", "Metrics")}: {f.metricas.join(", ")}.</p>
            </Tarjeta>
          ))}

          <Tarjeta
            titulo={t("Fuentes nacionales", "National sources")}
            subtitulo={c.via_integracion_nacional ?? undefined}
            acciones={<Layers3 aria-hidden className="h-4 w-4 text-ink-3" />}
          >
            <ul className="divide-y divide-line text-[13px]">
              {Object.entries(c.acceso_fuentes_nacionales).map(([nombre, a]) => {
                const def = ESTADO_ACCESO[a.estado ?? ""];
                const e = def ? { texto: t(...def.texto), tono: def.tono } : { texto: a.estado ?? "—", tono: "neutral" as Tono };
                return (
                  <li key={nombre} className="flex flex-col gap-1 py-2 sm:flex-row sm:items-center sm:gap-3">
                    <span className="w-28 shrink-0 font-semibold text-ink">{nombre}</span>
                    <Insignia tono={e.tono}>{e.texto}</Insignia>
                    <span className="text-ink-2">{a.motivo}</span>
                  </li>
                );
              })}
            </ul>
          </Tarjeta>
        </div>
      )}
    </>
  );
}
