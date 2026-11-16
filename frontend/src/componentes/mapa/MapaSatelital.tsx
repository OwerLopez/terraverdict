import { clsx } from "clsx";
import { Activity, Crosshair, Layers, Mountain, MapPin, Satellite, SplitSquareHorizontal, Waves } from "lucide-react";
import maplibregl, { type GeoJSONSource, type Map as MapaML, type StyleSpecification } from "maplibre-gl";
import { useEffect, useMemo, useRef, useState } from "react";
import type { Esquemas } from "../../api/cliente";
import { useCapaSismos, useCapaVolcanes } from "../../api/consultas";
import { numero } from "../../lib/formato";
import { t } from "../../lib/i18n";
import { Insignia } from "../ui";

const GIBS = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best";

type Periodo = "diaria" | "8dias" | "mensual";

/**
 * Capas de NASA GIBS verificadas contra su WMTSCapabilities (2026-11-16): identificador, nivel de zoom
 * máximo (TileMatrixSet), formato, periodicidad y leyenda oficial. GIBS ajusta la fecha al periodo de
 * cada producto (p. ej. cualquier día de un mes devuelve el compuesto mensual).
 */
export const CAPAS = [
  {
    id: "MODIS_Terra_CorrectedReflectance_TrueColor",
    grupo: "imagen",
    nombre: ["Color real · MODIS Terra", "True color · MODIS Terra"],
    resolucion: "250 m",
    nivel: 9,
    ext: "jpg",
    periodo: "diaria" as Periodo,
    significado: ["Imagen del día: nubes, nieve en las cumbres, cauces y represas visibles.", "Image of the day: clouds, snow on the peaks, river beds and reservoirs."],
  },
  {
    id: "HLS_S30_Nadir_BRDF_Adjusted_Reflectance",
    grupo: "imagen",
    nombre: ["Sentinel-2 HLS · 30 m", "Sentinel-2 HLS · 30 m"],
    resolucion: "30 m",
    nivel: 12,
    ext: "png",
    periodo: "diaria" as Periodo,
    significado: ["Detalle de 30 m (pasada cada 2–5 días): represas, bofedales y zonas urbanas.", "30 m detail (revisit every 2–5 days): reservoirs, wetlands and urban areas."],
  },
  {
    id: "MODIS_Terra_L3_NDVI_Monthly",
    grupo: "analisis",
    nombre: ["Vegetación (NDVI mensual)", "Vegetation (monthly NDVI)"],
    resolucion: "1 km",
    nivel: 7,
    ext: "png",
    periodo: "mensual" as Periodo,
    leyenda: "MODIS_L3_NDVI_H.svg",
    significado: ["Verdor de la vegetación: en sequía los bofedales y pastos de la cabecera pierden verdor.", "Vegetation greenness: in drought the headwater wetlands and grasslands lose greenness."],
  },
  {
    id: "MODIS_Terra_L3_Land_Surface_Temp_8Day_Day",
    grupo: "analisis",
    nombre: ["Temperatura de superficie (día, 8 días)", "Land surface temperature (day, 8-day)"],
    resolucion: "1 km",
    nivel: 7,
    ext: "png",
    periodo: "8dias" as Periodo,
    leyenda: "MODIS_Land_Surface_Temp_H.svg",
    significado: ["Calentamiento del suelo (no del aire): contraste entre altiplano, valles y ciudad.", "Ground heating (not air): contrast between high plateau, valleys and the city."],
  },
  {
    id: "SMAP_L4_Analyzed_Root_Zone_Soil_Moisture",
    grupo: "analisis",
    nombre: ["Humedad del suelo (zona radicular)", "Soil moisture (root zone)"],
    resolucion: "9 km",
    nivel: 6,
    ext: "png",
    periodo: "diaria" as Periodo,
    leyenda: "SMAP_Analyzed_Soil_Moisture_H.svg",
    significado: ["Agua disponible en el suelo (desde 2015): suelo saturado favorece crecidas y huaicos.", "Water available in the soil (since 2015): saturated soil favors floods and debris flows."],
  },
] as const;

type Capa = (typeof CAPAS)[number];
type CapaId = Capa["id"];

/** Fecha en el formato del periodo de la capa (los compuestos mensuales empiezan el día 1). */
function fechaCapa(capa: Capa, fecha: string): string {
  return capa.periodo === "mensual" ? `${fecha.slice(0, 7)}-01` : fecha;
}

export function urlCapa(id: CapaId, fecha: string): string {
  const capa = CAPAS.find((c) => c.id === id) ?? CAPAS[0];
  return `${GIBS}/${capa.id}/default/${fechaCapa(capa, fecha)}/GoogleMapsCompatible_Level${capa.nivel}/{z}/{y}/{x}.${capa.ext}`;
}

const REFERENCIAS = `${GIBS}/Reference_Features_15m/default/default/GoogleMapsCompatible_Level13/{z}/{y}/{x}.png`;

function haceDias(n: number): string {
  return new Date(Date.now() - n * 86_400_000).toISOString().slice(0, 10);
}

/** Comparaciones con fechas de la crónica de eventos documentados (datos/eventos/arequipa.json). */
const COMPARACIONES: { a: string; b: string; texto: [string, string]; capa: CapaId }[] = [
  { a: "2023-11-07", b: "2025-02-15", capa: "MODIS_Terra_L3_NDVI_Monthly", texto: ["Represas al 39 % (nov 2023) frente a crecida y turbidez (feb 2025)", "Reservoirs at 39 % (Nov 2023) vs flood and turbidity (Feb 2025)"] },
  { a: "2024-09-15", b: "2025-02-15", capa: "SMAP_L4_Analyzed_Root_Zone_Soil_Moisture", texto: ["Estiaje (sep 2024) frente a lluvias (feb 2025)", "Dry season (Sep 2024) vs rainy season (Feb 2025)"] },
];

/** Color por profundidad (km): someros (más destructivos) en cálido, profundos en frío. */
const COLOR_PROFUNDIDAD: maplibregl.ExpressionSpecification = [
  "step",
  ["get", "profundidad_km"],
  "#eb6834",
  70,
  "#f0b429",
  150,
  "#86b6ef",
  300,
  "#5b6cff",
];

function poligonoBbox(b: number[]) {
  const [x1, y1, x2, y2] = b as [number, number, number, number];
  return {
    type: "Feature" as const,
    properties: {},
    geometry: { type: "Polygon" as const, coordinates: [[[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]]] },
  };
}

export function MapaSatelital({
  dominio,
  unidades,
}: {
  dominio: Esquemas["DominioSalida"] | undefined;
  unidades: Esquemas["Feature"][];
}) {
  const contenedor = useRef<HTMLDivElement>(null);
  const mapa = useRef<MapaML | null>(null);
  const [listo, setListo] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [capa, setCapa] = useState<CapaId>("MODIS_Terra_L3_NDVI_Monthly");
  const [fecha, setFecha] = useState(haceDias(35));
  const [comparar, setComparar] = useState(false);
  const [fechaB, setFechaB] = useState(haceDias(35));
  const [mezcla, setMezcla] = useState(50);
  // 2D por defecto: en 3D el relieve (2–6 km de altura) tapa los sismos y volcanes dibujados a nivel del mar.
  const [tresD, setTresD] = useState(false);
  const [exageracion, setExageracion] = useState(1.6);
  const [verSismos, setVerSismos] = useState(true);
  const [verVolcanes, setVerVolcanes] = useState(true);
  const [verReferencias, setVerReferencias] = useState(true);
  const sismos = useCapaSismos(5);
  const volcanes = useCapaVolcanes();

  const def = CAPAS.find((c) => c.id === capa) ?? CAPAS[0];
  const bbox = dominio?.bbox;
  const conGeometria = useMemo(() => unidades.filter((u) => u.geometry?.type === "Point"), [unidades]);
  const pendientes = useMemo(() => unidades.filter((u) => !u.geometry), [unidades]);

  useEffect(() => {
    if (!contenedor.current || mapa.current) return;
    const vacia = { type: "FeatureCollection" as const, features: [] };
    const estilo: StyleSpecification = {
      version: 8,
      sources: {
        fondo: {
          type: "raster",
          tiles: [`${GIBS}/BlueMarble_ShadedRelief_Bathymetry/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg`],
          tileSize: 256,
          maxzoom: 8,
          attribution: t("Imágenes: NASA GIBS / ESDIS", "Imagery: NASA GIBS / ESDIS"),
        },
        relieve: {
          type: "raster-dem",
          tiles: ["https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"],
          encoding: "terrarium",
          tileSize: 256,
          maxzoom: 13,
          // Atribución exigida por tilezen/joerd (docs/licencias-y-atribuciones.md).
          attribution: t(
            "Relieve: Mapzen Terrain Tiles · 3DEP, SRTM, GMTED2010 (USGS), ETOPO1 (NOAA)",
            "Terrain: Mapzen Terrain Tiles · 3DEP, SRTM, GMTED2010 (USGS), ETOPO1 (NOAA)",
          ),
        },
        sombras: { type: "raster-dem", tiles: ["https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"], encoding: "terrarium", tileSize: 256, maxzoom: 13 },
        referencias: { type: "raster", tiles: [REFERENCIAS], tileSize: 256, maxzoom: 13 },
        dominio: { type: "geojson", data: vacia },
        sismos: { type: "geojson", data: vacia },
        volcanes: { type: "geojson", data: vacia },
      },
      layers: [
        { id: "fondo", type: "raster", source: "fondo" },
        { id: "sombras", type: "hillshade", source: "sombras", paint: { "hillshade-exaggeration": 0.3, "hillshade-shadow-color": "#000000" } },
        { id: "referencias", type: "raster", source: "referencias", paint: { "raster-opacity": 0.85 } },
        { id: "dominio-relleno", type: "fill", source: "dominio", paint: { "fill-color": "#3987e5", "fill-opacity": 0.05 } },
        { id: "dominio-borde", type: "line", source: "dominio", paint: { "line-color": "#86b6ef", "line-width": 1.6, "line-dasharray": [3, 2] } },
        {
          id: "sismos",
          type: "circle",
          source: "sismos",
          paint: {
            "circle-radius": ["interpolate", ["linear"], ["get", "magnitud"], 5, 3, 6, 6, 7, 10, 8, 15],
            "circle-color": COLOR_PROFUNDIDAD,
            "circle-opacity": 0.8,
            "circle-stroke-color": "#ffffff",
            "circle-stroke-width": 0.8,
          },
        },
        {
          id: "volcanes",
          type: "circle",
          source: "volcanes",
          paint: {
            "circle-radius": ["interpolate", ["linear"], ["get", "erupciones"], 0, 6, 25, 14],
            "circle-color": "#d64545",
            "circle-stroke-color": "#ffffff",
            "circle-stroke-width": 2,
          },
        },
      ],
    };
    try {
      const m = new maplibregl.Map({
        container: contenedor.current,
        style: estilo,
        center: [-71.4, -16.0],
        zoom: 7.6,
        pitch: 0,
        bearing: 0,
        maxPitch: 80,
        attributionControl: { compact: true },
      });
      m.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");
      m.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-right");
      m.on("load", () => setListo(true));
      m.on("error", (e) => {
        const msg = e.error?.message ?? "";
        if (msg.includes("WebGL")) setError(t("Su navegador no soporta WebGL: el mapa 3D no puede mostrarse.", "Your browser does not support WebGL: the 3D map cannot be shown."));
      });
      const ficha = (lngLat: maplibregl.LngLat, html: HTMLElement) => new maplibregl.Popup({ offset: 10, closeButton: false }).setLngLat(lngLat).setDOMContent(html).addTo(m);
      m.on("click", "sismos", (e) => {
        const p = e.features?.[0]?.properties as { fecha: string; magnitud: number; profundidad_km: number } | undefined;
        if (!p) return;
        const el = document.createElement("div");
        el.style.cssText = "font:12px system-ui;color:#0b0b0b";
        el.textContent = `M ${p.magnitud} · ${p.fecha} · ${t("profundidad", "depth")} ${numero(p.profundidad_km, 0)} km · USGS ComCat`;
        ficha(e.lngLat, el);
      });
      m.on("click", "volcanes", (e) => {
        const p = e.features?.[0]?.properties as { nombre: string; erupciones: number; probabilidad_anual: number; ultima_erupcion?: number } | undefined;
        if (!p) return;
        const el = document.createElement("div");
        el.style.cssText = "font:12px system-ui;color:#0b0b0b;max-width:240px";
        el.textContent = t(
          `${p.nombre}: ${p.erupciones} erupciones desde 1550 · ${numero(p.probabilidad_anual * 100, 1)} % anual (frecuencia histórica, no pronóstico) · Smithsonian GVP`,
          `${p.nombre}: ${p.erupciones} eruptions since 1550 · ${numero(p.probabilidad_anual * 100, 1)} % per year (historical frequency, not a forecast) · Smithsonian GVP`,
        );
        ficha(e.lngLat, el);
      });
      for (const capaId of ["sismos", "volcanes"]) {
        m.on("mouseenter", capaId, () => (m.getCanvas().style.cursor = "pointer"));
        m.on("mouseleave", capaId, () => (m.getCanvas().style.cursor = ""));
      }
      mapa.current = m;
    } catch {
      setError(t("No se pudo iniciar el mapa (WebGL no disponible).", "The map could not start (WebGL unavailable)."));
    }
    return () => {
      mapa.current?.remove();
      mapa.current = null;
    };
    // El mapa se crea una sola vez; los cambios se aplican en los efectos siguientes.
     
  }, []);

  // Capa principal (A) y, en modo comparación, la segunda fecha (B) encima con opacidad regulable.
  useEffect(() => {
    const m = mapa.current;
    if (!m || !listo) return;
    for (const id of ["capa-b", "capa-a"]) {
      if (m.getLayer(id)) m.removeLayer(id);
      if (m.getSource(id)) m.removeSource(id);
    }
    m.addSource("capa-a", { type: "raster", tiles: [urlCapa(def.id, fecha)], tileSize: 256, maxzoom: def.nivel });
    m.addLayer({ id: "capa-a", type: "raster", source: "capa-a", paint: { "raster-fade-duration": 200 } }, "sombras");
    if (comparar) {
      m.addSource("capa-b", { type: "raster", tiles: [urlCapa(def.id, fechaB)], tileSize: 256, maxzoom: def.nivel });
      m.addLayer({ id: "capa-b", type: "raster", source: "capa-b", paint: { "raster-opacity": mezcla / 100, "raster-fade-duration": 0 } }, "sombras");
    }
    // La mezcla se ajusta en su propio efecto (sin recrear fuentes).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [def.id, def.nivel, fecha, fechaB, comparar, listo]);

  useEffect(() => {
    const m = mapa.current;
    if (m && listo && m.getLayer("capa-b")) m.setPaintProperty("capa-b", "raster-opacity", mezcla / 100);
  }, [mezcla, listo]);

  useEffect(() => {
    const m = mapa.current;
    if (!m || !listo) return;
    m.setTerrain(tresD ? { source: "relieve", exaggeration: exageracion } : null);
    m.easeTo({ pitch: tresD ? 50 : 0, duration: 600 });
  }, [tresD, exageracion, listo]);

  useEffect(() => {
    const m = mapa.current;
    if (!m || !listo || !bbox) return;
    (m.getSource("dominio") as GeoJSONSource | undefined)?.setData({ type: "FeatureCollection", features: [poligonoBbox(bbox)] });
  }, [bbox, listo]);

  useEffect(() => {
    const m = mapa.current;
    if (!m || !listo) return;
    (m.getSource("sismos") as GeoJSONSource | undefined)?.setData(
      (verSismos && sismos.data ? sismos.data : { type: "FeatureCollection", features: [] }) as GeoJSON.FeatureCollection,
    );
    (m.getSource("volcanes") as GeoJSONSource | undefined)?.setData(
      (verVolcanes && volcanes.data ? volcanes.data : { type: "FeatureCollection", features: [] }) as GeoJSON.FeatureCollection,
    );
    if (m.getLayer("referencias")) m.setLayoutProperty("referencias", "visibility", verReferencias ? "visible" : "none");
  }, [sismos.data, volcanes.data, verSismos, verVolcanes, verReferencias, listo]);

  useEffect(() => {
    const m = mapa.current;
    if (!m || !listo) return;
    const marcadores = conGeometria.map((u) => {
      const el = document.createElement("div");
      el.style.cssText = "width:14px;height:14px;border-radius:999px;background:#eb6834;border:2px solid #fff;box-shadow:0 0 0 4px rgba(235,104,52,.25);cursor:pointer";
      el.setAttribute("aria-label", String(u.properties.nombre ?? u.id));
      const contenido = document.createElement("div");
      contenido.style.cssText = "font:12px system-ui;color:#0b0b0b;max-width:220px";
      const titulo = document.createElement("strong");
      titulo.textContent = String(u.properties.nombre ?? u.id);
      const detalle = document.createElement("div");
      detalle.style.color = "#52514e";
      detalle.textContent = `${u.properties.tipo} · ${t("geometría", "geometry")} ${u.properties.estado_geometria}`;
      contenido.append(titulo, detalle);
      const [lon, lat] = (u.geometry?.coordinates ?? [0, 0]) as [number, number];
      return new maplibregl.Marker({ element: el })
        .setLngLat([lon, lat])
        .setPopup(new maplibregl.Popup({ offset: 14, closeButton: false }).setDOMContent(contenido))
        .addTo(m);
    });
    return () => marcadores.forEach((mk) => mk.remove());
  }, [conGeometria, listo]);

  const volver = () => {
    if (!bbox || !mapa.current) return;
    const [x1, y1, x2, y2] = bbox as [number, number, number, number];
    mapa.current.fitBounds([[x1, y1], [x2, y2]], { padding: 60, pitch: tresD ? 50 : 0, bearing: -18, duration: 1200 });
  };

  const usarComparacion = (c: (typeof COMPARACIONES)[number]) => {
    setCapa(c.capa);
    setFecha(c.a);
    setFechaB(c.b);
    setMezcla(50);
    setComparar(true);
  };

  const botonCapa = (c: Capa) => (
    <button
      key={c.id}
      type="button"
      role="radio"
      aria-checked={capa === c.id}
      onClick={() => setCapa(c.id)}
      className={clsx(
        "flex w-full items-center justify-between rounded-lg px-2.5 py-1.5 text-left text-[12.5px] transition-colors",
        capa === c.id ? "bg-accent-soft font-medium text-accent-ink" : "text-ink-2 hover:bg-surface-2",
      )}
    >
      <span className="flex items-center gap-2">
        {c.grupo === "imagen" ? <Satellite className="h-3.5 w-3.5" /> : <Waves className="h-3.5 w-3.5" />}
        {t(c.nombre[0], c.nombre[1])}
      </span>
      <span className="cifra text-[11px] text-ink-3">{c.resolucion}</span>
    </button>
  );

  return (
    <div className="relative h-full w-full overflow-hidden bg-[#0d0d0d]">
      <div ref={contenedor} className="absolute inset-0" aria-label={t("Mapa satelital de la cuenca del Chili", "Satellite map of the Chili basin")} role="region" />
      {error && <div className="absolute inset-0 grid place-items-center p-6 text-center text-sm text-white/80">{error}</div>}

      <div className="vidrio absolute left-3 top-3 max-h-[calc(100%-1.5rem)] w-[min(92vw,310px)] overflow-y-auto rounded-2xl border border-line p-4 shadow-flotante md:left-5 md:top-5">
        <p className="etiqueta mb-1.5 flex items-center gap-1.5"><Layers className="h-3.5 w-3.5" /> {t("Análisis satelital", "Satellite analysis")}</p>
        <div className="space-y-0.5" role="radiogroup" aria-label={t("Capa de análisis", "Analysis layer")}>
          {CAPAS.filter((c) => c.grupo === "analisis").map(botonCapa)}
        </div>
        <p className="etiqueta mb-1.5 mt-3 flex items-center gap-1.5"><Satellite className="h-3.5 w-3.5" /> {t("Imagen", "Imagery")}</p>
        <div className="space-y-0.5" role="radiogroup" aria-label={t("Capa de imagen", "Imagery layer")}>
          {CAPAS.filter((c) => c.grupo === "imagen").map(botonCapa)}
        </div>

        <label className="mt-3 block text-[12px] text-ink-2">
          {comparar ? t("Fecha A (debajo)", "Date A (below)") : t("Fecha", "Date")}
          <input type="date" value={fecha} max={haceDias(0)} min="2000-02-24" onChange={(e) => e.target.value && setFecha(e.target.value)} className="mt-1 h-9 w-full rounded-lg border border-line bg-surface px-2.5 text-[13px] text-ink" />
        </label>
        <label className="mt-2 flex items-center gap-2 text-[12.5px] font-medium text-ink">
          <input type="checkbox" checked={comparar} onChange={(e) => setComparar(e.target.checked)} className="accent-[var(--accent)]" />
          <SplitSquareHorizontal className="h-3.5 w-3.5" /> {t("Comparar dos fechas", "Compare two dates")}
        </label>
        {comparar && (
          <div className="mt-2 space-y-2">
            <label className="block text-[12px] text-ink-2">
              {t("Fecha B (encima)", "Date B (on top)")}
              <input type="date" value={fechaB} max={haceDias(0)} min="2000-02-24" onChange={(e) => e.target.value && setFechaB(e.target.value)} className="mt-1 h-9 w-full rounded-lg border border-line bg-surface px-2.5 text-[13px] text-ink" />
            </label>
            <label className="block text-[11.5px] text-ink-3">
              <span className="flex justify-between"><span>A · {fechaCapa(def, fecha)}</span><span>B · {fechaCapa(def, fechaB)}</span></span>
              <input type="range" min={0} max={100} value={mezcla} onChange={(e) => setMezcla(Number(e.target.value))} aria-label={t("Mezcla entre la fecha A y la fecha B", "Blend between date A and date B")} className="mt-1 w-full accent-[var(--accent)]" />
            </label>
          </div>
        )}
        <div className="mt-2 space-y-1">
          <p className="text-[11px] text-ink-3">{t("Comparaciones con eventos documentados:", "Comparisons with documented events:")}</p>
          {COMPARACIONES.map((c) => (
            <button key={c.a + c.capa} type="button" onClick={() => usarComparacion(c)} className="block w-full rounded-lg border border-line px-2.5 py-1.5 text-left text-[11.5px] text-ink-2 hover:bg-surface-2 hover:text-ink">
              {t(...c.texto)}
            </button>
          ))}
        </div>

        <p className="etiqueta mb-1.5 mt-3">{t("Capas superpuestas", "Overlays")}</p>
        <div className="space-y-1 text-[12.5px] text-ink">
          <label className="flex items-center gap-2"><input type="checkbox" checked={verSismos} onChange={(e) => setVerSismos(e.target.checked)} className="accent-[var(--accent)]" /><Activity className="h-3.5 w-3.5" /> {t("Sismos M ≥ 5 (USGS, 1973–hoy)", "Earthquakes M ≥ 5 (USGS, 1973–today)")}</label>
          <label className="flex items-center gap-2"><input type="checkbox" checked={verVolcanes} onChange={(e) => setVerVolcanes(e.target.checked)} className="accent-[var(--accent)]" /><Mountain className="h-3.5 w-3.5" /> {t("Volcanes (Smithsonian GVP)", "Volcanoes (Smithsonian GVP)")}</label>
          <label className="flex items-center gap-2"><input type="checkbox" checked={verReferencias} onChange={(e) => setVerReferencias(e.target.checked)} className="accent-[var(--accent)]" /><MapPin className="h-3.5 w-3.5" /> {t("Ríos, vías y lugares", "Rivers, roads and places")}</label>
        </div>

        <div className="mt-3 flex items-center justify-between border-t border-line pt-3">
          <label className="flex items-center gap-2 text-[12.5px] font-medium text-ink">
            <input type="checkbox" checked={tresD} onChange={(e) => setTresD(e.target.checked)} className="accent-[var(--accent)]" />
            <Mountain className="h-3.5 w-3.5" /> {t("Relieve 3D", "3D terrain")}
          </label>
          <button type="button" onClick={volver} className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[12px] text-ink-2 hover:bg-surface-2 hover:text-ink">
            <Crosshair className="h-3.5 w-3.5" /> {t("Cuenca", "Basin")}
          </button>
        </div>
        {tresD && (verSismos || verVolcanes) && (
          <p className="mt-2 text-[11.5px] leading-snug" style={{ color: "var(--serious)" }}>
            {t("En 3D el relieve oculta los sismos y volcanes: desactive el relieve para verlos.", "In 3D the terrain hides earthquakes and volcanoes: turn terrain off to see them.")}
          </p>
        )}
        {tresD && (
          <label className="mt-2 block text-[11.5px] text-ink-3">
            {t("Exageración vertical", "Vertical exaggeration")}: <span className="cifra font-medium text-ink-2">{exageracion.toFixed(1)}×</span>
            <input type="range" min={1} max={3} step={0.1} value={exageracion} onChange={(e) => setExageracion(Number(e.target.value))} className="mt-1 w-full accent-[var(--accent)]" />
          </label>
        )}
      </div>

      {/* Leyenda: qué muestra la capa, su fecha efectiva, resolución, periodicidad y fuente. */}
      <div className="vidrio absolute bottom-10 right-3 w-[min(92vw,340px)] rounded-2xl border border-line p-3.5 shadow-flotante md:right-5">
        <p className="text-[13px] font-semibold text-ink">{t(def.nombre[0], def.nombre[1])}</p>
        <p className="mt-0.5 text-[12px] leading-snug text-ink-2">{t(def.significado[0], def.significado[1])}</p>
        {"leyenda" in def && (
          <img src={`https://gibs.earthdata.nasa.gov/legends/${def.leyenda}`} alt={t("Escala de colores de la capa (NASA GIBS)", "Layer color scale (NASA GIBS)")} className="mt-2 w-full rounded bg-white/90 p-1" loading="lazy" />
        )}
        <p className="mt-2 text-[11px] text-ink-3">
          NASA GIBS · {def.resolucion} · {def.periodo === "mensual" ? t("compuesto mensual", "monthly composite") : def.periodo === "8dias" ? t("compuesto de 8 días", "8-day composite") : t("diaria", "daily")} · {comparar ? `${fechaCapa(def, fecha)} → ${fechaCapa(def, fechaB)}` : fechaCapa(def, fecha)}
        </p>
        {(verSismos || verVolcanes) && (
          <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-line pt-2 text-[11px] text-ink-2">
            {verSismos && (
              <>
                <span className="flex items-center gap-1"><span className="h-2.5 w-2.5 rounded-full" style={{ background: "#eb6834" }} /> {"< 70 km"}</span>
                <span className="flex items-center gap-1"><span className="h-2.5 w-2.5 rounded-full" style={{ background: "#f0b429" }} /> 70–150</span>
                <span className="flex items-center gap-1"><span className="h-2.5 w-2.5 rounded-full" style={{ background: "#86b6ef" }} /> 150–300</span>
                <span className="flex items-center gap-1"><span className="h-2.5 w-2.5 rounded-full" style={{ background: "#5b6cff" }} /> {"> 300 km"}</span>
              </>
            )}
            {verVolcanes && <span className="flex items-center gap-1"><span className="h-2.5 w-2.5 rounded-full border-2 border-white" style={{ background: "#d64545" }} /> {t("volcán (tamaño = erupciones)", "volcano (size = eruptions)")}</span>}
          </div>
        )}
      </div>

      <div className="vidrio absolute bottom-10 left-3 hidden w-[300px] rounded-2xl border border-line p-4 shadow-flotante xl:block xl:left-[340px]">
        <p className="etiqueta mb-2 flex items-center gap-1.5"><MapPin className="h-3.5 w-3.5" /> {t("Unidades de análisis", "Analysis units")}</p>
        <ul className="space-y-1.5 text-[12.5px]">
          {conGeometria.map((u) => (
            <li key={u.id}>
              <button
                type="button"
                className="flex w-full items-center gap-2 text-left text-ink hover:text-accent-ink"
                onClick={() => {
                  const [lon, lat] = (u.geometry?.coordinates ?? [0, 0]) as [number, number];
                  mapa.current?.flyTo({ center: [lon, lat], zoom: 11, duration: 1400 });
                }}
              >
                <span className="h-2.5 w-2.5 shrink-0 rounded-full border-2 border-white" style={{ background: "#eb6834" }} />
                <span className="truncate">{String(u.properties.nombre)}</span>
              </button>
            </li>
          ))}
        </ul>
        {pendientes.length > 0 && (
          <div className="mt-3 border-t border-line pt-3">
            <p className="mb-1.5 text-[11.5px] text-ink-3">
              {t(`Sin geometría todavía (${pendientes.length}): no se dibujan posiciones inventadas.`, `No geometry yet (${pendientes.length}): no invented positions are drawn.`)}
            </p>
            <div className="flex flex-wrap gap-1">
              {pendientes.map((u) => <Insignia key={u.id}>{String(u.properties.nombre).replace("Represa ", "")}</Insignia>)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
