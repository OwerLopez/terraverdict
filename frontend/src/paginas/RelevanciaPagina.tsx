import { useState } from "react";
import { Clock } from "lucide-react";
import { useCatalogoMetricas, useMapasMetricas, useMatriz } from "../api/consultas";
import type { Esquemas } from "../api/cliente";
import { MapaCalor } from "../componentes/graficos/MapaCalor";
import { Encabezado, Esqueleto, ErrorCarga, Insignia, Segmentado, Tarjeta } from "../componentes/ui";
import { textoViabilidad } from "../lib/formato";
import { t } from "../lib/i18n";
import { ImportanciaVariables } from "../componentes/metricas/compartidos";

type Matriz = Esquemas["MatrizRelevancia"];
type Vista = "validados" | "todos";

/**
 * Separa los problemas con resultados validados de los que todavía no tienen datos. Nada se rellena:
 * la vista "validados" solo quita filas y columnas sin celdas publicadas; "todos" muestra la matriz completa.
 */
export function particionar(matriz: Matriz): { conResultados: Matriz["problemas"]; enEspera: Matriz["problemas"] } {
  const conCeldas = new Set(matriz.celdas.map((c) => c.problema_id));
  return {
    conResultados: matriz.problemas.filter((p) => conCeldas.has(p.id)),
    enEspera: matriz.problemas.filter((p) => !conCeldas.has(p.id)),
  };
}

export function soloValidados(matriz: Matriz): Matriz {
  const { conResultados } = particionar(matriz);
  const ids = new Set(conResultados.map((p) => p.id));
  const variables = new Set(matriz.celdas.filter((c) => ids.has(c.problema_id)).map((c) => c.variable_id));
  const candidatas = new Set(conResultados.flatMap((p) => p.candidatas));
  return {
    ...matriz,
    problemas: conResultados,
    variables: matriz.variables.filter((v) => variables.has(v.id) || candidatas.has(v.id)),
    celdas: matriz.celdas.filter((c) => ids.has(c.problema_id)),
  };
}

export function RelevanciaPagina() {
  const matriz = useMatriz();
  const mapas = useMapasMetricas();
  const catalogo = useCatalogoMetricas();
  const fichaImportancia = catalogo.data?.metricas.find((m) => m.id === "importancia_permutacion");
  const [vista, setVista] = useState<Vista>("validados");
  const particion = matriz.data ? particionar(matriz.data) : null;
  const hayValidados = (particion?.conResultados.length ?? 0) > 0;
  const mostrada = matriz.data && vista === "validados" && hayValidados ? soloValidados(matriz.data) : matriz.data;
  const nombresValidados = particion?.conResultados.map((p) => `${p.id}: ${p.nombre}`).join(" · ");
  const idsEspera = particion?.enEspera.map((p) => p.id) ?? [];

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
        acciones={
          matriz.data && (
            <div className="flex flex-wrap items-center gap-2">
              {hayValidados && (
                <Segmentado<Vista>
                  etiqueta={t("Problemas mostrados", "Problems shown")}
                  valor={vista}
                  alCambiar={setVista}
                  opciones={[
                    { valor: "validados", texto: t(`${nombresValidados} (validado)`, `${nombresValidados} (validated)`) },
                    { valor: "todos", texto: t("Todos los problemas", "All problems") },
                  ]}
                />
              )}
              {idsEspera.length > 0 && (
                <Insignia tono="warning" icono={Clock}>
                  {t(`${idsEspera.join(", ")} en espera de convenio de datos locales`, `${idsEspera.join(", ")} awaiting local data agreements`)}
                </Insignia>
              )}
              {!hayValidados && <Insignia tono="neutral">{t("Sin resultados", "No results")}</Insignia>}
            </div>
          )
        }
        pie={t("Método: plantillas por problema, validación por bloques, importancia por permutación, estabilidad con remuestreos, nulo barajado y FDR (docs/modulo-relevancia.md).", "Method: per-problem templates, block validation, permutation importance, resampling stability, shuffled null and FDR (docs/modulo-relevancia.md).")}
      >
        {matriz.isLoading ? <Esqueleto className="h-80" /> : matriz.error ? <ErrorCarga error={matriz.error} /> : mostrada && <MapaCalor matriz={mostrada} />}
      </Tarjeta>
      {matriz.data && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {matriz.data.problemas.map((p) => {
            const espera = idsEspera.includes(p.id);
            return (
              <div key={p.id} className="rounded-2xl border border-line bg-surface p-4 shadow-tarjeta">
                <div className="flex items-center justify-between gap-2">
                  <p className="font-mono text-[11px] text-ink-3">{p.id} · {t("entrena en", "trains on")} {p.dominio_entrenamiento}</p>
                  <Insignia tono={espera ? "warning" : "good"}>{espera ? t("En espera de datos", "Awaiting data") : t("Validado", "Validated")}</Insignia>
                </div>
                <p className="mt-1 font-semibold text-ink">{p.nombre}</p>
                <p className="mt-1 text-[12.5px] text-ink-2">{p.objetivo}</p>
                <p className="mt-2 text-[12px] text-ink-3">{t("Muestras", "Samples")}: {p.muestras} · {t("viabilidad", "feasibility")} {textoViabilidad(p.viabilidad)}</p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
