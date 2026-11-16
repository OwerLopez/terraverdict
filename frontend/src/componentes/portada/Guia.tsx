/**
 * Bloques de orientación de la portada: guía de 3 minutos para el jurado, banner del mapa satelital y
 * muro de misiones. Todo enlaza a funciones reales; las cifras salen de la API (`/api/v1/portada`) o del
 * manifiesto verificado del time-lapse, nunca de texto fijo.
 */
import { AlertTriangle, ArrowRight, Bot, Compass, Globe2, LineChart, Mountain, Satellite, ShieldCheck, Sun, Target, Waves } from "lucide-react";
import { Link } from "react-router-dom";
import { abrirTerra, PREGUNTAS_RAPIDAS } from "../ChatFlotante";
import { abrirRecorrido } from "../Recorrido";
import { numero } from "../../lib/formato";
import { t } from "../../lib/i18n";
import { LAPSO } from "../../lib/timelapse";

type Habilidad = { valor: number | null; modelo: string | null; horizonte: string | null } | null | undefined;

const COLORES_PASO = ["from-[#0d366b] to-[#1d63c8]", "from-[#e87ba4] to-[#6250d6]", "from-[#eb6834] to-[#e34948]", "from-[#008300] to-[#1baf7a]"];

function Paso({ n, icono: Icono, titulo, texto, accion, a, alClic }: {
  n: number;
  icono: typeof Globe2;
  titulo: string;
  texto: string;
  accion: string;
  a?: string;
  alClic?: () => void;
}) {
  const cuerpo = (
    <>
      <div className="flex items-center gap-3">
        <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-gradient-to-br ${COLORES_PASO[(n - 1) % COLORES_PASO.length]} text-white shadow`}><Icono className="h-5 w-5" aria-hidden /></span>
        <p className="etiqueta">{t(`Paso ${n}`, `Step ${n}`)}</p>
      </div>
      <p className="mt-3 text-[15px] font-semibold leading-snug text-ink">{titulo}</p>
      <p className="mt-1.5 flex-1 text-[12.5px] leading-relaxed text-ink-2">{texto}</p>
      <span className="mt-3 inline-flex items-center gap-1 text-[12.5px] font-semibold text-accent-ink">{accion} <ArrowRight className="h-3.5 w-3.5" aria-hidden /></span>
    </>
  );
  const clase = "flex h-full flex-col rounded-2xl border border-line bg-surface p-4 text-left shadow-tarjeta transition-transform hover:-translate-y-0.5 hover:border-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent";
  return a ? <Link to={a} className={clase}>{cuerpo}</Link> : <button type="button" onClick={alClic} className={clase}>{cuerpo}</button>;
}

/** Portada: banner con degradado, la pregunta del problema y las tres acciones principales. */
export function HeroPortada({ alMapa }: { alMapa: () => void }) {
  return (
    <section data-tour="hero" className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#071a35] via-[#0d366b] to-[#0b6a8a] p-6 text-white shadow-flotante md:p-9">
      <div aria-hidden className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-[#0ea5b7]/30 blur-3xl" />
      <div aria-hidden className="pointer-events-none absolute -bottom-28 left-1/3 h-72 w-72 rounded-full bg-[#eb6834]/25 blur-3xl" />
      <div className="relative max-w-3xl">
        <p className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-[11.5px] font-semibold uppercase tracking-wider text-white/85 ring-1 ring-white/15">
          <Satellite className="h-3.5 w-3.5" aria-hidden /> {t("NASA Space Apps 2026 · Cuenca del Chili, Arequipa → Perú", "NASA Space Apps 2026 · Chili basin, Arequipa → Peru")}
        </p>
        <h1 className="mt-4 text-[28px] font-semibold leading-[1.15] tracking-tight md:text-[40px]">
          {t("Arequipa se queda sin agua ", "Arequipa runs out of water ")}
          <span className="bg-gradient-to-r from-[#7dd3fc] via-[#5eead4] to-[#fdba74] bg-clip-text text-transparent">
            {t("por falta… y por exceso", "from too little… and from too much")}
          </span>
        </h1>
        <p className="mt-3 max-w-2xl text-[15.5px] leading-relaxed text-white/85">
          {t(
            "TerraVerdict usa datos abiertos de NASA para responder, con evidencia auditable, tres preguntas: ¿qué está cambiando de verdad?, ¿qué se puede anticipar? y ¿dónde conviene actuar?",
            "TerraVerdict uses NASA open data to answer three questions with auditable evidence: what is really changing, what can be anticipated, and where to act.",
          )}
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <button type="button" onClick={abrirRecorrido} className="inline-flex items-center gap-2 rounded-xl bg-white px-5 py-2.5 text-[14px] font-semibold text-[#0d366b] shadow-lg transition hover:-translate-y-0.5">
            <Compass className="h-4 w-4" aria-hidden /> {t("Iniciar el recorrido guiado", "Start the guided tour")}
          </button>
          <button type="button" onClick={() => abrirTerra()} className="inline-flex items-center gap-2 rounded-xl bg-white/10 px-4 py-2.5 text-[14px] font-semibold text-white ring-1 ring-white/30 transition hover:bg-white/20">
            <Bot className="h-4 w-4" aria-hidden /> {t("Preguntar a la IA", "Ask the AI")}
          </button>
          <button type="button" onClick={alMapa} className="inline-flex items-center gap-2 rounded-xl bg-white/10 px-4 py-2.5 text-[14px] font-semibold text-white ring-1 ring-white/30 transition hover:bg-white/20">
            <Globe2 className="h-4 w-4" aria-hidden /> {t("Mapa satelital 3D", "3D satellite map")}
          </button>
        </div>
      </div>
    </section>
  );
}

/**
 * "Qué resuelve" en tres tarjetas: el problema, lo que hace el sistema y por qué creerle. Sin cifras
 * escritas a mano: los números concretos aparecen debajo, leídos de la API y con su fuente.
 */
export function QueResuelve() {
  const tarjetas: { icono: typeof Globe2; color: string; etiqueta: [string, string]; titulo: [string, string]; texto: [string, string] }[] = [
    {
      icono: AlertTriangle,
      color: "from-[#eb6834] to-[#e34948]",
      etiqueta: ["El problema", "The problem"],
      titulo: ["Demasiada poca agua… y demasiada", "Too little water… and too much"],
      texto: [
        "Arequipa, la segunda ciudad del Perú, depende de las represas del Chili. La sequía las vacía y la lluvia extrema arrastra lodo a la planta potabilizadora y corta el servicio (febrero de 2025).",
        "Arequipa, Peru's second-largest city, depends on the Chili basin reservoirs. Drought empties them, and extreme rain washes mud into the treatment plant and cuts the supply (February 2025).",
      ],
    },
    {
      icono: Target,
      color: "from-[#1d63c8] to-[#0ea5b7]",
      etiqueta: ["Lo que hace TerraVerdict", "What TerraVerdict does"],
      titulo: ["Convierte datos de NASA en veredictos probados", "Turns NASA data into tested verdicts"],
      texto: [
        "Cruza lluvia satelital GPM IMERG (desde 1998), clima NASA POWER (desde 1981) y catálogos oficiales para decir qué tendencias son reales, qué se puede pronosticar y con cuánta anticipación, con intervalos del 90 %.",
        "It combines GPM IMERG satellite rain (since 1998), NASA POWER climate (since 1981) and official hazard catalogs to tell which trends are real, what can be forecast and how far ahead, with 90 % intervals.",
      ],
    },
    {
      icono: ShieldCheck,
      color: "from-[#008300] to-[#1baf7a]",
      etiqueta: ["Por qué creerle", "Why you can trust it"],
      titulo: ["Cada cifra es auditable", "Every number is auditable"],
      texto: [
        "Cada resultado enlaza a descargas con hash SHA-256 y a una prueba fuera de muestra; si la evidencia no alcanza, se abstiene. La IA solo responde con resultados publicados y un verificador revisa cada cifra.",
        "Every result links to SHA-256-hashed downloads and an out-of-sample test; when evidence is insufficient it abstains. The AI answers only from published results, and a verifier checks each figure.",
      ],
    },
  ];
  return (
    <section aria-label={t("Qué resuelve TerraVerdict", "What TerraVerdict solves")} className="grid gap-3 md:grid-cols-3">
      {tarjetas.map(({ icono: Icono, color, etiqueta, titulo, texto }) => (
        <div key={etiqueta[1]} className="relative overflow-hidden rounded-2xl border border-line bg-surface p-4 pt-5 shadow-tarjeta">
          <span aria-hidden className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${color}`} />
          <p className="etiqueta flex items-center gap-2">
            <span className={`grid h-7 w-7 place-items-center rounded-lg bg-gradient-to-br ${color} text-white`}><Icono className="h-4 w-4" aria-hidden /></span>
            {t(...etiqueta)}
          </p>
          <p className="mt-2 text-[15.5px] font-semibold leading-snug text-ink">{t(...titulo)}</p>
          <p className="mt-1.5 text-[13px] leading-relaxed text-ink-2">{t(...texto)}</p>
        </div>
      ))}
    </section>
  );
}

/** Guía de evaluación en 3 minutos: cuatro accesos directos a lo que distingue al proyecto. */
export function GuiaJurado({ habilidadSequia }: { habilidadSequia: Habilidad }) {
  const h = habilidadSequia;
  return (
    <section aria-labelledby="guia-jurado" className="rounded-3xl border border-line bg-gradient-to-br from-[#0d366b]/[0.07] to-transparent p-5 md:p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="guia-jurado" className="flex items-center gap-2 text-[18px] font-semibold tracking-tight text-ink">
          <Compass className="h-5 w-5 text-accent" aria-hidden /> {t("Evaluación guiada en 3 minutos", "3-minute guided evaluation for judges")}
        </h2>
        <p className="text-[12.5px] text-ink-3">{t("Cuatro paradas; cada una abre la función real.", "Four stops; each one opens the real feature.")}</p>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Paso n={1} icono={Globe2} a="/mapa" titulo={t("Mapa satelital 3D de la cuenca", "Interactive 3D basin map")} texto={t("Capas NASA GIBS (MODIS, SMAP) e imágenes HLS de 30 m (Sentinel-2 y Landsat), relieve 3D, cortina entre fechas y time-lapse de Aguada Blanca.", "NASA GIBS layers (MODIS, SMAP) and 30 m HLS imagery (Sentinel-2 and Landsat), 3D terrain, date swipe and an Aguada Blanca time-lapse.")} accion={t("Abrir el mapa", "Open the map")} />
        <Paso n={2} icono={Bot} alClic={() => abrirTerra(t(...(PREGUNTAS_RAPIDAS[2] as [string, string])))} titulo={t("IA con verificación numérica", "AI with numeric verification")} texto={t("Terra (Google Gemini) responde solo con expedientes publicados, los cita y un verificador determinista comprueba cada cifra: se ve cuáles pasan y cuáles no.", "Terra (Google Gemini) answers only from published case files, cites them, and a deterministic verifier checks every figure: you see which ones pass and which do not.")} accion={t("Preguntar a Terra", "Ask Terra")} />
        <Paso
          n={3}
          icono={LineChart}
          a="/modelos"
          titulo={h?.valor != null ? t(`Sequía a 1 mes: habilidad ${numero(h.valor, 2)}`, `Drought at 1 month: skill ${numero(h.valor, 2)}`) : t("Pronóstico de sequía a 1 mes", "1-month drought forecast")}
          texto={h?.valor != null ? t(`Modelo elegido en validación (${h.modelo}): ${numero(h.valor * 100, 0)} % menos error cuadrático que la climatología en la prueba fuera de muestra, con intervalo conformal del 90 %.`, `Model chosen on validation (${h.modelo}): ${numero(h.valor * 100, 0)} % less squared error than climatology on the out-of-sample test, with a 90 % conformal interval.`) : t("Comparación de modelos fuera de muestra con intervalos conformales.", "Out-of-sample model comparison with conformal intervals.")}
          accion={t("Ver predicción frente a realidad", "See prediction vs reality")}
        />
        <Paso n={4} icono={ShieldCheck} a="/procesos" titulo={t("Auditoría y prueba SHA-256", "Audit & SHA-256 proof")} texto={t("Ejecuciones reales del pipeline, descargas de NASA con su hash SHA-256 y la cadena de custodia de cada resultado.", "Real pipeline runs, NASA downloads with their SHA-256 hash and the chain of custody of every result.")} accion={t("Ver procesos", "See pipeline runs")} />
      </div>
    </section>
  );
}

/** Banner del mapa con una imagen HLS real de Aguada Blanca (la más reciente sin nubes del manifiesto). */
export function BannerMapa() {
  const ultimo = [...LAPSO.meses].reverse().find((m) => m.elegida)?.elegida;
  return (
    <Link to="/mapa" className="group relative block overflow-hidden rounded-3xl border border-line shadow-tarjeta">
      <div className="grid md:grid-cols-[1fr_300px]">
        <div className="relative z-10 bg-gradient-to-r from-[#0a1f3d] via-[#0d366b] to-[#0d366b]/80 p-6 text-white md:p-8">
          <p className="text-[12px] font-semibold uppercase tracking-wider text-white/70">{t("Gemelo satelital de la cuenca", "Satellite view of the basin")}</p>
          <h2 className="mt-2 max-w-xl text-[22px] font-semibold leading-tight tracking-tight md:text-[26px]">
            {t("Explore la cuenca del Chili en 3D: NASA GIBS, HLS 30 m y relieve", "Explore the 3D satellite view of the Chili basin: NASA GIBS, HLS 30 m and elevation")}
          </h2>
          <p className="mt-2 max-w-xl text-[13px] leading-relaxed text-white/80">
            {t("Relieve 3D (SRTM y otras fuentes vía Mapzen), capas MODIS y SMAP, sismos USGS y volcanes GVP, cortina entre fechas y time-lapse mensual del embalse.", "3D terrain (SRTM and other sources via Mapzen), MODIS and SMAP layers, USGS earthquakes and GVP volcanoes, date swipe and a monthly reservoir time-lapse.")}
          </p>
          <span className="mt-4 inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2 text-[13.5px] font-semibold text-[#0d366b] transition-transform group-hover:translate-x-0.5">
            <Globe2 className="h-4 w-4" aria-hidden /> {t("Abrir el mapa satelital", "Open the satellite map")}
          </span>
        </div>
        {ultimo && (
          <figure className="relative min-h-[200px] bg-black">
            <img src={ultimo.url} alt={t(`Represa Aguada Blanca, ${ultimo.sensor}, ${ultimo.fecha}`, `Aguada Blanca reservoir, ${ultimo.sensor}, ${ultimo.fecha}`)} className="absolute inset-0 h-full w-full object-cover [image-rendering:auto]" loading="lazy" />
            <figcaption className="absolute inset-x-2 bottom-2 rounded-md bg-black/65 px-2 py-1 text-[11px] text-white">
              Aguada Blanca · {ultimo.sensor} · {ultimo.fecha} · NASA GIBS
            </figcaption>
          </figure>
        )}
      </div>
    </Link>
  );
}

/**
 * Misiones y productos que sostienen el proyecto, con su uso real en TerraVerdict. Periodos y resoluciones
 * comprobados contra la documentación de cada producto y contra los manifiestos de descarga; HLS S30 se
 * atribuye a ESA/Copernicus (Sentinel-2) armonizado por NASA, y MODIS no se presenta como de 30 m.
 */
const MISIONES: { icono: typeof Globe2; nombre: string; producto: [string, string]; dato: [string, string]; uso: [string, string] }[] = [
  { icono: Waves, nombre: "NASA GPM IMERG", producto: ["IMERG Final diaria V07 · 0,1° · GES DISC", "IMERG Final daily V07 · 0.1° · GES DISC"], dato: ["1998–sep 2025, diaria completa", "1998–Sep 2025, full daily record"], uso: ["Objetivo de la Matriz de Relevancia (lluvia extrema en la cabecera)", "Target of the Relevance Matrix (extreme rain in the headwaters)"] },
  { icono: Sun, nombre: "NASA POWER", producto: ["MERRA-2 (meteorología) y CERES/SRB (radiación) · celdas de 0,5°", "MERRA-2 (meteorology) and CERES/SRB (radiation) · 0.5° cells"], dato: ["Diaria 1981–oct 2026 (radiación desde 1984)", "Daily 1981–Oct 2026 (radiation since 1984)"], uso: ["Tendencias, sequía (SPI), lluvia extrema y los 25 departamentos", "Trends, drought (SPI), extreme rain and the 25 departments"] },
  { icono: Satellite, nombre: "NASA MODIS Terra", producto: ["Color real 250 m · NDVI 1 km · temperatura de superficie 1 km", "True color 250 m · NDVI 1 km · land surface temperature 1 km"], dato: ["2000–hoy vía NASA GIBS; LST descargada para el análisis", "2000–today via NASA GIBS; LST downloaded for analysis"], uso: ["Capas del mapa y temperatura de superficie", "Map layers and land surface temperature"] },
  { icono: Satellite, nombre: "HLS (NASA/USGS + ESA)", producto: ["Landsat 8/9 (L30) y Sentinel-2 de ESA/Copernicus (S30) armonizados por NASA · 30 m", "Landsat 8/9 (L30) and ESA/Copernicus Sentinel-2 (S30) harmonized by NASA · 30 m"], dato: [`${LAPSO.meses.filter((m) => m.elegida).length} meses verificados sin nubes sobre Aguada Blanca`, `${LAPSO.meses.filter((m) => m.elegida).length} cloud-free months verified over Aguada Blanca`], uso: ["Cortina entre fechas y time-lapse del embalse", "Date swipe and reservoir time-lapse"] },
  { icono: Waves, nombre: "NASA SMAP L4", producto: ["Humedad del suelo en la zona radicular · 9 km", "Root-zone soil moisture · 9 km"], dato: ["2015–hoy vía NASA GIBS", "2015–today via NASA GIBS"], uso: ["Capa de contexto en el mapa (aún no entra en los modelos)", "Context layer on the map (not yet used in the models)"] },
  { icono: Mountain, nombre: "SRTM (NASA/NGA)", producto: ["Modelo digital de elevación, vía Mapzen Terrain Tiles (con 3DEP, GMTED2010 y ETOPO1)", "Digital elevation model, via Mapzen Terrain Tiles (with 3DEP, GMTED2010 and ETOPO1)"], dato: ["Relieve 3D del visor (teselas hasta z13)", "3D terrain in the viewer (tiles up to z13)"], uso: ["Relieve 3D de la cuenca", "3D terrain of the basin"] },
  { icono: Mountain, nombre: "NASA Global Landslide Catalog", producto: ["Inventario de deslizamientos detonados por lluvia", "Rainfall-triggered landslide inventory"], dato: ["Eventos del sur del Perú", "Events in southern Peru"], uso: ["Deslizamientos (con abstención si hay menos de 30 eventos)", "Landslides (abstains with fewer than 30 events)"] },
];

export function MuroMisiones() {
  return (
    <section aria-labelledby="muro-misiones">
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="muro-misiones" className="text-[18px] font-semibold tracking-tight text-ink">{t("Datos de observación de la Tierra que sostienen el proyecto", "Earth observation data behind the project")}</h2>
        <p className="text-[12px] text-ink-3">{t("Nombres de misiones como referencia; TerraVerdict no está respaldado por NASA, ESA ni USGS.", "Mission names for reference; TerraVerdict is not endorsed by NASA, ESA or USGS.")}</p>
      </div>
      <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {MISIONES.map((m) => (
          <li key={m.nombre} className="rounded-2xl border border-line bg-surface p-4 shadow-tarjeta">
            <p className="flex items-center gap-2 text-[14px] font-semibold text-ink"><m.icono className="h-4 w-4 text-accent" aria-hidden /> {m.nombre}</p>
            <p className="mt-1.5 text-[12px] text-ink-2">{t(...m.producto)}</p>
            <p className="mt-1.5 text-[12px] font-medium text-ink">{t(...m.dato)}</p>
            <p className="mt-1 text-[11.5px] text-ink-3">{t(...m.uso)}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
