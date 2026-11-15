import { Table2 } from "lucide-react";
import { useMemo, useState } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type TooltipProps,
} from "recharts";
import type { Esquemas } from "../../api/cliente";
import { useColores } from "../../lib/colores";
import { conUnidad, nombreMes, numero, simboloUnidad } from "../../lib/formato";
import { anioDecimal, banda, evaluarRecta, rectaSen } from "../../lib/tendencia";
import { Boton } from "../ui";
import { t } from "../../lib/i18n";

type Observacion = Esquemas["ObservacionSalida"];
type Pendiente = Esquemas["Pendiente"];

interface Fila {
  t: number;
  fecha: string;
  valor: number | null;
  tendencia?: number;
  banda?: [number, number];
}


export function etiquetaPeriodo(fecha: string, agregacion?: Record<string, unknown>): string {
  const [a, m] = fecha.split("-").map(Number);
  const meses = agregacion?.meses;
  if (Array.isArray(meses) && meses.length > 1 && a && m) {
    const fin = meses[meses.length - 1] as number;
    const anioFin = fin < (m ?? 1) ? a + 1 : a;
    return `${nombreMes(m ?? 1)} ${a} – ${nombreMes(fin)} ${anioFin}`;
  }
  if (agregacion?.tipo === "media_anual") return t(`Año ${a}`, `Year ${a}`);
  return fecha;
}

export function GraficoSerie({
  observaciones,
  unidad,
  agregacion,
  pendiente,
  alto = 300,
  nombre = "Observado",
}: {
  observaciones: Observacion[];
  unidad: string;
  agregacion?: Record<string, unknown>;
  pendiente?: Pendiente | null;
  alto?: number;
  nombre?: string;
}) {
  const c = useColores();
  const [tabla, setTabla] = useState(false);

  const filas = useMemo<Fila[]>(() => {
    const base = observaciones.map((o) => ({ t: anioDecimal(o.t), fecha: o.t, valor: o.valor }));
    if (!pendiente) return base;
    const puntos = base.filter((f) => f.valor !== null).map((f) => ({ t: f.t, y: f.valor as number }));
    if (puntos.length < 3) return base;
    const r = rectaSen(puntos, pendiente.valor);
    return base.map((f) => ({
      ...f,
      tendencia: evaluarRecta(r, f.t),
      banda: banda(r.pivote, pendiente.intervalo.lo, pendiente.intervalo.hi, f.t),
    }));
  }, [observaciones, pendiente]);

  const marcas = useMemo(() => marcasAnio(filas.map((f) => f.t)), [filas]);
  const simbolo = simboloUnidad(unidad);
  const decimales = Math.max(...observaciones.map((o) => Math.abs(o.valor ?? 0))) >= 100 ? 1 : 2;

  const Contenido = ({ active, payload }: TooltipProps<number, string>) => {
    if (!active || !payload?.length) return null;
    const f = payload[0]?.payload as Fila;
    return (
      <div className="min-w-[180px] rounded-xl border border-line bg-surface px-3 py-2.5 text-[12.5px] shadow-flotante">
        <p className="mb-1.5 font-semibold text-ink">{etiquetaPeriodo(f.fecha, agregacion)}</p>
        <Linea color={c.serie1} texto={nombre} valor={f.valor === null ? t("sin dato", "no data") : conUnidad(f.valor, unidad, decimales)} />
        {f.tendencia !== undefined && (
          <Linea color={c.serie2} texto={t("Tendencia de Sen", "Sen trend")} valor={conUnidad(f.tendencia, unidad, decimales)} discontinua />
        )}
      </div>
    );
  };

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <ul className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[12.5px] text-ink-2" aria-label={t("Leyenda", "Legend")}>
          <li className="flex items-center gap-1.5"><span className="h-0.5 w-4 rounded" style={{ background: c.serie1 }} />{nombre}</li>
          {pendiente && (
            <>
              <li className="flex items-center gap-1.5"><span className="h-0 w-4 border-t-2 border-dashed" style={{ borderColor: c.serie2 }} />{t("Tendencia de Sen", "Sen trend")}</li>
              <li className="flex items-center gap-1.5"><span className="h-3 w-4 rounded-sm" style={{ background: c.banda }} />{t(`IC ${Math.round((pendiente.intervalo.nivel ?? 0.9) * 100)} % de la pendiente`, `${Math.round((pendiente.intervalo.nivel ?? 0.9) * 100)} % CI of the slope`)}</li>
            </>
          )}
        </ul>
        <Boton tamano="sm" variante="fantasma" icono={Table2} onClick={() => setTabla((v) => !v)} aria-pressed={tabla}>
          {tabla ? t("Ver gráfico", "Show chart") : t("Ver tabla", "Show table")}
        </Boton>
      </div>

      {tabla ? (
        <div className="max-h-[320px] overflow-auto rounded-xl border border-line">
          <table className="w-full text-[13px]">
            <caption className="sr-only">{t("Valores de la serie", "Series values")}</caption>
            <thead className="sticky top-0 bg-surface-2 text-left text-ink-2">
              <tr><th className="px-3 py-2 font-medium">{t("Periodo", "Period")}</th><th className="px-3 py-2 text-right font-medium">{t("Valor", "Value")} ({simbolo || "—"})</th></tr>
            </thead>
            <tbody>
              {filas.map((f) => (
                <tr key={f.fecha} className="border-t border-line">
                  <td className="px-3 py-1.5 text-ink-2">{etiquetaPeriodo(f.fecha, agregacion)}</td>
                  <td className="cifra px-3 py-1.5 text-right">{numero(f.valor, decimales)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div style={{ height: alto }} role="img" aria-label={t(`Serie temporal ${nombre} en ${simbolo}`, `Time series ${nombre} in ${simbolo}`)}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={filas} margin={{ top: 8, right: 12, bottom: 0, left: 4 }}>
              <CartesianGrid stroke={c.rejilla} vertical={false} />
              <XAxis
                dataKey="t"
                type="number"
                domain={["dataMin", "dataMax"]}
                ticks={marcas}
                tickFormatter={(v: number) => String(Math.round(v))}
                tick={{ fill: c.tinta3, fontSize: 11 }}
                tickLine={false}
                axisLine={{ stroke: c.eje }}
                minTickGap={16}
              />
              <YAxis
                width={52}
                tick={{ fill: c.tinta3, fontSize: 11 }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v: number) => numero(v, decimales === 1 ? 0 : 1)}
                domain={["auto", "auto"]}
                label={{ value: simbolo, angle: -90, position: "insideLeft", fill: c.tinta3, fontSize: 11, dy: 20 }}
              />
              <Tooltip content={<Contenido />} cursor={{ stroke: c.eje, strokeWidth: 1 }} isAnimationActive={false} />
              {pendiente && <Area dataKey="banda" stroke="none" fill={c.banda} isAnimationActive={false} activeDot={false} />}
              <Line
                dataKey="valor"
                stroke={c.serie1}
                strokeWidth={2}
                dot={false}
                connectNulls={false}
                activeDot={{ r: 4.5, stroke: c.superficie, strokeWidth: 2, fill: c.serie1 }}
                isAnimationActive={false}
              />
              {pendiente && (
                <Line dataKey="tendencia" stroke={c.serie2} strokeWidth={2} strokeDasharray="6 4" dot={false} activeDot={false} isAnimationActive={false} />
              )}
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

/** Marcas del eje x en años redondos: cada 10 años en series largas, cada 5 o 1 en cortas. */
export function marcasAnio(tiempos: number[]): number[] {
  if (tiempos.length === 0) return [];
  const min = Math.min(...tiempos);
  const max = Math.max(...tiempos);
  const tramo = max - min;
  const paso = tramo > 30 ? 10 : tramo > 12 ? 5 : tramo > 4 ? 2 : 1;
  const marcas: number[] = [];
  for (let a = Math.ceil(min / paso) * paso; a <= max; a += paso) marcas.push(a);
  return marcas;
}

function Linea({ color, texto, valor, discontinua }: { color: string; texto: string; valor: string; discontinua?: boolean }) {
  return (
    <p className="flex items-center justify-between gap-4 py-0.5">
      <span className="flex items-center gap-1.5 text-ink-2">
        <span className={discontinua ? "h-0 w-3 border-t-2 border-dashed" : "h-0.5 w-3 rounded"} style={discontinua ? { borderColor: color } : { background: color }} />
        {texto}
      </span>
      <span className="cifra font-medium text-ink">{valor}</span>
    </p>
  );
}
