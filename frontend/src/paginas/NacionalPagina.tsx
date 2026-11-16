import type { ExpressionSpecification } from "maplibre-gl";
import { TarjetaAltitud } from "../componentes/portada/Altitud";
import { CloudRain, Droplets, MapPinned, Mountain, Ruler, Thermometer, Waves } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { Esquemas } from "../api/cliente";
import { useExpedienteVigente, useNacional } from "../api/consultas";
import { MapaPuntos } from "../componentes/fenomenos/MapaPuntos";
import { TablaDatos } from "../componentes/fenomenos/TablaDatos";
import { ChipEstado, Dato, Encabezado, ErrorCarga, EstadoVacio, Esqueleto, Insignia, Segmentado, Tarjeta, VEREDICTOS } from "../componentes/ui";
import { RAMPA_AZUL } from "../lib/colores";
import { fechaHora, nombreMes, numero, valorP } from "../lib/formato";
import { areasDepartamentos, escala, valores, type Metrica } from "../lib/coropletas";
import { t } from "../lib/i18n";

type Panorama = Esquemas["ResultadoPanoramaNacional"];
type Departamento = Esquemas["DepartamentoNacional"];

const RAMPA: ExpressionSpecification = ["interpolate", ["linear"], ["get", "valor"], 0, RAMPA_AZUL[0], 0.25, RAMPA_AZUL[2], 0.5, RAMPA_AZUL[3], 0.75, RAMPA_AZUL[5], 1, RAMPA_AZUL[6]];

/** Estado de humedad del SPI con texto e ícono (nunca solo color). */
function EstadoSpi({ d }: { d: Departamento }) {
  if (!d.spi_confiable) return <Insignia>{t("No interpretable (árido)", "Not interpretable (arid)")}</Insignia>;
  const v = d.spi12;
  if (v <= -1) return <Insignia tono="serious" icono={Droplets}>{t("Seco", "Dry")} {numero(v, 2, { signo: true })}</Insignia>;
  if (v >= 1) return <Insignia tono="accent" icono={CloudRain}>{t("Húmedo", "Wet")} {numero(v, 2, { signo: true })}</Insignia>;
  return <Insignia>{t("Normal", "Normal")} {numero(v, 2, { signo: true })}</Insignia>;
}

const UNIDADES: Record<Metrica, string> = { temperatura: "°C/dec", tendencia_lluvia: "mm/dec", lluvia: "mm/año" };

function puntos(deps: Departamento[], metrica: Metrica): Esquemas["Feature"][] {
  const norm = escala(deps, metrica);
  return deps.map((d) => {
    const v = valores(d, metrica);
    return {
      type: "Feature",
      id: d.id,
      geometry: { type: "Point", coordinates: [d.lon, d.lat] },
      properties: { nombre: d.nombre, valor: norm(v.color), original: v.real },
    };
  });
}

function useLimitesDepartamentos() {
  return useQuery({
    queryKey: ["peru-departamentos"],
    staleTime: Infinity,
    queryFn: async () => {
      const r = await fetch("/datos/peru-departamentos.geojson");
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return (await r.json()) as GeoJSON.FeatureCollection;
    },
  });
}

/** Leyenda continua con los extremos en unidades reales. */
function LeyendaRampa({ deps, metrica }: { deps: Departamento[]; metrica: Metrica }) {
  const reales = deps.map((d) => valores(d, metrica).real);
  const min = Math.min(...reales);
  const max = Math.max(...reales);
  return (
    <div className="mt-3 flex items-center gap-3 text-[12px] text-ink-3">
      <span className="cifra">{numero(min, metrica === "lluvia" ? 0 : 2)}</span>
      <span aria-hidden className="h-2.5 flex-1 rounded-full" style={{ background: `linear-gradient(90deg, ${RAMPA_AZUL[0]}, ${RAMPA_AZUL[2]}, ${RAMPA_AZUL[3]}, ${RAMPA_AZUL[5]}, ${RAMPA_AZUL[6]})` }} />
      <span className="cifra">{numero(max, metrica === "lluvia" ? 0 : 2)}</span>
      <span>{metrica === "lluvia" ? t("mm/año (escala log)", "mm/yr (log scale)") : UNIDADES[metrica]}</span>
    </div>
  );
}

type Inventario = Esquemas["ResultadoInventario"];
const RAMPA_DENSIDAD: ExpressionSpecification = ["interpolate", ["linear"], ["get", "valor"], 0, RAMPA_AZUL[1], 0.5, RAMPA_AZUL[4], 1, RAMPA_AZUL[6]];
const TIPOS_EN: Record<string, string> = {
  Flujo: "Flow",
  Caída: "Fall",
  Deslizamiento: "Slide",
  Reptación: "Creep",
  "Movimiento complejo": "Complex movement",
  Vuelco: "Topple",
  "Desplazamiento lateral": "Lateral spread",
};

/** Deslizamientos con dos familias independientes: catálogo de noticias (NASA GLC) e inventario de campo (INGEMMET). */
function ContrasteDeslizamientos() {
  const { detalle } = useExpedienteVigente("inventario");
  const r = detalle.data?.resultado as Inventario | undefined;
  const c = r?.contraste_ingemmet;
  if (!c) return null;
  const maxN = Math.max(1, ...c.densidad_celdas.celdas.map((x) => x.n));
  const celdas: Esquemas["Feature"][] = c.densidad_celdas.celdas.map((x, i) => ({
    type: "Feature",
    id: `ingemmet-${i}`,
    geometry: { type: "Point", coordinates: [x.lon, x.lat] },
    properties: { n: x.n, valor: Math.log10(1 + x.n) / Math.log10(1 + maxN) },
  }));
  const tipos = Object.entries(c.por_tipo_dominio).sort((a, b) => b[1] - a[1]);
  const total = tipos.reduce((a, [, n]) => a + n, 0);
  const pct = (x: number | null | undefined) => (x === null || x === undefined ? "—" : `${numero(x * 100, 0)} %`);
  return (
    <Tarjeta
      titulo={t("Deslizamientos: dos familias de evidencia independientes", "Landslides: two independent evidence families")}
      subtitulo={t(
        `NASA GLC (noticias) frente al inventario de campo de INGEMMET · expediente ${detalle.data?.id ?? ""}`,
        `NASA GLC (news reports) vs INGEMMET field inventory · case file ${detalle.data?.id ?? ""}`,
      )}
      pie={t(
        `${c.metodo_linea_base} La fecha del inventario es la del levantamiento, no la del evento: se valida el lugar, no el momento. Ambas fuentes favorecen zonas accesibles. Fuente: INGEMMET, GEOCATMIN (solo agregados).`,
        `Baseline: 2,000 uniform random points inside Peru in the same box (seed 0); p = P(Binom(n, p_random) ≥ k). Inventory dates are survey dates, not event dates: this validates location, not timing. Both sources favour accessible areas. Source: INGEMMET, GEOCATMIN (aggregates only).`,
      )}
    >
      <div className="grid gap-4 sm:grid-cols-3">
        <Dato
          etiqueta={t("Inventario INGEMMET", "INGEMMET inventory")}
          icono={Mountain}
          valor={numero(c.registros_dominio, 0)}
          nota={t(`movimientos en masa en el sur (de ${numero(c.registros_nacionales, 0)} en el Perú)`, `mass movements in the south (of ${numero(c.registros_nacionales, 0)} in Peru)`)}
        />
        <Dato
          etiqueta={t("GLC a < 5 km de INGEMMET", "GLC within 5 km of INGEMMET")}
          icono={Ruler}
          valor={pct(c.fraccion_menor_5km)}
          nota={t(`${c.eventos_glc_comparados} eventos; lugares al azar: ${pct(c.azar_fraccion_menor_5km)} · p ${valorP(c.p_valor_binomial_5km)}`, `${c.eventos_glc_comparados} events; random places: ${pct(c.azar_fraccion_menor_5km)} · p ${valorP(c.p_valor_binomial_5km)}`)}
        />
        <Dato
          etiqueta={t("Distancia mediana", "Median distance")}
          icono={Ruler}
          valor={`${numero(c.mediana_km ?? NaN, 1)} km`}
          nota={t(`al azar: ${numero(c.azar_mediana_km ?? NaN, 1)} km`, `random places: ${numero(c.azar_mediana_km ?? NaN, 1)} km`)}
        />
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <MapaPuntos
          puntos={celdas}
          color={RAMPA_DENSIDAD}
          radio={["interpolate", ["linear"], ["get", "valor"], 0, 3, 1, 9]}
          centro={[-72.5, -15.5]}
          zoom={5}
          alto={340}
          descripcion={t("Densidad del inventario INGEMMET en celdas de 0,25°", "INGEMMET inventory density in 0.25° cells")}
          etiqueta={(p) => t(`${numero(Number(p.n), 0)} registros en la celda`, `${numero(Number(p.n), 0)} records in cell`)}
        />
        <div>
          <p className="etiqueta mb-2">{t("Tipo de movimiento (sur del Perú)", "Movement type (southern Peru)")}</p>
          <ul className="space-y-2 text-[13px]">
            {tipos.map(([tipo, n]) => (
              <li key={tipo}>
                <div className="flex justify-between gap-2">
                  <span className="text-ink-2">{t(tipo, TIPOS_EN[tipo] ?? tipo)}</span>
                  <span className="cifra text-ink">{numero(n, 0)}</span>
                </div>
                <div className="mt-1 h-1.5 rounded-full bg-surface-2">
                  <div className="h-1.5 rounded-full bg-accent" style={{ width: `${(100 * n) / Math.max(1, total)}%` }} />
                </div>
              </li>
            ))}
          </ul>
          <TablaDatos
            titulo={t("Inventario INGEMMET por departamento (sur)", "INGEMMET inventory by department (south)")}
            columnas={[t("Departamento", "Department"), t("Registros", "Records")]}
            filas={Object.entries(c.por_departamento_dominio).sort((a, b) => b[1] - a[1]).map(([d, n]) => [d, numero(n, 0)])}
          />
        </div>
      </div>
    </Tarjeta>
  );
}

function Sismicidad({ s }: { s: NonNullable<Panorama["sismicidad"]> }) {
  const lista = s.celdas ?? [];
  const tasaMax = Math.max(1e-9, ...lista.map((x) => x.tasa_anual));
  const celdas: Esquemas["Feature"][] = lista.map((c, i) => ({
    type: "Feature",
    id: `celda-${i}`,
    geometry: { type: "Point", coordinates: [c.lon, c.lat] },
    properties: { n: c.n, tasa: c.tasa_anual, m_max: c.m_max, valor: Math.min(1, Math.log10(1 + c.tasa_anual) / Math.log10(1 + tasaMax)) },
  }));
  return (
    <Tarjeta
      titulo={t("Sismicidad nacional (celdas de 1°)", "National seismicity (1° cells)")}
      subtitulo={t(
        `USGS ComCat, ${s.periodo.desde} a ${s.periodo.hasta}: ${numero(s.eventos, 0)} sismos M ≥ 4,5. Mc = ${numero(s.mc, 1)}; b = ${numero(s.valor_b, 3)} (IC90 ${numero(s.intervalo_b.lo, 3)} a ${numero(s.intervalo_b.hi, 3)}).`,
        `USGS ComCat, ${s.periodo.desde} to ${s.periodo.hasta}: ${numero(s.eventos, 0)} earthquakes M ≥ 4.5. Mc = ${numero(s.mc, 1)}; b = ${numero(s.valor_b, 3)} (90 % CI ${numero(s.intervalo_b.lo, 3)} to ${numero(s.intervalo_b.hi, 3)}).`,
      )}
      pie={t("Tasas históricas del catálogo global: no son pronósticos. El catálogo oficial del Perú lo mantiene el IGP.", "Historical rates from the global catalog: not forecasts. Peru's official catalog is maintained by IGP.")}
    >
      <div className="grid gap-5 lg:grid-cols-[1fr_300px]">
        <MapaPuntos
          puntos={celdas}
          color={RAMPA}
          radio={["interpolate", ["linear"], ["get", "valor"], 0, 3, 1, 14]}
          centro={[-75.5, -9.5]}
          zoom={4.2}
          alto={460}
          descripcion={t("Tasa anual de sismos M ≥ Mc por celda de 1°", "Annual rate of M ≥ Mc earthquakes per 1° cell")}
          etiqueta={(p) => t(`${numero(Number(p.tasa), 2)} sismos/año · M máx ${numero(Number(p.m_max), 1)}`, `${numero(Number(p.tasa), 2)} quakes/yr · max M ${numero(Number(p.m_max), 1)}`)}
        />
        <div className="space-y-4 text-[13px]">
          <div>
            <p className="etiqueta mb-2">{t("Valor b por franja de latitud", "b-value by latitude band")}</p>
            <ul className="space-y-1.5">
              {Object.entries(s.valor_b_por_franja ?? {}).map(([franja, b]) => (
                <li key={franja} className="flex justify-between gap-3">
                  <span className="text-ink-2">{franja}</span>
                  <span className="cifra font-semibold text-ink">{b === null || b === undefined ? "—" : numero(b, 3)}</span>
                </li>
              ))}
            </ul>
            <p className="mt-2 text-[12px] text-ink-3">{t("b ≈ 1 es lo esperado en zonas de subducción; diferencias entre franjas se leen con su incertidumbre.", "b ≈ 1 is expected in subduction zones; differences between bands must be read with their uncertainty.")}</p>
          </div>
          <div>
            <p className="etiqueta mb-2">{t("Mayores sismos del catálogo", "Largest earthquakes in the catalog")}</p>
            <ul className="space-y-1.5">
              {(s.grandes_sismos ?? []).slice(0, 6).map((g) => (
                <li key={`${g.fecha}-${g.magnitud}`} className="flex justify-between gap-3">
                  <span className="text-ink-2">{g.fecha}</span>
                  <span className="cifra font-semibold text-ink">M {numero(g.magnitud, 1)}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
      <TablaDatos
        titulo={t("Celdas sísmicas", "Seismic cells")}
        columnas={[t("Latitud", "Latitude"), t("Longitud", "Longitude"), t("Sismos", "Earthquakes"), t("Tasa anual", "Annual rate"), t("M máx", "Max M")]}
        filas={lista.map((c) => [numero(c.lat, 1), numero(c.lon, 1), numero(c.n, 0), numero(c.tasa_anual, 2), numero(c.m_max, 1)])}
      />
    </Tarjeta>
  );
}

export function NacionalPagina() {
  const consulta = useNacional();
  const limites = useLimitesDepartamentos();
  const [metrica, setMetrica] = useState<Metrica>("temperatura");
  const r = consulta.data?.resultado as Panorama | null | undefined;
  const deps = useMemo(() => r?.departamentos ?? [], [r]);
  const areas = useMemo(() => areasDepartamentos(limites.data, deps, metrica), [limites.data, deps, metrica]);
  const unicos = deps.filter((d) => !d.comparte_celda_con);
  const compartidas = deps.filter((d) => d.comparte_celda_con).map((d) => `${d.nombre} – ${deps.find((x) => x.id === d.comparte_celda_con)?.nombre ?? d.comparte_celda_con}`);
  const anios = deps.flatMap((d) => d.serie_anios ?? []);
  const periodo = anios.length ? `${Math.min(...anios)}–${Math.max(...anios)}` : "";
  const umbralSpi = r?.umbral_spi_mm;
  const conteo = (clave: "tendencia_temperatura" | "tendencia_lluvia") =>
    unicos.reduce<Record<string, number>>((acc, d) => ({ ...acc, [d[clave].veredicto]: (acc[d[clave].veredicto] ?? 0) + 1 }), {});

  return (
    <div className="space-y-6">
      <Encabezado
        eyebrow={deps.length ? t(`Escala nacional · ${deps.length} departamentos`, `National scale · ${deps.length} departments`) : t("Escala nacional", "National scale")}
        titulo={t("El Perú con el mismo motor que Arequipa", "Peru with the same engine as Arequipa")}
        descripcion={t(
          "Cada departamento se analiza con las mismas reglas que la cuenca del Chili: Sello de Confianza para las tendencias, SPI con parámetros del entrenamiento y estadística sísmica. Agregar una región es configuración, no código nuevo.",
          "Every department is analysed with the same rules as the Chili basin: Confidence Seal for trends, SPI with training-period parameters, and seismic statistics. Adding a region is configuration, not new code.",
        )}
      />
      {consulta.isLoading ? (
        <Esqueleto className="h-96" />
      ) : consulta.error ? (
        <ErrorCarga error={consulta.error} />
      ) : !r ? (
        <EstadoVacio icono={MapPinned} titulo={t("Aún no hay un panorama nacional publicado", "No national panorama published yet")}>
          {t("Ejecute `tv experimentos --solo nacional` y `tv publicar`.", "Run `tv experimentos --solo nacional` and `tv publicar`.")}
        </EstadoVacio>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Dato etiqueta={t("Celdas climáticas", "Climate cells")} icono={MapPinned} valor={numero(unicos.length, 0)} nota={compartidas.length ? t(`${deps.length} departamentos; comparten celda: ${compartidas.join("; ")}`, `${deps.length} departments; sharing a cell: ${compartidas.join("; ")}`) : t(`${deps.length} departamentos`, `${deps.length} departments`)} />
            <Dato etiqueta={t("Calentamiento", "Warming")} icono={Thermometer} valor={`${unicos.filter((d) => d.tendencia_temperatura.sen_por_decada > 0).length}/${unicos.length}`} nota={t(`celdas con pendiente de Sen positiva${periodo ? ` (${periodo})` : ""}; ver el Sello de cada una`, `cells with positive Sen slope${periodo ? ` (${periodo})` : ""}; see each Seal`)} />
            <Dato etiqueta={t("Tendencia de temperatura confirmada", "Confirmed temperature trend")} icono={Thermometer} valor={numero(conteo("tendencia_temperatura").preliminar ?? 0, 0)} nota={t("preliminares: significativas con pruebas pendientes (una sola familia de datos)", "preliminary: significant with pending tests (single data family)")} />
            <Dato etiqueta={t("SPI no interpretable", "SPI not interpretable")} icono={Waves} valor={numero(unicos.filter((d) => !d.spi_confiable).length, 0)} nota={typeof umbralSpi === "number" ? t(`celdas áridas (< ${numero(umbralSpi, 0)} mm/año): el SPI no se interpreta`, `arid cells (< ${numero(umbralSpi, 0)} mm/yr): SPI is not interpreted`) : t("celdas áridas: el SPI no se interpreta", "arid cells: SPI is not interpreted")} />
          </div>

          <Tarjeta
            titulo={t("Mapa por departamento", "Map by department")}
            subtitulo={t(`Celda NASA POWER de cada capital · expediente ${consulta.data?.expediente_id}`, `NASA POWER cell of each capital · case file ${consulta.data?.expediente_id}`)}
            acciones={
              <Segmentado<Metrica>
                etiqueta={t("Variable del mapa", "Map variable")}
                valor={metrica}
                alCambiar={setMetrica}
                opciones={[
                  { valor: "temperatura", texto: t("Tendencia T", "T trend") },
                  { valor: "tendencia_lluvia", texto: t("Tendencia lluvia", "Rain trend") },
                  { valor: "lluvia", texto: t("Lluvia media", "Mean rain") },
                ]}
              />
            }
            pie={t(
              `Generado ${fechaHora(consulta.data?.generado_utc)} · cada departamento se colorea con el valor de la celda NASA POWER (0,5°) de su capital, marcada con un punto; no es un promedio del territorio. Límites: Natural Earth (dominio público).`,
              `Generated ${fechaHora(consulta.data?.generado_utc)} · each department is filled with the value of its capital's NASA POWER cell (0.5°), marked with a dot; it is not an area average. Boundaries: Natural Earth (public domain).`,
            )}
          >
            <MapaPuntos
              puntos={puntos(deps, metrica)}
              areas={areas}
              atribucionAreas={t("Límites: Natural Earth", "Boundaries: Natural Earth")}
              color={RAMPA}
              radio={5}
              centro={[-75.5, -9.5]}
              zoom={4.2}
              alto={460}
              descripcion={t("Departamentos del Perú", "Departments of Peru")}
              etiqueta={(p) => `${String(p.nombre)}: ${numero(Number(p.original), metrica === "lluvia" ? 0 : 2)} ${metrica === "lluvia" ? t("mm/año", "mm/yr") : UNIDADES[metrica]}`}
            />
            <LeyendaRampa deps={deps} metrica={metrica} />
          </Tarjeta>

          <Tarjeta
            titulo={t("Sello de Confianza por departamento", "Confidence Seal by department")}
            subtitulo={t(
              "Con una sola familia de datos (POWER) ningún veredicto puede ser 'robusta': la prueba de independencia queda pendiente. El sistema lo declara en vez de sobrevender.",
              "With a single data family (POWER) no verdict can be 'robust': the independence test remains pending. The system says so instead of overselling.",
            )}
          >
            <div className="overflow-x-auto">
              <table className="w-full min-w-[860px] text-left text-[13px]">
                <thead className="text-ink-2">
                  <tr className="border-b border-line">
                    <th className="px-2 py-2 font-medium">{t("Departamento", "Department")}</th>
                    <th className="px-2 py-2 font-medium">{t("T media", "Mean T")}</th>
                    <th className="px-2 py-2 font-medium">{t("Tendencia T (°C/década)", "T trend (°C/decade)")}</th>
                    <th className="px-2 py-2 font-medium">{t("Lluvia anual", "Annual rain")}</th>
                    <th className="px-2 py-2 font-medium">{t("Tendencia lluvia (mm/década)", "Rain trend (mm/decade)")}</th>
                    <th className="px-2 py-2 font-medium">SPI-12 ({deps[0] ? `${nombreMes(Number(deps[0].spi_mes.slice(5, 7)))} ${deps[0].spi_mes.slice(0, 4)}` : "—"})</th>
                    <th className="px-2 py-2 font-medium">{t("Deslizamientos GLC", "GLC landslides")}</th>
                  </tr>
                </thead>
                <tbody>
                  {deps.map((d) => (
                    <tr key={d.id} className="border-b border-line align-top">
                      <td className="px-2 py-2">
                        <p className="font-medium text-ink">{d.nombre}</p>
                        <p className="text-[11.5px] text-ink-3">
                          {d.capital}
                          {d.comparte_celda_con ? ` · ${t("misma celda que", "same cell as")} ${d.comparte_celda_con}` : ""}
                        </p>
                      </td>
                      <td className="cifra px-2 py-2">{numero(d.temperatura_media_c, 1)} °C</td>
                      <td className="px-2 py-2">
                        <p className="cifra font-medium text-ink">
                          {numero(d.tendencia_temperatura.sen_por_decada, 2, { signo: true })}{" "}
                          <span className="text-[11.5px] font-normal text-ink-3">[{numero(d.tendencia_temperatura.intervalo.lo, 2)}, {numero(d.tendencia_temperatura.intervalo.hi, 2)}] · p {valorP(d.tendencia_temperatura.p_conservador)}</span>
                        </p>
                        <ChipEstado mapa={VEREDICTOS} valor={d.tendencia_temperatura.veredicto} />
                      </td>
                      <td className="cifra px-2 py-2">{numero(d.lluvia_anual_media_mm, 0)} mm</td>
                      <td className="px-2 py-2">
                        <p className="cifra font-medium text-ink">
                          {numero(d.tendencia_lluvia.sen_por_decada, 1, { signo: true })}{" "}
                          <span className="text-[11.5px] font-normal text-ink-3">p {valorP(d.tendencia_lluvia.p_conservador)}</span>
                        </p>
                        <ChipEstado mapa={VEREDICTOS} valor={d.tendencia_lluvia.veredicto} />
                      </td>
                      <td className="px-2 py-2"><EstadoSpi d={d} /></td>
                      <td className="cifra px-2 py-2">{numero(d.deslizamientos_glc, 0)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-[12px] text-ink-3">
              {t(
                "Tendencias: Theil-Sen con IC90 y p conservador (máximo de tres variantes de Mann-Kendall). SPI: parámetros gamma de 1981–2015. Deslizamientos: NASA Global Landslide Catalog (basado en noticias, subregistra zonas rurales).",
                "Trends: Theil-Sen with 90 % CI and conservative p (maximum of three Mann-Kendall variants). SPI: gamma parameters from 1981–2015. Landslides: NASA Global Landslide Catalog (news-based, under-reports rural areas).",
              )}{" "}
              <Link to="/expedientes" className="text-accent-ink hover:underline">{t("Ver expedientes", "See case files")}</Link>
            </p>
          </Tarjeta>

          {r.sismicidad && <Sismicidad s={r.sismicidad} />}
          <ContrasteDeslizamientos />
        </>
      )}
      <TarjetaAltitud />
    </div>
  );
}
