import { useQueries } from "@tanstack/react-query";
import {
  ArrowRight,
  Bot,
  CheckCircle2,
  Clock,
  Database,
  Droplets,
  ExternalLink,
  FileCheck2,
  Gauge,
  Globe2,
  Mountain,
  Thermometer,
  Waves,
  Workflow,
  type LucideIcon,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { api, pedir } from "../api/cliente";
import {
  useEventos,
  useExpediente,
  useExpedientes,
  useFuentes,
  useObservaciones,
  useResumen,
  useSeries,
  useVerificacion,
} from "../api/consultas";
import { BarraEstados, LineaTiempo } from "../componentes/graficos/Evidencia";
import { GraficoSerie } from "../componentes/graficos/GraficoSerie";
import {
  Boton,
  ChipEstado,
  Dato,
  ESTADOS_PRUEBA,
  ESTADOS_VERIFICACION,
  Encabezado,
  Esqueleto,
  ErrorCarga,
  Insignia,
  NOMBRES_PRUEBA,
  Tarjeta,
  VEREDICTOS,
} from "../componentes/ui";
import { CATEGORIAS_EVENTO } from "../lib/colores";
import { TEXTO_COTA, cifraCitada, conUnidad, fecha, numero, valorP } from "../lib/formato";

const SERIE_T = "chili_analisis.cabecera_power:temperatura_aire_2m:power_mensual:p1y";
type Crisis = {
  id: string;
  etiqueta: string;
  icono: LucideIcon;
  /** Índice de la cifra principal dentro de las cifras del evento. */
  principal: number;
  /** Proporción entre dos cifras citadas (se muestra como cálculo, no como dato de la fuente). */
  medidor?: { parte: number; total: number; texto: string };
};

const CRISIS: Crisis[] = [
  { id: "2023-11-almacenamiento-bajo", etiqueta: "Por falta", icono: Droplets, principal: 0, medidor: { parte: 0, total: 1, texto: "de la capacidad útil" } },
  { id: "2025-02-corte-turbidez", etiqueta: "Por exceso", icono: Waves, principal: 0 },
  { id: "2024-03-colmatacion-aguada-blanca", etiqueta: "Por desgaste", icono: Mountain, principal: 1, medidor: { parte: 1, total: 0, texto: "de la capacidad de diseño" } },
];

function Crisis() {
  const eventos = useEventos();
  if (eventos.isLoading) return <div className="grid gap-4 md:grid-cols-3">{[0, 1, 2].map((i) => <Esqueleto key={i} className="h-56" />)}</div>;
  if (eventos.error) return <ErrorCarga error={eventos.error} />;
  const porId = new Map((eventos.data ?? []).map((e) => [e.id, e]));
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {CRISIS.map(({ id, etiqueta, icono: Icono, principal, medidor }) => {
        const e = porId.get(id);
        const cifra = e?.cifras[principal];
        if (!e || !cifra) return null;
        const color = CATEGORIAS_EVENTO[e.categoria]?.color ?? "var(--accent)";
        const secundarias = e.cifras.filter((_, i) => i !== principal);
        const parte = medidor ? e.cifras[medidor.parte] : undefined;
        const total = medidor ? e.cifras[medidor.total] : undefined;
        const proporcion = parte && total && total.valor > 0 ? (parte.valor / total.valor) * 100 : null;
        const fuente = e.fuentes[0];
        return (
          <article key={id} className="relative flex flex-col overflow-hidden rounded-2xl border border-line bg-surface p-5 shadow-tarjeta animate-aparecer">
            <span aria-hidden className="absolute inset-x-0 top-0 h-[3px]" style={{ background: color }} />
            <div className="flex items-center justify-between gap-3">
              <p className="etiqueta">{etiqueta} · {fecha(e.fecha, e.precision)}</p>
              <span className="grid h-7 w-7 place-items-center rounded-lg bg-surface-2">
                <Icono aria-hidden className="h-4 w-4" style={{ color }} />
              </span>
            </div>
            <p className="cifra mt-3 text-[34px] font-semibold leading-none tracking-tight text-ink" title={TEXTO_COTA[cifra.cota]}>
              {cifraCitada(cifra)}
            </p>
            <p className="mt-1.5 text-[12.5px] text-ink-2">{cifra.descripcion}</p>
            {proporcion !== null && medidor && (
              <div className="mt-3">
                <div className="h-1.5 overflow-hidden rounded-full bg-surface-3" role="img" aria-label={`${numero(proporcion, 0)} % ${medidor.texto}`}>
                  <div className="h-full rounded-full" style={{ width: `${Math.min(100, proporcion)}%`, background: color }} />
                </div>
                <p className="mt-1.5 text-[11.5px] text-ink-3">
                  <span className="cifra font-semibold text-ink-2">{numero(proporcion, 0)} %</span> {medidor.texto} · calculado con las cifras citadas
                </p>
              </div>
            )}
            {secundarias.length > 0 && (
              <dl className="mt-3 space-y-1 border-t border-line pt-3 text-[12.5px]">
                {secundarias.map((c) => (
                  <div key={c.descripcion} className="flex items-baseline justify-between gap-3">
                    <dt className="text-ink-2">{c.descripcion}</dt>
                    <dd className="cifra shrink-0 font-semibold text-ink" title={TEXTO_COTA[c.cota]}>{cifraCitada(c)}</dd>
                  </div>
                ))}
              </dl>
            )}
            <p className="mt-3 text-[13.5px] font-medium leading-snug text-ink">{e.titulo}</p>
            {fuente && (
              <a href={fuente.url} target="_blank" rel="noreferrer" className="mt-auto inline-flex items-center gap-1 pt-3 text-[12px] text-accent-ink hover:underline">
                <ExternalLink aria-hidden className="h-3 w-3" /> Fuente: {fuente.medio ?? fuente.titulo}
              </a>
            )}
          </article>
        );
      })}
    </div>
  );
}

function PrimerResultado() {
  const expedientes = useExpedientes({ serie_id: SERIE_T });
  const id = expedientes.data?.items[0]?.id;
  const expediente = useExpediente(id);
  const obs = useObservaciones(SERIE_T);
  const series = useSeries({ variable_id: "temperatura_aire_2m" });
  const serie = series.data?.items[0];
  const r = expediente.data?.resultado;
  const tendencia = r && r.tipo === "tendencia" ? r : null;
  const elevacion = expediente.data?.procedencia.pasos?.find((p) => p.id === "descarga_power")?.metricas?.elevacion_celda_m;
  const subtitulo = [
    "Media anual del aire a 2 m · celda NASA POWER (MERRA-2)",
    typeof elevacion === "number" ? `a ${numero(elevacion, 0)} m` : null,
    tendencia ? `· ${tendencia.periodo.desde}–${tendencia.periodo.hasta}` : null,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <Tarjeta
      titulo="Primer resultado real: temperatura en la cabecera"
      subtitulo={subtitulo}
      acciones={id && <Link to={`/expedientes/${id}`}><Boton tamano="sm" icono={FileCheck2}>Expediente</Boton></Link>}
      pie={
        <>Fuente: NASA POWER (MERRA-2) y NOAA CPC (ONI) · cálculo reproducible en <code className="font-mono">scripts/analisis_preliminar.py</code></>
      }
    >
      <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
        <div>
          {obs.isLoading ? (
            <Esqueleto className="h-[300px]" />
          ) : obs.error ? (
            <ErrorCarga error={obs.error} />
          ) : (
            <GraficoSerie
              observaciones={obs.data?.observaciones ?? []}
              unidad={obs.data?.unidad ?? "Cel"}
              agregacion={serie?.agregacion}
              pendiente={tendencia?.pendiente}
              nombre="Temperatura media anual"
            />
          )}
        </div>
        <div className="space-y-4">
          {tendencia ? (
            <>
              <div>
                <p className="etiqueta">Tendencia de Sen</p>
                <p className="mt-1 text-[30px] font-semibold leading-none tracking-tight">
                  {conUnidad(tendencia.pendiente.valor, tendencia.pendiente.unidad, 2, true)}
                </p>
                <p className="mt-1 text-[12.5px] text-ink-2">
                  IC 90 %: {numero(tendencia.pendiente.intervalo.lo, 2)} a {numero(tendencia.pendiente.intervalo.hi, 2)} · p {valorP(tendencia.significancia.p_conservador)}
                </p>
              </div>
              <div>
                <p className="etiqueta mb-1.5">Veredicto</p>
                <ChipEstado mapa={VEREDICTOS} valor={tendencia.veredicto} />
              </div>
              <div>
                <p className="etiqueta mb-1.5">Sello de confianza</p>
                <ul className="space-y-1.5 text-[13px]">
                  {Object.entries(tendencia.sello).map(([k, p]) => (
                    <li key={k} className="flex items-center justify-between gap-2">
                      <span className="text-ink-2">{NOMBRES_PRUEBA[k] ?? k}</span>
                      <ChipEstado mapa={ESTADOS_PRUEBA} valor={p.estado} />
                    </li>
                  ))}
                </ul>
              </div>
            </>
          ) : (
            <Esqueleto className="h-60" />
          )}
        </div>
      </div>
    </Tarjeta>
  );
}

function Proporcion({ etiqueta, correctas, total, nota }: { etiqueta: string; correctas: number; total: number; nota: string }) {
  const pct = total > 0 ? (correctas / total) * 100 : 0;
  return (
    <div className="rounded-xl border border-line bg-surface-2 p-3">
      <p className="text-[12px] text-ink-2">{etiqueta}</p>
      <p className="mt-1 text-[20px] font-semibold leading-none tracking-tight text-ink">
        <span className="cifra">{correctas}</span>
        <span className="text-[13px] font-medium text-ink-3"> de {total}</span>
      </p>
      <div className="mt-2 h-1 overflow-hidden rounded-full bg-surface-3" aria-hidden>
        <div className="h-full rounded-full" style={{ width: `${pct}%`, background: "var(--accent)" }} />
      </div>
      <p className="mt-1.5 text-[11.5px] leading-snug text-ink-3">{nota}</p>
    </div>
  );
}

function VerificacionFuentes() {
  const verificacion = useVerificacion();
  const resumen = useResumen();
  const fuentes = useFuentes();
  const r = resumen.data;
  const pendientes = (fuentes.data ?? []).filter((f) => f.estado_verificacion !== "verificado");
  return (
    <Tarjeta
      titulo="Verificación de fuentes"
      subtitulo={verificacion.data?.fuentes ? `Consultas reales del ${fecha(verificacion.data.fuentes.generado_utc)}` : undefined}
      acciones={<Link to="/fuentes"><Boton tamano="sm" variante="fantasma" icono={ArrowRight}>Ver fuentes</Boton></Link>}
    >
      {verificacion.data ? <BarraEstados conteos={verificacion.data.estados_fuentes} /> : <Esqueleto className="h-16" />}
      {r && (
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {r.verificacion_fuentes && (
            <Proporcion
              etiqueta="Consultas a catálogos"
              correctas={r.verificacion_fuentes.correctas}
              total={r.verificacion_fuentes.total}
              nota="Respondieron lo esperado (CMR, AppEEARS, POWER, NOAA, Copernicus)"
            />
          )}
          {r.verificacion_enlaces && (
            <Proporcion
              etiqueta="Enlaces del reto y de la guía"
              correctas={r.verificacion_enlaces.correctas}
              total={r.verificacion_enlaces.total}
              nota="HTTP 200 en al menos una de las corridas automáticas"
            />
          )}
        </div>
      )}
      {pendientes.length > 0 && (
        <div className="mt-4 border-t border-line pt-3">
          <p className="etiqueta mb-2">Fuentes aún sin verificación completa</p>
          <ul className="space-y-1.5">
            {pendientes.map((f) => (
              <li key={f.id} className="flex items-center justify-between gap-3 text-[13px]">
                <span className="truncate text-ink-2" title={f.nombre}>{f.nombre}</span>
                <ChipEstado mapa={ESTADOS_VERIFICACION} valor={f.estado_verificacion} />
              </li>
            ))}
          </ul>
        </div>
      )}
    </Tarjeta>
  );
}

function VolumenRepresas() {
  const series = useSeries({ variable_id: "volumen_util" });
  const lista = (series.data?.items ?? []).filter((s) => s.unidad_id && !s.unidad_id.endsWith("sistema_regulado"));
  const valores = useQueries({
    queries: lista.map((s) => ({
      queryKey: ["observaciones", s.id],
      queryFn: () => pedir(api.GET("/api/v1/series/{serie_id}/observaciones", { params: { path: { serie_id: s.id } } })),
    })),
  });
  const filas = lista
    .map((s, i) => ({ s, obs: valores[i]?.data?.observaciones.at(-1) }))
    .filter((f) => f.obs?.valor !== null && f.obs?.valor !== undefined)
    .sort((a, b) => (b.obs?.valor ?? 0) - (a.obs?.valor ?? 0));
  const maximo = Math.max(1, ...filas.map((f) => f.obs?.valor ?? 0));
  const nombre = (id: string) =>
    id.replace("chili_analisis.", "").replace(/_/g, " ").replace("pane", "pañe").replace("bamputane", "bamputañe").replace("espanoles", "españoles");

  return (
    <Tarjeta
      titulo="Volumen útil por represa"
      subtitulo={filas[0]?.obs ? `Reporte hídrico oficial del ${fecha(filas[0].obs.t)}` : "Reporte hídrico oficial"}
      pie="Fuente: AUTODEMA (PDF transcrito; la suma coincide con el total reportado ±0,05 hm³). Dato puntual, no una serie."
    >
      {series.isLoading ? (
        <Esqueleto className="h-48" />
      ) : (
        <ul className="space-y-2.5">
          {filas.map(({ s, obs }) => (
            <li key={s.id} className="grid grid-cols-[120px_1fr_72px] items-center gap-3 text-[13px]">
              <span className="truncate capitalize text-ink-2">{nombre(s.unidad_id ?? "")}</span>
              <div className="h-2.5 rounded-full bg-surface-2">
                <div className="h-full rounded-full" style={{ width: `${((obs?.valor ?? 0) / maximo) * 100}%`, background: "var(--accent)" }} />
              </div>
              <span className="cifra text-right font-medium text-ink">{conUnidad(obs?.valor, "hm3", 1)}</span>
            </li>
          ))}
        </ul>
      )}
    </Tarjeta>
  );
}

function Modulos() {
  const resumen = useResumen();
  const r = resumen.data;
  const exp = new Map((r?.expedientes_por_tipo ?? []).map((c) => [c.clave, c.total]));
  const filas = [
    { m: "M1", nombre: "Matriz de relevancia", estado: exp.get("relevancia") ? `${exp.get("relevancia")} expediente(s)` : "Sin resultados publicados", listo: Boolean(exp.get("relevancia")) },
    { m: "M2", nombre: "Tendencias + sello", estado: exp.get("tendencia") ? `${exp.get("tendencia")} expedientes preliminares` : "Sin resultados", listo: Boolean(exp.get("tendencia")) },
    { m: "M3", nombre: "Gemelo y atribución", estado: exp.get("atribucion") ? `${exp.get("atribucion")} expediente(s)` : "Contrato listo · pendiente de integración", listo: Boolean(exp.get("atribucion")) },
    { m: "M4", nombre: "Anticipación", estado: exp.get("pronostico") || exp.get("alerta") ? "Con resultados" : "Contrato listo · pendiente de integración", listo: Boolean(exp.get("pronostico") || exp.get("alerta")) },
    { m: "M5", nombre: "Cuenca y decisión", estado: exp.get("priorizacion") || exp.get("colmatacion") ? "Con resultados" : "Contrato listo · pendiente de integración", listo: Boolean(exp.get("priorizacion") || exp.get("colmatacion")) },
    { m: "IA", nombre: "Asistente verificado", estado: r?.asistente_conectado ? "Conectado" : "No conectado · verificador numérico activo", listo: Boolean(r?.asistente_conectado) },
  ];
  return (
    <Tarjeta titulo="Estado de los módulos" subtitulo="Lo que ya produce resultados y lo que espera al pipeline de ciencia de datos">
      <ul className="divide-y divide-line">
        {filas.map((f) => (
          <li key={f.m} className="flex items-center justify-between gap-3 py-2.5">
            <span className="flex items-center gap-3">
              <span className="grid h-7 w-9 place-items-center rounded-md bg-surface-2 font-mono text-[11px] font-semibold text-ink-2">{f.m}</span>
              <span className="text-[13.5px] font-medium text-ink">{f.nombre}</span>
            </span>
            <Insignia tono={f.listo ? "good" : "neutral"} icono={f.listo ? CheckCircle2 : Clock}>{f.estado}</Insignia>
          </li>
        ))}
      </ul>
      <p className="mt-3 flex items-center gap-2 text-[12.5px] text-ink-3">
        <Workflow className="h-3.5 w-3.5" /> Trabajadores de ciencia de datos activos: <span className="font-semibold text-ink">{r?.trabajadores_activos ?? 0}</span>
      </p>
    </Tarjeta>
  );
}

export function Panel() {
  const navegar = useNavigate();
  const resumen = useResumen();
  const eventos = useEventos();
  const r = resumen.data;
  const verificadas = r?.fuentes_por_estado.find((c) => c.clave === "verificado")?.total ?? 0;
  const clima = eventos.data?.find((e) => e.categoria === "clima");
  const oni = clima?.cifras[0];

  return (
    <div className="space-y-6">
      <Encabezado
        eyebrow="Cuenca regulada del Chili · Arequipa, Perú"
        titulo="Arequipa se queda sin agua por falta… y por exceso"
        descripcion="TerraVerdict reúne datos abiertos de NASA y fuentes oficiales para saber qué cambia en la cuenca, por qué, con cuánta confianza y dónde actuar. Cada cifra de esta pantalla viene de una fuente real y citada."
        acciones={
          <>
            <Boton variante="primario" icono={Globe2} onClick={() => navegar("/mapa")}>Mapa satelital</Boton>
            <Boton icono={ArrowRight} onClick={() => navegar("/expedientes")}>Expedientes</Boton>
          </>
        }
      />

      <Crisis />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Dato
          etiqueta="El Niño en curso"
          icono={Thermometer}
          tono="critical"
          valor={oni ? numero(oni.valor, 2, { signo: true }) : "—"}
          unidad="°C"
          nota={oni ? `${oni.descripcion} · NOAA CPC` : "Cargando…"}
        />
        <Dato
          etiqueta="Fuentes verificadas"
          icono={Database}
          tono="good"
          valor={r ? `${verificadas}/${r.fuentes_total}` : "—"}
          nota="Comprobadas con consultas reales a sus catálogos oficiales"
        />
        <Dato
          etiqueta="Observaciones reales"
          icono={Gauge}
          valor={r ? numero(r.observaciones_total, 0) : "—"}
          nota={r ? `${r.series_total} series publicadas con procedencia completa` : undefined}
        />
        <Dato
          etiqueta="Asistente de IA"
          icono={Bot}
          tono={r?.asistente_conectado ? "good" : "neutral"}
          valor={r?.asistente_conectado ? "Conectado" : "En espera"}
          nota="Toda respuesta pasará por el verificador numérico, ya activo"
        />
      </div>

      <PrimerResultado />

      <div className="grid gap-6 lg:grid-cols-2">
        <VerificacionFuentes />
        <VolumenRepresas />
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
        <Tarjeta titulo="Crónica reciente" subtitulo="Eventos documentados con su fuente" acciones={<Link to="/eventos"><Boton tamano="sm" variante="fantasma" icono={ArrowRight}>Ver todo</Boton></Link>}>
          {eventos.data ? <LineaTiempo eventos={eventos.data} limite={4} /> : <Esqueleto className="h-64" />}
        </Tarjeta>
        <Modulos />
      </div>
    </div>
  );
}
