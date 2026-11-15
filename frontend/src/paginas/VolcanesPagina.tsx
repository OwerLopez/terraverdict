import { Mountain, ShieldAlert } from "lucide-react";
import { useCallback, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { Esquemas } from "../api/cliente";
import { useCapaVolcanes, useExpedienteVigente } from "../api/consultas";
import { MapaPuntos } from "../componentes/fenomenos/MapaPuntos";
import { TablaDatos } from "../componentes/fenomenos/TablaDatos";
import { Encabezado, ErrorCarga, EstadoVacio, Esqueleto, Tarjeta } from "../componentes/ui";
import { RAMPA_AZUL } from "../lib/colores";
import { numero } from "../lib/formato";

type Volcan = Esquemas["VolcanRecurrencia"];

const ANCHO = 640;
const IZQ = 128;
const DER = 30;
const FILA = 30;

function escala(dominio: [number, number], rango: [number, number]) {
  return (v: number) => rango[0] + ((v - dominio[0]) / (dominio[1] - dominio[0])) * (rango[1] - rango[0]);
}

/** Probabilidad anual (%) con su IC90: punto + bigote, un renglón por volcán. */
function GraficoProbabilidad({ volcanes }: { volcanes: Volcan[] }) {
  const [activo, setActivo] = useState<number | null>(null);
  const maximo = Math.max(...volcanes.map((v) => v.intervalo.hi * 100), 1);
  const x = escala([0, maximo * 1.05], [IZQ, ANCHO - DER]);
  const alto = volcanes.length * FILA + 34;
  const marcas = [0, maximo / 4, maximo / 2, (3 * maximo) / 4, maximo].map((m) => Math.round(m * 10) / 10);
  return (
    <svg viewBox={`0 0 ${ANCHO} ${alto}`} className="w-full" role="img" aria-label="Probabilidad anual de inicio de erupción por volcán, con su intervalo de confianza del 90 %">
      {marcas.map((m) => (
        <g key={m}>
          <line x1={x(m)} x2={x(m)} y1={4} y2={alto - 26} stroke="var(--grid)" />
          <text x={x(m)} y={alto - 10} textAnchor="middle" fontSize={11} fill="var(--ink-3)">
            {numero(m, 1)} %
          </text>
        </g>
      ))}
      {volcanes.map((v, i) => {
        const y = 4 + i * FILA + FILA / 2;
        const enfoque = activo === i;
        return (
          <g
            key={v.numero_gvp}
            tabIndex={0}
            onMouseEnter={() => setActivo(i)}
            onMouseLeave={() => setActivo(null)}
            onFocus={() => setActivo(i)}
            onBlur={() => setActivo(null)}
            aria-label={`${v.nombre}: ${numero(v.probabilidad_anual * 100, 2)} % al año, IC90 ${numero(v.intervalo.lo * 100, 2)} a ${numero(v.intervalo.hi * 100, 2)} %`}
            className="outline-none"
          >
            <rect x={0} y={y - FILA / 2} width={ANCHO} height={FILA} fill={enfoque ? "var(--accent-soft)" : "transparent"} rx={6} />
            <text x={IZQ - 10} y={y + 4} textAnchor="end" fontSize={12} fill="var(--ink)">
              {v.nombre}
            </text>
            <line x1={x(v.intervalo.lo * 100)} x2={x(v.intervalo.hi * 100)} y1={y} y2={y} stroke="var(--serie-1)" strokeWidth={2} strokeLinecap="round" />
            <circle cx={x(v.probabilidad_anual * 100)} cy={y} r={5} fill="var(--serie-1)" stroke="var(--surface-solida)" strokeWidth={2} />
            {enfoque && (
              <text x={x(v.intervalo.hi * 100) + 8} y={y + 4} fontSize={11.5} fill="var(--ink-2)" className="cifra">
                {numero(v.probabilidad_anual * 100, 2)} % ({numero(v.intervalo.lo * 100, 2)}–{numero(v.intervalo.hi * 100, 2)})
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}

/** Historia eruptiva: una marca por inicio de erupción confirmado desde el inicio del registro. */
function LineaTiempo({ volcanes, desde }: { volcanes: Volcan[]; desde: number }) {
  const hasta = new Date().getFullYear();
  const x = escala([desde, hasta], [IZQ, ANCHO - DER]);
  const alto = volcanes.length * FILA + 34;
  const decenas = [];
  for (let a = Math.ceil(desde / 100) * 100; a <= hasta; a += 100) decenas.push(a);
  return (
    <svg viewBox={`0 0 ${ANCHO} ${alto}`} className="w-full" role="img" aria-label={`Años de inicio de cada erupción confirmada desde ${desde}, por volcán`}>
      {decenas.map((a) => (
        <g key={a}>
          <line x1={x(a)} x2={x(a)} y1={4} y2={alto - 26} stroke="var(--grid)" />
          <text x={x(a)} y={alto - 10} textAnchor="middle" fontSize={11} fill="var(--ink-3)">
            {a}
          </text>
        </g>
      ))}
      {volcanes.map((v, i) => {
        const y = 4 + i * FILA + FILA / 2;
        return (
          <g key={v.numero_gvp}>
            <text x={IZQ - 10} y={y + 4} textAnchor="end" fontSize={12} fill="var(--ink)">
              {v.nombre}
            </text>
            <line x1={IZQ} x2={ANCHO - DER} y1={y} y2={y} stroke="var(--border-strong)" />
            {(v.inicios ?? []).map((a, j) => (
              <rect key={`${a}-${j}`} x={x(a) - 2} y={y - 8} width={4} height={16} rx={2} fill="var(--serie-1)">
                <title>{`${v.nombre}: erupción iniciada en ${a}`}</title>
              </rect>
            ))}
          </g>
        );
      })}
    </svg>
  );
}

export function VolcanesPagina() {
  const { detalle } = useExpedienteVigente("recurrencia");
  const capa = useCapaVolcanes();
  const r = detalle.data?.resultado.tipo === "recurrencia" ? (detalle.data.resultado as Esquemas["ResultadoRecurrencia"]) : undefined;
  const activos = useMemo(
    () => (r?.volcanes ?? []).filter((v) => v.erupciones > 0).sort((a, b) => b.probabilidad_anual - a.probabilidad_anual),
    [r],
  );
  const etiqueta = useCallback(
    (p: Record<string, unknown>) => `${String(p.nombre)} · ${numero(Number(p.probabilidad_anual) * 100, 2)} %/año · ${numero(Number(p.distancia_km), 0)} km de Arequipa`,
    [],
  );

  return (
    <>
      <Encabezado
        eyebrow="Fenómenos naturales"
        titulo="Actividad volcánica"
        descripcion="Frecuencia histórica de erupciones (Smithsonian GVP) con su intervalo exacto. Son frecuencias, no pronósticos: el estado actual de cada volcán lo informa el OVS-IGP."
      />
      {detalle.isError && <ErrorCarga error={detalle.error} className="mb-4" />}
      {detalle.isLoading && <Esqueleto className="h-80" />}
      {!detalle.isLoading && !r && <EstadoVacio icono={Mountain} titulo="Sin expediente de recurrencia">Publique los resultados con <code>tv publicar</code>.</EstadoVacio>}
      {r && (
        <div className="grid gap-5 xl:grid-cols-2">
          <Tarjeta
            titulo="Probabilidad anual de inicio de erupción"
            subtitulo={`${r.metodo}. Desde ${r.inicio_registro}.`}
            pie={<>Fuente: expediente <Link className="font-mono text-accent-ink hover:underline" to={`/expedientes/${detalle.data?.id}`}>{detalle.data?.id}</Link></>}
          >
            <div className="overflow-x-auto">
              <div className="min-w-[520px] sm:min-w-0">
  <GraficoProbabilidad volcanes={activos} />
              </div>
            </div>
            <TablaDatos
              titulo="Probabilidad anual por volcán"
              columnas={["Volcán", "Erupciones", "P anual (%)", "IC90 (%)", "Intervalo medio (años)", "Distancia (km)"]}
              filas={activos.map((v) => [
                v.nombre,
                v.erupciones,
                numero(v.probabilidad_anual * 100, 2),
                `${numero(v.intervalo.lo * 100, 2)} – ${numero(v.intervalo.hi * 100, 2)}`,
                numero(v.intervalo_medio_anios, 1),
                numero(v.distancia_km, 1),
              ])}
            />
          </Tarjeta>
          <Tarjeta titulo="Historia eruptiva" subtitulo="Cada marca es el inicio de una erupción confirmada.">
            <div className="overflow-x-auto">
              <div className="min-w-[520px] sm:min-w-0">
  <LineaTiempo volcanes={activos} desde={r.inicio_registro} />
              </div>
            </div>
            <TablaDatos
              titulo="Años de inicio de erupción"
              columnas={["Volcán", "Años"]}
              filas={activos.map((v) => [v.nombre, (v.inicios ?? []).join(", ") || "—"])}
            />
          </Tarjeta>
          <Tarjeta titulo="Ubicación" className="xl:col-span-2">
            <MapaPuntos
              puntos={capa.data?.features ?? []}
              color={["interpolate", ["linear"], ["get", "probabilidad_anual"], 0, RAMPA_AZUL[1], 0.02, RAMPA_AZUL[4], 0.05, RAMPA_AZUL[6]]}
              radio={7}
              centro={[-71.5, -16.2]}
              zoom={6}
              alto={360}
              descripcion="Mapa de los volcanes del sur del Perú; el tono de azul indica la probabilidad anual histórica."
              etiqueta={etiqueta}
            />
            <p className="mt-3 flex items-start gap-2 text-[12.5px] text-ink-2">
              <ShieldAlert aria-hidden className="mt-0.5 h-4 w-4 shrink-0" style={{ color: "var(--warning)" }} />
              {(r.abstencion.motivos ?? []).join(" ")} {(r.abstencion.advertencias ?? []).join(" ")}
            </p>
          </Tarjeta>
        </div>
      )}
    </>
  );
}
