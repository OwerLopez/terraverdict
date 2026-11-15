import { Compass } from "lucide-react";
import { lazy, Suspense } from "react";
import { Link, Route, Routes } from "react-router-dom";
import { Marco } from "./componentes/Marco";
import { t } from "./lib/i18n";
import { Esqueleto, EstadoVacio } from "./componentes/ui";
import { AsistentePagina } from "./paginas/AsistentePagina";
import { EventosPagina } from "./paginas/EventosPagina";
import { ExpedientesPagina } from "./paginas/ExpedientesPagina";
import { FuentesPagina } from "./paginas/FuentesPagina";
import { Panel } from "./paginas/Panel";
import { ProcesosPagina } from "./paginas/ProcesosPagina";
import { RelevanciaPagina } from "./paginas/RelevanciaPagina";
import { SeriesPagina } from "./paginas/SeriesPagina";

// El mapa (MapLibre + WebGL) se carga solo cuando se visita.
const MapaPagina = lazy(() => import("./paginas/MapaPagina").then((m) => ({ default: m.MapaPagina })));
const SismosPagina = lazy(() => import("./paginas/SismosPagina").then((m) => ({ default: m.SismosPagina })));
const VolcanesPagina = lazy(() => import("./paginas/VolcanesPagina").then((m) => ({ default: m.VolcanesPagina })));
const FenomenosPagina = lazy(() => import("./paginas/FenomenosPagina").then((m) => ({ default: m.FenomenosPagina })));
const CaosPagina = lazy(() => import("./paginas/CaosPagina").then((m) => ({ default: m.CaosPagina })));
const NacionalPagina = lazy(() => import("./paginas/NacionalPagina").then((m) => ({ default: m.NacionalPagina })));
const ModelosPagina = lazy(() => import("./paginas/ModelosPagina").then((m) => ({ default: m.ModelosPagina })));

function NoEncontrada() {
  return (
    <EstadoVacio icono={Compass} titulo={t("Esta página no existe", "This page does not exist")} acciones={<Link to="/" className="text-accent-ink hover:underline">{t("Volver al panel", "Back to dashboard")}</Link>}>
      {t("Revise la dirección o use la navegación lateral.", "Check the address or use the side navigation.")}
    </EstadoVacio>
  );
}

export function App() {
  return (
    <Marco>
      <Suspense fallback={<Esqueleto className="m-6 h-[60vh]" />}>
        <Routes>
          <Route path="/" element={<Panel />} />
          <Route path="/mapa" element={<MapaPagina />} />
          <Route path="/series" element={<SeriesPagina />} />
          <Route path="/expedientes" element={<ExpedientesPagina />} />
          <Route path="/expedientes/:id" element={<ExpedientesPagina />} />
          <Route path="/peru" element={<NacionalPagina />} />
          <Route path="/fenomenos" element={<FenomenosPagina />} />
          <Route path="/sismos" element={<SismosPagina />} />
          <Route path="/volcanes" element={<VolcanesPagina />} />
          <Route path="/caos" element={<CaosPagina />} />
          <Route path="/modelos" element={<ModelosPagina />} />
          <Route path="/relevancia" element={<RelevanciaPagina />} />
          <Route path="/procesos" element={<ProcesosPagina />} />
          <Route path="/fuentes" element={<FuentesPagina />} />
          <Route path="/eventos" element={<EventosPagina />} />
          <Route path="/asistente" element={<AsistentePagina />} />
          <Route path="*" element={<NoEncontrada />} />
        </Routes>
      </Suspense>
    </Marco>
  );
}
