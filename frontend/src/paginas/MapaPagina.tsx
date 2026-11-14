import { useDominios, useUnidadesGeo } from "../api/consultas";
import { MapaSatelital } from "../componentes/mapa/MapaSatelital";
import { ErrorCarga } from "../componentes/ui";

export function MapaPagina() {
  const dominios = useDominios();
  const unidades = useUnidadesGeo("chili_analisis");
  const dominio = dominios.data?.find((d) => d.id === "chili_analisis");
  if (dominios.error) return <div className="p-6"><ErrorCarga error={dominios.error} /></div>;
  return <MapaSatelital dominio={dominio} unidades={unidades.data?.features ?? []} />;
}
