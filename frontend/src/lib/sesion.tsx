import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, useCallback, useContext, useMemo, type ReactNode } from "react";
import { api, ErrorApi, guardarToken, interpretarProblema, obtenerToken, pedir, type Esquemas } from "../api/cliente";

interface ContextoSesion {
  identidad: Esquemas["Identidad"] | null;
  cargando: boolean;
  iniciar: (email: string, contrasena: string) => Promise<void>;
  cerrar: () => void;
  puede: (rol: "lector" | "analista" | "admin") => boolean;
}

const RANGO = { lector: 1, analista: 2, admin: 3 } as const;
const Contexto = createContext<ContextoSesion | null>(null);

export function ProveedorSesion({ children }: { children: ReactNode }) {
  const cliente = useQueryClient();
  const consulta = useQuery({
    queryKey: ["identidad"],
    enabled: Boolean(obtenerToken()),
    retry: false,
    queryFn: async () => {
      try {
        return await pedir(api.GET("/api/v1/auth/yo"));
      } catch (e) {
        if (e instanceof ErrorApi && e.status === 401) guardarToken(null);
        throw e;
      }
    },
  });

  const iniciar = useCallback(
    async (email: string, contrasena: string) => {
      const cuerpo = new URLSearchParams({ username: email, password: contrasena });
      const r = await fetch(`${import.meta.env.VITE_API_URL ?? ""}/api/v1/auth/token`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: cuerpo,
      });
      const datos: unknown = await r.json().catch(() => null);
      if (!r.ok) throw interpretarProblema(r.status, datos);
      guardarToken((datos as Esquemas["Token"]).access_token);
      await cliente.invalidateQueries({ queryKey: ["identidad"] });
      await consulta.refetch();
    },
    [cliente, consulta],
  );

  const cerrar = useCallback(() => {
    guardarToken(null);
    cliente.setQueryData(["identidad"], null);
    cliente.removeQueries({ queryKey: ["identidad"] });
  }, [cliente]);

  const identidad = consulta.data ?? null;
  const valor = useMemo<ContextoSesion>(
    () => ({
      identidad,
      cargando: consulta.isFetching,
      iniciar,
      cerrar,
      puede: (rol) => Boolean(identidad?.rol && RANGO[identidad.rol] >= RANGO[rol]),
    }),
    [identidad, consulta.isFetching, iniciar, cerrar],
  );
  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}

export function useSesion(): ContextoSesion {
  const c = useContext(Contexto);
  if (!c) throw new Error("useSesion debe usarse dentro de ProveedorSesion");
  return c;
}
