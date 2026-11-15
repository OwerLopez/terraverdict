import type { ExpressionSpecification } from "maplibre-gl";
import { CloudRain, Droplets, MapPinned, Thermometer, Waves } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { Esquemas } from "../api/cliente";
import { useNacional } from "../api/consultas";
import { MapaPuntos } from "../componentes/fenomenos/MapaPuntos";
import { TablaDatos } from "../componentes/fenomenos/TablaDatos";
import { ChipEstado, Dato, Encabezado, ErrorCarga, EstadoVacio, Esqueleto, Insignia, Segmentado, Tarjeta, VEREDICTOS } from "../componentes/ui";
import { RAMPA_AZUL } from "../lib/colores";
import { fechaHora, nombreMes, numero, valorP } from "../lib/formato";
import { t } from "../lib/i18n";

type Panorama = Esquemas["ResultadoPanoramaNacional"];
type Departamento = Esquemas["DepartamentoNacional"];
type Metrica = "temperatura" | "lluvia" | "tendencia_lluvia";

const RAMPA: ExpressionSpecification = ["interpolate", ["linear"], ["get", "valor"], 0, RAMPA_AZUL[0], 0.25, RAMPA_AZUL[2], 0.5, RAMPA_AZUL[3], 0.75, RAMPA_AZUL[5], 1, RAMPA_AZUL[6]];

/** Estado de humedad del SPI con texto e ícono (nunca solo color). */
function EstadoSpi({ d }: { d: Departamento }) {
  if (!d.spi_confiable) return <Insignia>{t("No interpretable (árido)", "Not interpretable (arid)")}</Insignia>;
  const v = d.spi12;
  if (v <= -1) return <Insignia tono="serious" icono={Droplets}>{t("Seco", "Dry")} {numero(v, 2, { signo: true })}</Insignia>;
  if (v >= 1) return <Insignia tono="accent" icono={CloudRain}>{t("Húmedo", "Wet")} {numero(v, 2, { signo: true })}</Insignia>;
  return <Insignia>{t("Normal", "Normal")} {numero(v, 2, { signo: true })}</Insignia>;
}

function puntos(deps: Departamento[], metrica: Metrica): Esquemas["Feature"][] {
  const valor = (d: Departamento) =>
    metrica === "temperatura" ? d.tendencia_temperatura.sen_por_decada : metrica === "lluvia" ? Math.log10(1 + d.lluvia_anual_media_mm) : d.tendencia_lluvia.sen_por_decada;
  const vals = deps.map(valor);
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  return deps.map((d) => ({
    type: "Feature",
    id: d.id,
    geometry: { type: "Point", coordinates: [d.lon, d.lat] },
    properties: { nombre: d.nombre, valor: max > min ? (valor(d) - min) / (max - min) : 0.5, original: valor(d) },
  }));
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
  const [metrica, setMetrica] = useState<Metrica>("temperatura");
  const r = consulta.data?.resultado as Panorama | null | undefined;
  const deps = useMemo(() => r?.departamentos ?? [], [r]);
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
            pie={t(`Generado ${fechaHora(consulta.data?.generado_utc)} · intensidad del azul = valor relativo entre departamentos`, `Generated ${fechaHora(consulta.data?.generado_utc)} · blue intensity = relative value across departments`)}
          >
            <MapaPuntos
              puntos={puntos(deps, metrica)}
              color={RAMPA}
              radio={9}
              centro={[-75.5, -9.5]}
              zoom={4.2}
              alto={460}
              descripcion={t("Departamentos del Perú", "Departments of Peru")}
              etiqueta={(p) => `${String(p.nombre)}: ${numero(Number(p.original), 2)}`}
            />
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
        </>
      )}
    </div>
  );
}
