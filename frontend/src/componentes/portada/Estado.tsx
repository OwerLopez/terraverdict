/**
 * "¿Cómo estamos hoy?": semáforo hídrico, tabla maestra de veredictos y simulador ENSO → sequía.
 *
 * Reglas: cada cifra viene de `/api/v1/portada` (indicadores calculados desde los crudos y expedientes) o de
 * la crónica de eventos citados; cada tarjeta dice la fecha de su último dato. Un dato antiguo se muestra
 * como antiguo, no como actual, y nada se clasifica con umbrales inventados.
 */
import { clsx } from "clsx";
import { Activity, CloudRain, Droplets, ExternalLink, FileCheck2, Mountain, Thermometer, Waves, type LucideIcon } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { Esquemas } from "../../api/cliente";
import { useEventos } from "../../api/consultas";
import { cifraCitada, numero } from "../../lib/formato";
import { categoriaEnso, type Indicadores } from "../../lib/indicadores";
import { t } from "../../lib/i18n";
import { lecturaHabilidad, lecturaP } from "../../lib/lectura";
import { Esqueleto, Insignia, Tarjeta, type Tono } from "../ui";

type Portada = Esquemas["Portada"];
type Fila = Esquemas["FilaVeredicto"];

const MESES_ES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const MESES_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** "2026-10" → "oct 2026" / "Oct 2026". */
export function mesTexto(ym: string): string {
  const [a, m] = ym.split("-").map(Number);
  if (!a || !m) return ym;
  return t(`${MESES_ES[m - 1]} ${a}`, `${MESES_EN[m - 1]} ${a}`);
}

function mesesDesde(fecha: string): number {
  const d = new Date(fecha);
  const hoy = new Date();
  return (hoy.getFullYear() - d.getFullYear()) * 12 + (hoy.getMonth() - d.getMonth());
}

const CATEGORIA_SPI: Record<string, [string, string, Tono]> = {
  extremadamente_seco: ["Extremadamente seco", "Extremely dry", "critical"],
  severamente_seco: ["Severamente seco", "Severely dry", "critical"],
  moderadamente_seco: ["Moderadamente seco", "Moderately dry", "serious"],
  cercano_a_lo_normal: ["Cercano a lo normal", "Near normal", "neutral"],
  moderadamente_humedo: ["Moderadamente húmedo", "Moderately wet", "good"],
  muy_humedo: ["Muy húmedo", "Very wet", "good"],
  extremadamente_humedo: ["Extremadamente húmedo", "Extremely wet", "accent"],
};

function Luz({ tono }: { tono: Tono }) {
  const color = { critical: "var(--critical)", serious: "var(--serious)", warning: "var(--warning)", good: "var(--good)", accent: "var(--accent)", neutral: "var(--ink-3)" }[tono];
  return <span aria-hidden className="inline-block h-3 w-3 shrink-0 rounded-full ring-4 ring-[color-mix(in_srgb,currentColor_18%,transparent)]" style={{ background: color, color }} />;
}

function Celda({ icono: Icono, tono, titulo, valor, detalle, fecha, pie }: { icono: LucideIcon; tono: Tono; titulo: string; valor: string; detalle: string; fecha: string; pie?: React.ReactNode }) {
  return (
    <div className="flex flex-col rounded-2xl border border-line bg-surface p-4">
      <div className="flex items-center justify-between gap-2">
        <p className="etiqueta flex items-center gap-1.5"><Icono className="h-3.5 w-3.5" aria-hidden /> {titulo}</p>
        <Luz tono={tono} />
      </div>
      <p className="cifra mt-2 text-[28px] font-semibold leading-none tracking-tight text-ink">{valor}</p>
      <p className="mt-1.5 text-[12.5px] leading-snug text-ink-2">{detalle}</p>
      <p className="mt-2 text-[11.5px] font-medium text-ink-3">{fecha}</p>
      {pie && <div className="mt-2 border-t border-line pt-2 text-[11.5px] leading-snug text-ink-3">{pie}</div>}
    </div>
  );
}

/** Semáforo hídrico: represas (último dato citado), ENSO (ONI y Niño mensual) y sequía en la cabecera (SPI-3). */
export function Semaforo({ ind, cargando }: { ind: Indicadores | null; cargando: boolean }) {
  const eventos = useEventos();
  const represa = useMemo(
    () => (eventos.data ?? []).filter((e) => ["almacenamiento", "escasez"].includes(e.categoria) && e.cifras.some((c) => c.unidad === "%" || c.unidad === "hm3")).sort((a, b) => b.fecha.localeCompare(a.fecha))[0],
    [eventos.data],
  );
  const hoy = new Date();
  const titulo = t(`Semáforo hídrico · ${MESES_ES[hoy.getMonth()]} ${hoy.getFullYear()}`, `Water status today · ${MESES_EN[hoy.getMonth()]} ${hoy.getFullYear()}`);
  if (cargando && !ind) return <Esqueleto className="h-60" />;
  const oni = ind?.enso.oni;
  const nino = ind?.enso.nino_mensual;
  const spi = ind?.sequia_actual.ultimo_confiable;
  const cat = ind?.sequia_actual.categoria_ultimo_confiable ? CATEGORIA_SPI[ind.sequia_actual.categoria_ultimo_confiable] : null;
  const fuerte = ind?.sequia_por_enso.categorias.find((c) => c.categoria === "nino_fuerte");
  const resto = ind?.sequia_por_enso.fisher_nino_vs_resto;
  const pctRepresa = represa?.cifras.find((c) => c.unidad === "%");
  const antiguedad = represa ? mesesDesde(represa.fecha) : 0;

  return (
    <section aria-labelledby="semaforo" data-tour="estado" className="rounded-3xl border border-line bg-surface-2/60 p-5 md:p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="semaforo" className="text-[20px] font-semibold tracking-tight text-ink">{titulo}</h2>
        <p className="text-[12px] text-ink-3">{t("Cada tarjeta muestra la fecha de su último dato. No es una alerta oficial.", "Each card shows the date of its latest data. Not an official warning.")}</p>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        {represa ? (
          <Celda
            icono={Droplets}
            tono={antiguedad > 6 ? "neutral" : "warning"}
            titulo={t("Represas del Chili", "Chili reservoirs")}
            valor={pctRepresa ? cifraCitada(pctRepresa) : cifraCitada(represa.cifras[0]!)}
            detalle={t(represa.titulo, represa.titulo_en ?? represa.titulo)}
            fecha={t(`Último dato público citado: ${mesTexto(represa.fecha.slice(0, 7))} (hace ${antiguedad} meses)`, `Latest cited public figure: ${mesTexto(represa.fecha.slice(0, 7))} (${antiguedad} months ago)`)}
            pie={antiguedad > 6 ? t("Dato antiguo: AUTODEMA no publica una serie abierta; no se presenta como volumen de hoy.", "Stale figure: AUTODEMA publishes no open series; it is not shown as today's volume.") : undefined}
          />
        ) : (
          <Esqueleto className="h-48" />
        )}
        {oni ? (
          <Celda
            icono={Thermometer}
            tono={oni.episodio_noaa === "el_nino" ? "critical" : oni.episodio_noaa === "la_nina" ? "warning" : "neutral"}
            titulo={t("El Niño – Oscilación del Sur", "El Niño – Southern Oscillation")}
            valor={`ONI ${numero(oni.valor, 2, { signo: true })} °C`}
            detalle={
              oni.episodio_noaa === "el_nino"
                ? t(`Episodio El Niño según NOAA (${oni.trimestres_consecutivos_nino} trimestres seguidos ≥ +0,5 °C)${oni.intensidad === "nino_fuerte" ? "; intensidad fuerte por convención (≥ 1,5 °C)" : ""}.`, `El Niño episode per NOAA (${oni.trimestres_consecutivos_nino} consecutive seasons ≥ +0.5 °C)${oni.intensidad === "nino_fuerte" ? "; strong by convention (≥ 1.5 °C)" : ""}.`)
                : oni.episodio_noaa === "la_nina"
                  ? t("Episodio La Niña según NOAA.", "La Niña episode per NOAA.")
                  : t("Sin episodio declarado por el criterio de NOAA.", "No episode under NOAA's criterion.")
            }
            fecha={t(`ONI ${oni.trimestre} ${oni.anio} · NOAA CPC`, `ONI ${oni.trimestre} ${oni.anio} · NOAA CPC`)}
            pie={nino && t(
              `Más reciente (mensual, OISST 1991–2020): Niño 3.4 ${numero(nino.nino34_anom, 2, { signo: true })} °C y Niño 1+2 (costa del Perú) ${numero(nino.nino12_anom, 2, { signo: true })} °C en ${mesTexto(`${nino.anio}-${String(nino.mes).padStart(2, "0")}`)}. Otra base: no se compara cifra a cifra con el ONI.`,
              `Most recent (monthly, OISST 1991–2020): Niño 3.4 ${numero(nino.nino34_anom, 2, { signo: true })} °C and Niño 1+2 (Peru coast) ${numero(nino.nino12_anom, 2, { signo: true })} °C in ${mesTexto(`${nino.anio}-${String(nino.mes).padStart(2, "0")}`)}. Different baseline: not compared figure by figure with the ONI.`,
            )}
          />
        ) : (
          <Esqueleto className="h-48" />
        )}
        {spi && cat ? (
          <Celda
            icono={CloudRain}
            tono={cat[2]}
            titulo={t("Sequía en la cabecera (SPI-3)", "Headwater drought (SPI-3)")}
            valor={`${numero(spi.spi3, 2, { signo: true })}`}
            detalle={t(`${cat[0]}: ${numero(spi.acumulado_3m_mm, 0)} mm en 3 meses frente a ${numero(spi.media_climatologica_3m_mm, 0)} mm de media.`, `${cat[1]}: ${numero(spi.acumulado_3m_mm, 0)} mm over 3 months vs a ${numero(spi.media_climatologica_3m_mm, 0)} mm mean.`)}
            fecha={t(`3 meses hasta ${mesTexto(spi.mes)} · NASA POWER diario`, `3 months to ${mesTexto(spi.mes)} · NASA POWER daily`)}
            pie={fuerte && resto && t(
              `Riesgo de la temporada dic–mar: con El Niño fuerte hubo sequía en ${fuerte.con_sequia} de ${fuerte.n} temporadas (IC90 ${numero(fuerte.ic90[0] * 100, 0)}–${numero(fuerte.ic90[1] * 100, 0)} %), frente a ${resto.resto[0]} de ${resto.resto[1]} sin El Niño. Frecuencia histórica, no pronóstico.`,
              `Dec–Mar season risk: under strong El Niño, drought occurred in ${fuerte.con_sequia} of ${fuerte.n} seasons (90 % CI ${numero(fuerte.ic90[0] * 100, 0)}–${numero(fuerte.ic90[1] * 100, 0)} %), vs ${resto.resto[0]} of ${resto.resto[1]} without El Niño. Historical frequency, not a forecast.`,
            )}
          />
        ) : (
          <Esqueleto className="h-48" />
        )}
      </div>
    </section>
  );
}

// ------------------------------------------------------------------------------------------------

const NOMBRE_FENOMENO: Record<Fila["fenomeno"], [string, string, LucideIcon, string]> = {
  lluvia_extrema: ["Lluvia extrema", "Extreme rain", CloudRain, "/metricas"],
  sequia: ["Sequía (SPI-3)", "Drought (SPI-3)", Droplets, "/modelos"],
  sismos: ["Sismos", "Earthquakes", Activity, "/sismos"],
  volcanes: ["Volcanes", "Volcanoes", Mountain, "/volcanes"],
  deslizamientos: ["Deslizamientos", "Landslides", Waves, "/peru"],
};

const VEREDICTO: Record<Fila["veredicto"], [string, string, Tono]> = {
  habilidad_confirmada: ["Habilidad confirmada fuera de muestra", "Skill confirmed out of sample", "good"],
  habilidad_con_indicio: ["Indicio de habilidad: vigilancia, no alerta", "Indication of skill: monitoring, not warning", "warning"],
  sin_habilidad: ["Sin habilidad demostrada", "No demonstrated skill", "neutral"],
  descriptivo: ["Descripción estadística (no pronóstico)", "Statistical description (no forecast)", "neutral"],
  recurrencia_historica: ["Recurrencia histórica (no pronóstico)", "Historical recurrence (no forecast)", "neutral"],
  abstencion: ["Abstención: datos insuficientes", "Abstention: insufficient data", "serious"],
};

function textoTendencia(f: Fila): string {
  const d = f.tendencia;
  if (!d || d.valor == null) return "—";
  if (d.tipo === "pendiente") {
    const veredicto =
      { sin_tendencia: t("no confirmada", "not confirmed"), preliminar: t("preliminar", "preliminary"), fragil: t("frágil: falla una prueba del Sello", "fragile: fails a Seal test"), robusta: t("robusta", "robust"), no_decidible: t("no decidible", "undecidable") }[d.veredicto ?? ""] ?? d.veredicto ?? "";
    const unidad = d.unidad === "Cel/decada" ? t("°C/década", "°C/decade") : t("mm/década", "mm/decade");
    const que = d.variable === "temperatura" ? t("Temperatura", "Temperature") : t("Lluvia dic–mar", "Dec–Mar rain");
    return `${que}: ${numero(d.valor, 2, { signo: true })} ${unidad} (${t("IC90", "90 % CI")} ${numero(d.intervalo?.[0], 2)}–${numero(d.intervalo?.[1], 2)}; ${d.periodo}) · ${veredicto}`;
  }
  if (d.tipo === "valor_b") return t(`Gutenberg-Richter b = ${numero(d.valor, 2)} (IC90 ${numero(d.intervalo?.[0], 2)}–${numero(d.intervalo?.[1], 2)}; ${d.periodo})`, `Gutenberg-Richter b = ${numero(d.valor, 2)} (90 % CI ${numero(d.intervalo?.[0], 2)}–${numero(d.intervalo?.[1], 2)}; ${d.periodo})`);
  if (d.tipo === "probabilidad_anual") return t(`${d.variable}: ${numero(d.valor * 100, 1)} % anual (IC90 ${numero((d.intervalo?.[0] ?? 0) * 100, 1)}–${numero((d.intervalo?.[1] ?? 0) * 100, 1)} %; ${d.periodo})`, `${d.variable}: ${numero(d.valor * 100, 1)} % per year (90 % CI ${numero((d.intervalo?.[0] ?? 0) * 100, 1)}–${numero((d.intervalo?.[1] ?? 0) * 100, 1)} %; ${d.periodo})`);
  return t(`${numero(d.valor, 0)} eventos documentados`, `${numero(d.valor, 0)} documented events`);
}

function textoAnticipacion(f: Fila): string {
  const a = f.anticipacion;
  if (f.fenomeno === "volcanes") return t("No a corto plazo: sin monitoreo continuo no se pronostican erupciones", "Not in the short term: no eruption forecasts without continuous monitoring");
  if (f.fenomeno === "deslizamientos") return t("En abstención: se necesitan ≥ 30 eventos para un umbral de lluvia", "Abstaining: ≥ 30 events are needed for a rainfall threshold");
  if (!a || a.valor == null) return "—";
  const nombre = a.metrica === "bss_climatologia" ? "BSS" : a.metrica === "habilidad_climatologia" ? t("habilidad ECM", "MSE skill") : t("ganancia", "gain");
  const valor = a.metrica === "ganancia_informacion_bits" ? `${numero(a.valor, 3)} bits` : numero(a.valor, 2);
  const horizonte = a.horizonte?.replace("día", t("día", "day")).replace("meses", t("meses", "months")).replace("mes", t("mes", "month"));
  return `${horizonte}: ${nombre} ${valor} (${t("IC90", "90 % CI")} ${numero(a.intervalo?.[0], 2)}–${numero(a.intervalo?.[1], 2)}; p DM ${numero(a.p_diebold_mariano, 3)}) · ${a.modelo.replace(/_/g, " ")}`;
}

/** Tabla de lectura rápida: una fila por fenómeno, cada celda con su expediente de origen. */
export function TablaVeredictos({ portada }: { portada: Portada | undefined }) {
  if (!portada) return <Esqueleto className="h-72" />;
  return (
    <Tarjeta
      tour="veredictos"
      titulo={t("Tabla maestra de veredictos: cinco fenómenos", "Master verdict table: five hazards")}
      subtitulo={t("Tendencia histórica, capacidad de anticipar (modelo elegido en validación, evaluado una sola vez en la prueba) y veredicto.", "Historical trend, ability to anticipate (model chosen on validation, evaluated once on the test set) and verdict.")}
      pie={portada.regla_evidencia}
    >
      <div className="overflow-x-auto">
        <table className="w-full min-w-[860px] border-collapse text-left text-[13px]">
          <caption className="sr-only">{t("Veredictos por fenómeno", "Verdicts by hazard")}</caption>
          <thead>
            <tr className="border-b border-line text-ink-3">
              <th scope="col" className="py-2 pr-3 font-semibold">{t("Fenómeno", "Hazard")}</th>
              <th scope="col" className="py-2 pr-3 font-semibold">{t("Fuente", "Source")}</th>
              <th scope="col" className="py-2 pr-3 font-semibold">{t("Tendencia histórica", "Historical trend")}</th>
              <th scope="col" className="py-2 pr-3 font-semibold">{t("¿Se puede anticipar?", "Can it be anticipated?")}</th>
              <th scope="col" className="py-2 font-semibold">{t("Veredicto TerraVerdict", "TerraVerdict verdict")}</th>
            </tr>
          </thead>
          <tbody>
            {portada.filas.map((f) => {
              const [es, en, Icono, ruta] = NOMBRE_FENOMENO[f.fenomeno];
              const [ves, ven, tono] = VEREDICTO[f.veredicto];
              const a = f.anticipacion;
              const exp = a?.expediente_id ?? f.tendencia?.expediente_id;
              return (
                <tr key={f.fenomeno} className="border-b border-line align-top last:border-0">
                  <th scope="row" className="py-2.5 pr-3 font-semibold text-ink">
                    <Link to={ruta} className="inline-flex items-center gap-1.5 hover:text-accent-ink"><Icono className="h-4 w-4 text-accent" aria-hidden /> {t(es, en)}</Link>
                  </th>
                  <td className="py-2.5 pr-3 text-[12.5px] text-ink-2">{f.fuentes.join(" · ")}</td>
                  <td className="py-2.5 pr-3 text-[12.5px] text-ink-2">{textoTendencia(f)}</td>
                  <td className="py-2.5 pr-3 text-[12.5px] text-ink-2">
                    {textoAnticipacion(f)}
                    {a && a.valor != null && a.metrica !== "ganancia_informacion_bits" && <span className="mt-0.5 block text-[11.5px] text-ink-3">{lecturaHabilidad(a.valor, a.metrica)} · {lecturaP(a.p_diebold_mariano)}</span>}
                  </td>
                  <td className="py-2.5">
                    <Insignia tono={tono}>{t(ves, ven)}</Insignia>
                    {f.abstencion?.[0] && <span className="mt-1 block text-[11.5px] text-ink-3">{f.abstencion[0]}</span>}
                    {exp && (
                      <Link to={`/expedientes/${exp}`} className="mt-1 inline-flex items-center gap-1 font-mono text-[11px] text-accent-ink hover:underline">
                        <FileCheck2 className="h-3 w-3" aria-hidden /> {exp}
                      </Link>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Tarjeta>
  );
}

// ------------------------------------------------------------------------------------------------

/**
 * Simulador ENSO → sequía: mueve el ONI y muestra la frecuencia histórica de sequía (SPI-3 de febrero ≤ −1)
 * en las temporadas con ese tipo de ENSO, con su intervalo de Wilson del 90 %. Es un escenario histórico
 * condicional, no un pronóstico calibrado; el fondo MERESE se muestra como contexto citado, sin asignaciones.
 */
export function SimuladorEnso({ ind }: { ind: Indicadores | null }) {
  const actual = ind?.enso.oni.valor ?? 0;
  const [oni, setOni] = useState<number | null>(null);
  const eventos = useEventos();
  const merese = eventos.data?.find((e) => e.id === "2024-04-merese-sedapar");
  if (!ind) return <Esqueleto className="h-72" />;
  const valor = oni ?? actual;
  const cat = categoriaEnso(valor);
  const datos = ind.sequia_por_enso;
  const fila = datos.categorias.find((c) => c.categoria === cat);
  const max = Math.max(actual, 2.5);
  return (
    <Tarjeta
      titulo={t("Simulador de estrés por El Niño", "El Niño stress simulator")}
      subtitulo={t(`Escenario histórico condicional (${datos.periodo?.[0]}–${datos.periodo?.[1]}): con este ONI, ¿con qué frecuencia hubo sequía en la temporada de lluvias de la cabecera?`, `Historical conditional scenario (${datos.periodo?.[0]}–${datos.periodo?.[1]}): with this ONI, how often was there drought in the headwater rainy season?`)}
      pie={`${datos.definicion}. ${datos.lectura} Fisher (El Niño frente al resto): p = ${numero(datos.fisher_nino_vs_resto.p_unilateral, 3)}.`}
    >
      <label className="block text-[13px] font-medium text-ink">
        ONI (DJF): <span className="cifra text-[20px] font-semibold">{numero(valor, 2, { signo: true })} °C</span>
        {oni === null && <span className="ml-2 text-[12px] font-normal text-ink-3">{t(`valor actual (${ind.enso.oni.trimestre} ${ind.enso.oni.anio})`, `current value (${ind.enso.oni.trimestre} ${ind.enso.oni.anio})`)}</span>}
        <input type="range" min={-1.5} max={max} step={0.01} value={valor} onChange={(e) => setOni(Number(e.target.value))} className="mt-2 w-full accent-[var(--accent)]" aria-label={t("Valor del ONI", "ONI value")} />
        <span className="flex justify-between text-[11px] text-ink-3"><span>{t("−1,5 La Niña", "−1.5 La Niña")}</span><span>0</span><span>{numero(max, 2, { signo: true })} {t("El Niño", "El Niño")}</span></span>
      </label>
      <div className="mt-4 grid gap-4 md:grid-cols-[1fr_1.2fr]">
        <div className="rounded-2xl bg-surface-2 p-4">
          <p className="etiqueta">{fila?.nombre}</p>
          <p className="cifra mt-1 text-[34px] font-semibold leading-none text-ink">{fila?.frecuencia != null ? `${numero(fila.frecuencia * 100, 0)} %` : "—"}</p>
          <p className="mt-1 text-[12.5px] text-ink-2">
            {fila && t(`Sequía en ${fila.con_sequia} de ${fila.n} temporadas · IC90 ${numero(fila.ic90[0] * 100, 0)}–${numero(fila.ic90[1] * 100, 0)} %`, `Drought in ${fila.con_sequia} of ${fila.n} seasons · 90 % CI ${numero(fila.ic90[0] * 100, 0)}–${numero(fila.ic90[1] * 100, 0)} %`)}
            {fila && fila.anios_con_sequia.length > 0 && ` (${fila.anios_con_sequia.join(", ")})`}
          </p>
          <p className="mt-2 text-[11.5px] text-ink-3">{t("Pocas temporadas por categoría: el intervalo es ancho y así se muestra.", "Few seasons per category: the interval is wide and shown as such.")}</p>
        </div>
        <ul className="space-y-2" aria-label={t("Frecuencia por categoría ENSO", "Frequency by ENSO category")}>
          {datos.categorias.map((c) => (
            <li key={c.categoria} className={clsx("rounded-xl border px-3 py-2", c.categoria === cat ? "border-accent bg-accent-soft" : "border-line")}>
              <div className="flex items-center justify-between text-[12px]"><span className="text-ink-2">{c.nombre}</span><span className="cifra font-semibold text-ink">{c.frecuencia != null ? `${numero(c.frecuencia * 100, 0)} %` : "—"} <span className="font-normal text-ink-3">({c.con_sequia}/{c.n})</span></span></div>
              <div className="relative mt-1.5 h-2 rounded-full bg-surface-3">
                <span className="absolute inset-y-0 rounded-full bg-[color-mix(in_srgb,var(--accent)_30%,transparent)]" style={{ left: `${c.ic90[0] * 100}%`, width: `${(c.ic90[1] - c.ic90[0]) * 100}%` }} />
                {c.frecuencia != null && <span className="absolute top-1/2 h-3 w-1 -translate-y-1/2 rounded bg-accent" style={{ left: `calc(${c.frecuencia * 100}% - 2px)` }} />}
              </div>
            </li>
          ))}
        </ul>
      </div>
      {merese && (
        <div className="mt-4 rounded-xl border border-dashed border-line-strong p-3 text-[12.5px] text-ink-2">
          <p>
            <span className="font-semibold text-ink">{t("Contexto de decisión:", "Decision context:")}</span>{" "}
            {t(merese.titulo, merese.titulo_en ?? merese.titulo)}.{" "}
            {t(
              "TerraVerdict no asigna ese presupuesto: la priorización por quebrada (erosión RUSLE, módulo M5) aún no está implementada. Este escenario solo indica en qué temporadas el riesgo histórico de déficit fue mayor.",
              "TerraVerdict does not allocate that budget: per-gully prioritization (RUSLE erosion, module M5) is not implemented yet. This scenario only shows in which seasons the historical deficit risk was higher.",
            )}
          </p>
          {merese.fuentes[0] && (
            <a href={merese.fuentes[0].url} target="_blank" rel="noreferrer" className="mt-1 inline-flex items-center gap-1 text-accent-ink hover:underline"><ExternalLink className="h-3 w-3" /> {t("Fuente", "Source")}</a>
          )}
        </div>
      )}
    </Tarjeta>
  );
}
