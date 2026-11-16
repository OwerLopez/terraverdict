/**
 * Por qué la cabecera es más fría que la ciudad: temperatura media 1991–2020 de la estación NOAA GHCN de
 * Arequipa y de la celda NASA POWER de la cabecera, con su elevación. El gradiente de 6,5 °C/km es la
 * referencia de la atmósfera estándar y se muestra como referencia física, no como corrección de los datos.
 */
import { Mountain } from "lucide-react";
import { usePortada } from "../../api/consultas";
import { numero } from "../../lib/formato";
import { comoIndicadores } from "../../lib/indicadores";
import { t } from "../../lib/i18n";
import { Tarjeta } from "../ui";

export function TarjetaAltitud() {
  const a = comoIndicadores(usePortada().data?.indicadores)?.altitud;
  if (!a) return null;
  const filas = [
    { nombre: t(`Ciudad · estación NOAA GHCN ${a.estacion_ciudad.estacion} (aeropuerto)`, `City · NOAA GHCN station ${a.estacion_ciudad.estacion} (airport)`), z: a.estacion_ciudad.elevacion_m, temp: a.estacion_ciudad.temperatura_media_c },
    { nombre: t("Celda NASA POWER de la «ciudad» (promedio de 0,5°)", "NASA POWER «city» cell (0.5° average)"), z: a.celda_ciudad_power.elevacion_celda_m, temp: a.celda_ciudad_power.temperatura_media_c },
    { nombre: t("Celda NASA POWER de la cabecera", "NASA POWER headwater cell"), z: a.celda_cabecera.elevacion_celda_m, temp: a.celda_cabecera.temperatura_media_c },
  ];
  return (
    <Tarjeta
      titulo={<span className="flex items-center gap-2"><Mountain className="h-4 w-4 text-accent" aria-hidden /> {t("¿Por qué la cabecera marca unos 6 °C y la ciudad unos 15 °C?", "Why does the headwater read about 6 °C and the city about 15 °C?")}</span>}
      subtitulo={t(`Temperatura media ${a.periodo[0].slice(0, 4)}–${a.periodo[1].slice(0, 4)} y elevación de cada punto`, `Mean temperature ${a.periodo[0].slice(0, 4)}–${a.periodo[1].slice(0, 4)} and elevation of each point`)}
      pie={t(
        "6,5 °C/km es la referencia de la atmósfera estándar (OACI): una referencia física para entender la diferencia, no una corrección aplicada a las observaciones. El gradiente real cambia con la humedad, la estación y la pendiente.",
        "6.5 °C/km is the standard-atmosphere reference (ICAO): a physical reference to understand the difference, not a correction applied to the observations. The real lapse rate varies with humidity, season and slope.",
      )}
    >
      <div className="grid gap-4 md:grid-cols-[1.4fr_1fr]">
        <ul className="space-y-2">
          {filas.map((f) => (
            <li key={f.nombre} className="flex items-center justify-between gap-3 rounded-xl bg-surface-2 px-3 py-2 text-[13px]">
              <span className="text-ink-2">{f.nombre}</span>
              <span className="cifra shrink-0 font-semibold text-ink">{numero(f.z, 0)} m · {numero(f.temp, 1)} °C</span>
            </li>
          ))}
        </ul>
        <div className="rounded-xl border border-line p-3 text-[13px] leading-relaxed text-ink-2">
          <p>
            {t(
              `Entre la estación de la ciudad y la cabecera hay ${numero(a.desnivel_m, 0)} m de desnivel y ${numero(a.diferencia_c, 1)} °C de diferencia: ${numero(a.gradiente_observado_c_km, 1)} °C por kilómetro.`,
              `Between the city station and the headwater there are ${numero(a.desnivel_m, 0)} m of elevation and ${numero(a.diferencia_c, 1)} °C of difference: ${numero(a.gradiente_observado_c_km, 1)} °C per kilometre.`,
            )}
          </p>
          <p className="mt-2">
            {t(
              `Con la referencia de ${numero(a.gradiente_referencia_c_km, 1)} °C/km se esperarían ${numero(a.esperado_con_referencia_c, 1)} °C: el orden de magnitud coincide. La celda POWER de la «ciudad» promedia terreno a unos ${numero(Math.round(a.celda_ciudad_power.elevacion_celda_m / 100) * 100, 0)} m, por eso es más fría que la estación.`,
              `With the ${numero(a.gradiente_referencia_c_km, 1)} °C/km reference one would expect ${numero(a.esperado_con_referencia_c, 1)} °C: the order of magnitude matches. The POWER «city» cell averages terrain at about ${numero(Math.round(a.celda_ciudad_power.elevacion_celda_m / 100) * 100, 0)} m, which is why it is colder than the station.`,
            )}
          </p>
        </div>
      </div>
    </Tarjeta>
  );
}
