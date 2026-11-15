/** Consultas de datos con TanStack Query. Cada hook consume un endpoint del contrato. */
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, pedir, type Esquemas } from "./cliente";

const MINUTO = 60_000;

export const useResumen = () =>
  useQuery({
    queryKey: ["resumen"],
    queryFn: () => pedir(api.GET("/api/v1/resumen")),
    refetchInterval: 30_000,
  });

export const useSalud = () =>
  useQuery({
    queryKey: ["salud"],
    queryFn: () => pedir(api.GET("/api/v1/salud/lista")),
    refetchInterval: 20_000,
    retry: false,
  });

export const useFuentes = () =>
  useQuery({ queryKey: ["fuentes"], queryFn: () => pedir(api.GET("/api/v1/fuentes")), staleTime: 5 * MINUTO });

export const useVariables = () =>
  useQuery({ queryKey: ["variables"], queryFn: () => pedir(api.GET("/api/v1/variables")), staleTime: 10 * MINUTO });

export const useUnidadesMedida = () =>
  useQuery({
    queryKey: ["unidades-medida"],
    queryFn: () => pedir(api.GET("/api/v1/unidades-medida")),
    staleTime: Infinity,
  });

export const useEventos = () =>
  useQuery({ queryKey: ["eventos"], queryFn: () => pedir(api.GET("/api/v1/eventos")), staleTime: 5 * MINUTO });

export const useVerificacion = () =>
  useQuery({ queryKey: ["verificacion"], queryFn: () => pedir(api.GET("/api/v1/verificacion")), staleTime: 5 * MINUTO });

export const useDominios = () =>
  useQuery({ queryKey: ["dominios"], queryFn: () => pedir(api.GET("/api/v1/dominios")), staleTime: 10 * MINUTO });

export const useUnidadesGeo = (dominioId: string) =>
  useQuery({
    queryKey: ["unidades-geo", dominioId],
    queryFn: () =>
      pedir(api.GET("/api/v1/dominios/{dominio_id}/unidades", { params: { path: { dominio_id: dominioId } } })),
    staleTime: 5 * MINUTO,
  });

export const useSeries = (filtros: { variable_id?: string; unidad_id?: string } = {}) =>
  useQuery({
    queryKey: ["series", filtros],
    queryFn: () => pedir(api.GET("/api/v1/series", { params: { query: { limite: 500, ...filtros } } })),
    placeholderData: keepPreviousData,
  });

export const useObservaciones = (serieId: string | undefined) =>
  useQuery({
    queryKey: ["observaciones", serieId],
    enabled: Boolean(serieId),
    queryFn: () =>
      pedir(
        api.GET("/api/v1/series/{serie_id}/observaciones", {
          params: { path: { serie_id: serieId ?? "" } },
        }),
      ),
  });

export const useExpedientes = (filtros: { tipo?: Esquemas["ExpedienteResumen"]["tipo"]; serie_id?: string } = {}) =>
  useQuery({
    queryKey: ["expedientes", filtros],
    queryFn: () => pedir(api.GET("/api/v1/expedientes", { params: { query: { limite: 200, ...filtros } } })),
  });

export const useExpediente = (id: string | undefined) =>
  useQuery({
    queryKey: ["expediente", id],
    enabled: Boolean(id),
    queryFn: () =>
      pedir(api.GET("/api/v1/expedientes/{expediente_id}", { params: { path: { expediente_id: id ?? "" } } })),
  });

export const useMatriz = () =>
  useQuery({ queryKey: ["matriz"], queryFn: () => pedir(api.GET("/api/v1/relevancia/matriz")) });

export const useProcesos = () =>
  useQuery({
    queryKey: ["procesos"],
    queryFn: () => pedir(api.GET("/api/v1/procesos", { params: { query: { limite: 100 } } })),
    refetchInterval: 5_000,
  });

export const useEventosProceso = (id: string | undefined, activo: boolean) =>
  useQuery({
    queryKey: ["eventos-proceso", id],
    enabled: Boolean(id),
    refetchInterval: activo ? 3_000 : false,
    queryFn: () =>
      pedir(api.GET("/api/v1/procesos/{proceso_id}/eventos", { params: { path: { proceso_id: id ?? "" } } })),
  });

export function useSolicitarProceso() {
  const cliente = useQueryClient();
  return useMutation({
    mutationFn: (cuerpo: Esquemas["ProcesoCrear"]) => pedir(api.POST("/api/v1/procesos", { body: cuerpo })),
    onSuccess: () => cliente.invalidateQueries({ queryKey: ["procesos"] }),
  });
}

export function useCancelarProceso() {
  const cliente = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      pedir(
        api.PATCH("/api/v1/procesos/{proceso_id}", {
          params: { path: { proceso_id: id } },
          body: { estado: "cancelado" },
        }),
      ),
    onSuccess: () => cliente.invalidateQueries({ queryKey: ["procesos"] }),
  });
}

export function useVerificarTexto() {
  return useMutation({
    mutationFn: (cuerpo: Esquemas["SolicitudVerificacion"]) =>
      pedir(api.POST("/api/v1/asistente/verificar", { body: cuerpo })),
  });
}

export function useConsultarAsistente() {
  return useMutation({
    mutationFn: (cuerpo: Esquemas["ConsultaAsistente"]) =>
      pedir(api.POST("/api/v1/asistente/consultas", { body: cuerpo })),
  });
}

export const useFenomenos = () =>
  useQuery({ queryKey: ["fenomenos"], queryFn: () => pedir(api.GET("/api/v1/fenomenos")), staleTime: 10 * MINUTO });

export const useCapaSismos = (magnitudMin: number) =>
  useQuery({
    queryKey: ["capa-sismos", magnitudMin],
    queryFn: () => pedir(api.GET("/api/v1/capas/sismos", { params: { query: { magnitud_min: magnitudMin } } })),
    placeholderData: keepPreviousData,
  });

export const useCapaVolcanes = () =>
  useQuery({ queryKey: ["capa-volcanes"], queryFn: () => pedir(api.GET("/api/v1/capas/volcanes")) });

/** Expediente vigente más reciente de un tipo (o el elegido por ID), con su detalle completo. */
export function useExpedienteVigente(tipo: Esquemas["ExpedienteResumen"]["tipo"], id?: string) {
  const lista = useExpedientes({ tipo });
  const elegido = id ?? lista.data?.items[0]?.id;
  const detalle = useExpediente(elegido);
  return { lista, detalle, elegido };
}

/** Panorama nacional vigente (25 departamentos con el mismo motor). */
export const useNacional = () =>
  useQuery({ queryKey: ["nacional"], queryFn: () => pedir(api.GET("/api/v1/nacional")), staleTime: 10 * MINUTO });

export const useCatalogoMetricas = () =>
  useQuery({ queryKey: ["metricas"], queryFn: () => pedir(api.GET("/api/v1/metricas")), staleTime: 30 * MINUTO });

export const useMapasMetricas = () =>
  useQuery({ queryKey: ["metricas", "mapas"], queryFn: () => pedir(api.GET("/api/v1/metricas/mapas")), staleTime: 5 * MINUTO });

export const useHistorial = () =>
  useQuery({ queryKey: ["historial"], queryFn: () => pedir(api.GET("/api/v1/historial")), staleTime: 5 * MINUTO });
