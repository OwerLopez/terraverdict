import { useMatriz } from "../api/consultas";
import { MapaCalor } from "../componentes/graficos/MapaCalor";
import { Encabezado, Esqueleto, ErrorCarga, Insignia, Tarjeta } from "../componentes/ui";

export function RelevanciaPagina() {
  const matriz = useMatriz();
  return (
    <div className="space-y-6">
      <Encabezado
        eyebrow="Módulo M1"
        titulo="Matriz de relevancia"
        descripcion="Para cada problema, qué variables importan, en qué dirección y con cuánta confianza. Cada celda proviene de un expediente validado fuera de muestra; si no hay resultado, la celda queda vacía en lugar de inventarse."
      />
      <Tarjeta
        titulo="Problema × variable"
        acciones={matriz.data && <Insignia tono={matriz.data.estado === "vacia" ? "neutral" : "good"}>{matriz.data.estado === "vacia" ? "Sin resultados" : "Con resultados"}</Insignia>}
        pie="Método: plantillas por problema, validación por bloques, importancia por permutación, estabilidad con remuestreos, nulo barajado y FDR (docs/modulo-relevancia.md)."
      >
        {matriz.isLoading ? <Esqueleto className="h-80" /> : matriz.error ? <ErrorCarga error={matriz.error} /> : matriz.data && <MapaCalor matriz={matriz.data} />}
      </Tarjeta>
      {matriz.data && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {matriz.data.problemas.map((p) => (
            <div key={p.id} className="rounded-2xl border border-line bg-surface p-4 shadow-tarjeta">
              <p className="font-mono text-[11px] text-ink-3">{p.id} · entrena en {p.dominio_entrenamiento}</p>
              <p className="mt-1 font-semibold text-ink">{p.nombre}</p>
              <p className="mt-1 text-[12.5px] text-ink-2">{p.objetivo}</p>
              <p className="mt-2 text-[12px] text-ink-3">Muestras: {p.muestras} · viabilidad {p.viabilidad}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
