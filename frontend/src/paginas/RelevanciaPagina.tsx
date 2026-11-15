import { useCatalogoMetricas, useMapasMetricas, useMatriz } from "../api/consultas";
import { MapaCalor } from "../componentes/graficos/MapaCalor";
import { Encabezado, Esqueleto, ErrorCarga, Insignia, Tarjeta } from "../componentes/ui";
import { t } from "../lib/i18n";
import { ImportanciaVariables } from "../componentes/metricas/compartidos";

export function RelevanciaPagina() {
  const matriz = useMatriz();
  const mapas = useMapasMetricas();
  const catalogo = useCatalogoMetricas();
  const fichaImportancia = catalogo.data?.metricas.find((m) => m.id === "importancia_permutacion");
  return (
    <div className="space-y-6">
      <Encabezado
        eyebrow={t("Módulo M1", "Module M1")}
        titulo={t("Matriz de relevancia", "Relevance matrix")}
        descripcion={t("Para cada problema, qué variables importan, en qué dirección y con cuánta confianza. Cada celda proviene de un expediente validado fuera de muestra; si no hay resultado, la celda queda vacía en lugar de inventarse.", "For each problem, which variables matter, in which direction and with how much confidence. Every cell comes from an out-of-sample validated case file; without a result the cell stays empty instead of being invented.")}
      />
      {mapas.data && <ImportanciaVariables mapas={mapas.data} ficha={fichaImportancia} />}
      <Tarjeta
        titulo={t("Problema × variable", "Problem × variable")}
        acciones={matriz.data && <Insignia tono={matriz.data.estado === "vacia" ? "neutral" : "good"}>{matriz.data.estado === "vacia" ? t("Sin resultados", "No results") : t("Con resultados", "With results")}</Insignia>}
        pie={t("Método: plantillas por problema, validación por bloques, importancia por permutación, estabilidad con remuestreos, nulo barajado y FDR (docs/modulo-relevancia.md).", "Method: per-problem templates, block validation, permutation importance, resampling stability, shuffled null and FDR (docs/modulo-relevancia.md).")}
      >
        {matriz.isLoading ? <Esqueleto className="h-80" /> : matriz.error ? <ErrorCarga error={matriz.error} /> : matriz.data && <MapaCalor matriz={matriz.data} />}
      </Tarjeta>
      {matriz.data && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {matriz.data.problemas.map((p) => (
            <div key={p.id} className="rounded-2xl border border-line bg-surface p-4 shadow-tarjeta">
              <p className="font-mono text-[11px] text-ink-3">{p.id} · {t("entrena en", "trains on")} {p.dominio_entrenamiento}</p>
              <p className="mt-1 font-semibold text-ink">{p.nombre}</p>
              <p className="mt-1 text-[12.5px] text-ink-2">{p.objetivo}</p>
              <p className="mt-2 text-[12px] text-ink-3">{t("Muestras", "Samples")}: {p.muestras} · {t("viabilidad", "feasibility")} {p.viabilidad}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
