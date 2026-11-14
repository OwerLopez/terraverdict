import { Compass } from "lucide-react";
import { lazy, Suspense } from "react";
import { Link, Route, Routes } from "react-router-dom";
import { Marco } from "./componentes/Marco";
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

function NoEncontrada() {
  return (
    <EstadoVacio icono={Compass} titulo="Esta página no existe" acciones={<Link to="/" className="text-accent-ink hover:underline">Volver al panel</Link>}>
      Revise la dirección o use la navegación lateral.
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
