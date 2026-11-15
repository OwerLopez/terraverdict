import { Activity, ShieldAlert } from "lucide-react";
import type { ExpressionSpecification } from "maplibre-gl";
import { useCallback, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Esquemas } from "../api/cliente";
import { useCapaSismos, useExpedienteVigente, useExpedientes } from "../api/consultas";
import { MapaPuntos } from "../componentes/fenomenos/MapaPuntos";
import { TablaDatos } from "../componentes/fenomenos/TablaDatos";
import { Dato, Encabezado, ErrorCarga, EstadoVacio, Esqueleto, NotaFuente, Segmentado, Tarjeta } from "../componentes/ui";
import { RAMPA_AZUL, useColores } from "../lib/colores";
import { numero } from "../lib/formato";

type Sismicidad = Esquemas["ResultadoSismicidad"];

/** Profundidad (km) → rampa azul secuencial: someros claros, profundos oscuros. */
const PASOS_PROFUNDIDAD = [0, 35, 70, 150, 300] as const;
const COLOR_PROFUNDIDAD: ExpressionSpecification = [
  "step",
  ["coalesce", ["get", "profundidad_km"], 0],
  RAMPA_AZUL[1],
  35,
  RAMPA_AZUL[2],
  70,
  RAMPA_AZUL[3],
  150,
  RAMPA_AZUL[5],
  300,
  RAMPA_AZUL[6],
];
const RADIO_MAGNITUD: ExpressionSpecification = ["interpolate", ["linear"], ["get", "magnitud"], 5, 3, 6, 6, 7, 11, 8.5, 20];

export function SismosPagina() {
  const [magnitudMin, setMagnitudMin] = useState<"5" | "6" | "7">("5");
  const capa = useCapaSismos(Number(magnitudMin));
  const { detalle } = useExpedienteVigente("sismicidad");
  const comparaciones = useExpedientes({ tipo: "comparacion_modelos" });
  const conteos = comparaciones.data?.items.find((e) => e.titulo.startsWith("Conteo sísmico"));
  const colores = useColores();
  const r = detalle.data?.resultado.tipo === "sismicidad" ? (detalle.data.resultado as Sismicidad) : undefined;
  const anuales = useMemo(
    () => Object.entries(r?.conteos_anuales ?? {}).map(([anio, n]) => ({ anio, n })),
    [r?.conteos_anuales],
  );
  const etiqueta = useCallback(
    (p: Record<string, unknown>) =>
      `M ${numero(Number(p.magnitud), 1)} · ${String(p.fecha)} · ${p.profundidad_km != null ? `${numero(Number(p.profundidad_km), 0)} km` : "profundidad sin dato"}`,
    [],
  );
  const puntos = capa.data?.features ?? [];

  return (
    <>
      <Encabezado
        eyebrow="Fenómenos naturales"
        titulo="Actividad sísmica"
        descripcion="Catálogo USGS a 350 km de Arequipa: completitud, valor b y tasas. Describe la sismicidad; no pronostica sismos."
        acciones={
          <Segmentado
            etiqueta="Magnitud mínima en el mapa"
            valor={magnitudMin}
            alCambiar={setMagnitudMin}
            opciones={[
              { valor: "5", texto: "M ≥ 5" },
              { valor: "6", texto: "M ≥ 6" },
              { valor: "7", texto: "M ≥ 7" },
            ]}
          />
        }
      />
      {(capa.isError || detalle.isError) && <ErrorCarga error={capa.error ?? detalle.error} className="mb-4" />}
      {r && (
        <div className="mb-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Dato etiqueta="Valor b" valor={numero(r.valor_b, 2)} nota={`IC90 ${numero(r.intervalo_b.lo, 2)} – ${numero(r.intervalo_b.hi, 2)}`} icono={Activity} />
          <Dato etiqueta="Completitud Mc" valor={numero(r.mc, 1)} nota="Máxima curvatura + 0,2 (conservadora)" />
          <Dato etiqueta="Tasa anual M ≥ Mc" valor={numero(r.tasa_anual_mc, 1)} unidad="sismos/año" nota={`${numero(r.eventos, 0)} eventos (${r.periodo.desde} – ${r.periodo.hasta})`} />
          <Dato etiqueta="CV de intereventos" valor={numero(r.cv_intereventos, 2)} nota="≈ 1: Poisson · > 1: agrupamiento (desagrupados)" />
        </div>
      )}
      <div className="grid gap-5 xl:grid-cols-[1.4fr_1fr]">
        <Tarjeta
          titulo="Sismos por magnitud y profundidad"
          subtitulo={capa.data?.nota ?? undefined}
          pie={capa.data?.expediente_id ? <>Fuente: expediente <Link className="font-mono text-accent-ink hover:underline" to={`/expedientes/${capa.data.expediente_id}`}>{capa.data.expediente_id}</Link></> : undefined}
        >
          {capa.isLoading ? (
            <Esqueleto className="h-[420px]" />
          ) : puntos.length === 0 ? (
            <EstadoVacio titulo="Sin sismos publicados">Publique los resultados con <code>tv publicar</code>.</EstadoVacio>
          ) : (
            <>
              <MapaPuntos
                puntos={puntos}
                color={COLOR_PROFUNDIDAD}
                radio={RADIO_MAGNITUD}
                centro={[-72.2, -16.4]}
                descripcion={`Mapa con ${puntos.length} sismos de magnitud ${magnitudMin} o mayor; el tamaño indica la magnitud y el tono de azul la profundidad.`}
                etiqueta={etiqueta}
              />
              <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-[12px] text-ink-2" aria-label="Leyenda de profundidad">
                <span className="font-semibold">Profundidad:</span>
                {PASOS_PROFUNDIDAD.map((p, i) => (
                  <span key={p} className="inline-flex items-center gap-1.5">
                    <span className="h-3 w-3 rounded-full border border-white" style={{ background: [RAMPA_AZUL[1], RAMPA_AZUL[2], RAMPA_AZUL[3], RAMPA_AZUL[5], RAMPA_AZUL[6]][i] }} />
                    {i < PASOS_PROFUNDIDAD.length - 1 ? `${p}–${PASOS_PROFUNDIDAD[i + 1]} km` : `> ${p} km`}
                  </span>
                ))}
              </div>
              <TablaDatos
                titulo="Sismos del mapa"
                columnas={["Fecha", "Magnitud", "Profundidad (km)", "Latitud", "Longitud"]}
                filas={puntos.map((f) => {
                  const p = f.properties as Record<string, number | string | null>;
                  const [lon, lat] = (f.geometry?.coordinates ?? []) as number[];
                  return [String(p.fecha), numero(Number(p.magnitud), 1), p.profundidad_km != null ? numero(Number(p.profundidad_km), 0) : "—", numero(lat, 3), numero(lon, 3)];
                })}
              />
            </>
          )}
        </Tarjeta>
        <div className="space-y-5">
          <Tarjeta titulo="Sismos M ≥ Mc por año" subtitulo="Conteo anual del catálogo completo (incluye réplicas).">
            {anuales.length === 0 ? (
              <Esqueleto className="h-56" />
            ) : (
              <>
                <div role="img" aria-label={`Barras del número de sismos por año entre ${anuales[0]?.anio} y ${anuales.at(-1)?.anio}`}>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={anuales} margin={{ top: 8, right: 8, bottom: 0, left: -18 }}>
                      <CartesianGrid vertical={false} stroke={colores.rejilla} />
                      <XAxis dataKey="anio" tick={{ fontSize: 11, fill: colores.tinta3 }} tickLine={false} axisLine={{ stroke: colores.eje }} interval="preserveStartEnd" minTickGap={24} />
                      <YAxis tick={{ fontSize: 11, fill: colores.tinta3 }} tickLine={false} axisLine={false} allowDecimals={false} />
                      <Tooltip cursor={{ fill: colores.neutro }} contentStyle={{ background: colores.superficie, borderRadius: 10, border: "none", fontSize: 12 }} formatter={(v) => [String(v), "sismos"]} />
                      <Bar dataKey="n" fill={colores.serie1} radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <TablaDatos titulo="Sismos por año" columnas={["Año", "Sismos M ≥ Mc"]} filas={anuales.map((a) => [a.anio, a.n])} />
              </>
            )}
          </Tarjeta>
          <Tarjeta titulo="¿Hay estructura más allá del azar?">
            <p className="flex items-start gap-2 text-[13px] text-ink-2">
              <ShieldAlert aria-hidden className="mt-0.5 h-4 w-4 shrink-0" style={{ color: "var(--warning)" }} />
              El conteo mensual se compara con un Poisson de tasa constante. Una ganancia de información con IC90 por encima de 0
              indicaría agrupamiento aprovechable; no sería un pronóstico de sismos.
            </p>
            {conteos && (
              <p className="mt-3 text-[13px]">
                <Link className="font-medium text-accent-ink hover:underline" to={`/modelos?id=${conteos.id}`}>
                  Ver la comparación de modelos de conteo →
                </Link>
              </p>
            )}
            <NotaFuente>Desagrupamiento: Gardner y Knopoff (1974). Valor b: Aki (1965) con IC por bootstrap.</NotaFuente>
          </Tarjeta>
        </div>
      </div>
    </>
  );
}
