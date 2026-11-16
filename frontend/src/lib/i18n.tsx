import { useQueryClient } from "@tanstack/react-query";
/**
 * Internacionalización español / inglés.
 *
 * Cada texto de la interfaz se escribe con sus dos versiones juntas: `t("Expedientes", "Case files")`.
 * Así ninguna cadena puede quedar sin traducir (la prueba `i18n.test.ts` lo comprueba en todo `src/`).
 * Los datos de las fuentes (títulos de eventos, citas, nombres oficiales) se muestran en su idioma
 * original: traducirlos sería alterar la evidencia citada.
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type Idioma = "es" | "en";
const CLAVE = "terraverdict.idioma";

function inicial(): Idioma {
  try {
    const guardado = localStorage.getItem(CLAVE);
    if (guardado === "es" || guardado === "en") return guardado;
  } catch {
    /* almacenamiento no disponible: se usa el idioma principal */
  }
  // Inglés es el idioma principal (evaluación internacional); el español se elige con el selector y se recuerda.
  return "en";
}

let actual: Idioma = inicial();

/** Idioma vigente (para funciones de formato fuera de React). */
export function idiomaActual(): Idioma {
  return actual;
}

/** Cambia el idioma fuera de React (pruebas y utilidades); en la interfaz se usa `useIdioma().cambiar`. */
export function fijarIdioma(i: Idioma): void {
  actual = i;
}

/** Texto en el idioma vigente. */
export function t(es: string, en: string): string {
  return actual === "en" ? en : es;
}

/** Locale de Intl: "es" usa coma decimal (como el verificador numérico); "en" usa punto. */
export function locale(): string {
  return actual === "en" ? "en" : "es";
}

const Contexto = createContext<{ idioma: Idioma; cambiar: (i: Idioma) => void }>({ idioma: actual, cambiar: () => {} });

export function ProveedorIdioma({ children }: { children: ReactNode }) {
  const [idioma, setIdioma] = useState<Idioma>(actual);
  const consultas = useQueryClient();
  const cambiar = useCallback((i: Idioma) => {
    actual = i;
    // Los datos se traducen al recibirlos: al cambiar de idioma se vuelven a pedir.
    consultas.removeQueries();
    try {
      localStorage.setItem(CLAVE, i);
    } catch {
      /* sin persistencia: el cambio vale para esta visita */
    }
    setIdioma(i);
  }, [consultas]);
  useEffect(() => {
    document.documentElement.lang = idioma;
  }, [idioma]);
  const valor = useMemo(() => ({ idioma, cambiar }), [idioma, cambiar]);
  // `key` vuelve a montar el árbol: todas las llamadas a t() se reevalúan con el idioma nuevo.
  return (
    <Contexto.Provider value={valor}>
      <div key={idioma} className="contents">
        {children}
      </div>
    </Contexto.Provider>
  );
}

export function useIdioma() {
  return useContext(Contexto);
}
