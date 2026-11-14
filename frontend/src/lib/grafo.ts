/** Distribución en capas (orden topológico) de los pasos de una procedencia. */

export interface PasoGrafo {
  id: string;
  nombre: string;
  entradas?: string[];
}

export interface NodoUbicado<T extends PasoGrafo> {
  paso: T;
  capa: number;
  fila: number;
}

export interface Arista {
  desde: string;
  hasta: string;
}

export function aristas(pasos: PasoGrafo[]): Arista[] {
  const ids = new Set(pasos.map((p) => p.id));
  return pasos.flatMap((p) =>
    (p.entradas ?? [])
      .filter((e) => e.startsWith("paso:") && ids.has(e.slice(5)))
      .map((e) => ({ desde: e.slice(5), hasta: p.id })),
  );
}

/**
 * Capa de un paso = 1 + capa máxima de sus entradas (0 si no tiene).
 * Los pasos sin entradas explícitas después de la primera capa se encadenan al anterior
 * en el orden declarado, para que el recorrido se lea de izquierda a derecha.
 */
export function ubicar<T extends PasoGrafo>(pasos: T[]): { nodos: NodoUbicado<T>[]; aristas: Arista[]; capas: number } {
  const lista = aristas(pasos);
  const capa = new Map<string, number>();
  const porId = new Map(pasos.map((p) => [p.id, p]));
  const visitando = new Set<string>();

  const calcular = (id: string): number => {
    const conocida = capa.get(id);
    if (conocida !== undefined) return conocida;
    if (visitando.has(id)) return 0; // defensa ante ciclos: la API ya los rechaza
    visitando.add(id);
    const entradas = lista.filter((a) => a.hasta === id).map((a) => calcular(a.desde));
    const valor = entradas.length ? Math.max(...entradas) + 1 : 0;
    visitando.delete(id);
    capa.set(id, valor);
    return valor;
  };
  pasos.forEach((p) => calcular(p.id));

  const filas = new Map<number, number>();
  const nodos = pasos.map((p) => {
    const c = capa.get(p.id) ?? 0;
    const fila = filas.get(c) ?? 0;
    filas.set(c, fila + 1);
    return { paso: porId.get(p.id) as T, capa: c, fila };
  });
  return { nodos, aristas: lista, capas: Math.max(0, ...nodos.map((n) => n.capa)) + 1 };
}
