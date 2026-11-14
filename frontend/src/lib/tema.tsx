import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type Tema = "sistema" | "light" | "dark";

interface ContextoTema {
  tema: Tema;
  oscuro: boolean;
  cambiar: (t: Tema) => void;
}

const Contexto = createContext<ContextoTema | null>(null);

function leer(): Tema {
  try {
    const t = localStorage.getItem("tv-tema");
    return t === "light" || t === "dark" ? t : "sistema";
  } catch {
    return "sistema";
  }
}

export function ProveedorTema({ children }: { children: ReactNode }) {
  const [tema, setTema] = useState<Tema>(leer);
  const [sistemaOscuro, setSistemaOscuro] = useState(
    () => typeof window !== "undefined" && window.matchMedia?.("(prefers-color-scheme: dark)").matches,
  );

  useEffect(() => {
    const mq = window.matchMedia?.("(prefers-color-scheme: dark)");
    const alCambiar = (e: MediaQueryListEvent) => setSistemaOscuro(e.matches);
    mq?.addEventListener("change", alCambiar);
    return () => mq?.removeEventListener("change", alCambiar);
  }, []);

  const cambiar = useCallback((t: Tema) => {
    setTema(t);
    try {
      if (t === "sistema") localStorage.removeItem("tv-tema");
      else localStorage.setItem("tv-tema", t);
    } catch {
      /* preferencia solo en memoria */
    }
    if (t === "sistema") delete document.documentElement.dataset.theme;
    else document.documentElement.dataset.theme = t;
  }, []);

  const valor = useMemo(
    () => ({ tema, cambiar, oscuro: tema === "dark" || (tema === "sistema" && sistemaOscuro) }),
    [tema, cambiar, sistemaOscuro],
  );
  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}

export function useTema(): ContextoTema {
  const c = useContext(Contexto);
  if (!c) throw new Error("useTema debe usarse dentro de ProveedorTema");
  return c;
}

/** Lee un token de color CSS (cambia con el tema). */
export function colorToken(nombre: string): string {
  if (typeof window === "undefined") return "";
  return getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();
}
