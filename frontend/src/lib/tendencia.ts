/**
 * Recta de tendencia para dibujar una pendiente de Theil-Sen publicada en un expediente.
 * La pendiente viene del expediente (no se recalcula). El intercepto sigue la convención
 * de Sen: mediana de (y − b·t). La banda usa las pendientes del intervalo publicado,
 * pivotando en la mediana de los datos.
 */

export interface Punto {
  t: number; // año decimal
  y: number;
}

export function mediana(valores: number[]): number {
  if (valores.length === 0) return Number.NaN;
  const orden = [...valores].sort((a, b) => a - b);
  const medio = Math.floor(orden.length / 2);
  return orden.length % 2 ? (orden[medio] as number) : ((orden[medio - 1] as number) + (orden[medio] as number)) / 2;
}

export function anioDecimal(iso: string): number {
  const [a, m, d] = iso.slice(0, 10).split("-").map(Number);
  return (a ?? 0) + ((m ?? 1) - 1) / 12 + ((d ?? 1) - 1) / 365;
}

export interface Recta {
  pendientePorAnio: number;
  intercepto: number;
  pivote: Punto;
}

export function rectaSen(puntos: Punto[], pendientePorDecada: number): Recta {
  const b = pendientePorDecada / 10;
  const validos = puntos.filter((p) => Number.isFinite(p.y));
  const intercepto = mediana(validos.map((p) => p.y - b * p.t));
  const pivote = { t: mediana(validos.map((p) => p.t)), y: mediana(validos.map((p) => p.y)) };
  return { pendientePorAnio: b, intercepto, pivote };
}

export function evaluarRecta(r: Recta, t: number): number {
  return r.intercepto + r.pendientePorAnio * t;
}

/** Valores de la banda del intervalo en t: rectas con pendientes lo/hi que pasan por el pivote. */
export function banda(pivote: Punto, loPorDecada: number, hiPorDecada: number, t: number): [number, number] {
  const a = pivote.y + (loPorDecada / 10) * (t - pivote.t);
  const b = pivote.y + (hiPorDecada / 10) * (t - pivote.t);
  return a <= b ? [a, b] : [b, a];
}
