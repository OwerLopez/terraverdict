/**
 * Predicción frente a realidad en el periodo de prueba (fuera de muestra): observado (negro), pronóstico del
 * modelo elegido en validación (azul), climatología (gris discontinuo) e intervalo conformal del 90 % (banda).
 * Los datos son la `serie_prueba` de resultados/sequia.json, exportada por `tv publicar` en indicadores.json.
 */
import { useMemo } from "react";
import { Area, CartesianGrid, ComposedChart, Legend, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useColores } from "../../lib/colores";
import { numero } from "../../lib/formato";
import type { SeriePrueba } from "../../lib/indicadores";
import { t } from "../../lib/i18n";

/**
 * Banda del 90 % de un mes. El pipeline guarda el intervalo conformal como semianchura q (una sola cifra,
 * calibrada en validación): banda = pronóstico ± q. Si trae un par [lo, hi] por mes, se usa tal cual.
 */
export function banda(serie: SeriePrueba, i: number): [number, number] | null {
  const iv = serie.intervalo_90 as unknown as (number | [number, number] | null)[];
  const p = serie.pronostico[i];
  if (Array.isArray(iv[i])) return iv[i] as [number, number];
  const q = iv.length === 1 && typeof iv[0] === "number" ? iv[0] : typeof iv[i] === "number" ? (iv[i] as number) : null;
  return q != null && p != null ? [p - q, p + q] : null;
}

export function PrediccionRealidad({ serie, particion }: { serie: SeriePrueba; particion: Record<string, [string, string]> | null }) {
  const c = useColores();
  const datos = useMemo(
    () =>
      serie.fechas.map((f, i) => ({
        fecha: f.slice(0, 7),
        observado: serie.observado[i] ?? null,
        pronostico: serie.pronostico[i] ?? null,
        referencia: serie.referencia[i] ?? null,
        banda: banda(serie, i),
      })),
    [serie],
  );
  const dentro = datos.filter((d) => d.banda && d.observado != null && d.observado >= d.banda[0] && d.observado <= d.banda[1]).length;
  const conBanda = datos.filter((d) => d.banda && d.observado != null).length;
  const tramos = particion
    ? (["entrenamiento", "validacion", "prueba"] as const).map((k) => ({ k, desde: particion[k]?.[0]?.slice(0, 4), hasta: particion[k]?.[1]?.slice(0, 4) }))
    : [];
  const nombreTramo = { entrenamiento: t("Entrenamiento", "Training"), validacion: t("Validación", "Validation"), prueba: t("Prueba (mostrada)", "Test (shown)") };

  return (
    <div>
      {tramos.length > 0 && (
        <div className="mb-3 flex overflow-hidden rounded-lg border border-line text-[11.5px]" aria-label={t("Periodos del protocolo", "Protocol periods")}>
          {tramos.map((p) => (
            <div key={p.k} className={p.k === "prueba" ? "flex-[1.2] bg-accent-soft px-2 py-1 font-semibold text-accent-ink" : p.k === "validacion" ? "flex-1 bg-surface-2 px-2 py-1 text-ink-2" : "flex-[3] px-2 py-1 text-ink-3"}>
              {nombreTramo[p.k]} {p.desde}–{p.hasta}
            </div>
          ))}
          <div className="flex-[0.8] border-l border-dashed border-line px-2 py-1 text-ink-3">{t("Pronóstico operativo: no publicado", "Operational forecast: not published")}</div>
        </div>
      )}
      <div className="h-[320px]" role="img" aria-label={t(`Predicción frente a realidad de ${serie.objetivo}: ${datos.length} meses de prueba`, `Prediction vs reality for ${serie.objetivo}: ${datos.length} test months`)}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={datos} margin={{ top: 8, right: 12, bottom: 4, left: -8 }}>
            <CartesianGrid stroke={c.rejilla} vertical={false} />
            <XAxis dataKey="fecha" tick={{ fill: c.tinta3, fontSize: 11 }} stroke={c.eje} minTickGap={28} />
            <YAxis tick={{ fill: c.tinta3, fontSize: 11 }} stroke={c.eje} label={{ value: "SPI-3", angle: -90, position: "insideLeft", fill: c.tinta3, fontSize: 11, dx: 14 }} />
            <ReferenceLine y={-1} stroke="var(--serious)" strokeDasharray="4 3" label={{ value: t("sequía (SPI ≤ −1)", "drought (SPI ≤ −1)"), fill: c.tinta3, fontSize: 10, position: "insideBottomLeft" }} />
            <Tooltip
              contentStyle={{ background: c.superficie, border: `1px solid ${c.rejilla}`, borderRadius: 10, fontSize: 12 }}
              formatter={(v: unknown, nombre: string) => (Array.isArray(v) ? [`${numero(v[0] as number, 2)} – ${numero(v[1] as number, 2)}`, nombre] : [numero(v as number, 2), nombre])}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Area dataKey="banda" name={t("Intervalo conformal 90 %", "90 % conformal interval")} stroke="none" fill={c.banda} isAnimationActive={false} />
            <Line dataKey="referencia" name={t("Climatología", "Climatology")} stroke={c.tinta3} strokeDasharray="4 4" dot={false} strokeWidth={1.2} isAnimationActive={false} />
            <Line dataKey="pronostico" name={t(`Pronóstico (${serie.modelo})`, `Forecast (${serie.modelo})`)} stroke={c.serie1} dot={false} strokeWidth={2} isAnimationActive={false} />
            <Line dataKey="observado" name={t("Observado", "Observed")} stroke={c.tinta} dot={false} strokeWidth={2} isAnimationActive={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-2 text-[12px] text-ink-3">
        {t(
          `${dentro} de ${conBanda} meses observados quedaron dentro del intervalo del 90 % (${numero((dentro / Math.max(1, conBanda)) * 100, 0)} %). Modelo elegido en validación (${serie.familia ?? "—"}); la prueba se evaluó una sola vez.`,
          `${dentro} of ${conBanda} observed months fell inside the 90 % interval (${numero((dentro / Math.max(1, conBanda)) * 100, 0)} %). Model chosen on validation (${serie.familia ?? "—"}); the test set was evaluated once.`,
        )}
      </p>
    </div>
  );
}
