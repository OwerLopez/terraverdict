/**
 * Cliente HTTP tipado. Los tipos se generan desde docs/api/openapi.json
 * (`npm run api:tipos`): si el backend cambia el contrato, TypeScript lo detecta.
 */
import createClient from "openapi-fetch";
import glosario from "../lib/glosario-en.json";
import { idiomaActual } from "../lib/i18n";
import type { components, paths } from "./esquema";

export type Esquemas = components["schemas"];
export type Problema = Esquemas["ProblemaHTTP"];

const CLAVE_TOKEN = "tv-token";

export function obtenerToken(): string | null {
  try {
    return sessionStorage.getItem(CLAVE_TOKEN);
  } catch {
    return null;
  }
}

export function guardarToken(token: string | null): void {
  try {
    if (token) sessionStorage.setItem(CLAVE_TOKEN, token);
    else sessionStorage.removeItem(CLAVE_TOKEN);
  } catch {
    /* almacenamiento no disponible: la sesión dura lo que la pestaña */
  }
}

export const api = createClient<paths>({ baseUrl: import.meta.env.VITE_API_URL ?? "" });

api.use({
  onRequest({ request }) {
    const token = obtenerToken();
    if (token) request.headers.set("Authorization", `Bearer ${token}`);
    return request;
  },
});

/** Error de la API con el cuerpo RFC 9457 (problem+json) ya interpretado. */
export class ErrorApi extends Error {
  readonly status: number;
  readonly codigo: string;
  readonly problema: Partial<Problema> | null;

  constructor(status: number, problema: Partial<Problema> | null) {
    super(problema?.detail ?? problema?.title ?? `Error HTTP ${status}`);
    this.name = "ErrorApi";
    this.status = status;
    this.codigo = problema?.codigo ?? (status === 0 ? "sin_conexion" : "error_http");
    this.problema = problema;
  }
}

export function interpretarProblema(status: number, cuerpo: unknown): ErrorApi {
  const problema =
    cuerpo && typeof cuerpo === "object" && "codigo" in cuerpo ? (cuerpo as Partial<Problema>) : null;
  return new ErrorApi(status, problema);
}

/** Desempaqueta una respuesta de openapi-fetch: devuelve los datos o lanza ErrorApi. */
export async function pedir<T>(
  promesa: Promise<{ data?: T; error?: unknown; response: Response }>,
): Promise<T> {
  let resultado: { data?: T; error?: unknown; response: Response };
  try {
    resultado = await promesa;
  } catch {
    throw new ErrorApi(0, { title: "Sin conexión con la API", codigo: "sin_conexion" });
  }
  if (resultado.error !== undefined || resultado.data === undefined) {
    throw interpretarProblema(resultado.response.status, resultado.error);
  }
  return idiomaActual() === "en" ? traducirDatos(resultado.data) : resultado.data;
}

const GLOSARIO: Record<string, string> = glosario;

/**
 * Textos de los datos en inglés: cada cadena que coincide exactamente con el glosario
 * (`scripts/glosario_en.py`, traducción validada: conserva todos los dígitos) se reemplaza.
 * Los valores numéricos, los identificadores y las cadenas sin traducción quedan intactos.
 */
export function traducirDatos<T>(valor: T): T {
  if (typeof valor === "string") return (GLOSARIO[valor] ?? valor) as T;
  if (Array.isArray(valor)) return valor.map((v) => traducirDatos(v)) as T;
  if (valor && typeof valor === "object") {
    return Object.fromEntries(Object.entries(valor).map(([k, v]) => [k, traducirDatos(v)])) as T;
  }
  return valor;
}
