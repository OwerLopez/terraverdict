import { clsx } from "clsx";
import { Crosshair, Layers, Mountain, MapPin, Satellite } from "lucide-react";
import maplibregl, { type Map as MapaML, type StyleSpecification } from "maplibre-gl";
import { useEffect, useMemo, useRef, useState } from "react";
import type { Esquemas } from "../../api/cliente";
import { Insignia } from "../ui";

const GIBS = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best";

/** Capas de NASA GIBS verificadas el 2026-11-14 (plantilla REST, EPSG:3857). */
export const CAPAS = [
  { id: "MODIS_Terra_CorrectedReflectance_TrueColor", nombre: "MODIS Terra · color real", resolucion: "250 m", nivel: 9, ext: "jpg", fecha: true },
  { id: "MODIS_Aqua_CorrectedReflectance_TrueColor", nombre: "MODIS Aqua · color real", resolucion: "250 m", nivel: 9, ext: "jpg", fecha: true },
  { id: "VIIRS_NOAA20_CorrectedReflectance_TrueColor", nombre: "VIIRS NOAA-20 · color real", resolucion: "375 m", nivel: 9, ext: "jpg", fecha: true },
  { id: "HLS_S30_Nadir_BRDF_Adjusted_Reflectance", nombre: "HLS Sentinel-2 · 30 m", resolucion: "30 m", nivel: 12, ext: "png", fecha: true },
  { id: "HLS_L30_Nadir_BRDF_Adjusted_Reflectance", nombre: "HLS Landsat · 30 m", resolucion: "30 m", nivel: 12, ext: "png", fecha: true },
] as const;

type CapaId = (typeof CAPAS)[number]["id"];

export function urlCapa(id: CapaId, fecha: string): string {
  const capa = CAPAS.find((c) => c.id === id) ?? CAPAS[0];
  return `${GIBS}/${capa.id}/default/${fecha}/GoogleMapsCompatible_Level${capa.nivel}/{z}/{y}/{x}.${capa.ext}`;
}

function haceDias(n: number): string {
  const d = new Date(Date.now() - n * 86_400_000);
  return d.toISOString().slice(0, 10);
}

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
  const [capa, setCapa] = useState<CapaId>("MODIS_Terra_CorrectedReflectance_TrueColor");
  const [fecha, setFecha] = useState(haceDias(2));
  const [tresD, setTresD] = useState(true);
  const [exageracion, setExageracion] = useState(1.6);

  const bbox = dominio?.bbox;
  const conGeometria = useMemo(() => unidades.filter((u) => u.geometry?.type === "Point"), [unidades]);
  const pendientes = useMemo(() => unidades.filter((u) => !u.geometry), [unidades]);

  useEffect(() => {
    if (!contenedor.current || mapa.current) return;
    const capaInicial = CAPAS[0];
    const estilo: StyleSpecification = {
      version: 8,
      sources: {
        fondo: {
          type: "raster",
          tiles: [`${GIBS}/BlueMarble_ShadedRelief_Bathymetry/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg`],
          tileSize: 256,
          maxzoom: 8,
          attribution: "Imágenes: NASA GIBS / ESDIS",
        },
        diaria: { type: "raster", tiles: [urlCapa(capaInicial.id, fecha)], tileSize: 256, maxzoom: capaInicial.nivel },
        relieve: {
          type: "raster-dem",
          tiles: ["https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"],
          encoding: "terrarium",
          tileSize: 256,
          maxzoom: 13,
          attribution: "Relieve: AWS Terrain Tiles",
        },
        sombras: {
          type: "raster-dem",
          tiles: ["https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"],
          encoding: "terrarium",
          tileSize: 256,
          maxzoom: 13,
        },
        dominio: { type: "geojson", data: { type: "FeatureCollection", features: [] } },
      },
      layers: [
        { id: "fondo", type: "raster", source: "fondo" },
        { id: "diaria", type: "raster", source: "diaria", paint: { "raster-fade-duration": 200 } },
        { id: "sombras", type: "hillshade", source: "sombras", paint: { "hillshade-exaggeration": 0.3, "hillshade-shadow-color": "#000000" } },
        { id: "dominio-relleno", type: "fill", source: "dominio", paint: { "fill-color": "#3987e5", "fill-opacity": 0.05 } },
        { id: "dominio-borde", type: "line", source: "dominio", paint: { "line-color": "#86b6ef", "line-width": 1.6, "line-dasharray": [3, 2] } },
      ],
    };
    try {
      const m = new maplibregl.Map({
        container: contenedor.current,
        style: estilo,
        center: [-71.35, -16.0],
        zoom: 8.2,
        pitch: 58,
        bearing: -18,
        maxPitch: 80,
        attributionControl: { compact: true },
      });
      m.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");
      m.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-right");
      m.on("load", () => setListo(true));
      m.on("error", (e) => {
        const msg = e.error?.message ?? "";
        if (msg.includes("WebGL")) setError("Su navegador no soporta WebGL: el mapa 3D no puede mostrarse.");
      });
      mapa.current = m;
    } catch {
      setError("No se pudo iniciar el mapa (WebGL no disponible).");
    }
    return () => {
      mapa.current?.remove();
      mapa.current = null;
    };
    // El mapa se crea una sola vez; los cambios se aplican en los efectos siguientes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Capa diaria: se recrea la fuente para respetar el nivel máximo de cada producto.
  useEffect(() => {
    const m = mapa.current;
    if (!m || !listo) return;
    const def = CAPAS.find((c) => c.id === capa) ?? CAPAS[0];
    if (m.getLayer("diaria")) m.removeLayer("diaria");
    if (m.getSource("diaria")) m.removeSource("diaria");
    m.addSource("diaria", { type: "raster", tiles: [urlCapa(def.id, fecha)], tileSize: 256, maxzoom: def.nivel });
    m.addLayer({ id: "diaria", type: "raster", source: "diaria", paint: { "raster-fade-duration": 200 } }, "sombras");
  }, [capa, fecha, listo]);

  useEffect(() => {
    const m = mapa.current;
    if (!m || !listo) return;
    m.setTerrain(tresD ? { source: "relieve", exaggeration: exageracion } : null);
    m.easeTo({ pitch: tresD ? 58 : 0, duration: 600 });
  }, [tresD, exageracion, listo]);

  useEffect(() => {
    const m = mapa.current;
    if (!m || !listo || !bbox) return;
    const fuente = m.getSource("dominio") as maplibregl.GeoJSONSource | undefined;
    fuente?.setData({ type: "FeatureCollection", features: [poligonoBbox(bbox)] });
  }, [bbox, listo]);

  useEffect(() => {
    const m = mapa.current;
    if (!m || !listo) return;
    const marcadores = conGeometria.map((u) => {
      const el = document.createElement("div");
      el.className = "tv-marcador";
      el.style.cssText =
        "width:14px;height:14px;border-radius:999px;background:#eb6834;border:2px solid #fff;box-shadow:0 0 0 4px rgba(235,104,52,.25);cursor:pointer";
      el.setAttribute("aria-label", String(u.properties.nombre ?? u.id));
      const contenido = document.createElement("div");
      contenido.style.cssText = "font:12px system-ui;color:#0b0b0b;max-width:220px";
      const titulo = document.createElement("strong");
      titulo.textContent = String(u.properties.nombre ?? u.id);
      const detalle = document.createElement("div");
      detalle.style.color = "#52514e";
      detalle.textContent = `${u.properties.tipo} · geometría ${u.properties.estado_geometria}`;
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
    mapa.current.fitBounds([[x1, y1], [x2, y2]], { padding: 60, pitch: tresD ? 58 : 0, bearing: -18, duration: 1200 });
  };

  return (
    <div className="relative h-full w-full overflow-hidden bg-[#0d0d0d]">
      <div ref={contenedor} className="absolute inset-0" aria-label="Mapa satelital de la cuenca del Chili" role="region" />
      {error && (
        <div className="absolute inset-0 grid place-items-center p-6 text-center text-sm text-white/80">{error}</div>
      )}

      <div className="vidrio absolute left-3 top-3 w-[min(92vw,300px)] rounded-2xl border border-line p-4 shadow-flotante md:left-5 md:top-5">
        <p className="etiqueta mb-2 flex items-center gap-1.5"><Layers className="h-3.5 w-3.5" /> Capa satelital</p>
        <div className="space-y-1" role="radiogroup" aria-label="Capa satelital">
          {CAPAS.map((c) => (
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
              <span className="flex items-center gap-2"><Satellite className="h-3.5 w-3.5" />{c.nombre}</span>
              <span className="cifra text-[11px] text-ink-3">{c.resolucion}</span>
            </button>
          ))}
        </div>
        <label className="mt-3 block text-[12px] text-ink-2">
          Fecha de la imagen
          <input
            type="date"
            value={fecha}
            max={haceDias(0)}
            min="2000-02-24"
            onChange={(e) => e.target.value && setFecha(e.target.value)}
            className="mt-1 h-9 w-full rounded-lg border border-line bg-surface px-2.5 text-[13px] text-ink"
          />
        </label>
        <p className="mt-1.5 text-[11px] leading-snug text-ink-3">
          Imagen diaria real de NASA GIBS. Las nubes y los días sin pasada se ven tal cual: no se rellenan.
        </p>
        <div className="mt-3 flex items-center justify-between border-t border-line pt-3">
          <label className="flex items-center gap-2 text-[12.5px] font-medium text-ink">
            <input type="checkbox" checked={tresD} onChange={(e) => setTresD(e.target.checked)} className="accent-[var(--accent)]" />
            <Mountain className="h-3.5 w-3.5" /> Relieve 3D
          </label>
          <button type="button" onClick={volver} className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[12px] text-ink-2 hover:bg-surface-2 hover:text-ink">
            <Crosshair className="h-3.5 w-3.5" /> Cuenca
          </button>
        </div>
        {tresD && (
          <label className="mt-2 block text-[11.5px] text-ink-3">
            Exageración vertical: <span className="cifra font-medium text-ink-2">{exageracion.toFixed(1)}×</span>
            <input type="range" min={1} max={3} step={0.1} value={exageracion} onChange={(e) => setExageracion(Number(e.target.value))} className="mt-1 w-full accent-[var(--accent)]" />
          </label>
        )}
      </div>

      <div className="vidrio absolute bottom-10 left-3 hidden w-[300px] rounded-2xl border border-line p-4 shadow-flotante md:left-5 md:block">
        <p className="etiqueta mb-2 flex items-center gap-1.5"><MapPin className="h-3.5 w-3.5" /> Unidades de análisis</p>
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
              Sin geometría todavía ({pendientes.length}): se publicarán al delimitarlas (etapa E1). No se dibujan posiciones inventadas.
            </p>
            <div className="flex flex-wrap gap-1">
              {pendientes.map((u) => <Insignia key={u.id}>{String(u.properties.nombre).replace("Represa ", "")}</Insignia>)}
            </div>
          </div>
        )}
        <p className="mt-3 flex items-center gap-2 border-t border-line pt-3 text-[11.5px] text-ink-3">
          <span className="h-0 w-5 border-t-2 border-dashed border-[#86b6ef]" /> Caja aproximada del dominio (polígono oficial pendiente)
        </p>
      </div>
    </div>
  );
}
