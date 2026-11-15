import maplibregl, { type ExpressionSpecification, type Map as MapaML } from "maplibre-gl";
import { useEffect, useRef, useState } from "react";
import type { Esquemas } from "../../api/cliente";
import { t } from "../../lib/i18n";

const GIBS = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best";

/**
 * Puntos GeoJSON sobre el relieve de NASA GIBS. El color y el radio llegan como expresiones de
 * MapLibre (p. ej., profundidad → rampa azul, magnitud → radio). Cada punto es enfocable por
 * teclado a través de la tabla de datos de la página; el mapa es un complemento visual.
 */
export function MapaPuntos({
  puntos,
  color,
  radio,
  centro,
  zoom = 5.2,
  descripcion,
  etiqueta,
  alto = 420,
}: {
  puntos: Esquemas["Feature"][];
  color: ExpressionSpecification | string;
  radio: ExpressionSpecification | number;
  centro: [number, number];
  zoom?: number;
  descripcion: string;
  etiqueta: (p: Record<string, unknown>) => string;
  alto?: number;
}) {
  const contenedor = useRef<HTMLDivElement>(null);
  const mapa = useRef<MapaML | null>(null);
  const [listo, setListo] = useState(false);

  useEffect(() => {
    if (!contenedor.current || mapa.current) return;
    const m = new maplibregl.Map({
      container: contenedor.current,
      center: centro,
      zoom,
      attributionControl: { compact: true },
      style: {
        version: 8,
        sources: {
          fondo: {
            type: "raster",
            tiles: [`${GIBS}/BlueMarble_ShadedRelief_Bathymetry/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg`],
            tileSize: 256,
            maxzoom: 8,
            attribution: t("Imágenes: NASA GIBS / ESDIS", "Imagery: NASA GIBS / ESDIS"),
          },
        },
        layers: [{ id: "fondo", type: "raster", source: "fondo" }],
      },
    });
    m.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    m.on("load", () => setListo(true));
    mapa.current = m;
    return () => {
      m.remove();
      mapa.current = null;
    };
    // El mapa se crea una vez; centro y zoom iniciales no deben recrearlo.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const m = mapa.current;
    if (!m || !listo) return;
    const datos = { type: "FeatureCollection" as const, features: puntos as GeoJSON.Feature[] };
    const fuente = m.getSource("puntos") as maplibregl.GeoJSONSource | undefined;
    if (fuente) fuente.setData(datos);
    else {
      m.addSource("puntos", { type: "geojson", data: datos });
      m.addLayer({
        id: "puntos",
        type: "circle",
        source: "puntos",
        paint: {
          "circle-color": color,
          "circle-radius": radio,
          "circle-opacity": 0.85,
          "circle-stroke-color": "#ffffff",
          "circle-stroke-width": 1,
        },
      });
      const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 8 });
      m.on("mouseenter", "puntos", (e) => {
        m.getCanvas().style.cursor = "pointer";
        const f = e.features?.[0];
        if (!f) return;
        popup.setLngLat(e.lngLat).setText(etiqueta(f.properties ?? {})).addTo(m);
      });
      m.on("mouseleave", "puntos", () => {
        m.getCanvas().style.cursor = "";
        popup.remove();
      });
    }
  }, [puntos, listo, color, radio, etiqueta]);

  return (
    <div
      ref={contenedor}
      role="img"
      aria-label={descripcion}
      className="w-full overflow-hidden rounded-xl border border-line"
      style={{ height: alto }}
    />
  );
}
