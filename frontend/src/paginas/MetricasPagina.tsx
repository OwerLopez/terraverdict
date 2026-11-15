import { BookOpenText, Grid3x3, History, Table2 } from "lucide-react";
import { useMemo, useState } from "react";
import { Area, CartesianGrid, ComposedChart, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Esquemas } from "../api/cliente";
import { useCatalogoMetricas, useHistorial, useMapasMetricas } from "../api/consultas";
import { TablaDatos } from "../componentes/fenomenos/TablaDatos";
import { type CeldaMatriz, type ColumnaMatriz, LeyendaEscala, MatrizCalor } from "../componentes/graficos/MatrizCalor";
import { Boton, Encabezado, ErrorCarga, EstadoVacio, Esqueleto, Segmentado, Tarjeta } from "../componentes/ui";
import { RAMPA_AZUL, RAMPA_NARANJA, colorDivergente, colorSecuencial, useColores } from "../lib/colores";
import { fechaHora, numero, valorP } from "../lib/formato";
import { t } from "../lib/i18n";
import { UMBRAL_P_DM, evidencia, nombreFamilia, nombreModelo, nombreSerie, nombreTarea } from "../lib/modelos";
import { FichaMetrica, ImportanciaVariables, InsigniaEvidencia, TEXTO_EVIDENCIA, bilingue, partesTitulo } from "../componentes/metricas/compartidos";

type Ficha = Esquemas["FichaMetrica"];
type Mapas = Esquemas["MapasMetricas"];
type Historial = Esquemas["ResultadoHistorialMetricas"];
type TareaHistorial = Esquemas["HistorialTarea"];
type VentanaCaos = Esquemas["VentanaCaos"];

const DIVERGENTE: string[] = [...[...RAMPA_NARANJA].reverse(), "var(--neutral-mid)", ...RAMPA_AZUL];
const ORDEN_FAMILIA: Record<string, number> = { referencia: 0, clasico: 1, red_neuronal: 2, ensamble: 3 };

// ------------------------------------------------------------------------------------------------
// 1. Mapa de calor modelo × tarea, una métrica a la vez

type MetricaMapa = "prueba" | "validacion" | "ic90" | "p_dm" | "dispersion";

function valorCelda(c: Mapas["celdas"][number], m: MetricaMapa): number | null {
  if (m === "prueba") return c.puntaje_prueba ?? null;
  if (m === "validacion") return c.puntaje_validacion;
  if (m === "ic90") return c.ic90_inferior ?? null;
  if (m === "p_dm") return c.p_diebold_mariano ?? null;
  return c.dispersion_semillas ?? null;
}

function MapaMetricas({ mapas, fichas }: { mapas: Mapas; fichas: Map<string, Ficha> }) {
  const [metrica, setMetrica] = useState<MetricaMapa>("prueba");
  const indice = useMemo(() => new Map(mapas.celdas.map((c) => [`${c.modelo}|${c.expediente_id}`, c])), [mapas]);
  // Cada columna (tarea) usa su propia métrica principal: el color se escala por columna.
  const escala = useMemo(() => {
    const e = new Map<string, number>();
    for (const tarea of mapas.tareas) {
      const vals = mapas.celdas.filter((c) => c.expediente_id === tarea.expediente_id).map((c) => valorCelda(c, metrica)).filter((v): v is number => v !== null);
      e.set(tarea.expediente_id, metrica === "dispersion" ? Math.max(1e-9, ...vals) : Math.max(1e-9, ...vals.map(Math.abs)));
    }
    return e;
  }, [mapas, metrica]);

  const columnas: ColumnaMatriz[] = mapas.tareas.map((x) => ({ id: x.expediente_id, ...partesTitulo(x.titulo) }));
  const filas = mapas.modelos.map((m) => ({ id: m.nombre, etiqueta: nombreModelo(m.nombre), sub: nombreFamilia(m.familia) }));
  const idFicha: Record<MetricaMapa, string> = { prueba: "bss_climatologia", validacion: "puntaje_validacion", ic90: "ic90", p_dm: "p_diebold_mariano", dispersion: "dispersion_semillas" };

  const celda = (f: { id: string }, col: ColumnaMatriz): CeldaMatriz | undefined => {
    const c = indice.get(`${f.id}|${col.id}`);
    if (!c) return undefined;
    const v = valorCelda(c, metrica);
    const tarea = mapas.tareas.find((x) => x.expediente_id === col.id);
    const detalle = t(
      `${nombreModelo(c.modelo)} · ${col.etiqueta}: validación ${numero(c.puntaje_validacion, 3)}, prueba ${numero(c.puntaje_prueba, 3)}, IC90 ${numero(c.ic90_inferior, 3)} a ${numero(c.ic90_superior, 3)}, p DM ${valorP(c.p_diebold_mariano)}, evidencia ${TEXTO_EVIDENCIA[evidencia(c.ic90_inferior, c.p_diebold_mariano)]()}${tarea?.mejor_validacion === c.modelo ? " · elegido en validación" : ""}`,
      `${nombreModelo(c.modelo)} · ${col.etiqueta}: validation ${numero(c.puntaje_validacion, 3)}, test ${numero(c.puntaje_prueba, 3)}, 90 % CI ${numero(c.ic90_inferior, 3)} to ${numero(c.ic90_superior, 3)}, DM p ${valorP(c.p_diebold_mariano)}, evidence ${TEXTO_EVIDENCIA[evidencia(c.ic90_inferior, c.p_diebold_mariano)]()}${tarea?.mejor_validacion === c.modelo ? " · chosen on validation" : ""}`,
    );
    if (v === null) return { texto: "—", detalle };
    const e = escala.get(col.id) ?? 1;
    const color =
      metrica === "p_dm" ? colorDivergente(v, 0.5, UMBRAL_P_DM, false) : metrica === "dispersion" ? colorSecuencial(v / e) : colorDivergente(v, e);
    return { texto: metrica === "p_dm" ? valorP(v) : numero(v, metrica === "dispersion" ? 3 : 2), color, detalle, marcada: tarea?.mejor_validacion === c.modelo };
  };

  const ficha = fichas.get(idFicha[metrica]);
  return (
    <Tarjeta
      titulo={<span className="flex items-center gap-2"><Grid3x3 className="h-4 w-4 text-accent" /> {t("Mapa de calor: cada modelo en cada tarea", "Heatmap: every model on every task")}</span>}
      subtitulo={t(
        "Cifras publicadas en los expedientes de comparación de modelos. El borde marca el modelo elegido en validación; la prueba no participa en la elección.",
        "Figures published in the model-comparison case files. The outline marks the model chosen on validation; the test period takes no part in the choice.",
      )}
    >
      <div className="mb-3 flex flex-wrap gap-2">
        <Segmentado
          etiqueta={t("Métrica del mapa", "Heatmap metric")}
          valor={metrica}
          alCambiar={setMetrica}
          opciones={[
            { valor: "prueba", texto: t("Habilidad en prueba", "Test skill") },
            { valor: "validacion", texto: t("En validación", "On validation") },
            { valor: "ic90", texto: t("IC90 inferior", "90 % CI lower") },
            { valor: "p_dm", texto: "p Diebold-Mariano" },
            { valor: "dispersion", texto: t("Entre semillas", "Across seeds") },
          ]}
        />
      </div>
      <MatrizCalor
        titulo={t("Métricas por modelo y tarea", "Metrics by model and task")}
        etiquetaFilas={t("Modelo", "Model")}
        filas={filas}
        columnas={columnas}
        celda={celda}
        leyenda={
          metrica === "dispersion" ? (
            <LeyendaEscala colores={[...RAMPA_AZUL]} izquierda={t("estable", "stable")} derecha={t("varía con la semilla", "varies with seed")} />
          ) : (
            <LeyendaEscala
              colores={DIVERGENTE}
              izquierda={metrica === "p_dm" ? t("p alto (sin evidencia)", "high p (no evidence)") : t("peor que la climatología", "worse than climatology")}
              centro={metrica === "p_dm" ? t(`centro: p = ${numero(UMBRAL_P_DM, 2)}`, `centre: p = ${numero(UMBRAL_P_DM, 2)}`) : t("gris: igual que la climatología (0)", "grey: same as climatology (0)")}
              derecha={metrica === "p_dm" ? t("p bajo (evidencia)", "low p (evidence)") : t("mejor", "better")}
              nota={metrica !== "p_dm" ? t("Cada columna usa la métrica principal de su tarea (Brier, ECM o bits) y su propia escala de color.", "Each column uses its task's main metric (Brier, MSE or bits) and its own colour scale.") : undefined}
            />
          )
        }
      />
      {metrica === "prueba" ? (
        <div className="mt-3 grid gap-2 md:grid-cols-3">
          {["bss_climatologia", "habilidad_climatologia", "ganancia_informacion_bits"].map((id) => {
            const f = fichas.get(id);
            return f ? <FichaMetrica key={id} ficha={f} compacta /> : null;
          })}
        </div>
      ) : (
        ficha && <div className="mt-3"><FichaMetrica ficha={ficha} compacta /></div>
      )}
    </Tarjeta>
  );
}

// ------------------------------------------------------------------------------------------------
// 3. Historial año a año (origen móvil)

const REGIMEN = {
  validacion_del_diseno: () => t("Validación del diseño (optimista)", "Design validation (optimistic)"),
  fuera_de_muestra: () => t("Fuera de muestra", "Out of sample"),
};

function HistorialPronostico({ historial, fichas }: { historial: Historial; fichas: Map<string, Ficha> }) {
  const claves = Object.keys(historial.tareas);
  const [clave, setClave] = useState(claves[0] ?? "");
  const [tabla, setTabla] = useState(false);
  const c = useColores();
  const tarea = historial.tareas[clave] as TareaHistorial | undefined;

  const modelos = useMemo(() => {
    if (!tarea) return [];
    const m = new Map<string, string>();
    for (const a of tarea.anios) for (const [k, v] of Object.entries(a.modelos ?? {})) m.set(k, v.familia);
    return [...m.entries()].sort((a, b) => (ORDEN_FAMILIA[a[1]] ?? 9) - (ORDEN_FAMILIA[b[1]] ?? 9) || a[0].localeCompare(b[0]));
  }, [tarea]);

  if (!tarea) return null;
  const red = tarea.diseno.red;
  const principal = tarea.lectura_principal ?? null;
  // Clásico de comparación elegido por VALIDACIÓN (media del puntaje de validación de cada corte):
  // elegirlo por la cifra de prueba sería sesgo de selección.
  const clasicos = modelos.filter(([, f]) => f === "clasico").map(([k]) => k);
  const validacionMedia = (k: string) => {
    const v = tarea.anios.map((a) => a.modelos?.[k]?.validacion).filter((x): x is number => typeof x === "number");
    return v.length ? v.reduce((s, x) => s + x, 0) / v.length : -1e9;
  };
  const mejorClasico = [...clasicos].sort((a, b) => validacionMedia(b) - validacionMedia(a))[0];
  const ordenAgregado = (claves: string[]) => {
    const primeros = [principal, red].filter((k): k is string => !!k && claves.includes(k));
    const familia = (k: string) => ORDEN_FAMILIA[modelos.find(([m]) => m === k)?.[1] ?? ""] ?? 9;
    return [...primeros, ...claves.filter((k) => !primeros.includes(k)).sort((a, b) => familia(a) - familia(b) || a.localeCompare(b))];
  };
  const escala = Math.max(1e-9, ...tarea.anios.flatMap((a) => Object.values(a.modelos ?? {}).map((m) => Math.abs(m.prueba ?? 0))));
  const columnas: ColumnaMatriz[] = tarea.anios.map((a) => ({ id: String(a.anio), etiqueta: String(a.anio), sub: `n ${a.n.prueba ?? 0}`, grupo: REGIMEN[a.regimen]() }));
  const datos = tarea.anios
    .filter((a) => !a.omitido)
    .map((a) => ({
      anio: a.anio,
      red: a.modelos?.[red]?.prueba ?? null,
      banda: a.modelos?.[red]?.ic90?.length === 2 ? [a.modelos[red]?.ic90?.[0] ?? null, a.modelos[red]?.ic90?.[1] ?? null] : null,
      clasico: mejorClasico ? (a.modelos?.[mejorClasico]?.prueba ?? null) : null,
      persistencia: a.modelos?.ref_persistencia?.prueba ?? null,
    }));
  const frontera = historial.metodo && typeof historial.metodo === "object" ? Number((historial.metodo as Record<string, unknown>).frontera_diseno) : NaN;
  const ficha = fichas.get(tarea.metrica_principal);

  return (
    <Tarjeta
      titulo={<span className="flex items-center gap-2"><History className="h-4 w-4 text-accent" /> {t("Historial año a año: ¿cómo habría rendido cada modelo?", "Year-by-year history: how would each model have performed?")}</span>}
      subtitulo={t(
        `Origen móvil: para cada año Y se entrena con datos hasta Y−2, se calibra con Y−1 y se evalúa en Y, con el diseño congelado (red ${nombreModelo(red)}, ventana ${tarea.diseno.ventana}). Los años hasta ${frontera} sirvieron para elegir el diseño: su lectura es optimista.`,
        `Rolling origin: for each year Y the model trains on data up to Y−2, calibrates on Y−1 and is evaluated on Y, with the frozen design (${nombreModelo(red)} network, window ${tarea.diseno.ventana}). Years up to ${frontera} were used to choose the design: read them as optimistic.`,
      )}
      pie={tarea.descripcion}
    >
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <Segmentado etiqueta={t("Tarea", "Task")} valor={clave} alCambiar={setClave} opciones={claves.map((k) => ({ valor: k, texto: nombreTarea(k) }))} />
      </div>
      <div className="mb-5">
        <h3 className="mb-1 text-[13.5px] font-semibold text-ink">{t("Habilidad agregada por régimen", "Aggregated skill by regime")}</h3>
        <p className="mb-2 text-[12.5px] text-ink-2">
          {t(
            "Lectura principal (primera fila de cada régimen): el modelo que eligió la validación de cada año. Las demás filas son comparaciones en orden fijo; elegir entre ellas la de mejor cifra en la prueba sería sesgo de selección.",
            "Main reading (first row of each regime): the model chosen on each year's validation. The other rows are comparisons in a fixed order; picking the one with the best test score would be selection bias.",
          )}
        </p>
        <div className="overflow-x-auto rounded-xl border border-line">
          <table className="w-full text-[12.5px]">
            <caption className="sr-only">{t("Habilidad agregada por régimen", "Aggregated skill by regime")}</caption>
            <thead className="bg-surface-2 text-left text-ink-2">
              <tr>
                <th className="px-3 py-2 font-medium">{t("Régimen", "Regime")}</th>
                <th className="px-3 py-2 font-medium">{t("Modelo", "Model")}</th>
                <th className="px-3 py-2 text-right font-medium">{t("Habilidad", "Skill")}</th>
                <th className="px-3 py-2 text-right font-medium">IC90</th>
                <th className="px-3 py-2 text-right font-medium">{t("p DM", "DM p")}</th>
                <th className="px-3 py-2 text-right font-medium">{t("Años", "Years")}</th>
                <th className="px-3 py-2 font-medium">{t("Evidencia", "Evidence")}</th>
              </tr>
            </thead>
            <tbody>
              {(["fuera_de_muestra", "validacion_del_diseno"] as const).flatMap((reg) =>
                ordenAgregado(Object.keys(tarea.agregado?.[reg] ?? {}).filter((k) => k !== "ref_climatologia"))
                  .map((k) => [k, (tarea.agregado?.[reg] ?? {})[k]] as const)
                  .filter((par): par is readonly [string, NonNullable<(typeof par)[1]>] => !!par[1])
                  .map(([k, v]) => (
                    <tr key={`${reg}-${k}`} className={`border-t border-line ${k === principal ? "bg-surface-2" : ""}`}>
                      <td className="px-3 py-1.5 text-ink-2">{REGIMEN[reg]()}</td>
                      <td className={`px-3 py-1.5 text-ink ${k === principal ? "font-semibold" : "font-medium"}`}>{nombreModelo(k)}{k === red ? ` · ${t("red congelada", "frozen network")}` : ""}{k === principal ? ` · ${t("lectura principal", "main reading")}` : ""}</td>
                      <td className="cifra px-3 py-1.5 text-right">{numero(v.valor, 3)}</td>
                      <td className="cifra px-3 py-1.5 text-right">{numero(v.ic90?.[0], 3)} – {numero(v.ic90?.[1], 3)}</td>
                      <td className="cifra px-3 py-1.5 text-right">{valorP(v.p_diebold_mariano)}</td>
                      <td className="cifra px-3 py-1.5 text-right">{v.anios}</td>
                      <td className="px-3 py-1.5"><InsigniaEvidencia lo={v.ic90?.[0]} p={v.p_diebold_mariano} /></td>
                    </tr>
                  )),
              )}
            </tbody>
          </table>
        </div>
      </div>
      <p className="mb-2 text-[12.5px] text-ink-2">
        {t("Detalle por año (contexto: cada año tiene pocas observaciones, 12 meses en sequía y sismos; no se lee por separado).", "Per-year detail (context: each year has few observations, 12 months for drought and earthquakes; not read on its own).")}
      </p>
      <MatrizCalor
        titulo={t("Habilidad en prueba por modelo y año", "Test skill by model and year")}
        etiquetaFilas={t("Modelo", "Model")}
        filas={modelos.map(([k, f]) => ({ id: k, etiqueta: nombreModelo(k), sub: k === red ? t("red congelada", "frozen network") : nombreFamilia(f) }))}
        columnas={columnas}
        celda={(f, col) => {
          const a = tarea.anios.find((x) => String(x.anio) === col.id);
          if (!a) return undefined;
          if (a.omitido) return { texto: "—", detalle: t(`${col.etiqueta}: no evaluado (${a.omitido})`, `${col.etiqueta}: not evaluated (${a.omitido})`), omitida: a.omitido };
          const m = a.modelos?.[f.id];
          if (!m) return undefined;
          const v = m.prueba ?? null;
          return {
            texto: v === null ? "—" : numero(v, 2),
            color: v === null ? undefined : colorDivergente(v, escala),
            marcada: a.elegido_en_validacion === f.id,
            detalle: t(
              `${nombreModelo(f.id)} en ${col.etiqueta} (${REGIMEN[a.regimen]()}, n ${a.n.prueba}): ${numero(v, 3)}, IC90 ${numero(m.ic90?.[0], 3)} a ${numero(m.ic90?.[1], 3)}, p DM ${valorP(m.p_diebold_mariano)}${a.elegido_en_validacion === f.id ? " · elegido en la validación de ese corte" : ""}`,
              `${nombreModelo(f.id)} in ${col.etiqueta} (${REGIMEN[a.regimen]()}, n ${a.n.prueba}): ${numero(v, 3)}, 90 % CI ${numero(m.ic90?.[0], 3)} to ${numero(m.ic90?.[1], 3)}, DM p ${valorP(m.p_diebold_mariano)}${a.elegido_en_validacion === f.id ? " · chosen on that fold's validation" : ""}`,
            ),
          };
        }}
        leyenda={<LeyendaEscala colores={DIVERGENTE} izquierda={t("peor que la climatología", "worse than climatology")} centro={t("gris: igual (0) · borde: elegido en la validación del corte", "grey: equal (0) · outline: chosen on the fold's validation")} derecha={t("mejor", "better")} />}
      />

      <div className="mt-5">
        <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
          <ul className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[12.5px] text-ink-2" aria-label={t("Leyenda", "Legend")}>
            <li className="flex items-center gap-1.5"><span className="h-0.5 w-4 rounded" style={{ background: c.serie1 }} />{nombreModelo(red)}</li>
            <li className="flex items-center gap-1.5"><span className="h-3 w-4 rounded-sm" style={{ background: c.banda }} />{t("IC90 de la red", "Network 90 % CI")}</li>
            {mejorClasico && <li className="flex items-center gap-1.5"><span className="h-0 w-4 border-t-2 border-dashed" style={{ borderColor: c.serie2 }} />{nombreModelo(mejorClasico)} ({t("clásico elegido en validación", "classical chosen on validation")})</li>}
            <li className="flex items-center gap-1.5"><span className="h-0 w-4 border-t-2 border-dotted" style={{ borderColor: c.tinta3 }} />{nombreModelo("ref_persistencia")}</li>
          </ul>
          <Boton tamano="sm" variante="fantasma" icono={Table2} onClick={() => setTabla((v) => !v)} aria-pressed={tabla}>
            {tabla ? t("Ver gráfico", "Show chart") : t("Ver tabla", "Show table")}
          </Boton>
        </div>
        {tabla ? (
          <TablaDatos
            titulo={t("Habilidad por año", "Skill by year")}
            columnas={[t("Año", "Year"), nombreModelo(red), "IC90", mejorClasico ? nombreModelo(mejorClasico) : "—", nombreModelo("ref_persistencia")]}
            filas={datos.map((d) => [d.anio, numero(d.red, 3), d.banda ? `${numero(d.banda[0], 3)} – ${numero(d.banda[1], 3)}` : "—", numero(d.clasico, 3), numero(d.persistencia, 3)])}
          />
        ) : (
          <div className="h-[260px]" role="img" aria-label={t(`Habilidad por año de ${nombreModelo(red)} frente a la climatología`, `Skill by year of ${nombreModelo(red)} versus climatology`)}>
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={datos} margin={{ top: 8, right: 12, bottom: 0, left: 4 }}>
                <CartesianGrid stroke={c.rejilla} vertical={false} />
                <XAxis dataKey="anio" type="number" domain={["dataMin", "dataMax"]} ticks={datos.map((d) => d.anio)} allowDecimals={false} tick={{ fill: c.tinta3, fontSize: 11 }} tickLine={false} axisLine={{ stroke: c.eje }} />
                <YAxis width={48} tick={{ fill: c.tinta3, fontSize: 11 }} tickLine={false} axisLine={false} tickFormatter={(v: number) => numero(v, 1)} />
                <ReferenceLine y={0} stroke={c.tinta3} label={{ value: t("climatología", "climatology"), position: "insideBottomRight", fill: c.tinta3, fontSize: 10.5 }} />
                {Number.isFinite(frontera) && <ReferenceLine x={frontera + 0.5} stroke={c.eje} strokeDasharray="4 4" />}
                <Tooltip
                  isAnimationActive={false}
                  formatter={(v: unknown, nombre: string) => [Array.isArray(v) ? `${numero(v[0] as number, 3)} – ${numero(v[1] as number, 3)}` : numero(v as number, 3), nombre]}
                  contentStyle={{ background: c.superficie, border: `1px solid ${c.rejilla}`, borderRadius: 12, fontSize: 12 }}
                />
                <Area dataKey="banda" name={t("IC90", "90 % CI")} stroke="none" fill={c.banda} isAnimationActive={false} activeDot={false} />
                <Line dataKey="red" name={nombreModelo(red)} stroke={c.serie1} strokeWidth={2} dot={{ r: 3 }} isAnimationActive={false} connectNulls={false} />
                {mejorClasico && <Line dataKey="clasico" name={nombreModelo(mejorClasico)} stroke={c.serie2} strokeWidth={2} strokeDasharray="6 4" dot={false} isAnimationActive={false} />}
                <Line dataKey="persistencia" name={nombreModelo("ref_persistencia")} stroke={c.tinta3} strokeWidth={1.5} strokeDasharray="2 3" dot={false} isAnimationActive={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {ficha && <div className="mt-3"><FichaMetrica ficha={ficha} compacta /></div>}
    </Tarjeta>
  );
}

// ------------------------------------------------------------------------------------------------
// 4. Historial de la dinámica (caos en ventanas)

type MetricaCaos = "entropia_permutacion" | "entropia_muestral" | "lyapunov" | "determinismo" | "k_01" | "p_no_linealidad";

function HistorialCaos({ historial, fichas }: { historial: Historial; fichas: Map<string, Ficha> }) {
  const [metrica, setMetrica] = useState<MetricaCaos>("p_no_linealidad");
  const series = Object.entries(historial.caos ?? {});
  const anios = useMemo(() => [...new Set(series.flatMap(([, s]) => s.ventanas.map((v) => v.fin)))].sort((a, b) => a - b), [series]);
  const valores = series.flatMap(([, s]) => s.ventanas.map((v) => v[metrica] as number | null | undefined)).filter((v): v is number => typeof v === "number");
  const min = Math.min(...valores);
  const max = Math.max(...valores);
  // p mínimo POSIBLE con el número de sustitutos (lo guarda el resultado); sin él, se rotula como observado
  const minimosPosibles = series.map(([, s]) => s.resumen?.p_minimo_posible).filter((v): v is number => typeof v === "number");
  const pMinimoEsPosible = minimosPosibles.length === series.length && minimosPosibles.length > 0;
  const pMinimo = pMinimoEsPosible ? Math.min(...minimosPosibles) : Math.min(...series.flatMap(([, s]) => s.ventanas.map((v) => v.p_no_linealidad ?? 1)));
  if (!series.length) return null;
  const ficha = fichas.get(metrica);
  const nombres: Record<MetricaCaos, string> = {
    p_no_linealidad: t("No linealidad (p)", "Nonlinearity (p)"),
    entropia_permutacion: t("Entropía de permutación", "Permutation entropy"),
    entropia_muestral: t("Entropía muestral", "Sample entropy"),
    lyapunov: "λ Lyapunov",
    determinismo: t("Determinismo", "Determinism"),
    k_01: "K 0-1",
  };
  return (
    <Tarjeta
      titulo={<span className="flex items-center gap-2"><History className="h-4 w-4 text-accent" /> {t("Historial de la dinámica: teoría del caos en ventanas deslizantes", "Dynamics history: chaos theory in sliding windows")}</span>}
      subtitulo={t(
        "Cada columna es una ventana de varios años que termina ese año (paso anual), con los mismos métodos validados con Lorenz, Hénon y el mapa logístico. Muestra si la dinámica cambió con el tiempo.",
        "Each column is a multi-year window ending that year (annual step), using the same methods validated on Lorenz, Hénon and the logistic map. It shows whether the dynamics changed over time.",
      )}
      pie={
        Object.keys(historial.series_omitidas ?? {}).length
          ? t(`Series sin crudos locales: ${Object.keys(historial.series_omitidas ?? {}).map(nombreSerie).join(", ")}.`, `Series without local raw data: ${Object.keys(historial.series_omitidas ?? {}).map(nombreSerie).join(", ")}.`)
          : undefined
      }
    >
      <div className="mb-3">
        <Segmentado etiqueta={t("Invariante", "Invariant")} valor={metrica} alCambiar={setMetrica} opciones={(Object.keys(nombres) as MetricaCaos[]).map((k) => ({ valor: k, texto: nombres[k] }))} />
      </div>
      <MatrizCalor
        titulo={t("Invariantes de caos por serie y ventana", "Chaos invariants by series and window")}
        etiquetaFilas={t("Serie", "Series")}
        anchoFila={220}
        filas={series.map(([k, s]) => ({
          id: k,
          etiqueta: nombreSerie(k),
          sub: s.resumen
            ? t(
                `ventana de ${s.ventana_anios} años · p ≤ ${numero(s.resumen.alfa, 2)}: ${s.resumen.p_sin_corregir}/${s.resumen.evaluadas} sin corregir, ${s.resumen.q_bh} con BH, ${s.resumen.p_holm} con Holm`,
                `${s.ventana_anios}-year window · p ≤ ${numero(s.resumen.alfa, 2)}: ${s.resumen.p_sin_corregir}/${s.resumen.evaluadas} uncorrected, ${s.resumen.q_bh} with BH, ${s.resumen.p_holm} with Holm`,
              )
            : t(`ventana de ${s.ventana_anios} años`, `${s.ventana_anios}-year window`),
        }))}
        columnas={anios.map((a) => ({ id: String(a), etiqueta: `’${String(a).slice(2)}`, sub: undefined }))}
        celda={(f, col) => {
          const s = historial.caos?.[f.id];
          const v: VentanaCaos | undefined = s?.ventanas.find((x) => String(x.fin) === col.id);
          if (!v) return undefined;
          const rango = `${v.inicio}–${v.fin}`;
          if (v.omitido) return { texto: "—", omitida: v.omitido, detalle: t(`${f.etiqueta}, ${rango}: no evaluada (${v.omitido})`, `${f.etiqueta}, ${rango}: not evaluated (${v.omitido})`) };
          const x = v[metrica] as number | null | undefined;
          if (typeof x !== "number") return { texto: "—", detalle: `${f.etiqueta}, ${rango}` };
          // p: evidencia de no linealidad en escala −log10(p), saturada en el p mínimo alcanzable (1/(n+1))
          const color = metrica === "p_no_linealidad" ? colorSecuencial(-Math.log10(x) / -Math.log10(pMinimo)) : colorSecuencial(max > min ? (x - min) / (max - min) : 0.5);
          return {
            texto: metrica === "p_no_linealidad" ? valorP(x) : numero(x, 2),
            color,
            marcada: metrica === "p_no_linealidad" && x <= 0.05,
            detalle: t(
              `${f.etiqueta}, ventana ${rango} (n ${v.n}): entropía de permutación ${numero(v.entropia_permutacion, 3)} (orden ${v.orden_permutacion}), entropía muestral ${numero(v.entropia_muestral, 3)}, λ ${numero(v.lyapunov, 4)}, determinismo ${numero(v.determinismo, 3)}, K ${numero(v.k_01, 2)}, p no linealidad ${valorP(v.p_no_linealidad)} (sin corregir; Holm ${valorP(v.p_holm)}, BH ${valorP(v.q_bh)})`,
              `${f.etiqueta}, window ${rango} (n ${v.n}): permutation entropy ${numero(v.entropia_permutacion, 3)} (order ${v.orden_permutacion}), sample entropy ${numero(v.entropia_muestral, 3)}, λ ${numero(v.lyapunov, 4)}, determinism ${numero(v.determinismo, 3)}, K ${numero(v.k_01, 2)}, nonlinearity p ${valorP(v.p_no_linealidad)} (uncorrected; Holm ${valorP(v.p_holm)}, BH ${valorP(v.q_bh)})`,
            ),
          };
        }}
        leyenda={
          metrica === "p_no_linealidad" ? (
            <LeyendaEscala colores={[...RAMPA_AZUL]} izquierda={t("p alto: compatible con ruido lineal", "high p: consistent with linear noise")} centro={t("borde: p ≤ 0,05 sin corregir (descriptivo: las ventanas se solapan y no se ajustan por comparaciones múltiples)", "outline: p ≤ 0.05 uncorrected (descriptive: windows overlap and are not adjusted for multiple comparisons)")} derecha={pMinimoEsPosible ? t(`p bajo: no lineal (mínimo posible ${valorP(pMinimo)})`, `low p: nonlinear (lowest possible ${valorP(pMinimo)})`) : t(`p bajo: no lineal (mínimo observado ${valorP(pMinimo)})`, `low p: nonlinear (lowest observed ${valorP(pMinimo)})`)} />
          ) : (
            <LeyendaEscala colores={[...RAMPA_AZUL]} izquierda={numero(min, 2)} derecha={numero(max, 2)} nota={t("Escala común a todas las series para comparar entre ellas.", "One scale for all series so they can be compared.")} />
          )
        }
      />
      {ficha && <div className="mt-3"><FichaMetrica ficha={ficha} compacta /></div>}
    </Tarjeta>
  );
}

// ------------------------------------------------------------------------------------------------
// 5. Página

export function MetricasPagina() {
  const catalogo = useCatalogoMetricas();
  const mapas = useMapasMetricas();
  const historial = useHistorial();
  const fichas = useMemo(() => new Map((catalogo.data?.metricas ?? []).map((m) => [m.id, m])), [catalogo.data]);
  const resultado = historial.data?.resultado as unknown as Historial | null | undefined;
  const grupos = catalogo.data?.grupos ?? {};

  return (
    <div className="space-y-6">
      <Encabezado
        eyebrow={t("M8 · Métricas e historial", "M8 · Metrics and history")}
        titulo={t("Métricas, mapas de calor e historial", "Metrics, heatmaps and history")}
        descripcion={t(
          "Todas las métricas con que se evalúan los modelos, cada una explicada. Los mapas muestran cada modelo en cada tarea y cómo habría rendido año a año con los datos de entonces. El historial de la dinámica muestra si el carácter caótico o lineal de cada serie cambió con el tiempo.",
          "Every metric used to evaluate the models, each one explained. The heatmaps show every model on every task and how it would have performed year by year with the data available then. The dynamics history shows whether each series' chaotic or linear character changed over time.",
        )}
      />

      {mapas.isLoading ? <Esqueleto className="h-80" /> : mapas.error ? <ErrorCarga error={mapas.error} /> : mapas.data && mapas.data.tareas.length ? (
        <>
          <MapaMetricas mapas={mapas.data} fichas={fichas} />
          <ImportanciaVariables mapas={mapas.data} ficha={fichas.get("importancia_permutacion")} />
        </>
      ) : (
        <EstadoVacio titulo={t("Sin comparaciones de modelos publicadas", "No published model comparisons")}>{t("Corra tv experimentos y tv publicar para ver los mapas de calor.", "Run tv experimentos and tv publicar to see the heatmaps.")}</EstadoVacio>
      )}

      {historial.isLoading ? <Esqueleto className="h-96" /> : historial.error ? <ErrorCarga error={historial.error} /> : resultado ? (
        <>
          <p className="text-[12px] text-ink-3">
            {t("Historial", "History")}: {historial.data?.expediente_id} · {fechaHora(historial.data?.generado_utc)}
          </p>
          <HistorialPronostico historial={resultado} fichas={fichas} />
          <HistorialCaos historial={resultado} fichas={fichas} />
        </>
      ) : (
        <EstadoVacio titulo={t("Sin historial publicado", "No published history")}>{t("Corra tv experimentos --solo historial y tv publicar.", "Run tv experimentos --solo historial and tv publicar.")}</EstadoVacio>
      )}

      <section aria-labelledby="fichas-metricas">
        <h2 id="fichas-metricas" className="mb-3 flex items-center gap-2 text-[17px] font-semibold text-ink">
          <BookOpenText className="h-4 w-4 text-accent" /> {t("Fichas de las métricas", "Metric reference cards")}
        </h2>
        {catalogo.isLoading ? <Esqueleto className="h-60" /> : catalogo.error ? <ErrorCarga error={catalogo.error} /> : (
          <div className="space-y-5">
            {Object.entries(grupos).map(([id, nombre]) => {
              const lista = (catalogo.data?.metricas ?? []).filter((m) => m.grupo === id);
              if (!lista.length) return null;
              return (
                <div key={id}>
                  <h3 className="etiqueta mb-2">{bilingue(nombre)}</h3>
                  <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                    {lista.map((m) => <FichaMetrica key={m.id} ficha={m} />)}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
