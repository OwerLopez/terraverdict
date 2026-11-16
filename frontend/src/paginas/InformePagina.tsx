/**
 * Informe ejecutivo de 2 páginas, imprimible como PDF, generado con los datos reales de un expediente.
 *
 * - Página 1: veredicto para la decisión, cifras clave, incertidumbre y limitaciones.
 * - Página 2: fuentes, procedencia (código, commit, hashes) y pasos del proceso.
 * Con `?imprimir=1` abre el diálogo de impresión ("Guardar como PDF") al terminar de cargar.
 * No usa logotipos de NASA ni de otras instituciones: no es una publicación oficial de ninguna de ellas.
 */
import { ArrowLeft, Printer } from "lucide-react";
import { useEffect } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import type { Esquemas } from "../api/cliente";
import { useExpediente } from "../api/consultas";
import { Boton, ErrorCarga, Esqueleto } from "../componentes/ui";
import { fechaHora, numero, valorP } from "../lib/formato";
import { t } from "../lib/i18n";
import { lecturaHabilidad, lecturaP } from "../lib/lectura";
import { traducirTitulo } from "../lib/titulos";

type Expediente = Esquemas["ExpedienteSalida"];
type Cifra = { etiqueta: string; valor: string; nota?: string };

/** Cifras clave según el tipo de resultado (sin inventar: solo campos del expediente). */
function cifrasClave(e: Expediente): { cifras: Cifra[]; veredicto: string; limitaciones: string[] } {
  const r = e.resultado as Record<string, unknown> & { tipo: string };
  const abst = (r.abstencion ?? {}) as { publicar?: boolean; motivos?: string[]; advertencias?: string[] };
  const limitaciones = [...(abst.motivos ?? []), ...(abst.advertencias ?? [])];
  if (r.tipo === "comparacion_modelos") {
    const c = r as unknown as Esquemas["ResultadoComparacionModelos"];
    const m = c.modelos.find((x) => x.nombre === c.mejor_validacion);
    const lo = m?.intervalo_prueba?.lo;
    const confirmada = lo != null && lo > 0 && (m?.p_diebold_mariano ?? 1) < 0.1;
    return {
      cifras: [
        { etiqueta: t("Modelo elegido en validación", "Model chosen on validation"), valor: m?.nombre ?? "—", nota: m?.familia },
        { etiqueta: t("Habilidad en prueba", "Test skill"), valor: numero(m?.puntaje_prueba, 3), nota: lecturaHabilidad(m?.puntaje_prueba, c.metrica_principal) ?? undefined },
        { etiqueta: "IC90", valor: m?.intervalo_prueba ? `${numero(m.intervalo_prueba.lo, 3)} – ${numero(m.intervalo_prueba.hi, 3)}` : "—" },
        { etiqueta: "p Diebold-Mariano", valor: valorP(m?.p_diebold_mariano), nota: lecturaP(m?.p_diebold_mariano) ?? undefined },
        { etiqueta: t("Horizonte", "Horizon"), valor: c.horizonte, nota: `${t("prueba", "test")} ${c.periodo_prueba.desde} – ${c.periodo_prueba.hasta}` },
      ],
      veredicto: !c.abstencion.publicar
        ? t("Abstención: el modelo no se publica como herramienta de decisión.", "Abstention: the model is not published as a decision tool.")
        : confirmada
          ? t("Habilidad confirmada fuera de muestra: utilizable como apoyo a la vigilancia, junto con los avisos oficiales.", "Skill confirmed out of sample: usable to support monitoring, alongside official warnings.")
          : t("Solo indicio de habilidad: útil para vigilancia, no para disparar alertas.", "Indication of skill only: useful for monitoring, not to trigger warnings."),
      limitaciones,
    };
  }
  if (r.tipo === "tendencia") {
    const c = r as unknown as Esquemas["ResultadoTendencia"];
    return {
      cifras: [
        { etiqueta: t("Pendiente de Sen", "Sen slope"), valor: `${numero(c.pendiente.valor, 2, { signo: true })} ${c.pendiente.unidad}` },
        { etiqueta: "IC90", valor: `${numero(c.pendiente.intervalo.lo, 2)} – ${numero(c.pendiente.intervalo.hi, 2)}` },
        { etiqueta: t("p conservador", "Conservative p"), valor: valorP(c.significancia.p_conservador) },
        { etiqueta: t("Periodo", "Period"), valor: `${c.periodo.desde}–${c.periodo.hasta}`, nota: `n = ${c.n}` },
      ],
      veredicto: t(`Veredicto del Sello de Confianza: ${c.veredicto}.`, `Confidence Seal verdict: ${c.veredicto}.`),
      limitaciones,
    };
  }
  if (r.tipo === "sismicidad") {
    const c = r as unknown as Esquemas["ResultadoSismicidad"];
    return {
      cifras: [
        { etiqueta: t("Valor b", "b-value"), valor: numero(c.valor_b, 2), nota: `IC90 ${numero(c.intervalo_b.lo, 2)} – ${numero(c.intervalo_b.hi, 2)}` },
        { etiqueta: t("Eventos", "Events"), valor: numero(c.eventos, 0), nota: `Mc ${numero(c.mc, 1)}` },
        { etiqueta: t("Tasa anual ≥ Mc", "Annual rate ≥ Mc"), valor: numero(c.tasa_anual_mc, 1) },
      ],
      veredicto: t("Descripción estadística: no se pronostican sismos.", "Statistical description: earthquakes are not forecast."),
      limitaciones,
    };
  }
  if (r.tipo === "recurrencia") {
    const c = r as unknown as Esquemas["ResultadoRecurrencia"];
    return {
      cifras: c.volcanes.slice(0, 4).map((v) => ({ etiqueta: v.nombre, valor: `${numero(v.probabilidad_anual * 100, 1)} %/${t("año", "yr")}`, nota: `${v.erupciones} ${t("erupciones", "eruptions")} · IC90 ${numero(v.intervalo.lo * 100, 1)}–${numero(v.intervalo.hi * 100, 1)} %` })),
      veredicto: t("Frecuencia histórica, no un pronóstico de erupción.", "Historical frequency, not an eruption forecast."),
      limitaciones,
    };
  }
  if (r.tipo === "inventario") {
    const c = r as unknown as Esquemas["ResultadoInventario"];
    return {
      cifras: [{ etiqueta: t("Eventos documentados", "Documented events"), valor: numero(c.eventos.length, 0), nota: t(`mínimo para un umbral: ${c.eventos_minimos_umbral}`, `minimum for a threshold: ${c.eventos_minimos_umbral}`) }],
      veredicto: c.umbral_estimado ? t("Umbral de lluvia estimado.", "Rainfall threshold estimated.") : t("Abstención: datos insuficientes para un umbral.", "Abstention: insufficient data for a threshold."),
      limitaciones,
    };
  }
  return { cifras: [], veredicto: e.resumen, limitaciones };
}

export function InformePagina() {
  const { id } = useParams();
  const [params] = useSearchParams();
  const exp = useExpediente(id);
  const e = exp.data;
  useEffect(() => {
    if (e && params.get("imprimir") === "1") {
      const h = window.setTimeout(() => window.print(), 500);
      return () => window.clearTimeout(h);
    }
  }, [e, params]);
  if (exp.isLoading) return <Esqueleto className="h-[80vh]" />;
  if (exp.error || !e) return <ErrorCarga error={exp.error} />;
  const { cifras, veredicto, limitaciones } = cifrasClave(e);
  const p = e.procedencia;
  const hoy = new Date().toISOString().slice(0, 16).replace("T", " ");

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2 print:hidden">
        <Link to={`/expedientes/${e.id}`} className="inline-flex items-center gap-1.5 text-[13px] text-ink-2 hover:text-ink"><ArrowLeft className="h-4 w-4" /> {e.id}</Link>
        <Boton variante="primario" icono={Printer} onClick={() => window.print()}>{t("Guardar como PDF (2 páginas)", "Save as PDF (2 pages)")}</Boton>
      </div>
      <article id="informe-imprimible" className="mx-auto max-w-[800px] bg-white p-8 text-[#111] shadow-tarjeta print:p-0 print:shadow-none">
        <header className="flex items-start justify-between gap-4 border-b-2 border-[#0d366b] pb-3">
          <div className="flex items-center gap-2.5">
            <svg viewBox="0 0 32 32" className="h-9 w-9" aria-hidden>
              <rect width="32" height="32" rx="9" fill="#0d366b" />
              <circle cx="16" cy="17" r="7.5" fill="none" stroke="#86b6ef" strokeWidth="2" />
              <path d="M8.5 17c3-2.6 12-2.6 15 0" fill="none" stroke="#86b6ef" strokeWidth="1.6" />
              <circle cx="23.5" cy="8.5" r="2.5" fill="#eb6834" />
            </svg>
            <div>
              <p className="text-[16px] font-semibold">TerraVerdict</p>
              <p className="text-[11px] text-[#555]">{t("Informe ejecutivo · documento no oficial", "Executive brief · unofficial document")}</p>
            </div>
          </div>
          <div className="text-right text-[11px] text-[#555]">
            <p className="font-mono">{e.id}</p>
            <p>{t("Generado", "Generated")}: {hoy} UTC</p>
            <p>{t("Expediente del", "Case file of")} {fechaHora(e.creado_en)}</p>
          </div>
        </header>

        <h1 className="mt-5 text-[22px] font-semibold leading-tight">{traducirTitulo(e.titulo)}</h1>
        <p className="mt-2 text-[13px] leading-relaxed text-[#333]">{e.resumen}</p>

        <section className="mt-5 rounded-lg border-2 border-[#0d366b] p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-[#0d366b]">{t("Veredicto para la toma de decisiones", "Verdict for decision-making")}</p>
          <p className="mt-1 text-[15px] font-semibold">{veredicto}</p>
          <p className="mt-1 text-[11.5px] text-[#555]">{t("Sello de confianza: estado del expediente", "Confidence seal: case-file status")} «{e.estado}»{e.veredicto ? ` · ${t("veredicto", "verdict")} «${e.veredicto}»` : ""} · {t("contenido verificado por SHA-256", "content verified by SHA-256")}</p>
        </section>

        {cifras.length > 0 && (
          <section className="mt-5">
            <h2 className="text-[13px] font-semibold uppercase tracking-wider text-[#0d366b]">{t("Cifras verificadas", "Verified figures")}</h2>
            <table className="mt-2 w-full border-collapse text-[12.5px]">
              <tbody>
                {cifras.map((c) => (
                  <tr key={c.etiqueta} className="border-b border-[#ddd] align-top">
                    <th scope="row" className="py-1.5 pr-3 text-left font-medium text-[#333]">{c.etiqueta}</th>
                    <td className="py-1.5 pr-3 font-mono font-semibold">{c.valor}</td>
                    <td className="py-1.5 text-[11.5px] text-[#555]">{c.nota ?? ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}

        <section className="mt-5">
          <h2 className="text-[13px] font-semibold uppercase tracking-wider text-[#0d366b]">{t("Limitaciones e incertidumbre", "Limitations and uncertainty")}</h2>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-[12.5px] text-[#333]">
            {limitaciones.map((l) => <li key={l}>{l}</li>)}
            <li>{t("Resultados experimentales: no sustituyen a los avisos oficiales (SENAMHI, IGP, INGEMMET, INDECI, ENFEN).", "Experimental results: they do not replace official warnings (SENAMHI, IGP, INGEMMET, INDECI, ENFEN).")}</li>
            <li>{t("Las cifras de prueba se calcularon una sola vez con un periodo no usado para elegir el modelo; los intervalos son del 90 %.", "Test figures were computed once on a period not used to choose the model; intervals are 90 %.")}</li>
          </ul>
        </section>

        <div className="salto-pagina" />

        <section className="mt-6">
          <h2 className="text-[13px] font-semibold uppercase tracking-wider text-[#0d366b]">{t("Fuentes", "Sources")}</h2>
          <ul className="mt-2 space-y-1 text-[12px] text-[#333]">
            {p.fuentes.map((f) => (
              <li key={f.fuente_id + (f.coleccion ?? "")}>
                <span className="font-mono">{f.fuente_id}</span>
                {f.coleccion ? ` · ${f.coleccion}` : ""}
                {f.version ? ` · v${f.version}` : ""}
                {f.doi ? ` · doi:${f.doi}` : ""}
                {f.url ? ` · ${f.url}` : ""}
              </li>
            ))}
          </ul>
        </section>

        <section className="mt-5">
          <h2 className="text-[13px] font-semibold uppercase tracking-wider text-[#0d366b]">{t("Procedencia y reproducibilidad", "Provenance and reproducibility")}</h2>
          <dl className="mt-2 grid grid-cols-[180px_1fr] gap-x-3 gap-y-1 text-[11.5px]">
            <dt className="text-[#555]">{t("Repositorio", "Repository")}</dt><dd className="font-mono">{p.codigo?.repositorio ?? "—"}</dd>
            <dt className="text-[#555]">Commit</dt><dd className="break-all font-mono">{p.codigo?.commit ?? "—"}</dd>
            <dt className="text-[#555]">{t("Comando", "Command")}</dt><dd className="font-mono">{p.codigo?.script ?? "—"}</dd>
            <dt className="text-[#555]">{t("Hash del contenido", "Content hash")}</dt><dd className="break-all font-mono">{e.hash_contenido}</dd>
            {p.preregistro_sha256 && (<><dt className="text-[#555]">{t("Preregistro (SHA-256)", "Preregistration (SHA-256)")}</dt><dd className="break-all font-mono">{p.preregistro_sha256}</dd></>)}
            <dt className="text-[#555]">{t("Generado (pipeline)", "Generated (pipeline)")}</dt><dd className="font-mono">{p.generado_utc}</dd>
          </dl>
          {p.hash_entradas && Object.keys(p.hash_entradas).length > 0 && (
            <ul className="mt-2 space-y-0.5 text-[10.5px] text-[#444]">
              {Object.entries(p.hash_entradas).slice(0, 12).map(([k, v]) => <li key={k} className="break-all font-mono">{k}: {String(v)}</li>)}
            </ul>
          )}
        </section>

        {p.pasos && p.pasos.length > 0 && (
          <section className="mt-5">
            <h2 className="text-[13px] font-semibold uppercase tracking-wider text-[#0d366b]">{t("Pasos del proceso", "Process steps")}</h2>
            <ol className="mt-2 list-decimal space-y-0.5 pl-5 text-[11.5px] text-[#333]">
              {p.pasos.slice(0, 10).map((s) => <li key={s.id}><span className="font-medium">{s.nombre}</span>{s.descripcion ? ` — ${s.descripcion}` : ""}</li>)}
            </ol>
          </section>
        )}

        <footer className="mt-6 border-t border-[#ddd] pt-2 text-[10.5px] leading-snug text-[#555]">
          {t(
            "TerraVerdict es un proyecto independiente. Usa datos abiertos de NASA (POWER, GPM IMERG, MODIS, HLS, GIBS, GLC), NOAA, USGS, Smithsonian GVP y fuentes peruanas citadas; no es una publicación oficial de NASA ni de ninguna otra institución, y ninguna de ellas lo respalda.",
            "TerraVerdict is an independent project. It uses open data from NASA (POWER, GPM IMERG, MODIS, HLS, GIBS, GLC), NOAA, USGS, the Smithsonian GVP and cited Peruvian sources; it is not an official publication of NASA or any other institution, and none of them endorses it.",
          )}
        </footer>
      </article>
    </div>
  );
}
