import { ArrowLeft, Braces, FileCheck2, GitBranch, ShieldCheck } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import type { Esquemas } from "../api/cliente";
import { useExpediente, useExpedientes, useObservaciones, useSeries } from "../api/consultas";
import { GrafoProceso } from "../componentes/graficos/GrafoProceso";
import { GraficoSerie } from "../componentes/graficos/GraficoSerie";
import {
  Boton,
  ChipEstado,
  ESTADOS_PRUEBA,
  Encabezado,
  Esqueleto,
  EstadoVacio,
  ErrorCarga,
  Insignia,
  NOMBRES_PRUEBA,
  Tarjeta,
  VEREDICTOS,
} from "../componentes/ui";
import { conUnidad, etiquetaMetrica, fechaHora, numero, valorMetrica, valorP } from "../lib/formato";
import { t } from "../lib/i18n";

const TIPOS_ES_EN: Record<string, [string, string]> = {
  tendencia: ["Tendencia", "Trend"],
  relevancia: ["Relevancia", "Relevance"],
  atribucion: ["Atribución", "Attribution"],
  pronostico: ["Pronóstico", "Forecast"],
  alerta: ["Alerta", "Alert"],
  colmatacion: ["Colmatación", "Siltation"],
  priorizacion: ["Priorización", "Prioritization"],
  caos: ["Dinámica y caos", "Dynamics and chaos"],
  comparacion_modelos: ["Comparación de modelos", "Model comparison"],
  recurrencia: ["Recurrencia volcánica", "Volcanic recurrence"],
  sismicidad: ["Sismicidad", "Seismicity"],
  inventario: ["Inventario de eventos", "Event inventory"],
  panorama_nacional: ["Panorama nacional", "National panorama"],
};
const tipoTexto = (tipo: string) => (TIPOS_ES_EN[tipo] ? t(...TIPOS_ES_EN[tipo]) : tipo);

/** Vista especializada de cada tipo de resultado M6/M7 (el JSON queda disponible, plegado). */
const VISTA_POR_TIPO: Record<string, string> = {
  caos: "/caos",
  comparacion_modelos: "/modelos",
  recurrencia: "/volcanes",
  sismicidad: "/sismos",
  inventario: "/fenomenos",
  panorama_nacional: "/peru",
};

function ListaExpedientes() {
  const exp = useExpedientes();
  return (
    <div>
      <Encabezado
        eyebrow={t("Resultados científicos", "Scientific results")}
        titulo={t("Expedientes", "Case files")}
        descripcion={t("Un expediente es un resultado inmutable con su procedencia completa. Su ID se deriva del contenido: el mismo cálculo da siempre el mismo ID, y cualquier cambio produce uno nuevo.", "A case file is an immutable result with its full provenance. Its ID is derived from the content: the same computation always yields the same ID, and any change yields a new one.")}
      />
      {exp.isLoading ? (
        <div className="grid gap-4 md:grid-cols-2">{[0, 1].map((i) => <Esqueleto key={i} className="h-40" />)}</div>
      ) : exp.error ? (
        <ErrorCarga error={exp.error} />
      ) : exp.data?.items.length === 0 ? (
        <EstadoVacio icono={FileCheck2} titulo={t("Todavía no hay expedientes", "No case files yet")}>
          {t("El pipeline los publica con", "The pipeline publishes them with")} <code className="font-mono">POST /api/v1/expedientes</code>.
        </EstadoVacio>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {exp.data?.items.map((e) => (
            <Link key={e.id} to={`/expedientes/${e.id}`} className="group">
              <article className="h-full rounded-2xl border border-line bg-surface p-5 shadow-tarjeta transition-all group-hover:-translate-y-0.5 group-hover:border-line-strong group-hover:shadow-flotante">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-[11.5px] text-ink-3">{e.id}</span>
                  <Insignia>{e.modulo} · {tipoTexto(e.tipo)}</Insignia>
                  {e.veredicto && <ChipEstado mapa={VEREDICTOS} valor={e.veredicto} />}
                </div>
                <h2 className="mt-3 text-[16px] font-semibold leading-snug text-ink">{e.titulo}</h2>
                <p className="mt-1.5 line-clamp-3 text-[13px] leading-relaxed text-ink-2">{e.resumen}</p>
                <p className="mt-3 text-[12px] text-ink-3">{t("Publicado", "Published")} {fechaHora(e.creado_en)}</p>
              </article>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function ResultadoTendencia({ r, serieId }: { r: Esquemas["ResultadoTendencia"]; serieId: string | null }) {
  const obs = useObservaciones(serieId ?? undefined);
  const series = useSeries({});
  const serie = series.data?.items.find((s) => s.id === serieId);
  const cifras = [
    { etiqueta: t("Pendiente de Sen", "Sen slope"), valor: conUnidad(r.pendiente.valor, r.pendiente.unidad, 2, true) },
    { etiqueta: t(`IC ${Math.round((r.pendiente.intervalo.nivel ?? 0.9) * 100)} %`, `${Math.round((r.pendiente.intervalo.nivel ?? 0.9) * 100)} % CI`), valor: `${numero(r.pendiente.intervalo.lo, 2)} ${t("a", "to")} ${numero(r.pendiente.intervalo.hi, 2)}` },
    { etiqueta: t("p conservador", "Conservative p"), valor: valorP(r.significancia.p_conservador) },
    { etiqueta: t("Observaciones", "Observations"), valor: `${r.n} (${r.periodo.desde}–${r.periodo.hasta})` },
  ];
  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cifras.map((c) => (
          <div key={c.etiqueta} className="rounded-2xl border border-line bg-surface p-4 shadow-tarjeta">
            <p className="etiqueta">{c.etiqueta}</p>
            <p className="cifra mt-2 text-[22px] font-semibold tracking-tight text-ink">{c.valor}</p>
          </div>
        ))}
      </div>

      {serieId && (
        <Tarjeta titulo={t("Serie y tendencia", "Series and trend")} subtitulo={t("Pendiente publicada en el expediente; la banda muestra el intervalo de la pendiente.", "Slope published in the case file; the band shows the slope's interval.")}>
          {obs.data ? (
            <GraficoSerie observaciones={obs.data.observaciones} unidad={obs.data.unidad} agregacion={serie?.agregacion} pendiente={r.pendiente} alto={320} />
          ) : (
            <Esqueleto className="h-[320px]" />
          )}
        </Tarjeta>
      )}

      <Tarjeta
        titulo={<span className="flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-accent" /> {t("Sello de confianza", "Confidence seal")}</span>}
        subtitulo={t("Cinco pruebas antes de creer una tendencia. Un veredicto 'robusta' exige las cinco aprobadas: la API rechaza cualquier otro caso.", "Five tests before believing a trend. A 'robust' verdict requires all five passed: the API rejects any other case.")}
      >
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
          {Object.entries(r.sello).map(([clave, prueba]) => (
            <div key={clave} className="flex flex-col rounded-xl border border-line bg-surface-2 p-3.5">
              <div className="flex items-start justify-between gap-2">
                <p className="text-[13.5px] font-semibold text-ink">{NOMBRES_PRUEBA[clave] ?? clave}</p>
              </div>
              <div className="mt-2"><ChipEstado mapa={ESTADOS_PRUEBA} valor={prueba.estado} /></div>
              {prueba.metricas && Object.keys(prueba.metricas).length > 0 && (
                <dl className="mt-3 space-y-1 text-[12px]">
                  {Object.entries(prueba.metricas).slice(0, 5).map(([k, v]) => (
                    <div key={k} className="flex justify-between gap-2">
                      <dt className="truncate text-ink-3" title={etiquetaMetrica(k)}>{etiquetaMetrica(k)}</dt>
                      <dd className="cifra shrink-0 font-medium text-ink">{valorMetrica(v)}</dd>
                    </div>
                  ))}
                </dl>
              )}
              {prueba.nota && <p className="mt-auto pt-3 text-[11.5px] leading-snug text-ink-2">{prueba.nota}</p>}
            </div>
          ))}
        </div>
        <Detectabilidad r={r} />
      </Tarjeta>
    </>
  );
}

/** Explica la prueba de detectabilidad con sus propias métricas (Weatherhead et al., 1998). */
function Detectabilidad({ r }: { r: Esquemas["ResultadoTendencia"] }) {
  const m = r.sello.detectabilidad?.metricas ?? {};
  const necesarios = typeof m.anios_necesarios === "number" ? m.anios_necesarios : null;
  const disponibles = typeof m.anios_disponibles === "number" ? m.anios_disponibles : null;
  const adicionales = r.anios_para_decidir;
  if (necesarios === null || disponibles === null) {
    if (adicionales === null || adicionales === undefined) return null;
    return (
      <p className="mt-4 text-[13px] text-ink-2">
        {t("Años adicionales necesarios para decidir (Weatherhead et al., 1998):", "Additional years needed to decide (Weatherhead et al., 1998):")} <strong className="cifra text-ink">{numero(adicionales, 1)}</strong>
      </p>
    );
  }
  const suficiente = disponibles >= necesarios;
  return (
    <div className="mt-4 rounded-xl border border-line bg-surface-2 p-3.5 text-[13px] leading-relaxed text-ink-2">
      <p className="font-medium text-ink">{t("¿Alcanza la longitud de la serie?", "Is the series long enough?")}</p>
      <p className="mt-1">
        {t("Para distinguir esta pendiente del ruido natural (σ y autocorrelación de la serie) se necesitan unos", "To tell this slope apart from natural noise (σ and autocorrelation of the series) it takes about")}{" "}
        <strong className="cifra text-ink">{numero(necesarios, 1)} {t("años", "years")}</strong>; {t("hay", "there are")}{" "}
        <strong className="cifra text-ink">{numero(disponibles, 0)}</strong>.{" "}
        {suficiente
          ? t("La longitud no es la limitación: lo que falta son las pruebas pendientes del sello.", "Length is not the limitation: what is missing are the seal's pending tests.")
          : t(`Faltan unos ${numero(necesarios - disponibles, 1)} años de datos para decidir.`, `About ${numero(necesarios - disponibles, 1)} more years of data are needed to decide.`)}
      </p>
      <p className="mt-1 text-[11.5px] text-ink-3">Weatherhead et al. (1998), J. Geophys. Res. 103(D14), 17 149–17 161.</p>
    </div>
  );
}

function DetalleExpediente({ id }: { id: string }) {
  const exp = useExpediente(id);
  if (exp.isLoading) return <Esqueleto className="h-96" />;
  if (exp.error || !exp.data) return <ErrorCarga error={exp.error} />;
  const e = exp.data;

  const descargar = () => {
    const url = URL.createObjectURL(new Blob([JSON.stringify(e, null, 2)], { type: "application/json" }));
    const a = Object.assign(document.createElement("a"), { href: url, download: `${e.id}.json` });
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <Link to="/expedientes" className="inline-flex items-center gap-1.5 text-[13px] text-ink-2 hover:text-ink">
        <ArrowLeft className="h-4 w-4" /> {t("Expedientes", "Case files")}
      </Link>
      <Encabezado
        eyebrow={`${e.modulo} · ${tipoTexto(e.tipo)} · ${e.id}`}
        titulo={e.titulo}
        descripcion={e.resumen}
        acciones={
          <>
            {e.veredicto && <ChipEstado mapa={VEREDICTOS} valor={e.veredicto} />}
            <Boton tamano="sm" icono={Braces} onClick={descargar}>JSON</Boton>
          </>
        }
      />
      {e.estado === "retirado" && (
        <div role="status" className="rounded-xl border border-line bg-surface-2 p-3 text-[13px] text-ink-2">
          {t("Expediente retirado", "Case file withdrawn")} {e.retirado_en ? `${t("el", "on")} ${fechaHora(e.retirado_en)}` : ""}: {e.motivo_retiro}
        </div>
      )}

      {e.resultado.tipo === "tendencia" ? (
        <ResultadoTendencia r={e.resultado} serieId={e.serie_id} />
      ) : (
        <Tarjeta
          titulo={t("Resultado", "Result")}
          subtitulo={t("Este tipo de resultado tiene su propia vista, con gráficos, mapas e incertidumbre.", "This result type has its own view, with charts, maps and uncertainty.")}
          acciones={VISTA_POR_TIPO[e.resultado.tipo] && <Link to={VISTA_POR_TIPO[e.resultado.tipo] ?? "/"}><Boton tamano="sm" variante="primario">{t("Abrir la vista", "Open the view")}</Boton></Link>}
        >
          <details>
            <summary className="cursor-pointer text-[13px] font-medium text-accent-ink">{t("Ver el resultado completo (JSON validado por el contrato)", "See the full result (contract-validated JSON)")}</summary>
            <pre className="mt-2 max-h-[480px] overflow-auto rounded-xl bg-surface-2 p-4 font-mono text-[12px] text-ink-2">{JSON.stringify(e.resultado, null, 2)}</pre>
          </details>
        </Tarjeta>
      )}

      <Tarjeta
        titulo={<span className="flex items-center gap-2"><GitBranch className="h-4 w-4 text-accent" /> {t("Cómo llegué a esto", "How I got here")}</span>}
        subtitulo={t("Los pasos reales que produjeron este resultado. Haga clic en un paso para ver sus métricas.", "The real steps that produced this result. Click a step to see its metrics.")}
      >
        {e.procedencia.pasos && e.procedencia.pasos.length > 0 ? (
          <GrafoProceso pasos={e.procedencia.pasos} />
        ) : (
          <EstadoVacio titulo={t("El pipeline no registró pasos para este expediente", "The pipeline recorded no steps for this case file")} />
        )}
      </Tarjeta>

      <Tarjeta titulo={t("Procedencia", "Provenance")} pie={<>{t("Hash del contenido", "Content hash")}: <span className="font-mono">{e.hash_contenido}</span></>}>
        <div className="grid gap-5 text-[13px] md:grid-cols-3">
          <div>
            <p className="etiqueta mb-2">{t("Fuentes", "Sources")}</p>
            <ul className="space-y-1.5">
              {e.procedencia.fuentes.map((f) => (
                <li key={f.fuente_id}>
                  {f.url ? (
                    <a href={f.url} target="_blank" rel="noreferrer" className="text-accent-ink hover:underline">{f.fuente_id}</a>
                  ) : (
                    <span className="text-ink">{f.fuente_id}</span>
                  )}
                  <span className="block text-[11.5px] text-ink-3">{t("consultado", "retrieved")} {fechaHora(f.consultado_utc)}</span>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <p className="etiqueta mb-2">{t("Código", "Code")}</p>
            <p className="text-ink">{e.procedencia.codigo?.repositorio ?? "—"}</p>
            <p className="font-mono text-[12px] text-ink-2">{e.procedencia.codigo?.script ?? ""}</p>
          </div>
          <div>
            <p className="etiqueta mb-2">{t("Entradas (SHA-256)", "Inputs (SHA-256)")}</p>
            {Object.entries(e.procedencia.hash_entradas ?? {}).map(([k, v]) => (
              <p key={k} className="truncate font-mono text-[11.5px] text-ink-2" title={v}>{k}: {v.slice(0, 16)}…</p>
            ))}
            <p className="mt-2 text-[12px] text-ink-3">{t("Generado", "Generated")} {fechaHora(e.procedencia.generado_utc)} · {t("publicado por", "published by")} {e.creado_por}</p>
          </div>
        </div>
      </Tarjeta>
    </div>
  );
}

export function ExpedientesPagina() {
  const { id } = useParams();
  return id ? <DetalleExpediente id={id} /> : <ListaExpedientes />;
}
